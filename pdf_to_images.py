#!/usr/bin/env python3
"""
pdf_to_images.py

Convert all PDFs in a directory to per-page PNG images.

Dependencies:
    pip install pdf2image
    # On Linux/Mac you’ll also need poppler installed:
    #   Ubuntu/Debian: sudo apt-get install poppler-utils
    #   macOS (Homebrew): brew install poppler
"""

import os
import sys
from pdf2image import convert_from_path

def pdfs_to_images(input_dir: str, output_dir: str, dpi: int = 300, fmt: str = "png"):
    """
    Convert all PDF files in input_dir to images in output_dir.
    Each page becomes one image file named: {pdf_basename}_page_{page_number}.{fmt}
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(input_dir, fname)
        basename = os.path.splitext(fname)[0]
        print(f"Converting {fname}…")

        # Convert pages
        try:
            pages = convert_from_path(pdf_path, dpi=dpi)
        except Exception as e:
            print(f"  ❌ Failed to convert {fname}: {e}")
            continue

        # Save each page
        for idx, page in enumerate(pages, start=1):
            out_name = f"{basename}_page_{idx}.{fmt}"
            out_path = os.path.join(output_dir, out_name)
            page.save(out_path, fmt.upper())
            print(f"  ✔ Saved {out_name}")

if __name__ == "__main__":
    # if len(sys.argv) not in (3,4):
        # print("Usage: python pdf_to_images.py <input_dir> <output_dir> [dpi]")
        # sys.exit(1)

    in_dir = "big_data"
    out_dir = "big_data_images"
    # dpi_val = int(sys.argv[3]) if len(sys.argv) == 4 else 300

    pdfs_to_images(in_dir, out_dir, dpi=300)
    print("Done.")
