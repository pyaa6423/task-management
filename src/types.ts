export type EventColor =
  | "red"
  | "orange"
  | "yellow"
  | "green"
  | "teal"
  | "blue"
  | "purple"
  | "pink"
  | "gray";

export interface ColorEntry {
  key: EventColor;
  label: string;
  hex: string;
  textHex: string;
}

export const COLOR_PALETTE: ColorEntry[] = [
  { key: "red",    label: "Red",    hex: "#E53E3E", textHex: "#ffffff" },
  { key: "orange", label: "Orange", hex: "#DD6B20", textHex: "#ffffff" },
  { key: "yellow", label: "Yellow", hex: "#D69E2E", textHex: "#1a1a1a" },
  { key: "green",  label: "Green",  hex: "#38A169", textHex: "#ffffff" },
  { key: "teal",   label: "Teal",   hex: "#319795", textHex: "#ffffff" },
  { key: "blue",   label: "Blue",   hex: "#3182CE", textHex: "#ffffff" },
  { key: "purple", label: "Purple", hex: "#805AD5", textHex: "#ffffff" },
  { key: "pink",   label: "Pink",   hex: "#D53F8C", textHex: "#ffffff" },
  { key: "gray",   label: "Gray",   hex: "#718096", textHex: "#ffffff" },
];

export interface TimelineEvent {
  id: string;
  title: string;
  startMinutes: number; // 0–1439
  endMinutes: number;   // 1–1440
  color: EventColor;
  notes?: string;
  date: string;         // "YYYY-MM-DD"
}

export interface PluginData {
  events: TimelineEvent[];
  currentDate: string;
  defaultColor: EventColor;
}

export const DEFAULT_PLUGIN_DATA: PluginData = {
  events: [],
  currentDate: (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; })(),
  defaultColor: "blue",
};

export const VIEW_TYPE_TIMELINE = "time-management-timeline";

export const PIXELS_PER_HOUR   = 80;
export const PIXELS_PER_MINUTE = PIXELS_PER_HOUR / 60;
export const TIMELINE_HEIGHT   = PIXELS_PER_HOUR * 24;
export const HOUR_LABEL_WIDTH  = 56;
export const EVENT_LEFT_OFFSET = 64;
export const MIN_EVENT_HEIGHT  = 20;
export const SNAP_MINUTES      = 15;
