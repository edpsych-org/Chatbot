"""
PDF text extraction service.

Strategy:
  1. Try pymupdf (fitz) text-layer extraction (fast, high confidence).
  2. If the extracted text is too short (<100 chars) the PDF is likely scanned —
     fall back to pdf2image + pytesseract OCR page-by-page.
  3. Return (text, confidence, ocr_used). Confidence = 1.0 for text layer,
     0.7 for OCR, 0.0 if everything failed.
"""

import io
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, float, bool]:
    """
    Extract text from a PDF (text layer first, OCR fallback).

    Args:
        file_bytes: raw PDF file bytes.

    Returns:
        Tuple of (extracted_text, confidence_score, ocr_was_used).
        confidence is 1.0 for text layer, 0.7 for OCR fallback, 0.0 on total failure.
    """
    # --- 1. Try pymupdf text-layer extraction ---------------------------------
    text = ""
    try:
        import fitz  # PyMuPDF

        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            parts = []
            for page in doc:
                try:
                    parts.append(page.get_text() or "")
                except Exception as page_err:
                    logger.warning(f"pymupdf page extraction failed: {page_err}")
            text = "\n".join(parts).strip()
    except Exception as e:
        logger.warning(f"pymupdf extraction failed: {e}")
        text = ""

    if len(text) >= 100:
        logger.info(f"PDF text-layer extraction succeeded ({len(text)} chars)")
        return text, 1.0, False

    # --- 2. OCR fallback via pdf2image + pytesseract --------------------------
    logger.info(
        f"PDF text layer too short ({len(text)} chars) — falling back to OCR"
    )
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(file_bytes, dpi=300)
        ocr_parts = []
        for idx, image in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(image) or ""
                ocr_parts.append(page_text)
            except Exception as page_err:
                logger.warning(f"OCR failed on page {idx}: {page_err}")

        ocr_text = "\n".join(ocr_parts).strip()
        if ocr_text:
            logger.info(f"OCR extraction succeeded ({len(ocr_text)} chars)")
            return ocr_text, 0.7, True

        logger.warning("OCR produced no text")
        return "", 0.0, True
    except Exception as e:
        logger.error(f"OCR fallback failed: {e}")
        # Return whatever (possibly tiny) text we got from the text layer
        if text:
            return text, 0.3, False
        return "", 0.0, False
