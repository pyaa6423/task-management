# frappe-gantt SVG Structure & Pitfalls

## SVG Element Hierarchy (v0.6.1)

```
svg.gantt
├── g.grid
│   ├── rect.grid-header          ← header background
│   ├── rect.grid-row (× N)      ← one per task
│   ├── line.row-line (× N)      ← horizontal lines between rows
│   └── line.tick (× M)          ← vertical date lines
├── g.date
│   ├── text.upper-text (× ?)    ← month/year labels ("March", "April")
│   └── text.lower-text (× M)   ← day/date labels ("14", "15", "16")
├── rect.today-highlight          ← today column highlight
└── g.bar-wrapper (× N)          ← one per task, positioned via transform="translate(x, y)"
    ├── g.bar-group
    │   ├── rect.bar              ← background bar
    │   └── rect.bar-progress     ← progress fill
    └── text.bar-label            ← task name text
```

## Known Pitfalls

### 1. Never shift grid-rows programmatically

**Problem:** Changing `y` on grid-rows requires cascading changes to:
- All `row-line` y1/y2
- All `tick` y2 (but NOT y1 — they start at header)
- All `bar-wrapper` transform translate y-values
- `today-highlight` y and height
- `grid-header` height

Missing even one causes visible misalignment. This was attempted 3+ times and failed each time due to edge cases (e.g., `tick` y1 values vary, `bar-wrapper` transform parsing).

**Solution:** Don't shift. Append-only, or use CSS transforms.

### 2. `header_height` option doesn't help

Setting `header_height: 80` makes the header taller, but frappe-gantt positions `lower-text` relative to the bottom of the header. So increasing header height just pushes date labels down — it doesn't create space *below* the labels.

**Solution:** Use CSS `transform: translateY(-Npx)` on `.lower-text` to move labels up within existing space.

### 3. Color classes must be injected as `<style>`, not inline

frappe-gantt's `custom_class` on tasks adds a CSS class to the `bar-wrapper`. But the library applies its own `fill` via inline styles on `.bar` and `.bar-progress`. You must use `!important` in injected styles to override.

```javascript
// Inject via <style> element
css += `.bar-item-0 .bar { fill: #e60012 !important; }\n`;
```

### 4. SVG element insertion order matters

Insert overlays **after** the grid group but **before** bar wrappers:
```javascript
gridEl.parentNode.insertBefore(overlayGroup, gridEl.nextSibling);
```

Month separator lines should go **last** (on top of everything):
```javascript
svg.appendChild(monthGroup);
```

### 5. `lower-text` count may differ from column count

frappe-gantt may not render a `lower-text` for every visible column (e.g., it skips some at certain zoom levels). When iterating columns, check `if (i < textEls.length)` before accessing.

### 6. Date calculation from `gantt_start`

`ganttChart.gantt_start` gives the leftmost date. Each column in Day mode = 1 day. The x-offset of the first column is:
```javascript
const offsetX = parseFloat(textEls[0].getAttribute("x")) - colWidth / 2;
```

### 7. Re-rendering on view mode change

When `change_view_mode()` is called, frappe-gantt rebuilds the SVG. Any overlays/modifications are lost. Must re-apply after mode change:
```javascript
setTimeout(() => addOverlays(ganttDiv), 50);
```

Use `svg.dataset.overlayApplied` flag to prevent double-apply within a single render, but clear it on re-render.
