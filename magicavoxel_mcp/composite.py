"""Utilities for compositing multiple VoxelBuffer objects into a master scene."""

import numpy as np
from magicavoxel_mcp.voxel_buffer import VoxelBuffer


def paste_vox_buffer(
    master: VoxelBuffer,
    prop: VoxelBuffer,
    offset_x: int,
    offset_y: int,
    offset_z: int,
    rotation: int = 0,
    auto_crop: bool = True,
) -> tuple[int, tuple[np.ndarray, np.ndarray, np.ndarray], tuple[int, int, int]]:
    """Pastes a prop VoxelBuffer into a master VoxelBuffer at (offset_x, offset_y, offset_z).

    rotation: 0, 90, 180, or 270 degrees clockwise around Z axis.
    auto_crop: If True, crops empty outer bounds before placing so the prop base sits flush.
    Returns: (voxels_painted, coords, target_bounding_size)
    """
    grid = prop.grid.copy()

    if auto_crop:
        bbox = prop.bounding_box()
        if bbox is None:
            return 0, (0, 0, 0)
        (min_x, min_y, min_z), (max_x, max_y, max_z) = bbox
        grid = grid[min_x : max_x + 1, min_y : max_y + 1, min_z : max_z + 1]

    if rotation == 90:
        grid = np.rot90(grid, 1, axes=(0, 1))
    elif rotation == 180:
        grid = np.rot90(grid, 2, axes=(0, 1))
    elif rotation == 270:
        grid = np.rot90(grid, 3, axes=(0, 1))
    elif rotation != 0:
        raise ValueError(f"rotation must be 0, 90, 180, or 270 degrees, got {rotation}")

    pw, pd, ph = grid.shape
    mw, md, mh = master.shape

    src_x0 = max(0, -offset_x)
    src_y0 = max(0, -offset_y)
    src_z0 = max(0, -offset_z)

    dst_x0 = max(0, offset_x)
    dst_y0 = max(0, offset_y)
    dst_z0 = max(0, offset_z)

    src_x1 = min(pw, mw - offset_x)
    src_y1 = min(pd, md - offset_y)
    src_z1 = min(ph, mh - offset_z)

    dst_x1 = dst_x0 + (src_x1 - src_x0)
    dst_y1 = dst_y0 + (src_y1 - src_y0)
    dst_z1 = dst_z0 + (src_z1 - src_z0)

    if src_x1 <= src_x0 or src_y1 <= src_y0 or src_z1 <= src_z0:
        empty = np.array([], dtype=np.intp)
        return 0, (empty, empty, empty), (pw, pd, ph)

    src_sub = grid[src_x0:src_x1, src_y0:src_y1, src_z0:src_z1]
    dst_sub = master.grid[dst_x0:dst_x1, dst_y0:dst_y1, dst_z0:dst_z1]

    mask = src_sub != 0
    dst_sub[mask] = src_sub[mask]

    local_xs, local_ys, local_zs = np.nonzero(mask)
    coords = (local_xs + dst_x0, local_ys + dst_y0, local_zs + dst_z0)
    return int(np.count_nonzero(mask)), coords, (pw, pd, ph)
