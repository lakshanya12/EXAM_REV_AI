# preprocessor.py — Uses OpenCV to clean up images before OCR
# This step dramatically improves accuracy on low-quality scans

import cv2
import numpy as np

def preprocess_image(image_path: str) -> np.ndarray:
    """
    Takes a raw image path and returns a cleaned numpy array.
    Steps: grayscale → denoise → threshold → deskew
    """
    # Load the image
    img = cv2.imread(image_path)

    # Convert to grayscale (OCR works better on single channel)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove noise using Gaussian blur
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # Apply adaptive thresholding — handles uneven lighting in photos of handwritten notes
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # Deskew: detect the angle of text and rotate the image to straighten it
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Only deskew if the tilt is significant
        if abs(angle) > 0.5:
            h, w = thresh.shape
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            thresh = cv2.warpAffine(thresh, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return thresh