"""Per-connection session state: the active VoxelBuffer, region handles so a
shape can be recolored/erased after the fact, and named checkpoints for
safe rollback. Kept free of any MCP dependency so it's unit-testable on its
own — magicavoxel_mcp/server.py just wires these methods up as tools.
"""

from dataclasses import dataclass, replace

import numpy as np

from magicavoxel_mcp.voxel_buffer import VoxelBuffer

Coords = tuple[np.ndarray, np.ndarray, np.ndarray]


@dataclass(frozen=True)
class RegionInfo:
    id: int
    kind: str
    color_index: int
    coords: Coords

    @property
    def voxel_count(self) -> int:
        return len(self.coords[0])


@dataclass
class Checkpoint:
    grid: np.ndarray
    palette: np.ndarray
    regions: dict[int, RegionInfo]
    next_region_id: int


class Session:
    """Regions are paint-time snapshots of which voxels a shape call touched.
    If a later shape overlaps and repaints those cells, recoloring/erasing an
    earlier region will still affect them — there's no z-order/last-writer
    tracking. That would need a real scene graph; out of scope here."""

    def __init__(self) -> None:
        self.buffer: VoxelBuffer | None = None
        self.regions: dict[int, RegionInfo] = {}
        self._next_region_id: int = 1
        self.checkpoints: dict[str, Checkpoint] = {}

    def new_canvas(self, width: int, height: int, depth: int) -> None:
        self.buffer = VoxelBuffer(width, height, depth)
        self.regions = {}
        self._next_region_id = 1

    def set_buffer(self, buffer: VoxelBuffer) -> None:
        self.buffer = buffer
        self.regions = {}
        self._next_region_id = 1

    def require_buffer(self) -> VoxelBuffer:
        if self.buffer is None:
            raise ValueError("No active canvas — call create_canvas or import_vox first")
        return self.buffer

    def add_region(self, kind: str, color_index: int, coords: Coords) -> int:
        region_id = self._next_region_id
        self._next_region_id += 1
        self.regions[region_id] = RegionInfo(region_id, kind, color_index, coords)
        return region_id

    def _require_region(self, region_id: int) -> RegionInfo:
        if region_id not in self.regions:
            raise ValueError(f"No such region_id {region_id}")
        return self.regions[region_id]

    def recolor_region(self, region_id: int, color_index: int) -> int:
        buffer = self.require_buffer()
        region = self._require_region(region_id)
        if not (1 <= color_index <= 255):
            raise ValueError(f"color_index must be between 1 and 255, got {color_index}")
        xs, ys, zs = region.coords
        buffer.grid[xs, ys, zs] = color_index
        self.regions[region_id] = replace(region, color_index=color_index)
        return region.voxel_count

    def erase_region(self, region_id: int) -> int:
        buffer = self.require_buffer()
        region = self._require_region(region_id)
        xs, ys, zs = region.coords
        buffer.grid[xs, ys, zs] = 0
        del self.regions[region_id]
        return region.voxel_count

    def list_regions(self) -> list[RegionInfo]:
        return sorted(self.regions.values(), key=lambda r: r.id)

    def save_checkpoint(self, name: str) -> None:
        buffer = self.require_buffer()
        self.checkpoints[name] = Checkpoint(
            grid=buffer.grid.copy(),
            palette=buffer.palette.copy(),
            regions=dict(self.regions),
            next_region_id=self._next_region_id,
        )

    def restore_checkpoint(self, name: str) -> None:
        if name not in self.checkpoints:
            raise ValueError(f"No such checkpoint {name!r}")
        checkpoint = self.checkpoints[name]
        self.buffer = VoxelBuffer(*checkpoint.grid.shape)
        self.buffer.grid = checkpoint.grid.copy()
        self.buffer.palette = checkpoint.palette.copy()
        self.regions = dict(checkpoint.regions)
        self._next_region_id = checkpoint.next_region_id
