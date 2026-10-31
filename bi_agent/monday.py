from typing import Any

import requests

from .config import Settings

URL = "https://api.monday.com/v2"
BOARD_QUERY = """
query ($board_ids: [ID!]) {
  boards(ids: $board_ids) {
    name
    items_page(limit: 100) {
      items {
        name
        column_values { column { title } text }
      }
    }
  }
}
"""


class MondayClient:
    def __init__(self, settings: Settings, session: requests.Session | None = None):
        settings.require_monday()
        self.settings = settings
        self.session = session or requests.Session()

    def get_board_data(self, board_id: str) -> dict[str, Any]:
        response = self.session.post(
            URL,
            json={"query": BOARD_QUERY, "variables": {"board_ids": [str(board_id)]}},
            headers={"Authorization": self.settings.monday_api_key,
                     "Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("errors"):
            raise RuntimeError("Monday.com returned a GraphQL error")
        return result

    def get_all_data(self) -> dict[str, Any]:
        return {
            "work_orders": self.get_board_data(self.settings.work_board_id),
            "deals": self.get_board_data(self.settings.deal_board_id),
        }
