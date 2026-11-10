export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, init: RequestInit = {}, redirectOnAuth = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`/backend${path}`, {
    ...init,
    headers,
    credentials: "same-origin",
  });
  if (response.status === 401 && redirectOnAuth && typeof window !== "undefined") {
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login");
    }
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (body.detail != null) detail = JSON.stringify(body.detail);
    } catch {
      /* The body was not JSON. */
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function apiOrigin(): string {
  const protocol = window.location.protocol;
  const port = process.env.NEXT_PUBLIC_API_PORT || "8000";
  return `${protocol}//${window.location.hostname}:${port}`;
}

export type UploadProgress = {
  ratio: number;
  phase: "sending" | "inspecting";
};

export function uploadMedia(file: File, onProgress: (progress: UploadProgress) => void): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${apiOrigin()}/media`);
    xhr.withCredentials = true;
    xhr.timeout = 10 * 60 * 1000;
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress({ ratio: event.loaded / event.total, phase: "sending" });
      }
    };
    xhr.upload.onload = () => onProgress({ ratio: 1, phase: "inspecting" });
    xhr.onload = () => {
      let body: { detail?: string } = {};
      try {
        body = JSON.parse(xhr.responseText || "{}") as { detail?: string };
      } catch {
        body = {};
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body);
      else reject(new ApiError(xhr.status, body.detail || xhr.statusText || "Upload was rejected"));
    };
    xhr.onerror = () =>
      reject(new ApiError(0, "Upload failed before the server answered. Keep this page on 127.0.0.1 and leave the API window open."));
    xhr.ontimeout = () => reject(new ApiError(0, "The server took too long to inspect this file."));
    const data = new FormData();
    data.append("file", file);
    xhr.send(data);
  });
}

export function statusSocketUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const port = process.env.NEXT_PUBLIC_API_PORT || "8000";
  return `${protocol}//${window.location.hostname}:${port}/ws/status`;
}
