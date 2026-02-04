from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List
import shutil
import os
import json

from Doc_Verification.stringmatching import verify_documents

app = FastAPI(title="Campus One AI – Document Verification")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Campus One AI Document Verification API is live"
    }
    
    
@app.post("/verify")
async def verify_documents_api(
    documents: List[UploadFile] = File(...),
    doc_types: str = Form(...),          # <-- STRING ONLY
    input_fields: str = Form(...)
):
    """
    documents  : uploaded PDF files
    doc_types  : comma-separated string (order matters)
    input_fields : JSON string
    """

    # Parse input_fields JSON
    try:
        input_fields = json.loads(input_fields)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in input_fields")

    # Parse doc_types safely
    doc_types_list = [d.strip() for d in doc_types.split(",") if d.strip()]

    if len(documents) != len(doc_types_list):
        raise HTTPException(
            status_code=400,
            detail=f"documents count ({len(documents)}) "
                   f"!= doc_types count ({len(doc_types_list)})"
        )

    uploaded_docs = {}

    for doc, doc_type in zip(documents, doc_types_list):
        file_path = os.path.join(UPLOAD_DIR, doc.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(doc.file, f)

        uploaded_docs[doc_type] = file_path

    result = verify_documents(uploaded_docs, input_fields)
    return result