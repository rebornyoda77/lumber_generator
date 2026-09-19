"""Shared helpers used by every LumberGenerator command.

Covers the toolbar-button registration boilerplate and the grouped-component
creation logic that lets Fusion's Parts List/BOM auto-count quantities for
a cut list (reusing one component definition per unique name, added as
additional occurrences, instead of a new definition every time).
"""

import adsk.core

app = adsk.core.Application.get()
ui = app.userInterface

TARGET_WORKSPACE_ID = "FusionSolidEnvironment"
TARGET_PANEL_ID = "SolidScriptsAddinsPanel"

IN_TO_CM = 2.54

# Extra spacing between stacked occurrences of the same component so
# repeats don't render exactly on top of each other.
STACK_GAP_CM = IN_TO_CM


def add_button(cmd_id, cmd_name, cmd_description, on_command_created, handlers):
    """Create (or reuse) a command definition and add it as a button on the
    Solid workspace's Scripts and Add-Ins panel. `handlers` is the calling
    module's list to keep event handlers alive for the add-in's lifetime.
    """
    cmd_def = ui.commandDefinitions.itemById(cmd_id)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(cmd_id, cmd_name, cmd_description)

    cmd_def.commandCreated.add(on_command_created)
    handlers.append(on_command_created)

    workspace = ui.workspaces.itemById(TARGET_WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(TARGET_PANEL_ID)
    if not panel.controls.itemById(cmd_id):
        panel.controls.addCommand(cmd_def)


def remove_button(cmd_id):
    workspace = ui.workspaces.itemById(TARGET_WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(TARGET_PANEL_ID)

    control = panel.controls.itemById(cmd_id)
    if control:
        control.deleteMe()

    cmd_def = ui.commandDefinitions.itemById(cmd_id)
    if cmd_def:
        cmd_def.deleteMe()


def add_grouped_occurrence(root_comp, component_name, stack_offset_cm, build_component):
    """Add an occurrence of `component_name`, reusing an existing component
    definition of that exact name if one already exists in root_comp (so
    Fusion's Parts List/BOM groups and counts them together), or building a
    new one otherwise.

    stack_offset_cm is an (x, y, z) tuple; each repeat is offset by that
    vector times how many occurrences of this component already exist, so
    stacked repeats are visibly separated.

    build_component(component) is called only when a new component
    definition is created, and is responsible for building its geometry.
    """
    existing_component = None
    match_count = 0
    for occurrence in root_comp.occurrences:
        if occurrence.component.name == component_name:
            existing_component = occurrence.component
            match_count += 1

    dx, dy, dz = stack_offset_cm
    placement = adsk.core.Matrix3D.create()
    placement.translation = adsk.core.Vector3D.create(
        dx * match_count, dy * match_count, dz * match_count
    )

    if existing_component:
        root_comp.occurrences.addExistingComponent(existing_component, placement)
        return

    occurrence = root_comp.occurrences.addNewComponent(placement)
    component = occurrence.component
    component.name = component_name
    build_component(component)


def format_inches(value_in: float) -> str:
    if value_in == int(value_in):
        return f"{int(value_in)}in"
    return f"{value_in:.2f}in"
