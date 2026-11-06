"use client";

import { useEffect, useState } from "react";

import { PhaseNotice, Section } from "@/components/Panels";
import { api } from "@/lib/api";
import { bytes } from "@/lib/format";
import type { HostReport } from "@/lib/types";

export default function DevicesPage() {
  const [host, setHost] = useState<HostReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<HostReport>("/system/host")
      .then(setHost)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Host query failed"));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl text-paper">Device manager</h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-mist">
          This API process is the local device agent for the computer it is running on. Remote pairing is Phase 6.
        </p>
      </div>
      {error ? <p className="text-sm text-alarm">{error}</p> : null}
      <Section title="Local playback computer">
        {host ? (
          <dl className="grid gap-2 text-sm md:grid-cols-2">
            <Item label="Hostname" value={host.hostname} />
            <Item label="Platform" value={host.platform_version} />
            <Item label="Python" value={host.python_version} />
            <Item label="CPU threads" value={String(host.cpu_count ?? "—")} />
            <Item label="Memory" value={bytes(host.memory_total_bytes)} />
            <Item label="Bind" value={host.localhost_only ? "Loopback only" : "Not loopback"} />
            <Item label="GPU reported" value={host.gpu.available ? "Yes" : "No"} />
            <Item label="App" value={`${host.app_version} · phase ${host.phase}`} />
          </dl>
        ) : (
          <p className="text-sm text-mist">Reading the local host…</p>
        )}
        {host?.gpu.adapters.length ? (
          <ul className="mt-3 space-y-2">
            {host.gpu.adapters.map((adapter) => (
              <li key={`${adapter.source}:${adapter.name}`} className="border border-line px-3 py-2 font-mono text-xs text-paper">
                {adapter.name}
                <span className="text-mist"> · {adapter.source}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {host ? <p className="mt-3 text-xs leading-5 text-mist">{host.gpu.note}</p> : null}
      </Section>
      <PhaseNotice
        phase={6}
        title="Remote device agents"
        summary="Discovery, pairing, media distribution, and scheduled multi-computer playback are not implemented. No network device is contacted."
        planned={["Authorized device list", "Pairing", "Media distribution", "Coordinated start times"]}
      />
    </div>
  );
}

function Item({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line px-3 py-2">
      <dt className="text-mist">{label}</dt>
      <dd className="font-mono text-paper">{value}</dd>
    </div>
  );
}
