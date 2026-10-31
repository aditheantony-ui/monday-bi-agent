from bi_agent.config import Settings
from bi_agent.monday import MondayClient


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"data": {"boards": []}}


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return FakeResponse()


def test_monday_graphql_request_is_configured():
    session = FakeSession()
    client = MondayClient(
        Settings(
            monday_api_key="test",
            work_board_id="1",
            deal_board_id="2",
        ),
        session=session,
    )
    result = client.get_board_data("1")
    assert result == {"data": {"boards": []}}
    assert session.calls[0][1]["json"]["variables"] == {"board_ids": ["1"]}
    assert session.calls[0][1]["headers"]["Authorization"] == "test"
