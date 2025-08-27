"""Various helpers for our service classes."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class ServiceHelpers:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @asynccontextmanager
    async def _get_session(
        self, session: AsyncSession | None = None
    ) -> AsyncIterator[AsyncSession]:
        if session is not None:
            yield session
        else:
            async with self._session_factory() as s:
                yield s
