from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import json

from Doc_Verification.stringmatching import verify_documents

app = FastAPI(title="Campus One AI – Document Verification")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Campus One AI Document Verification API is live"
    }

@app.post("/verify")
async def verify_documents_api(
    documents: List[UploadFile] = File(...),
    doc_types: str = Form(...),
    input_fields: str = Form(...)
):

    try:
        input_fields = json.loads(input_fields)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON in input_fields")

    doc_types_list = [d.strip() for d in doc_types.split(",") if d.strip()]

    if len(documents) != len(doc_types_list):
        raise HTTPException(400, "documents and doc_types mismatch")

    uploaded_docs = {}

    for doc, doc_type in zip(documents, doc_types_list):

        if doc.content_type != "application/pdf":
            raise HTTPException(400, "Only PDF files allowed")

        uploaded_docs[doc_type] = await doc.read()

    return verify_documents(uploaded_docs, input_fields)