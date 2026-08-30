import pytest
import os
import numpy as np
from magicavoxel_mcp.scene import Scene, Component
from magicavoxel_mcp.vox_io import write_vox, read_vox
from magicavoxel_mcp.voxel_buffer import VoxelBuffer


def test_component_geometry_helpers():
    comp = Component("test_prop", 16, 16, 16)
    count = comp.fill_box((2, 2, 0), (6, 6, 4), color_index=5)
    assert count == 5 * 5 * 5
    assert comp.buffer.grid[2, 2, 0] == 5

    carved = comp.carve_box((3, 3, 1), (5, 5, 3))
    assert carved == 3 * 3 * 3
    assert comp.buffer.grid[3, 3, 1] == 0
    assert comp.buffer.grid[2, 2, 0] == 5


def test_scene_declarative_assembly(tmp_path):
    scene = Scene(32, 32, 32, name="mini_scene")
    scene.set_palette_entry(1, 100, 50, 20)
    scene.set_palette_entry(2, 50, 150, 50)

    # Base component
    base = scene.add_component("base", 32, 32, 4, offset=(0, 0, 0))
    base.fill_box((0, 0, 0), (31, 31, 2), color_index=1)

    # Pillar component
    pillar = scene.add_component("pillar", 6, 6, 12, offset=(8, 8, 3))
    pillar.fill_cylinder((3, 3, 6), radius=2.5, height=10, axis="z", color_index=2)

    buf = scene.compile()
    assert buf.shape == (32, 32, 32)
    assert buf.grid[0, 0, 0] == 1
    assert buf.grid[10, 10, 5] == 2
    assert tuple(buf.palette[1][:3]) == (100, 50, 20)

    # Test export
    out_file = str(tmp_path / "compiled_scene.vox")
    count = scene.export_vox(out_file)
    assert os.path.exists(out_file)
    assert count > 0

    # Test from_vox
    loaded_scene = Scene.from_vox(out_file, name="reloaded")
    assert loaded_scene.width == 32
    assert loaded_scene.height == 32
    assert len(loaded_scene.components) == 1