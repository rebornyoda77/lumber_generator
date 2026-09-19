# LumberGenerator

A Fusion 360 add-in that generates dimensional lumber stock as Fusion
components. Pick a nominal size (e.g. `2x4`) and a length, and it creates a
new component sized to the actual S4S dressed dimensions (e.g. `2x4` ->
1.5in x 3.5in), extruded to the length you specify.

## What it does

- Adds a **Create Lumber Stock** button to the Solid workspace's
  Scripts and Add-Ins panel.
- Opens a dialog with:
  - A dropdown of standard nominal sizes: `2x4`, `2x6`, `2x8`, `2x10`,
    `2x12`, `4x4`, `1x2`, `1x4`, `1x6`, `1x8`.
  - A length field. It accepts Fusion's normal expression syntax, so you
    can type `36`, `36 in`, `3 ft`, or `8'`.
- On execution, creates a new component in the active design named
  descriptively (e.g. `2x4 - 36in`), containing a rectangular sketch on the
  XY plane, sized to the actual dressed dimensions for the chosen nominal
  size, extruded to the requested length.

The nominal-to-actual lookup table lives in
[`LumberGenerator/commands/lumber_sizes.py`](LumberGenerator/commands/lumber_sizes.py)
as a plain dict, so adding more sizes later is a one-line change.

## Structure

```
LumberGenerator/
  LumberGenerator.py          # entry point (run/stop)
  LumberGenerator.manifest    # add-in manifest
  commands/
    __init__.py               # registers all commands
    create_lumber_command.py  # dialog + geometry creation for the command
    lumber_sizes.py           # nominal -> actual dimension lookup table
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

Symlink from your cloned repo (run in an **elevated** Command Prompt or
PowerShell — creating symlinks on Windows requires admin rights or Developer
Mode enabled):

```cmd
mklink /D "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\LumberGenerator" "C:\path\to\fusion_add_on\LumberGenerator"
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
6. Switch to the **Design** workspace, **Solid** tab. You should see a new
   **Create Lumber Stock** button in the Scripts and Add-Ins panel (usually
   at the far right of the toolbar).
7. Click it, pick a nominal size and length, and hit **OK**. A new
   component should appear in the browser tree, named like `2x4 - 36in`.

### Iterating on changes

After editing any `.py` file, you don't need to reload the whole add-in from
the dialog every time — with **Run on Startup** unchecked, just select
`LumberGenerator` in the Add-Ins list and click **Stop**, then **Run** again
to pick up the changes. If Fusion's Python editor is open, its built-in
"Run" (green triangle) with the add-in file selected also works.
