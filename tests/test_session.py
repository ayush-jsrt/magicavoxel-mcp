import pytest

from magicavoxel_mcp.geometry import fill_box
from magicavoxel_mcp.session import Session


def test_require_buffer_before_canvas_raises():
    session = Session()
    with pytest.raises(ValueError):
        session.require_buffer()


def test_add_region_and_recolor():
    session = Session()
    session.new_canvas(5, 5, 5)
    count, coords, _ = fill_box(session.buffer, (0, 0, 0), (1, 1, 1), 5)
    region_id = session.add_region("box", 5, coords)

    session.recolor_region(region_id, 9)
    assert session.buffer.get_voxel(0, 0, 0) == 9
    assert session.regions[region_id].color_index == 9


def test_recolor_unknown_region_raises():
    session = Session()
    session.new_canvas(3, 3, 3)
    with pytest.raises(ValueError):
        session.recolor_region(999, 1)


def test_recolor_rejects_invalid_color():
    session = Session()
    session.new_canvas(3, 3, 3)
    _, coords, _ = fill_box(session.buffer, (0, 0, 0), (0, 0, 0), 5)
    region_id = session.add_region("box", 5, coords)
    with pytest.raises(ValueError):
        session.recolor_region(region_id, 0)


def test_erase_region_clears_voxels_and_forgets_region():
    session = Session()
    session.new_canvas(5, 5, 5)
    count, coords, _ = fill_box(session.buffer, (0, 0, 0), (1, 1, 1), 5)
    region_id = session.add_region("box", 5, coords)

    erased = session.erase_region(region_id)
    assert erased == count
    assert session.buffer.voxel_count() == 0
    assert region_id not in session.regions


def test_list_regions_sorted_by_id():
    session = Session()
    session.new_canvas(5, 5, 5)
    _, c1, _ = fill_box(session.buffer, (0, 0, 0), (0, 0, 0), 1)
    _, c2, _ = fill_box(session.buffer, (1, 1, 1), (1, 1, 1), 2)
    id2 = session.add_region("box", 2, c2)
    id1 = session.add_region("box", 1, c1)

    listed = session.list_regions()
    assert [r.id for r in listed] == sorted([id1, id2])


def test_checkpoint_round_trip():
    session = Session()
    session.new_canvas(4, 4, 4)
    _, coords, _ = fill_box(session.buffer, (0, 0, 0), (1, 1, 1), 3)
    region_id = session.add_region("box", 3, coords)
    session.save_checkpoint("before")

    session.recolor_region(region_id, 7)
    fill_box(session.buffer, (2, 2, 2), (3, 3, 3), 9)
    assert session.buffer.voxel_count() > 8

    session.restore_checkpoint("before")
    assert session.buffer.get_voxel(0, 0, 0) == 3
    assert session.buffer.voxel_count() == 8
    assert region_id in session.regions
    assert session.regions[region_id].color_index == 3


def test_restore_unknown_checkpoint_raises():
    session = Session()
    session.new_canvas(3, 3, 3)
    with pytest.raises(ValueError):
        session.restore_checkpoint("nope")


def test_restore_checkpoint_without_prior_buffer_reconstructs_it():
    session = Session()
    session.new_canvas(4, 4, 4)
    fill_box(session.buffer, (0, 0, 0), (0, 0, 0), 1)
    session.save_checkpoint("snap")

    fresh_session = Session()
    fresh_session.checkpoints["snap"] = session.checkpoints["snap"]
    fresh_session.restore_checkpoint("snap")

    assert fresh_session.buffer is not None
    assert fresh_session.buffer.shape == (4, 4, 4)
    assert fresh_session.buffer.get_voxel(0, 0, 0) == 1
