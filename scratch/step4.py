from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_sphere
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.vox_io import read_vox, write_vox

master = read_vox("scratch/phase3_cottage.vox")

# Palette entries
master.set_palette_entry(5, 205, 200, 188)  # Cobblestone path light (matte)
master.set_palette_entry(6, 175, 170, 158)  # Cobblestone path darker (matte)
master.set_palette_entry(20, 168, 102, 54)  # Warm bench wood
master.set_palette_entry(21, 130, 80, 42)   # Dark wood shadow
master.set_palette_entry(43, 80, 135, 62)   # Shrub green
master.set_palette_entry(50, 198, 152, 98)  # Hair blonde/brown
master.set_palette_entry(51, 255, 214, 186) # Peach skin tone
master.set_palette_entry(52, 68, 118, 180)  # Blue sweater
master.set_palette_entry(53, 56, 44, 38)    # Dark brown pants
master.set_palette_entry(54, 30, 30, 30)    # Eyes charcoal
master.set_palette_entry(62, 230, 52, 52)   # Red flower
master.set_palette_entry(63, 248, 208, 42)  # Yellow flower
master.set_palette_entry(64, 218, 88, 38)   # Terracotta pot
master.set_palette_entry(65, 78, 162, 68)   # Plant foliage

# 1. Reading Character & Bench
actor = VoxelBuffer(30, 22, 24)
actor.palette = master.palette.copy()

# Bench legs
fill_box(actor, (4, 4, 0), (5, 5, 4), 21)
fill_box(actor, (4, 11, 0), (5, 12, 4), 21)
fill_box(actor, (21, 4, 0), (22, 5, 4), 21)
fill_box(actor, (21, 11, 0), (22, 12, 4), 21)
# Bench seat slats
fill_box(actor, (3, 4, 5), (23, 12, 5), 20)
for gx in range(3, 24):
    actor.grid[gx, 8, 5] = 21

# Backrest
fill_box(actor, (4, 12, 5), (5, 12, 14), 21)
fill_box(actor, (21, 12, 5), (22, 12, 14), 21)
fill_box(actor, (3, 12, 8), (23, 12, 10), 20)
fill_box(actor, (3, 12, 12), (23, 12, 14), 20)

# Character sitting in center (local x=13, y=7, z=6)
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

# 2. Side Table & Potted Plant
table = VoxelBuffer(12, 12, 14)
table.palette = master.palette.copy()
for lx in (2, 9):
    for ly in (2, 9):
        fill_box(table, (lx, ly, 0), (lx + 1, ly + 1, 4), 20)
fill_box(table, (1, 1, 5), (10, 10, 5), 20)
fill_box(table, (3, 3, 6), (8, 8, 8), 64)
fill_box(table, (2, 2, 8), (9, 9, 8), 64)
fill_box(table, (3, 3, 9), (8, 8, 12), 65)
table.grid[4, 2, 10] = table.grid[4, 9, 11] = table.grid[2, 5, 11] = table.grid[9, 6, 10] = 65

paste_vox_buffer(master, table, offset_x=54, offset_y=18, offset_z=8, auto_crop=True)

# 3. Cobblestone Path
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

# 4. Bushes & Wildflowers
for bx_pos, by_pos, bz_pos, br_pos in [(46, 64, 14, 4.5), (68, 40, 12, 3.5), (70, 32, 10, 3.0), (22, 44, 11, 4.0), (14, 56, 16, 4.5)]:
    fill_sphere(master, (bx_pos, by_pos, bz_pos), radius=br_pos, color_index=43)

flowers = [(18, 18, 8, 62), (22, 22, 8, 63), (25, 16, 8, 62), (16, 24, 8, 63), (46, 10, 8, 62), (50, 13, 8, 63), (40, 26, 8, 62), (60, 28, 10, 62)]
for fx, fy, fz, fcol in flowers:
    master.grid[fx, fy, fz] = master.grid[fx, fy, fz + 1] = 2
    master.grid[fx, fy, fz + 2] = fcol

for tx_pos, ty_pos, tz_pos in [(14, 14, 8), (22, 10, 8), (36, 6, 8), (42, 8, 8), (56, 18, 8), (60, 23, 9)]:
    master.grid[tx_pos, ty_pos, tz_pos] = master.grid[tx_pos, ty_pos, tz_pos + 1] = 4

write_vox(master, "c:/Users/ayush/Desktop/magicavoxel-mcp/cozy_reading_diorama.vox")