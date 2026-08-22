"""Vectorized shape primitives that paint directly into a VoxelBuffer's grid."""

import numpy as np

from magicavoxel_mcp.voxel_buffer import VoxelBuffer


def _clip_box(shape: tuple[int, int, int], min_corner, max_corner):
    mins = [max(0, min(min_corner[i], max_corner[i])) for i in range(3)]
    maxs = [min(shape[i] - 1, max(min_corner[i], max_corner[i])) for i in range(3)]
    return mins, maxs


def fill_box(buffer: VoxelBuffer, min_corner, max_corner, color_index: int):
    """Fill an axis-aligned box (inclusive corners). Returns (count, coords)
    where coords is the (xs, ys, zs) index arrays of the voxels painted."""
    mins, maxs = _clip_box(buffer.shape, min_corner, max_corner)
    if any(mins[i] > maxs[i] for i in range(3)):
        empty = np.array([], dtype=np.intp)
        return 0, (empty, empty, empty)
    region = buffer.grid[mins[0]:maxs[0] + 1, mins[1]:maxs[1] + 1, mins[2]:maxs[2] + 1]
    count = region.size
    region[...] = color_index
    xs, ys, zs = np.meshgrid(
        np.arange(mins[0], maxs[0] + 1),
        np.arange(mins[1], maxs[1] + 1),
        np.arange(mins[2], maxs[2] + 1),
        indexing="ij",
    )
    return count, (xs.ravel(), ys.ravel(), zs.ravel())


def fill_sphere(buffer: VoxelBuffer, center, radius: float, color_index: int):
    """Fill a solid sphere. Returns (count, coords) where coords is the
    (xs, ys, zs) index arrays of the voxels painted."""
    shape = buffer.shape
    lo = [max(0, int(np.floor(center[i] - radius))) for i in range(3)]
    hi = [min(shape[i] - 1, int(np.ceil(center[i] + radius))) for i in range(3)]
    if any(lo[i] > hi[i] for i in range(3)):
        empty = np.array([], dtype=np.intp)
        return 0, (empty, empty, empty)

    xs = np.arange(lo[0], hi[0] + 1)
    ys = np.arange(lo[1], hi[1] + 1)
    zs = np.arange(lo[2], hi[2] + 1)
    dx = (xs - center[0])[:, None, None]
    dy = (ys - center[1])[None, :, None]
    dz = (zs - center[2])[None, None, :]
    mask = dx * dx + dy * dy + dz * dz <= radius * radius

    region = buffer.grid[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
    region[mask] = color_index

    local_xs, local_ys, local_zs = np.nonzero(mask)
    coords = (local_xs + lo[0], local_ys + lo[1], local_zs + lo[2])
    return int(mask.sum()), coords


def fill_cylinder(buffer: VoxelBuffer, center, radius: float, height: float, axis: str, color_index: int):
    """Fill a solid cylinder. `axis` is 'x', 'y', or 'z' — the axis the
    cylinder's height extends along, centered on `center` in the other two
    axes. Returns (count, coords) where coords is the (xs, ys, zs) index
    arrays of the voxels painted."""
    if axis not in ("x", "y", "z"):
        raise ValueError(f"axis must be 'x', 'y', or 'z', got {axis!r}")
    axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
    radial_idx = [i for i in range(3) if i != axis_idx]

    shape = buffer.shape
    lo = [0, 0, 0]
    hi = [0, 0, 0]
    lo[axis_idx] = max(0, int(np.floor(center[axis_idx] - height / 2)))
    hi[axis_idx] = min(shape[axis_idx] - 1, int(np.ceil(center[axis_idx] + height / 2)))
    for i in radial_idx:
        lo[i] = max(0, int(np.floor(center[i] - radius)))
        hi[i] = min(shape[i] - 1, int(np.ceil(center[i] + radius)))
    if any(lo[i] > hi[i] for i in range(3)):
        empty = np.array([], dtype=np.intp)
        return 0, (empty, empty, empty)

    coords = [np.arange(lo[i], hi[i] + 1) for i in range(3)]
    shape_bcast = [1, 1, 1]
    grids = []
    for i in range(3):
        s = list(shape_bcast)
        s[i] = len(coords[i])
        grids.append((coords[i] - center[i]).reshape(s))

    radial_sq = sum(grids[i] ** 2 for i in radial_idx)
    mask = radial_sq <= radius * radius
    mask = np.broadcast_to(mask, tuple(hi[i] - lo[i] + 1 for i in range(3)))

    region = buffer.grid[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
    region[mask] = color_index

    local_xs, local_ys, local_zs = np.nonzero(mask)
    result_coords = (local_xs + lo[0], local_ys + lo[1], local_zs + lo[2])
    return int(mask.sum()), result_coords
