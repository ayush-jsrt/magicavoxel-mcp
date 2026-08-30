from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_cylinder
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.vox_io import read_vox, write_vox

master = read_vox("scratch/phase1_base.vox")

# Palette entries for tree and lantern
master.set_palette_entry(22, 44, 38, 48)    # Charcoal trunk
master.set_palette_entry(23, 30, 26, 34)    # Dark bark
master.set_palette_entry(40, 68, 122, 58)   # Mid green
master.set_palette_entry(41, 48, 95, 42)    # Dark green
master.set_palette_entry(42, 92, 152, 74)   # Light green
master.set_palette_entry(60, 255, 250, 160) # Glowing lantern core (emissive)
master.set_palette_entry(61, 255, 220, 85)  # Warm lantern edge

# Build isolated Tree & Lantern Prefab
tree = VoxelBuffer(36, 34, 52)
tree.palette = master.palette.copy()

# Trunk at local (12, 16, 0)
fill_box(tree, (8, 14, 0), (16, 18, 1), 22)
fill_cylinder(tree, (12, 16, 12), radius=3.4, height=24, axis="z", color_index=22)

# Overhanging branch towards +X
for b in range(18):
    bx = 12 + b
    by = 16 - int(b * 0.22)
    bz = 20 + int(b * 0.28)
    fill_box(tree, (bx, by - 1, bz), (bx, by + 1, bz + 2), 22)

# Hanging Lantern at (28, 12, 23)
lx, ly, lz = 28, 12, 23
tree.grid[lx, ly, lz] = tree.grid[lx, ly, lz - 1] = 23
fill_box(tree, (lx - 2, ly - 2, lz - 2), (lx + 2, ly + 2, lz - 2), 23)
fill_box(tree, (lx - 2, ly - 2, lz - 8), (lx + 2, ly + 2, lz - 8), 60) # Emissive core
for cx_off, cy_off in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
    for cz in range(lz - 8, lz - 2):
        tree.grid[lx + cx_off, ly + cy_off, cz] = 23
fill_box(tree, (lx - 2, ly - 2, lz - 9), (lx + 2, ly + 2, lz - 9), 23)

# Horizontal Tiered Foliage Pancake Layers
# Lower Left Tier (z=24-31)
fill_cylinder(tree, (10, 16, 26), radius=8.5, height=5, axis="z", color_index=40)
fill_cylinder(tree, (10, 16, 30), radius=7.5, height=4, axis="z", color_index=42)

# Upper Left Tier (z=33-39)
fill_cylinder(tree, (11, 16, 35), radius=7.0, height=4, axis="z", color_index=40)
fill_cylinder(tree, (11, 16, 39), radius=5.5, height=4, axis="z", color_index=42)

# Crown Tier (z=42-46)
fill_cylinder(tree, (11, 16, 44), radius=4.0, height=4, axis="z", color_index=40)

# Overhang Foliage Tier above lantern (z=27-34)
fill_cylinder(tree, (23, 14, 29), radius=6.0, height=5, axis="z", color_index=40)
fill_cylinder(tree, (23, 14, 33), radius=4.8, height=3, axis="z", color_index=42)

# Stamp Tree Prefab into Master at (6, 18, 8)
paste_vox_buffer(master, tree, offset_x=6, offset_y=18, offset_z=8, auto_crop=True)

write_vox(master, "scratch/phase2_tree.vox")