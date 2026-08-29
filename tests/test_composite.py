import pytest
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.geometry import fill_box
from magicavoxel_mcp.voxel_buffer import VoxelBuffer


def test_paste_vox_buffer_basic():
    master = VoxelBuffer(20, 20, 20)
    prop = VoxelBuffer(6, 6, 6)
    fill_box(prop, (0, 0, 0), (3, 3, 3), 10)

    count, coords, size = paste_vox_buffer(master, prop, offset_x=5, offset_y=5, offset_z=0)
    assert count == 64
    assert len(coords[0]) == 64
    assert master.get_voxel(5, 5, 0) == 10
    assert master.get_voxel(8, 8, 3) == 10
    assert master.get_voxel(9, 9, 4) == 0


def test_paste_vox_buffer_with_rotation():
    master = VoxelBuffer(20, 20, 20)
    prop = VoxelBuffer(10, 4, 4)
    fill_box(prop, (0, 0, 0), (9, 3, 3), 20)

    count, coords, size = paste_vox_buffer(master, prop, offset_x=2, offset_y=2, offset_z=0, rotation=90)
    assert count == 160
    assert len(coords[0]) == 160
    # After 90 deg rotation, (10, 4, 4) becomes (4, 10, 4)
    assert size == (4, 10, 4)
    assert master.get_voxel(2, 2, 0) == 20
    assert master.get_voxel(5, 11, 3) == 20


def test_paste_vox_buffer_clipping():
    master = VoxelBuffer(10, 10, 10)
    prop = VoxelBuffer(6, 6, 6)
    fill_box(prop, (0, 0, 0), (5, 5, 5), 30)

    count, coords, size = paste_vox_buffer(master, prop, offset_x=8, offset_y=8, offset_z=8)
    assert count == 8  # 2x2x2 inside master bounds (8, 9)
    assert len(coords[0]) == 8
    assert master.get_voxel(8, 8, 8) == 30
