---
name: frontend-gantt
description: Build and customize Gantt chart UIs with frappe-gantt. Use this skill when working on Gantt chart visualization, SVG chart customization, calendar-aware UI (weekends/holidays), or color theme systems for charts. Trigger on requests like "customize the Gantt chart", "add weekend highlighting", "change chart colors", "add a day-of-week row", or any frappe-gantt related work.
---

# Gantt Chart UI Implementation

A skill for building and customizing Gantt chart interfaces with frappe-gantt, covering SVG manipulation pitfalls, calendar features, and theming.

## Critical: SVG DOM Manipulation Rules

frappe-gantt renders the chart as an SVG. When customizing it, follow these rules strictly:

### DO: Append-only modifications
- **Add new elements** (overlays, labels, lines) on top of existing SVG
- **Modify text content** of existing elements (e.g., append day-of-week to date labels)
- **Use CSS** for visual adjustments (transforms, colors, fonts)

### DO NOT: Shift existing elements
- **Never change `y` coordinates** of grid rows, bars, ticks, or row-lines
- **Never modify `transform` attributes** on bar-wrappers
- **Never resize `grid-header`** height via JavaScript

**Why:** frappe-gantt's internal layout is tightly coupled. Shifting one element (e.g., grid rows down by 20px) requires shifting ALL related elements — grid rows, row-lines, ticks, bars, today-highlight, grid-header — and invariably something gets missed or misaligned. This approach was attempted multiple times and consistently failed.

### The correct pattern for adding content below date labels

Instead of making space by pushing elements down, use `<tspan>` to add a second line within the existing `<text>` element, and use CSS `transform: translateY()` to shift the text up within the existing header space:

```javascript
// Add day-of-week below date number via tspan
const el = lowerTextElement;
const origText = el.textContent.trim();
const elX = el.getAttribute("x");
el.textContent = "";

const dateLine = document.createElementNS(ns, "tspan");
dateLine.setAttribute("x", elX);
dateLine.textContent = origText;
el.appendChild(dateLine);

const dowLine = document.createElementNS(ns, "tspan");
dowLine.setAttribute("x", elX);
dowLine.setAttribute("dy", "1.2em");
dowLine.textContent = "月";  // day of week
el.appendChild(dowLine);
```

```css
/* Shift date text up to make room for the second line */
.gantt .lower-text {
    transform: translateY(-8px);
}
```

---

## Weekend / Holiday Overlays

Add colored rectangles **constrained to grid row area only** (not extending into header or below last row):

```javascript
const gridTop = parseFloat(gridRows[0].getAttribute("y"));
const lastRow = gridRows[gridRows.length - 1];
const gridBottom = parseFloat(lastRow.getAttribute("y")) + parseFloat(lastRow.getAttribute("height"));

// Overlay rect
rect.setAttribute("y", gridTop);
rect.setAttribute("height", gridBottom - gridTop);
```

**Key:** Use `gridTop` to `gridBottom`, NOT `0` to `svgHeight`. The overlay should match the today-highlight behavior.

### Japanese Holidays

Maintain a static Set of holiday dates for the target year. Include substitute holidays (振替休日). Common miss: 春分の日 (around March 20) and 秋分の日 (around September 23) vary by year — verify against the official calendar.

---

## Color Theme System

### Architecture
- Define themes as objects with `bar[]` and `progress[]` color arrays
- Assign colors per-task by index (`bar-item-${index}`)
- Inject `<style>` element dynamically — remove and recreate on theme change
- Support per-item color overrides via `colorOverrides` map + `<input type="color">`

### Per-item color picker pattern
- Render a color legend above the chart with a colored dot per task
- Hide `<input type="color">` behind the dot (opacity: 0, positioned absolutely)
- On input change, update `colorOverrides[itemId]` and re-inject styles

### Theme switching
- Clear `colorOverrides` when theme changes (user expectation: fresh palette)
- Clear `colorOverrides` when navigating between project/subtask views

---

## frappe-gantt Options Reference (v0.6.1)

Useful options for `new Gantt(element, tasks, options)`:

| Option | Default | Notes |
|--------|---------|-------|
| `view_mode` | "Day" | "Day", "Week", "Month" |
| `padding` | 18 | Vertical padding between bars |
| `header_height` | 50 | **Caution**: increases header but also moves date text down — doesn't create useful space |
| `bar_height` | 20 | Height of each bar |
| `bar_corner_radius` | 3 | Rounded corners |

**Important:** `header_height` does NOT create space between date labels and bars. It increases the total header area but frappe-gantt positions text relative to the bottom of the header, so text moves down with it. Use CSS `transform` instead.

---

## Reference Files

- **`references/frappe-gantt-pitfalls.md`** — Detailed SVG structure and known issues
