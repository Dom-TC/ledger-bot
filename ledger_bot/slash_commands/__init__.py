"""Module containing all our 'slash commands'."""

from . import command_add_user, command_hello, command_new_sale, setup_slash

setup_slash = setup_slash.setup_slash
command_hello = command_hello.command_hello
command_add_user = command_add_user.command_add_user
command_new_sale = command_new_sale.command_new_sale
