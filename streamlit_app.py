import streamlit as st
import os
import json
import requests
from groq import Groq

st.set_page_config(page_title="Monday Business Intelligence Agent", layout="wide")

# Load environment variables
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
WORK_BOARD_ID = os.getenv("WORK_BOARD_ID")
DEAL_BOARD_ID = os.getenv("DEAL_BOARD_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not MONDAY_API_KEY or not GROQ_API_KEY:
    st.error("API keys not configured. Please add secrets in settings.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

URL = "https://api.monday.com/v2"
headers = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}

def get_board_data(board_id):
    query = f"""
    {{
      boards(ids: {board_id}) {{
        name
        items_page(limit: 100) {{
          items {{
            name
            column_values {{
              column {{
                title
              }}
              text
            }}
          }}
        }}
      }}
    }}
    """
    response = requests.post(URL, json={"query": query}, headers=headers)
    return response.json()

def get_all_data():
    return {
        "work_orders": get_board_data(WORK_BOARD_ID),
        "deals": get_board_data(DEAL_BOARD_ID)
    }

st.title("Monday Business Intelligence Agent")
question = st.text_input("Enter your business question")

if st.button("Generate Insight"):
    with st.spinner("Processing..."):
        data = get_all_data()
        simplified_data = json.dumps(data)[:10000]

        prompt = f"""
You are a Business Intelligence Assistant.

DATA:
{simplified_data}

QUESTION:
{question}

Provide structured executive summary.
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        st.write(response.choices[0].message.content)