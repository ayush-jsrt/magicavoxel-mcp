---
name: voxel-art-director
description: End-to-end framework and best practices for creating complex 3D voxel art, modular scenes, dioramas, and MagicaVoxel models using single-agent and multi-subagent prefab workflows with MagicaVoxel MCP.
---

# Voxel Art Director & Modular 3D Scene Architecture

This skill equips agents with a production-grade 3D voxel art pipeline. It prevents spatial drift, visual amnesia, scaling mismatches, and color collisions when generating simple models or large, multi-element dioramas.

---

## 🧭 1. Spatial Rules & Coordinate Conventions

Coordinate mapping across all tools and scripts:
* **$X$ = Width** (Left $\leftrightarrow$ Right)
* **$Y$ = Depth** (Front $\leftrightarrow$ Back / into the screen)
* **$Z$ = Height** (Up $\leftrightarrow$ Down — build tall objects by increasing $Z$)
* **Origin $(0, 0, 0)$**: The bottom-front-left corner of the canvas.
* **$Z=0$ Base Alignment Contract**: All ground-touching props and structures must start flush with $Z=0$ (the bottom of their local canvas).

---

## 🚦 2. Workflow Routing: Single-Agent vs. Subagent Prefabs

Choose the workflow mode based on scene complexity:

| Scenario | Mode | Architecture |
| :--- | :--- | :--- |
| Single asset or model $\le 32 \times 32 \times 32$ (e.g. sword, chair, character, small tree) | **Mode A: Single-Agent Phased Sculpting** | Built sequentially in one canvas using phased blockout, region handles, and micro-renders. |
| Complex scene $> 32^3$ with $2+$ distinct objects (e.g. ramen shop, street corner, diorama, room) | **Mode B: Modular Subagenting & Level Assembly** | **MANDATORY**: Bounding boxes allocated $\to$ Subagents sculpt prefabs $\to$ Verified via local renders $\to$ Stamped with `stamp_vox`. |

> [!WARNING]
> **Anti-Monolith Enforcement**: Never attempt to build multi-object scenes ($>32^3$) in a single monolithic Python script or one-shot prompt. Monolithic generation causes proportion collapse, blobby foliage, and missed focal details. Always decompose into modular subagent prefabs.

---

## 📋 3. Mandatory Step 0: User-Facing Blueprint Presentation

**BEFORE modifying voxels or spawning child subagents**, the Orchestrator MUST present the structured scene blueprint to the user:

```markdown
### 🗺️ Master Scene Specification: [Scene Title]
- **Master Canvas Size**: [Width] x [Depth] x [Height] (e.g. 128 x 128 x 64)
- **Lighting & Mood**: `neutral` (Studio) or `night` (Moody)
- **Palette Theme**: [Summary of color palette, e.g. Cyberpunk Neon, Medieval Wood & Stone]

#### 📦 Component Allocation & Subagent Budget:
| Asset / Component | Subagent Canvas Size (w x d x h) | Target Offset (X, Y, Z) | Rotation | Palette Band | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `terrain_base` | 128 x 128 x 6 | (0, 0, 0) | 0° | 1–15 | Cobblestone ground & sidewalk |
| `ramen_cart` | 28 x 18 x 22 | (20, 16, 6) | 0° | 20–40 | Timber cart, counter & fabric roof |
| `vending_machine` | 12 x 10 x 24 | (60, 18, 6) | 0° | 50–70 | Illuminated beverage machine |
| `stool` (x2) | 6 x 6 x 8 | (24, 10, 6), (36, 10, 6) | 0° | 20–40 | Wooden bar stools |
```

---

## 🎨 4. Global Palette Contract (No Color Collisions)

MagicaVoxel models use a single shared 256-color palette. To prevent subagents from overwriting each other's colors when assembled:

1. **Reserved Index Bands**:
   * `1–19`: Base terrain, foundations, asphalt, stone, concrete.
   * `20–49`: Primary architecture, wood, walls, roofs.
   * `50–79`: Mechanical, metal, machinery, appliances.
   * `80–109`: Foliage, organics, plants, cloth, glass.
   * `110–139`: Emissive accents, neon lights, lanterns, signs.
2. **Pre-configured Palette**:
   * The Orchestrator sets up colors up front via `apply_palette()` and can save a `palette_template.vox` for subagents to import.

---

## 🤖 5. Mode B: Subagent Prefab Protocol

### Spawning Child Subagents
When delegating components, invoke subagents using `invoke_subagent` with a strict contract prompt:

```text
Role: Voxel Asset Sculptor - [Component Name]
Prompt:
You are building the '[Component Name]' asset for a larger voxel scene.
1. Create a canvas of EXACTLY {w}x{d}x{h} using create_canvas({w}, {d}, {h}).
2. Build the model flush with the floor (Z=0).
3. Use only palette indices in the assigned band ({band_start}-{band_end}).
4. Use add_shape and set_voxel to detail the model.
5. Verify your geometry using render(views=["hero"]).
6. Save the final asset using export_vox("scratch/props/{component_name}.vox").
```

---

## 🧩 6. Master Scene Assembly (NumPy Compositing)

Once all subagents export their `.vox` files, the Orchestrator stamps them into the master canvas using `magicavoxel_mcp.composite.paste_vox_buffer`:

```python
import numpy as np
from magicavoxel_mcp.composite import paste_vox_buffer
from magicavoxel_mcp.vox_io import read_vox, write_vox
from magicavoxel_mcp.voxel_buffer import VoxelBuffer

# 1. Create master canvas
master = VoxelBuffer(128, 128, 64)

# 2. Apply master palette
# master.set_palette_entry(index, r, g, b) ...

# 3. Stamp subagent assets
assets = [
    ("scratch/props/terrain_base.vox", 0, 0, 0, 0),
    ("scratch/props/ramen_cart.vox", 20, 16, 6, 0),
    ("scratch/props/vending_machine.vox", 60, 18, 6, 0),
    ("scratch/props/stool.vox", 24, 10, 6, 0),
    ("scratch/props/stool.vox", 36, 10, 6, 0),
]

for vox_path, ox, oy, oz, rot in assets:
    prop_buf = read_vox(vox_path)
    count, size = paste_vox_buffer(
        master, prop_buf, offset_x=ox, offset_y=oy, offset_z=oz, rotation=rot, auto_crop=True
    )
    print(f"Stamped {vox_path} at ({ox}, {oy}, {oz}) [rot={rot}°]: {count} voxels")

# 4. Save assembled master scene
write_vox(master, "master_scene.vox")
```

---

## 🛠️ 7. Mode A: Single-Agent Phased Construction

For single models, follow the 4-phase sequential pipeline:

* **Phase 1 (Foundation & Silhouette)**: Block out main volume. Call `render(views=["hero", "top", "front"])`.
* **Phase 2 (Architectural Features & CSG Carving)**: Cutouts, overhangs, secondary forms. Save `save_checkpoint("phase_2")`.
* **Phase 3 (Detailing & Accents)**: Micro-voxels, bevels, trims. Log all `region_id`s.
* **Phase 4 (Palette Polish)**: Final `apply_palette` adjustments.

---

## 🪓 8. Constructive Solid Geometry (CSG) & Subtractive Sculpting

Do NOT try to build complex hollow shapes out of hundreds of individual thin boxes. Instead, use **Subtractive Sculpting** (`add_shape` $\to$ `carve_shape`):

| Target Feature | Method | Tool Calls |
| :--- | :--- | :--- |
| **Arched Doorway / Gate** | Solid Wall + Horizontal Cylinder Carve | `add_shape(shape="box", ...)` $\to$ `carve_shape(shape="cylinder", axis="y", ...)` |
| **Window Cutout** | Solid Wall + Box Carve | `add_shape(shape="box", ...)` $\to$ `carve_shape(shape="box", ...)` |
| **Hollow Pot / Bowl / Mug** | Solid Cylinder + Inner Cylinder Carve | `add_shape(shape="cylinder", radius=6, ...)` $\to$ `carve_shape(shape="cylinder", radius=4, ...)` |
| **Roof Slope / Chamfer** | Solid Block + Angled Cylinder/Sphere Carve | `add_shape(shape="box", ...)` $\to$ `carve_shape(shape="cylinder", ...)` along eaves |
| **Hollow Room / Cave Interior**| Solid Cube + Inner Box/Sphere Carve | `add_shape(shape="box", size_x=24, ...)` $\to$ `carve_shape(shape="box", size_x=20, ...)` |

---

## 👁️ 9. Mandatory Visual Feedback Loop (Render After Every Change)

> [!IMPORTANT]
> **Look Before Proceeding**: Never sculpt blindly in bulk. Agents (both Orchestrator and Child Subagents) MUST invoke `render(views=["hero"])` after almost every meaningful change (blocking base $\to$ render, carving cutouts $\to$ render, detailing $\to$ render). 
> 
> * **Why**: 3D spatial drift occurs quickly without visual confirmation. Viewing the rendered image allows the agent to immediately spot misalignments, wrong proportions, and occlusion issues before stacking more voxels on top.
> * **Rule of Thumb**: Maximum 1–2 shape/carve operations between visual checks.

---

## 🛡️ Anti-Amnesia Protocol (Preserving Spatial Context)
To prevent image token pruning from causing spatial mistakes:
1. Always maintain the **Text Spatial Ledger** in your notes (never rely purely on visual memory from 5 steps ago).
2. Take micro-renders after almost every edit to refresh the active visual context.
3. Save checkpoints before risky structural edits.