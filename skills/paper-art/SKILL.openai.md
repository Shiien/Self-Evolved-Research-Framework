---
name: paper-art
description: Create pixel art / flat SVG visual identity for the research project — project mascots, concept illustrations, README hero images, slide decorations that stay visually consistent across paper, README, and presentation materials. Save to outputs/visuals/{name}.svg as a tracked deliverable. Triggers on "pixel art", "画像素图", "SVG illustration", "project mascot", "README hero image", "decorative visual for {slide|README|docs}". For rigorous academic figures (architecture / pipeline / flow) use `paper-illustrate`; for data-driven plots (line / bar / scatter / heatmap) use `paper-figure`.
---

# paper-art

**Trigger**: User asks for a decorative or identity-level visual — pixel art, flat SVG, isometric illustration, README hero image, project mascot, slide decoration. For rigorous academic figures (architecture, pipeline, TikZ), route to `paper-illustrate`; for data-driven plots (matplotlib / seaborn / PGFPlots), route to `paper-figure`.

**Process**:

### 1. Gather project context

- Read `config.yaml` — extract `project.name`, `research.domain`, `research.keywords` to inform subject/theme.
- If a brand color exists (e.g. in `config.yaml` or prior SVGs under `outputs/visuals/`), reuse it for palette consistency.
- Ask the user only for missing details (subject, style, size).

### 2. Design

- **Style**: pixel art (default), flat SVG, or isometric. Pixel art = low-res retro; flat SVG = scalable clean shapes; isometric = 3D-look at 30°.
- **Palette** — 3–5 colors. Keep one anchored to the project brand so all visuals in `outputs/visuals/` read as a family:
  - Skin: `#FFDAB9` (light), `#E8967A` / `#D4956A` (shadow)
  - Eyes: `#333`
  - Hair: `#8B5E3C`, `#2C2C2C`, `#FFD700`, `#C0392B`
  - Clothes: **project brand color** (pull from config or previous visuals)
  - Shoes/pants: `#444`
  - Accessories: `#555`, `#FFD700`
- **Size**:
  - Badge / icon: tight `viewBox`, character 8–10 px wide
  - README hero: wide landscape (`viewBox="0 0 800 200"` typical)
  - Slide decoration: match slide aspect

### 3. Generate SVG

**Pixel grid**:
- Each "pixel" = `<rect>` with `width="7" height="7"` (7px grid, no gaps).
- Characters: 8–10 px wide × 8–12 px tall.
- Reuse characters via `<g transform="translate(x,y)">`.

**Character template** (7px grid):
```
Row 0 (hair top):   4 pixels centered
Row 1 (hair):       6 pixels wide
Row 2 (face top):   6 skin
Row 3 (eyes):       skin, eye, skin, skin, eye, skin
Row 4 (mouth):      skin, skin, mouth, mouth, skin, skin
Row 5 (body top):   hand, 6 shirt, hand        (8 wide)
Row 6 (body):       6 shirt
Row 7 (legs):       2 + gap + 2                (5 wide with gap)
```

**SVG skeleton**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H" font-family="monospace">
  <defs>
    <!-- arrow markers, gradients if needed -->
  </defs>
  <rect width="W" height="H" fill="#fafbfc" rx="12"/>      <!-- background -->
  <!-- characters via <g transform="translate(...)"> -->
  <!-- labels via <text text-anchor="middle"> -->
</svg>
```

**Chat-bubble / arrow recipes** (when scene involves dialogue or directional flow): see `~/.agents/skills/pixel-art/SKILL.md` if already installed globally — copy proven patterns from there. Otherwise:

```xml
<!-- Bubble (speaks-left) -->
<rect x="110" y="29" width="280" height="26" fill="#e8f4fd"
      stroke="#4a9eda" stroke-width="1.5" rx="8"/>
<polygon points="108,41 99,47 108,46" fill="#e8f4fd"
         stroke="#4a9eda" stroke-width="1.5"/>
<rect x="107" y="40" width="3" height="7" fill="#e8f4fd"/>   <!-- stroke cover -->
<text x="123" y="46" font-size="13px">📄 Message</text>

<!-- Arrow -->
<defs>
  <marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#4a9eda"/>
  </marker>
</defs>
<line x1="392" y1="42" x2="465" y2="42" stroke="#4a9eda" stroke-width="2" marker-end="url(#ar)"/>
```

### 4. Save + iterate

- Write to `outputs/visuals/{name}.svg` (**not** inline — this is a tracked deliverable).
- If `~/.agents/skills/pixel-art/` (global) is also triggered, defer to this project-level skill so the output lands in `outputs/visuals/`.
- Show a 1-line summary: dimensions, colors used, file path.
- Iterate with user on screenshot feedback. Typical 2–4 iterations.

### 5. Tighten + checklist

- Trim `viewBox` to actual content (≥10px padding).
- Remove unused `<defs>`.
- If visual is part of a tracked deliverable, suggest `checklist-update` to mark completion.

**Inputs**: user concept + optional `config.yaml` (brand color, domain), optional prior visuals in `outputs/visuals/` for palette matching
**Outputs**: `outputs/visuals/{name}.svg` (self-contained, no external deps)
**Token**: ~2-6K (1-2K generation + 1-4K iteration)
**Composition**:
- For academic paper figures (architecture, pipeline, flow) → `paper-illustrate`
- For data-driven plots (line / bar / scatter / heatmap / table) → `paper-figure`
- When visual is a listed checklist deliverable → `checklist-update`
- When visual anchors a README/slide section → `writing-draft` for accompanying text

## Common pitfalls

- **Arrow direction**: `orient="auto"` follows line direction — swap `x1`/`x2` to flip.
- **Bubble overlap**: ≥38px vertical spacing between rows of dialogue.
- **Text overflow**: monospace 13px ≈ 7.8px/char, emoji ≈ 14px. Measure before setting bubble width.
- **Character / bubble clash**: keep character x-zone ≥10px away from bubble x-zone.
- **Loose viewBox**: match to content bounds, ~10px padding. No wasted space.
- **Stroke artifact at bubble tail**: always cover the join with a thin `<rect>` matching the fill.
- **Palette drift**: if the project already has visuals in `outputs/visuals/`, reuse their primary color — don't re-roll the palette per image.
