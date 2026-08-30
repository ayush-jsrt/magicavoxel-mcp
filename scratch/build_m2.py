from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_sphere
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.vox_io import read_vox, write_vox

master = read_vox("scratch/milestone_1_accurate.vox")

# Palette
master.set_palette_entry(30, 248, 244, 236) # Cottage white stucco
master.set_palette_entry(31, 218, 208, 198) # Wall shadow
master.set_palette_entry(32, 58, 112, 182)  # Blue roof tile
master.set_palette_entry(33, 40, 80, 142)   # Blue roof ridge/trim
master.set_palette_entry(34, 145, 148, 155) # Chimney stone light
master.set_palette_entry(38, 120, 122, 130) # Chimney stone dark
master.set_palette_entry(35, 248, 248, 248) # Pure white smoke & ridge cap
master.set_palette_entry(36, 120, 75, 40)   # Timber frame dark wood
master.set_palette_entry(37, 168, 108, 56)  # Door light wood
master.set_palette_entry(10, 185, 226, 218) # Glass tint
master.set_palette_entry(43, 80, 135, 62)   # Shrub dark green
master.set_palette_entry(44, 98, 158, 76)   # Shrub light green
master.set_palette_entry(62, 230, 52, 52)   # Red flower
master.set_palette_entry(63, 248, 208, 42)  # Yellow flower
master.set_palette_entry(64, 218, 88, 38)   # Terracotta
master.set_palette_entry(65, 78, 162, 68)   # Plant foliage

# Refined Cottage Prefab (26x26x34)
cottage = VoxelBuffer(26, 26, 34)
cottage.palette = master.palette.copy()

# 1. White Stucco Walls (18x18x11)
fill_box(cottage, (3, 3, 0), (21, 21, 11), 30)

# 2. Dark Timber Corner Posts & Base Sill
for cx in (3, 21):
    for cy in (3, 21):
        fill_box(cottage, (cx, cy, 0), (cx, cy, 11), 36)

# 3. Front Facade (Facing -Y at local y=3)
# Door Frame, Door, and Threshold Step
fill_box(cottage, (9, 3, 0), (15, 3, 9), 36)
fill_box(cottage, (10, 3, 0), (14, 3, 8), 37)
cottage.grid[13, 3, 4] = 36 # Doorknob
fill_box(cottage, (9, 2, 0), (15, 2, 0), 36) # Front threshold stone

# Attic window
fill_box(cottage, (11, 3, 13), (13, 3, 15), 36)
cottage.grid[12, 3, 14] = 10

# 4. Right Side Facade (Facing +X at local x=21)
fill_box(cottage, (21, 8, 4), (21, 15, 9), 36)
fill_box(cottage, (21, 9, 5), (21, 14, 8), 10)
cottage.grid[21, 11, 5] = cottage.grid[21, 11, 6] = cottage.grid[21, 11, 7] = cottage.grid[21, 11, 8] = 36
cottage.grid[21, 12, 5] = cottage.grid[21, 12, 6] = cottage.grid[21, 12, 7] = cottage.grid[21, 12, 8] = 36

# Terracotta flowerbox with flowers
fill_box(cottage, (22, 7, 3), (22, 16, 4), 64)
fill_box(cottage, (22, 8, 5), (22, 15, 5), 65)
cottage.grid[22, 9, 6] = 62
cottage.grid[22, 13, 6] = 63

# 5. Blue Pitched Roof (Pitched over X)
roof_h = 10
for r in range(roof_h + 1):
    z_lvl = 11 + r
    x_min = 2 + r
    x_max = 22 - r
    fill_box(cottage, (x_min, 2, z_lvl), (x_max, 22, z_lvl), 32)
    fill_box(cottage, (x_min, 2, z_lvl), (x_min, 22, z_lvl), 33)
    fill_box(cottage, (x_max, 2, z_lvl), (x_max, 22, z_lvl), 33)
    if r < roof_h:
        fill_box(cottage, (3 + r, 3, z_lvl), (21 - r, 3, z_lvl), 30)
        fill_box(cottage, (3 + r, 21, z_lvl), (21 - r, 21, z_lvl), 30)

# White ridge peak cap
fill_box(cottage, (11, 2, 21), (13, 22, 21), 35)

# 6. Stone Chimney with brick variation
for cz in range(12, 23):
    for cx in range(16, 20):
        for cy in range(13, 17):
            col = 34 if (cx + cy + cz) % 3 != 0 else 38
            cottage.grid[cx, cy, cz] = col
fill_box(cottage, (15, 12, 22), (20, 17, 23), 33)

# Smoke Puffs
fill_box(cottage, (17, 14, 25), (19, 16, 27), 35)
fill_box(cottage, (18, 15, 28), (20, 17, 30), 35)
fill_box(cottage, (19, 16, 31), (21, 18, 33), 35)

# Stamp Cottage onto plateau at (48, 46, 14)
paste_vox_buffer(master, cottage, offset_x=48, offset_y=46, offset_z=14, auto_crop=True)

# 7. Flanking Shrubbery & Flowerbushes around Cottage (as seen in reference)
# Right side bushes (flanking right wall)
fill_sphere(master, (71, 56, 17), radius=3.5, color_index=43)
fill_sphere(master, (72, 46, 16), radius=3.0, color_index=44)
fill_sphere(master, (73, 38, 14), radius=3.2, color_index=43)

# Left back rose bush (behind cottage doorway on slope)
fill_sphere(master, (46, 66, 16), radius=3.5, color_index=43)
master.grid[45, 65, 19] = 62
master.grid[47, 66, 18] = 62
master.grid[46, 67, 19] = 62

out_vox = "scratch/milestone_2_progress.vox"
write_vox(master, out_vox)
print(f"Enhanced Milestone 2 assembled: {master.voxel_count()} voxels -> {out_vox}")