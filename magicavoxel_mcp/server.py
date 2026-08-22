"""MCP server exposing voxel authoring tools. Holds one Session (active
VoxelBuffer, region handles, checkpoints) per server process (Milestone 1/2
scope: single session)."""

import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server import MCPServer
from mcp.server.mcpserver import Context, Image

from magicavoxel_mcp.blender_render import render_views
from magicavoxel_mcp.contact_sheet import compose_contact_sheet
from magicavoxel_mcp.geometry import fill_box, fill_cylinder, fill_sphere
from magicavoxel_mcp.mesh_export import write_cube_mesh
from magicavoxel_mcp.session import Session
from magicavoxel_mcp.vox_io import read_vox, write_vox


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
def create_canvas(ctx: Context, width: int, height: int, depth: int) -> str:
    """Create a new empty voxel canvas, replacing any existing one. Dimensions
    must each be between 1 and 256 (MagicaVoxel's per-model limit)."""
    _session(ctx).new_canvas(width, height, depth)
    return f"Created a {width}x{height}x{depth} canvas."


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

    shape: "box", "sphere", or "cylinder".
    For "box": uses center_x/y/z and size_x/y/z to build a box centered there.
    For "sphere": uses center_x/y/z and radius.
    For "cylinder": uses center_x/y/z, radius, height, and axis ("x"/"y"/"z").

    Returns a region_id that can be passed to recolor_region/erase_region
    later to edit just this shape.
    """
    session = _session(ctx)
    buffer = session.require_buffer()
    center = (center_x, center_y, center_z)

    if shape == "box":
        min_corner = (center_x - size_x // 2, center_y - size_y // 2, center_z - size_z // 2)
        max_corner = (min_corner[0] + size_x - 1, min_corner[1] + size_y - 1, min_corner[2] + size_z - 1)
        count, coords = fill_box(buffer, min_corner, max_corner, color_index)
    elif shape == "sphere":
        count, coords = fill_sphere(buffer, center, radius, color_index)
    elif shape == "cylinder":
        count, coords = fill_cylinder(buffer, center, radius, height, axis, color_index)
    else:
        raise ValueError(f"Unknown shape {shape!r}: expected 'box', 'sphere', or 'cylinder'")

    region_id = session.add_region(shape, color_index, coords)
    return f"Painted {count} voxels for {shape} (region_id={region_id})."


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
def render(ctx: Context, views: list[str] | None = None, image_size: int = 512) -> Image:
    """Render the current canvas and return an image so you can visually
    check the model. By default, renders a single "hero" perspective 3/4
    angle — the most useful one for judging how something actually looks.

    Pass `views` to see something else instead: a subset of "hero", "front",
    "back", "left", "right", "top" (the latter five are orthographic axis
    views — useful for verifying exact geometry, but they flatten depth).
    Passing more than one view returns a single labeled contact-sheet image
    tiling all of them together, rather than one image per view.
    """
    buffer = _session(ctx).require_buffer()
    if views is None:
        views = ["hero"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        obj_path = f"{tmp_dir}/model.obj"
        write_cube_mesh(buffer, obj_path)
        view_paths = render_views(obj_path, tmp_dir, views, image_size=image_size)

        if len(view_paths) == 1:
            (output_path,) = view_paths.values()
        else:
            output_path = f"{tmp_dir}/contact_sheet.png"
            compose_contact_sheet(view_paths, output_path)

        with open(output_path, "rb") as f:
            sheet_bytes = f.read()
    return Image(data=sheet_bytes, format="png")


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


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
