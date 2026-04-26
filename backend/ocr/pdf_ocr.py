# pdf_ocr.py — Extracts text directly from digital (non-scanned) PDFs
# PyMuPDF is fast and accurate for text-layer PDFs

import fitz  # fitz is the import name for PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    """
    Opens a PDF and extracts the text from every page.
    Works great for typed/digital PDFs. Falls back to empty string for scanned ones.
    """
    full_text = ""

    doc = fitz.open(file_path)

    for page_number in range(len(doc)):
        page = doc[page_number]
        page_text = page.get_text()  # Extracts raw text from the page
        full_text += f"\n--- Page {page_number + 1} ---\n{page_text}"

    doc.close()
    return full_text.strip()