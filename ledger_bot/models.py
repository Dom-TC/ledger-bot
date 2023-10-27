"""The datamodels for ledger_bot."""
import logging
from typing import Union

from yarl import URL

log = logging.getLogger(__name__)


class Model:
    def __init__(self, **kwargs):
        for attr in self.attributes:
            setattr(self, attr, kwargs.get(attr))

    def __str__(self):
        attrs = ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in self.attributes)
        return f"{self.__class__.__name__}({attrs})"


class Member(Model):
    attributes = [
        "primary_key",
        "discord_id",
        "username",
        "nickname",
        "sell_transactions",
        "buy_transactions" "bot_id",
    ]

    @classmethod
    def from_airtable(cls, data: dict) -> "Member":
        fields = data["fields"]
        return cls(
            primary_key=data["id"],
            username=fields.get("username"),
            discord_id=fields.get("discord_id"),
            nickname=fields.get("nickname"),
            sell_transactions=fields.get("sell_transactions"),
            buy_transactions=fields.get("buy_transactions"),
            bot_id=fields.get("bot_id"),
        )

    @property
    def display_name(self):
        name = self.nickname if self.nickname else self.username
        return f"{name}"


class AirTableError(Exception):
    def __init__(
        self, url: URL, response_dict: Union[dict, str], *args: object
    ) -> None:
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
