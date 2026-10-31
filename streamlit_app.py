
import json
import os

import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# --------------------------------------------------
# Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Monday Business Intelligence Agent",
    layout="wide"
)

# Load environment variables from the local .env file
load_dotenv()

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
WORK_BOARD_ID = os.getenv("WORK_BOARD_ID")
DEAL_BOARD_ID = os.getenv("DEAL_BOARD_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")

# Validate required configuration
if not MONDAY_API_KEY or not GROQ_API_KEY:
    st.error(
        "API keys not configured. "
        "Please check MONDAY_API_KEY and GROQ_API_KEY in your .env file."
    )
    st.stop()

if not WORK_BOARD_ID or not DEAL_BOARD_ID:
    st.error(
        "Board IDs not configured. "
        "Please check WORK_BOARD_ID and DEAL_BOARD_ID in your .env file."
    )
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

MONDAY_URL = "https://api.monday.com/v2"

HEADERS = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json",
}

# --------------------------------------------------
# Monday.com Data Retrieval
# --------------------------------------------------
def get_board_data(board_id):
    """Retrieve up to 100 items from a Monday.com board."""
    query = """
    query ($board_ids: [ID!]) {
      boards(ids: $board_ids) {
        name
        items_page(limit: 100) {
          items {
            name
            column_values {
              column {
                title
              }
              text
            }
          }
        }
      }
    }
    """

    try:
        response = requests.post(
            MONDAY_URL,
            json={
                "query": query,
                "variables": {"board_ids": [str(board_id)]},
            },
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("errors"):
            raise RuntimeError(
                "Monday.com returned a GraphQL error: "
                + json.dumps(result["errors"])
            )

        return result

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not retrieve Monday.com board data: {exc}"
        ) from exc


def get_all_data():
    """Retrieve work-order and deal board data."""
    return {
        "work_orders": get_board_data(WORK_BOARD_ID),
        "deals": get_board_data(DEAL_BOARD_ID),
    }


# --------------------------------------------------
# Streamlit User Interface
# --------------------------------------------------
st.title("Monday Business Intelligence Agent")
st.caption(
    "Ask questions about your Monday.com work orders and deal pipeline."
)

question = st.text_input(
    "Enter your business question",
    placeholder="Example: Summarize the deal pipeline and identify key risks."
)

if st.button("Generate Insight", type="primary"):
    if not question.strip():
        st.warning("Please enter a business question.")
        st.stop()

    try:
        with st.spinner("Retrieving Monday.com data and generating insights..."):
            if BACKEND_URL:
                backend_response = requests.post(
                    f"{BACKEND_URL}/agent/query",
                    json={"question": question},
                    timeout=120,
                )
                backend_response.raise_for_status()
                answer = backend_response.json()["answer"]
                data = None
            else:
                data = get_all_data()

            if data is not None:
                # Limit the prompt size for this initial version.
                simplified_data = json.dumps(data, ensure_ascii=False)[:10000]

                prompt = f"""
You are a Business Intelligence Assistant analyzing Monday.com data.

Use only the supplied data. Do not invent figures, records, or trends.
If the supplied data is incomplete or truncated, clearly state that limitation.
Distinguish calculated facts from interpretations and recommendations.

DATA:
{simplified_data}

BUSINESS QUESTION:
{question}

Provide a structured executive summary with:
1. Direct answer
2. Key findings supported by the supplied data
3. Relevant metrics, when available
4. Risks or limitations
5. Recommended next steps

If the data does not support an answer, say so clearly.
"""

                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    timeout=120,
                )

                answer = response.choices[0].message.content

        st.subheader("Business Insights")
        st.markdown(answer)

    except (requests.RequestException, RuntimeError, ValueError) as exc:
        st.error(
            "Unable to generate insights. "
            "Check your API configuration and application logs."
        )
        # Avoid exposing credentials or raw API responses in the UI.
        print(f"BI Agent error: {type(exc).__name__}: {exc}")
