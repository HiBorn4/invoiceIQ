# detect_stamp_yolo.py

from pdf2image import convert_from_bytes
from ultralytics import YOLO
from PIL import Image
import io
import os

def pdf_to_images(pdf_bytes, dpi=300):
    return convert_from_bytes(pdf_bytes, dpi=dpi)

def detect_and_crop_stamp(pdf_path, output_dir="crops", model_path="yolov8n.pt"):
    os.makedirs(output_dir, exist_ok=True)

    # Load your fine-tuned stamp detector
    model = YOLO(model_path)

    # Convert PDF pages → PIL images
    with open(pdf_path, "rb") as f:
        pages = pdf_to_images(f.read())

    for i, page in enumerate(pages, start=1):
        # Run detection
        results = model(page)
        for det in results:
            for *box, conf, cls in det.boxes.cpu().numpy():
                # assuming cls==0 is “stamp”
                x1, y1, x2, y2 = map(int, box)
                crop = page.crop((x1, y1, x2, y2))
                crop.save(os.path.join(output_dir, f"page{i}_stamp.png"))

if __name__ == "__main__":
    detect_and_crop_stamp("big_data/1.pdf", output_dir="stamp_crops", model_path="best_stamp_model.pt")
