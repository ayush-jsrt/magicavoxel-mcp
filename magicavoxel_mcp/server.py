"""MCP server exposing voxel authoring tools. Holds one active VoxelBuffer per
server process (Milestone 1 scope: single session, single active model)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from magicavoxel_mcp.geometry import fill_box, fill_cylinder, fill_sphere
from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.vox_io import write_vox


@dataclass
class AppState:
    buffer: VoxelBuffer | None = None


@asynccontextmanager
async def lifespan(_server: MCPServer) -> AsyncIterator[AppState]:
    yield AppState()


server = MCPServer(
    name="magicavoxel-mcp",
    description="Create voxel art and export it as MagicaVoxel .vox files",
    lifespan=lifespan,
)


def _require_buffer(ctx: Context) -> VoxelBuffer:
    state: AppState = ctx.request_context.lifespan_context
    if state.buffer is None:
        raise ValueError("No active canvas — call create_canvas first")
    return state.buffer


@server.tool()
def create_canvas(ctx: Context, width: int, height: int, depth: int) -> str:
    """Create a new empty voxel canvas, replacing any existing one. Dimensions
    must each be between 1 and 256 (MagicaVoxel's per-model limit)."""
    state: AppState = ctx.request_context.lifespan_context
    state.buffer = VoxelBuffer(width, height, depth)
    return f"Created a {width}x{height}x{depth} canvas."


@server.tool()
def set_voxel(ctx: Context, x: int, y: int, z: int, color_index: int) -> str:
    """Set a single voxel's color index (1-255; 0 means empty)."""
    buffer = _require_buffer(ctx)
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
    """
    buffer = _require_buffer(ctx)
    center = (center_x, center_y, center_z)

    if shape == "box":
        min_corner = (center_x - size_x // 2, center_y - size_y // 2, center_z - size_z // 2)
        max_corner = (min_corner[0] + size_x - 1, min_corner[1] + size_y - 1, min_corner[2] + size_z - 1)
        count = fill_box(buffer, min_corner, max_corner, color_index)
    elif shape == "sphere":
        count = fill_sphere(buffer, center, radius, color_index)
    elif shape == "cylinder":
        count = fill_cylinder(buffer, center, radius, height, axis, color_index)
    else:
        raise ValueError(f"Unknown shape {shape!r}: expected 'box', 'sphere', or 'cylinder'")

    return f"Painted {count} voxels for {shape}."


@server.tool()
def apply_palette(ctx: Context, entries: list[list[int]]) -> str:
    """Set palette colors. `entries` is a list of [index, r, g, b] or
    [index, r, g, b, a] (a defaults to 255), index 0-255."""
    buffer = _require_buffer(ctx)
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
def export_vox(ctx: Context, path: str) -> str:
    """Write the current canvas to a .vox file at the given path."""
    buffer = _require_buffer(ctx)
    write_vox(buffer, path)
    return f"Wrote {buffer.voxel_count()} voxels to {path}."


@server.tool()
def inspect_model(ctx: Context) -> str:
    """Return a text summary of the current canvas: dimensions, voxel count,
    and bounding box of non-empty voxels."""
    buffer = _require_buffer(ctx)
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
