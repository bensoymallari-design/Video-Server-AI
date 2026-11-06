import { PhaseNotice } from "@/components/Panels";

export default function ProfilesPage() {
  return (
    <PhaseNotice
      phase={3}
      title="Event profiles"
      summary="Profiles are not saved. There is no load, duplicate, import, export, or restore action in this build."
      planned={[
        "Versioned profile documents",
        "Canvas, outputs, media, and startup behavior",
        "Validation before a profile is applied",
        "A previous-configuration restore once display changes exist",
      ]}
    />
  );
}
