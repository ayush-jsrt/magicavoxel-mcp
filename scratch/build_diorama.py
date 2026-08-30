import os
import numpy as np
from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_sphere, fill_cylinder
from magicavoxel_mcp.vox_io import write_vox

# 84x84x76 canvas
canvas = VoxelBuffer(84, 84, 76)

# --- 1. PALETTE DEFINITIONS ---
# Earth & Grass
canvas.set_palette_entry(1, 95, 60, 40)      # Base brown earth
canvas.set_palette_entry(2, 138, 192, 85)   # Main vibrant grass
canvas.set_palette_entry(3, 118, 168, 70)   # Stepped grass tier
canvas.set_palette_entry(4, 158, 212, 100)  # Highlight grass
canvas.set_palette_entry(5, 230, 224, 208)  # Cobblestone path light
canvas.set_palette_entry(6, 195, 188, 172)  # Cobblestone path darker

# Sky Backdrop Walls
canvas.set_palette_entry(10, 185, 226, 218) # Sky wall mint/cyan
canvas.set_palette_entry(11, 212, 240, 234) # Sky wall top highlight
canvas.set_palette_entry(12, 248, 248, 235) # Sun / cloud soft white

# Wood & Tree
canvas.set_palette_entry(20, 168, 102, 54)  # Warm bench wood
canvas.set_palette_entry(21, 130, 80, 42)   # Dark wood shadow
canvas.set_palette_entry(22, 42, 38, 48)    # Dark charcoal tree trunk
canvas.set_palette_entry(23, 28, 25, 34)    # Darkest tree bark

# Cottage
canvas.set_palette_entry(30, 248, 244, 236) # Cottage white stucco
canvas.set_palette_entry(31, 218, 208, 198) # Cottage wall shadow
canvas.set_palette_entry(32, 58, 112, 182)  # Cottage blue roof
canvas.set_palette_entry(33, 40, 80, 142)   # Cottage blue roof trim/ridge
canvas.set_palette_entry(34, 145, 148, 155) # Chimney stone
canvas.set_palette_entry(35, 255, 255, 255) # Smoke & Book pure white
canvas.set_palette_entry(36, 120, 75, 40)   # Window & Door wood trim

# Foliage
canvas.set_palette_entry(40, 68, 122, 58)   # Tree foliage mid green
canvas.set_palette_entry(41, 48, 95, 42)    # Tree foliage dark green
canvas.set_palette_entry(42, 92, 152, 74)   # Tree foliage light green
canvas.set_palette_entry(43, 80, 135, 62)   # Bush/shrub green

# Character
canvas.set_palette_entry(50, 198, 152, 98)  # Hair blonde/brown
canvas.set_palette_entry(51, 255, 214, 186) # Peach skin tone
canvas.set_palette_entry(52, 68, 118, 180)  # Blue sweater
canvas.set_palette_entry(53, 56, 44, 38)    # Dark brown pants
canvas.set_palette_entry(54, 30, 30, 30)    # Eyes charcoal

# Accents & Lighting
canvas.set_palette_entry(60, 255, 250, 180) # Glowing lantern core
canvas.set_palette_entry(61, 255, 224, 98)  # Lantern warm edge
canvas.set_palette_entry(62, 230, 52, 52)   # Red flower
canvas.set_palette_entry(63, 248, 208, 42)  # Yellow flower
canvas.set_palette_entry(64, 218, 88, 38)   # Terracotta pot
canvas.set_palette_entry(65, 78, 162, 68)   # Plant foliage

# --- 2. BASE PLATFORM & STEPPED TERRAIN ---
# Brown earth base (4 <= x,y <= 79, 0 <= z <= 5)
fill_box(canvas, (4, 4, 0), (79, 79, 5), 1)

# Main grass surface (4 <= x,y <= 79, 6 <= z <= 7)
fill_box(canvas, (4, 4, 6), (79, 79, 7), 2)

# Bevel base platform outer corners
for z in range(8):
    canvas.grid[4, 4, z] = 0
    canvas.grid[4, 79, z] = 0
    canvas.grid[79, 4, z] = 0
    canvas.grid[79, 79, z] = 0

# Stepped rolling green hills in back-center & left
fill_box(canvas, (4, 36, 8), (36, 79, 11), 2)
fill_box(canvas, (4, 46, 12), (32, 79, 15), 3)
fill_box(canvas, (4, 56, 16), (28, 79, 19), 2)
fill_box(canvas, (4, 66, 20), (24, 79, 23), 4)

# Back-right hill under cottage
fill_box(canvas, (44, 38, 8), (79, 79, 10), 2)
fill_box(canvas, (52, 46, 11), (79, 79, 13), 3)
fill_box(canvas, (60, 54, 14), (79, 79, 16), 4)

# --- 3. DIORAMA CORNER SKY WALLS ---
fill_box(canvas, (4, 4, 8), (6, 79, 70), 10)
fill_box(canvas, (4, 77, 8), (79, 79, 70), 10)
fill_box(canvas, (4, 4, 69), (6, 79, 70), 11)
fill_box(canvas, (4, 77, 69), (79, 79, 70), 11)

for z in range(60, 71):
    diff = z - 60
    for step in range(diff):
        canvas.grid[4, 4 + step, z] = 0
        canvas.grid[4 + step, 4, z] = 0
        canvas.grid[79 - step, 79, z] = 0
        canvas.grid[79, 79 - step, z] = 0

# Soft cloud on back wall
fill_sphere(canvas, (42, 77, 58), radius=4.5, color_index=12)

# --- 4. COBBLESTONE PATHWAY ---
path_segments = [
    (52, 46, 11, 4, 3),
    (48, 42, 10, 4, 3),
    (44, 37, 9, 4, 3),
    (40, 32, 8, 4, 3),
    (37, 26, 8, 4, 3),
    (34, 20, 8, 4, 4),
    (30, 14, 8, 4, 3),
    (27, 8, 8, 4, 3),
    (36, 15, 8, 4, 3),
    (42, 16, 8, 3, 3),
]
for px, py, pz, sx, sy in path_segments:
    for ix in range(px, px + sx):
        for iy in range(py, py + sy):
            col = 5 if (ix * 3 + iy * 5) % 4 != 0 else 6
            canvas.grid[ix, iy, pz] = col

# --- 5. COTTAGE HOUSE ---
hx, hy, hz = 52, 48, 14
fill_box(canvas, (hx, hy, hz), (hx + 17, hy + 17, hz + 11), 30)

for cx in (hx, hx + 17):
    for cy in (hy, hy + 17):
        fill_box(canvas, (cx, cy, hz), (cx, cy, hz + 11), 36)

# Front Door
fill_box(canvas, (hx + 5, hy, hz), (hx + 10, hy, hz + 8), 36)
fill_box(canvas, (hx + 6, hy, hz), (hx + 9, hy, hz + 7), 21)

# Right Window with flower box
fill_box(canvas, (hx + 17, hy + 6, hz + 4), (hx + 17, hy + 11, hz + 8), 36)
fill_box(canvas, (hx + 17, hy + 7, hz + 5), (hx + 17, hy + 10, hz + 7), 10)
fill_box(canvas, (hx + 18, hy + 5, hz + 3), (hx + 18, hy + 12, hz + 4), 64)
fill_box(canvas, (hx + 18, hy + 6, hz + 5), (hx + 18, hy + 11, hz + 5), 65)

# Blue Gabled Roof (Pitched over X)
roof_h = 8
for r in range(roof_h + 1):
    z_level = hz + 11 + r
    x_min = hx - 2 + r
    x_max = hx + 19 - r
    fill_box(canvas, (x_min, hy - 2, z_level), (x_max, hy + 19, z_level), 32)
    fill_box(canvas, (x_min, hy - 2, z_level), (x_min, hy + 19, z_level), 33)
    fill_box(canvas, (x_max, hy - 2, z_level), (x_max, hy + 19, z_level), 33)

for r in range(roof_h):
    z_level = hz + 11 + r
    x_min = hx + r
    x_max = hx + 17 - r
    fill_box(canvas, (x_min, hy, z_level), (x_max, hy, z_level), 30)

# Stone Chimney with staggered smoke
fill_box(canvas, (hx + 13, hy + 11, hz + 12), (hx + 16, hy + 14, hz + 22), 34)
fill_box(canvas, (hx + 12, hy + 10, hz + 22), (hx + 17, hy + 15, hz + 23), 33)
fill_box(canvas, (hx + 14, hy + 12, hz + 25), (hx + 16, hy + 14, hz + 27), 35)
fill_box(canvas, (hx + 15, hy + 13, hz + 28), (hx + 17, hy + 15, hz + 30), 35)
fill_box(canvas, (hx + 16, hy + 14, hz + 31), (hx + 18, hy + 16, hz + 33), 35)

# --- 6. SCULPTED OAK TREE & WARM HANGING LANTERN ---
tx, ty, tz = 18, 24, 8

# Tree roots
fill_box(canvas, (tx - 4, ty - 2, tz), (tx + 4, ty + 2, tz + 1), 22)
fill_box(canvas, (tx - 2, ty - 4, tz), (tx + 2, ty + 4, tz + 1), 22)

# Solid thick trunk
fill_cylinder(canvas, (tx, ty, tz + 10), radius=3.2, height=20, axis="z", color_index=22)

# Arched overhanging branch towards the right (+X)
for b in range(14):
    bx = tx + b
    by = ty - int(b * 0.2)
    bz = tz + 18 + int(b * 0.25)
    fill_box(canvas, (bx, by - 1, bz), (bx, by + 1, bz + 2), 22)

# Hanging Lantern
lx, ly, lz = tx + 12, ty - 3, tz + 19
canvas.grid[lx, ly, lz] = 23
canvas.grid[lx, ly, lz - 1] = 23
fill_box(canvas, (lx - 2, ly - 2, lz - 2), (lx + 2, ly + 2, lz - 2), 23)
fill_box(canvas, (lx - 1, ly - 1, lz - 6), (lx + 1, ly + 1, lz - 3), 60)
for cx_off, cy_off in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
    for cz in range(lz - 6, lz - 2):
        canvas.grid[lx + cx_off, ly + cy_off, cz] = 61
fill_box(canvas, (lx - 2, ly - 2, lz - 7), (lx + 2, ly + 2, lz - 7), 23)

# Broad Horizontal Foliage Canopy Clouds
# Main left cloud (wide horizontal disc/ellipsoid)
fill_box(canvas, (tx - 10, ty - 8, tz + 22), (tx + 4, ty + 6, tz + 29), 40)
fill_box(canvas, (tx - 9, ty - 7, tz + 30), (tx + 3, ty + 5, tz + 33), 42)
fill_box(canvas, (tx - 8, ty - 6, tz + 34), (tx + 1, ty + 4, tz + 38), 40)
# Top crown cloud
fill_box(canvas, (tx - 6, ty - 4, tz + 39), (tx, ty + 2, tz + 43), 42)

# Overhanging right cloud (above lantern & branch)
fill_box(canvas, (tx + 2, ty - 6, tz + 24), (tx + 14, ty + 3, tz + 31), 40)
fill_box(canvas, (tx + 3, ty - 5, tz + 32), (tx + 12, ty + 2, tz + 36), 42)

# Sculpt rounded edges on foliage boxes
for fx, fy, fz, fr in [(tx - 3, ty - 1, tz + 28, 8.5), (tx + 8, ty - 1, tz + 29, 6.5), (tx - 3, ty - 1, tz + 39, 5.5)]:
    fill_sphere(canvas, (fx, fy, fz), radius=fr, color_index=40)

# --- 7. WOODEN BENCH & CHIBI READING CHARACTER ---
bx, by, bz = 36, 24, 8

for leg_x in (bx, bx + 13):
    for leg_y in (by, by + 6):
        fill_box(canvas, (leg_x, leg_y, bz), (leg_x + 1, leg_y + 1, bz + 3), 21)

fill_box(canvas, (bx - 1, by, bz + 4), (bx + 14, by + 7, bz + 4), 20)
for gx in range(bx - 1, bx + 15):
    canvas.grid[gx, by + 3, bz + 4] = 21

fill_box(canvas, (bx, by + 7, bz + 4), (bx + 1, by + 7, bz + 12), 21)
fill_box(canvas, (bx + 13, by + 7, bz + 4), (bx + 14, by + 7, bz + 12), 21)
fill_box(canvas, (bx - 1, by + 7, bz + 7), (bx + 14, by + 7, bz + 8), 20)
fill_box(canvas, (bx - 1, by + 7, bz + 10), (bx + 14, by + 7, bz + 12), 20)

# Chibi Character
cx, cy, cz = bx + 6, by + 2, bz + 5

fill_box(canvas, (cx - 2, cy - 2, cz - 4), (cx - 1, cy + 2, cz), 53)
fill_box(canvas, (cx + 1, cy - 2, cz - 4), (cx + 2, cy + 2, cz), 53)
fill_box(canvas, (cx - 2, cy - 3, cz - 4), (cx - 1, cy - 2, cz - 3), 21)
fill_box(canvas, (cx + 1, cy - 3, cz - 4), (cx + 2, cy - 2, cz - 3), 21)

# Torso (Blue sweater)
fill_box(canvas, (cx - 3, cy, cz), (cx + 3, cy + 3, cz + 6), 52)
fill_box(canvas, (cx - 4, cy - 1, cz + 1), (cx - 4, cy + 2, cz + 5), 52)
fill_box(canvas, (cx + 4, cy - 1, cz + 1), (cx + 4, cy + 2, cz + 5), 52)
canvas.grid[cx - 3, cy - 1, cz + 2] = 51
canvas.grid[cx + 3, cy - 1, cz + 2] = 51

# Open White Book in lap
fill_box(canvas, (cx - 2, cy - 2, cz + 2), (cx + 2, cy, cz + 2), 35)
fill_box(canvas, (cx - 2, cy - 2, cz + 1), (cx + 2, cy, cz + 1), 20)

# Head
fill_box(canvas, (cx - 3, cy, cz + 7), (cx + 3, cy + 4, cz + 13), 51)
canvas.grid[cx - 2, cy - 1, cz + 9] = 54
canvas.grid[cx + 2, cy - 1, cz + 9] = 54

# Blonde Hair
fill_box(canvas, (cx - 4, cy - 1, cz + 12), (cx + 4, cy + 5, cz + 15), 50)
fill_box(canvas, (cx - 4, cy + 3, cz + 8), (cx + 4, cy + 5, cz + 14), 50)
fill_box(canvas, (cx - 4, cy, cz + 8), (cx - 4, cy + 4, cz + 13), 50)
fill_box(canvas, (cx + 4, cy, cz + 8), (cx + 4, cy + 4, cz + 13), 50)
fill_box(canvas, (cx - 3, cy - 1, cz + 11), (cx + 3, cy - 1, cz + 13), 50)
canvas.grid[cx, cy - 1, cz + 11] = 51 # Hair center part

# --- 8. SIDE TABLE & POTTED PLANT ---
sx, sy, sz = bx + 18, by + 1, bz
for lx in (sx, sx + 5):
    for ly in (sy, sy + 5):
        fill_box(canvas, (lx, ly, sz), (lx, ly, sz + 3), 20)
fill_box(canvas, (sx - 1, sy - 1, sz + 4), (sx + 6, sy + 6, sz + 4), 20)

fill_box(canvas, (sx + 1, sy + 1, sz + 5), (sx + 4, sy + 4, sz + 7), 64)
fill_box(canvas, (sx, sy, sz + 7), (sx + 5, sy + 5, sz + 7), 64)
fill_box(canvas, (sx + 1, sy + 1, sz + 8), (sx + 4, sy + 4, sz + 11), 65)
canvas.grid[sx + 2, sy, sz + 9] = 65
canvas.grid[sx + 2, sy + 5, sz + 10] = 65
canvas.grid[sx, sy + 2, sz + 10] = 65
canvas.grid[sx + 5, sy + 3, sz + 9] = 65

# --- 9. SHRUBS & WILDFLOWERS ---
shrub_coords = [
    (48, 66, 14, 4.0),
    (70, 42, 12, 3.5),
    (72, 34, 10, 3.0),
    (24, 46, 11, 3.5),
    (14, 58, 16, 4.5),
]
for bx_pos, by_pos, bz_pos, br_pos in shrub_coords:
    fill_sphere(canvas, (bx_pos, by_pos, bz_pos), radius=br_pos, color_index=43)

flowers = [
    (20, 20, 8, 62),
    (24, 24, 8, 63),
    (27, 18, 8, 62),
    (18, 26, 8, 63),
    (48, 10, 8, 62),
    (52, 14, 8, 63),
    (42, 28, 8, 62),
    (46, 24, 8, 63),
    (62, 30, 10, 62),
]
for fx, fy, fz, fcol in flowers:
    canvas.grid[fx, fy, fz] = 2
    canvas.grid[fx, fy, fz + 1] = 2
    canvas.grid[fx, fy, fz + 2] = fcol

tufts = [
    (16, 15, 8), (24, 12, 8), (38, 8, 8), (44, 10, 8),
    (58, 20, 8), (62, 25, 9), (30, 36, 8), (22, 34, 8)
]
for tx_pos, ty_pos, tz_pos in tufts:
    canvas.grid[tx_pos, ty_pos, tz_pos] = 4
    canvas.grid[tx_pos, ty_pos, tz_pos + 1] = 4

# Save output .vox file
out_vox = "c:/Users/ayush/Desktop/magicavoxel-mcp/scratch/cozy_reading_diorama.vox"
write_vox(canvas, out_vox)
print(f"Master diorama generated successfully with {canvas.voxel_count()} voxels -> {out_vox}")