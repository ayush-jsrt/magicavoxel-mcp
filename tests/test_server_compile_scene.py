import pytest
import os
from unittest.mock import MagicMock
from magicavoxel_mcp.server import compile_scene
from magicavoxel_mcp.session import Session


def test_compile_scene_tool_execution(tmp_path):
    # Create mock context
    mock_ctx = MagicMock()
    session = Session()
    mock_ctx.request_context.lifespan_context = session

    # Create dummy scene script
    script_file = tmp_path / "sample_scene.py"
    script_content = """
scene = Scene(24, 24, 24, name="test_diorama")
scene.set_palette_entry(1, 200, 100, 50)
base = scene.add_component("base", 24, 24, 4, offset=(0, 0, 0))
base.fill_box((0, 0, 0), (23, 23, 3), 1)
"""
    script_file.write_text(script_content, encoding="utf-8")

    res = compile_scene(mock_ctx, str(script_file), checkpoint_name="m1_test")
    assert "Compiled Scene 'test_diorama'" in res
    assert "Saved checkpoint 'm1_test'" in res

    # Verify session state
    buf = session.require_buffer()
    assert buf.shape == (24, 24, 24)
    assert buf.voxel_count() == 24 * 24 * 4
    assert "m1_test" in session.checkpoints