"""Base view classes for the ledger bot."""

import discord


class BaseView(discord.ui.View):
    """Base view class."""

    def __init__(self, *args, **kwargs):
        # Set timeout to None unless explicitly overridden
        kwargs.setdefault("timeout", None)
        super().__init__(*args, **kwargs)


class BaseLayoutView(discord.ui.LayoutView):
    """Base layout view."""

    def __init__(self, *args, **kwargs):
        # Set timeout to None unless explicitly overridden
        kwargs.setdefault("timeout", None)
        super().__init__(*args, **kwargs)
