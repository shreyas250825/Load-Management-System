from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import PyPDF2
from transformers import pipeline
import os

# Initialize FastAPI app
app = FastAPI()

# Define data models
class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    question: str
    options: List[str]
    answer: str

# Initialize global variables
qa_model = pipeline("question-answering")  # QA model for question answering
text_data = ""  # Placeholder for extracted text

# Utility: Extract text from PDF
def extract_text_from_pdf(pdf_path):
    global text_data
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_data = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        raise ValueError(f"Error reading PDF: {e}")

# Endpoint to load slides
@app.post("/load-slides/")
def load_slides(pdf_path: str):
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=400, detail="PDF file not found.")
    try:
        extract_text_from_pdf(pdf_path)
        return {"message": "Slides loaded successfully."}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to ask questions
@app.post("/ask-question/", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    global text_data
    if not text_data:
        raise HTTPException(status_code=400, detail="No slides loaded. Please load the slides first.")

    question = request.question

    # Use QA model to find an answer
    try:
        answer = qa_model({"question": question, "context": text_data})["answer"]
        # Generate options (dummy options for now)
        options = [answer, "Option B", "Option C", "Option D"]
        return QuestionResponse(question=question, options=options, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {e}")

# Example usage
# 1. Start the server: `uvicorn filename:app --reload`
# 2. Load slides: POST to `/load-slides/` with `pdf_path`
# 3. Ask questions: POST to `/ask-question/` with `{"question": "Your question here"}`