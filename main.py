from fastapi import FastAPI
from pydantic import BaseModel
from monday_api import get_all_data
from groq import Groq
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()

# Initialize Groq client safely
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY is missing in .env file")

client = Groq(api_key=groq_api_key)


class Question(BaseModel):
    question: str


@app.get("/")
def home():
    return {"message": "Monday BI Agent Running 🚀"}


@app.get("/test")
def test_monday_connection():
    return get_all_data()


@app.post("/ask")
def ask_question(q: Question):
    try:
        # Fetch monday data
        data = get_all_data()

        # 🔥 Reduce data size to avoid token overflow
        simplified_data = json.dumps(data)
        simplified_data = simplified_data[:10000]  # keep under limit

        prompt = f"""
You are a Business Intelligence Assistant for founders.

Use the provided monday.com data to answer clearly and concisely.

DATA (truncated):
{simplified_data}

FOUNDER QUESTION:
{q.question}

Instructions:
- Calculate totals if relevant
- Highlight receivables or financial risks
- Mention sector-level insights if possible
- Mention data quality issues if visible
- Keep response structured and professional
"""

        # ✅ Updated Stable Groq Model
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        answer = response.choices[0].message.content

        return {"answer": answer}

    except Exception as e:
        return {
            "error": "Something went wrong while processing the request.",
            "details": str(e)
        }