# handwritten_ocr.py — Uses Microsoft's TrOCR model to read handwritten text
# TrOCR is a transformer-based OCR model fine-tuned on handwritten datasets

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch

# Load model and processor once at startup (not on every request)
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

def extract_text_from_handwritten(image_path: str) -> str:
    """
    Reads a handwritten image using TrOCR.
    Splits tall images into horizontal strips to handle multi-line notes.
    """
    image = Image.open(image_path).convert("RGB")

    # TrOCR processes one line at a time, so we split into horizontal strips
    width, height = image.size
    strip_height = 60  # Approximate height of one handwritten line
    all_lines = []

    for y in range(0, height, strip_height):
        # Crop each horizontal strip
        strip = image.crop((0, y, width, min(y + strip_height, height)))

        # Prepare image for the model
        pixel_values = processor(images=strip, return_tensors="pt").pixel_values

        # Generate text tokens
        with torch.no_grad():
            generated_ids = model.generate(pixel_values)

        # Decode tokens back to string
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        if generated_text.strip():
            all_lines.append(generated_text.strip())

    return "\n".join(all_lines)