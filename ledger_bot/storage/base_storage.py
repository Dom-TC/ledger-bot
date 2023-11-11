"""Base storage class to interface with the end database."""


import logging
from typing import List, Literal, Optional

from aiohttp import ClientSession

from ledger_bot.errors import AirTableError

from ._storage_helpers import airtable_sleep, run_request

log = logging.getLogger(__name__)


class BaseStorage:
    async def _get(
        self,
        url: str,
        params: Optional[dict[str, str]] = None,
        session: Optional[ClientSession] = None,
    ):
        async def run_fetch(session_to_use: ClientSession):
            async with session_to_use.get(
                url,
                params=params,
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    print(r.url)
                    raise AirTableError(r.url, await r.json())
                response: dict = await r.json()
                return response

        async with self._semaphore:
            result = await run_request(run_fetch, session)
            await airtable_sleep()
            return result

    async def _list(
        self,
        base_url: str,
        filter_by_formula: Optional[str],
        session: Optional[ClientSession] = None,
        view: Optional[str] = None,
    ):
        params = {}
        if filter_by_formula := filter_by_formula:
            params.update({"filterByFormula": filter_by_formula})
        if view := view:
            params.update({"view": view})
        response = await self._get(base_url, params, session)
        return response.get("records", [])

    async def _iterate(
        self,
        base_url: str,
        filter_by_formula: str,
        sort: Optional[list[str]] = None,
        session: Optional[ClientSession] = None,
    ):
        params = {"filterByFormula": filter_by_formula}
        if sort:
            for idx, field in enumerate(sort):
                params.update({"sort[{index}][field]".format(index=idx): field})
                params.update({"sort[{index}][direction]".format(index=idx): "desc"})
        offset = None
        while True:
            if offset:
                params.update(offset=offset)
            async with self._semaphore:
                response = await self._get(base_url, params, session)
                await airtable_sleep()
            records = response.get("records", [])
            for record in records:
                yield record
            offset = response.get("offset")
            if not offset:
                break

    async def _delete(
        self,
        base_url: str,
        records_to_delete: List[str],
        session: Optional[ClientSession] = None,
    ):
        async def run_delete(session_to_use: ClientSession):
            async with session_to_use.delete(
                (
                    base_url
                    if len(records_to_delete) > 1
                    else base_url + f"/{records_to_delete[0]}"
                ),
                params=(
                    {"records": records_to_delete}
                    if len(records_to_delete) > 1
                    else None
                ),
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    log.warning(f"Failed to delete IDs: {records_to_delete}")
                    raise AirTableError(r.url, await r.json())

        async with self._semaphore:
            result = await run_request(run_delete, session)
            await airtable_sleep()
            return result

    async def _modify(
        self,
        url: str,
        method: Literal["post", "patch"],
        record: dict,
        session: Optional[ClientSession] = None,
    ):
        async def run_insert(session_to_use: ClientSession):
            data = {"fields": record}
            async with session_to_use.request(
                method,
                url,
                json=data,
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    raise AirTableError(r.url, await r.json())
                response: dict = await r.json()
                return response

        async with self._semaphore:
            result = await run_request(run_insert, session)
            await airtable_sleep()
            return result

    async def _insert(
        self, url: str, record: dict, session: Optional[ClientSession] = None
    ):
        return await self._modify(url, "post", record, session)

    async def _update(
        self, url: str, record: dict, session: Optional[ClientSession] = None
    ):
        return await self._modify(url, "patch", record, session)
