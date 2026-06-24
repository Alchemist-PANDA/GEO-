import os
from sqlmodel import create_engine, Session
from contextlib import contextmanager

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///geo_saas.db"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)


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
