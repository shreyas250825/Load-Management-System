from fastapi import FastAPI, HTTPException, File, UploadFile
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
def extract_text_from_pdf(file_path):
    global text_data
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_data = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        raise ValueError(f"Error reading PDF: {e}")

# Endpoint to upload and load slides
@app.post("/upload-slides/")
def upload_slides(file: UploadFile = File(...)):
    global text_data
    try:
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        extract_text_from_pdf(file_location)
        os.remove(file_location)  # Clean up temporary file
        return {"message": "Slides uploaded and loaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")

# Endpoint to ask questions
@app.post("/ask-question/", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    global text_data
    if not text_data:
        raise HTTPException(status_code=400, detail="No slides loaded. Please upload the slides first.")

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
# 2. Upload slides: POST to `/upload-slides/` with a file
# 3. Ask questions: POST to `/ask-question/` with `{"question": "Your question here"}`
