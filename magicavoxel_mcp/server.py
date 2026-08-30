"""MCP server exposing voxel authoring tools. Holds one Session (active
VoxelBuffer, region handles, checkpoints) per server process (Milestone 1/2
scope: single session)."""

import os
import shutil
import subprocess
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import numpy as np
from mcp.server import MCPServer
from mcp.server.mcpserver import Context, Image

from magicavoxel_mcp.blender_render import render_views
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.contact_sheet import compose_contact_sheet
from magicavoxel_mcp.geometry import fill_box, fill_cylinder, fill_sphere
from magicavoxel_mcp.mesh_export import write_cube_mesh
from magicavoxel_mcp.session import Session
from magicavoxel_mcp.vox_io import read_vox, write_vox


def resolve_magicavoxel_exe(custom_path: str | None = None) -> str:
    if custom_path:
        return custom_path
    env_path = os.environ.get("MAGICAVOXEL_EXE") or os.environ.get("MAGICAVOXEL_MCP_APP_EXE")
    if env_path and os.path.exists(env_path):
        return env_path
    candidates = [
        r"C:\Users\ayush\Desktop\MagicaVoxel\MagicaVoxel-0.99.7.2-win64\MagicaVoxel.exe",
        os.path.expanduser(r"~\Desktop\MagicaVoxel\MagicaVoxel-0.99.7.2-win64\MagicaVoxel.exe"),
        r"C:\Program Files\MagicaVoxel\MagicaVoxel.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    which_path = shutil.which("MagicaVoxel") or shutil.which("magicavoxel")
    if which_path:
        return which_path
    raise RuntimeError(
        "Could not find MagicaVoxel.exe. Set MAGICAVOXEL_EXE environment variable or install it."
    )


@asynccontextmanager
async def lifespan(_server: MCPServer) -> AsyncIterator[Session]:
    yield Session()


server = MCPServer(
    name="magicavoxel-mcp",
    description="Create voxel art and export it as MagicaVoxel .vox files",
    lifespan=lifespan,
)


def _session(ctx: Context) -> Session:
    return ctx.request_context.lifespan_context


@server.tool()
def create_canvas(ctx: Context, width: int, depth: int, height: int) -> str:
    """Create a new empty voxel canvas, replacing any existing one. Dimensions
    must each be between 1 and 256 (MagicaVoxel's per-model limit).

    Coordinate convention (applies to this and every other tool that takes
    x/y/z): x = width (left/right), y = depth (into the screen), z = height
    (up). z is the vertical axis in renders — build tall things by growing z,
    not y.
    """
    _session(ctx).new_canvas(width, depth, height)
    return f"Created a {width}x{depth}x{height} (width x depth x height) canvas."


@server.tool()
def import_vox(ctx: Context, path: str) -> str:
    """Load an existing .vox file as the active canvas, replacing any
    existing one. Region handles from any prior canvas are discarded."""
    buffer = read_vox(path)
    _session(ctx).set_buffer(buffer)
    return f"Imported {buffer.shape[0]}x{buffer.shape[1]}x{buffer.shape[2]} canvas ({buffer.voxel_count()} voxels) from {path}."


@server.tool()
def set_voxel(ctx: Context, x: int, y: int, z: int, color_index: int) -> str:
    """Set a single voxel's color index (1-255; 0 means empty)."""
    buffer = _session(ctx).require_buffer()
    buffer.set_voxel(x, y, z, color_index)
    return f"Set voxel ({x}, {y}, {z}) to color {color_index}."


@server.tool()
def add_shape(
    ctx: Context,
    shape: str,
    color_index: int,
    center_x: int = 0,
    center_y: int = 0,
    center_z: int = 0,
    size_x: int = 1,
    size_y: int = 1,
    size_z: int = 1,
    radius: float = 1.0,
    height: float = 1.0,
    axis: str = "z",
) -> str:
    """Add a geometric primitive to the canvas.

    Coordinate convention: x = width (left/right), y = depth (into the
    screen), z = height (up) — use z for "tall", not y.

    shape: "box", "sphere", or "cylinder".
    For "box": uses center_x/y/z and size_x/y/z to build a box centered
    there. Centering is `min_corner = center - size // 2` (floor division —
    for even sizes this puts one more voxel below/behind center than
    above/in front) and `max_corner = min_corner + size - 1` (inclusive).
    For "sphere": uses center_x/y/z and radius. A voxel exactly `radius`
    away from center is included (inclusive boundary).
    For "cylinder": uses center_x/y/z, radius, height, and axis ("x"/"y"/"z"
    — the axis the cylinder stands along; "z" is upright). Boundary on both
    radius and height is inclusive.

    If the shape extends past the canvas edges, it's silently clipped — the
    returned message reports the clipped count when this happens; cross-check
    against list_regions/inspect_model if a voxel count looks lower than
    expected.

    Returns a region_id that can be passed to recolor_region/erase_region
    later to edit just this shape.
    """
    session = _session(ctx)
    buffer = session.require_buffer()
    center = (center_x, center_y, center_z)

    if shape == "box":
        min_corner = (center_x - size_x // 2, center_y - size_y // 2, center_z - size_z // 2)
        max_corner = (min_corner[0] + size_x - 1, min_corner[1] + size_y - 1, min_corner[2] + size_z - 1)
        count, coords, requested_count = fill_box(buffer, min_corner, max_corner, color_index)
    elif shape == "sphere":
        count, coords, requested_count = fill_sphere(buffer, center, radius, color_index)
    elif shape == "cylinder":
        count, coords, requested_count = fill_cylinder(buffer, center, radius, height, axis, color_index)
    else:
        raise ValueError(f"Unknown shape {shape!r}: expected 'box', 'sphere', or 'cylinder'")

    region_id = session.add_region(shape, color_index, coords)
    message = f"Painted {count} voxels for {shape} (region_id={region_id})."
    if count < requested_count:
        clipped = requested_count - count
        message += f" {clipped} of {requested_count} requested voxels fell outside the canvas bounds and were not painted."
    return message


@server.tool()
def carve_shape(
    ctx: Context,
    shape: str,
    center_x: int = 0,
    center_y: int = 0,
    center_z: int = 0,
    size_x: int = 1,
    size_y: int = 1,
    size_z: int = 1,
    radius: float = 1.0,
    height: float = 1.0,
    axis: str = "z",
) -> str:
    """Carve/subtract a 3D geometric volume out of the existing canvas (sets
    voxels to empty 0). Ideal for carving arches, doorways, windows, hollow
    interiors (rooms, pots, bowls), and organic sculpted cuts.

    Coordinate convention: x = width (left/right), y = depth (into screen),
    z = height (up).
    shape: "box", "sphere", or "cylinder".
    """
    session = _session(ctx)
    buffer = session.require_buffer()
    center = (center_x, center_y, center_z)

    grid_before = buffer.grid.copy()

    if shape == "box":
        min_corner = (center_x - size_x // 2, center_y - size_y // 2, center_z - size_z // 2)
        max_corner = (min_corner[0] + size_x - 1, min_corner[1] + size_y - 1, min_corner[2] + size_z - 1)
        count, coords, requested_count = fill_box(buffer, min_corner, max_corner, 0)
    elif shape == "sphere":
        count, coords, requested_count = fill_sphere(buffer, center, radius, 0)
    elif shape == "cylinder":
        count, coords, requested_count = fill_cylinder(buffer, center, radius, height, axis, 0)
    else:
        raise ValueError(f"Unknown shape {shape!r}: expected 'box', 'sphere', or 'cylinder'")

    xs, ys, zs = coords
    if len(xs) > 0:
        actually_carved = int(np.count_nonzero(grid_before[xs, ys, zs]))
    else:
        actually_carved = 0

    return f"Carved {actually_carved} voxels for {shape} (cleared {count} total canvas positions)."


@server.tool()
def stamp_vox(
    ctx: Context,
    path: str,
    offset_x: int = 0,
    offset_y: int = 0,
    offset_z: int = 0,
    rotation: int = 0,
) -> str:
    """Stamp an external .vox model (e.g. crafted by a child subagent or loaded
    from disk) into the active canvas at (offset_x, offset_y, offset_z).

    rotation: 0, 90, 180, or 270 degrees clockwise around the vertical Z-axis.
    Automatically aligns the base to the offset floor (auto_crop) and registers
    a new region_id so the stamped asset can be recolored or erased later.
    """
    session = _session(ctx)
    master_buffer = session.require_buffer()
    prop_buffer = read_vox(path)

    count, coords, target_size = paste_vox_buffer(
        master_buffer,
        prop_buffer,
        offset_x=offset_x,
        offset_y=offset_y,
        offset_z=offset_z,
        rotation=rotation,
        auto_crop=True,
    )

    region_id = session.add_region(f"stamp:{os.path.basename(path)}", color_index=0, coords=coords)
    return (
        f"Stamped {count} voxels from {path} at ({offset_x}, {offset_y}, {offset_z}) "
        f"[rot={rotation}°, size={target_size[0]}x{target_size[1]}x{target_size[2]}] "
        f"(region_id={region_id})."
    )


@server.tool()
def recolor_region(ctx: Context, region_id: int, color_index: int) -> str:
    """Recolor all voxels belonging to a region returned by add_shape."""
    count = _session(ctx).recolor_region(region_id, color_index)
    return f"Recolored {count} voxels in region {region_id} to color {color_index}."


@server.tool()
def erase_region(ctx: Context, region_id: int) -> str:
    """Erase (set to empty) all voxels belonging to a region returned by
    add_shape. The region_id is then no longer valid."""
    count = _session(ctx).erase_region(region_id)
    return f"Erased {count} voxels in region {region_id}."


@server.tool()
def list_regions(ctx: Context) -> str:
    """List all active region ids with their shape kind, color, and voxel
    count — use this to recall region ids for recolor_region/erase_region."""
    regions = _session(ctx).list_regions()
    if not regions:
        return "No active regions."
    lines = [
        f"region_id={r.id} kind={r.kind} color_index={r.color_index} voxel_count={r.voxel_count}"
        for r in regions
    ]
    return "\n".join(lines)


@server.tool()
def apply_palette(ctx: Context, entries: list[list[int]]) -> str:
    """Set palette colors. `entries` is a list of [index, r, g, b] or
    [index, r, g, b, a] (a defaults to 255), index 0-255."""
    buffer = _session(ctx).require_buffer()
    for entry in entries:
        if len(entry) == 4:
            index, r, g, b = entry
            a = 255
        elif len(entry) == 5:
            index, r, g, b, a = entry
        else:
            raise ValueError(f"Each palette entry must have 4 or 5 values, got {entry!r}")
        buffer.set_palette_entry(index, r, g, b, a)
    return f"Updated {len(entries)} palette entries."


@server.tool()
def save_checkpoint(ctx: Context, name: str) -> str:
    """Save a named snapshot of the current canvas (grid, palette, and
    regions) that can be restored later with restore_checkpoint."""
    _session(ctx).save_checkpoint(name)
    return f"Saved checkpoint {name!r}."


@server.tool()
def restore_checkpoint(ctx: Context, name: str) -> str:
    """Restore the canvas (grid, palette, and regions) to a previously saved
    checkpoint, discarding any changes made since."""
    _session(ctx).restore_checkpoint(name)
    return f"Restored checkpoint {name!r}."


@server.tool()
def export_vox(ctx: Context, path: str) -> str:
    """Write the current canvas to a .vox file at the given path."""
    buffer = _session(ctx).require_buffer()
    write_vox(buffer, path)
    return f"Wrote {buffer.voxel_count()} voxels to {path}."


@server.tool()
def render(
    ctx: Context,
    views: list[str] | None = None,
    image_size: int = 512,
    lighting: str = "neutral",
    engine: str = "cycles",
) -> Image:
    """Render the current canvas and return an image so you can visually
    check the model. By default, renders a single "hero" perspective 3/4
    angle — the most useful one for judging how something actually looks.

    Pass `views` to see something else instead — perspective vantage points
    (real depth, like actually looking at it): "hero" (alias for
    hero_front_right), "hero_front_right", "hero_front_left",
    "hero_back_right", "hero_back_left", "hero_top" (steep aerial 3/4),
    "hero_low" (low dramatic angle); or orthographic axis views (flatten
    depth, useful only for verifying exact geometry/alignment): "front",
    "back", "left", "right", "top". Passing more than one view returns a
    single labeled contact-sheet image tiling all of them together, rather
    than one image per view.

    lighting: "neutral" (default, flat studio lighting — best for judging
    shape/color) or "night" (dark ambient, warm low key light, cool blue rim
    fill — for moody night scenes). This is a global mood approximation, not
    real light sources tied to lanterns/neon/etc. in the model.

    engine: "cycles" (default, path-traced MagicaVoxel aesthetic with soft
    shadows, ambient ground catcher, and voxel edge bevels) or "eevee"
    (ultra-fast rasterized preview).

    The camera always auto-fits the entire scene's bounding box — there is
    no occlusion check, so any shape sitting between the camera and the rest
    of the model (e.g. a wall placed on the camera-facing side rather than
    the back) will block the view with no warning; if a render looks
    unexpectedly blank, check for enclosing geometry on the near side and
    try a different hero angle. The same auto-fit also scales to the full
    extent of whatever is in the canvas, so a large element (e.g. a
    room-scale floor) combined with a small one will shrink the small
    element to a sliver — check inspect_model's bounding box first if the
    canvas mixes very different scales.
    """
    buffer = _session(ctx).require_buffer()
    if views is None:
        views = ["hero"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        obj_path = f"{tmp_dir}/model.obj"
        write_cube_mesh(buffer, obj_path)
        view_paths = render_views(
            obj_path,
            tmp_dir,
            views,
            image_size=image_size,
            lighting=lighting,
            engine=engine,
        )

        if len(view_paths) == 1:
            (output_path,) = view_paths.values()
        else:
            output_path = f"{tmp_dir}/contact_sheet.png"
            compose_contact_sheet(view_paths, output_path)

        with open(output_path, "rb") as f:
            sheet_bytes = f.read()
    return Image(data=sheet_bytes, format="png")


@server.tool()
def open_in_magicavoxel(ctx: Context, vox_path: str | None = None) -> str:
    """Open the current canvas (or an existing .vox file) in the installed
    desktop MagicaVoxel application for native interaction and GPU path-traced rendering.
    """
    exe = resolve_magicavoxel_exe()
    app_dir = os.path.dirname(exe)

    if vox_path is None:
        buffer = _session(ctx).require_buffer()
        vox_dir = os.path.join(app_dir, "vox")
        if os.path.isdir(vox_dir):
            target_path = os.path.join(vox_dir, "mcp_model.vox")
        else:
            target_path = os.path.abspath("mcp_model.vox")
        write_vox(buffer, target_path)
    else:
        target_path = os.path.abspath(vox_path)
        if not os.path.exists(target_path):
            raise ValueError(f"File {target_path} does not exist")

    subprocess.Popen([exe, target_path], cwd=app_dir)
    return f"Opened {target_path} in MagicaVoxel ({exe})."


@server.tool()
def inspect_model(ctx: Context) -> str:
    """Return a text summary of the current canvas: dimensions, voxel count,
    and bounding box of non-empty voxels."""
    buffer = _session(ctx).require_buffer()
    bbox = buffer.bounding_box()
    bbox_str = f"{bbox[0]} to {bbox[1]}" if bbox else "empty"
    return (
        f"Canvas size: {buffer.shape[0]}x{buffer.shape[1]}x{buffer.shape[2]}. "
        f"Voxel count: {buffer.voxel_count()}. Bounding box: {bbox_str}."
    )


from magicavoxel_mcp.scene import Scene, Component


@server.tool()
def compile_scene(
    ctx: Context,
    script_path: str,
    checkpoint_name: str | None = None,
) -> str:
    """Execute a declarative Scene-as-Code Python script, compile its components
    into the active session VoxelBuffer, and optionally save a milestone checkpoint.
    """
    abs_path = os.path.abspath(script_path)
    if not os.path.exists(abs_path):
        raise ValueError(f"Scene script '{abs_path}' does not exist.")

    session = _session(ctx)

    # Execution context with pre-imported engine classes
    local_scope: dict = {
        "Scene": Scene,
        "Component": Component,
    }
    
    with open(abs_path, "r", encoding="utf-8") as f:
        code_str = f.read()

    # Execute the declarative script
    exec(code_str, local_scope)

    # Locate the Scene object or VoxelBuffer in script globals
    scene_obj: Scene | None = None
    buffer_obj = None

    if "scene" in local_scope and isinstance(local_scope["scene"], Scene):
        scene_obj = local_scope["scene"]
    elif "build_scene" in local_scope and callable(local_scope["build_scene"]):
        res = local_scope["build_scene"]()
        if isinstance(res, Scene):
            scene_obj = res
        elif hasattr(res, "grid") and hasattr(res, "palette"):
            buffer_obj = res

    if scene_obj is not None:
        compiled_buf = scene_obj.compile()
        session.buffer = compiled_buf
        comp_count = len(scene_obj.components)
        summary = (
            f"Compiled Scene '{scene_obj.name}' ({compiled_buf.shape[0]}x{compiled_buf.shape[1]}x{compiled_buf.shape[2]}) "
            f"with {comp_count} component(s) -> {compiled_buf.voxel_count()} total voxels."
        )
    elif buffer_obj is not None:
        session.buffer = buffer_obj
        summary = (
            f"Compiled buffer ({buffer_obj.shape[0]}x{buffer_obj.shape[1]}x{buffer_obj.shape[2]}) "
            f"-> {buffer_obj.voxel_count()} total voxels."
        )
    else:
        # Check if any Scene instance was created in local_scope
        for val in local_scope.values():
            if isinstance(val, Scene):
                scene_obj = val
                break
        if scene_obj is not None:
            compiled_buf = scene_obj.compile()
            session.buffer = compiled_buf
            summary = (
                f"Compiled Scene '{scene_obj.name}' ({compiled_buf.shape[0]}x{compiled_buf.shape[1]}x{compiled_buf.shape[2]}) "
                f"with {len(scene_obj.components)} component(s) -> {compiled_buf.voxel_count()} total voxels."
            )
        else:
            raise ValueError(
                "Scene script must define a `scene = Scene(...)` instance or a `build_scene() -> Scene` function."
            )

    if checkpoint_name:
        session.save_checkpoint(checkpoint_name)
        summary += f" Saved checkpoint '{checkpoint_name}'."

    return summary


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()

