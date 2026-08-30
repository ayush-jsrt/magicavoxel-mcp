"""
Declarative Scene-as-Code Engine for MagicaVoxel MCP.

Provides structured, parametric scene modeling with isolated components,
coordinate transforms, native .vox import/export, and deterministic compilation.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.geometry import fill_box, fill_sphere, fill_cylinder
from magicavoxel_mcp.vox_io import read_vox, write_vox


class Component:
    """A modular, isolated 3D voxel asset with local transforms and geometry helpers."""

    def __init__(
        self,
        name: str,
        width: int,
        depth: int,
        height: int,
        offset: Tuple[int, int, int] = (0, 0, 0),
        rotation: int = 0,
        enabled: bool = True,
        buffer: Optional[VoxelBuffer] = None,
    ):
        self.name = name
        self.offset = offset
        self.rotation = rotation
        self.enabled = enabled

        if buffer is not None:
            self.buffer = buffer
        else:
            self.buffer = VoxelBuffer(width, depth, height)

    @property
    def shape(self) -> Tuple[int, int, int]:
        return self.buffer.shape

    def set_voxel(self, x: int, y: int, z: int, color_index: int) -> None:
        self.buffer.set_voxel(x, y, z, color_index)

    def fill_box(self, p1: Tuple[int, int, int], p2: Tuple[int, int, int], color_index: int) -> int:
        count, _, _ = fill_box(self.buffer, p1, p2, color_index)
        return count

    def fill_sphere(self, center: Tuple[int, int, int], radius: float, color_index: int) -> int:
        count, _, _ = fill_sphere(self.buffer, center, radius, color_index)
        return count

    def fill_cylinder(self, center: Tuple[int, int, int], radius: float, height: float, axis: str, color_index: int) -> int:
        count, _, _ = fill_cylinder(self.buffer, center, radius, height, axis, color_index)
        return count

    def carve_box(self, p1: Tuple[int, int, int], p2: Tuple[int, int, int]) -> int:
        count, _, _ = fill_box(self.buffer, p1, p2, color_index=0)
        return count

    def carve_sphere(self, center: Tuple[int, int, int], radius: float) -> int:
        count, _, _ = fill_sphere(self.buffer, center, radius, color_index=0)
        return count

    def carve_cylinder(self, center: Tuple[int, int, int], radius: float, height: float, axis: str) -> int:
        count, _, _ = fill_cylinder(self.buffer, center, radius, height, axis, color_index=0)
        return count


class Scene:
    """Master Declarative Scene Graph."""

    def __init__(self, width: int, depth: int, height: int, name: str = "scene"):
        self.name = name
        self.width = width
        self.depth = depth
        self.height = height
        self.master_buffer = VoxelBuffer(width, depth, height)
        self.components: List[Component] = []
        self._component_map: Dict[str, Component] = {}

    def set_palette_entry(self, index: int, r: int, g: int, b: int, a: int = 255) -> None:
        self.master_buffer.set_palette_entry(index, r, g, b, a)

    def apply_palette(self, entries: Dict[int, Union[Tuple[int, int, int], Tuple[int, int, int, int]]]) -> None:
        for idx, col in entries.items():
            if len(col) == 3:
                self.master_buffer.set_palette_entry(idx, col[0], col[1], col[2], 255)
            elif len(col) == 4:
                self.master_buffer.set_palette_entry(idx, col[0], col[1], col[2], col[3])

    def add_component(
        self,
        name: str,
        width: int,
        depth: int,
        height: int,
        offset: Tuple[int, int, int] = (0, 0, 0),
        rotation: int = 0,
        enabled: bool = True,
    ) -> Component:
        """Create and register a new parametric component."""
        comp = Component(name, width, depth, height, offset, rotation, enabled)
        comp.buffer.palette = self.master_buffer.palette.copy()
        self.components.append(comp)
        self._component_map[name] = comp
        return comp

    def add_vox(
        self,
        name: str,
        vox_path: str,
        offset: Tuple[int, int, int] = (0, 0, 0),
        rotation: int = 0,
        enabled: bool = True,
    ) -> Component:
        """Import an existing .vox file as a modular declarative component."""
        buf = read_vox(vox_path)
        comp = Component(
            name=name,
            width=buf.shape[0],
            depth=buf.shape[1],
            height=buf.shape[2],
            offset=offset,
            rotation=rotation,
            enabled=enabled,
            buffer=buf,
        )
        self.components.append(comp)
        self._component_map[name] = comp
        return comp

    @classmethod
    def from_vox(cls, vox_path: str, name: str = "imported_scene") -> Scene:
        """Initialize a full declarative scene directly from an existing .vox file."""
        buf = read_vox(vox_path)
        scene = cls(buf.shape[0], buf.shape[1], buf.shape[2], name=name)
        scene.master_buffer = buf
        scene.add_vox(name="base_model", vox_path=vox_path, offset=(0, 0, 0))
        return scene

    def get_component(self, name: str) -> Optional[Component]:
        return self._component_map.get(name)

    def compile(self) -> VoxelBuffer:
        """Compile all active components in defined order into a master VoxelBuffer."""
        compiled = VoxelBuffer(self.width, self.depth, self.height)
        compiled.palette = self.master_buffer.palette.copy()

        for comp in self.components:
            if not comp.enabled:
                continue
            ox, oy, oz = comp.offset
            paste_vox_buffer(
                master=compiled,
                prop=comp.buffer,
                offset_x=ox,
                offset_y=oy,
                offset_z=oz,
                rotation=comp.rotation,
                auto_crop=True,
            )

        self.master_buffer = compiled
        return compiled

    def export_vox(self, output_path: str) -> int:
        """Compile and write the scene to standard MagicaVoxel .vox format."""
        buf = self.compile()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        write_vox(buf, output_path)
        return buf.voxel_count()