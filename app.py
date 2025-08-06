import os
import sys
import json
import tempfile
import types
from PIL import Image
from dotenv import load_dotenv
import streamlit as st

# Fix for torch.classes error in Doctr
dummy_module = types.ModuleType("torch.classes")
dummy_module.__path__ = []
sys.modules["torch.classes"] = dummy_module

from utils import analyze_invoice_image, pdf_to_images

load_dotenv()

st.set_page_config(page_title="📄 Formatting Auditor", layout="centered")
st.title("📄 Document Formatting Auditor (GPT-4o)")

# Allow both image and PDF uploads
uploaded = st.file_uploader("Upload an invoice image or PDF", type=["png", "jpg", "jpeg", "webp", "pdf"])

if uploaded:
    selected_image = None

    if uploaded.name.lower().endswith(".pdf"):
        # Convert PDF to images
        pdf_images = pdf_to_images(uploaded.read())

        if not pdf_images:
            st.error("No pages found in PDF.")
            st.stop()

        # Let user select a page
        page_num = st.number_input("Select page", min_value=1, max_value=len(pdf_images), value=1)
        selected_image = pdf_images[page_num - 1]
    else:
        selected_image = Image.open(uploaded)

    st.image(selected_image, caption="Selected Image", use_container_width=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        selected_image.save(tmp.name)
        tmp_path = tmp.name

    # Run OCR
    # st.subheader("🔍 Extracted Text with DocTR:")
    # extracted_text = extract_text_doctr(tmp_path)
    # shortened_text = extracted_text[:2000]
    # if st.toggle("Show full OCR text"):
    #     st.code(extracted_text)
    # else:
    #     st.code(shortened_text)

    # GPT Analysis
    st.info("Analyzing image with GPT-4o…")
    with st.spinner("Running formatting audit…"):
        result = analyze_invoice_image(tmp_path)

    if result.get("error"):
        st.error(result["error"])
        if result.get("raw"):
            st.subheader("Raw LLM output:")
            st.code(result["raw"])
    else:
        st.success("Audit complete. Issues found:")
        st.json(result["data"])

        # Download button
        json_str = json.dumps(result["data"], indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name="invoice_data.json",
            mime="application/json"
        )
