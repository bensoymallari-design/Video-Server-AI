"use client";

import { useEffect, useState } from "react";

import { Meter, Section } from "@/components/Panels";
import { statusSocketUrl } from "@/lib/api";
import { bytes, when } from "@/lib/format";
import type { StatusSample } from "@/lib/types";

export default function MonitoringPage() {
  const [sample, setSample] = useState<StatusSample | null>(null);
  const [state, setState] = useState("connecting");
  const [receivedAt, setReceivedAt] = useState<number | null>(null);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let stopped = false;
    let retry: number | undefined;

    const connect = () => {
      socket = new WebSocket(statusSocketUrl());
      socket.onopen = () => setState("live");
      socket.onmessage = (event) => {
        setSample(JSON.parse(event.data) as StatusSample);
        setReceivedAt(Date.now());
      };
      socket.onerror = () => setState("error");
      socket.onclose = () => {
        setState("disconnected");
        if (!stopped) retry = window.setTimeout(connect, 2000);
      };
    };
    connect();
    return () => {
      stopped = true;
      if (retry) window.clearTimeout(retry);
      socket?.close();
    };
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl text-paper">System monitoring</h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-mist">
          CPU, memory, disk, and the connected-display count from this machine. Dropped-frame and GPU decode counters are not collected in this build.
        </p>
      </div>
      <Section title={`Channel ${state}`}>
        {sample ? (
          <div className="space-y-4">
            <Meter label="CPU" percent={sample.cpu_percent} />
            <Meter label="Memory" percent={sample.memory_percent} />
            <Meter label="Disk" percent={sample.disk_percent} />
            <dl className="grid gap-2 text-sm md:grid-cols-2">
              <Row label="Sample time" value={when(`${sample.time}`)} />
              <Row label="Process uptime" value={`${sample.uptime_seconds} s`} />
              <Row label="Memory used" value={`${bytes(sample.memory_used_bytes)} / ${bytes(sample.memory_total_bytes)}`} />
              <Row label="Data disk" value={`${bytes(sample.disk_used_bytes)} / ${bytes(sample.disk_total_bytes)}`} />
              <Row
                label="Connected displays"
                value={sample.displays_connected == null ? "Unknown" : String(sample.displays_connected)}
              />
              <Row label="Last message" value={receivedAt ? "just received" : "—"} />
            </dl>
            {state !== "live" ? (
              <p className="text-sm text-amber">The numbers above are the last sample. The channel is {state}.</p>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-mist">Waiting for the first sample. The socket is {state}.</p>
        )}
      </Section>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line px-3 py-2">
      <dt className="text-mist">{label}</dt>
      <dd className="font-mono text-paper">{value}</dd>
    </div>
  );
}
