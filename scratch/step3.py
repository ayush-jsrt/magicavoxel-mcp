from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.vox_io import read_vox, write_vox

master = read_vox("scratch/phase2_tree.vox")

# Cottage palette
master.set_palette_entry(30, 248, 244, 236) # White stucco
master.set_palette_entry(31, 218, 208, 198) # Wall shadow
master.set_palette_entry(32, 58, 112, 182)  # Blue roof
master.set_palette_entry(33, 40, 80, 142)   # Blue roof ridge/shadow
master.set_palette_entry(34, 145, 148, 155) # Chimney stone
master.set_palette_entry(35, 245, 245, 245) # Smoke white
master.set_palette_entry(36, 120, 75, 40)   # Timber trim
master.set_palette_entry(64, 218, 88, 38)   # Terracotta
master.set_palette_entry(65, 78, 162, 68)   # Flower foliage

cottage = VoxelBuffer(26, 26, 32)
cottage.palette = master.palette.copy()

# Stucco walls (18x18x12)
fill_box(cottage, (3, 3, 0), (21, 21, 12), 30)

# Corner posts
for cx in (3, 21):
    for cy in (3, 21):
        fill_box(cottage, (cx, cy, 0), (cx, cy, 12), 36)

# Front Door (facing -Y)
fill_box(cottage, (9, 3, 0), (15, 3, 9), 36)
fill_box(cottage, (10, 3, 0), (14, 3, 8), 21)

# Right Window with flowerbox (facing +X)
fill_box(cottage, (21, 9, 4), (21, 15, 9), 36)
fill_box(cottage, (21, 10, 5), (21, 14, 8), 10)
fill_box(cottage, (22, 8, 3), (22, 16, 4), 64)
fill_box(cottage, (22, 9, 5), (22, 15, 5), 65)

# Blue Gabled Roof (Pitched over X axis)
roof_h = 9
for r in range(roof_h + 1):
    z_lvl = 12 + r
    x_min = 2 + r
    x_max = 22 - r
    fill_box(cottage, (x_min, 2, z_lvl), (x_max, 22, z_lvl), 32)
    fill_box(cottage, (x_min, 2, z_lvl), (x_min, 22, z_lvl), 33)
    fill_box(cottage, (x_max, 2, z_lvl), (x_max, 22, z_lvl), 33)
    # Gable triangle wall
    if r < roof_h:
        fill_box(cottage, (3 + r, 3, z_lvl), (21 - r, 3, z_lvl), 30)

# Stone Chimney with staggered smoke puffs
fill_box(cottage, (16, 15, 12), (19, 18, 22), 34)
fill_box(cottage, (15, 14, 22), (20, 19, 23), 33)
fill_box(cottage, (17, 16, 25), (19, 18, 27), 35)
fill_box(cottage, (18, 17, 28), (20, 19, 30), 35)
fill_box(cottage, (19, 18, 31), (21, 20, 33), 35)

# Stamp Cottage at (48, 46, 14)
paste_vox_buffer(master, cottage, offset_x=48, offset_y=46, offset_z=14, auto_crop=True)

write_vox(master, "scratch/phase3_cottage.vox")