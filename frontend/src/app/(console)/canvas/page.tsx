"use client";

import { useEffect, useState } from "react";

import { PhaseNotice, Section, Topology } from "@/components/Panels";
import { api } from "@/lib/api";
import { resolution } from "@/lib/format";
import type { DisplayReport } from "@/lib/types";

export default function CanvasPage() {
  const [report, setReport] = useState<DisplayReport | null>(null);

  useEffect(() => {
    api<DisplayReport>("/displays")
      .then(setReport)
      .catch(() => setReport(null));
  }, []);

  return (
    <div className="space-y-5">
      <PhaseNotice
        phase={3}
        title="Canvas editor"
        summary="Virtual canvases, layers, cropping, and saved region maps are not in this build. The rectangle below is the operating-system desktop reported by the display query."
        planned={["Virtual canvas size", "Per-output source rectangles", "Layers", "Saved layouts"]}
      />
      <Section title="Current OS desktop">
        {report ? (
          <>
            <Topology report={report} />
            <p className="mt-3 font-mono text-xs text-paper">
              {report.desktop
                ? `${resolution(report.desktop.width, report.desktop.height)} origin ${report.desktop.x},${report.desktop.y}`
                : "No desktop bounds were calculated."}
            </p>
          </>
        ) : (
          <p className="text-sm text-mist">Display bounds are not available.</p>
        )}
      </Section>
    </div>
  );
}
