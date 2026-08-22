"""End-to-end check that the MCP server actually works over a real MCP
session (client <-> server via in-memory streams), not just direct Python
calls — this exercises the lifespan/context wiring that direct calls skip.
This is what caught the `lifespan_context` naming bug during Milestone 1."""

import os
from contextlib import asynccontextmanager

import anyio
import pytest
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from magicavoxel_mcp.blender_render import resolve_blender_exe
from magicavoxel_mcp.server import server
from magicavoxel_mcp.vox_io import read_vox, write_vox
from magicavoxel_mcp.voxel_buffer import VoxelBuffer

ALL_TOOL_NAMES = {
    "create_canvas",
    "import_vox",
    "set_voxel",
    "add_shape",
    "recolor_region",
    "erase_region",
    "list_regions",
    "apply_palette",
    "save_checkpoint",
    "restore_checkpoint",
    "export_vox",
    "inspect_model",
    "render",
}


@asynccontextmanager
async def live_session():
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        client_read, client_write = client_streams
        server_read, server_write = server_streams

        async with anyio.create_task_group() as tg:

            async def run_server():
                await server._lowlevel_server.run(
                    server_read,
                    server_write,
                    server._lowlevel_server.create_initialization_options(),
                )

            tg.start_soon(run_server)

            async with ClientSession(client_read, client_write) as session:
                await session.initialize()
                yield session

            tg.cancel_scope.cancel()


@pytest.mark.anyio
async def test_full_tool_sequence_over_real_session(tmp_path):
    async with live_session() as session:
        tools = await session.list_tools()
        names = {t.name for t in tools.tools}
        assert names == ALL_TOOL_NAMES

        result = await session.call_tool("create_canvas", {"width": 16, "height": 16, "depth": 16})
        assert not result.is_error

        result = await session.call_tool(
            "add_shape",
            {"shape": "sphere", "color_index": 3, "center_x": 8, "center_y": 8, "center_z": 8, "radius": 5},
        )
        assert not result.is_error

        result = await session.call_tool("set_voxel", {"x": 0, "y": 0, "z": 0, "color_index": 200})
        assert not result.is_error

        out_path = os.fspath(tmp_path / "e2e.vox")
        result = await session.call_tool("export_vox", {"path": out_path})
        assert not result.is_error

        result = await session.call_tool("inspect_model", {})
        assert not result.is_error
        summary = result.content[0].text
        assert "16x16x16" in summary

    loaded = read_vox(out_path)
    assert loaded.shape == (16, 16, 16)
    assert loaded.get_voxel(0, 0, 0) == 200
    assert loaded.get_voxel(8, 8, 8) == 3
    assert loaded.voxel_count() > 1


@pytest.mark.anyio
async def test_region_and_checkpoint_tools_over_real_session():
    async with live_session() as session:
        await session.call_tool("create_canvas", {"width": 10, "height": 10, "depth": 10})

        result = await session.call_tool(
            "add_shape",
            {"shape": "box", "color_index": 4, "center_x": 5, "center_y": 5, "center_z": 5, "size_x": 2, "size_y": 2, "size_z": 2},
        )
        assert not result.is_error
        text = result.content[0].text
        assert "region_id=" in text
        region_id = int(text.split("region_id=")[1].rstrip(").)"))

        result = await session.call_tool("list_regions", {})
        assert not result.is_error
        assert f"region_id={region_id}" in result.content[0].text

        result = await session.call_tool("save_checkpoint", {"name": "before"})
        assert not result.is_error

        result = await session.call_tool("recolor_region", {"region_id": region_id, "color_index": 50})
        assert not result.is_error

        result = await session.call_tool("erase_region", {"region_id": region_id + 999})
        assert result.is_error  # unknown region_id should surface as a tool error

        result = await session.call_tool("restore_checkpoint", {"name": "before"})
        assert not result.is_error

        result = await session.call_tool("list_regions", {})
        assert f"color_index=4" in result.content[0].text


@pytest.mark.anyio
async def test_import_vox_tool_over_real_session(tmp_path):
    source = VoxelBuffer(6, 6, 6)
    source.set_voxel(1, 2, 3, 77)
    vox_path = os.fspath(tmp_path / "existing.vox")
    write_vox(source, vox_path)

    async with live_session() as session:
        result = await session.call_tool("import_vox", {"path": vox_path})
        assert not result.is_error
        assert "6x6x6" in result.content[0].text


try:
    resolve_blender_exe()
    BLENDER_AVAILABLE = True
except RuntimeError:
    BLENDER_AVAILABLE = False


@pytest.mark.anyio
@pytest.mark.skipif(not BLENDER_AVAILABLE, reason="Blender not found on this machine")
async def test_render_tool_defaults_to_single_hero_view_over_real_session():
    async with live_session() as session:
        await session.call_tool("create_canvas", {"width": 6, "height": 6, "depth": 6})
        await session.call_tool(
            "add_shape",
            {"shape": "box", "color_index": 5, "center_x": 3, "center_y": 3, "center_z": 3, "size_x": 2, "size_y": 2, "size_z": 2},
        )

        result = await session.call_tool("render", {"image_size": 128})
        assert not result.is_error
        assert len(result.content) == 1
        image_block = result.content[0]
        assert image_block.type == "image"
        assert len(image_block.data) > 0

        result = await session.call_tool("inspect_model", {})
        assert not result.is_error
        assert "6x6x6" in result.content[0].text


@pytest.mark.anyio
@pytest.mark.skipif(not BLENDER_AVAILABLE, reason="Blender not found on this machine")
async def test_render_tool_accepts_explicit_multi_view_over_real_session():
    async with live_session() as session:
        await session.call_tool("create_canvas", {"width": 6, "height": 6, "depth": 6})
        await session.call_tool(
            "add_shape",
            {"shape": "box", "color_index": 5, "center_x": 3, "center_y": 3, "center_z": 3, "size_x": 2, "size_y": 2, "size_z": 2},
        )

        result = await session.call_tool("render", {"views": ["front", "top"], "image_size": 128})
        assert not result.is_error
        assert len(result.content) == 1
        image_block = result.content[0]
        assert image_block.type == "image"
        assert len(image_block.data) > 0
