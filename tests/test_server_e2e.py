"""End-to-end check that the MCP server actually works over a real MCP
session (client <-> server via in-memory streams), not just direct Python
calls — this exercises the lifespan/context wiring that direct calls skip."""

import os

import anyio
import pytest
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from magicavoxel_mcp.server import server
from magicavoxel_mcp.vox_io import read_vox


@pytest.mark.anyio
async def test_full_tool_sequence_over_real_session(tmp_path):
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

                tools = await session.list_tools()
                names = {t.name for t in tools.tools}
                assert names == {
                    "create_canvas",
                    "set_voxel",
                    "add_shape",
                    "apply_palette",
                    "export_vox",
                    "inspect_model",
                }

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

            tg.cancel_scope.cancel()

    loaded = read_vox(out_path)
    assert loaded.shape == (16, 16, 16)
    assert loaded.get_voxel(0, 0, 0) == 200
    assert loaded.get_voxel(8, 8, 8) == 3
    assert loaded.voxel_count() > 1
