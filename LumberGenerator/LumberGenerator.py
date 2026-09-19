"""LumberGenerator Fusion 360 add-in entry point.

Fusion calls run(context) when the add-in is loaded/started, and
stop(context) when it's stopped/unloaded. All actual command logic lives
under commands/ to keep this file a thin entry point.
"""

import traceback

import adsk.core

from .commands import start as start_commands
from .commands import stop as stop_commands


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        start_commands()
    except Exception:
        if ui:
            ui.messageBox(f"LumberGenerator failed to start:\n{traceback.format_exc()}")


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        stop_commands()
    except Exception:
        if ui:
            ui.messageBox(f"LumberGenerator failed to stop:\n{traceback.format_exc()}")
