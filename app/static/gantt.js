document.addEventListener("DOMContentLoaded", () => {
    const projectSelect = document.getElementById("project-select");
    const container = document.getElementById("gantt-container");
    const viewButtons = document.querySelectorAll(".view-modes button");
    const themeSwatches = document.querySelectorAll(".theme-swatch");

    let ganttChart = null;
    let currentMode = "Day";
    let currentProjectId = null;
    let lastLoadedTasks = null;
    let lastLoadedSubtasks = null;
    let lastSubtaskContext = null;
    let colorOverrides = {};

    // ── Color themes ──
    const themes = {
        nintendo: {
            bar:      ["#e60012", "#0ab44a", "#0068b7", "#f5a623", "#9b59b6", "#00a29a", "#e8457c", "#7c8b99"],
            progress: ["#c4000f", "#078a39", "#004d8a", "#d4891c", "#7d3f9b", "#007d75", "#c23365", "#5f6d78"],
        },
        mario: {
            bar:      ["#e60012", "#049cd8", "#43b047", "#fbd000", "#f8914e", "#7b5ea7", "#e85387", "#6dbfb8"],
            progress: ["#c4000f", "#037bb0", "#2f8a33", "#d4b100", "#d67a3c", "#5f4689", "#c43d6c", "#519e97"],
        },
        splatoon: {
            bar:      ["#e84b0a", "#2ae0c8", "#d645d1", "#bfd31e", "#4b26e2", "#f7b500", "#26d1e8", "#e8266f"],
            progress: ["#c43e08", "#1fb8a4", "#b033ad", "#9fb518", "#3b1db8", "#d49900", "#1daec4", "#c41d5b"],
        },
        zelda: {
            bar:      ["#2d8a4e", "#c9a227", "#3a7dc9", "#8b5e3c", "#6db06b", "#c45a3a", "#7394b5", "#a68b5b"],
            progress: ["#1f6b38", "#a6841d", "#2c62a3", "#6d4530", "#4e8d4f", "#a3432b", "#576f8c", "#887045"],
        },
        kirby: {
            bar:      ["#f4a4b8", "#ffd662", "#88ccee", "#b8e27c", "#d4a0e8", "#f7c9a8", "#a8dce0", "#e8b4c8"],
            progress: ["#e07a95", "#e0b840", "#6aaed0", "#96c454", "#b87ad0", "#e0a880", "#80bcc0", "#d090a8"],
        },
        monochrome: {
            bar:      ["#484848", "#6b6b6b", "#8e8e8e", "#a8a8a8", "#5a5a5a", "#787878", "#9a9a9a", "#b0b0b0"],
            progress: ["#333333", "#525252", "#707070", "#888888", "#444444", "#606060", "#808080", "#959595"],
        },
    };

    let currentTheme = "nintendo";

    // ── Japanese holidays 2026 (month-day) ──
    const holidays2026 = new Set([
        "2026-01-01", "2026-01-12", "2026-02-11", "2026-02-23",
        "2026-03-20", "2026-04-29", "2026-05-03", "2026-05-04",
        "2026-05-05", "2026-05-06", "2026-07-20", "2026-08-11",
        "2026-09-21", "2026-09-22", "2026-09-23", "2026-10-12",
        "2026-11-03", "2026-11-23", "2026-12-23",
    ]);

    function isHoliday(d) {
        const s = formatDate(d);
        return holidays2026.has(s);
    }

    function isWeekend(d) {
        const day = d.getDay();
        return day === 0 || day === 6;
    }

    function isNonWorkday(d) {
        return isWeekend(d) || isHoliday(d);
    }

    function formatDate(d) {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        return `${y}-${m}-${dd}`;
    }

    const DAY_LABELS = ["日", "月", "火", "水", "木", "金", "土"];

    // ── Post-render: add overlays (no DOM shifting — append only) ──
    function addOverlays(ganttEl) {
        if (currentMode !== "Day") return;

        const svg = ganttEl.querySelector("svg.gantt");
        if (!svg) return;

        if (svg.dataset.overlayApplied) return;
        svg.dataset.overlayApplied = "1";

        const gridRows = svg.querySelectorAll(".grid .grid-row");
        if (gridRows.length === 0) return;

        const lowerTexts = svg.querySelectorAll(".lower-text");
        if (lowerTexts.length === 0) return;

        // Gather lower-text positions
        const textEls = Array.from(lowerTexts);
        if (textEls.length < 2) return;

        const colWidth = parseFloat(textEls[1].getAttribute("x")) - parseFloat(textEls[0].getAttribute("x"));
        const ganttStart = ganttChart ? ganttChart.gantt_start : null;
        if (!ganttStart) return;
        const startDate = new Date(ganttStart);
        const offsetX = parseFloat(textEls[0].getAttribute("x")) - colWidth / 2;

        // Grid area (task rows)
        const gridTop = parseFloat(gridRows[0].getAttribute("y"));
        const lastRow = gridRows[gridRows.length - 1];
        const gridBottom = parseFloat(lastRow.getAttribute("y")) + parseFloat(lastRow.getAttribute("height"));

        const ns = "http://www.w3.org/2000/svg";
        const overlayGroup = document.createElementNS(ns, "g");
        const monthGroup = document.createElementNS(ns, "g");

        const svgWidth = parseFloat(svg.getAttribute("width")) || 2000;
        const svgHeight = parseFloat(svg.getAttribute("height")) || gridBottom + 50;
        const numCols = Math.ceil((svgWidth - offsetX) / colWidth) + 2;

        let prevMonth = -1;

        // ── 1. Append day-of-week to each lower-text (e.g. "15" → "15(月)") ──
        for (let i = 0; i < numCols; i++) {
            const d = new Date(startDate);
            d.setDate(d.getDate() + i);

            const x = offsetX + i * colWidth;
            const dow = d.getDay();

            // Update existing lower-text: keep date on first line, add day-of-week below via <tspan>
            if (i < textEls.length) {
                const el = textEls[i];
                const origText = el.textContent.trim();
                const elX = el.getAttribute("x");

                // Clear text content, rebuild with tspans
                el.textContent = "";

                // Determine color for this date
                let dateColor = null;
                let dowColor = "#999";
                if (dow === 0 || isHoliday(d)) {
                    dateColor = "#e60012";
                    dowColor = "#e60012";
                } else if (dow === 6) {
                    dateColor = "#0068b7";
                    dowColor = "#0068b7";
                }

                const dateLine = document.createElementNS(ns, "tspan");
                dateLine.setAttribute("x", elX);
                dateLine.textContent = origText;
                if (dateColor) dateLine.setAttribute("fill", dateColor);
                el.appendChild(dateLine);

                const dowLine = document.createElementNS(ns, "tspan");
                dowLine.setAttribute("x", elX);
                dowLine.setAttribute("dy", "1.2em");
                dowLine.setAttribute("class", "dow-label");
                dowLine.setAttribute("fill", dowColor);
                dowLine.textContent = DAY_LABELS[dow];
                el.appendChild(dowLine);
            }

            // ── 2. Non-workday overlay — grid rows only ──
            if (isNonWorkday(d)) {
                const rect = document.createElementNS(ns, "rect");
                rect.setAttribute("x", x);
                rect.setAttribute("y", gridTop);
                rect.setAttribute("width", colWidth);
                rect.setAttribute("height", gridBottom - gridTop);
                rect.setAttribute("fill", "rgba(0, 0, 0, 0.08)");
                rect.setAttribute("class", "nonworkday-overlay");
                overlayGroup.appendChild(rect);
            }

            // ── 3. Month separator ──
            const currentMonth = d.getMonth();
            if (prevMonth !== -1 && currentMonth !== prevMonth && d.getDate() === 1) {
                const line = document.createElementNS(ns, "line");
                line.setAttribute("x1", x);
                line.setAttribute("y1", 0);
                line.setAttribute("x2", x);
                line.setAttribute("y2", svgHeight);
                line.setAttribute("stroke", "#e60012");
                line.setAttribute("stroke-width", "2");
                line.setAttribute("stroke-opacity", "0.5");
                line.setAttribute("class", "month-separator");
                monthGroup.appendChild(line);
            }
            prevMonth = currentMonth;
        }

        // Insert overlays behind bars, month lines on top
        const gridEl = svg.querySelector(".grid");
        if (gridEl) {
            gridEl.parentNode.insertBefore(overlayGroup, gridEl.nextSibling);
            svg.appendChild(monthGroup);
        }
    }

    // ── View mode buttons ──
    viewButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            viewButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentMode = btn.dataset.mode;
            if (ganttChart) {
                ganttChart.change_view_mode(currentMode);
                // Re-apply overlays after mode change
                setTimeout(() => {
                    const ganttDiv = container.querySelector(".gantt-target") || container.querySelector("div:last-child");
                    if (ganttDiv) addOverlays(ganttDiv);
                }, 100);
            }
        });
    });

    // ── Theme swatches ──
    themeSwatches.forEach((swatch) => {
        swatch.addEventListener("click", () => {
            themeSwatches.forEach((s) => s.classList.remove("active"));
            swatch.classList.add("active");
            currentTheme = swatch.dataset.theme;
            colorOverrides = {};
            rerender();
        });
    });

    // ── Project selector ──
    projectSelect.addEventListener("change", async () => {
        const projectId = projectSelect.value;
        if (!projectId) {
            container.innerHTML = '<p class="placeholder">プロジェクトを選択してください</p>';
            ganttChart = null;
            currentProjectId = null;
            lastLoadedTasks = null;
            colorOverrides = {};
            return;
        }
        currentProjectId = projectId;
        lastLoadedSubtasks = null;
        lastSubtaskContext = null;
        colorOverrides = {};
        await loadGantt(projectId);
    });

    // ── Re-render current view ──
    function rerender() {
        if (lastLoadedSubtasks && lastSubtaskContext) {
            renderSubtasks(lastLoadedSubtasks, lastSubtaskContext.taskName);
        } else if (lastLoadedTasks && currentProjectId) {
            renderTasks(lastLoadedTasks);
        }
    }

    // ── Get color for an item ──
    function getItemColor(itemId, index) {
        const theme = themes[currentTheme];
        if (colorOverrides[itemId]) {
            return { bar: colorOverrides[itemId], progress: darken(colorOverrides[itemId], 0.2) };
        }
        const i = index % theme.bar.length;
        return { bar: theme.bar[i], progress: theme.progress[i] };
    }

    function darken(hex, amount) {
        const num = parseInt(hex.replace("#", ""), 16);
        const r = Math.max(0, Math.floor((num >> 16) * (1 - amount)));
        const g = Math.max(0, Math.floor(((num >> 8) & 0xff) * (1 - amount)));
        const b = Math.max(0, Math.floor((num & 0xff) * (1 - amount)));
        return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, "0")}`;
    }

    // ── Build color legend UI ──
    function buildLegend(items, parentEl) {
        const legend = document.createElement("div");
        legend.className = "color-legend";

        items.forEach((item, index) => {
            if (item.is_completed) return;

            const colors = getItemColor(item.id, index);
            const pill = document.createElement("span");
            pill.className = "color-legend-item";

            const dot = document.createElement("span");
            dot.className = "color-dot";
            dot.style.background = colors.bar;

            const colorInput = document.createElement("input");
            colorInput.type = "color";
            colorInput.value = colors.bar;
            colorInput.title = `${item.name} の色を変更`;
            colorInput.addEventListener("input", (e) => {
                const newColor = e.target.value;
                colorOverrides[item.id] = newColor;
                dot.style.background = newColor;
                applyColorStyles(items);
            });

            const label = document.createElement("span");
            label.textContent = item.name;

            dot.appendChild(colorInput);
            pill.appendChild(dot);
            pill.appendChild(label);
            legend.appendChild(pill);
        });

        parentEl.appendChild(legend);
    }

    // ── Apply per-item color styles ──
    function applyColorStyles(items) {
        let existing = document.getElementById("gantt-theme-styles");
        if (existing) existing.remove();

        const style = document.createElement("style");
        style.id = "gantt-theme-styles";

        let css = "";
        items.forEach((item, index) => {
            const colors = getItemColor(item.id, index);
            css += `.bar-item-${index} .bar { fill: ${colors.bar} !important; }\n`;
            css += `.bar-item-${index} .bar-progress { fill: ${colors.progress} !important; }\n`;
        });
        style.textContent = css;
        document.head.appendChild(style);
    }

    // ── Load & render project tasks ──
    async function loadGantt(projectId) {
        const res = await fetch(`/api/v1/gantt/projects/${projectId}`);
        const tasks = await res.json();
        lastLoadedTasks = tasks;
        lastLoadedSubtasks = null;
        lastSubtaskContext = null;
        renderTasks(tasks);
    }

    function renderTasks(tasks) {
        if (tasks.length === 0) {
            container.innerHTML = '<p class="placeholder">タスクがありません</p>';
            ganttChart = null;
            return;
        }

        const ganttTasks = tasks
            .filter((t) => t.start && t.end)
            .map((t, i) => ({
                id: t.id,
                name: t.name,
                start: t.start.split("T")[0],
                end: t.end.split("T")[0],
                progress: t.progress,
                custom_class: t.is_completed ? "bar-completed" : `bar-item-${i}`,
            }));

        if (ganttTasks.length === 0) {
            container.innerHTML = '<p class="placeholder">日付が設定されていないタスクです</p>';
            ganttChart = null;
            return;
        }

        applyColorStyles(tasks);
        container.innerHTML = "";
        buildLegend(tasks, container);

        const ganttDiv = document.createElement("div");
        ganttDiv.className = "gantt-target";
        container.appendChild(ganttDiv);

        ganttChart = new Gantt(ganttDiv, ganttTasks, {
            view_mode: currentMode,
            padding: 18,
            on_click: async (task) => {
                const taskId = task.id.replace("task-", "");
                await loadSubtasks(taskId, task.name);
            },
            on_date_change: () => {},
            on_progress_change: () => {},
        });

        setTimeout(() => addOverlays(ganttDiv), 50);
    }

    // ── Load & render subtasks ──
    async function loadSubtasks(taskId, taskName) {
        const res = await fetch(`/api/v1/gantt/tasks/${taskId}/subtasks`);
        const subtasks = await res.json();

        if (subtasks.length === 0) return;

        lastLoadedSubtasks = subtasks;
        lastSubtaskContext = { taskId, taskName };
        colorOverrides = {};
        renderSubtasks(subtasks, taskName);
    }

    function renderSubtasks(subtasks, taskName) {
        const ganttTasks = subtasks
            .filter((s) => s.start && s.end)
            .map((s, i) => ({
                id: s.id,
                name: s.name,
                start: s.start.split("T")[0],
                end: s.end.split("T")[0],
                progress: s.progress,
                custom_class: s.is_completed ? "bar-completed" : `bar-item-${i}`,
            }));

        if (ganttTasks.length === 0) return;

        applyColorStyles(subtasks);
        container.innerHTML = "";

        const backBtn = document.createElement("button");
        backBtn.className = "back-button";
        backBtn.textContent = "\u2190 タスク一覧に戻る";
        backBtn.addEventListener("click", () => {
            lastLoadedSubtasks = null;
            lastSubtaskContext = null;
            colorOverrides = {};
            if (currentProjectId) loadGantt(currentProjectId);
        });
        container.appendChild(backBtn);

        buildLegend(subtasks, container);

        const ganttDiv = document.createElement("div");
        ganttDiv.className = "gantt-target";
        container.appendChild(ganttDiv);

        ganttChart = new Gantt(ganttDiv, ganttTasks, {
            view_mode: currentMode,
            padding: 18,
        });

        setTimeout(() => addOverlays(ganttDiv), 50);
    }
});
