import pytest
from aiohttp import ClientSession

from ledger_bot.storage_airtable._storage_helpers import airtable_sleep, run_request


@pytest.mark.asyncio
async def test_run_request_without_session():
    async def mock_action_to_run(session):
        return {"response": "mocked"}

    result = await run_request(mock_action_to_run)

    assert result == {"response": "mocked"}


@pytest.mark.asyncio
async def test_run_request_with_session():
    async def mock_action_to_run(session):
        return {"response": "mocked"}

    mock_session = ClientSession()

    result = await run_request(mock_action_to_run, session=mock_session)

    assert result == {"response": "mocked"}
    assert not mock_session.closed
    await mock_session.close()


@pytest.mark.asyncio
async def test_run_request_error_handling():
    async def mock_action_to_run_error(session):
        raise ValueError("Mocked error")

    with pytest.raises(ValueError, match="Mocked error"):
        await run_request(mock_action_to_run_error)


@pytest.mark.asyncio
async def test_airtable_sleep(mocker):
    sleep_mock = mocker.patch("asyncio.sleep")

    await airtable_sleep()

    sleep_mock.assert_called_once_with(1.0 / 5)
