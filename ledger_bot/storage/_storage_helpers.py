"""Helper functions for interacting with AirTable."""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from aiohttp import ClientSession

log = logging.getLogger(__name__)


async def run_request(
    action_to_run: Callable[[ClientSession], Awaitable[Dict[str, Any]]],
    session: Optional[ClientSession] = None,
) -> Dict[str, Any]:
    """
    Asynchronously run requests reusing sessions provided.

    Paramaters
    ----------
    action_to_run : Callable
        The request that will be run

    session : ClientSession, optional
        The session to use, if provided
    """
    if not session:
        async with ClientSession() as new_session:
            return await action_to_run(new_session)
    else:
        return await action_to_run(session)


async def airtable_sleep() -> None:
    """Sleep to meet AirTable's rate limits (5 requests per second)."""
    await asyncio.sleep(1.0 / 5)
