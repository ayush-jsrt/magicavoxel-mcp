# magicavoxel-mcp — Architecture & Decisions

Living design doc. Update this as decisions are made or revised — treat it as the
source of truth for *why* things are built the way they are, not just what exists.

## Goal

An MCP server that lets an LLM agent (and other tooling) generate voxel art,
serialize it to real `.vox` files, and render it — without requiring MagicaVoxel
itself to be scriptable (it isn't; it's closed-source freeware with no CLI/API).

## Layering

```
LLM Agent (Claude/etc.) ──[MCP tools]──> MCP server (thin wrapper)
                                              │
                                        core library (plain Python,
                                        no MCP dependency — importable
                                        standalone from scripts/CI/etc.)
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                 VoxelBuffer            vox_writer/reader      renderer
                 (numpy grid +          (.vox chunk format,    (shells out to
                 palette, geometry      hand-rolled from       Blender headless)
                 primitives)            official spec)
```

The core library has **no MCP dependency** on purpose — the same code should be
usable from a plain script, a batch job, or a different agent host, not just via
MCP tool calls.

## Key decisions

- **Hand-roll the `.vox` writer/reader** against the official format spec from
  [`ephtracy/voxel-model`](https://github.com/ephtracy/voxel-model) (the
  MagicaVoxel author's own repo — `MagicaVoxel-file-format-vox.txt` and
  `-extension.txt` for scene graph / material chunks), using stdlib `struct`.
  Rejected third-party libs (`pyvox`, `voxelfuse`) as unmaintained/niche —
  avoid depending on them for a format this simple.
- **The RGBA chunk's index offset (voxel color `i` → chunk entry `i-1`) was
  documented here from the start but not actually implemented until it
  shipped a real bug**: custom palettes (via `apply_palette`) rendered wrong
  colors in real MagicaVoxel, while our own round-trip tests still passed —
  self-consistent write+read can't catch a shift both sides skip identically.
  Caught by visually inspecting a real build in MagicaVoxel (a ramen cart
  diorama built through the live MCP session), not by any automated test.
  Fixed in `vox_io.py`, with a
  new regression test that parses the raw RGBA chunk bytes independently of
  our own reader. Lesson: for format-compliance facts like this, a test that
  only exercises our own writer against our own reader is not sufficient —
  needs either a byte-level spec check or the real external tool.
- **Rendering via headless Blender, not MagicaVoxel itself.** MagicaVoxel has no
  CLI render mode, so it can't be part of an automated agent loop. Blender
  (`blender --background --python ...`) is the actual render backend.
- **Avoid third-party Blender `.vox`-import addons.** Instead, the writer also
  emits a plain mesh (`.obj`/`.glb`) of cubes directly from the voxel buffer, so
  Blender can import it with zero addons — one less unmaintained dependency.
- **MagicaVoxel is optional**, used only by a manual `open_in_magicavoxel`
  convenience tool (launches the real app on the generated `.vox` file for
  hand-tweaking / native path-traced render). It is *not* part of the automated
  render/capture loop.
- **`run_voxel_script` (LLM-generated NumPy code) is a code-execution surface**
  — must run sandboxed (subprocess, restricted builtins, timeout, no
  filesystem/network access), never a raw `exec()`.
- **256³ voxel grid limit** — enforce this in `create_canvas`, matching
  MagicaVoxel's actual per-model limit, rather than failing on import later.
- **Tool/app paths are configurable**, not hardcoded — install locations vary
  per machine (see Environment below for this machine's current paths).

## Render/capture loop (the agentic feedback cycle)

1. Agent calls `create_canvas`/`import_vox` / `add_shape` / `set_voxel` /
   `recolor_region` / `erase_region` repeatedly to build or edit a model.
2. `render` (implemented — see below) writes a companion mesh, shells out to
   headless Blender, and returns a single contact-sheet image (multiple
   angles tiled into one PNG) as an MCP image content block, so a
   vision-capable host sees the render directly in context.
3. Agent critiques the image and issues more edits; `save_checkpoint`/
   `restore_checkpoint` give it a safe way to back out of a bad attempt.
4. `export_vox` serializes the buffer to a `.vox` file when done.
5. Optionally, `open_in_magicavoxel` (not yet built) would launch the real app
   for manual finishing.

### Render pipeline internals (Milestone 2)

- `mesh_export.write_cube_mesh` converts the voxel grid to an OBJ+MTL mesh,
  emitting only exterior faces (6 numpy-shifted neighbor comparisons, not a
  per-voxel loop) grouped into one material per color actually used.
- `blender_scripts/render_views.py` runs inside Blender's own Python
  (`--background --python ... --`), imports the mesh via
  `bpy.ops.wm.obj_import(up_axis='Z', forward_axis='Y')` — verified against
  the actually-installed Blender 4.2.3, which removed the older
  `import_scene.obj` operator — recalculates normals (so the OBJ writer's
  winding order doesn't need to be outward-consistent), and renders each
  requested orthographic view with `BLENDER_EEVEE_NEXT` (Eevee was renamed in
  4.2; the older `BLENDER_EEVEE` id no longer exists).
- `blender_render.render_views` shells out to that script and resolves the
  Blender executable from an explicit argument, then
  `MAGICAVOXEL_MCP_BLENDER_EXE`, then `PATH` — never hardcoded.
- `contact_sheet.compose_contact_sheet` tiles the per-view PNGs into one
  labeled image via Pillow. The `render` tool returns this single combined
  image rather than multiple content blocks, sidestepping the need to verify
  whether this `mcp` version's tool-return conversion supports a list of
  `Image` objects.
- Verified end-to-end: unit tests on mesh face-culling, a real-Blender
  integration test asserting non-blank output, a real in-memory MCP session
  test exercising the `render` tool's `Image` conversion, and a manual visual
  check with an asymmetric test model confirming no axis flip/rotation bugs.

### Region handles (Milestone 2)

`add_shape` returns a `region_id` (from `session.Session`, which also holds
checkpoints) that `recolor_region`/`erase_region` can act on later, so a part
built earlier can be targeted without re-deriving its coordinates. Regions are
paint-time snapshots of which voxels a shape call touched — if a later shape
overlaps and repaints those cells, recoloring/erasing the earlier region still
affects them (no z-order/last-writer tracking; would need a real scene graph
to fix properly).

## Environment

- Conda env: `magicavoxel-mcp` (Python 3.11), created via
  `conda create -n magicavoxel-mcp python=3.11`.
- Python deps: see [`requirements.txt`](../requirements.txt) (`mcp`, `numpy`,
  `opensimplex`, `Pillow`).
- External apps found on this dev machine (paths will differ elsewhere — make
  these configurable, not assumed):
  - Blender: `C:\Program Files\Blender Foundation\Blender 4.2\blender.exe`
  - MagicaVoxel: **not installed** on this machine (confirmed via full `C:\`
    scan — no `MagicaVoxel.exe` found). Only a leftover `Voxel Models` output
    folder exists at `C:\Users\ayush\Desktop\MagicaVoxel\Voxel Models` from a
    prior install. Not required for the automated agent loop (see above) —
    only needed if/when the `open_in_magicavoxel` convenience tool is wired up.

## Open TODOs

- [x] Locate or install MagicaVoxel.exe on this machine (installed at
      `C:\Users\ayush\Desktop\MagicaVoxel\MagicaVoxel-0.99.7.2-win64\MagicaVoxel.exe`).
- [x] Scaffold core library: `VoxelBuffer`, geometry primitives, `.vox` writer/reader.
- [x] Scaffold MCP server (`MCPServer` from `mcp.server` — not `FastMCP`,
      which doesn't exist in the installed `mcp==2.0.0`) wrapping the core library.
- [x] Blender headless render script (mesh-from-cubes importer, camera/light setup).
- [x] Region handles + checkpoint/restore (`session.py`).
- [x] `import_vox` tool.
- [ ] Sandbox design for `run_voxel_script`.
- [ ] `open_in_magicavoxel` convenience tool.
- [ ] Mirror/rotate/array ops, true CSG boolean subtract, MagicaVoxel scene-graph chunks (`nTRN`/`nGRP`/`nSHP`) — all explicitly deferred past Milestone 2.
