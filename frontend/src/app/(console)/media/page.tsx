"use client";

import { DragEvent, useCallback, useEffect, useRef, useState } from "react";

import { Section } from "@/components/Panels";
import { ApiError, api, uploadMedia } from "@/lib/api";
import { bytes, rate, resolution, seconds, when } from "@/lib/format";
import type { Integrity, MediaAsset, TranscodeJob } from "@/lib/types";

export default function MediaPage() {
  const [items, setItems] = useState<MediaAsset[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const [jobs, setJobs] = useState<Record<string, TranscodeJob>>({});
  const [checks, setChecks] = useState<Record<string, Integrity>>({});
  const timers = useRef<number[]>([]);

  useEffect(() => {
    const active = timers.current;
    return () => {
      active.forEach((timer) => window.clearInterval(timer));
    };
  }, []);

  const load = useCallback(() => {
    api<MediaAsset[]>("/media")
      .then(setItems)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Media list failed"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function send(files: File[]) {
    setError("");
    setNotice("");
    for (const file of files) {
      setProgress(0);
      try {
        const asset = (await uploadMedia(file, setProgress)) as MediaAsset;
        setNotice(asset.duplicate ? `${file.name} matches an existing file and was not stored again.` : `${file.name} stored.`);
      } catch (caught) {
        setError(caught instanceof ApiError ? `${file.name}: ${caught.message}` : `${file.name}: upload failed`);
      }
    }
    setProgress(null);
    load();
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    void send(Array.from(event.dataTransfer.files));
  }

  async function transcode(id: string) {
    setError("");
    try {
      const job = await api<TranscodeJob>(`/media/${id}/transcode`, { method: "POST" });
      setJobs((current) => ({ ...current, [id]: job }));
      const timer = window.setInterval(() => {
        void api<TranscodeJob>(`/media/jobs/${job.id}`)
          .then((next) => {
            setJobs((current) => ({ ...current, [id]: next }));
            if (next.status === "succeeded" || next.status === "failed") {
              window.clearInterval(timer);
              load();
            }
          })
          .catch(() => window.clearInterval(timer));
      }, 1000);
      timers.current.push(timer);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Transcode failed");
    }
  }

  async function verify(id: string) {
    try {
      const result = await api<Integrity>(`/media/${id}/verify`);
      setChecks((current) => ({ ...current, [id]: result }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Integrity check failed");
    }
  }

  async function remove(asset: MediaAsset) {
    if (!window.confirm(`Remove ${asset.original_filename} from the library?`)) return;
    setError("");
    try {
      await api(`/media/${asset.id}`, { method: "DELETE" });
      load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Delete failed");
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl text-paper">Media library</h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-mist">
          MP4, MOV, MKV, WebM, JPG, PNG, and WebP. FFprobe records the original. A proxy is created only when you ask for one.
        </p>
      </div>
      {error ? <p className="border border-alarm/60 px-3 py-2 text-sm text-alarm">{error}</p> : null}
      {notice ? <p className="border border-signal/40 px-3 py-2 text-sm text-signal">{notice}</p> : null}
      <label
        onDragOver={(event) => event.preventDefault()}
        onDrop={onDrop}
        className="block cursor-pointer border border-dashed border-line bg-panel px-4 py-8 text-center"
      >
        <span className="text-sm text-paper">Drop files here or choose from disk</span>
        <input
          type="file"
          multiple
          accept=".mp4,.mov,.mkv,.webm,.jpg,.jpeg,.png,.webp,video/*,image/*"
          className="sr-only"
          onChange={(event) => {
            const files = Array.from(event.target.files ?? []);
            event.target.value = "";
            void send(files);
          }}
        />
        {progress != null ? (
          <div className="mx-auto mt-4 h-2 max-w-md bg-black/50">
            <div className="h-2 bg-amber" style={{ width: `${Math.round(progress * 100)}%` }} />
          </div>
        ) : null}
      </label>
      <Section title={`${items.length} asset${items.length === 1 ? "" : "s"}`}>
        <div className="space-y-3">
          {items.map((asset) => {
            const job = jobs[asset.id];
            const check = checks[asset.id];
            return (
              <article key={asset.id} className="grid gap-3 border border-line p-3 md:grid-cols-[160px_1fr]">
                <div className="flex h-28 items-center justify-center bg-black/40">
                  {asset.thumbnail_ready ? (
                    <img
                      src={`/backend/media/${asset.id}/thumbnail`}
                      alt=""
                      className="max-h-28 max-w-full object-contain"
                    />
                  ) : (
                    <span className="text-xs text-mist">No thumbnail</span>
                  )}
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h2 className="truncate text-sm text-paper">{asset.original_filename}</h2>
                      <p className="font-mono text-[11px] text-mist">{asset.sha256}</p>
                    </div>
                    <span className="font-mono text-[11px] uppercase text-amber">{asset.kind}</span>
                  </div>
                  <dl className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                    <Field label="Size" value={resolution(asset.width, asset.height)} />
                    <Field label="Rate" value={asset.kind === "video" ? rate(asset.frame_rate) : "—"} />
                    <Field label="Duration" value={seconds(asset.duration_seconds)} />
                    <Field label="Codec" value={asset.video_codec || "—"} />
                    <Field label="Audio" value={asset.audio_codec || "—"} />
                    <Field label="Bytes" value={bytes(asset.size_bytes)} />
                    <Field label="Stored" value={when(asset.created_at)} />
                    <Field label="Proxy" value={asset.has_proxy ? "ready" : "none"} />
                  </dl>
                  <p className="mt-2 text-xs leading-5 text-mist">{asset.validation_notes}</p>
                  {job ? (
                    <p className={`mt-2 font-mono text-xs ${job.status === "failed" ? "text-alarm" : "text-amber"}`}>
                      Transcode {job.status}
                      {job.error ? ` · ${job.error}` : ""}
                    </p>
                  ) : null}
                  {check ? (
                    <p className={`mt-2 text-xs ${check.ok ? "text-signal" : "text-alarm"}`}>{check.detail}</p>
                  ) : null}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button type="button" onClick={() => void verify(asset.id)} className="border border-line px-2 py-1 text-xs text-paper">
                      Check integrity
                    </button>
                    {asset.kind === "video" ? (
                      <button type="button" onClick={() => void transcode(asset.id)} className="border border-line px-2 py-1 text-xs text-paper">
                        Make H.264 proxy
                      </button>
                    ) : null}
                    <button type="button" onClick={() => void remove(asset)} className="border border-alarm/50 px-2 py-1 text-xs text-alarm">
                      Remove
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
          {!items.length ? <p className="text-sm text-mist">The library is empty.</p> : null}
        </div>
      </Section>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-mist">{label}</dt>
      <dd className="font-mono text-paper">{value}</dd>
    </div>
  );
}
