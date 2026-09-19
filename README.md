# LumberGenerator

A Fusion 360 add-in that generates dimensional lumber and plywood stock as
Fusion components.

- **Lumber**: pick a nominal size (e.g. `2x4`) and a length, and it creates
  a component sized to the actual S4S dressed dimensions (e.g. `2x4` ->
  1.5in x 3.5in), extruded to the length you specify.
- **Plywood**: pick a nominal thickness (e.g. `3/4`) and a custom width +
  length, and it creates a panel sized to the actual sanded thickness (e.g.
  `3/4` -> 0.719in) with the width/length you specify.

## What it does

- Adds **Create Lumber Stock** and **Create Plywood Panel** buttons to the
  Solid workspace's Scripts and Add-Ins panel.
- **Create Lumber Stock** opens a dialog with:
  - A dropdown of standard nominal sizes: `2x4`, `2x6`, `2x8`, `2x10`,
    `2x12`, `4x4`, `1x2`, `1x4`, `1x6`, `1x8`.
  - A length field. It accepts Fusion's normal expression syntax, so you
    can type `36`, `36 in`, `3 ft`, or `8'`.
  - On execution, creates (or adds another occurrence of) a component
    named descriptively (e.g. `2x4_36in`), containing a rectangular sketch
    on the XY plane, sized to the actual dressed dimensions for the chosen
    nominal size, extruded to the requested length.
- **Create Plywood Panel** opens a dialog with:
  - A dropdown of standard nominal thicknesses: `1/4`, `3/8`, `1/2`, `5/8`,
    `3/4`.
  - Width and length fields (default 48in x 96in, a full sheet), also
    accepting expressions like `24"` or `2'`.
  - On execution, creates (or adds another occurrence of) a component
    named descriptively (e.g. `ply_3-4in_24inx48in`), containing a
    rectangular sketch sized to the width/length you specify, extruded to
    the panel's actual sanded thickness.

The nominal-to-actual lookup tables live in
[`LumberGenerator/commands/lumber_sizes.py`](LumberGenerator/commands/lumber_sizes.py)
and
[`LumberGenerator/commands/plywood_sizes.py`](LumberGenerator/commands/plywood_sizes.py)
as plain dicts, so adding more sizes/thicknesses later is a one-line change.

## Cut lists

Lumber components are named `<nominal>_<length>` (e.g. `2x4_96in`);
plywood components are named `ply_<thickness>_<width>x<length>` (e.g.
`ply_3-4in_24inx48in`). Every piece with matching name-defining dimensions
reuses the same underlying component — creating a second `2x4` at 96in
doesn't make a new definition, it adds another occurrence of the existing
`2x4_96in` component (offset so repeats don't render on top of each other:
lumber stacks sideways, plywood stacks like a stack of sheets).

This matters because Fusion's Bill of Materials / Parts List groups and
counts by shared component, not by name text. To get an actual cut list
with quantities:

1. Create a **Drawing** from your design (**File -> New Drawing**, or from
   the Design workspace toolbar).
2. Insert a base view of your model.
3. Use **Table -> Parts List** (or **Table -> BOM**, depending on Fusion
   version) and select the view.
4. Fusion inserts a table listing each unique component with an
   auto-computed **QTY** column — that's your cut list.

You can also get the same grouped counts without a drawing via
**File -> Export -> Bill of Materials** (CSV) if your Fusion version
exposes it, or by reading component names/quantities from
**Manage -> Bill of Materials** if present in your workspace.

Note: because repeats of the same size share one component definition,
editing that component's sketch/extrude (e.g. to trim one board or panel)
changes every occurrence of that exact size. If you need to independently
adjust one specific piece later, right-click its occurrence in the browser
and use **Break Link** (or **Save As New Component**) to detach it into
its own definition first.

## Structure

```
LumberGenerator/
  LumberGenerator.py           # entry point (run/stop)
  LumberGenerator.manifest     # add-in manifest
  commands/
    __init__.py                # registers all commands
    common.py                  # shared UI registration + grouped-component/cut-list helpers
    create_lumber_command.py   # dialog + geometry creation for lumber
    lumber_sizes.py            # nominal -> actual dimension lookup table
    create_plywood_command.py  # dialog + geometry creation for plywood
    plywood_sizes.py           # nominal -> actual thickness lookup table
```

## Installing in Fusion 360

Fusion loads add-ins from its Add-Ins folder. Symlink (recommended, so `git
pull` updates show up immediately) or copy the `LumberGenerator/` folder
(the one containing `LumberGenerator.py` and `LumberGenerator.manifest`)
into that folder.

### macOS

Add-Ins folder:

```
~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/
```

Symlink from your cloned repo:

```bash
ln -s "$(pwd)/LumberGenerator" "$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/LumberGenerator"
```

### Windows

Add-Ins folder:

```
%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\
```

Symlink from your cloned repo. In **PowerShell**, `mklink` doesn't exist
(it's a `cmd.exe` builtin) and `%APPDATA%` doesn't expand there either —
use `New-Item` with `$env:APPDATA` instead:

```powershell
# Needs an elevated PowerShell, or Developer Mode enabled in Windows Settings
New-Item -ItemType SymbolicLink -Path "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns\LumberGenerator" -Target "C:\path\to\lumber_generator\LumberGenerator"

# No admin/Developer Mode needed:
New-Item -ItemType Junction -Path "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns\LumberGenerator" -Target "C:\path\to\lumber_generator\LumberGenerator"
```

If you're in `cmd.exe` instead of PowerShell, the original `mklink /D`
syntax works there:

```cmd
mklink /D "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\LumberGenerator" "C:\path\to\lumber_generator\LumberGenerator"
```

If none of that works for you, just copy the folder instead:

```powershell
Copy-Item -Recurse "C:\path\to\lumber_generator\LumberGenerator" "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns\LumberGenerator"
```

If you'd rather not deal with symlink permissions, just copy the
`LumberGenerator/` folder into the Add-Ins directory instead. You'll need to
re-copy it after making changes.

## Loading and running it in Fusion

1. Open Fusion 360.
2. Go to **Utilities** tab -> **Add-Ins** (or **Scripts and Add-Ins**, older
   UI).
3. Click the **Add-Ins** tab in the dialog.
4. `LumberGenerator` should appear in the list (Fusion scans the Add-Ins
   folder above). If it doesn't, click the green `+` next to "My Add-Ins"
   and browse to the `LumberGenerator` folder directly.
5. Select `LumberGenerator` and click **Run**. Optionally check **Run on
   Startup** if you want it to load automatically.
6. Switch to the **Design** workspace, **Solid** tab, and open the
   **ADD-INS** dropdown at the far right of the toolbar. You should see
   **Create Lumber Stock** and **Create Plywood Panel** listed there
   alongside "Scripts and Add-Ins..." and "Fusion App Store".
7. Click **Create Lumber Stock**, pick a nominal size and length, and hit
   **OK**. A new component should appear in the browser tree, named like
   `2x4_36in`.
8. Click **Create Plywood Panel**, pick a nominal thickness and a
   width/length, and hit **OK**. A new component should appear named like
   `ply_3-4in_24inx48in`.

### Iterating on changes

After editing any `.py` file, you don't need to reload the whole add-in from
the dialog every time — with **Run on Startup** unchecked, just select
`LumberGenerator` in the Add-Ins list and click **Stop**, then **Run** again
to pick up the changes. If Fusion's Python editor is open, its built-in
"Run" (green triangle) with the add-in file selected also works.
