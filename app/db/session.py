from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def _ensure_sqlite_dir(url: str) -> None:
    if url.startswith("sqlite:///./"):
        path = Path(url.replace("sqlite:///./", ""))
        path.parent.mkdir(parents=True, exist_ok=True)


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        url = settings.resolved_database_url
        _ensure_sqlite_dir(url)

        connect_args = {}
        engine_kwargs = {"pool_pre_ping": True}

        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            engine_kwargs.pop("pool_pre_ping", None)

        _engine = create_engine(url, connect_args=connect_args, **engine_kwargs)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_factory():
    get_engine()
    return _SessionLocal


def get_db():
    factory = get_session_factory()
    db: Session = factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models.agent_job import AgentJob  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
