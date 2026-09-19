"""Command: rename boards/panels to match their current dimensions.

Length (lumber) and width/length (plywood) can be linked to Fusion user
parameters (see create_lumber_command.py / create_plywood_command.py), so a
board's geometry can change after creation without its name updating to
match. This command re-reads each LumberGenerator-created component's
live, current dimensions (via the model parameters recorded on it at
creation time) and renames it to match - run it once you've finalized your
parameters, to bring names back in sync before generating a cut list.

This is an instant action with no dialog: clicking the button runs it and
reports a summary.
"""

import traceback

import adsk.core
import adsk.fusion

from . import common
from .plywood_sizes import nominal_thickness_to_name_token

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "lumberGenerator_syncNamesCmd"
CMD_NAME = "Sync Board Names"
CMD_DESCRIPTION = "Rename lumber/plywood components to match their current dimensions"

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

            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

            # No inputs needed - run immediately instead of showing a dialog.
            cmd.doExecute(False)
        except Exception:
            ui.messageBox(f"Failed to run Sync Board Names:\n{traceback.format_exc()}")


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            sync_board_names()
        except Exception:
            ui.messageBox(f"Failed to sync board names:\n{traceback.format_exc()}")


def sync_board_names():
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design. Open a design first.")
        return

    # Compute every LumberGenerator component's current canonical name
    # first, so a collision between two components' new names (rare, but
    # possible if parameters converge on the same size) can be caught and
    # skipped instead of silently merging them under one name.
    target_names = {}
    for component in design.allComponents:
        kind = common.get_tag(component, "kind")
        if kind not in ("lumber", "plywood"):
            continue
        new_name = _compute_current_name(design, component, kind)
        if new_name:
            target_names.setdefault(new_name, []).append(component)

    renamed = []
    unchanged = 0
    skipped_collisions = []

    for new_name, components in target_names.items():
        if len(components) > 1:
            skipped_collisions.extend((c.name, new_name) for c in components)
            continue

        component = components[0]
        if component.name == new_name:
            unchanged += 1
        else:
            renamed.append((component.name, new_name))
            component.name = new_name

    _report(renamed, unchanged, skipped_collisions)


def _compute_current_name(design, component, kind):
    if kind == "lumber":
        nominal_size = common.get_tag(component, "nominalSize")
        length_param_name = common.get_tag(component, "lengthParamName")
        if not nominal_size or not length_param_name:
            return None

        length_param = design.allParameters.itemByName(length_param_name)
        if not length_param:
            return None

        length_in = length_param.value / common.IN_TO_CM
        return f"{nominal_size}_{common.format_inches(length_in)}"

    if kind == "plywood":
        nominal_thickness = common.get_tag(component, "nominalThickness")
        width_param_name = common.get_tag(component, "widthParamName")
        length_param_name = common.get_tag(component, "lengthParamName")
        if not nominal_thickness or not width_param_name or not length_param_name:
            return None

        width_param = design.allParameters.itemByName(width_param_name)
        length_param = design.allParameters.itemByName(length_param_name)
        if not width_param or not length_param:
            return None

        width_in = width_param.value / common.IN_TO_CM
        length_in = length_param.value / common.IN_TO_CM
        thickness_token = nominal_thickness_to_name_token(nominal_thickness)
        return f"ply_{thickness_token}_{common.format_inches(width_in)}x{common.format_inches(length_in)}"

    return None


def _report(renamed, unchanged, skipped_collisions):
    lines = []
    if renamed:
        lines.append(f"Renamed {len(renamed)} component(s):")
        lines.extend(f"  {old} -> {new}" for old, new in renamed)
    else:
        lines.append("No components needed renaming.")

    if unchanged:
        lines.append(f"{unchanged} component(s) already matched their current dimensions.")

    if skipped_collisions:
        lines.append(
            f"\nSkipped {len(skipped_collisions)} component(s) - their new names would "
            "collide with another component's:"
        )
        lines.extend(f"  {old} -> {new}" for old, new in skipped_collisions)

    ui.messageBox("\n".join(lines))
