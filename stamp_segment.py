# detect_stamp_sam.py

import torch
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
from pdf2image import convert_from_bytes
from PIL import Image
import numpy as np
import os

def pdf_to_images(pdf_bytes, dpi=300):
    from pdf2image import convert_from_bytes
    return convert_from_bytes(pdf_bytes, dpi=dpi)

def detect_stamp_with_sam(page_img, checkpoint="sam_vit_b_01ec64.pth"):
    # Convert to numpy
    np_img = np.array(page_img)
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    device = "cpu"  # Force CPU for simplicity

    # Load SAM
    sam = sam_model_registry["vit_b"](checkpoint=checkpoint).to(device)
    mask_gen = SamAutomaticMaskGenerator(sam)

    # Generate masks
    masks = mask_gen.generate(np_img)

    # Heuristic: pick masks with high average blue channel
    blue_masks = []
    for m in masks:
        mask = m["segmentation"]
        avg_blue = np.mean(np_img[:,:,2][mask])
        if avg_blue > 150:  # stamp is blue → high B value
            blue_masks.append(mask)

    crops = []
    for mask in blue_masks:
        ys, xs = np.where(mask)
        x1, x2 = xs.min(), xs.max()
        y1, y2 = ys.min(), ys.max()
        crop = page_img.crop((x1, y1, x2, y2))
        crops.append(crop)
    return crops

def process_pdf(pdf_path, output_dir="crops", sam_checkpoint="sam_vit_b_01ec64.pth"):
    os.makedirs(output_dir, exist_ok=True)
    with open(pdf_path, "rb") as f:
        pages = pdf_to_images(f.read())
    for i, page in enumerate(pages, start=1):
        crops = detect_stamp_with_sam(page, checkpoint=sam_checkpoint)
        for j, c in enumerate(crops, start=1):
            c.save(os.path.join(output_dir, f"page{i}_sam_stamp{j}.png"))

if __name__ == "__main__":
    process_pdf("big_data/1.pdf")
