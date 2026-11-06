export type Role = "admin" | "operator" | "viewer";

export interface User {
  username: string;
  role: Role | string;
}

export interface Health {
  status: string;
  version: string;
  phase: number;
  time: string;
  checks: Record<string, string>;
}

export interface VideoMode {
  width: number;
  height: number;
  refresh_hz: number;
  current: boolean;
  preferred: boolean;
}

export interface DisplayOutput {
  id: string;
  name: string;
  connector: string;
  connected: boolean;
  primary: boolean;
  width: number | null;
  height: number | null;
  position_x: number | null;
  position_y: number | null;
  refresh_hz: number | null;
  rotation: string;
  physical_width_mm: number | null;
  physical_height_mm: number | null;
  modes: VideoMode[];
}

export interface DesktopBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DisplayReport {
  platform: string;
  adapter: string;
  query_succeeded: boolean;
  virtual_output_suspected: boolean;
  captured_at: string;
  note: string;
  error: string | null;
  limitations: string[];
  desktop: DesktopBounds | null;
  outputs: DisplayOutput[];
}

export interface GpuReport {
  available: boolean;
  adapters: { name: string; source: string }[];
  note: string;
}

export interface HostReport {
  hostname: string;
  platform: string;
  platform_version: string;
  python_version: string;
  cpu_count: number | null;
  memory_total_bytes: number;
  memory_available_bytes: number;
  gpu: GpuReport;
  localhost_only: boolean;
  app_version: string;
  phase: number;
}

export interface ConfigReport {
  app_name: string;
  version: string;
  phase: number;
  host: string;
  port: number;
  localhost_only: boolean;
  database: string;
  media_dir: string;
  max_upload_bytes: number;
  token_ttl_hours: number;
  cors_origins: string[];
  warnings: string[];
}

export interface MediaAsset {
  id: string;
  original_filename: string;
  sha256: string;
  size_bytes: number;
  extension: string;
  kind: string;
  container: string | null;
  video_codec: string | null;
  audio_codec: string | null;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  frame_rate: number | null;
  pixel_format: string | null;
  rotation_degrees: number | null;
  thumbnail_ready: boolean;
  has_proxy: boolean;
  validation_status: string;
  validation_notes: string;
  created_at: string;
  duplicate: boolean;
}

export interface TranscodeJob {
  id: string;
  media_id: string;
  status: string;
  error: string;
  created_at: string;
  finished_at: string | null;
}

export interface Integrity {
  id: string;
  ok: boolean;
  expected_sha256: string;
  actual_sha256: string | null;
  detail: string;
}

export interface AuditRow {
  id: string;
  created_at: string;
  actor: string;
  action: string;
  success: boolean;
  detail: string;
}

export interface Capability {
  id: string;
  name: string;
  phase: number;
  status: "available" | "unavailable" | string;
  summary: string;
}

export interface CapabilityReport {
  current_phase: number;
  features: Capability[];
}

export interface StatusSample {
  type: string;
  time: string;
  uptime_seconds: number;
  cpu_percent: number;
  memory_percent: number;
  memory_used_bytes: number;
  memory_total_bytes: number;
  disk_percent: number;
  disk_used_bytes: number;
  disk_total_bytes: number;
  displays_connected: number | null;
}
