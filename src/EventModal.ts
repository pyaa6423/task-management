import { App, Modal } from "obsidian";
import {
  TimelineEvent,
  PluginData,
  COLOR_PALETTE,
  EventColor,
} from "./types";
import { minutesToTimeString, timeStringToMinutes, generateId } from "./utils";

export class EventModal extends Modal {
  private data: PluginData;
  private existingEvent: TimelineEvent | null;
  private prefillStart: number;
  private prefillEnd: number;
  private prefillDate: string;
  private onSave: (event: TimelineEvent) => void;
  private onDelete: ((id: string) => void) | null;

  private selectedColor: EventColor;
  private errorEl: HTMLElement | null = null;

  constructor(
    app: App,
    data: PluginData,
    existingEvent: TimelineEvent | null,
    prefillStart: number,
    prefillEnd: number,
    prefillDate: string,
    onSave: (event: TimelineEvent) => void,
    onDelete: ((id: string) => void) | null = null
  ) {
    super(app);
    this.data = data;
    this.existingEvent = existingEvent;
    this.prefillStart = prefillStart;
    this.prefillEnd = prefillEnd;
    this.prefillDate = prefillDate;
    this.onSave = onSave;
    this.onDelete = onDelete;
    this.selectedColor = existingEvent?.color ?? data.defaultColor;
  }

  onOpen(): void {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass("tm-modal");

    // タイトル
    contentEl.createEl("h2", {
      text: this.existingEvent ? "イベントを編集" : "イベントを追加",
      cls: "tm-modal-title",
    });

    const form = contentEl.createDiv({ cls: "tm-modal-form" });

    // タイトル入力
    const titleField = this.createField(form, "タイトル");
    const titleInput = titleField.createEl("input", {
      type: "text",
      cls: "tm-modal-input",
    });
    titleInput.placeholder = "用事の名前";
    titleInput.value = this.existingEvent?.title ?? "";
    titleInput.focus();

    // 日付
    const dateField = this.createField(form, "日付");
    const dateInput = dateField.createEl("input", {
      type: "date",
      cls: "tm-modal-input",
    });
    dateInput.value = this.existingEvent?.date ?? this.prefillDate;

    // 開始・終了時間（横並び）
    const timeRow = form.createDiv({ cls: "tm-modal-time-row" });
    const startField = this.createField(timeRow, "開始時間");
    const startInput = startField.createEl("input", {
      type: "time",
      cls: "tm-modal-input",
    });
    startInput.value = minutesToTimeString(
      this.existingEvent?.startMinutes ?? this.prefillStart
    );

    const endField = this.createField(timeRow, "終了時間");
    const endInput = endField.createEl("input", {
      type: "time",
      cls: "tm-modal-input",
    });
    endInput.value = minutesToTimeString(
      this.existingEvent?.endMinutes ?? this.prefillEnd
    );

    // 色選択
    const colorField = this.createField(form, "カラー");
    const swatchGrid = colorField.createDiv({ cls: "tm-color-grid" });
    const swatchEls: Map<EventColor, HTMLElement> = new Map();

    for (const entry of COLOR_PALETTE) {
      const swatch = swatchGrid.createDiv({ cls: "tm-swatch" });
      swatch.style.backgroundColor = entry.hex;
      swatch.title = entry.label;
      if (entry.key === this.selectedColor) {
        swatch.addClass("tm-swatch--active");
      }
      swatch.addEventListener("click", () => {
        swatchEls.forEach((el) => el.removeClass("tm-swatch--active"));
        swatch.addClass("tm-swatch--active");
        this.selectedColor = entry.key;
      });
      swatchEls.set(entry.key, swatch);
    }

    // メモ
    const notesField = this.createField(form, "メモ（任意）");
    const notesInput = notesField.createEl("textarea", {
      cls: "tm-modal-textarea",
    });
    notesInput.rows = 3;
    notesInput.placeholder = "詳細メモ...";
    notesInput.value = this.existingEvent?.notes ?? "";

    // エラーメッセージ
    this.errorEl = form.createDiv({ cls: "tm-error-msg" });

    // ボタン行
    const btnRow = contentEl.createDiv({ cls: "tm-modal-buttons" });

    if (this.existingEvent && this.onDelete) {
      const deleteBtn = btnRow.createEl("button", {
        text: "削除",
        cls: "tm-btn-danger",
      });
      deleteBtn.addEventListener("click", () => {
        if (this.existingEvent && this.onDelete) {
          this.onDelete(this.existingEvent.id);
          this.close();
        }
      });
    }

    const spacer = btnRow.createDiv({ cls: "tm-btn-spacer" });
    spacer.style.flex = "1";

    const cancelBtn = btnRow.createEl("button", { text: "キャンセル" });
    cancelBtn.addEventListener("click", () => this.close());

    const saveBtn = btnRow.createEl("button", {
      text: "保存",
      cls: "tm-btn-primary",
    });
    saveBtn.addEventListener("click", () => {
      const title = titleInput.value.trim();
      const startMinutes = timeStringToMinutes(startInput.value);
      const endMinutes = timeStringToMinutes(endInput.value);
      const date = dateInput.value;

      if (!title) {
        this.showError("タイトルを入力してください。");
        return;
      }
      if (!date) {
        this.showError("日付を選択してください。");
        return;
      }
      if (endMinutes <= startMinutes) {
        this.showError("終了時間は開始時間より後にしてください。");
        return;
      }

      const event: TimelineEvent = {
        id: this.existingEvent?.id ?? generateId(),
        title,
        startMinutes,
        endMinutes,
        color: this.selectedColor,
        notes: notesInput.value.trim() || undefined,
        date,
      };

      this.onSave(event);
      this.close();
    });

    // Enter キーで保存
    titleInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") saveBtn.click();
    });
  }

  onClose(): void {
    this.contentEl.empty();
  }

  private createField(parent: HTMLElement, label: string): HTMLElement {
    const field = parent.createDiv({ cls: "tm-modal-field" });
    field.createEl("label", { text: label });
    return field;
  }

  private showError(msg: string): void {
    if (!this.errorEl) return;
    this.errorEl.setText(msg);
    this.errorEl.addClass("is-visible");
  }
}
