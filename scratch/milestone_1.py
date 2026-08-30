from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_sphere
from magicavoxel_mcp.vox_io import write_vox

# 84x84x76 Master Canvas
canvas = VoxelBuffer(84, 84, 76)

# Palette Initialization
canvas.set_palette_entry(1, 95, 60, 40)      # Base brown earth
canvas.set_palette_entry(2, 140, 195, 85)   # Main vibrant grass
canvas.set_palette_entry(3, 118, 168, 70)   # Stepped hill shadow
canvas.set_palette_entry(4, 162, 215, 102)  # Highlight grass
canvas.set_palette_entry(5, 205, 200, 188)  # Cobblestone path light (matte)
canvas.set_palette_entry(6, 175, 170, 158)  # Cobblestone path darker (matte)

canvas.set_palette_entry(10, 185, 226, 218) # Sky wall mint/cyan
canvas.set_palette_entry(11, 212, 240, 234) # Sky wall top rim
canvas.set_palette_entry(12, 235, 235, 225) # Soft cloud / sun

canvas.set_palette_entry(20, 168, 102, 54)  # Warm bench wood
canvas.set_palette_entry(21, 130, 80, 42)   # Dark wood shadow
canvas.set_palette_entry(22, 44, 38, 48)    # Dark charcoal tree trunk
canvas.set_palette_entry(23, 30, 26, 34)    # Darkest tree bark

canvas.set_palette_entry(30, 248, 244, 236) # Cottage white stucco
canvas.set_palette_entry(31, 218, 208, 198) # Cottage wall shadow
canvas.set_palette_entry(32, 58, 112, 182)  # Blue roof
canvas.set_palette_entry(33, 40, 80, 142)   # Blue roof ridge
canvas.set_palette_entry(34, 145, 148, 155) # Chimney stone
canvas.set_palette_entry(35, 240, 240, 240) # Smoke & Book white
canvas.set_palette_entry(36, 120, 75, 40)   # Timber trim

canvas.set_palette_entry(40, 68, 122, 58)   # Tree mid green
canvas.set_palette_entry(41, 48, 95, 42)    # Tree dark green
canvas.set_palette_entry(42, 92, 152, 74)   # Tree light green
canvas.set_palette_entry(43, 80, 135, 62)   # Bush/shrub green

canvas.set_palette_entry(50, 198, 152, 98)  # Hair blonde/brown
canvas.set_palette_entry(51, 255, 214, 186) # Peach skin tone
canvas.set_palette_entry(52, 68, 118, 180)  # Blue sweater
canvas.set_palette_entry(53, 56, 44, 38)    # Dark brown pants
canvas.set_palette_entry(54, 30, 30, 30)    # Eyes charcoal

canvas.set_palette_entry(60, 255, 245, 140) # Glowing lantern core (emissive)
canvas.set_palette_entry(61, 255, 210, 80)  # Lantern warm edge (emissive)
canvas.set_palette_entry(62, 230, 52, 52)   # Red flower
canvas.set_palette_entry(63, 248, 208, 42)  # Yellow flower
canvas.set_palette_entry(64, 218, 88, 38)   # Terracotta pot
canvas.set_palette_entry(65, 78, 162, 68)   # Plant foliage

# 1. Base Earth foundation (z=0..5)
fill_box(canvas, (4, 4, 0), (79, 79, 5), 1)

# 2. Main Turf surface (z=6..7)
fill_box(canvas, (4, 4, 6), (79, 79, 7), 2)

# Bevel base outer corners
for z in range(8):
    canvas.grid[4, 4, z] = canvas.grid[4, 79, z] = canvas.grid[79, 4, z] = canvas.grid[79, 79, z] = 0

# 3. Mint Corner Sky Walls (x=4, y=77)
fill_box(canvas, (4, 4, 8), (6, 79, 70), 10)
fill_box(canvas, (4, 77, 8), (79, 79, 70), 10)
fill_box(canvas, (4, 4, 69), (6, 79, 70), 11)
fill_box(canvas, (4, 77, 69), (79, 79, 70), 11)

# Smooth corner chamfer on sky walls
for z in range(60, 71):
    diff = z - 60
    for step in range(diff):
        canvas.grid[4, 4 + step, z] = canvas.grid[4 + step, 4, z] = 0
        canvas.grid[79 - step, 79, z] = canvas.grid[79, 79 - step, z] = 0

# Sun/cloud sphere on back wall
fill_sphere(canvas, (42, 77, 58), radius=4.5, color_index=12)

# 4. Stepped Green Hill Terraces
# Left/Center hill tiers
fill_box(canvas, (4, 34, 8), (38, 79, 11), 2)
fill_box(canvas, (4, 44, 12), (34, 79, 15), 3)
fill_box(canvas, (4, 54, 16), (30, 79, 19), 2)
fill_box(canvas, (4, 64, 20), (26, 79, 23), 4)

# Right hill tiers (foundation for cottage)
fill_box(canvas, (44, 36, 8), (79, 79, 10), 2)
fill_box(canvas, (52, 44, 11), (79, 79, 13), 3)
fill_box(canvas, (60, 52, 14), (79, 79, 16), 4)

out_vox = "scratch/diorama_progress.vox"
write_vox(canvas, out_vox)
print(f"Milestone 1 built: {canvas.voxel_count()} voxels -> {out_vox}")