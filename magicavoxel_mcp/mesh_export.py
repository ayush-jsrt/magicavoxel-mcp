"""Converts a VoxelBuffer into a plain OBJ+MTL cube mesh Blender can import
with zero addons. Only exterior faces are emitted (a face is skipped if its
neighbor voxel is solid) so the mesh stays small even near the 256^3 ceiling.
Winding order isn't guaranteed outward-consistent — the Blender-side render
script recalculates normals after import, so it doesn't need to be.
"""

import os

import numpy as np

from magicavoxel_mcp.voxel_buffer import VoxelBuffer

# Unit cube corners, indexed 0-7.
_CUBE_CORNERS = np.array(
    [
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
    ]
)

# For each of the 6 face directions: which 4 corners form that face, in order.
_FACES = {
    "+x": (1, 2, 6, 5),
    "-x": (0, 3, 7, 4),
    "+y": (2, 3, 7, 6),
    "-y": (0, 1, 5, 4),
    "+z": (4, 5, 6, 7),
    "-z": (0, 1, 2, 3),
}


def _exposed_mask(solid: np.ndarray, padded: np.ndarray, direction: str) -> np.ndarray:
    if direction == "+x":
        neighbor = padded[2:, 1:-1, 1:-1]
    elif direction == "-x":
        neighbor = padded[:-2, 1:-1, 1:-1]
    elif direction == "+y":
        neighbor = padded[1:-1, 2:, 1:-1]
    elif direction == "-y":
        neighbor = padded[1:-1, :-2, 1:-1]
    elif direction == "+z":
        neighbor = padded[1:-1, 1:-1, 2:]
    else:  # "-z"
        neighbor = padded[1:-1, 1:-1, :-2]
    return solid & (neighbor == 0)


def write_cube_mesh(buffer: VoxelBuffer, obj_path: str) -> None:
    grid = buffer.grid
    solid = grid != 0
    padded = np.pad(grid, 1, mode="constant", constant_values=0)

    # Group quads by color index so the OBJ can emit one usemtl block per
    # color actually used, instead of depending on per-vertex color import.
    quads_by_color: dict[int, list[tuple[int, int, int, str]]] = {}
    for direction in _FACES:
        exposed = _exposed_mask(solid, padded, direction)
        xs, ys, zs = np.nonzero(exposed)
        colors = grid[xs, ys, zs]
        for x, y, z, color in zip(xs.tolist(), ys.tolist(), zs.tolist(), colors.tolist()):
            quads_by_color.setdefault(color, []).append((x, y, z, direction))

    mtl_path = os.path.splitext(obj_path)[0] + ".mtl"
    mtl_name = os.path.basename(mtl_path)

    vertices: list[tuple[float, float, float]] = []
    obj_lines = [f"mtllib {mtl_name}"]
    mtl_lines = []

    for color in sorted(quads_by_color):
        r, g, b, _a = buffer.palette[color]
        mtl_lines.append(f"newmtl color_{color}")
        mtl_lines.append(f"Kd {r / 255:.4f} {g / 255:.4f} {b / 255:.4f}")
        mtl_lines.append("")

        obj_lines.append(f"usemtl color_{color}")
        for x, y, z, direction in quads_by_color[color]:
            corner_indices = _FACES[direction]
            face_vertex_ids = []
            for corner_idx in corner_indices:
                dx, dy, dz = _CUBE_CORNERS[corner_idx]
                vertices.append((x + dx, y + dy, z + dz))
                face_vertex_ids.append(len(vertices))  # OBJ vertex indices are 1-based
            obj_lines.append("f " + " ".join(str(i) for i in face_vertex_ids))

    vertex_lines = [f"v {vx} {vy} {vz}" for vx, vy, vz in vertices]

    with open(obj_path, "w") as f:
        f.write("\n".join(vertex_lines))
        f.write("\n")
        f.write("\n".join(obj_lines))
        f.write("\n")

    with open(mtl_path, "w") as f:
        f.write("\n".join(mtl_lines))
