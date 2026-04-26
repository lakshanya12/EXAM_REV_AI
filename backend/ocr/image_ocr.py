# image_ocr.py — Uses EasyOCR for scanned documents, printed text, mixed language images
# EasyOCR supports 80+ languages and handles both printed and some handwritten text

import easyocr
import numpy as np
from ocr.preprocessor import preprocess_image

# Initialize reader once (loading takes a few seconds)
reader = easyocr.Reader(["en"], gpu=False)

def extract_text_from_image(image_path: str) -> str:
    """
    Preprocesses the image with OpenCV, then runs EasyOCR on it.
    Returns all detected text joined into a single string.
    """
    # Clean up the image first (grayscale, denoise, threshold)
    cleaned_image = preprocess_image(image_path)

    # EasyOCR can take a numpy array directly
    results = reader.readtext(cleaned_image)

    # Each result is (bounding_box, text, confidence)
    # We only keep text with confidence above 40% to avoid garbage
    extracted_lines = [text for (_, text, confidence) in results if confidence > 0.4]

    return "\n".join(extracted_lines)