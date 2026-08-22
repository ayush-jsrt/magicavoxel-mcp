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
mesh_obj_path, output_dir, views_csv, image_size, lighting = argv
views = views_csv.split(",")
image_size = int(image_size)

LIGHTING_PRESETS = {
    # Flat, neutral studio lighting — predictable, good for verifying shape
    # and color rather than mood.
    "neutral": {
        "world_color": (0.85, 0.85, 0.85),
        "key_energy": 3.0, "key_color": (1.0, 1.0, 1.0), "key_rotation": (0.6, 0.2, 0.4),
        "fill_energy": 1.0, "fill_color": (1.0, 1.0, 1.0), "fill_rotation": (-0.5, -0.3, 2.6),
    },
    # Dark ambient + warm low key light (simulating lantern/street-level
    # warmth) + cool blue rim fill from behind for contrast — for moody
    # night scenes. We have no true per-object emission/point lights yet
    # (see docs/ARCHITECTURE.md), so this is a global mood approximation,
    # not actual light sources tied to lanterns/neon in the model.
    "night": {
        "world_color": (0.015, 0.015, 0.035),
        "key_energy": 1.6, "key_color": (1.0, 0.55, 0.25), "key_rotation": (1.3, 0.1, 0.5),
        "fill_energy": 0.7, "fill_color": (0.4, 0.55, 1.0), "fill_rotation": (-0.6, -0.2, 2.9),
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

corners = [model.matrix_world @ mathutils.Vector(c) for c in model.bound_box]
min_corner = mathutils.Vector((min(c[i] for c in corners) for i in range(3)))
max_corner = mathutils.Vector((max(c[i] for c in corners) for i in range(3)))
center = (min_corner + max_corner) / 2
extent = max((max_corner - min_corner)[i] for i in range(3))
distance = extent * 3 + 5
ortho_scale = extent * 1.3 + 1

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = image_size
scene.render.resolution_y = image_size
scene.render.film_transparent = False
scene.eevee.taa_render_samples = 64
scene.eevee.use_gtao = True
scene.eevee.gtao_factor = 1.0
scene.eevee.gtao_distance = max(extent * 0.15, 0.5)
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = False
scene.world.color = preset["world_color"]

sun_data = bpy.data.lights.new(name="Sun", type="SUN")
sun_data.energy = preset["key_energy"]
sun_data.color = preset["key_color"]
sun_obj = bpy.data.objects.new("Sun", sun_data)
sun_obj.rotation_euler = preset["key_rotation"]
bpy.context.collection.objects.link(sun_obj)

fill_data = bpy.data.lights.new(name="Fill", type="SUN")
fill_data.energy = preset["fill_energy"]
fill_data.color = preset["fill_color"]
fill_obj = bpy.data.objects.new("Fill", fill_data)
fill_obj.rotation_euler = preset["fill_rotation"]
bpy.context.collection.objects.link(fill_obj)

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
        camera_data.lens = 40
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
