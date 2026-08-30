from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box
from magicavoxel_mcp.vox_io import write_vox

# 84x84x76 Master Canvas
canvas = VoxelBuffer(84, 84, 76)

# Palette
canvas.set_palette_entry(1, 95, 60, 40)      # Base brown earth
canvas.set_palette_entry(2, 140, 195, 85)   # Main vibrant grass
canvas.set_palette_entry(3, 118, 168, 70)   # Stepped hill tier 2
canvas.set_palette_entry(4, 162, 215, 102)  # Highlight grass tier 3
canvas.set_palette_entry(10, 185, 226, 218) # Sky wall mint/cyan
canvas.set_palette_entry(11, 212, 240, 234) # Sky wall top highlight

# 1. Base Platform - Solid square block (4..79, 4..79)
fill_box(canvas, (4, 4, 0), (79, 79, 5), 1)
fill_box(canvas, (4, 4, 6), (79, 79, 7), 2)

# Bevel only the front-most open corners (x=79,y=4 and x=4,y=4 and x=79,y=79)
for z in range(8):
    # Front-center corner (x=79, y=4)
    canvas.grid[79, 4, z] = canvas.grid[78, 4, z] = canvas.grid[79, 5, z] = 0
    # Left front corner (x=4, y=4)
    canvas.grid[4, 4, z] = canvas.grid[5, 4, z] = canvas.grid[4, 5, z] = 0
    # Right back corner (x=79, y=79)
    canvas.grid[79, 79, z] = canvas.grid[78, 79, z] = canvas.grid[79, 78, z] = 0

# 2. Solid Sky Backdrop Walls (Flush with outer bounds at x=4 and y=79)
# Left wall: x=4..8, y=4..79, z=8..68
fill_box(canvas, (4, 4, 8), (8, 79, 68), 10)
# Back wall: x=4..79, y=75..79, z=8..68
fill_box(canvas, (4, 75, 8), (79, 79, 68), 10)

# Top highlight rim
fill_box(canvas, (4, 4, 68), (8, 79, 68), 11)
fill_box(canvas, (4, 75, 68), (79, 79, 68), 11)

# Fine 1-pixel micro-ladder steps on outer wall shoulders
for s in range(8):
    # Left wall front shoulder (descending down to y=4)
    for z in range(61 + s, 69):
        for x in range(4, 9):
            canvas.grid[x, 4 + s, z] = 0
    # Right wall right shoulder (descending down to x=79)
    for z in range(61 + s, 69):
        for y in range(75, 80):
            canvas.grid[79 - s, y, z] = 0

# 3. Clean, Smooth, Concentric Terraced Hills
# Tier 1 (z=8..10)
for x in range(8, 76):
    for y in range(24, 76):
        nx = (x - 36) / 28.0
        ny = (y - 12) / 24.0
        if nx*nx + ny*ny >= 1.0:
            for z in range(8, 11):
                canvas.grid[x, y, z] = 2

# Tier 2 (z=11..13)
for x in range(8, 76):
    for y in range(36, 76):
        nx = (x - 36) / 24.0
        ny = (y - 18) / 22.0
        if nx*nx + ny*ny >= 1.0:
            for z in range(11, 14):
                canvas.grid[x, y, z] = 3

# Tier 3 (z=14..16)
for x in range(8, 76):
    for y in range(46, 76):
        nx = (x - 36) / 20.0
        ny = (y - 24) / 20.0
        if nx*nx + ny*ny >= 1.0:
            for z in range(14, 17):
                canvas.grid[x, y, z] = 2

# Tier 4 (z=17..19)
fill_box(canvas, (8, 56, 17), (40, 75, 19), 4)

# Solid Cottage Foundation Plateau on the right
fill_box(canvas, (48, 42, 8), (75, 75, 13), 3)
fill_box(canvas, (52, 46, 14), (75, 75, 15), 2)

out_vox = "scratch/milestone_1_accurate.vox"
write_vox(canvas, out_vox)
print(f"Flush Milestone 1 built: {canvas.voxel_count()} voxels -> {out_vox}")