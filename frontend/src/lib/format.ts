export function bytes(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  let digits = 2;
  if (unit === 0 || size >= 100) digits = 0;
  else if (size >= 10) digits = 1;
  return `${size.toFixed(digits)} ${units[unit]}`;
}

export function resolution(width: number | null, height: number | null): string {
  if (width == null || height == null) return "—";
  return `${width}×${height}`;
}

export function seconds(value: number | null): string {
  if (value == null) return "—";
  const total = Math.round(value);
  const minutes = Math.floor(total / 60);
  const remain = total % 60;
  return `${minutes}:${remain.toString().padStart(2, "0")}`;
}

export function rate(value: number | null): string {
  if (value == null) return "—";
  return `${Number(value.toFixed(3))} Hz`;
}

export function when(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
    timeZoneName: "short",
  }).format(date);
}
