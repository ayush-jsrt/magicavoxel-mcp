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

1. Agent calls `create_canvas` / `add_shape` / `set_voxel` repeatedly to build a model.
2. `export_vox` serializes the buffer to a `.vox` file.
3. `render` writes a companion mesh, shells out to headless Blender, waits, and
   returns the resulting PNG as an MCP image content block — so a vision-capable
   host sees the render directly in context.
4. Agent critiques the image and issues more shape/voxel edits; repeat.
5. Optionally, `open_in_magicavoxel` launches the real app for manual finishing.

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

- [ ] Locate or install MagicaVoxel.exe on this machine.
- [ ] Scaffold core library: `VoxelBuffer`, geometry primitives, `.vox` writer/reader.
- [ ] Scaffold MCP server (`FastMCP`) wrapping the core library.
- [ ] Blender headless render script (mesh-from-cubes importer, camera/light setup).
- [ ] Sandbox design for `run_voxel_script`.
