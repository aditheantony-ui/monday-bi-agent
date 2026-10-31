import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()


class Settings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    monday_api_key: str | None = Field(default=None, validation_alias="MONDAY_API_KEY")
    work_board_id: str | None = Field(default=None, validation_alias="WORK_BOARD_ID")
    deal_board_id: str | None = Field(default=None, validation_alias="DEAL_BOARD_ID")
    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-20b", validation_alias="GROQ_MODEL")
    database_url: str = Field(default="sqlite:///./bi_agent.db", validation_alias="DATABASE_URL")
    backend_url: str = Field(default="http://localhost:8000", validation_alias="BACKEND_URL")
    model_dir: Path = Field(default=Path("models"), validation_alias="MODEL_DIR")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    def require_monday(self) -> None:
        missing = [name for name, value in (("MONDAY_API_KEY", self.monday_api_key),
                    ("WORK_BOARD_ID", self.work_board_id), ("DEAL_BOARD_ID", self.deal_board_id))
                   if not value]
        if missing:
            raise RuntimeError("Missing Monday.com configuration: " + ", ".join(missing))

    def require_groq(self) -> None:
        if not self.groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY configuration")


@lru_cache
def get_settings() -> Settings:
    return Settings(
        monday_api_key=os.getenv("MONDAY_API_KEY"),
        work_board_id=os.getenv("WORK_BOARD_ID"),
        deal_board_id=os.getenv("DEAL_BOARD_ID"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./bi_agent.db"),
        backend_url=os.getenv("BACKEND_URL", "http://localhost:8000"),
        model_dir=Path(os.getenv("MODEL_DIR", "models")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
