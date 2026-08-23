"""Vectorized shape primitives that paint directly into a VoxelBuffer's grid."""

import numpy as np

from magicavoxel_mcp.voxel_buffer import VoxelBuffer


def _clip_box(shape: tuple[int, int, int], min_corner, max_corner):
    mins = [max(0, min(min_corner[i], max_corner[i])) for i in range(3)]
    maxs = [min(shape[i] - 1, max(min_corner[i], max_corner[i])) for i in range(3)]
    return mins, maxs


def fill_box(buffer: VoxelBuffer, min_corner, max_corner, color_index: int):
    """Fill an axis-aligned box (inclusive corners — both min_corner and
    max_corner are painted). Returns (count, coords, requested_count):
    coords is the (xs, ys, zs) index arrays of the voxels actually painted;
    requested_count is how many voxels the box would cover with no canvas
    bounds at all, so callers can detect clipping via
    `requested_count - count`."""
    lo = [min(min_corner[i], max_corner[i]) for i in range(3)]
    hi = [max(min_corner[i], max_corner[i]) for i in range(3)]
    requested_count = (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1)

    mins, maxs = _clip_box(buffer.shape, min_corner, max_corner)
    if any(mins[i] > maxs[i] for i in range(3)):
        empty = np.array([], dtype=np.intp)
        return 0, (empty, empty, empty), requested_count
    region = buffer.grid[mins[0]:maxs[0] + 1, mins[1]:maxs[1] + 1, mins[2]:maxs[2] + 1]
    count = region.size
    region[...] = color_index
    xs, ys, zs = np.meshgrid(
        np.arange(mins[0], maxs[0] + 1),
        np.arange(mins[1], maxs[1] + 1),
        np.arange(mins[2], maxs[2] + 1),
        indexing="ij",
    )
    return count, (xs.ravel(), ys.ravel(), zs.ravel()), requested_count


def fill_sphere(buffer: VoxelBuffer, center, radius: float, color_index: int):
    """Fill a solid sphere (inclusive boundary — a voxel exactly `radius`
    away from `center` is painted, since the test is `<= radius**2`).
    Returns (count, coords, requested_count): coords is the (xs, ys, zs)
    index arrays of the voxels actually painted; requested_count is how many
    voxels the sphere would cover with no canvas bounds at all, so callers
    can detect clipping via `requested_count - count`."""
    shape = buffer.shape
    lo_unclamped = [int(np.floor(center[i] - radius)) for i in range(3)]
    hi_unclamped = [int(np.ceil(center[i] + radius)) for i in range(3)]
    lo = [max(0, lo_unclamped[i]) for i in range(3)]
    hi = [min(shape[i] - 1, hi_unclamped[i]) for i in range(3)]

    xs_full = np.arange(lo_unclamped[0], hi_unclamped[0] + 1)
    ys_full = np.arange(lo_unclamped[1], hi_unclamped[1] + 1)
    zs_full = np.arange(lo_unclamped[2], hi_unclamped[2] + 1)
    dx = (xs_full - center[0])[:, None, None]
    dy = (ys_full - center[1])[None, :, None]
    dz = (zs_full - center[2])[None, None, :]
    mask_full = dx * dx + dy * dy + dz * dz <= radius * radius
    requested_count = int(mask_full.sum())

    if any(lo[i] > hi[i] for i in range(3)):
        empty = np.array([], dtype=np.intp)
        return 0, (empty, empty, empty), requested_count

    mask = mask_full[
        lo[0] - lo_unclamped[0]:hi[0] - lo_unclamped[0] + 1,
        lo[1] - lo_unclamped[1]:hi[1] - lo_unclamped[1] + 1,
        lo[2] - lo_unclamped[2]:hi[2] - lo_unclamped[2] + 1,
    ]

    region = buffer.grid[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
    region[mask] = color_index

    local_xs, local_ys, local_zs = np.nonzero(mask)
    coords = (local_xs + lo[0], local_ys + lo[1], local_zs + lo[2])
    return int(mask.sum()), coords, requested_count


def fill_cylinder(buffer: VoxelBuffer, center, radius: float, height: float, axis: str, color_index: int):
    """Fill a solid cylinder (inclusive boundary on both the radius and the
    height extent — the tests are `<= radius**2` and ceil/floor-inclusive on
    the height axis). `axis` is 'x', 'y', or 'z' — the axis the cylinder's
    height extends along, centered on `center` in the other two axes.
    Returns (count, coords, requested_count): coords is the (xs, ys, zs)
    index arrays of the voxels actually painted; requested_count is how many
    voxels the cylinder would cover with no canvas bounds at all, so callers
    can detect clipping via `requested_count - count`."""
    if axis not in ("x", "y", "z"):
        raise ValueError(f"axis must be 'x', 'y', or 'z', got {axis!r}")
    axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
    radial_idx = [i for i in range(3) if i != axis_idx]

    shape = buffer.shape
    lo_unclamped = [0, 0, 0]
    hi_unclamped = [0, 0, 0]
    lo_unclamped[axis_idx] = int(np.floor(center[axis_idx] - height / 2))
    hi_unclamped[axis_idx] = int(np.ceil(center[axis_idx] + height / 2))
    for i in radial_idx:
        lo_unclamped[i] = int(np.floor(center[i] - radius))
        hi_unclamped[i] = int(np.ceil(center[i] + radius))
    lo = [max(0, lo_unclamped[i]) for i in range(3)]
    hi = [min(shape[i] - 1, hi_unclamped[i]) for i in range(3)]

    coords_full = [np.arange(lo_unclamped[i], hi_unclamped[i] + 1) for i in range(3)]
    shape_bcast = [1, 1, 1]
    grids = []
    for i in range(3):
        s = list(shape_bcast)
        s[i] = len(coords_full[i])
        grids.append((coords_full[i] - center[i]).reshape(s))

    radial_sq = sum(grids[i] ** 2 for i in radial_idx)
    mask_full = radial_sq <= radius * radius
    mask_full = np.broadcast_to(mask_full, tuple(hi_unclamped[i] - lo_unclamped[i] + 1 for i in range(3)))
    requested_count = int(mask_full.sum())

    if any(lo[i] > hi[i] for i in range(3)):
        empty = np.array([], dtype=np.intp)
        return 0, (empty, empty, empty), requested_count

    mask = mask_full[
        lo[0] - lo_unclamped[0]:hi[0] - lo_unclamped[0] + 1,
        lo[1] - lo_unclamped[1]:hi[1] - lo_unclamped[1] + 1,
        lo[2] - lo_unclamped[2]:hi[2] - lo_unclamped[2] + 1,
    ]

    region = buffer.grid[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
    region[mask] = color_index

    local_xs, local_ys, local_zs = np.nonzero(mask)
    result_coords = (local_xs + lo[0], local_ys + lo[1], local_zs + lo[2])
    return int(mask.sum()), result_coords, requested_count
