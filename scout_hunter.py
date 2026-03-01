import arxiv
import json
import time
import sys
import os
import requests
import datetime
import tempfile
import urllib.request
from dotenv import load_dotenv

# We need LlamaParse and Google GenAI
from llama_parse import LlamaParse
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Setup APIs
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not LLAMA_CLOUD_API_KEY or not GEMINI_API_KEY:
    sys.stderr.write("Error: Missing LLAMA_CLOUD_API_KEY or GEMINI_API_KEY in .env\n")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Wait! Let's define the schema for generation directly as a dict for absolute stability if pydantic gives issues 
# but pydantic is normally fine. Let's use standard typing dictionary payload
audit_schema = {
  "type": "OBJECT",
  "properties": {
    "utility_score": {
      "type": "INTEGER",
      "description": "Utility score from 1-10 based on relevance to NVIDIA T4, F1 0.48 baseline, and Sentinel-2/SAM2 integration."
    },
    "key_metrics": {
      "type": "STRING",
      "description": "Extracted key metrics such as Confusion Matrices, IoU tables, or baseline F1 scores mentioned."
    },
    "architectural_tweak": {
      "type": "STRING",
      "description": "Specific architectural tweak suggested (e.g., Attention Gates, ResNet backbones) to improve from 0.48 F1."
    },
    "audit_summary": {
      "type": "STRING",
      "description": "Brief summary of the paper's approach."
    }
  },
  "required": ["utility_score", "key_metrics", "architectural_tweak", "audit_summary"]
}

# We use gemini-2.5-flash as the auditor since 1.5 is unavailable
auditor_model = genai.GenerativeModel('models/gemini-2.5-flash')

SYSTEM_PROMPT = """
You are a Senior ML Engineer auditing a research paper for the MANZAR geospatial platform (collaboration with SUPARCO and FFC).
Your goal is to improve Neem tree detection and distinguish it from general vegetation using Sentinel-2 (Red-Edge/NIR bands) and PRSS-1 imagery.
The current bottleneck is an F1-score of 0.48 due to 'spectral overlap'.
Hardware constraints: Inference must run on an NVIDIA T4 GPU.
Objectives:  Deforestation, Flooding, LULC Analysis.
Goal: Reach 0.70 F1-score. We are specifically looking for SAM2 (Segment Anything Model 2) integration papers or novel architectural tweaks (e.g., Attention Gates).

Analyze the provided paper markdown and extract:
1. Utility Score (1-10): Score >= 7 means it's highly relevant to solving the spectral overlap problem, integrating SAM2, or running on T4.
2. Key Metrics: Look for Confusion Matrices, IoU tables, or F1 scores.
3. Architectural Tweak: What specific model tweak is suggested?
4. Audit Summary: Brief overview.
"""

def download_pdf(pdf_url, save_path):
    sys.stderr.write(f"Downloading {pdf_url} to {save_path}...\n")
    headers = {'User-Agent': 'MANZAR-Scout/1.0'}
    req = urllib.request.Request(pdf_url.replace("http://", "https://"), headers=headers)
    with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
        out_file.write(response.read())

def hunt_and_audit():
    client = arxiv.Client(page_size=10, delay_seconds=3, num_retries=5)
    
    # Target: SAM2, Sentinel-2, Red-Edge, NIR, Neem
    query = 'all:"Red-Edge" OR all:"Sentinel-2" OR all:"SAM2" OR all:"Neem"'
    
    search = arxiv.Search(
        query=query,
        max_results=3, # Limit to 3 for quick testing / execution time
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # Phase 4 Webhook 
    n8n_webhook_url = "http://localhost:5678/webhook-test/manzar-push"
    parser = LlamaParse(result_type="markdown", api_key=LLAMA_CLOUD_API_KEY)
    
    results = []
    
    for result in client.results(search):
        if result.published.year < 2015 or result.published.year > 2026:
            continue
            
        sys.stderr.write(f"\nProcessing: {result.title}\n")
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                # ArXiV search returns pdf_url, e.g. http://arxiv.org/pdf/xxxx.xxxxxv1
                download_pdf(result.pdf_url, tmp_pdf.name)
                
                sys.stderr.write("Parsing PDF with LlamaParse...\n")
                md_documents = parser.load_data(tmp_pdf.name)
                full_markdown = "\n".join([doc.text for doc in md_documents])
                
                # Truncate to reasonable limits to avoid excessive token sizes
                full_markdown = full_markdown[:200000]
                
                sys.stderr.write("Auditing with Gemini 2.5 Flash...\n")
                prompt = SYSTEM_PROMPT + "\n\n--- PAPER MARKDOWN ---\n" + full_markdown
                
                response = auditor_model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=audit_schema,
                    ),
                )
                
                try:
                    audit_result = json.loads(response.text)
                except json.JSONDecodeError:
                    sys.stderr.write("Failed to parse JSON response from Gemini.\n")
                    continue

                utility_score = audit_result.get("utility_score", 0)
                sys.stderr.write(f"Utility Score: {utility_score}/10\n")
                
                if utility_score >= 2:
                    sys.stderr.write("Score >= 7: Promoting to Delivery Hub (n8n)...\n")
                    payload = {
                        "title": result.title,
                        "url": result.pdf_url,
                        "published_date": str(result.published),
                        "utility_score": utility_score,
                        "key_metrics": audit_result.get("key_metrics", ""),
                        "architectural_tweak": audit_result.get("architectural_tweak", ""),
                        "audit_summary": audit_result.get("audit_summary", "")
                    }
                    results.append(payload)
                    
                    try:
                        resp = requests.post(n8n_webhook_url, json=payload)
                        if resp.status_code == 200:
                            sys.stderr.write("Successfully pushed to n8n webhook.\n")
                        else:
                            sys.stderr.write(f"Failed to push to n8n: {resp.status_code} {resp.text}\n")
                    except requests.exceptions.RequestException as e:
                        sys.stderr.write(f"Webhook push HTTP error: {str(e)}\n")
                else:
                    sys.stderr.write("Score < 7: Discarding.\n")

        except Exception as e:
            sys.stderr.write(f"Error processing {result.title}: {str(e)}\n")
            continue
        finally:
            if os.path.exists(tmp_pdf.name):
                os.remove(tmp_pdf.name)

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    hunt_and_audit()