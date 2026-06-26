import os
from sqlmodel import create_engine, Session
from contextlib import contextmanager

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///geo_saas.db"
)

if DATABASE_URL.startswith("postgresql") and not PSYCOPG2_AVAILABLE:
    DATABASE_URL = "sqlite:///geo_saas.db"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )
else:
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
