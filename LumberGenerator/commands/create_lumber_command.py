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

from .lumber_sizes import NOMINAL_SIZE_ORDER, get_actual_dimensions_in

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "lumberGenerator_createLumberCmd"
CMD_NAME = "Create Lumber Stock"
CMD_DESCRIPTION = "Create a dimensional lumber component (S4S actual dimensions)"

TARGET_WORKSPACE_ID = "FusionSolidEnvironment"
TARGET_PANEL_ID = "SolidScriptsAddinsPanel"

SIZE_INPUT_ID = "lumberGenerator_nominalSize"
LENGTH_INPUT_ID = "lumberGenerator_length"

IN_TO_CM = 2.54

# Extra spacing between stacked occurrences of the same board so repeats
# don't render exactly on top of each other.
STACK_GAP_CM = IN_TO_CM

# Handlers must be kept alive for the life of the add-in, otherwise Fusion
# garbage-collects them and the callbacks silently stop firing.
_handlers = []


def start():
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_DESCRIPTION
        )

    on_command_created = CommandCreatedHandler()
    cmd_def.commandCreated.add(on_command_created)
    _handlers.append(on_command_created)

    workspace = ui.workspaces.itemById(TARGET_WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(TARGET_PANEL_ID)
    if not panel.controls.itemById(CMD_ID):
        panel.controls.addCommand(cmd_def)


def stop():
    workspace = ui.workspaces.itemById(TARGET_WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(TARGET_PANEL_ID)

    control = panel.controls.itemById(CMD_ID)
    if control:
        control.deleteMe()

    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if cmd_def:
        cmd_def.deleteMe()

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
            length_in = length_cm / IN_TO_CM

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
    thickness_cm = thickness_in * IN_TO_CM
    width_cm = width_in * IN_TO_CM

    root_comp = design.rootComponent
    component_name = f"{nominal_size}_{format_length_in(length_in)}"

    # Every board of the same nominal size + length reuses one component
    # definition (as additional occurrences), rather than each becoming its
    # own unique component. Fusion's Parts List/BOM (in a Drawing) groups
    # occurrences by their shared component and auto-computes a QTY column,
    # so this is what lets the cut list count boards per size automatically.
    existing_component = None
    match_count = 0
    for occurrence in root_comp.occurrences:
        if occurrence.component.name == component_name:
            existing_component = occurrence.component
            match_count += 1

    placement = adsk.core.Matrix3D.create()
    placement.translation = adsk.core.Vector3D.create(0, match_count * (width_cm + STACK_GAP_CM), 0)

    if existing_component:
        root_comp.occurrences.addExistingComponent(existing_component, placement)
        return

    occurrence = root_comp.occurrences.addNewComponent(placement)
    component = occurrence.component
    component.name = component_name

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


def format_length_in(length_in: float) -> str:
    if length_in == int(length_in):
        return f"{int(length_in)}in"
    return f"{length_in:.2f}in"
