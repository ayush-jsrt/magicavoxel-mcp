import os

import pytest
from PIL import Image

from magicavoxel_mcp.blender_render import render_views, resolve_blender_exe
from magicavoxel_mcp.geometry import fill_box
from magicavoxel_mcp.mesh_export import write_cube_mesh
from magicavoxel_mcp.voxel_buffer import VoxelBuffer

try:
    resolve_blender_exe()
    BLENDER_AVAILABLE = True
except RuntimeError:
    BLENDER_AVAILABLE = False

pytestmark = pytest.mark.skipif(not BLENDER_AVAILABLE, reason="Blender not found on this machine")


def _is_blank(path, threshold=5):
    img = Image.open(path).convert("RGB")
    extrema = img.getextrema()
    # A blank render has near-zero variance in every channel.
    return all(hi - lo < threshold for lo, hi in extrema)


def test_render_views_produces_non_blank_pngs(tmp_path):
    buf = VoxelBuffer(6, 6, 6)
    fill_box(buf, (1, 1, 1), (3, 3, 3), 5)
    obj_path = os.fspath(tmp_path / "model.obj")
    write_cube_mesh(buf, obj_path)

    output_dir = os.fspath(tmp_path / "renders")
    result = render_views(obj_path, output_dir, ["front", "top", "hero"], image_size=128)

    assert set(result.keys()) == {"front", "top", "hero"}
    for path in result.values():
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert not _is_blank(path), f"{path} looks blank"


def test_render_views_rejects_unknown_view(tmp_path):
    buf = VoxelBuffer(3, 3, 3)
    buf.set_voxel(1, 1, 1, 1)
    obj_path = os.fspath(tmp_path / "model.obj")
    write_cube_mesh(buf, obj_path)

    with pytest.raises(ValueError):
        render_views(obj_path, os.fspath(tmp_path / "out"), ["sideways"])
