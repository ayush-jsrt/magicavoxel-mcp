import os
import numpy as np
from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_sphere, fill_cylinder
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.vox_io import write_vox

# --- 1. PALETTE SETUP ---
def init_palette(buf: VoxelBuffer):
    buf.set_palette_entry(1, 95, 60, 40)      # Base brown earth
    buf.set_palette_entry(2, 140, 195, 85)   # Main vibrant grass
    buf.set_palette_entry(3, 118, 168, 70)   # Stepped hill shadow
    buf.set_palette_entry(4, 162, 215, 102)  # Highlight grass
    buf.set_palette_entry(5, 205, 200, 188)  # Cobblestone path light (matte)
    buf.set_palette_entry(6, 175, 170, 158)  # Cobblestone path darker (matte)

    buf.set_palette_entry(10, 185, 226, 218) # Sky wall mint/cyan
    buf.set_palette_entry(11, 212, 240, 234) # Sky wall top rim
    buf.set_palette_entry(12, 235, 235, 225) # Soft cloud

    buf.set_palette_entry(20, 168, 102, 54)  # Warm bench wood
    buf.set_palette_entry(21, 130, 80, 42)   # Dark wood shadow
    buf.set_palette_entry(22, 44, 38, 48)    # Dark charcoal tree trunk
    buf.set_palette_entry(23, 30, 26, 34)    # Darkest tree bark

    buf.set_palette_entry(30, 248, 244, 236) # Cottage white stucco
    buf.set_palette_entry(31, 218, 208, 198) # Cottage wall shadow
    buf.set_palette_entry(32, 58, 112, 182)  # Blue roof
    buf.set_palette_entry(33, 40, 80, 142)   # Blue roof ridge/shadow
    buf.set_palette_entry(34, 145, 148, 155) # Chimney stone
    buf.set_palette_entry(35, 240, 240, 240) # Smoke & Book white
    buf.set_palette_entry(36, 120, 75, 40)   # Timber trim

    buf.set_palette_entry(40, 68, 122, 58)   # Tree mid green
    buf.set_palette_entry(41, 48, 95, 42)    # Tree dark green
    buf.set_palette_entry(42, 92, 152, 74)   # Tree light green
    buf.set_palette_entry(43, 80, 135, 62)   # Bush/shrub green

    buf.set_palette_entry(50, 198, 152, 98)  # Hair blonde/brown
    buf.set_palette_entry(51, 255, 214, 186) # Peach skin tone
    buf.set_palette_entry(52, 68, 118, 180)  # Blue sweater
    buf.set_palette_entry(53, 56, 44, 38)    # Dark brown pants
    buf.set_palette_entry(54, 30, 30, 30)    # Eyes charcoal

    buf.set_palette_entry(60, 255, 245, 140) # Glowing lantern core (emissive)
    buf.set_palette_entry(61, 255, 210, 80)  # Lantern warm edge (emissive)
    buf.set_palette_entry(62, 230, 52, 52)   # Red flower
    buf.set_palette_entry(63, 248, 208, 42)  # Yellow flower
    buf.set_palette_entry(64, 218, 88, 38)   # Terracotta pot
    buf.set_palette_entry(65, 78, 162, 68)   # Plant foliage

# Master Canvas
master = VoxelBuffer(84, 84, 76)
init_palette(master)

fill_box(master, (4, 4, 0), (79, 79, 5), 1)
fill_box(master, (4, 4, 6), (79, 79, 7), 2)
for z in range(8):
    master.grid[4, 4, z] = master.grid[4, 79, z] = master.grid[79, 4, z] = master.grid[79, 79, z] = 0

fill_box(master, (4, 4, 8), (6, 79, 70), 10)
fill_box(master, (4, 77, 8), (79, 79, 70), 10)
fill_box(master, (4, 4, 69), (6, 79, 70), 11)
fill_box(master, (4, 77, 69), (79, 79, 70), 11)
for z in range(60, 71):
    diff = z - 60
    for step in range(diff):
        master.grid[4, 4 + step, z] = master.grid[4 + step, 4, z] = 0
        master.grid[79 - step, 79, z] = master.grid[79, 79 - step, z] = 0

fill_sphere(master, (42, 77, 58), radius=4.5, color_index=12)

# Stepped background hills
fill_box(master, (4, 34, 8), (38, 79, 11), 2)
fill_box(master, (4, 44, 12), (34, 79, 15), 3)
fill_box(master, (4, 54, 16), (30, 79, 19), 2)
fill_box(master, (4, 64, 20), (26, 79, 23), 4)

fill_box(master, (44, 36, 8), (79, 79, 10), 2)
fill_box(master, (52, 44, 11), (79, 79, 13), 3)
fill_box(master, (60, 52, 14), (79, 79, 16), 4)

# --- TREE & LANTERN ---
tree = VoxelBuffer(34, 30, 48)
init_palette(tree)
fill_box(tree, (8, 12, 0), (16, 16, 1), 22)
fill_cylinder(tree, (12, 14, 11), radius=3.2, height=22, axis="z", color_index=22)

for b in range(16):
    bx = 12 + b
    by = 14 - int(b * 0.2)
    bz = 18 + int(b * 0.3)
    fill_box(tree, (bx, by - 1, bz), (bx, by + 1, bz + 2), 22)

lx, ly, lz = 26, 11, 22
tree.grid[lx, ly, lz] = tree.grid[lx, ly, lz - 1] = 23
fill_box(tree, (lx - 2, ly - 2, lz - 2), (lx + 2, ly + 2, lz - 2), 23)
fill_box(tree, (lx - 2, ly - 2, lz - 7), (lx + 2, ly + 2, lz - 7), 60)
for cx_off, cy_off in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
    for cz in range(lz - 7, lz - 2):
        tree.grid[lx + cx_off, ly + cy_off, cz] = 23
fill_box(tree, (lx - 2, ly - 2, lz - 8), (lx + 2, ly + 2, lz - 8), 23)

fill_cylinder(tree, (10, 14, 24), radius=8.0, height=4, axis="z", color_index=40)
fill_cylinder(tree, (10, 14, 28), radius=7.0, height=3, axis="z", color_index=42)
fill_cylinder(tree, (11, 14, 32), radius=6.5, height=4, axis="z", color_index=40)
fill_cylinder(tree, (11, 14, 36), radius=5.0, height=3, axis="z", color_index=42)
fill_cylinder(tree, (11, 14, 40), radius=4.0, height=4, axis="z", color_index=40)
fill_cylinder(tree, (21, 12, 27), radius=5.5, height=4, axis="z", color_index=40)
fill_cylinder(tree, (21, 12, 31), radius=4.5, height=3, axis="z", color_index=42)

paste_vox_buffer(master, tree, offset_x=6, offset_y=20, offset_z=8, auto_crop=True)

# --- COTTAGE ---
cottage = VoxelBuffer(24, 24, 28)
init_palette(cottage)
fill_box(cottage, (2, 2, 0), (20, 20, 12), 30)
for cx in (2, 20):
    for cy in (2, 20):
        fill_box(cottage, (cx, cy, 0), (cx, cy, 12), 36)

fill_box(cottage, (8, 2, 0), (14, 2, 9), 36)
fill_box(cottage, (9, 2, 0), (13, 2, 8), 21)

fill_box(cottage, (20, 8, 4), (20, 14, 9), 36)
fill_box(cottage, (20, 9, 5), (20, 13, 8), 10)
fill_box(cottage, (21, 7, 3), (21, 15, 4), 64)
fill_box(cottage, (21, 8, 5), (21, 14, 5), 65)

for r in range(9):
    z_lvl = 12 + r
    fill_box(cottage, (1 + r, 1, z_lvl), (21 - r, 21, z_lvl), 32)
    fill_box(cottage, (1 + r, 1, z_lvl), (1 + r, 21, z_lvl), 33)
    fill_box(cottage, (21 - r, 1, z_lvl), (21 - r, 21, z_lvl), 33)
    if r < 8:
        fill_box(cottage, (2 + r, 2, z_lvl), (20 - r, 2, z_lvl), 30)

fill_box(cottage, (15, 14, 12), (18, 17, 22), 34)
fill_box(cottage, (14, 13, 22), (19, 18, 23), 33)
fill_box(cottage, (16, 15, 25), (18, 17, 27), 35)
fill_box(cottage, (17, 16, 28), (19, 18, 30), 35)

paste_vox_buffer(master, cottage, offset_x=50, offset_y=46, offset_z=14, auto_crop=True)

# --- READING CHARACTER & BENCH ---
actor = VoxelBuffer(30, 22, 24)
init_palette(actor)

fill_box(actor, (4, 4, 0), (5, 5, 4), 21)
fill_box(actor, (4, 11, 0), (5, 12, 4), 21)
fill_box(actor, (21, 4, 0), (22, 5, 4), 21)
fill_box(actor, (21, 11, 0), (22, 12, 4), 21)
fill_box(actor, (3, 4, 5), (23, 12, 5), 20)
for gx in range(3, 24):
    actor.grid[gx, 8, 5] = 21

fill_box(actor, (4, 12, 5), (5, 12, 14), 21)
fill_box(actor, (21, 12, 5), (22, 12, 14), 21)
fill_box(actor, (3, 12, 8), (23, 12, 10), 20)
fill_box(actor, (3, 12, 12), (23, 12, 14), 20)

cx, cy, cz = 13, 7, 6
fill_box(actor, (cx - 3, cy - 3, cz - 5), (cx - 1, cy + 2, cz), 53)
fill_box(actor, (cx + 1, cy - 3, cz - 5), (cx + 3, cy + 2, cz), 53)
fill_box(actor, (cx - 3, cy - 4, cz - 5), (cx - 1, cy - 3, cz - 4), 21)
fill_box(actor, (cx + 1, cy - 4, cz - 5), (cx + 3, cy - 3, cz - 4), 21)

fill_box(actor, (cx - 4, cy, cz), (cx + 4, cy + 4, cz + 7), 52)
fill_box(actor, (cx - 5, cy - 1, cz + 1), (cx - 5, cy + 3, cz + 6), 52)
fill_box(actor, (cx + 5, cy - 1, cz + 1), (cx + 5, cy + 3, cz + 6), 52)
actor.grid[cx - 4, cy - 1, cz + 2] = 51
actor.grid[cx + 4, cy - 1, cz + 2] = 51

fill_box(actor, (cx - 3, cy - 2, cz + 2), (cx + 3, cy, cz + 3), 35)
fill_box(actor, (cx - 3, cy - 2, cz + 1), (cx + 3, cy, cz + 1), 20)

fill_box(actor, (cx - 4, cy, cz + 8), (cx + 4, cy + 5, cz + 15), 51)
actor.grid[cx - 2, cy - 1, cz + 10] = 54
actor.grid[cx + 2, cy - 1, cz + 10] = 54

fill_box(actor, (cx - 5, cy - 1, cz + 14), (cx + 5, cy + 6, cz + 17), 50)
fill_box(actor, (cx - 5, cy + 3, cz + 9), (cx + 5, cy + 6, cz + 16), 50)
fill_box(actor, (cx - 5, cy, cz + 9), (cx - 5, cy + 4, cz + 15), 50)
fill_box(actor, (cx + 5, cy, cz + 9), (cx + 5, cy + 4, cz + 15), 50)
fill_box(actor, (cx - 4, cy - 1, cz + 12), (cx + 4, cy - 1, cz + 15), 50)
actor.grid[cx, cy - 1, cz + 12] = 51

paste_vox_buffer(master, actor, offset_x=32, offset_y=20, offset_z=8, auto_crop=True)

# --- SIDE TABLE & POTTED PLANT ---
table = VoxelBuffer(12, 12, 14)
init_palette(table)
for lx in (2, 9):
    for ly in (2, 9):
        fill_box(table, (lx, ly, 0), (lx + 1, ly + 1, 4), 20)
fill_box(table, (1, 1, 5), (10, 10, 5), 20)
fill_box(table, (3, 3, 6), (8, 8, 8), 64)
fill_box(table, (2, 2, 8), (9, 9, 8), 64)
fill_box(table, (3, 3, 9), (8, 8, 12), 65)
table.grid[4, 2, 10] = table.grid[4, 9, 11] = table.grid[2, 5, 11] = table.grid[9, 6, 10] = 65

paste_vox_buffer(master, table, offset_x=54, offset_y=18, offset_z=8, auto_crop=True)

# --- PATHWAY, SHRUBS & WILDFLOWERS ---
path_coords = [
    (50, 44, 11, 4, 3), (46, 39, 10, 4, 3), (42, 34, 9, 4, 3),
    (38, 29, 8, 4, 3), (34, 23, 8, 4, 3), (30, 17, 8, 5, 4),
    (26, 11, 8, 5, 4), (22, 6, 8, 5, 3), (36, 12, 8, 4, 3), (42, 14, 8, 4, 3),
]
for px, py, pz, sx, sy in path_coords:
    for ix in range(px, px + sx):
        for iy in range(py, py + sy):
            col = 5 if (ix * 3 + iy * 5) % 4 != 0 else 6
            master.grid[ix, iy, pz] = col

for bx_pos, by_pos, bz_pos, br_pos in [(46, 64, 14, 4.5), (68, 40, 12, 3.5), (70, 32, 10, 3.0), (22, 44, 11, 4.0), (14, 56, 16, 4.5)]:
    fill_sphere(master, (bx_pos, by_pos, bz_pos), radius=br_pos, color_index=43)

flowers = [(18, 18, 8, 62), (22, 22, 8, 63), (25, 16, 8, 62), (16, 24, 8, 63), (46, 10, 8, 62), (50, 13, 8, 63), (40, 26, 8, 62), (60, 28, 10, 62)]
for fx, fy, fz, fcol in flowers:
    master.grid[fx, fy, fz] = master.grid[fx, fy, fz + 1] = 2
    master.grid[fx, fy, fz + 2] = fcol

for tx_pos, ty_pos, tz_pos in [(14, 14, 8), (22, 10, 8), (36, 6, 8), (42, 8, 8), (56, 18, 8), (60, 23, 9)]:
    master.grid[tx_pos, ty_pos, tz_pos] = master.grid[tx_pos, ty_pos, tz_pos + 1] = 4

out_vox = "c:/Users/ayush/Desktop/magicavoxel-mcp/cozy_reading_diorama.vox"
write_vox(master, out_vox)
print(f"Final modular diorama written to {out_vox}")