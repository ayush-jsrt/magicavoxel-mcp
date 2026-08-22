import pytest

from magicavoxel_mcp.voxel_buffer import MAX_DIM, VoxelBuffer


def test_create_canvas_basic():
    buf = VoxelBuffer(4, 5, 6)
    assert buf.shape == (4, 5, 6)
    assert buf.voxel_count() == 0
    assert buf.bounding_box() is None


@pytest.mark.parametrize("dims", [(0, 1, 1), (1, 0, 1), (1, 1, 0), (257, 1, 1), (-1, 1, 1)])
def test_create_canvas_rejects_out_of_range_dims(dims):
    with pytest.raises(ValueError):
        VoxelBuffer(*dims)


def test_create_canvas_allows_max_dim():
    buf = VoxelBuffer(MAX_DIM, 1, 1)
    assert buf.shape == (MAX_DIM, 1, 1)


def test_set_and_get_voxel():
    buf = VoxelBuffer(3, 3, 3)
    buf.set_voxel(1, 1, 1, 42)
    assert buf.get_voxel(1, 1, 1) == 42
    assert buf.get_voxel(0, 0, 0) == 0
    assert buf.voxel_count() == 1


@pytest.mark.parametrize("color_index", [0, -1, 256])
def test_set_voxel_rejects_invalid_color_index(color_index):
    buf = VoxelBuffer(2, 2, 2)
    with pytest.raises(ValueError):
        buf.set_voxel(0, 0, 0, color_index)


def test_bounding_box():
    buf = VoxelBuffer(10, 10, 10)
    buf.set_voxel(2, 3, 4, 5)
    buf.set_voxel(7, 1, 9, 5)
    assert buf.bounding_box() == ((2, 1, 4), (7, 3, 9))


def test_set_palette_entry():
    buf = VoxelBuffer(2, 2, 2)
    buf.set_palette_entry(0, 10, 20, 30, 40)
    assert tuple(buf.palette[0]) == (10, 20, 30, 40)


def test_set_palette_entry_rejects_out_of_range_index():
    buf = VoxelBuffer(2, 2, 2)
    with pytest.raises(ValueError):
        buf.set_palette_entry(256, 0, 0, 0)
