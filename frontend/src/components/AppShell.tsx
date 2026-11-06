"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { api } from "@/lib/api";
import type { Health, User } from "@/lib/types";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/assistant", label: "AI Assistant", phase: 4 },
  { href: "/media", label: "Media Library" },
  { href: "/canvas", label: "Canvas Editor", phase: 3 },
  { href: "/outputs", label: "Display Outputs" },
  { href: "/led", label: "LED Mapping", phase: 5 },
  { href: "/controllers", label: "Controllers", phase: 5 },
  { href: "/playback", label: "Playback", phase: 2 },
  { href: "/devices", label: "Device Manager" },
  { href: "/profiles", label: "Event Profiles", phase: 3 },
  { href: "/monitoring", label: "System Monitoring" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api<User>("/auth/me")
      .then((next) => {
        if (!cancelled) setUser(next);
      })
      .catch(() => {
        if (!cancelled) router.replace("/login");
      })
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api<Health>("/health", {}, false)
        .then((next) => {
          if (!cancelled) setHealth(next);
        })
        .catch(() => {
          if (!cancelled) setHealth(null);
        });
    };
    load();
    const timer = window.setInterval(load, 10000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  async function signOut() {
    await api("/auth/logout", { method: "POST" });
    router.replace("/login");
  }

  if (!ready || !user) {
    return <div className="grid min-h-screen place-items-center text-sm text-mist">Checking session…</div>;
  }

  return (
    <div className="min-h-screen md:grid md:grid-cols-[232px_1fr]">
      <aside className="border-b border-line bg-panel md:min-h-screen md:border-b-0 md:border-r">
        <div className="px-4 py-4">
          <div className="text-[11px] uppercase tracking-[0.22em] text-amber">Qubit</div>
          <div className="mt-1 text-sm text-paper">AI Media Server</div>
          <div className="mt-1 font-mono text-[11px] text-mist">Phase {health?.phase ?? 1}</div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-2 pb-3 md:block md:space-y-1 md:px-2">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between gap-3 whitespace-nowrap px-3 py-2 text-sm ${
                  active ? "bg-amber/15 text-paper" : "text-mist hover:bg-white/5 hover:text-paper"
                }`}
              >
                <span>{item.label}</span>
                {item.phase ? <span className="font-mono text-[10px] text-amber">P{item.phase}</span> : null}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="min-w-0">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3 md:px-6">
          <div className="flex items-center gap-3 text-xs">
            <span className={`h-2 w-2 rounded-full ${health?.status === "ok" ? "bg-signal" : "bg-alarm"}`} />
            <span className="font-mono text-mist">
              API {health ? `${health.status} · ${health.version}` : "unreachable"}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="font-mono text-mist">
              {user.username} · {user.role}
            </span>
            <button type="button" onClick={() => void signOut()} className="text-paper hover:text-amber">
              Sign out
            </button>
          </div>
        </header>
        <main className="px-4 py-5 md:px-6">{children}</main>
      </div>
    </div>
  );
}
