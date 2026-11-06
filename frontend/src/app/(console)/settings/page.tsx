"use client";

import { useEffect, useState } from "react";

import { Section } from "@/components/Panels";
import { ApiError, api } from "@/lib/api";
import { bytes, when } from "@/lib/format";
import type { AuditRow, ConfigReport } from "@/lib/types";

export default function SettingsPage() {
  const [config, setConfig] = useState<ConfigReport | null>(null);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api<ConfigReport>("/system/config"), api<AuditRow[]>("/system/audit")])
      .then(([nextConfig, nextAudit]) => {
        setConfig(nextConfig);
        setAudit(nextAudit);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Settings could not be loaded");
      });
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl text-paper">Settings</h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-mist">
          Non-secret runtime configuration and the recent audit trail. Secrets stay in the environment file.
        </p>
      </div>
      {error ? <p className="border border-alarm/60 px-3 py-2 text-sm text-alarm">{error}</p> : null}
      {config ? (
        <Section title="Runtime">
          <dl className="grid gap-2 text-sm md:grid-cols-2">
            <Item label="Application" value={`${config.app_name} ${config.version}`} />
            <Item label="Phase" value={String(config.phase)} />
            <Item label="Listen" value={`${config.host}:${config.port}`} />
            <Item label="Database" value={config.database} />
            <Item label="Media directory" value={config.media_dir} />
            <Item label="Upload limit" value={bytes(config.max_upload_bytes)} />
            <Item label="Session lifetime" value={`${config.token_ttl_hours} h`} />
            <Item label="Browser origins" value={config.cors_origins.join(", ") || "—"} />
          </dl>
          {config.warnings.length ? (
            <ul className="mt-3 space-y-2">
              {config.warnings.map((warning) => (
                <li key={warning} className="border border-amber/50 px-3 py-2 text-sm text-amber">
                  {warning}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-signal">No configuration warnings.</p>
          )}
        </Section>
      ) : null}
      <Section title="Audit">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-mist">
              <tr>
                <th className="px-2 py-2 font-medium">Time (UTC)</th>
                <th className="px-2 py-2 font-medium">Actor</th>
                <th className="px-2 py-2 font-medium">Action</th>
                <th className="px-2 py-2 font-medium">Result</th>
              </tr>
            </thead>
            <tbody>
              {audit.map((row) => (
                <tr key={row.id} className="border-t border-line">
                  <td className="px-2 py-2 font-mono">{when(row.created_at)}</td>
                  <td className="px-2 py-2">{row.actor}</td>
                  <td className="px-2 py-2 font-mono">{row.action}</td>
                  <td className={`px-2 py-2 ${row.success ? "text-signal" : "text-alarm"}`}>{row.success ? "ok" : "failed"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!audit.length ? <p className="text-sm text-mist">No audit rows yet.</p> : null}
        </div>
      </Section>
    </div>
  );
}

function Item({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line px-3 py-2">
      <dt className="text-mist">{label}</dt>
      <dd className="break-all font-mono text-paper">{value}</dd>
    </div>
  );
}
