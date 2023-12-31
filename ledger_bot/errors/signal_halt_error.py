"""Exception raised when receiving a halt signal."""

from __future__ import annotations

import logging
from signal import Signals
from sys import stderr

log = logging.getLogger(__name__)


class SignalHaltError(SystemExit):
    def __init__(self, signal_enum: Signals):
        self.signal_enum = signal_enum
        super().__init__(self.exit_code)
        stderr.write(repr(self))

    @property
    def exit_code(self) -> int:
        return self.signal_enum.value

    def __repr__(self) -> str:
        return f"\nExitted due to {self.signal_enum.name}"
