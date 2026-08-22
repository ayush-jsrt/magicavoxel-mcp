import os
import struct

from magicavoxel_mcp.geometry import fill_box, fill_sphere
from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.vox_io import read_vox, write_vox


def _raw_rgba_chunk(path):
    """Independently parse the RGBA chunk bytes straight from the file,
    without going through our own read_vox — this is what makes it a real
    spec-compliance check rather than a self-consistent round trip."""
    with open(path, "rb") as f:
        data = f.read()
    idx = data.index(b"RGBA")
    content_size, _children_size = struct.unpack_from("<ii", data, idx + 4)
    content = data[idx + 12: idx + 12 + content_size]
    return [struct.unpack_from("<BBBB", content, i * 4) for i in range(256)]


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


def test_voxel_color_index_maps_to_rgba_chunk_entry_minus_one(tmp_path):
    """Per the official spec, a voxel with color index i (1-255) refers to
    RGBA chunk entry i-1. This bug shipped once already (self-consistent
    round-trip tests can't catch it — only checking the real byte layout
    can), caught when opening real output in actual MagicaVoxel."""
    buf = VoxelBuffer(2, 2, 2)
    buf.set_palette_entry(60, 110, 55, 45, 255)
    buf.set_voxel(0, 0, 0, 60)

    path = os.fspath(tmp_path / "palette_offset.vox")
    write_vox(buf, path)

    chunk = _raw_rgba_chunk(path)
    assert chunk[59] == (110, 55, 45, 255)


def test_round_trip_empty_buffer(tmp_path):
    buf = VoxelBuffer(3, 3, 3)
    path = os.fspath(tmp_path / "empty.vox")
    write_vox(buf, path)
    loaded = read_vox(path)

    assert loaded.shape == (3, 3, 3)
    assert loaded.voxel_count() == 0
