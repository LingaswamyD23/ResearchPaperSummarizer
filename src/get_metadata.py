from src.utils import DOIParsingError, TitleAuthorParsingError
import re
from typing import Tuple
from .extractor import extract_text

DOI_REGEX  = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
ISSN_REGEX = re.compile(r"\b\d{4}-\d{3}[\dX]\b")

def find_doi_issn(text: str) -> Tuple[str, str]:
    doi_m  = DOI_REGEX.search(text)
    issn_m = ISSN_REGEX.search(text)
    doi   = doi_m.group(0) if doi_m else ""
    issn  = issn_m.group(0) if issn_m else ""
    if not doi and not issn:
        raise DOIParsingError("No DOI or ISSN found.")
    return doi, issn

def extract_title_authors(text: str) -> Tuple[str, str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise TitleAuthorParsingError("Empty text; no title/authors.")
    title = lines[0]
    authors = ""
    for ln in lines[1:6]:
        if "," in ln or " and " in ln:
            authors = ln
            break
    if not authors:
        raise TitleAuthorParsingError("Could not locate authors line.")
    return title, authors


def extract_all(pdf_path: str) -> dict:
    """
    Runs extract_text, find_doi_issn, extract_title_authors,
    and returns a dict with keys: text, doi_issn, title, authors.
    """
    text = extract_text(pdf_path)
    doi, issn = find_doi_issn(text)
    title, authors = extract_title_authors(text)
    return {
        "text": text,
        "doi_issn": doi or issn,
        "title": title,
        "authors": authors,
    }