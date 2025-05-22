import logging
import os

import pytesseract
from tqdm import tqdm
from src.utils import TextExtractionError, OCRExtractionError, setup_logger
import fitz                        # PyMuPDF
from typing import List
from PIL import Image
from langchain.schema import Document 



logger = setup_logger(__name__, level=logging.INFO)


def _load_native_mupdf(pdf_path: str) -> List[Document]:
    """
    Very fast embedded-text extraction with PyMuPDF.
    """
    docs = []
    try:
        doc = fitz.open(pdf_path)
        logger.info(f"[mupdf] {len(doc)} pages; extracting text natively")
        for i, page in enumerate(tqdm(doc, desc="Extracting text", unit="page"), start=1):
            txt = page.get_text().strip()
            docs.append(Document(page_content=txt, metadata={"page": i}))
            logger.debug(f"[mupdf] page {i}: {len(txt)} chars")
    except Exception as e:
        logger.warning(f"[mupdf] text extraction failed: {e}")
    return docs


def _render_page_to_pil(page, dpi: int):

    zoom = dpi / 72
    mat  = fitz.Matrix(zoom, zoom)
    pix  = page.get_pixmap(matrix=mat, alpha=False)
    # build a PIL image from pixmap
    mode = "RGB" if pix.n < 4 else "RGBA"
    img  = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    return img

def _load_ocr_sequential(
    pdf_path: str,
    dpi: int = 200,
    lang: str = "eng",
    max_pages: int | None = None
) -> List[Document]:
    """
    Render pages via PyMuPDF + PIL, then OCR with pytesseract.
    No external poppler; much faster than convert_from_path().
    """ 
    docs: List[Document] = []
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    page_range = range(total_pages) if max_pages is None else range(min(max_pages, total_pages))

    logger.info(f"[OCR-seq] Rendering {len(page_range)} pages via PyMuPDF at {dpi} DPI")
    for i in tqdm(page_range, desc="Pages OCR’d", unit="pg"):
        page = doc[i]
        try:
            img = _render_page_to_pil(page, dpi)
            text = pytesseract.image_to_string(img, lang=lang, config="--psm 3")
            docs.append(Document(page_content=text, metadata={"page": i+1}))
            logger.debug(f"[OCR-seq] page {i+1}: {len(text)} chars")
        except Exception as e:
            logger.error(f"[OCR-seq] error on page {i+1}: {e}")
            raise OCRExtractionError(f"OCR failed on page {i+1}: {e}")

    logger.info(f"[OCR-seq] Completed OCR for {len(docs)} pages")
    return docs




def extract_text(pdf_path: str, min_chars: int = 200, ocr_max_pages:int | None = None) -> str:

    if not os.path.isfile(pdf_path):
        raise TextExtractionError(f"File not found: {pdf_path}")


    native_docs = _load_native_mupdf(pdf_path)
    native_text = "\n\n".join(d.page_content for d in native_docs if d.page_content)
    if len(native_text) >= min_chars:
        logger.info(f"[mupdf] succeeded with {len(native_text)} chars")
        return native_text

    logger.info(f"[extract_text] native only {len(native_text)} chars; falling back to OCR")
    ocr_docs = _load_ocr_sequential(
        pdf_path,
        dpi=200,
        lang="eng",
        max_pages=ocr_max_pages
    )
    ocr_text = "\n\n".join(d.page_content for d in ocr_docs if d.page_content)
    if not ocr_text.strip():
        raise OCRExtractionError("Sequential OCR returned no text")
    return ocr_text
