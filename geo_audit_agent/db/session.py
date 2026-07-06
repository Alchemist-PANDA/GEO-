import os
from contextlib import contextmanager

from sqlmodel import Session, create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///geo_saas.db"
)

_engine_kwargs: dict = {"echo": False}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )

engine = create_engine(DATABASE_URL, **_engine_kwargs)


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_session():
    """FastAPI dependency for request-scoped sessions."""
    with get_session() as session:
        yield session
