"""Runs inside Blender's own Python (invoked via `blender --background
--python render_views.py -- <mesh_obj_path> <output_dir> <views_csv>
<image_size> <lighting>`). Imports a cube mesh, frames a camera per requested
view, and renders each to <output_dir>/<view>.png.

Axis-aligned views (front/back/left/right/top) are orthographic — useful for
verifying exact geometry, but they flatten depth entirely and read poorly as
"what does this actually look like". "hero" is a perspective 3/4 angle (the
classic voxel-art screenshot angle) that actually conveys depth and shape.
"""

import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
mesh_obj_path, output_dir, views_csv, image_size, lighting = argv[:5]
engine = argv[5].lower() if len(argv) > 5 else "cycles"

views = views_csv.split(",")
image_size = int(image_size)

def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


LIGHTING_PRESETS = {
    # MagicaVoxel-matching studio lighting: dark slate ambient backdrop
    # and pure white directional sun for vibrant, saturated voxel colors.
    "neutral": {
        "world_color": (0.22, 0.24, 0.27),
        "world_strength": 0.5,
        "key_energy": 3.5,
        "key_color": (1.0, 1.0, 1.0),
        "key_rotation": (0.75, 0.25, 0.8),
        "key_angle": 0.06,
        "fill_energy": 0.6,
        "fill_color": (0.95, 0.95, 1.0),
        "fill_rotation": (-0.5, -0.3, 2.6),
    },
    # Dark ambient + warm low key light (simulating lantern/street-level
    # warmth) + cool blue rim fill from behind for contrast — for moody
    # night scenes.
    "night": {
        "world_color": (0.015, 0.015, 0.035),
        "world_strength": 0.4,
        "key_energy": 2.5,
        "key_color": (1.0, 0.55, 0.25),
        "key_rotation": (1.3, 0.1, 0.5),
        "key_angle": 0.08,
        "fill_energy": 0.8,
        "fill_color": (0.4, 0.55, 1.0),
        "fill_rotation": (-0.6, -0.2, 2.9),
    },
}
if lighting not in LIGHTING_PRESETS:
    raise ValueError(f"Unknown lighting {lighting!r}: expected one of {sorted(LIGHTING_PRESETS)}")
preset = LIGHTING_PRESETS[lighting]

VIEW_DIRECTIONS = {
    # Orthographic axis views — flatten depth, useful only for verifying
    # exact geometry (alignment, proportions), not for judging how something
    # actually looks.
    "front": mathutils.Vector((0, -1, 0)),
    "back": mathutils.Vector((0, 1, 0)),
    "left": mathutils.Vector((-1, 0, 0)),
    "right": mathutils.Vector((1, 0, 0)),
    "top": mathutils.Vector((0, 0, 1)),
    # Perspective vantage points — real depth and shape, like actually
    # looking at the thing from somewhere. "hero" is an alias for the
    # front-right corner, kept as the default single-view angle.
    "hero_front_right": mathutils.Vector((1, -1, 0.75)).normalized(),
    "hero_front_left": mathutils.Vector((-1, -1, 0.75)).normalized(),
    "hero_back_right": mathutils.Vector((1, 1, 0.75)).normalized(),
    "hero_back_left": mathutils.Vector((-1, 1, 0.75)).normalized(),
    "hero_top": mathutils.Vector((0.3, -0.3, 1.6)).normalized(),
    "hero_low": mathutils.Vector((1, -1, 0.15)).normalized(),
}
VIEW_DIRECTIONS["hero"] = VIEW_DIRECTIONS["hero_front_right"]
PERSPECTIVE_VIEWS = {
    "hero", "hero_front_right", "hero_front_left",
    "hero_back_right", "hero_back_left", "hero_top", "hero_low",
}

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.wm.obj_import(
    filepath=mesh_obj_path,
    up_axis="Z",
    forward_axis="Y",
    use_split_objects=False,
    use_split_groups=False,
)

imported = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
if not imported:
    raise RuntimeError(f"No mesh objects imported from {mesh_obj_path}")
model = imported[0]

bpy.context.view_layer.objects.active = model
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")

# Convert imported material colors from sRGB to Linear space for true saturation
for mat in bpy.data.materials:
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            base_col = list(bsdf.inputs["Base Color"].default_value)
            lin_r = srgb_to_linear(base_col[0])
            lin_g = srgb_to_linear(base_col[1])
            lin_b = srgb_to_linear(base_col[2])
            bsdf.inputs["Base Color"].default_value = (lin_r, lin_g, lin_b, base_col[3])
            bsdf.inputs["Roughness"].default_value = 0.45

            # Detect glowing accent colors (warm lanterns, neon accents)
            is_warm_glow = (lin_r > 0.75 and lin_g > 0.65 and lin_b < 0.65)
            is_neon_glow = (lin_g > 0.8 and lin_b > 0.8 and lin_r < 0.4)
            if is_warm_glow or is_neon_glow:
                try:
                    if "Emission Color" in bsdf.inputs:
                        bsdf.inputs["Emission Color"].default_value = (lin_r, lin_g, lin_b, 1.0)
                    if "Emission Strength" in bsdf.inputs:
                        bsdf.inputs["Emission Strength"].default_value = 6.0
                except Exception:
                    pass

corners = [model.matrix_world @ mathutils.Vector(c) for c in model.bound_box]
min_corner = mathutils.Vector((min(c[i] for c in corners) for i in range(3)))
max_corner = mathutils.Vector((max(c[i] for c in corners) for i in range(3)))
center = (min_corner + max_corner) / 2
extent = max((max_corner - min_corner)[i] for i in range(3))
distance = extent * 3 + 5
ortho_scale = extent * 1.3 + 1

scene = bpy.context.scene
scene.render.resolution_x = image_size
scene.render.resolution_y = image_size
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"

if engine == "cycles":
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    # Add ground shadow catcher (like MagicaVoxel's ground plane)
    bpy.ops.mesh.primitive_plane_add(size=extent * 10 + 20, location=(center.x, center.y, min_corner.z))
    ground = bpy.context.active_object
    ground.is_shadow_catcher = True

    # Material micro-bevels for MagicaVoxel voxel edge definition
    for mat in bpy.data.materials:
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                try:
                    bevel = mat.node_tree.nodes.new("ShaderNodeBevel")
                    bevel.inputs["Radius"].default_value = 0.04
                    bevel.samples = 4
                    mat.node_tree.links.new(bevel.outputs["Normal"], bsdf.inputs["Normal"])
                except Exception:
                    pass

    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (*preset["world_color"], 1.0)
        bg.inputs["Strength"].default_value = preset.get("world_strength", 0.5)

else:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_gtao = True
    scene.eevee.gtao_factor = 1.0
    scene.eevee.gtao_distance = max(extent * 0.15, 0.5)

    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = False
    scene.world.color = preset["world_color"]

# Key Sun
sun_data = bpy.data.lights.new(name="Sun", type="SUN")
sun_data.energy = preset["key_energy"]
sun_data.color = preset["key_color"]
if hasattr(sun_data, "angle"):
    sun_data.angle = preset.get("key_angle", 0.08)
sun_obj = bpy.data.objects.new("Sun", sun_data)
sun_obj.rotation_euler = preset["key_rotation"]
bpy.context.collection.objects.link(sun_obj)

# Fill Light
fill_data = bpy.data.lights.new(name="Fill", type="SUN")
fill_data.energy = preset["fill_energy"]
fill_data.color = preset["fill_color"]
fill_obj = bpy.data.objects.new("Fill", fill_data)
fill_obj.rotation_euler = preset["fill_rotation"]
bpy.context.collection.objects.link(fill_obj)

# Camera
camera_data = bpy.data.cameras.new("Camera")
camera_obj = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera_obj)
scene.camera = camera_obj

for view in views:
    if view not in VIEW_DIRECTIONS:
        raise ValueError(f"Unknown view {view!r}: expected one of {sorted(VIEW_DIRECTIONS)}")
    direction = VIEW_DIRECTIONS[view]

    if view in PERSPECTIVE_VIEWS:
        camera_data.type = "PERSP"
        camera_data.lens = 45
        cam_distance = extent * 2.2 + 4
    else:
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = ortho_scale
        cam_distance = distance

    camera_obj.location = center + direction * cam_distance
    look_direction = (center - camera_obj.location).normalized()
    camera_obj.rotation_euler = look_direction.to_track_quat("-Z", "Y").to_euler()

    scene.render.filepath = f"{output_dir}/{view}.png"
    bpy.ops.render.render(write_still=True)
