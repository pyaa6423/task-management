document.addEventListener("DOMContentLoaded", () => {
    const projectSelect = document.getElementById("project-select");
    const container = document.getElementById("gantt-container");
    const viewButtons = document.querySelectorAll(".view-modes button");
    const themeSwatches = document.querySelectorAll(".theme-swatch");

    let ganttChart = null;
    let currentMode = "Day";
    let currentProjectId = null;
    let colorOverrides = {};
    let currentTasks = [];     // current level's task data
    let expandedTaskId = null; // currently expanded task id (e.g. "task-3")

    // Navigation stack for drill-down
    let navStack = []; // [{ type:"project", projectId } | { type:"task", taskId }]

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

    // ── Japanese holidays 2026 ──
    const holidays2026 = new Set([
        "2026-01-01", "2026-01-12", "2026-02-11", "2026-02-23",
        "2026-03-20", "2026-04-29", "2026-05-03", "2026-05-04",
        "2026-05-05", "2026-05-06", "2026-07-20", "2026-08-11",
        "2026-09-21", "2026-09-22", "2026-09-23", "2026-10-12",
        "2026-11-03", "2026-11-23", "2026-12-23",
    ]);

    function isHoliday(d) { return holidays2026.has(fmtDate(d)); }
    function isWeekend(d) { const day = d.getDay(); return day === 0 || day === 6; }
    function isNonWorkday(d) { return isWeekend(d) || isHoliday(d); }
    function fmtDate(d) {
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
    }
    function fmtShortDate(iso) {
        if (!iso) return "—";
        const d = new Date(iso);
        return `${d.getMonth()+1}/${d.getDate()}`;
    }
    const DAY_LABELS = ["日", "月", "火", "水", "木", "金", "土"];

    // ── Overlays (all modes: day-of-week + weekends + month lines) ──
    function addOverlays(ganttEl) {
        const svg = ganttEl.querySelector("svg.gantt");
        if (!svg || svg.dataset.overlayApplied) return;
        svg.dataset.overlayApplied = "1";

        const gridRows = svg.querySelectorAll(".grid .grid-row");
        const lowerTexts = svg.querySelectorAll(".lower-text");
        if (gridRows.length === 0 || lowerTexts.length === 0) return;

        const textEls = Array.from(lowerTexts);
        if (textEls.length < 2) return;

        const colWidth = parseFloat(textEls[1].getAttribute("x")) - parseFloat(textEls[0].getAttribute("x"));
        const ganttStart = ganttChart ? ganttChart.gantt_start : null;
        if (!ganttStart) return;

        const gridTop = parseFloat(gridRows[0].getAttribute("y"));
        const lastRow = gridRows[gridRows.length - 1];
        const gridBottom = parseFloat(lastRow.getAttribute("y")) + parseFloat(lastRow.getAttribute("height"));

        const ns = "http://www.w3.org/2000/svg";
        const overlayGroup = document.createElementNS(ns, "g");
        const monthGroup = document.createElementNS(ns, "g");

        if (currentMode === "Day") {
            // Day mode: day-of-week labels + weekend/holiday overlays + month separators
            const startDate = new Date(ganttStart);
            const offsetX = parseFloat(textEls[0].getAttribute("x")) - colWidth / 2;
            const svgWidth = parseFloat(svg.getAttribute("width")) || 2000;
            const numCols = Math.ceil((svgWidth - offsetX) / colWidth) + 2;

            let prevMonth = -1;
            for (let i = 0; i < numCols; i++) {
                const d = new Date(startDate);
                d.setDate(d.getDate() + i);
                const x = offsetX + i * colWidth;
                const dow = d.getDay();

                // Day-of-week label under date
                if (i < textEls.length) {
                    const el = textEls[i];
                    const origText = el.textContent.trim();
                    const elX = el.getAttribute("x");
                    el.textContent = "";
                    let dateColor = null, dowColor = "#999";
                    if (dow === 0 || isHoliday(d)) { dateColor = "#e60012"; dowColor = "#e60012"; }
                    else if (dow === 6) { dateColor = "#0068b7"; dowColor = "#0068b7"; }
                    const dl = document.createElementNS(ns, "tspan");
                    dl.setAttribute("x", elX); dl.textContent = origText;
                    if (dateColor) dl.setAttribute("fill", dateColor);
                    el.appendChild(dl);
                    const dw = document.createElementNS(ns, "tspan");
                    dw.setAttribute("x", elX); dw.setAttribute("dy", "1.2em");
                    dw.setAttribute("class", "dow-label"); dw.setAttribute("fill", dowColor);
                    dw.textContent = DAY_LABELS[dow];
                    el.appendChild(dw);
                }

                // Weekend/holiday overlay
                if (isNonWorkday(d)) {
                    const rect = document.createElementNS(ns, "rect");
                    rect.setAttribute("x", x); rect.setAttribute("y", gridTop);
                    rect.setAttribute("width", colWidth); rect.setAttribute("height", gridBottom - gridTop);
                    rect.setAttribute("fill", "rgba(0,0,0,0.08)"); rect.setAttribute("class", "nonworkday-overlay");
                    overlayGroup.appendChild(rect);
                }

                // Month separator
                const cm = d.getMonth();
                if (prevMonth !== -1 && cm !== prevMonth && d.getDate() === 1) {
                    const line = document.createElementNS(ns, "line");
                    line.setAttribute("x1", x); line.setAttribute("y1", 0);
                    line.setAttribute("x2", x); line.setAttribute("y2", gridBottom);
                    line.setAttribute("stroke", "#666"); line.setAttribute("stroke-width", "2");
                    line.setAttribute("class", "month-separator");
                    monthGroup.appendChild(line);
                }
                prevMonth = cm;
            }
        }

        const gridEl = svg.querySelector(".grid");
        if (gridEl) {
            gridEl.parentNode.insertBefore(overlayGroup, gridEl.nextSibling);
            svg.appendChild(monthGroup);
        }
    }

    // ── UI event handlers ──
    viewButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            viewButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentMode = btn.dataset.mode;
            if (ganttChart) {
                ganttChart.change_view_mode(currentMode);
                setTimeout(() => {
                    const gd = container.querySelector(".gantt-target");
                    if (gd) {
                        // Clear overlay flag since SVG was rebuilt
                        const svg = gd.querySelector("svg.gantt");
                        if (svg) delete svg.dataset.overlayApplied;
                        addOverlays(gd);
                    }
                }, 100);
            }
        });
    });

    themeSwatches.forEach((swatch) => {
        swatch.addEventListener("click", () => {
            themeSwatches.forEach((s) => s.classList.remove("active"));
            swatch.classList.add("active");
            currentTheme = swatch.dataset.theme;
            colorOverrides = {};
            renderCurrentView();
        });
    });

    let skipPushState = false; // flag to prevent pushState on popstate

    projectSelect.addEventListener("change", async () => {
        const pid = projectSelect.value;
        if (!pid) {
            currentProjectId = null; navStack = []; colorOverrides = {};
            ganttChart = null;

            if (!skipPushState) history.pushState({ view: "overview" }, "", "#overview");
            await loadOverview();
            return;
        }
        currentProjectId = pid;
        navStack = [];
        colorOverrides = {};
        expandedTaskId = null;
        if (!skipPushState) history.pushState({ view: "project", projectId: pid }, "", `#project-${pid}`);
        await loadProjectTasks(pid);
    });

    // Browser back/forward
    window.addEventListener("popstate", async (e) => {
        skipPushState = true;
        const state = e.state;
        if (!state || state.view === "overview") {
            projectSelect.value = "";
            currentProjectId = null; navStack = []; colorOverrides = {};
            ganttChart = null;
            await loadOverview();
        } else if (state.view === "project") {
            projectSelect.value = state.projectId;
            currentProjectId = state.projectId;
            navStack = []; colorOverrides = []; expandedTaskId = null;
            await loadProjectTasks(state.projectId);
        } else if (state.view === "drilldown") {
            projectSelect.value = state.projectId;
            currentProjectId = state.projectId;
            navStack = [{ type: "project", projectId: state.projectId }];
            colorOverrides = {};
            expandedTaskId = null;
            await drillDown(state.taskId);
        }
        skipPushState = false;
    });

    // ── Load overview (all projects in one gantt) ──
    async function loadOverview() {
        const res = await fetch("/api/v1/gantt/overview");
        const projects = await res.json();

        container.innerHTML = "";

        if (projects.length === 0) {
            container.innerHTML = '<p class="placeholder">プロジェクトがありません</p>';
            return;
        }

        // Build project navigation cards
        const navCards = document.createElement("div");
        navCards.className = "overview-nav";
        projects.forEach((project) => {
            const card = document.createElement("div");
            card.className = "overview-nav-card";
            card.addEventListener("click", () => {
                projectSelect.value = String(project.id);
                projectSelect.dispatchEvent(new Event("change"));
            });
            const name = document.createElement("span");
            name.className = "overview-nav-name";
            name.textContent = project.name;
            const meta = document.createElement("span");
            meta.className = "overview-nav-meta";
            const taskCount = project.tasks.length;
            const completedCount = project.tasks.filter(t => t.is_completed).length;
            meta.textContent = `${completedCount}/${taskCount} タスク完了`;
            card.appendChild(name);
            card.appendChild(meta);
            navCards.appendChild(card);
        });
        container.appendChild(navCards);

        // Build one combined gantt with all projects
        const allBars = [];
        const allTasksMeta = []; // for color mapping
        let colorIndex = 0;

        // Inject dynamic styles for all bars
        let css = "";
        const styleEl = document.getElementById("gantt-theme-styles");
        if (styleEl) styleEl.remove();
        const style = document.createElement("style");
        style.id = "gantt-theme-styles";

        const theme = themes[currentTheme];

        projects.forEach((project) => {
            const tasks = project.tasks.filter(t => t.start && t.end);
            if (tasks.length === 0) return;

            // Project separator bar (full-width label, no real dates — use project date range)
            if (project.start_date && project.end_date) {
                const sepClass = `bar-project-sep-${project.id}`;
                allBars.push({
                    id: `project-${project.id}`,
                    name: `■ ${project.name}`,
                    start: project.start_date,
                    end: project.end_date,
                    progress: 0,
                    custom_class: sepClass,
                });
                css += `.${sepClass} .bar { fill: #484848 !important; opacity: 0.9; }\n`;
                css += `.${sepClass} .bar-progress { fill: #484848 !important; }\n`;
                css += `.${sepClass} .bar-label { fill: #fff !important; font-weight: 700 !important; font-size: 13px !important; }\n`;
            }

            tasks.forEach((t) => {
                const ci = colorIndex % theme.bar.length;
                const barClass = t.is_completed ? "bar-completed" : `bar-ov-${colorIndex}`;
                allBars.push({
                    id: t.id,
                    name: t.name,
                    start: t.start.split("T")[0],
                    end: t.end.split("T")[0],
                    progress: t.progress,
                    custom_class: barClass,
                    _projectId: project.id,
                });
                css += `.bar-ov-${colorIndex} .bar { fill: ${theme.bar[ci]} !important; }\n`;
                css += `.bar-ov-${colorIndex} .bar-progress { fill: ${theme.progress[ci]} !important; }\n`;
                colorIndex++;
            });
        });

        style.textContent = css;
        document.head.appendChild(style);

        if (allBars.length === 0) {
            container.innerHTML += '<p class="placeholder">タスクがありません</p>';
            return;
        }

        // Wrapper: fixed labels on left + scrollable gantt on right
        const wrapper = document.createElement("div");
        wrapper.className = "overview-wrapper";

        const labelsDiv = document.createElement("div");
        labelsDiv.className = "overview-labels";

        const ganttScroll = document.createElement("div");
        ganttScroll.className = "overview-gantt-scroll";

        const ganttDiv = document.createElement("div");
        ganttDiv.className = "gantt-target";
        ganttScroll.appendChild(ganttDiv);

        wrapper.appendChild(labelsDiv);
        wrapper.appendChild(ganttScroll);
        container.appendChild(wrapper);

        ganttChart = new Gantt(ganttDiv, allBars, {
            view_mode: currentMode,
            padding: 18,
            popup_trigger: "manual",
            on_click: () => {},
            on_date_change: () => {},
            on_progress_change: () => {},
        });

        // Build fixed labels after gantt renders
        setTimeout(() => {
            buildOverviewLabels(ganttDiv, labelsDiv, allBars, projects);
            addOverlays(ganttDiv);
        }, 60);

        // Click on bar → navigate to that project
        ganttDiv.addEventListener("click", (e) => {
            const barWrapper = e.target.closest(".bar-wrapper");
            if (!barWrapper) return;
            const barLabel = barWrapper.querySelector(".bar-label");
            if (!barLabel) return;
            const name = barLabel.textContent.trim();

            const sepProject = projects.find(p => name === `■ ${p.name}`);
            if (sepProject) {
                projectSelect.value = String(sepProject.id);
                projectSelect.dispatchEvent(new Event("change"));
                return;
            }

            const bar = allBars.find(b => b.name === name && b._projectId);
            if (bar) {
                projectSelect.value = String(bar._projectId);
                projectSelect.dispatchEvent(new Event("change"));
            }
        });
    }

    // ── Build fixed labels for overview ──
    function buildOverviewLabels(ganttDiv, labelsDiv, allBars, projects) {
        labelsDiv.innerHTML = "";

        const svg = ganttDiv.querySelector("svg.gantt");
        if (!svg) return;

        const gridRows = svg.querySelectorAll(".grid .grid-row");
        if (gridRows.length === 0) return;

        // Get header height (space above first grid row)
        const headerHeight = parseFloat(gridRows[0].getAttribute("y"));

        // Spacer for header area
        const spacer = document.createElement("div");
        spacer.className = "overview-label-spacer";
        spacer.style.height = `${headerHeight}px`;
        labelsDiv.appendChild(spacer);

        // Create a label for each bar row
        allBars.forEach((bar, i) => {
            if (i >= gridRows.length) return;
            const row = gridRows[i];
            const rowHeight = parseFloat(row.getAttribute("height"));

            const label = document.createElement("div");
            label.className = "overview-label";
            label.style.height = `${rowHeight}px`;

            const isProject = bar.id.toString().startsWith("project-");

            if (isProject) {
                label.className = "overview-label is-project";
                const projectName = bar.name.replace("■ ", "");
                label.textContent = projectName;
                label.style.cursor = "pointer";
                label.addEventListener("click", () => {
                    const proj = projects.find(p => p.name === projectName);
                    if (proj) {
                        projectSelect.value = String(proj.id);
                        projectSelect.dispatchEvent(new Event("change"));
                    }
                });
            } else {
                label.textContent = bar.name;
            }

            labelsDiv.appendChild(label);
        });

        // Sync vertical scroll
        ganttDiv.closest(".overview-gantt-scroll").addEventListener("scroll", (e) => {
            labelsDiv.scrollTop = e.target.scrollTop;
        });
    }

    // Load initial view based on URL hash
    (async function initFromHash() {
        const hash = window.location.hash;
        const projectMatch = hash.match(/^#project-(\d+)(?:-task-(\d+))?$/);
        if (projectMatch) {
            const pid = projectMatch[1];
            const tid = projectMatch[2];
            projectSelect.value = pid;
            currentProjectId = pid;

            skipPushState = true;
            if (tid) {
                navStack = [{ type: "project", projectId: pid }];
                await drillDown(tid);
            } else {
                await loadProjectTasks(pid);
            }
            skipPushState = false;
        } else {
            history.replaceState({ view: "overview" }, "", "#overview");
            await loadOverview();
        }
    })();

    // ── Color helpers ──
    function getItemColor(itemId, index) {
        const theme = themes[currentTheme];
        if (colorOverrides[itemId]) return { bar: colorOverrides[itemId], progress: darken(colorOverrides[itemId], 0.2) };
        const i = index % theme.bar.length;
        return { bar: theme.bar[i], progress: theme.progress[i] };
    }
    function darken(hex, amt) {
        const n = parseInt(hex.replace("#",""),16);
        const r = Math.max(0,Math.floor((n>>16)*(1-amt)));
        const g = Math.max(0,Math.floor(((n>>8)&0xff)*(1-amt)));
        const b = Math.max(0,Math.floor((n&0xff)*(1-amt)));
        return `#${(r<<16|g<<8|b).toString(16).padStart(6,"0")}`;
    }
    function applyColorStyles(items, hasParent) {
        let el = document.getElementById("gantt-theme-styles");
        if (el) el.remove();
        const style = document.createElement("style");
        style.id = "gantt-theme-styles";
        let css = "";
        if (hasParent) {
            css += `.bar-parent .bar { fill: #a0a0a0 !important; }\n`;
            css += `.bar-parent .bar-progress { fill: #777 !important; }\n`;
        }
        items.forEach((item, i) => {
            const c = getItemColor(item.id, i);
            css += `.bar-item-${i} .bar { fill: ${c.bar} !important; }\n`;
            css += `.bar-item-${i} .bar-progress { fill: ${c.progress} !important; }\n`;
        });
        style.textContent = css;
        document.head.appendChild(style);
    }

    // ── Build legend ──
    function buildLegend(items, el) {
        const legend = document.createElement("div");
        legend.className = "color-legend";
        items.forEach((item, i) => {
            if (item.is_completed) return;
            const c = getItemColor(item.id, i);
            const pill = document.createElement("span"); pill.className = "color-legend-item";
            const dot = document.createElement("span"); dot.className = "color-dot"; dot.style.background = c.bar;
            const inp = document.createElement("input"); inp.type = "color"; inp.value = c.bar;
            inp.addEventListener("input", (e) => {
                colorOverrides[item.id] = e.target.value;
                dot.style.background = e.target.value;
                applyColorStyles(items, false);
            });
            const lbl = document.createElement("span"); lbl.textContent = item.name;
            dot.appendChild(inp); pill.appendChild(dot); pill.appendChild(lbl);
            legend.appendChild(pill);
        });
        el.appendChild(legend);
    }

    // ── Render current view ──
    function renderCurrentView() {
        const last = navStack[navStack.length - 1];
        if (!last) return;
        if (last.type === "project") loadProjectTasks(last.projectId);
        else if (last.type === "task") drillDown(last.taskId);
    }

    // ── Load project tasks (top level) ──
    async function loadProjectTasks(projectId) {
        const res = await fetch(`/api/v1/gantt/projects/${projectId}`);
        const tasks = await res.json();
        navStack = [{ type: "project", projectId }];
        expandedTaskId = null;
        currentTasks = tasks;
        renderGanttView(tasks, null);
    }

    // ── Drill down into a task ──
    async function drillDown(taskId) {
        const res = await fetch(`/api/v1/gantt/tasks/${taskId}/children`);
        const data = await res.json();
        if (!data.parent || data.children.length === 0) return;

        navStack.push({ type: "task", taskId });
        expandedTaskId = null;
        colorOverrides = {};
        currentTasks = data.children;
        if (!skipPushState) {
            history.pushState(
                { view: "drilldown", projectId: currentProjectId, taskId },
                "",
                `#project-${currentProjectId}-task-${taskId}`
            );
        }
        renderGanttView(data.children, data.parent);
    }

    // ── Main render: gantt bars + task cards below ──
    function renderGanttView(tasks, parentTask) {
        if (tasks.length === 0) {
            container.innerHTML = '<p class="placeholder">タスクがありません</p>';
            ganttChart = null;
            return;
        }

        const allBars = [];

        // Parent bar at top (if drilled down)
        if (parentTask && parentTask.start && parentTask.end) {
            allBars.push({
                id: parentTask.id, name: `◀ ${parentTask.name}`,
                start: parentTask.start.split("T")[0], end: parentTask.end.split("T")[0],
                progress: parentTask.progress, custom_class: "bar-parent",
            });
        }

        // Task bars
        tasks.filter(t => t.start && t.end).forEach((t, i) => {
            allBars.push({
                id: t.id, name: t.name,
                start: t.start.split("T")[0], end: t.end.split("T")[0],
                progress: t.progress,
                custom_class: t.is_completed ? "bar-completed" : `bar-item-${i}`,
            });
        });

        if (allBars.length === 0) {
            container.innerHTML = '<p class="placeholder">日付が設定されていないタスクです</p>';
            ganttChart = null;
            return;
        }

        applyColorStyles(tasks, !!parentTask);
        container.innerHTML = "";
        buildLegend(tasks, container);

        const ganttDiv = document.createElement("div");
        ganttDiv.className = "gantt-target";
        container.appendChild(ganttDiv);

        ganttChart = new Gantt(ganttDiv, allBars, {
            view_mode: currentMode,
            padding: 18,
            popup_trigger: "manual",
            on_click: () => {},
            on_date_change: () => {},
            on_progress_change: () => {},
        });

        // Click handler for parent bar (go back)
        if (parentTask) {
            ganttDiv.addEventListener("click", (e) => {
                const barWrapper = e.target.closest(".bar-wrapper");
                if (!barWrapper) return;
                const barLabel = barWrapper.querySelector(".bar-label");
                if (barLabel && barLabel.textContent.trim() === `◀ ${parentTask.name}`) {
                    goBack();
                }
            });
        }

        setTimeout(() => addOverlays(ganttDiv), 50);

        // Add task button
        if (currentProjectId) {
            const addBar = document.createElement("div");
            addBar.className = "add-task-bar";
            const addBtn = document.createElement("a");
            addBtn.href = `/projects/${currentProjectId}/tasks/new`;
            addBtn.className = "add-task-btn";
            addBtn.textContent = "＋ タスクを追加";
            addBar.appendChild(addBtn);
            container.appendChild(addBar);
        }

        // Task cards below gantt
        const cardsSection = document.createElement("div");
        cardsSection.className = "task-cards-section";
        container.appendChild(cardsSection);

        // Sort all tasks by end date (earliest first)
        const sortedTasks = [...tasks].sort((a, b) => {
            const aEnd = a.end ? new Date(a.end) : new Date("9999-12-31");
            const bEnd = b.end ? new Date(b.end) : new Date("9999-12-31");
            return aEnd - bEnd;
        });

        // Create placeholders in order, then fill async ones
        sortedTasks.forEach((taskData) => {
            const taskIndex = tasks.indexOf(taskData);
            const placeholder = document.createElement("div");
            placeholder.className = "task-card-slot";
            cardsSection.appendChild(placeholder);

            if (taskData.has_children) {
                loadTaskCard(taskData, taskIndex, placeholder);
            } else {
                renderLeafCard(taskData, taskIndex, placeholder);
            }
        });
    }

    // ── Load and render a single task's card ──
    async function loadTaskCard(taskData, taskIndex, parentEl) {
        const taskId = taskData.id.replace("task-", "");
        const res = await fetch(`/api/v1/gantt/tasks/${taskId}/children`);
        const data = await res.json();
        if (!data.children || data.children.length === 0) return;

        const children = data.children;
        const completed = children.filter(c => {
            if (c.has_children) return c.completed_count === c.total_count && c.total_count > 0;
            return c.is_completed;
        }).length;
        const total = children.length;
        const color = getItemColor(taskData.id, taskIndex);

        const panel = document.createElement("div");
        panel.className = "expand-panel";
        panel.style.borderColor = color.bar;

        // Header (clickable to drill down)
        const header = document.createElement("div");
        header.className = "expand-panel-header";
        header.style.background = color.bar;
        header.style.cursor = "pointer";
        header.title = "クリックでガントチャートに展開";
        header.addEventListener("click", () => {
            drillDown(taskId);
        });

        const titleArea = document.createElement("div");
        titleArea.className = "expand-panel-title-area";

        const dot = document.createElement("span");
        dot.className = "expand-panel-dot";
        dot.style.background = "#fff";

        const title = document.createElement("span");
        title.className = "expand-panel-title";
        title.textContent = taskData.name;

        const arrow = document.createElement("span");
        arrow.className = "expand-panel-arrow";
        arrow.textContent = "▶";

        const progressEl = document.createElement("span");
        progressEl.className = "expand-panel-progress";
        progressEl.style.color = color.bar;
        progressEl.textContent = `${completed}/${total} 完了`;

        const headerMeta = document.createElement("span");
        headerMeta.className = "expand-panel-meta";
        const hDateStr = `${fmtShortDate(taskData.start)} → ${fmtShortDate(taskData.end)}`;
        const hMemberStr = taskData.assigned_member ? ` ・ ${taskData.assigned_member}` : "";
        headerMeta.textContent = hDateStr + hMemberStr;

        titleArea.appendChild(dot);
        titleArea.appendChild(title);
        titleArea.appendChild(arrow);
        header.appendChild(titleArea);
        header.appendChild(headerMeta);
        header.appendChild(progressEl);
        panel.appendChild(header);

        // Progress bar
        const pbar = document.createElement("div");
        pbar.className = "expand-progress-bar";
        const pfill = document.createElement("div");
        pfill.className = "expand-progress-fill";
        pfill.style.width = total > 0 ? `${(completed/total)*100}%` : "0%";
        pfill.style.background = color.bar;
        pbar.appendChild(pfill);
        panel.appendChild(pbar);

        // Sort children by end date (earliest first)
        children.sort((a, b) => {
            const aEnd = a.end ? new Date(a.end) : new Date("9999-12-31");
            const bEnd = b.end ? new Date(b.end) : new Date("9999-12-31");
            return aEnd - bEnd;
        });

        // Children cards
        const cards = document.createElement("div");
        cards.className = "expand-cards";

        children.forEach((child) => {
            const card = document.createElement("div");
            card.className = `expand-card ${child.is_completed ? "completed" : ""}`;
            card.style.setProperty("--parent-color", color.bar);

            const check = document.createElement("span");
            check.className = "expand-card-check";

            if (child.has_children) {
                // Has children — show sub-progress instead of toggle
                const allDone = child.completed_count === child.total_count && child.total_count > 0;
                if (allDone) card.classList.add("completed");
                check.className = `expand-card-check has-sub ${allDone ? "all-done" : ""}`;
                check.textContent = `${child.completed_count}/${child.total_count}`;
                check.title = allDone
                    ? "全ての子タスクが完了"
                    : `子タスクが未完了 (${child.completed_count}/${child.total_count})`;
            } else {
                check.textContent = child.is_completed ? "✓" : "";
                check.style.cursor = "pointer";
                check.title = child.is_completed ? "未完了に戻す" : "完了にする";
                check.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    const cid = child.id.replace("task-", "");
                    const newState = !child.is_completed;
                    try {
                        const resp = await fetch(`/api/v1/tasks/${cid}`, {
                            method: "PUT",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ is_completed: newState }),
                        });
                        if (!resp.ok) {
                            const err = await resp.json();
                            alert(err.detail || "更新に失敗しました");
                            return;
                        }
                        child.is_completed = newState;
                        child.progress = newState ? 100 : 0;
                        check.textContent = newState ? "✓" : "";
                        check.title = newState ? "未完了に戻す" : "完了にする";
                        card.className = `expand-card ${newState ? "completed" : ""}`;
                        card.style.setProperty("--parent-color", color.bar);

                        // Update parent progress
                        const newCompleted = children.filter(c => {
                            if (c.has_children) return c.completed_count === c.total_count && c.total_count > 0;
                            return c.is_completed;
                        }).length;
                        progressEl.textContent = `${newCompleted}/${total} 完了`;
                        pfill.style.width = `${(newCompleted/total)*100}%`;
                    } catch (err) {
                        alert("通信エラーが発生しました");
                    }
                });
            }

            const info = document.createElement("div");
            info.className = "expand-card-info";

            const name = document.createElement("div");
            name.className = "expand-card-name";
            name.textContent = child.name;

            const meta = document.createElement("div");
            meta.className = "expand-card-meta";
            const dateStr = `${fmtShortDate(child.start)} → ${fmtShortDate(child.end)}`;
            const memberStr = child.assigned_member ? ` ・ ${child.assigned_member}` : "";
            meta.textContent = dateStr + memberStr;

            info.appendChild(name);
            info.appendChild(meta);
            card.appendChild(check);
            card.appendChild(info);

            // Check items link
            const checksLink = document.createElement("a");
            checksLink.className = "expand-card-checks-link";
            checksLink.href = `/tasks/${child.id.replace("task-", "")}/checks`;
            checksLink.textContent = "達成項目";
            checksLink.title = "達成項目を表示";
            checksLink.addEventListener("click", (e) => e.stopPropagation());
            card.appendChild(checksLink);

            // Add child task link
            const addChildLink = document.createElement("a");
            addChildLink.className = "expand-card-checks-link";
            addChildLink.href = `/projects/${currentProjectId}/tasks/new?parent_id=${child.id.replace("task-", "")}`;
            addChildLink.textContent = "＋子タスク";
            addChildLink.title = "子タスクを追加";
            addChildLink.addEventListener("click", (e) => e.stopPropagation());
            card.appendChild(addChildLink);

            // Edit task link
            const editLink = document.createElement("a");
            editLink.className = "expand-card-checks-link";
            editLink.href = `/tasks/${child.id.replace("task-", "")}/edit`;
            editLink.textContent = "編集";
            editLink.title = "タスクを編集";
            editLink.addEventListener("click", (e) => e.stopPropagation());
            card.appendChild(editLink);

            cards.appendChild(card);
        });

        panel.appendChild(cards);
        parentEl.appendChild(panel);
    }

    // ── Render a leaf task card (no children, just a checkable item) ──
    function renderLeafCard(taskData, taskIndex, parentEl) {
        const color = getItemColor(taskData.id, taskIndex);

        const panel = document.createElement("div");
        panel.className = "expand-panel leaf-panel";
        panel.style.borderColor = color.bar;

        const card = document.createElement("div");
        card.className = `leaf-card ${taskData.is_completed ? "completed" : ""}`;

        const check = document.createElement("span");
        check.className = "expand-card-check";
        check.textContent = taskData.is_completed ? "✓" : "";
        check.style.cursor = "pointer";
        check.title = taskData.is_completed ? "未完了に戻す" : "完了にする";
        check.addEventListener("click", async (e) => {
            e.stopPropagation();
            const tid = taskData.id.replace("task-", "");
            const newState = !taskData.is_completed;
            try {
                const resp = await fetch(`/api/v1/tasks/${tid}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_completed: newState }),
                });
                if (!resp.ok) {
                    const err = await resp.json();
                    alert(err.detail || "更新に失敗しました");
                    return;
                }
                taskData.is_completed = newState;
                check.textContent = newState ? "✓" : "";
                check.title = newState ? "未完了に戻す" : "完了にする";
                card.className = `leaf-card ${newState ? "completed" : ""}`;
            } catch (err) {
                alert("通信エラーが発生しました");
            }
        });

        const dot = document.createElement("span");
        dot.className = "leaf-card-dot";
        dot.style.background = color.bar;

        const info = document.createElement("div");
        info.className = "expand-card-info";

        const name = document.createElement("div");
        name.className = "expand-card-name";
        name.textContent = taskData.name;

        const meta = document.createElement("div");
        meta.className = "expand-card-meta";
        const dateStr = `${fmtShortDate(taskData.start)} → ${fmtShortDate(taskData.end)}`;
        const memberStr = taskData.assigned_member ? ` ・ ${taskData.assigned_member}` : "";
        meta.textContent = dateStr + memberStr;

        info.appendChild(name);
        info.appendChild(meta);

        // Check items link
        const checksLink = document.createElement("a");
        checksLink.className = "leaf-card-checks-link";
        checksLink.href = `/tasks/${taskData.id.replace("task-", "")}/checks`;
        checksLink.textContent = "達成項目";
        checksLink.title = "達成項目を表示";
        checksLink.addEventListener("click", (e) => e.stopPropagation());

        // Add child task link
        const addChildLink = document.createElement("a");
        addChildLink.className = "leaf-card-checks-link";
        addChildLink.href = `/projects/${currentProjectId}/tasks/new?parent_id=${taskData.id.replace("task-", "")}`;
        addChildLink.textContent = "＋子タスク";
        addChildLink.title = "子タスクを追加";
        addChildLink.addEventListener("click", (e) => e.stopPropagation());

        // Edit task link
        const editLink = document.createElement("a");
        editLink.className = "leaf-card-checks-link";
        editLink.href = `/tasks/${taskData.id.replace("task-", "")}/edit`;
        editLink.textContent = "編集";
        editLink.title = "タスクを編集";
        editLink.addEventListener("click", (e) => e.stopPropagation());

        card.appendChild(check);
        card.appendChild(dot);
        card.appendChild(info);
        card.appendChild(checksLink);
        card.appendChild(addChildLink);
        card.appendChild(editLink);
        panel.appendChild(card);
        parentEl.appendChild(panel);
    }

    // ── Go back ──
    function goBack() {
        if (navStack.length <= 1) {
            if (currentProjectId) { navStack = []; colorOverrides = {}; expandedTaskId = null; loadProjectTasks(currentProjectId); }
            return;
        }
        navStack.pop();
        const prev = navStack[navStack.length - 1];
        colorOverrides = {};
        expandedTaskId = null;
        if (prev.type === "project") loadProjectTasks(prev.projectId);
        else { navStack.pop(); drillDown(prev.taskId); }
    }
});
