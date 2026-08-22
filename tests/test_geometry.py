from magicavoxel_mcp.geometry import fill_box, fill_cylinder, fill_sphere
from magicavoxel_mcp.voxel_buffer import VoxelBuffer


def test_fill_box_exact_region():
    buf = VoxelBuffer(5, 5, 5)
    count = fill_box(buf, (1, 1, 1), (2, 2, 2), 7)
    assert count == 2 * 2 * 2
    assert buf.voxel_count() == count
    assert buf.get_voxel(1, 1, 1) == 7
    assert buf.get_voxel(2, 2, 2) == 7
    assert buf.get_voxel(0, 0, 0) == 0
    assert buf.get_voxel(3, 3, 3) == 0


def test_fill_box_clips_to_buffer_bounds():
    buf = VoxelBuffer(3, 3, 3)
    count = fill_box(buf, (-5, -5, -5), (100, 100, 100), 1)
    assert count == 3 * 3 * 3
    assert buf.voxel_count() == 27


def test_fill_box_handles_reversed_corners():
    buf = VoxelBuffer(5, 5, 5)
    count = fill_box(buf, (3, 3, 3), (1, 1, 1), 9)
    assert count == 3 * 3 * 3  # corners span indices 1,2,3 inclusive on each axis
    assert buf.get_voxel(1, 1, 1) == 9
    assert buf.get_voxel(3, 3, 3) == 9


def test_fill_sphere_paints_center_and_respects_radius():
    buf = VoxelBuffer(21, 21, 21)
    count = fill_sphere(buf, (10, 10, 10), 5, 3)
    assert count > 0
    assert buf.get_voxel(10, 10, 10) == 3
    assert buf.get_voxel(0, 0, 0) == 0
    assert buf.voxel_count() == count


def test_fill_sphere_out_of_bounds_is_noop():
    buf = VoxelBuffer(5, 5, 5)
    count = fill_sphere(buf, (1000, 1000, 1000), 2, 1)
    assert count == 0
    assert buf.voxel_count() == 0


def test_fill_cylinder_along_z_axis():
    buf = VoxelBuffer(11, 11, 11)
    count = fill_cylinder(buf, (5, 5, 5), radius=3, height=6, axis="z", color_index=2)
    assert count > 0
    assert buf.get_voxel(5, 5, 5) == 2
    # Outside the radius on the same z-plane should be empty.
    assert buf.get_voxel(0, 0, 5) == 0
    assert buf.voxel_count() == count


def test_fill_cylinder_rejects_bad_axis():
    buf = VoxelBuffer(5, 5, 5)
    try:
        fill_cylinder(buf, (2, 2, 2), radius=1, height=2, axis="w", color_index=1)
        assert False, "expected ValueError"
    except ValueError:
        pass
