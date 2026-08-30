from magicavoxel_mcp.voxel_buffer import VoxelBuffer
from magicavoxel_mcp.geometry import fill_box, fill_sphere
from magicavoxel_mcp.vox_io import write_vox

master = VoxelBuffer(84, 84, 76)

# Palette
master.set_palette_entry(1, 95, 60, 40)      # Base brown earth
master.set_palette_entry(2, 140, 195, 85)   # Main vibrant grass
master.set_palette_entry(3, 118, 168, 70)   # Stepped hill shadow
master.set_palette_entry(4, 162, 215, 102)  # Highlight grass
master.set_palette_entry(10, 185, 226, 218) # Sky wall mint/cyan
master.set_palette_entry(11, 212, 240, 234) # Sky wall top rim
master.set_palette_entry(12, 235, 235, 225) # Soft cloud

# Earth & Grass
fill_box(master, (4, 4, 0), (79, 79, 5), 1)
fill_box(master, (4, 4, 6), (79, 79, 7), 2)
for z in range(8):
    master.grid[4, 4, z] = master.grid[4, 79, z] = master.grid[79, 4, z] = master.grid[79, 79, z] = 0

# Sky Walls
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

# Deep stepped knolls in corner
fill_box(master, (4, 34, 8), (38, 79, 11), 2)
fill_box(master, (4, 44, 12), (34, 79, 15), 3)
fill_box(master, (4, 54, 16), (30, 79, 19), 2)
fill_box(master, (4, 64, 20), (26, 79, 23), 4)

fill_box(master, (44, 36, 8), (79, 79, 10), 2)
fill_box(master, (52, 44, 11), (79, 79, 13), 3)
fill_box(master, (60, 52, 14), (79, 79, 16), 4)

write_vox(master, "scratch/phase1_base.vox")