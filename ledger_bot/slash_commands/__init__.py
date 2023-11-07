"""Module containing all our 'slash commands'."""

from . import (
    command_add_user,
    command_hello,
    command_help,
    command_list,
    command_new_sale,
    setup_slash,
)

setup_slash = setup_slash.setup_slash
command_hello = command_hello.command_hello
command_add_user = command_add_user.command_add_user
command_new_sale = command_new_sale.command_new_sale
command_help = command_help.command_help
command_list = command_list.command_list
