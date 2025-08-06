# crop_blue_stamp.py

import os
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_bytes

def pdf_to_images(pdf_bytes: bytes, dpi: int = 300):
    """
    Convert PDF bytes to a list of PIL Images (one per page).
    """
    return convert_from_bytes(pdf_bytes, dpi=dpi)

def crop_blue_stamp_from_pil(pil_img: Image.Image, min_area: int = 2000):
    """
    Given a PIL image, detect the largest blue stamp and return the cropped PIL image.
    Raises ValueError if no suitable stamp is found.
    """
    # Convert PIL→OpenCV BGR
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Blue HSV range (tweak if needed)
    lower_blue = np.array([90, 50,  50])
    upper_blue = np.array([140,255,255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Morphological clean-up
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No blue regions found.")

    # Largest contour
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(contour)
    if w * h < min_area:
        raise ValueError("Largest blue region too small.")

    # Crop from original PIL
    return pil_img.crop((x, y, x + w, y + h)), (x, y, w, h)

def process_file(input_path: str, output_dir: str, min_area: int = 2000):
    """
    Process a single file (PDF or image). Saves crops to output_dir.
    """
    basename = os.path.splitext(os.path.basename(input_path))[0]
    ext = os.path.splitext(input_path)[1].lower()

    # Prepare a subdirectory per input file
    sub_out = os.path.join(output_dir, basename)
    os.makedirs(sub_out, exist_ok=True)

    pages = []
    if ext == ".pdf":
        with open(input_path, "rb") as f:
            pdf_bytes = f.read()
        pages = pdf_to_images(pdf_bytes)
    else:
        # single image file
        pages = [Image.open(input_path).convert("RGB")]

    for idx, page in enumerate(pages, start=1):
        try:
            crop, bbox = crop_blue_stamp_from_pil(page, min_area=min_area)
            out_fname = f"{basename}_page{idx}_stamp.png"
            out_path = os.path.join(sub_out, out_fname)
            crop.save(out_path)
            print(f"[OK] {input_path} (page {idx}): cropped stamp saved to {out_path}, bbox={bbox}")
        except Exception as e:
            print(f"[WARN] {input_path} (page {idx}): {e}")

def process_directory(input_dir: str, output_dir: str, min_area: int = 2000):
    """
    Walks input_dir recursively, processes all .pdf/.png/.jpg/.jpeg/.webp files.
    """
    valid_exts = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
    for root, _, files in os.walk(input_dir):
        for fname in files:
            if os.path.splitext(fname)[1].lower() in valid_exts:
                input_path = os.path.join(root, fname)
                process_file(input_path, output_dir, min_area=min_area)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Detect and crop blue stamps from PDF/image directory.")
    # parser.add_argument("input_dir", help="Directory containing PDFs/images to process")
    # parser.add_argument("output_dir", help="Directory to save cropped stamps")
    parser.add_argument("--min_area", type=int, default=2000,
                        help="Minimum area (px) for detected stamp")
    args = parser.parse_args()

    process_directory("big_data", "big_data_stamps", min_area=args.min_area)
