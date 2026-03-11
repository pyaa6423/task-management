import { Plugin, WorkspaceLeaf } from "obsidian";
import {
  PluginData,
  DEFAULT_PLUGIN_DATA,
  VIEW_TYPE_TIMELINE,
} from "./types";
import { TimelineView } from "./TimelineView";

export default class TimeManagementPlugin extends Plugin {
  pluginData: PluginData = { ...DEFAULT_PLUGIN_DATA };

  async onload(): Promise<void> {
    await this.loadPluginData();

    this.registerView(
      VIEW_TYPE_TIMELINE,
      (leaf: WorkspaceLeaf) => new TimelineView(leaf, this)
    );

    this.addRibbonIcon("calendar-clock", "タイムラインを開く", () => {
      this.activateView();
    });

    this.addCommand({
      id: "open-timeline",
      name: "タイムラインを開く",
      callback: () => this.activateView(),
    });
  }

  async onunload(): Promise<void> {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_TIMELINE);
  }

  async loadPluginData(): Promise<void> {
    const loaded = await this.loadData();
    this.pluginData = Object.assign({}, DEFAULT_PLUGIN_DATA, loaded);
  }

  async savePluginData(): Promise<void> {
    await this.saveData(this.pluginData);
  }

  private async activateView(): Promise<void> {
    const existing = this.app.workspace.getLeavesOfType(VIEW_TYPE_TIMELINE);
    if (existing.length > 0) {
      this.app.workspace.revealLeaf(existing[0]);
      return;
    }

    const leaf = this.app.workspace.getLeaf(false);
    await leaf.setViewState({
      type: VIEW_TYPE_TIMELINE,
      active: true,
    });
    this.app.workspace.revealLeaf(leaf);
  }
}
