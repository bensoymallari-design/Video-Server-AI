"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { User } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    api<User>("/auth/me", {}, false)
      .then(() => router.replace("/"))
      .catch(() => undefined);
  }, [router]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await api<User>("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }, false);
      router.replace("/");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Sign-in failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4">
      <form onSubmit={onSubmit} className="w-full max-w-md border border-line bg-panel p-6">
        <div className="text-[11px] uppercase tracking-[0.22em] text-amber">Qubit</div>
        <h1 className="mt-2 text-2xl text-paper">Sign in</h1>
        <p className="mt-2 text-sm leading-6 text-mist">
          Local administrator session. The API listens on loopback unless its configuration says otherwise.
        </p>
        <label className="mt-5 block text-xs uppercase tracking-[0.14em] text-mist" htmlFor="username">
          Username
        </label>
        <input
          id="username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          className="mt-2 w-full border border-line bg-ink px-3 py-2 text-sm text-paper"
        />
        <label className="mt-4 block text-xs uppercase tracking-[0.14em] text-mist" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="mt-2 w-full border border-line bg-ink px-3 py-2 text-sm text-paper"
        />
        {error ? <p className="mt-4 text-sm text-alarm">{error}</p> : null}
        <button
          type="submit"
          disabled={pending}
          className="mt-5 w-full bg-amber px-3 py-2 text-sm font-semibold text-ink disabled:opacity-60"
        >
          {pending ? "Checking…" : "Enter control surface"}
        </button>
      </form>
    </main>
  );
}
