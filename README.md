# ResearchPaperSummarizer

A Streamlit app to extract DOI/ISSN, title, authors and generate a 3–5 sentence summary from research paper PDFs using OCR and a Groq-backed LLM.

## Features

- **PDF Upload & Storage**  
  - Upload one or more PDF files via a clean Streamlit UI  
  - Raw PDFs saved under `/input`, metadata and Excel outputs under `/output`  
  - All uploads, metadata and generated Excel blobs persisted in SQLite  

- **Text Extraction**  
  - Native text extraction with PyMuPDF (super fast)  
  - Fallback OCR via Tesseract (sequential, optional page-limit)  
  - Configurable “Read all pages” checkbox or limit to first N pages

- **Metadata Parsing**  
  - Auto-detect DOI or ISSN with regex  
  - Heuristic title/author extraction from the first few lines  

- **Summarization**  
  - 3–5 sentence paper summary via LangChain + Groq API  
  - User-selectable LLM model  

- **Results & Downloads**  
  - Preview extracted metadata in-app  
  - Download per-batch metadata as an Excel file  
  - Browse and re-download any previous upload and its summary  

- **Logging & Error Handling**  
  - Per-batch log files under `/logs`  
  - Clear user alerts on failures (OCR, parsing, DB errors)  
  - Streamlit progress bars for long operations  

## Installation & Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/LingaswamyD23/ResearchPaperSummarizer.git
   cd ResearchPaperSummarizer
   
2. **Create & activate Python environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
3. **Install dependencies**
    ```bash
    pip install -r requirements.txt

4. **Obtain a Groq API key**

    Sign into your Groq account at https://groq.com/

    Navigate to Developers > Free API Keys(https://console.groq.com/keys)

    Click Create API Key, give it a name like ResearchPaperSummarizer and copy the resulting key


5. **Configure environment variables**
    ```bash
    Create a .env in the project root:
    ResearchPaperSummarizer_DIR=/home/<user>/<project_dir>
    ResearchPaperSummarizer_DIR_DB=${PAPER_SUMMARY_DIR}/db/ResearchPaperSummarizer.db
    AVAILABLE_MODELS='["llama2","vicuna-13b","mistral-7b"]'
    GROQ_API_KEY=your_groq_api_key_here
    MODEL_NAME="llama-3.1-8b-instant"

    -Troubleshooting:
      If you need to override the project directory, edit BASE_DIR in src/config.py.
      To change the default model or API key, you can also update them directly in src/summarizer.py (not recommended for production).


6. **Run the app**
    ```bash
    streamlit run ResearchPaperSummarizer.py
7. **Visit** http://localhost:8501 in your browser.


## Dependencies & External Tools
    - Streamlit – web UI
    - PyMuPDF – fast native PDF text & page rendering
    - pdf2image – optional fallback image conversion (not used by default)
    - pytesseract – OCR via Tesseract
    - LangChain & langchain-groq – LLM orchestration
    - SQLite – persistent storage for uploads, metadata, outputs
    - Groq API – for on-prem or cloud LLM inference

## Repository Structure
  ResearchPaperSummarizer/
  ├── db/
  │   └── ResearchPaperSummarizer.db
  ├── src/
  │   ├── __init__.py
  │   ├── config.py
  │   ├── db.py
  │   ├── extractor.py
  │   ├── get_metadata.py
  │   ├── summarizer.py
  │   └── utils/
  │       ├── __init__.py
  │       ├── exceptions.py
  │       └── logger.py
  ├── test_pdf/
  │   ├── 1708.02002.pdf
  │   ├── 1902.06838.pdf
  │   └── Non Stationary Multi‐Armed Bandit_ Empirical Evaluation.pdf
  ├── LICENSE
  ├── README.md
  ├── requirements.txt
  └── ResearchPaperSummarizer.py

