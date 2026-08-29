---
name: voxel-art-director
description: End-to-end framework for creating 3D voxel art and MagicaVoxel dioramas using an interactive milestone-based pipeline with mandatory visual render checkpoints.
---

# Voxel Art Director & Interactive Milestone Architecture

This skill equips agents with a production-grade 3D voxel art pipeline. It prevents spatial drift, visual amnesia, scaling mismatches, and over-generation by breaking scene construction into **interactive, step-by-step milestones with mandatory user review gates**.

---

## 🧭 1. Spatial Rules & Coordinate Conventions

Coordinate mapping across all tools and scripts:
* **$X$ = Width** (Left $\leftrightarrow$ Right)
* **$Y$ = Depth** (Front $\leftrightarrow$ Back / into the screen)
* **$Z$ = Height** (Up $\leftrightarrow$ Down — build tall objects by increasing $Z$)
* **Origin $(0, 0, 0)$**: The bottom-front-left corner of the canvas.
* **$Z=0$ Base Alignment**: All ground-touching geometry starts flush with $Z=0$.

---

## 📐 2. The Atomic Voxel Scale Rule

Before choosing canvas dimensions, identify the **Smallest Resolvable Detail ($1\text{ voxel}$)**:
* **$1\text{ voxel}$**: Character eye slit, book page thickness, flower blossom, window mullion.
* **Focal Anchor Scale**: Character head $\approx 7$–$9$ voxels, total character height $\approx 18$–$22$ voxels.
* **Prop Proportions**: Cottage $\approx 1.5\times$ character height ($26$–$32$ voxels), Tree $\approx 2\times$ character height ($40$–$50$ voxels).
* **Master Canvas**: Extrapolate surrounding buffer $\to 64^3$ to $96^3$ for dioramas.

---

## 🔍 3. Mandatory Step 0: Reference & Requirement Deconstruction

**BEFORE writing any voxel commands or blueprints**, perform an explicit deconstruction:

1. **Feature & Geometry Matrix**: Deconstruct all objects into geometric primitives (boxes, cylinders, disks, spheres).
2. **Proportions & Focal Hierarchy**: Measure relative scale ratios between the primary subject and background environment.
3. **Palette & Material Sampling**: List RGB/HEX color tones and flag emissive surfaces (lanterns, neons).
4. **Spatial Occlusion Mapping**: Map foreground vs. background depth layers.

---

## 📋 4. Mandatory Step 1: Master Milestone Roadmap

Break down the scene into **4–6 ordered milestones**, starting from the foundation up:

```markdown
### 🗺️ Master Scene Specification: [Scene Title]
- **Canvas Dimensions**: [Width] x [Depth] x [Height] (e.g. 84 x 84 x 76)
- **Palette Theme**: [Summary of colors and lighting]

#### 🚩 Milestone Roadmap:
* **Milestone 1**: Base Platform, Terraced Terrain & Backdrop Sky Walls
* **Milestone 2**: Major Architectural Structure (e.g. Cottage / Main Building)
* **Milestone 3**: Primary Organic/Focal Prop (e.g. Oak Tree with Hanging Lantern)
* **Milestone 4**: Character & Central Seating / Vehicle
* **Milestone 5**: Set Dressing, Pathways, Foliage & Wildflowers
* **Milestone 6**: Palette Polish & Final Cycles Lighting Render
```

---

## 🛑 5. Interactive Milestone Execution Contract (STRICT)

> [!IMPORTANT]
> **One Milestone per Prompt Turn**:
> * An agent **MUST NEVER execute more than one milestone in a single response**.
> * The user MUST be given the opportunity to review, critique, suggest enhancements, or modify the scene after each milestone completion.

### Standard Turn Lifecycle for Each Milestone:
1. **Execute Milestone Geometry**: Use `add_shape`, `carve_shape`, `set_voxel`, or local modular stamping for the current milestone.
2. **Render Hero View**: Call `render(views=["hero"], engine="cycles")` to generate an up-to-date visual.
3. **Save Checkpoint**: Call `save_checkpoint(f"milestone_{N}")`.
4. **Present & Stop**: Present the rendered image, summarize what was built in this milestone, and **STOP to ask the user for feedback before proceeding to the next milestone**.

---

## 🪓 6. Constructive Solid Geometry (CSG) & Subtractive Sculpting

Do NOT build complex hollow shapes out of hundreds of individual thin boxes. Use **Subtractive Sculpting** (`add_shape` $\to$ `carve_shape`):

| Target Feature | Method | Tool Sequence |
| :--- | :--- | :--- |
| **Arched Doorway / Gate** | Solid Wall + Horizontal Cylinder Carve | `add_shape(box)` $\to$ `carve_shape(cylinder, axis="y")` |
| **Window Cutout** | Solid Wall + Box Carve | `add_shape(box)` $\to$ `carve_shape(box)` |
| **Hollow Pot / Bowl / Mug** | Solid Cylinder + Inner Cylinder Carve | `add_shape(cylinder, r=6)` $\to$ `carve_shape(cylinder, r=4)` |
| **Roof Slope / Eaves Chamfer** | Solid Block + Cylinder/Sphere Carve | `add_shape(box)` $\to$ `carve_shape(cylinder)` along eaves |
| **Hollow Room Interior** | Solid Cube + Inner Box Carve | `add_shape(box, 24)` $\to$ `carve_shape(box, 20)` |

---

## 🛡️ 7. Anti-Amnesia Protocol

1. **Text Spatial Ledger**: Maintain coordinates and bounding boxes in notes.
2. **Render Every Milestone**: The end-of-milestone render refreshes the multimodal image context.
3. **Checkpoints**: Revert cleanly with `restore_checkpoint()` if the user requests changes.