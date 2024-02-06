"""Exception raised when dealing with datetime.."""

import logging
from datetime import datetime

log = logging.getLogger(__name__)


class TimeTravelError(Exception):
    def __init__(self, parsed_date: datetime, command_time: datetime):
        super().__init__()
        self.parsed_date = parsed_date
        self.command_time = command_time

    @property
    def parsed_date_string(self):
        return self.parsed_date.strftime("%a %H:%M:%S %Z")

    @property
    def command_time_string(self):
        return self.command_time.strftime("%a %H:%M:%S")

    @property
    def message(self):
        return (
            "Reminder data parsed as {parsed_date} but it is now {now}.\n"
            "I'm sorry, time travel is difficult 😢."
        ).format(
            parsed_date=self.parsed_date_string,
            now=self.command_time_string,
        )


class DatetimeParsingError(Exception):
    pass
