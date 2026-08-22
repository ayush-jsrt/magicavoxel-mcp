# magicavoxel-mcp

An MCP (Model Context Protocol) server that lets an LLM agent create voxel
art programmatically and export it as real MagicaVoxel `.vox` files — build
shapes, edit specific parts after the fact, and render multi-angle previews,
all without MagicaVoxel itself needing to be scriptable (it isn't).

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design
rationale and decision log.

## Features

- **Voxel authoring** — build models from box/sphere/cylinder primitives or
  set individual voxels, up to MagicaVoxel's 256×256×256 per-model limit.
- **Region-based editing** — every shape you add returns a `region_id` you
  can recolor or erase later without re-deriving its coordinates.
- **Checkpoints** — snapshot the canvas and roll back to it, so an agent can
  try something and safely undo it.
- **`.vox` import/export** — reads and writes the real MagicaVoxel file
  format (hand-implemented from the
  [official spec](https://github.com/ephtracy/voxel-model), not a
  third-party library), so files open directly in MagicaVoxel.
- **Multi-angle rendering** — renders the model from several angles in
  headless [Blender](https://www.blender.org/) and returns one combined,
  labeled image, so a vision-capable agent can actually see what it built.

## Requirements

- **Python 3.11+**
- **[Blender](https://www.blender.org/download/)** (4.x) — required only for
  the `render` tool. Not needed for voxel authoring or `.vox` export/import.
- **[MagicaVoxel](https://ephtracy.github.io/)** — optional. Not required by
  the server at all; useful if you want to open the files it produces in the
  actual editor.

## Installation

1. Clone this repository and `cd` into it.
2. Create and activate a virtual environment (Python 3.11+):

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

   (or with conda: `conda create -n magicavoxel-mcp python=3.11 && conda activate magicavoxel-mcp`)

3. Install the package and its dependencies:

   ```powershell
   pip install -e .
   ```

   For running the test suite, also install dev dependencies:

   ```powershell
   pip install -r requirements-dev.txt
   ```

4. If you want to use the `render` tool, make sure Blender is discoverable.
   The server looks for it in this order:
   1. Explicit path passed in code (not applicable via MCP tool calls)
   2. The `MAGICAVOXEL_MCP_BLENDER_EXE` environment variable
   3. `blender` on your system `PATH`

   Example (PowerShell), if Blender isn't on `PATH`:

   ```powershell
   $env:MAGICAVOXEL_MCP_BLENDER_EXE = "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
   ```

   Set this permanently via your OS environment variables, or in whatever
   config launches the MCP server (see below), if you don't want to set it
   per-shell-session.

## Verifying the install

Run the test suite:

```powershell
pytest
```

If Blender isn't configured, the Blender-dependent tests are skipped
automatically rather than failing.

You can also sanity-check the server starts:

```powershell
python -m magicavoxel_mcp.server
```

This starts the server on stdio and will appear to hang with no output —
that's expected, since it's waiting for an MCP client to connect. Press
Ctrl+C to stop it. It isn't meant to be run standalone like this in normal
use; see the next section.

## Connecting an MCP client

This server communicates over stdio, so any MCP-compatible host (Claude
Code, Claude Desktop, Cursor, etc.) can run and talk to it directly — you
don't run it manually yourself. Copy [`.mcp.json.example`](.mcp.json.example)
to `.mcp.json` and fill in the two paths for your machine:

```json
{
  "mcpServers": {
    "magicavoxel": {
      "command": "C:\\path\\to\\your\\venv-or-conda-env\\python.exe",
      "args": ["-m", "magicavoxel_mcp.server"],
      "env": {
        "MAGICAVOXEL_MCP_BLENDER_EXE": "C:\\path\\to\\Blender\\blender.exe"
      }
    }
  }
}
```

`command` should be the Python interpreter from the environment you
installed into. `.mcp.json` itself is gitignored (paths are machine-specific)
— only the `.example` file is committed.

For Claude Code specifically, a project-level `.mcp.json` is picked up
automatically (you may need to run `/mcp reconnect` or restart the session);
it can also be registered with `claude mcp add`. Consult your client's
documentation for the exact config file location and format.

## Available tools

| Tool | Description |
|---|---|
| `create_canvas(width, height, depth)` | Start a new empty canvas (each dimension 1-256). |
| `import_vox(path)` | Load an existing `.vox` file as the active canvas. |
| `set_voxel(x, y, z, color_index)` | Set a single voxel (color_index 1-255; 0 is empty). |
| `add_shape(shape, color_index, ...)` | Paint a `"box"`, `"sphere"`, or `"cylinder"`. Returns a `region_id`. |
| `recolor_region(region_id, color_index)` | Recolor all voxels in a previously added shape. |
| `erase_region(region_id)` | Clear all voxels in a previously added shape. |
| `list_regions()` | List active region ids with their kind, color, and voxel count. |
| `apply_palette(entries)` | Set palette colors: `[index, r, g, b]` or `[index, r, g, b, a]`. |
| `save_checkpoint(name)` / `restore_checkpoint(name)` | Snapshot and roll back the canvas. |
| `export_vox(path)` | Write the canvas to a `.vox` file. |
| `render(views, image_size)` | Render `"front"/"back"/"left"/"right"/"top"` views (default: front, right, top) as one contact-sheet image. |
| `inspect_model()` | Text summary: dimensions, voxel count, bounding box. |

Regions are paint-time snapshots — if a later shape overlaps and repaints
voxels from an earlier one, recoloring/erasing the earlier region still
affects them. See `docs/ARCHITECTURE.md` for details and other known
limitations.

## Not yet implemented

- `open_in_magicavoxel` convenience tool (launching the real app on a file)
- Mirror/rotate/array operations, true CSG boolean subtract
- MagicaVoxel scene-graph chunks (`nTRN`/`nGRP`/`nSHP`) — only single-model files are supported
- A sandboxed `run_voxel_script` tool for agent-authored procedural generation

## Development

- Core logic lives in `magicavoxel_mcp/` and has no MCP dependency — it's
  plain, importable Python (`VoxelBuffer`, geometry primitives, `.vox`
  reader/writer, mesh export, Blender render wrapper) usable from scripts
  outside an agent context. `magicavoxel_mcp/server.py` is a thin MCP layer
  on top of it.
- Tests live in `tests/`, including a real in-memory MCP client/server
  session test (`tests/test_server_e2e.py`) and a real-fixture compatibility
  test against a genuine MagicaVoxel-authored file.
- Run `pytest -v` for verbose output.
