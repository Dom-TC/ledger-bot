"""Mixin for dealing with the EventWines table."""

import datetime
import logging
from typing import Dict, List, Optional

import discord
from aiohttp import ClientSession

from ledger_bot.models import BotMessage, Transaction

from .base_storage import BaseStorage

log = logging.getLogger(__name__)


class EventWinesMixin(BaseStorage):
    event_wines_url: str
    bot_id: str
