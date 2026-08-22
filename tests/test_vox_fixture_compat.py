import os

from magicavoxel_mcp.vox_io import read_vox

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_reads_real_magicavoxel_authored_file():
    """ff3.vox is a real single-model file exported by MagicaVoxel itself
    (see tests/fixtures/NOTICE.md), not something our own writer produced —
    this validates the reader against actual app output, independent of any
    round-trip symmetry bugs that could hide in write+read alone."""
    path = os.path.join(FIXTURES_DIR, "ff3.vox")
    buf = read_vox(path)

    assert all(dim > 0 for dim in buf.shape)
    assert buf.voxel_count() > 0
    mins, maxs = buf.bounding_box()
    for i in range(3):
        assert 0 <= mins[i] <= maxs[i] < buf.shape[i]
