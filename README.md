# 🛰️ MANZAR Scout Hunter

<p align="center">
  <em>An automated AI-driven research pipeline for the MANZAR Geospatial Platform</em>
</p>

## 📖 Overview

**MANZAR Scout Hunter** is an automated AI agent pipeline designed to continuously scan, download, and audit the latest research papers from ArXiv. It acts as an autonomous knowledge-gathering scout for the MANZAR platform (in collaboration with SUPARCO and FFC), specifically focusing on identifying novel techniques for **Neem tree detection, deforestation tracking, flooding analysis, and LULC (Land Use and Land Cover) mapping**.

Currently, the MANZAR platform faces a bottleneck with a baseline **F1-score of 0.48** due to spectral overlap between Neem trees and general vegetation in Sentinel-2 (Red-Edge/NIR) imagery. This project automates the search for architectural tweaks (e.g., Attention Gates, SAM2 integration) to help us reach our target **F1-score of 0.70+**, all while ensuring models can comfortably run inference on an **NVIDIA T4 GPU**.

---

## ⚡ How It Works

This project leverages state-of-the-art Generative AI and automated workflow engines:

1. **Scouting (ArXiv)**: The Python script (`scout_hunter.py`) aggressively queries ArXiv for the latest papers matching critical keywords (e.g., "SAM2", "Sentinel-2", "Red-Edge", "Neem").
2. **Extraction (LlamaParse)**: It downloads the PDFs and uses **LlamaParse** to flawlessly extract the structure and text of the research papers into clean Markdown format.
3. **Auditing (Gemini 2.5 Flash)**: The extracted Markdown is passed to Google's **Gemini 2.5 Flash** model. Gemini acts as a Virtual Senior ML Engineer, auditing the paper against our strict criteria (T4 constraints, target F1 scores, spectral overlap resolutions).
4. **Scoring & Delivery (n8n)**: Gemini outputs a JSON payload scoring the paper's utility (1-10) and extracting the exact architectural tweaks. If the paper scores a 2 or higher (relevance threshold), the payload is automatically pushed to a local **n8n** webhook for immediate team delivery and integration.

---

## 🛠️ Tech Stack

*   **Python**: Core orchestration language.
*   **LlamaParse**: Used for highly accurate PDF-to-Markdown document parsing.
*   **Google Gemini 2.5 Flash**: The LLM engine responsible for critically auditing and scoring the research papers.
*   **n8n**: Open-source workflow automation platform used as the "Delivery Hub" to receive valid research payloads.
*   **Docker & Docker Compose**: Containerization of the n8n environment and execution runners.

---

## 🚀 Getting Started

Follow these steps to run **MANZAR Scout Hunter** locally on your machine.

### 1. Prerequisites
Ensure you have the following installed:
*   [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/)
*   [Python 3.10+](https://www.python.org/downloads/)
*   API Keys for **LlamaParse** and **Google Gemini**

### 2. Environment Setup
Clone the repository and set up your environment variables.

```bash
git clone https://github.com/mubeenvr27/MANZAR-Scout-Hunter.git
cd MANZAR-Scout-Hunter

# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

Create a `.env` file in the root of the project with your API keys:
```env
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 3. Start the Delivery Hub (n8n)
We use Docker to spin up n8n, which acts as the webhook receiver for successful paper audits.

```bash
# Start the n8n container in the background
sudo docker compose up -d

# Verify it is running
sudo docker compose ps
```
*n8n will be accessible locally at `http://localhost:5678`.*

### 4. Run the Scout Hunter
Once the webhook receiver is live, you can execute the primary scouting script:

```bash
python scout_hunter.py
```

The script will:
1. Fetch the latest papers.
2. Parse and evaluate them internally.
3. Output the reasoning and JSON scores to the terminal.
4. Auto-push the best papers to the `http://localhost:5678/webhook-test/manzar-push` webhook.

---

## 🛑 Shutting Down

To stop the n8n container and save resources, run:

```bash
sudo docker compose stop
```

*(Refer to `shutdown_notes.txt` for more detailed teardown and restart procedures if needed).*

---
*Built for the future of geospatial intelligence.*