"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Section, Stat, Topology } from "@/components/Panels";
import { api } from "@/lib/api";
import { bytes, resolution } from "@/lib/format";
import type { CapabilityReport, DisplayReport, Health, HostReport, MediaAsset } from "@/lib/types";

export default function DashboardPage() {
  const [host, setHost] = useState<HostReport | null>(null);
  const [displays, setDisplays] = useState<DisplayReport | null>(null);
  const [media, setMedia] = useState<MediaAsset[] | null>(null);
  const [features, setFeatures] = useState<CapabilityReport | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    Promise.all([
      api<HostReport>("/system/host"),
      api<DisplayReport>("/displays"),
      api<MediaAsset[]>("/media"),
      api<CapabilityReport>("/system/capabilities"),
      api<Health>("/health", {}, false),
    ])
      .then(([nextHost, nextDisplays, nextMedia, nextFeatures, nextHealth]) => {
        setHost(nextHost);
        setDisplays(nextDisplays);
        setMedia(nextMedia);
        setFeatures(nextFeatures);
        setHealth(nextHealth);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "The dashboard could not load");
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const connected = displays?.outputs.filter((item) => item.connected).length;
  const unavailable = features?.features.filter((item) => item.status !== "available") ?? [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl text-paper">Dashboard</h1>
          <p className="mt-1 text-sm text-mist">Live host, display, and library data from this API process.</p>
        </div>
        <button type="button" onClick={load} className="border border-line px-3 py-2 text-sm text-paper hover:border-amber">
          Refresh
        </button>
      </div>
      {error ? <p className="border border-alarm/60 bg-alarm/10 px-3 py-2 text-sm text-alarm">{error}</p> : null}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Stat label="Computer" value={host?.hostname || "—"} detail={host ? `${host.platform} · Python ${host.python_version}` : "Waiting for host report"} />
        <Stat
          label="GPU"
          value={host?.gpu.available ? `${host.gpu.adapters.length} adapter${host.gpu.adapters.length === 1 ? "" : "s"}` : "None reported"}
          detail={host?.gpu.note}
        />
        <Stat
          label="Displays"
          value={connected == null ? "—" : String(connected)}
          detail={displays ? `${displays.adapter} · ${displays.query_succeeded ? "query succeeded" : "query failed"}` : "Waiting for display query"}
        />
        <Stat label="Media" value={media ? String(media.length) : "—"} detail="Stored originals. Upload does not re-encode." />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
        <Section
          title="Detected desktop"
          action={
            <Link href="/outputs" className="text-xs text-amber">
              Output detail
            </Link>
          }
        >
          {displays ? <Topology report={displays} /> : <p className="text-sm text-mist">Querying displays…</p>}
          {displays ? <p className="mt-3 text-xs leading-5 text-mist">{displays.note}</p> : null}
          {displays?.desktop ? (
            <p className="mt-2 font-mono text-xs text-paper">
              Desktop {resolution(displays.desktop.width, displays.desktop.height)} at {displays.desktop.x},{displays.desktop.y}
            </p>
          ) : null}
        </Section>
        <Section title="Service checks">
          <dl className="space-y-2 text-sm">
            {health
              ? Object.entries(health.checks).map(([name, status]) => (
                  <div key={name} className="flex justify-between border border-line px-3 py-2">
                    <dt className="text-mist">{name}</dt>
                    <dd className={status === "ok" ? "font-mono text-signal" : "font-mono text-alarm"}>{status}</dd>
                  </div>
                ))
              : <p className="text-mist">Waiting for health.</p>}
          </dl>
          <p className="mt-3 text-xs leading-5 text-mist">
            Memory available {host ? bytes(host.memory_available_bytes) : "—"} of {host ? bytes(host.memory_total_bytes) : "—"}. CPU
            threads {host?.cpu_count ?? "—"}.
          </p>
        </Section>
      </div>
      <Section title="Build scope">
        <div className="grid gap-2 md:grid-cols-2">
          {unavailable.map((item) => (
            <div key={item.id} className="border border-line bg-panel2 px-3 py-2">
              <div className="flex justify-between gap-3 text-sm text-paper">
                <span>{item.name}</span>
                <span className="font-mono text-[11px] text-amber">Phase {item.phase}</span>
              </div>
              <p className="mt-1 text-xs leading-5 text-mist">{item.summary}</p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
