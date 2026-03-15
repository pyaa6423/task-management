# CSS Patterns Reference

## Button Groups (segmented control)

```css
.button-group {
    display: flex;
    gap: 0;
}

.button-group button {
    padding: 0.5rem 1rem;
    border: 2px solid #d9d9d9;
    background: #fff;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
}

.button-group button:first-child { border-radius: 6px 0 0 6px; }
.button-group button:last-child { border-radius: 0 6px 6px 0; }
.button-group button:not(:first-child) { border-left: none; }

.button-group button.active {
    background: var(--accent, #e60012);
    color: #fff;
    border-color: var(--accent, #e60012);
}
```

## Pill/Tag Components

```css
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.625rem;
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
}
```

## Color Swatch Selector

```css
.swatch {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 2px solid transparent;
    cursor: pointer;
    transition: all 0.2s;
}

.swatch:hover { transform: scale(1.2); }

.swatch.active {
    border-color: #484848;
    box-shadow: 0 0 0 2px #fff, 0 0 0 4px #484848;
}
```

## Card Container

```css
.card {
    background: #fff;
    border-radius: 10px;
    padding: 1.25rem;
    border: 1px solid #e8e8e8;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
```

## Header with Accent Border

```css
header {
    background: #fff;
    padding: 0.875rem 2rem;
    border-bottom: 3px solid var(--accent, #e60012);
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
```

## Form Select

```css
select {
    padding: 0.5rem 0.75rem;
    font-size: 0.95rem;
    border: 2px solid #d9d9d9;
    border-radius: 6px;
    background: #fff;
    outline: none;
    transition: border-color 0.2s;
}

select:focus {
    border-color: var(--accent, #e60012);
}
```

## Outline Button (accent)

```css
.btn-outline {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.4rem 0.875rem;
    background: #fff;
    color: var(--accent, #e60012);
    border: 2px solid var(--accent, #e60012);
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-outline:hover {
    background: var(--accent, #e60012);
    color: #fff;
}
```

## Hidden Color Input Pattern

Overlay a native `<input type="color">` on a custom element:

```css
.color-picker-wrapper {
    position: relative;
    display: inline-block;
}

.color-picker-wrapper input[type="color"] {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
    border: none;
    padding: 0;
    width: 100%;
    height: 100%;
}
```

## Scrollbar Styling (WebKit)

```css
.scrollable::-webkit-scrollbar {
    height: 8px;
}

.scrollable::-webkit-scrollbar-track {
    background: #f7f7f7;
    border-radius: 4px;
}

.scrollable::-webkit-scrollbar-thumb {
    background: #d9d9d9;
    border-radius: 4px;
}

.scrollable::-webkit-scrollbar-thumb:hover {
    background: var(--accent, #e60012);
}
```

## Utility: Responsive Flex Controls

```css
.toolbar {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.toolbar > :last-child {
    margin-left: auto;  /* push last item to the right */
}
```
