---
name: ui-customization
description: Guide for UI styling, layout adjustments, and visual customization of web applications. Use this skill when working on color schemes, responsive layout, SVG/chart styling, calendar-aware UI, or integrating third-party UI libraries. Trigger on requests like "change the color scheme", "fix the layout", "make it look like X", "add weekend highlighting", "the text is overlapping", or any visual/styling work.
---

# UI Customization Guide

A skill for making visual changes to web UIs — covering CSS techniques, third-party library integration, SVG manipulation, and common pitfalls.

## Principle: Least Invasive Change First

When adjusting visuals, always try approaches in this order:

1. **CSS only** — transforms, margins, padding, colors, fonts
2. **CSS + minimal DOM** — add a class, append an element
3. **DOM modification** — change text content, add child elements
4. **DOM restructuring** — move/shift existing elements ← **last resort**

Each step up in invasiveness multiplies the risk of side effects. Most visual issues can be solved at step 1-2.

---

## Third-Party Library Customization

### The Golden Rule

**Never restructure a library's generated DOM.** Libraries expect their DOM structure to remain intact. Instead:

- **Override styles with CSS** (`!important` when needed — library inline styles often require it)
- **Append elements** on top of or beside the library's output
- **Modify text content** of existing elements (safe if the library doesn't re-read it)
- **Use library options/config** first before resorting to post-render DOM manipulation

### Post-render modification pattern

```javascript
// Wait for library to finish rendering, then modify
const chart = new SomeChart(container, data, options);
setTimeout(() => customizeChart(container), 50);

// Guard against double-apply
function customizeChart(el) {
    const target = el.querySelector(".chart-root");
    if (!target || target.dataset.customized) return;
    target.dataset.customized = "1";
    // ... append overlays, modify labels, etc.
}
```

### When the library re-renders

Many libraries rebuild their DOM on state changes (zoom, resize, data update). Your customizations will be lost. Always re-apply after:

```javascript
chart.on("viewChange", () => {
    setTimeout(() => customizeChart(container), 50);
});
```

---

## SVG Customization

### Safe operations
- Change `fill`, `stroke`, `opacity` on existing elements
- Append new `<rect>`, `<line>`, `<text>`, `<g>` elements
- Add `<tspan>` inside `<text>` for multi-line labels
- Use CSS transforms (`transform: translateY(-8px)`) for positioning

### Dangerous operations
- Changing `y`, `x`, `width`, `height` on structural elements (grid rows, headers)
- Modifying `transform="translate()"` on positioned groups
- Changing `viewBox` or SVG dimensions after library rendering

### Multi-line text in SVG

SVG `<text>` doesn't support `\n`. Use `<tspan>` with `dy`:

```javascript
const ns = "http://www.w3.org/2000/svg";
const text = existingTextElement;
const origText = text.textContent;
const x = text.getAttribute("x");

text.textContent = "";

const line1 = document.createElementNS(ns, "tspan");
line1.setAttribute("x", x);
line1.textContent = origText;
text.appendChild(line1);

const line2 = document.createElementNS(ns, "tspan");
line2.setAttribute("x", x);
line2.setAttribute("dy", "1.2em");  // relative offset from previous line
line2.textContent = "second line";
text.appendChild(line2);
```

If the second line pushes into content below, use CSS `transform: translateY(-Npx)` on the parent `<text>` to shift everything up — **do not** move other elements down.

### Overlay insertion order

SVG renders back-to-front (later elements on top). Insert in this order:
1. Background overlays (weekends, highlights) → right after grid
2. Data elements (bars, nodes) → middle
3. Foreground lines (separators, today marker) → last (`svg.appendChild()`)

---

## CSS Spacing & Overlap Fixes

When elements overlap or spacing is wrong:

### DO
```css
/* Use transform — doesn't affect layout flow */
.header-text { transform: translateY(-8px); }

/* Use padding/margin on the container */
.chart-header { padding-bottom: 16px; }

/* Use gap in flex/grid layouts */
.controls { display: flex; gap: 1rem; }
```

### DON'T
```javascript
// Don't programmatically shift y-coordinates of multiple dependent elements
elements.forEach(el => el.setAttribute("y", parseFloat(el.getAttribute("y")) + 20));
// This WILL break — you'll miss some elements or miscalculate dependencies
```

---

## Color Scheme Design

### Dynamic theming with CSS custom properties

```css
:root {
    --accent: #e60012;
    --accent-hover: #c4000f;
    --bg: #ffffff;
    --bg-secondary: #f7f7f7;
    --text: #484848;
    --border: #e0e0e0;
}

.header { border-bottom: 3px solid var(--accent); }
.button.active { background: var(--accent); }
```

### Dynamic theme injection (when CSS vars aren't enough)

For per-element styling (e.g., each chart bar gets a different color):

```javascript
function injectStyles(colors) {
    let el = document.getElementById("dynamic-theme");
    if (el) el.remove();

    const style = document.createElement("style");
    style.id = "dynamic-theme";
    style.textContent = colors.map((c, i) =>
        `.item-${i} { background: ${c} !important; }`
    ).join("\n");
    document.head.appendChild(style);
}
```

**Key:** Always remove the old `<style>` before adding a new one to prevent accumulation.

### Per-item color picker pattern

```html
<span class="color-dot" style="background: #e60012;">
    <input type="color" value="#e60012"
           style="opacity: 0; position: absolute; cursor: pointer;">
</span>
```

User clicks the visible dot → native color picker opens → on `input` event, update the dot and re-inject styles.

---

## Calendar-Aware UI (Japanese)

### Day-of-week display
- 日(Sun): red `#e60012`
- 土(Sat): blue `#0068b7`
- 平日(Weekday): gray `#999`
- 祝日(Holiday): red — **both the date number AND the day label**

### Holiday data
- Maintain as a `Set` of `"YYYY-MM-DD"` strings for the target year
- 春分の日 and 秋分の日 vary by year — always verify
- Include 振替休日 (substitute holidays: when a holiday falls on Sunday, Monday becomes a holiday)

### Non-workday overlays
- Use a consistent muted color (e.g., `rgba(0, 0, 0, 0.08)`)
- Don't differentiate holidays from weekends visually — both are "non-work days"
- Constrain overlays to the data area, not the full chart (match today-highlight behavior)

---

## Responsive Considerations

### Chart containers
```css
.chart-container {
    overflow-x: auto;    /* horizontal scroll for wide charts */
    min-height: 300px;   /* prevent collapse when empty */
}
```

### Control bars
```css
.controls {
    display: flex;
    flex-wrap: wrap;     /* stack on narrow screens */
    gap: 1rem;
    align-items: center;
}

.view-modes { margin-left: auto; }  /* push to right */
```

---

## Debugging Visual Issues

1. **Open DevTools → Elements** — inspect the exact element that's wrong
2. **Check computed styles** — is a library overriding your CSS? You may need `!important`
3. **Check element dimensions** — does the container clip? (`overflow: hidden` is a common culprit)
4. **Check SVG coordinates** — SVG uses its own coordinate system; CSS `width`/`height` on the `<svg>` tag may differ from internal coordinates
5. **Screenshot and annotate** — when reporting/analyzing issues, always reference the actual visual output

---

## Reference Files

- **`references/css-patterns.md`** — Common CSS patterns for forms, buttons, cards, and layouts
