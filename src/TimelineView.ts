import { ItemView, WorkspaceLeaf } from "obsidian";
import { VIEW_TYPE_TIMELINE } from "./types";
import { TimelineRenderer } from "./TimelineRenderer";
import TimeManagementPlugin from "./main";

export class TimelineView extends ItemView {
  private renderer: TimelineRenderer | null = null;
  private plugin: TimeManagementPlugin;

  constructor(leaf: WorkspaceLeaf, plugin: TimeManagementPlugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType(): string {
    return VIEW_TYPE_TIMELINE;
  }

  getDisplayText(): string {
    return "タイムライン";
  }

  getIcon(): string {
    return "calendar-clock";
  }

  async onOpen(): Promise<void> {
    this.renderer = new TimelineRenderer(
      this.contentEl,
      this.app,
      this.plugin.pluginData,
      async (newData) => {
        this.plugin.pluginData = newData;
        await this.plugin.savePluginData();
        this.renderer?.update(newData);
      }
    );
    this.renderer.mount();
  }

  async onClose(): Promise<void> {
    this.renderer?.destroy();
    this.renderer = null;
  }

  refresh(): void {
    this.renderer?.update(this.plugin.pluginData);
  }
}
