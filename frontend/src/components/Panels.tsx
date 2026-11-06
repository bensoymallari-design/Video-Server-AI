import type { ReactNode } from "react";

import type { DisplayOutput, DisplayReport } from "@/lib/types";
import { resolution } from "@/lib/format";

export function Section({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="border border-line bg-panel">
      <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-mist">{title}</h2>
        {action}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}

export function Stat({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="border border-line bg-panel px-4 py-3">
      <div className="text-[11px] uppercase tracking-[0.16em] text-mist">{label}</div>
      <div className="mt-2 font-mono text-xl text-paper">{value}</div>
      {detail ? <div className="mt-1 text-xs leading-5 text-mist">{detail}</div> : null}
    </div>
  );
}

export function PhaseNotice({
  phase,
  title,
  summary,
  planned,
}: {
  phase: number;
  title: string;
  summary: string;
  planned: string[];
}) {
  return (
    <div className="mx-auto max-w-3xl">
      <div className="border border-amber/50 bg-panel">
        <div className="border-b border-line px-5 py-4">
          <div className="text-[11px] uppercase tracking-[0.18em] text-amber">Unavailable in this build · Phase {phase}</div>
          <h1 className="mt-2 text-2xl text-paper">{title}</h1>
        </div>
        <div className="space-y-4 px-5 py-5 text-sm leading-6 text-mist">
          <p>{summary}</p>
          <ul className="space-y-2">
            {planned.map((item) => (
              <li key={item} className="border border-line bg-panel2 px-3 py-2 text-paper">
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export function Meter({ label, percent }: { label: string; percent: number }) {
  const width = Math.max(0, Math.min(100, percent));
  return (
    <div>
      <div className="mb-1 flex justify-between font-mono text-xs text-mist">
        <span>{label}</span>
        <span>{width.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-black/50">
        <div className="h-2 bg-amber" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

export function Topology({ report }: { report: DisplayReport }) {
  const placed = report.outputs.filter(
    (item) => item.connected && item.width && item.height && item.position_x != null && item.position_y != null,
  );
  if (!report.query_succeeded) {
    return <p className="text-sm text-alarm">Display query failed. {report.error}</p>;
  }
  if (!placed.length) {
    return <p className="text-sm text-mist">The query succeeded and reported no placed, connected outputs.</p>;
  }
  const minX = Math.min(...placed.map((item) => item.position_x ?? 0));
  const minY = Math.min(...placed.map((item) => item.position_y ?? 0));
  const maxX = Math.max(...placed.map((item) => (item.position_x ?? 0) + (item.width ?? 0)));
  const maxY = Math.max(...placed.map((item) => (item.position_y ?? 0) + (item.height ?? 0)));
  const spanW = Math.max(1, maxX - minX);
  const spanH = Math.max(1, maxY - minY);
  return (
    <div className="relative h-72 w-full border border-line bg-black/40">
      {placed.map((item) => (
        <OutputBox key={item.id} item={item} minX={minX} minY={minY} spanW={spanW} spanH={spanH} />
      ))}
    </div>
  );
}

function OutputBox({
  item,
  minX,
  minY,
  spanW,
  spanH,
}: {
  item: DisplayOutput;
  minX: number;
  minY: number;
  spanW: number;
  spanH: number;
}) {
  return (
    <div
      className="absolute overflow-hidden border border-amber/80 bg-amber/10 p-2"
      style={{
        left: `${(((item.position_x ?? 0) - minX) / spanW) * 100}%`,
        top: `${(((item.position_y ?? 0) - minY) / spanH) * 100}%`,
        width: `${((item.width ?? 0) / spanW) * 100}%`,
        height: `${((item.height ?? 0) / spanH) * 100}%`,
      }}
    >
      <div className="text-xs text-paper">{item.name}</div>
      <div className="font-mono text-[11px] text-amber">{resolution(item.width, item.height)}</div>
      <div className="font-mono text-[11px] text-mist">
        {item.position_x},{item.position_y}
        {item.primary ? " · primary" : ""}
      </div>
    </div>
  );
}
