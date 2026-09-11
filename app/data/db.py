from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config.paths import database_path
from app.data.models.base import Base


def create_db_engine(db_path: str | None = None):
    """Create the SQLAlchemy engine for the local SQLite database.

    Foreign keys are off by default in SQLite; enabling them per-connection
    is required for the ForeignKey constraints in the models to be enforced.
    """
    url = f"sqlite:///{db_path or database_path()}"
    engine = create_engine(url, future=True)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
