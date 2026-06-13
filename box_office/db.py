"""Engine, session and schema bootstrap. Run `python -m box_office.db`."""

from __future__ import annotations

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from . import config, models  # noqa: F401  (registers all tables)

engine = create_engine(config.DATABASE_URL, echo=False)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db() -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


if __name__ == "__main__":
    init_db()
    print(f"Schema created at {config.DB_PATH}")
    print("Tables:", ", ".join(sorted(SQLModel.metadata.tables)))
