"""Mixin for dealing with the EventDeposits table."""

import datetime
import logging
from typing import Dict, List, Optional

import discord
from aiohttp import ClientSession

from ledger_bot.models import BotMessage, Transaction

from .base_storage import BaseStorage

log = logging.getLogger(__name__)


class EventDepositsMixin(BaseStorage):
    event_deposits_url: str
    bot_id: str
