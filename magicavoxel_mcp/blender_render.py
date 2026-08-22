"""Shells out to headless Blender to render views of a cube mesh. Blender's
own path isn't hardcoded — install locations vary per machine (see
docs/ARCHITECTURE.md)."""

import os
import shutil
import subprocess

_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "blender_scripts", "render_views.py")

# The "hero*" views are perspective vantage points; the rest are orthographic
# axis views. Keep in sync with VIEW_DIRECTIONS in blender_scripts/render_views.py.
VALID_VIEWS = (
    "front", "back", "left", "right", "top",
    "hero", "hero_front_right", "hero_front_left",
    "hero_back_right", "hero_back_left", "hero_top", "hero_low",
)

# Keep in sync with LIGHTING_PRESETS in blender_scripts/render_views.py.
VALID_LIGHTING = ("neutral", "night")


def resolve_blender_exe(blender_exe: str | None = None) -> str:
    if blender_exe:
        return blender_exe
    env_path = os.environ.get("MAGICAVOXEL_MCP_BLENDER_EXE")
    if env_path:
        return env_path
    which_path = shutil.which("blender")
    if which_path:
        return which_path
    raise RuntimeError(
        "Could not find Blender. Pass blender_exe explicitly, set the "
        "MAGICAVOXEL_MCP_BLENDER_EXE environment variable, or add Blender to PATH."
    )


def render_views(
    mesh_obj_path: str,
    output_dir: str,
    views: list[str],
    image_size: int = 512,
    lighting: str = "neutral",
    blender_exe: str | None = None,
    timeout: float = 90,
) -> dict[str, str]:
    for view in views:
        if view not in VALID_VIEWS:
            raise ValueError(f"Unknown view {view!r}: expected one of {VALID_VIEWS}")
    if lighting not in VALID_LIGHTING:
        raise ValueError(f"Unknown lighting {lighting!r}: expected one of {VALID_LIGHTING}")

    exe = resolve_blender_exe(blender_exe)
    os.makedirs(output_dir, exist_ok=True)

    args = [
        exe,
        "--background",
        "--factory-startup",
        "--python",
        _SCRIPT_PATH,
        "--",
        mesh_obj_path,
        output_dir,
        ",".join(views),
        str(image_size),
        lighting,
    ]
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-20:])
        raise RuntimeError(f"Blender render failed (exit {result.returncode}):\n{tail}")

    output_paths = {}
    for view in views:
        path = os.path.join(output_dir, f"{view}.png")
        if not os.path.exists(path):
            tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-30:])
            raise RuntimeError(
                f"Blender exited 0 but did not produce expected output {path}. "
                f"Blender output:\n{tail}"
            )
        output_paths[view] = path
    return output_paths
