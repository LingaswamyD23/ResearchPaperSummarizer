import os
import ast
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)


# Base directory 
BASE_DIR = os.getenv("ResearchPaperSummarizer_DIR", "<path>/ResearchPaperSummarizer")


# Subdirectories (relative to BASE_DIR)
INPUT_DIR  = os.getenv("INPUT_DIR",  os.path.join(BASE_DIR, "input"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output"))
LOG_DIR    = os.getenv("LOG_DIR",    os.path.join(BASE_DIR, "logs"))
DB_DIR     = os.getenv("DB_DIR",     os.path.join(BASE_DIR, "db"))


# Database file path

DB_PATH = os.getenv(
    "ResearchPaperSummarizer_DB",
    os.path.join(DB_DIR, "ResearchPaperSummarizer.db")
)


_raw_models = os.getenv(
    "AVAILABLE_MODELS",
    '["gemma2-9b-it","llama-3.3-70b-versatile","llama-3.1-8b-instant", "llama3-70b-8192","llama3-8b-8192","deepseek-r1-distill-llama-70b"]'
)

try:
    AVAILABLE_MODELS = ast.literal_eval(_raw_models)
    if not isinstance(AVAILABLE_MODELS, list):
        raise ValueError("AVAILABLE_MODELS is not a list")
except Exception:
    # fallback if parsing fails
    AVAILABLE_MODELS = ["gemma2-9b-it","llama-3.3-70b-versatile","llama-3.1-8b-instant", "llama3-70b-8192","llama3-8b-8192","deepseek-r1-distill-llama-70b"]


# Ensure all directories exist

for path in (BASE_DIR, INPUT_DIR, OUTPUT_DIR, LOG_DIR, DB_DIR):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Could not create directory {path}: {e}")

