import os

from magicavoxel_mcp.geometry import fill_box, fill_sphere
from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.vox_io import read_vox, write_vox


def test_round_trip_preserves_grid_and_palette(tmp_path):
    buf = VoxelBuffer(8, 9, 10)
    fill_box(buf, (0, 0, 0), (2, 2, 2), 5)
    fill_sphere(buf, (5, 5, 5), 3, 12)
    buf.set_palette_entry(4, 200, 100, 50, 255)

    path = os.fspath(tmp_path / "roundtrip.vox")
    write_vox(buf, path)
    loaded = read_vox(path)

    assert loaded.shape == buf.shape
    assert (loaded.grid == buf.grid).all()
    assert (loaded.palette == buf.palette).all()


def test_round_trip_empty_buffer(tmp_path):
    buf = VoxelBuffer(3, 3, 3)
    path = os.fspath(tmp_path / "empty.vox")
    write_vox(buf, path)
    loaded = read_vox(path)

    assert loaded.shape == (3, 3, 3)
    assert loaded.voxel_count() == 0
