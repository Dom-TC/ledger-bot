"""
Module containing all of ledger-bots scheduled commands.

The schedule itself is set in LedgerBot.py:LedgerBot
"""

from . import cleanup

cleanup = cleanup.cleanup
