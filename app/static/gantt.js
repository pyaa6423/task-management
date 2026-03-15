document.addEventListener("DOMContentLoaded", () => {
    const projectSelect = document.getElementById("project-select");
    const container = document.getElementById("gantt-container");
    const viewButtons = document.querySelectorAll(".view-modes button");
    let ganttChart = null;
    let currentMode = "Day";

    viewButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            viewButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentMode = btn.dataset.mode;
            if (ganttChart) {
                ganttChart.change_view_mode(currentMode);
            }
        });
    });

    projectSelect.addEventListener("change", async () => {
        const projectId = projectSelect.value;
        if (!projectId) {
            container.innerHTML = '<p class="placeholder">Select a project to view the Gantt chart.</p>';
            ganttChart = null;
            return;
        }
        await loadGantt(projectId);
    });

    async function loadGantt(projectId) {
        const res = await fetch(`/api/v1/gantt/projects/${projectId}`);
        const tasks = await res.json();

        if (tasks.length === 0) {
            container.innerHTML = '<p class="placeholder">No tasks found for this project.</p>';
            ganttChart = null;
            return;
        }

        const ganttTasks = tasks
            .filter((t) => t.start && t.end)
            .map((t) => ({
                id: t.id,
                name: t.name,
                start: t.start.split("T")[0],
                end: t.end.split("T")[0],
                progress: t.progress,
                custom_class: getBarClass(t),
            }));

        if (ganttTasks.length === 0) {
            container.innerHTML = '<p class="placeholder">Tasks have no dates set.</p>';
            ganttChart = null;
            return;
        }

        container.innerHTML = "";
        ganttChart = new Gantt(container, ganttTasks, {
            view_mode: currentMode,
            on_click: async (task) => {
                const taskId = task.id.replace("task-", "");
                await loadSubtasks(taskId, task.name);
            },
            on_date_change: () => {},
            on_progress_change: () => {},
        });
    }

    async function loadSubtasks(taskId, taskName) {
        const res = await fetch(`/api/v1/gantt/tasks/${taskId}/subtasks`);
        const subtasks = await res.json();

        if (subtasks.length === 0) {
            alert(`No subtasks for "${taskName}".`);
            return;
        }

        const ganttTasks = subtasks
            .filter((s) => s.start && s.end)
            .map((s) => ({
                id: s.id,
                name: s.name,
                start: s.start.split("T")[0],
                end: s.end.split("T")[0],
                progress: s.progress,
                custom_class: getBarClass(s),
            }));

        if (ganttTasks.length === 0) {
            alert(`Subtasks for "${taskName}" have no dates set.`);
            return;
        }

        container.innerHTML = "";
        ganttChart = new Gantt(container, ganttTasks, {
            view_mode: currentMode,
        });
    }

    function getBarClass(item) {
        const classes = [];
        if (item.is_completed) {
            classes.push("bar-completed");
        }
        if (item.priority <= 1) {
            classes.push("bar-priority-high");
        } else if (item.priority <= 3) {
            classes.push("bar-priority-medium");
        } else {
            classes.push("bar-priority-low");
        }
        return classes.join(" ");
    }
});
