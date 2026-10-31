from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100))
    prediction: Mapped[float] = mapped_column(Float)
    probability: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class BoardSnapshot(Base):
    __tablename__ = "board_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    board_name: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def save_prediction(factory: sessionmaker[Session], result: dict[str, Any],
                    features: dict[str, float]) -> None:
    with factory.begin() as session:
        session.add(Prediction(model_name="xgboost-deal-outcome",
                                prediction=result["prediction"],
                                probability=result["probability"],
                                features=features))
