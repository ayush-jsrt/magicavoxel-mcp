"""Runs inside Blender's own Python (invoked via `blender --background
--python render_views.py -- <mesh_obj_path> <output_dir> <views_csv>
<image_size>`). Imports a cube mesh, frames a camera per requested view, and
renders each to <output_dir>/<view>.png.

Axis-aligned views (front/back/left/right/top) are orthographic — useful for
verifying exact geometry, but they flatten depth entirely and read poorly as
"what does this actually look like". "hero" is a perspective 3/4 angle (the
classic voxel-art screenshot angle) that actually conveys depth and shape.
"""

import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
mesh_obj_path, output_dir, views_csv, image_size = argv
views = views_csv.split(",")
image_size = int(image_size)

VIEW_DIRECTIONS = {
    "front": mathutils.Vector((0, -1, 0)),
    "back": mathutils.Vector((0, 1, 0)),
    "left": mathutils.Vector((-1, 0, 0)),
    "right": mathutils.Vector((1, 0, 0)),
    "top": mathutils.Vector((0, 0, 1)),
    "hero": mathutils.Vector((1, -1, 0.75)).normalized(),
}
PERSPECTIVE_VIEWS = {"hero"}

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
scene.world.color = (0.85, 0.85, 0.85)

sun_data = bpy.data.lights.new(name="Sun", type="SUN")
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
sun_obj.rotation_euler = (0.6, 0.2, 0.4)
bpy.context.collection.objects.link(sun_obj)

fill_data = bpy.data.lights.new(name="Fill", type="SUN")
fill_data.energy = 1.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
fill_obj.rotation_euler = (-0.5, -0.3, 2.6)
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
