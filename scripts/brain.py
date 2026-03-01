import os
import sys
from dotenv import load_dotenv
from google import genai
from llama_parse import LlamaParse

# Load environment variables from .env file
load_dotenv()

# Get API keys
gemini_api_key = os.getenv("GEMINI_API_KEY")
llama_cloud_api_key = os.getenv("LLAMA_CLOUD_API_KEY")

# Validate API keys
if not gemini_api_key:
    print("ERROR: GEMINI_API_KEY environment variable is not set!")
    print("Please set it using: export GEMINI_API_KEY='your-key-here'")
    print("Or create a .env file with: GEMINI_API_KEY=your-key-here")
    sys.exit(1)

if not llama_cloud_api_key:
    print("ERROR: LLAMA_CLOUD_API_KEY environment variable is not set!")
    print("Please set it using: export LLAMA_CLOUD_API_KEY='your-key-here'")
    print("Or create a .env file with: LLAMA_CLOUD_API_KEY=your-key-here")
    sys.exit(1)

try:
    # Initialize Clients
    client = genai.Client(api_key=gemini_api_key)
    parser = LlamaParse(api_key=llama_cloud_api_key, result_type="markdown")
    print("API clients initialized successfully!")
except Exception as e:
    print(f"Error initializing API clients: {e}")
    sys.exit(1)

def audit_paper(pdf_url):
    try:
        print(f"Parsing PDF from: {pdf_url}")
        
        # Step A: Parse PDF tables (F1, IoU, dB)
        documents = parser.load_data(pdf_url)
        content = documents[0].text[:18000]
        print(f"Extracted {len(content)} characters from PDF")

        # Step B: Multi-Objective Audit
        prompt = f"""
        Analyze this paper for the MANZAR project (Lahore, Pakistan). 
        Target: Fix 0.33 Precision bottleneck using NVIDIA T4 hardware.

        Provide technical answers for these 4 Objectives:
        1. NEEM DETECTION: Find the Spectral Index (NDRE, GNDVI, or REP) used for species separation.
        2. DEFORESTATION: Find the architecture loss function (Dice, Focal, etc.) for scarce data.
        3. FLOODING: Find the specific Sentinel-1 SAR decibel (dB) threshold for water masking.
        4. LULC FUSION: Explain the synchronization method for Sentinel-1 and Sentinel-2 timestamps.

        Content: {content}
        """
        
        print("Sending request to Gemini...")
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return response.text
        
    except Exception as e:
        return f"Audit Failed: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_url = sys.argv[1]
        result = audit_paper(pdf_url)
        print("\n" + "="*60)
        print("AUDIT RESULT:")
        print("="*60)
        print(result)
        print("="*60)
    else:
        print("Usage: python script_name.py <pdf_url>")
        print("\nExample: python script_name.py https://arxiv.org/pdf/2301.12345.pdf")
        sys.exit(1)