"""Core components."""

from . import config, help_manager

Config = config.Config
register_help_reaction = help_manager.register_help_reaction
register_help_command = help_manager.register_help_command
HelpManager = help_manager.HelpManager
