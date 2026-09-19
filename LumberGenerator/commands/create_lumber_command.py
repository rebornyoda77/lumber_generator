"""Command: create a dimensional lumber component.

Adds a button that opens a dialog to pick a nominal lumber size and a
length, then builds (or adds another occurrence of) a component with a
rectangular sketch on the XY plane extruded to the requested length, sized
to the actual (S4S dressed) dimensions for that nominal size. Boards with
the same nominal size + length share one component definition so Fusion's
Parts List/BOM can auto-count quantity per size (see README "Cut lists").
"""

import traceback

import adsk.core
import adsk.fusion

from . import common
from .lumber_sizes import NOMINAL_SIZE_ORDER, get_actual_dimensions_in

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "lumberGenerator_createLumberCmd"
CMD_NAME = "Create Lumber Stock"
CMD_DESCRIPTION = "Create a dimensional lumber component (S4S actual dimensions)"

SIZE_INPUT_ID = "lumberGenerator_nominalSize"
LENGTH_INPUT_ID = "lumberGenerator_length"

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

            size_input = inputs.addDropDownCommandInput(
                SIZE_INPUT_ID, "Nominal Size", adsk.core.DropDownStyles.TextListDropDownStyle
            )
            for size in NOMINAL_SIZE_ORDER:
                size_input.listItems.add(size, size == NOMINAL_SIZE_ORDER[0])

            # A ValueInput of unit type "in" accepts Fusion's normal expression
            # syntax, so users can type "36", "36 in", "3 ft", or "8'" and it
            # will evaluate correctly.
            default_length = adsk.core.ValueInput.createByString("96 in")
            inputs.addValueInput(LENGTH_INPUT_ID, "Length", "in", default_length)

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
            size_input = inputs.itemById(SIZE_INPUT_ID)
            length_input = inputs.itemById(LENGTH_INPUT_ID)

            nominal_size = size_input.selectedItem.name
            length_cm = length_input.value  # internal database units are cm
            length_in = length_cm / common.IN_TO_CM

            create_lumber_component(nominal_size, length_cm, length_in)
        except Exception:
            ui.messageBox(f"Failed to create lumber component:\n{traceback.format_exc()}")


class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        # Nothing to clean up; present so the dialog closes cleanly.
        pass


def create_lumber_component(nominal_size: str, length_cm: float, length_in: float):
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design. Open or create a design first.")
        return

    thickness_in, width_in = get_actual_dimensions_in(nominal_size)
    thickness_cm = thickness_in * common.IN_TO_CM
    width_cm = width_in * common.IN_TO_CM

    root_comp = design.rootComponent
    component_name = f"{nominal_size}_{common.format_inches(length_in)}"

    def build_component(component):
        sketch = component.sketches.add(component.xYConstructionPlane)
        corner1 = adsk.core.Point3D.create(0, 0, 0)
        corner2 = adsk.core.Point3D.create(width_cm, thickness_cm, 0)
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(corner1, corner2)

        profile = sketch.profiles.item(0)
        extrudes = component.features.extrudeFeatures
        extrude_input = extrudes.createInput(
            profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        extrude_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(length_cm))
        extrudes.add(extrude_input)

    # Stack repeats of the same size+length side by side along Y so they
    # don't render on top of each other.
    stack_offset_cm = (0, width_cm + common.STACK_GAP_CM, 0)
    common.add_grouped_occurrence(root_comp, component_name, stack_offset_cm, build_component)
