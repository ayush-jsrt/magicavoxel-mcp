from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_cylinder
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.vox_io import read_vox, write_vox

master = read_vox("scratch/milestone_2_progress.vox")

# Palette
master.set_palette_entry(22, 44, 38, 48)    # Charcoal trunk
master.set_palette_entry(23, 30, 26, 34)    # Dark bark / struts
master.set_palette_entry(40, 68, 122, 58)   # Foliage mid green
master.set_palette_entry(41, 48, 95, 42)    # Foliage dark green
master.set_palette_entry(42, 92, 152, 74)   # Foliage light green highlight
master.set_palette_entry(60, 255, 250, 160) # Glowing lantern core (emissive)
master.set_palette_entry(61, 255, 220, 85)  # Warm lantern edge (emissive)

tree = VoxelBuffer(56, 44, 58)
tree.palette = master.palette.copy()

# Trunk Base at local (16, 20, 0)
tx, ty, tz = 16, 20, 0

# Flared roots
fill_box(tree, (tx - 6, ty - 4, 0), (tx + 6, ty + 4, 1), 22)
fill_box(tree, (tx - 4, ty - 6, 0), (tx + 4, ty + 6, 1), 22)

# Solid Vertical Trunk rising to z=24
fill_cylinder(tree, (tx, ty, 12), radius=3.5, height=24, axis="z", color_index=22)

# Long Arched Branch extending to the right (+X, -Y) towards local x=40, y=10
for b in range(26):
    bx = tx + b
    by = ty - int(b * 0.42)
    bz = 18 + int(b * 0.32)
    fill_box(tree, (bx, by - 1, bz), (bx, by + 1, bz + 2), 22)

# Hanging Lantern at branch tip (local x=tx+22=38, y=ty-9=11, z=24)
lx, ly, lz = tx + 22, ty - 9, 24
tree.grid[lx, ly, lz] = tree.grid[lx, ly, lz - 1] = 23 # Strut

# Lantern Top Cap (6x6)
fill_box(tree, (lx - 3, ly - 3, lz - 2), (lx + 3, ly + 3, lz - 2), 23)
# Emissive Core (6x6x8)
fill_box(tree, (lx - 2, ly - 2, lz - 9), (lx + 2, ly + 2, lz - 3), 60)
# Dark Corner Struts
for cx_off, cy_off in [(-3, -3), (-3, 3), (3, -3), (3, 3)]:
    for cz in range(lz - 9, lz - 2):
        tree.grid[lx + cx_off, ly + cy_off, cz] = 23
# Bottom Cap (6x6)
fill_box(tree, (lx - 3, ly - 3, lz - 10), (lx + 3, ly + 3, lz - 10), 23)

# Foliage Pancake Plates (Layered horizontal discs with stepped stepped edges)
# Plate 1: Lower-Left Main Tier (Local x=8, y=20, z=26..32, radius=11)
fill_cylinder(tree, (8, 20, 27), radius=11.0, height=4, axis="z", color_index=40)
fill_cylinder(tree, (8, 20, 30), radius=9.5, height=3, axis="z", color_index=42)

# Plate 2: Upper Mid Tier (Local x=14, y=20, z=33..39, radius=9)
fill_cylinder(tree, (14, 20, 34), radius=9.0, height=4, axis="z", color_index=40)
fill_cylinder(tree, (14, 20, 37), radius=7.8, height=3, axis="z", color_index=42)

# Plate 3: Crown (Local x=16, y=20, z=40..46, radius=6.5)
fill_cylinder(tree, (16, 20, 41), radius=6.5, height=4, axis="z", color_index=40)
fill_cylinder(tree, (16, 20, 44), radius=5.0, height=3, axis="z", color_index=42)

# Plate 4: Right Canopy Shelf above Lantern (Local x=28, y=14, z=28..34, radius=7.5)
fill_cylinder(tree, (28, 14, 29), radius=7.5, height=4, axis="z", color_index=40)
fill_cylinder(tree, (28, 14, 32), radius=6.2, height=3, axis="z", color_index=42)

# Stamp Tree Prefab into Master at (6, 14, 8)
paste_vox_buffer(master, tree, offset_x=6, offset_y=14, offset_z=8, auto_crop=True)

out_vox = "scratch/milestone_3_progress.vox"
write_vox(master, out_vox)
print(f"Broad Milestone 3 assembled: {master.voxel_count()} voxels -> {out_vox}")