import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MONDAY_API_KEY")
WORK_BOARD_ID = os.getenv("WORK_BOARD_ID")
DEAL_BOARD_ID = os.getenv("DEAL_BOARD_ID")

URL = "https://api.monday.com/v2"

headers = {
    "Authorization": API_KEY,
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

    if response.status_code != 200:
        return {"error": response.text}

    return response.json()


def get_all_data():
    return {
        "work_orders": get_board_data(WORK_BOARD_ID),
        "deals": get_board_data(DEAL_BOARD_ID)
    }