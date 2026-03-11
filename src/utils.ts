export function snapToGrid(minutes: number, gridSize: number): number {
  return Math.round(minutes / gridSize) * gridSize;
}

export function minutesToTimeString(totalMinutes: number): string {
  const clamped = Math.min(Math.max(totalMinutes, 0), 1440);
  const h = Math.floor(clamped / 60) % 24;
  const m = clamped % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function timeStringToMinutes(timeStr: string): number {
  const [h, m] = timeStr.split(":").map(Number);
  return h * 60 + m;
}

export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

export function isoDateToday(): string {
  return new Date().toISOString().split("T")[0];
}

export function formatDateDisplay(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  const today = isoDateToday();
  const todayDate = new Date();
  const yesterday = new Date(todayDate);
  yesterday.setDate(todayDate.getDate() - 1);
  const tomorrow = new Date(todayDate);
  tomorrow.setDate(todayDate.getDate() + 1);

  const formatYMD = (d: Date) => d.toISOString().split("T")[0];

  let prefix = "";
  if (isoDate === today) prefix = "今日 · ";
  else if (isoDate === formatYMD(yesterday)) prefix = "昨日 · ";
  else if (isoDate === formatYMD(tomorrow)) prefix = "明日 · ";

  const formatted = date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "short",
  });

  return prefix + formatted;
}

export function addDays(isoDate: string, delta: number): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  date.setDate(date.getDate() + delta);
  return date.toISOString().split("T")[0];
}
