# ocr_router.py — Decides which OCR method to use based on file type
# This is the "smart router" that picks the right tool for each file

import os
from ocr.pdf_ocr import extract_text_from_pdf
from ocr.handwritten_ocr import extract_text_from_handwritten
from ocr.image_ocr import extract_text_from_image

# Image file extensions we handle
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]

def extract_text_from_file(file_path: str) -> str:
    """
    Routes the file to the correct OCR method:
    - PDF → PyMuPDF first, fallback to EasyOCR if text is empty (scanned PDF)
    - Image → OpenCV preprocess + EasyOCR (for printed) or TrOCR (for handwritten)
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        # Try digital PDF extraction first
        text = extract_text_from_pdf(file_path)

        # If we got almost nothing, the PDF is probably scanned — use EasyOCR
        if len(text.strip()) < 50:
            print("Digital PDF extraction failed — switching to EasyOCR")
            text = extract_text_using_easyocr_on_pdf(file_path)

        return text

    elif ext in IMAGE_EXTENSIONS:
        # Heuristic: if filename contains "handwritten", use TrOCR
        # Otherwise default to EasyOCR which handles most cases
        if "handwritten" in file_path.lower():
            return extract_text_from_handwritten(file_path)
        else:
            return extract_text_from_image(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_text_using_easyocr_on_pdf(pdf_path: str) -> str:
    """
    Converts each PDF page to an image and runs EasyOCR on it.
    Used as fallback for scanned PDFs.
    """
    import fitz
    from PIL import Image
    import io
    from ocr.image_ocr import extract_text_from_image
    import tempfile

    doc = fitz.open(pdf_path)
    all_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=200)  # Render page at 200 DPI for better quality
        image_data = pix.tobytes("png")

        # Save as temp image file so EasyOCR can read it
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_data)
            tmp_path = tmp.name

        page_text = extract_text_from_image(tmp_path)
        all_text.append(page_text)
        os.remove(tmp_path)

    doc.close()
    return "\n".join(all_text)