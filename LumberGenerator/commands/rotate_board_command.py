"""Command: rotate selected board(s)/panel(s) in place.

Fusion doesn't have a real command-line for driving modeling actions, so
this is the fast alternative: select one or more occurrences, pick which
of the occurrence's own local axes to spin around, type an angle (defaults
to 90deg, but accepts any expression), hit OK. Each selected occurrence is
rotated about its own local origin, so it doesn't get flung around the
assembly - it just turns in place.

For a board built by create_lumber_command, local Z is the length axis, so
rotating about it flips the board between lying flat and standing on edge.
For a panel built by create_plywood_command, local Z is the thickness/
face-normal axis, so rotating about it turns the sheet within its own
plane. Local X/Y are also offered for anything that needs a different
axis.

Tip: this command lives on its own real toolbar panel (see common.py),
not nested in a dropdown, so it can be assigned a keyboard shortcut -
hover its button, click the "..." that appears, and choose "Change
Keyboard Shortcut..." - for a select-then-hotkey habit instead of
dragging the Move/Copy gizmo by hand.
"""

import traceback

import adsk.core
import adsk.fusion

from . import common

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "lumberGenerator_rotateBoardCmd"
CMD_NAME = "Rotate Selected 90°"
CMD_DESCRIPTION = "Rotate the selected board/panel occurrence(s) about their own local axis"

SELECTION_INPUT_ID = "lumberGenerator_rotateSelection"
AXIS_INPUT_ID = "lumberGenerator_rotateAxis"
ANGLE_INPUT_ID = "lumberGenerator_rotateAngle"

AXIS_LOCAL_X = "Local X"
AXIS_LOCAL_Y = "Local Y"
AXIS_LOCAL_Z = "Local Z (length axis for lumber / face-normal for plywood)"

AXIS_VECTORS = {
    AXIS_LOCAL_X: (1.0, 0.0, 0.0),
    AXIS_LOCAL_Y: (0.0, 1.0, 0.0),
    AXIS_LOCAL_Z: (0.0, 0.0, 1.0),
}

# Handlers must be kept alive for the life of the add-in, otherwise Fusion
# garbage-collects them and the callbacks silently stop firing.
_handlers = []


def start():
    on_command_created = CommandCreatedHandler()
    common.add_button(CMD_ID, CMD_NAME, CMD_DESCRIPTION, on_command_created, _handlers)


def stop():
    common.remove_button(CMD_ID)
    _handlers.clear()


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            selection_input = inputs.addSelectionInput(
                SELECTION_INPUT_ID, "Board(s)", "Select the board(s)/panel(s) to rotate"
            )
            selection_input.addSelectionFilter("Occurrences")
            selection_input.setSelectionLimits(1, 0)

            axis_input = inputs.addDropDownCommandInput(
                AXIS_INPUT_ID, "Axis", adsk.core.DropDownStyles.TextListDropDownStyle
            )
            for axis_name in (AXIS_LOCAL_Z, AXIS_LOCAL_X, AXIS_LOCAL_Y):
                axis_input.listItems.add(axis_name, axis_name == AXIS_LOCAL_Z)

            default_angle = adsk.core.ValueInput.createByString("90 deg")
            inputs.addValueInput(ANGLE_INPUT_ID, "Angle", "deg", default_angle)

            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

            on_destroy = CommandDestroyHandler()
            cmd.destroy.add(on_destroy)
            _handlers.append(on_destroy)
        except Exception:
            ui.messageBox(f"Failed to create command dialog:\n{traceback.format_exc()}")


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            inputs = args.command.commandInputs
            selection_input = inputs.itemById(SELECTION_INPUT_ID)
            axis_input = inputs.itemById(AXIS_INPUT_ID)
            angle_input = inputs.itemById(ANGLE_INPUT_ID)

            axis_name = axis_input.selectedItem.name
            local_axis = AXIS_VECTORS[axis_name]
            angle_rad = angle_input.value  # angle inputs resolve to radians

            rotated = 0
            skipped = 0
            for i in range(selection_input.selectionCount):
                occurrence = adsk.fusion.Occurrence.cast(selection_input.selection(i).entity)
                if not occurrence:
                    skipped += 1
                    continue
                common.rotate_occurrence_in_place(occurrence, local_axis, angle_rad)
                rotated += 1

            if skipped:
                ui.messageBox(
                    f"Rotated {rotated} occurrence(s). Skipped {skipped} selection(s) that "
                    "weren't components (e.g. a face or body picked directly)."
                )
        except Exception:
            ui.messageBox(f"Failed to rotate selection:\n{traceback.format_exc()}")


class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        # Nothing to clean up; present so the dialog closes cleanly.
        pass
