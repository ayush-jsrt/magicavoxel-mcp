import os

from magicavoxel_mcp.geometry import fill_box
from magicavoxel_mcp.mesh_export import write_cube_mesh
from magicavoxel_mcp.voxel_buffer import VoxelBuffer


def _count_obj_lines(path, prefix):
    with open(path) as f:
        return sum(1 for line in f if line.startswith(prefix))


def test_single_voxel_emits_all_six_faces(tmp_path):
    buf = VoxelBuffer(3, 3, 3)
    buf.set_voxel(1, 1, 1, 5)
    obj_path = os.fspath(tmp_path / "single.obj")
    write_cube_mesh(buf, obj_path)

    assert _count_obj_lines(obj_path, "f ") == 6
    assert _count_obj_lines(obj_path, "v ") == 6 * 4


def test_solid_box_only_emits_exterior_faces(tmp_path):
    buf = VoxelBuffer(4, 4, 4)
    fill_box(buf, (0, 0, 0), (1, 1, 1), 5)  # solid 2x2x2 block, same color
    obj_path = os.fspath(tmp_path / "box.obj")
    write_cube_mesh(buf, obj_path)

    # Surface area of a 2x2x2 cube of unit cubes = 6 faces * 2x2 = 24 quads,
    # not the naive 8 voxels * 6 faces = 48.
    assert _count_obj_lines(obj_path, "f ") == 24


def test_writes_mtl_with_one_material_per_color(tmp_path):
    buf = VoxelBuffer(3, 3, 3)
    buf.set_voxel(0, 0, 0, 5)
    buf.set_voxel(2, 2, 2, 9)
    obj_path = os.fspath(tmp_path / "multi.obj")
    write_cube_mesh(buf, obj_path)

    mtl_path = os.fspath(tmp_path / "multi.mtl")
    assert os.path.exists(mtl_path)
    with open(mtl_path) as f:
        content = f.read()
    assert "newmtl color_5" in content
    assert "newmtl color_9" in content

    with open(obj_path) as f:
        obj_content = f.read()
    assert "mtllib multi.mtl" in obj_content
    assert "usemtl color_5" in obj_content
    assert "usemtl color_9" in obj_content


def test_empty_buffer_produces_no_faces(tmp_path):
    buf = VoxelBuffer(3, 3, 3)
    obj_path = os.fspath(tmp_path / "empty.obj")
    write_cube_mesh(buf, obj_path)

    assert _count_obj_lines(obj_path, "f ") == 0
