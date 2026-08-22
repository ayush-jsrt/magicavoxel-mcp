"""Hand-rolled reader/writer for MagicaVoxel's .vox chunk format, built
directly from the official spec (github.com/ephtracy/voxel-model). Only
single-model files are supported (no PACK/scene-graph chunks) — that's all
Milestone 1 needs.
"""

import struct

import numpy as np

from magicavoxel_mcp.voxel_buffer import VoxelBuffer

MAGIC = b"VOX "
VERSION = 150


def _chunk(chunk_id: bytes, content: bytes, children: bytes = b"") -> bytes:
    return chunk_id + struct.pack("<ii", len(content), len(children)) + content + children


def write_vox(buffer: VoxelBuffer, path: str) -> None:
    size_x, size_y, size_z = buffer.shape
    size_content = struct.pack("<iii", size_x, size_y, size_z)

    xs, ys, zs = np.nonzero(buffer.grid)
    colors = buffer.grid[xs, ys, zs]
    voxel_rows = np.empty((len(xs), 4), dtype=np.uint8)
    voxel_rows[:, 0] = xs
    voxel_rows[:, 1] = ys
    voxel_rows[:, 2] = zs
    voxel_rows[:, 3] = colors
    xyzi_content = struct.pack("<i", len(xs)) + voxel_rows.tobytes()

    rgba_content = buffer.palette.astype(np.uint8).tobytes()

    children = (
        _chunk(b"SIZE", size_content)
        + _chunk(b"XYZI", xyzi_content)
        + _chunk(b"RGBA", rgba_content)
    )
    main_chunk = _chunk(b"MAIN", b"", children)

    with open(path, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<i", VERSION))
        f.write(main_chunk)


def read_vox(path: str) -> VoxelBuffer:
    with open(path, "rb") as f:
        data = f.read()

    if data[0:4] != MAGIC:
        raise ValueError(f"not a .vox file: bad magic {data[0:4]!r}")
    (version,) = struct.unpack_from("<i", data, 4)

    offset = 8
    main_id = data[offset:offset + 4]
    if main_id != b"MAIN":
        raise ValueError(f"expected MAIN chunk, got {main_id!r}")
    main_content_size, main_children_size = struct.unpack_from("<ii", data, offset + 4)
    children_start = offset + 12 + main_content_size
    children_end = children_start + main_children_size

    size_xyz = None
    voxels = []
    palette = None

    pos = children_start
    while pos < children_end:
        chunk_id = data[pos:pos + 4]
        content_size, chunk_children_size = struct.unpack_from("<ii", data, pos + 4)
        content_start = pos + 12
        content = data[content_start:content_start + content_size]

        if chunk_id == b"SIZE":
            size_xyz = struct.unpack_from("<iii", content, 0)
        elif chunk_id == b"XYZI":
            (num_voxels,) = struct.unpack_from("<i", content, 0)
            for i in range(num_voxels):
                x, y, z, c = struct.unpack_from("<BBBB", content, 4 + i * 4)
                voxels.append((x, y, z, c))
        elif chunk_id == b"RGBA":
            palette = [struct.unpack_from("<BBBB", content, i * 4) for i in range(256)]

        pos = content_start + content_size + chunk_children_size

    if size_xyz is None:
        raise ValueError("no SIZE chunk found in .vox file")

    buffer = VoxelBuffer(*size_xyz)
    for x, y, z, c in voxels:
        buffer.set_voxel(x, y, z, c)
    if palette is not None:
        for i, rgba in enumerate(palette):
            buffer.set_palette_entry(i, *rgba)

    return buffer
