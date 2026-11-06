import { PhaseNotice } from "@/components/Panels";

export default function ControllersPage() {
  return (
    <PhaseNotice
      phase={5}
      title="Controllers"
      summary="No Colorlight or NovaStar protocol is implemented. This server does not connect to a processor and does not change receiving-card settings."
      planned={[
        "Manual profiles for Colorlight X20, X16, X100, and A200",
        "Manual profiles for NovaStar MCTRL4K, H-series, and TB-series",
        "A clear split between profile data and settings that still have to be applied in the manufacturer tool",
      ]}
    />
  );
}
