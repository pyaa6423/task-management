import { App } from "obsidian";
import {
  PluginData,
  TimelineEvent,
  COLOR_PALETTE,
  PIXELS_PER_HOUR,
  PIXELS_PER_MINUTE,
  TIMELINE_HEIGHT,
  HOUR_LABEL_WIDTH,
  EVENT_LEFT_OFFSET,
  MIN_EVENT_HEIGHT,
  SNAP_MINUTES,
} from "./types";
import {
  minutesToTimeString,
  snapToGrid,
  formatDateDisplay,
  addDays,
  isoDateToday,
} from "./utils";
import { EventModal } from "./EventModal";

export class TimelineRenderer {
  private container: HTMLElement;
  private app: App;
  private data: PluginData;
  private onDataChange: (data: PluginData) => void;

  private eventsLayer: HTMLElement | null = null;
  private currentTimeEl: HTMLElement | null = null;
  private scrollContainer: HTMLElement | null = null;
  private dateLabel: HTMLElement | null = null;
  private intervalId: number | null = null;

  constructor(
    container: HTMLElement,
    app: App,
    data: PluginData,
    onDataChange: (data: PluginData) => void
  ) {
    this.container = container;
    this.app = app;
    this.data = data;
    this.onDataChange = onDataChange;
  }

  mount(): void {
    this.container.empty();
    this.container.addClass("tm-timeline-root");

    const toolbar = this.buildToolbar();
    this.container.appendChild(toolbar);

    this.scrollContainer = this.container.createDiv({ cls: "tm-scroll-container" });
    const canvas = this.scrollContainer.createDiv({ cls: "tm-timeline-canvas" });
    canvas.style.height = `${TIMELINE_HEIGHT}px`;

    canvas.appendChild(this.buildHourGrid());

    this.eventsLayer = canvas.createDiv({ cls: "tm-events-layer" });
    this.renderEvents();

    // 現在時刻ライン
    this.currentTimeEl = canvas.createDiv({ cls: "tm-current-time" });
    this.updateCurrentTimeLine();
    this.startCurrentTimeUpdater();

    // クリックで新規イベント
    canvas.addEventListener("click", (e: MouseEvent) => this.handleCanvasClick(e, canvas));

    // 現在時刻付近にスクロール
    requestAnimationFrame(() => {
      const now = new Date();
      const targetPx = (now.getHours() - 1) * PIXELS_PER_HOUR;
      if (this.scrollContainer) {
        this.scrollContainer.scrollTop = Math.max(0, targetPx);
      }
    });
  }

  update(data: PluginData): void {
    this.data = data;
    this.renderEvents();
    if (this.dateLabel) {
      this.dateLabel.setText(formatDateDisplay(data.currentDate));
    }
  }

  destroy(): void {
    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.container.empty();
  }

  private buildToolbar(): HTMLElement {
    const toolbar = createDiv({ cls: "tm-toolbar" });

    const prevBtn = toolbar.createEl("button", { cls: "tm-nav-btn", text: "‹" });
    prevBtn.title = "前の日";
    prevBtn.addEventListener("click", () => this.navigateDate(-1));

    this.dateLabel = toolbar.createDiv({ cls: "tm-toolbar-date" });
    this.dateLabel.setText(formatDateDisplay(this.data.currentDate));

    const nextBtn = toolbar.createEl("button", { cls: "tm-nav-btn", text: "›" });
    nextBtn.title = "次の日";
    nextBtn.addEventListener("click", () => this.navigateDate(1));

    const todayBtn = toolbar.createEl("button", { cls: "tm-today-btn", text: "今日" });
    todayBtn.addEventListener("click", () => {
      const today = isoDateToday();
      if (this.data.currentDate !== today) {
        const newData = { ...this.data, currentDate: today };
        this.onDataChange(newData);
      }
    });

    return toolbar;
  }

  private buildHourGrid(): HTMLElement {
    const grid = createDiv({ cls: "tm-hour-grid" });

    for (let h = 0; h < 24; h++) {
      const row = grid.createDiv({ cls: "tm-hour-row" });
      row.style.height = `${PIXELS_PER_HOUR}px`;
      row.style.top = `${h * PIXELS_PER_HOUR}px`;

      const label = row.createDiv({ cls: "tm-hour-label" });
      label.setText(`${String(h).padStart(2, "0")}:00`);

      // 30分サブライン
      const halfLine = grid.createDiv({ cls: "tm-half-hour-line" });
      halfLine.style.top = `${h * PIXELS_PER_HOUR + PIXELS_PER_HOUR / 2}px`;
    }

    return grid;
  }

  private renderEvents(): void {
    if (!this.eventsLayer) return;
    this.eventsLayer.empty();

    const todayEvents = this.data.events.filter(
      (e) => e.date === this.data.currentDate
    );

    for (const event of todayEvents) {
      const el = this.createEventEl(event);
      this.eventsLayer.appendChild(el);
    }
  }

  private createEventEl(event: TimelineEvent): HTMLElement {
    const palette = COLOR_PALETTE.find((c) => c.key === event.color);
    const bgColor = palette?.hex ?? "#3182CE";
    const textColor = palette?.textHex ?? "#ffffff";

    const topPx = event.startMinutes * PIXELS_PER_MINUTE;
    const heightPx = Math.max(
      (event.endMinutes - event.startMinutes) * PIXELS_PER_MINUTE,
      MIN_EVENT_HEIGHT
    );

    const el = createDiv({ cls: "tm-event" });
    el.style.top = `${topPx}px`;
    el.style.height = `${heightPx}px`;
    el.style.left = `${EVENT_LEFT_OFFSET}px`;
    el.style.right = "8px";
    el.style.backgroundColor = bgColor;
    el.style.color = textColor;

    el.createDiv({ cls: "tm-event__title", text: event.title });

    const timeText = `${minutesToTimeString(event.startMinutes)} – ${minutesToTimeString(event.endMinutes)}`;
    el.createDiv({ cls: "tm-event__time", text: timeText });

    el.addEventListener("click", (e) => {
      e.stopPropagation();
      new EventModal(
        this.app,
        this.data,
        event,
        event.startMinutes,
        event.endMinutes,
        event.date,
        (updated) => {
          const events = this.data.events.map((ev) =>
            ev.id === updated.id ? updated : ev
          );
          this.onDataChange({ ...this.data, events });
        },
        (id) => {
          const events = this.data.events.filter((ev) => ev.id !== id);
          this.onDataChange({ ...this.data, events });
        }
      ).open();
    });

    return el;
  }

  private handleCanvasClick(e: MouseEvent, canvas: HTMLElement): void {
    const target = e.target as HTMLElement;
    if (target.closest(".tm-event")) return;

    const rect = canvas.getBoundingClientRect();
    const offsetY = e.clientY - rect.top + (this.scrollContainer?.scrollTop ?? 0);

    const rawMinutes = offsetY / PIXELS_PER_MINUTE;
    const snappedMinutes = snapToGrid(rawMinutes, SNAP_MINUTES);
    const startMinutes = Math.min(Math.max(snappedMinutes, 0), 1439);
    const endMinutes = Math.min(startMinutes + 60, 1440);

    new EventModal(
      this.app,
      this.data,
      null,
      startMinutes,
      endMinutes,
      this.data.currentDate,
      (newEvent) => {
        const events = [...this.data.events, newEvent];
        this.onDataChange({ ...this.data, events });
      }
    ).open();
  }

  private updateCurrentTimeLine(): void {
    if (!this.currentTimeEl) return;
    const now = new Date();
    const totalMinutes = now.getHours() * 60 + now.getMinutes();
    const topPx = totalMinutes * PIXELS_PER_MINUTE;
    this.currentTimeEl.style.top = `${topPx}px`;
  }

  private startCurrentTimeUpdater(): void {
    this.intervalId = window.setInterval(() => {
      this.updateCurrentTimeLine();
    }, 60_000);
  }

  private navigateDate(delta: -1 | 1): void {
    const newDate = addDays(this.data.currentDate, delta);
    this.onDataChange({ ...this.data, currentDate: newDate });
  }
}
