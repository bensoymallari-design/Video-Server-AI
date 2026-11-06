import { PhaseNotice } from "@/components/Panels";

export default function LedPage() {
  return (
    <PhaseNotice
      phase={5}
      title="LED mapping"
      summary="Cabinet and receiving-card maps are not stored or drawn yet. Virtual output regions and physical cabinet maps will stay separate when that editor exists."
      planned={["Manual cabinet placement", "Sending-port view", "Import and export", "No firmware writes"]}
    />
  );
}
