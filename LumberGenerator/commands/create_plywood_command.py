"""Command: create a plywood panel component.

Adds a button that opens a dialog to pick a nominal plywood thickness and a
custom width + length, then builds (or adds another occurrence of) a
component with a rectangular sketch on the XY plane extruded to the
panel's actual (sanded) thickness. Unlike dimensional lumber, plywood's
width and length are cut to whatever size is needed rather than coming
from a standard table - only thickness has a nominal-vs-actual gap.

Panels with the same thickness + width + length share one component
definition so Fusion's Parts List/BOM can auto-count quantity (see README
"Cut lists").
"""

import traceback

import adsk.core
import adsk.fusion

from . import common
from .plywood_sizes import (
    NOMINAL_THICKNESS_ORDER,
    get_actual_thickness_in,
    nominal_thickness_to_name_token,
)

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "lumberGenerator_createPlywoodCmd"
CMD_NAME = "Create Plywood Panel"
CMD_DESCRIPTION = "Create a plywood panel component (actual sanded thickness)"

THICKNESS_INPUT_ID = "lumberGenerator_plywoodThickness"
WIDTH_INPUT_ID = "lumberGenerator_plywoodWidth"
LENGTH_INPUT_ID = "lumberGenerator_plywoodLength"

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

            thickness_input = inputs.addDropDownCommandInput(
                THICKNESS_INPUT_ID,
                "Nominal Thickness",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            default_thickness = "3/4"
            for thickness in NOMINAL_THICKNESS_ORDER:
                thickness_input.listItems.add(thickness, thickness == default_thickness)

            # ValueInputs of unit type "in" accept Fusion's normal expression
            # syntax, so users can type "24", "24 in", "2 ft", or "2'".
            default_width = adsk.core.ValueInput.createByString("48 in")
            inputs.addValueInput(WIDTH_INPUT_ID, "Width", "in", default_width)

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
            thickness_input = inputs.itemById(THICKNESS_INPUT_ID)
            width_input = inputs.itemById(WIDTH_INPUT_ID)
            length_input = inputs.itemById(LENGTH_INPUT_ID)

            nominal_thickness = thickness_input.selectedItem.name
            # .expression is the raw text the user typed (e.g. "24 in" or a
            # user parameter name like "cabinet_width") - passed through to
            # the sketch dimensions so the panel stays linked to a
            # referenced parameter, instead of a fixed resolved value.
            width_expression = width_input.expression
            length_expression = length_input.expression
            # Internal database units are cm.
            width_cm = width_input.value
            length_cm = length_input.value
            width_in = width_cm / common.IN_TO_CM
            length_in = length_cm / common.IN_TO_CM

            create_plywood_component(
                nominal_thickness,
                width_expression,
                length_expression,
                width_cm,
                length_cm,
                width_in,
                length_in,
            )
        except Exception:
            ui.messageBox(f"Failed to create plywood component:\n{traceback.format_exc()}")


class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        # Nothing to clean up; present so the dialog closes cleanly.
        pass


def create_plywood_component(
    nominal_thickness: str,
    width_expression: str,
    length_expression: str,
    width_cm: float,
    length_cm: float,
    width_in: float,
    length_in: float,
):
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design. Open or create a design first.")
        return

    actual_thickness_in = get_actual_thickness_in(nominal_thickness)
    actual_thickness_cm = actual_thickness_in * common.IN_TO_CM

    root_comp = design.rootComponent
    thickness_token = nominal_thickness_to_name_token(nominal_thickness)
    component_name = (
        f"ply_{thickness_token}_{common.format_inches(width_in)}x{common.format_inches(length_in)}"
    )

    def build_component(component):
        sketch = component.sketches.add(component.xYConstructionPlane)
        common.add_dimensioned_rectangle(
            sketch, width_cm, length_cm, width_expression, length_expression
        )

        profile = sketch.profiles.item(0)
        extrudes = component.features.extrudeFeatures
        extrude_input = extrudes.createInput(
            profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        extrude_input.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(actual_thickness_cm)
        )
        extrudes.add(extrude_input)

    # Stack repeats of the same thickness+width+length along Z, like a
    # physical stack of sheets.
    stack_offset_cm = (0, 0, actual_thickness_cm + common.STACK_GAP_CM)
    common.add_grouped_occurrence(root_comp, component_name, stack_offset_cm, build_component)
