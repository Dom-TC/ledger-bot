"""Setup Database."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

log = logging.getLogger(__name__)


def setup_database(config):
    """Setup the database session factory."""
    db_path = f"sqlite+aiosqlite:///{config['database_path']}"

    log.info(f"Setting up database: {db_path}")
    engine = create_async_engine(db_path, connect_args={"check_same_thread": False})

    # Session factory
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    return session_factory
