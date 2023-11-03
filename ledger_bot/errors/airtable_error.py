"""Exception raised when failing to interact with AirTable."""

import logging
from typing import Union

from yarl import URL

log = logging.getLogger(__name__)


class AirTableError(Exception):
    def __init__(self, url: URL, response_dict: dict, *args: object) -> None:
        error_dict: dict = response_dict["error"]
        self.url = url
        if type(error_dict) is dict:
            self.error_type = error_dict.get("type")
            self.error_message = error_dict.get("message")
        else:
            self.error_type = error_dict
            self.error_message = ""
        super().__init__(*args)

    def __repr__(self) -> str:
        return "{class_name}(type:{error_type}, message:'{error_message}', url:{url})".format(
            class_name=self.__class__,
            error_type=self.error_type,
            error_message=self.error_message,
            url=self.url,
        )

    def __str__(self) -> str:
        return "Error from AirTable operation of type '{error_type}', with message:'{error_message}'. Request URL: {url}".format(
            error_type=self.error_type, error_message=self.error_message, url=self.url
        )
