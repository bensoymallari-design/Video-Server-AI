"use client";

import { useCallback, useEffect, useState } from "react";

import { Section, Topology } from "@/components/Panels";
import { api } from "@/lib/api";
import { rate, resolution, when } from "@/lib/format";
import type { DisplayReport } from "@/lib/types";

export default function OutputsPage() {
  const [report, setReport] = useState<DisplayReport | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const load = useCallback(() => {
    setPending(true);
    setError("");
    api<DisplayReport>("/displays")
      .then(setReport)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Display query failed"))
      .finally(() => setPending(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl text-paper">Display outputs</h1>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-mist">
            Read-only detection. This page does not change resolution, refresh rate, or desktop topology.
          </p>
        </div>
        <button type="button" onClick={load} className="border border-line px-3 py-2 text-sm text-paper hover:border-amber">
          {pending ? "Querying…" : "Query displays"}
        </button>
      </div>
      {error ? <p className="border border-alarm/60 px-3 py-2 text-sm text-alarm">{error}</p> : null}
      {report ? (
        <>
          <Section title="Topology">
            <Topology report={report} />
            <dl className="mt-4 grid gap-2 text-sm md:grid-cols-2">
              <div className="border border-line px-3 py-2">
                <dt className="text-mist">Adapter</dt>
                <dd className="font-mono text-paper">{report.adapter}</dd>
              </div>
              <div className="border border-line px-3 py-2">
                <dt className="text-mist">Captured</dt>
                <dd className="font-mono text-paper">{when(report.captured_at)}</dd>
              </div>
            </dl>
            <p className="mt-3 text-sm leading-6 text-mist">{report.note}</p>
            {report.virtual_output_suspected ? (
              <p className="mt-2 border border-amber/50 px-3 py-2 text-sm text-amber">
                A connected output name looks virtual. Treat it as a desktop session, not as a panel input.
              </p>
            ) : null}
          </Section>
          <Section title="Outputs and modes">
            <div className="space-y-4">
              {report.outputs.map((output) => (
                <article key={output.id} className="border border-line">
                  <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2">
                    <div>
                      <div className="text-sm text-paper">{output.name}</div>
                      <div className="font-mono text-[11px] text-mist">{output.connector}</div>
                    </div>
                    <div className="font-mono text-xs text-mist">
                      {output.connected ? "connected" : "disconnected"}
                      {output.primary ? " · primary" : ""} · {output.rotation} · {resolution(output.width, output.height)} ·{" "}
                      {output.refresh_hz == null ? "—" : rate(output.refresh_hz)}
                    </div>
                  </header>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-mist">
                        <tr>
                          <th className="px-3 py-2 font-medium">Mode</th>
                          <th className="px-3 py-2 font-medium">Refresh</th>
                          <th className="px-3 py-2 font-medium">Flags</th>
                        </tr>
                      </thead>
                      <tbody>
                        {output.modes.length ? (
                          output.modes.map((mode, index) => (
                            <tr key={`${output.id}-${index}`} className="border-t border-line font-mono">
                              <td className="px-3 py-2">{resolution(mode.width, mode.height)}</td>
                              <td className="px-3 py-2">{rate(mode.refresh_hz)}</td>
                              <td className="px-3 py-2 text-amber">
                                {mode.current ? "current " : ""}
                                {mode.preferred ? "preferred" : ""}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td className="px-3 py-2 text-mist" colSpan={3}>
                              No modes were listed.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </article>
              ))}
              {!report.outputs.length ? <p className="text-sm text-mist">The adapter returned an empty output list.</p> : null}
            </div>
          </Section>
          <Section title="Limits of this reading">
            <ul className="space-y-2 text-sm text-mist">
              {report.limitations.map((item) => (
                <li key={item} className="border border-line px-3 py-2">
                  {item}
                </li>
              ))}
            </ul>
          </Section>
        </>
      ) : (
        <p className="text-sm text-mist">Waiting for the display query.</p>
      )}
    </div>
  );
}
