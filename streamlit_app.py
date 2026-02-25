import streamlit as st
import os
import json
import requests
from groq import Groq

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Monday Business Intelligence Agent",
    layout="wide"
)

# ---------------- Load Secrets ----------------
MONDAY_API_KEY = os.getenv("eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjYyNTU4NDEwOCwiYWFpIjoxMSwidWlkIjoxMDAyODQwMjAsImlhZCI6IjIwMjYtMDItMjVUMDU6NDc6NTQuMDAwWiIsInBlciI6Im1lOndyaXRlIiwiYWN0aWQiOjMzOTYwMjA3LCJyZ24iOiJhcHNlMiJ9.UE5JUWWveCpaye7AtGRedTw_Rokk0RYHeH27YkVOIUw")
WORK_BOARD_ID = os.getenv("5026839673")
DEAL_BOARD_ID = os.getenv("5026839687")
GROQ_API_KEY = os.getenv("REDACTED_GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

URL = "https://api.monday.com/v2"
headers = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}

# ---------------- Fetch Data ----------------
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

# ---------------- Styling ----------------
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #ffffff;
    color: #111111;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}
.main-title {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 32px;
    font-weight: 600;
    border-bottom: 2px solid #000000;
    padding-bottom: 12px;
    margin-bottom: 10px;
}
.sub-text {
    font-size: 14px;
    color: #444444;
    margin-bottom: 30px;
}
.section-title {
    font-size: 18px;
    font-weight: 600;
    border-bottom: 1px solid #cccccc;
    padding-bottom: 6px;
    margin-top: 30px;
    margin-bottom: 15px;
}
.answer-box {
    background-color: #ffffff;
    padding: 22px;
    border: 1px solid #000000;
    border-radius: 2px;
    font-size: 15px;
    line-height: 1.6;
}
button {
    background-color: #000000 !important;
    color: #ffffff !important;
    border-radius: 0px !important;
}
input {
    border-radius: 0px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UI ----------------
st.markdown('<div class="main-title">Monday Business Intelligence Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">Executive-level financial and operational reporting across work orders and deal pipeline</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">Executive Query</div>', unsafe_allow_html=True)

question = st.text_input("Enter your business question")

if st.button("Generate Insight"):
    if question.strip() == "":
        st.warning("Please enter a question.")
    else:
        with st.spinner("Processing data..."):
            try:
                data = get_all_data()
                simplified_data = json.dumps(data)[:10000]

                prompt = f"""
You are a Business Intelligence Assistant for founders.

DATA:
{simplified_data}

QUESTION:
{question}

Provide structured executive summary with totals and risk highlights.
"""

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )

                answer = response.choices[0].message.content

                st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)
                st.markdown('<div class="answer-box">' + answer + '</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error("Error processing request.")