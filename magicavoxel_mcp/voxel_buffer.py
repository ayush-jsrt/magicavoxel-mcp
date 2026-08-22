"""In-memory voxel grid + palette, the shared state all tools operate on."""

import colorsys

import numpy as np

MAX_DIM = 256


def default_palette() -> np.ndarray:
    """A reasonable 256x4 RGBA palette. MagicaVoxel always stores its own
    palette chunk in every file, so there's no compatibility requirement to
    replicate the app's built-in default here — this is just a usable
    out-of-the-box look until `apply_palette` is called."""
    palette = np.zeros((256, 4), dtype=np.uint8)
    palette[:, 3] = 255
    for i in range(255):
        hue = i / 255
        r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.95)
        palette[i, 0] = int(r * 255)
        palette[i, 1] = int(g * 255)
        palette[i, 2] = int(b * 255)
    return palette


class VoxelBuffer:
    """A single voxel model: a 3D grid of palette indices (0 = empty) plus
    the 256-color palette those indices refer to."""

    def __init__(self, size_x: int, size_y: int, size_z: int):
        for name, dim in (("size_x", size_x), ("size_y", size_y), ("size_z", size_z)):
            if not (1 <= dim <= MAX_DIM):
                raise ValueError(f"{name} must be between 1 and {MAX_DIM}, got {dim}")
        self.grid = np.zeros((size_x, size_y, size_z), dtype=np.uint8)
        self.palette = default_palette()

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.grid.shape

    def set_voxel(self, x: int, y: int, z: int, color_index: int) -> None:
        if not (1 <= color_index <= 255):
            raise ValueError(f"color_index must be between 1 and 255, got {color_index}")
        self.grid[x, y, z] = color_index

    def get_voxel(self, x: int, y: int, z: int) -> int:
        return int(self.grid[x, y, z])

    def voxel_count(self) -> int:
        return int(np.count_nonzero(self.grid))

    def bounding_box(self) -> tuple[tuple[int, int, int], tuple[int, int, int]] | None:
        """Bounding box of non-empty voxels as (min_xyz, max_xyz) inclusive, or
        None if the buffer is empty."""
        nonzero = np.argwhere(self.grid != 0)
        if nonzero.size == 0:
            return None
        mins = tuple(int(v) for v in nonzero.min(axis=0))
        maxs = tuple(int(v) for v in nonzero.max(axis=0))
        return mins, maxs

    def set_palette_entry(self, index: int, r: int, g: int, b: int, a: int = 255) -> None:
        if not (0 <= index <= 255):
            raise ValueError(f"palette index must be between 0 and 255, got {index}")
        self.palette[index] = (r, g, b, a)
