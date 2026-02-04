import os
import json
from PyPDF2 import PdfReader
import fitz
import pytesseract
from PIL import Image
import numpy as np
import shutil
import cv2
import io

pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")

# ---------- IMAGE PREPROCESS ----------
def preprocess_image(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]
    return Image.fromarray(gray)

# ---------- PDF TEXT ----------
def extract_with_pypdf2(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text.strip()

def extract_with_ocr(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        pix = page.get_pixmap(dpi=400)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img = preprocess_image(img)
        ocr_text = pytesseract.image_to_string(
            img, lang="eng+hin", config="--oem 3 --psm 6"
        )
        text += ocr_text + "\n"
    return text.strip()

def pdf2text_hybrid(path):
    text = extract_with_pypdf2(path)
    if len(text) > 100:
        return text
    return extract_with_ocr(path)

# ---------- REQUIRED FIELDS ----------
REQUIRED_FIELDS = {
    "10th_marksheet": [
        "name", "father_name", "mother_name",
        "dob", "roll_number_10th", "board"
    ],
    "12th_marksheet": [
        "name", "father_name", "mother_name",
        "roll_number_12th", "board"
    ],
    "aadhar_card": [
        "name", "aadhar_number", "vid_number"
    ],
    "entrance_exam": [
        "name", "application_number", "final_percentile_score"
    ]
}

# ---------- STRING MATCHING ----------
def match_required_fields(extracted_text, input_fields, required_fields):
    extracted_text = extracted_text.lower()
    matched = {}

    # Aadhaar special logic
    if "aadhar_number" in required_fields or "vid_number" in required_fields:
        aadhar = input_fields.get("aadhar_number")
        vid = input_fields.get("vid_number")

        if aadhar:
            matched["aadhar_number"] = aadhar.lower() in extracted_text
        elif vid:
            matched["vid_number"] = vid.lower() in extracted_text

        if input_fields.get("name"):
            matched["name"] = input_fields["name"].lower() in extracted_text

        return matched

    # Normal documents
    for field in required_fields:
        value = input_fields.get(field)
        if not value:
            continue
        matched[field] = value.lower() in extracted_text

    return matched

# ---------- VERIFICATION ----------
def verify_documents(uploaded_docs, input_fields):
    results = {}

    for doc_type, file_path in uploaded_docs.items():

        if not os.path.exists(file_path):
            continue

        extracted_text = pdf2text_hybrid(file_path)
        required_fields = REQUIRED_FIELDS.get(doc_type, [])

        matched_data = match_required_fields(
            extracted_text, input_fields, required_fields
        )

        matched_count = sum(matched_data.values())
        total_fields = len(matched_data)

        percentage = round((matched_count / total_fields) * 100, 2) if total_fields else 0.0
        status = "VERIFIED" if percentage >= 80 else "REJECTED"

        results[doc_type] = {
            "parsed_data": extracted_text,
            "matched_data": matched_data,
            "percentage_matched": percentage,
            "verified_status": status
        }

    return results

# ---------- RUN ----------
if __name__ == "__main__":

    uploaded_docs = {
        "12th_marksheet": "XII Marksheet.pdf",
        "aadhar_card": "Aadhar.pdf"
    }

    input_fields = {
        "name": "VASU GOEL",
        "father_name": "PANKAJ GOEL",
        "mother_name": "NEELIMA GOEL",
        "dob": "12-08-2005",
        "roll_number_10th": "A12345",
        "roll_number_12th": "B67890",
        "board": "ICSE",
        "aadhar_number": "4349 8043 1450",
        "vid_number": "9999 8888 7777",
        "application_number": "ENT2024XYZ",
        "final_percentile_score": "98.76"
    }

    output = verify_documents(uploaded_docs, input_fields)

    with open("verification_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("AI Verification completed.")