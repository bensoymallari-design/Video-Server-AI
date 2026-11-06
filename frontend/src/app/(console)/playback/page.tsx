import { PhaseNotice } from "@/components/Panels";

export default function PlaybackPage() {
  return (
    <PhaseNotice
      phase={2}
      title="Playback"
      summary="There is no playback process in this build. No window is opened, no test pattern is generated, and transport controls are not wired to a renderer."
      planned={[
        "A playback process separate from the API",
        "One fullscreen output on a selected display",
        "Start, stop, and pause",
        "Scaling, position, and a test pattern",
        "Output status, including dropped frames when the renderer can count them",
      ]}
    />
  );
}
