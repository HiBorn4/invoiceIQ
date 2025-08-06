import os
import base64
import re
import json
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from pdf2image import convert_from_bytes
from PIL import Image

load_dotenv()

# Azure OpenAI creds
AZURE_API_KEY     = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT    = os.getenv("AI_BASE")
AZURE_DEPLOYMENT  = os.getenv("AZURE_DEPLOYMENT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_VERSION")

chat_model = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    deployment_name=AZURE_DEPLOYMENT,
    api_version=AZURE_API_VERSION,
    temperature=0,
    max_tokens=2000,
)

def clean_llm_response(raw: str) -> str:
    # strip code fences if any
    return re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip()

def analyze_invoice_image(raw_invoice_txt: str) -> dict:

    try:
        # Load and encode the image in base64
        with open(raw_invoice_txt, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")


        system_prompt = {
            "role": "system",
            "content": (
                "You are a highly accurate invoice data extractor. "
                "You will be given an invoice image with both printed and stamped content. "
                "Your job is to extract the following fields using OCR and visual analysis of the image. "
                "Be precise and return values only if they are clearly visible. Otherwise, return null.\n\n"
                "### Fields to Extract:\n"
                "- vendor_code: Usually appears inside a barcode label or QA stamp. Alphanumeric, e.g., DDA00038AD.\n"
                "- invoice_no: A 10-digit number. Found in the upper right section.\n"
                "- invoice_date: Format YYYY-MM-DD. If original is DD.MM.YYYY, convert it.\n"
                "- po_no: A 10-digit number (Purchase Order No.). Search for 10-digit sequences.\n"
                "- part no.: Found in the tabular section labeled 'Part No./Part Description'.\n"
                "- quantity: Corresponds to the part number row in the table.\n"
                "- received_quantity: Found in blue ink stamp marked as 'Rec. Qty'.\n\n"
                "### Output Format:\n"
                "Return the result as a clean JSON object like:\n"
                "{\n"
                "  \"vendor_code\": \"DDA00038AD\",\n"
                "  \"invoice_no\": \"6452526857\",\n"
                "  \"invoice_date\": \"2025-05-15\",\n"
                "  \"po_no\": \"6711089838\",\n"
                "  \"part no.\": \"0102AB201790N\",\n"
                "  \"quantity\": 161,\n"
                "  \"received_quantity\": 161\n"
                "}\n\n"
                "If any field is missing or illegible, return its value as null. "
                "Do not explain anything — output only valid JSON."
            )
        }



        user_prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Here is the invoice image. Extract only and exactly the fields mentioned in the system instructions."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}"
                    }
                }
            ]
        }

        resp = chat_model.invoke([system_prompt, user_prompt])
        cleaned = clean_llm_response(resp.content)
        data = json.loads(cleaned)
        return {"data": data}

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "raw": cleaned}

    except Exception as e:
        return {"error": str(e), "raw": None}
    
def pdf_to_images(pdf_file: bytes, dpi: int = 300) -> list[Image.Image]:
    """
    Convert PDF bytes to a list of PIL Images (one per page).
    
    Args:
        pdf_file (bytes): The PDF file in bytes (e.g., from Streamlit uploader).
        dpi (int): Resolution for image conversion (default: 300).
        
    Returns:
        list[PIL.Image.Image]: List of images, one per page.
    """
    images = convert_from_bytes(pdf_file, dpi=dpi)
    return images