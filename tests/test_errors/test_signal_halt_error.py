from signal import Signals

import pytest

from ledger_bot.errors.signal_halt_error import SignalHaltError


def test_signal_halt_error(capsys):
    with pytest.raises(SystemExit) as exc_info:
        raise SignalHaltError(Signals.SIGTERM)

    exception = exc_info.value

    assert exception.exit_code == Signals.SIGTERM.value
    assert f"Exitted due to {Signals.SIGTERM.name}" in repr(exception)
