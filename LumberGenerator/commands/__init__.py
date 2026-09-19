"""Registers all LumberGenerator commands with Fusion's UI.

To add another command later, create a new module in this package with its
own start()/stop() functions and wire it up here alongside create_lumber_command.
"""

from . import create_lumber_command, create_plywood_command

_command_modules = [create_lumber_command, create_plywood_command]


def start():
    for module in _command_modules:
        module.start()


def stop():
    for module in _command_modules:
        module.stop()
