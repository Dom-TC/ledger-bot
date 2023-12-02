"""Base storage class to interface with the end database."""


import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Literal, Optional, Union

from aiohttp import ClientSession

from ledger_bot.errors import AirTableError

from ._storage_helpers import airtable_sleep, run_request

log = logging.getLogger(__name__)


class BaseStorage:
    semaphore = asyncio.Semaphore(5)

    def __init__(
        self,
        airtable_base: str,
        airtable_key: str,
    ):
        self.airtable_base = airtable_base
        self.airtable_key = airtable_key
        self.auth_header = {"Authorization": f"Bearer {self.airtable_key}"}

    async def _get(
        self,
        url: str,
        params: dict[str, str | List[str] | None] | None = None,
        session: Optional[ClientSession] = None,
    ):
        async def run_fetch(session_to_use: ClientSession):
            async with session_to_use.get(
                url,
                params=params,
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    raise AirTableError(r.url, await r.json())
                response: dict = await r.json()
                return response

        async with self.semaphore:
            result = await run_request(run_fetch, session)
            await airtable_sleep()
            return result

    async def _list(
        self,
        base_url: str,
        filter_by_formula: Optional[str],
        session: Optional[ClientSession] = None,
        view: Optional[str] = None,
    ) -> List:
        params: Dict[str, Any] = {}
        if filter_by_formula := filter_by_formula:
            params.update({"filterByFormula": filter_by_formula})
        if view := view:
            params.update({"view": view})
        response = await self._get(base_url, params, session)
        records: List = response.get("records", [])

        return records

    async def _iterate(
        self,
        base_url: str,
        *,
        filter_by_formula: Optional[str],
        sort: Optional[list[str]] = None,
        session: Optional[ClientSession] = None,
        fields: Optional[Union[list[str], str]] = None,
    ) -> AsyncGenerator[dict, None]:
        params: dict[str, str | List[str] | None] = {}

        if filter_by_formula:
            params = {"filterByFormula": filter_by_formula}
        if sort:
            for idx, field in enumerate(sort):
                params[f"sort[{idx}][field]"] = field
                params[f"sort[{idx}][direction]"] = "asc"
        if fields:
            if isinstance(fields, list):
                params["fields[]"] = fields
            else:
                params["fields[]"] = [fields]
        offset = None
        while True:
            if offset:
                params.update(offset=offset)
            async with self.semaphore:
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
    ) -> Dict:
        async def run_delete(session_to_use: ClientSession) -> Dict:
            url = (
                base_url
                if len(records_to_delete) > 1
                else f"{base_url}/{records_to_delete[0]}"
            )
            params = (
                {"records": records_to_delete} if len(records_to_delete) > 1 else None
            )

            async with session_to_use.delete(
                url=url,
                params=params,
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    raise AirTableError(r.url, await r.json())
                response: dict = await r.json()
                return response

        async with self.semaphore:
            result: Dict = await run_request(run_delete, session)
            await airtable_sleep()
            return result

    async def _modify(
        self,
        url: str,
        method: Literal["post", "patch"],
        record: dict,
        upsert_fields: Optional[list[str]],
        session: Optional[ClientSession] = None,
    ) -> Dict:
        async def run_insert(session_to_use: ClientSession) -> Dict:
            is_single_record = "records" not in record
            has_fields = "fields" not in record
            data: dict[str, Union[str, dict, list]] = (
                {"fields": record} if is_single_record and has_fields else record
            )
            entity_url = url
            if upsert_fields is not None:
                if "records" not in record:
                    data["records"] = [data.copy()]
                    data.pop("fields")
                    if data.get("id"):
                        data.pop("id")
                data["performUpsert"] = {"fieldsToMergeOn": upsert_fields}
            elif is_single_record and (record_id := record.get("id")):
                entity_url += "/" + record_id
                record.pop("id")

            async with session_to_use.request(
                method,
                entity_url,
                json=data,
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    raise AirTableError(r.url, await r.json(), data)
                response: dict = await r.json()
                return response

        async with self.semaphore:
            result: Dict = await run_request(run_insert, session)
            await airtable_sleep()
            return result

    async def _insert(
        self,
        url: str,
        record: dict,
        session: Optional[ClientSession] = None,
        upsert_fields: Optional[list[str]] = None,
    ) -> Dict:
        return await self._modify(url, "post", record, upsert_fields, session)

    async def _update(
        self,
        url: str,
        record: dict,
        session: Optional[ClientSession] = None,
        upsert_fields: Optional[list[str]] = None,
    ) -> Dict:
        return await self._modify(url, "patch", record, upsert_fields, session)
