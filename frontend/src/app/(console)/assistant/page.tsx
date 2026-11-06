import { PhaseNotice } from "@/components/Panels";

const EXAMPLE = `{
  "intent": "configure_canvas",
  "canvas": { "width": 7680, "height": 1080 },
  "outputs": [
    {
      "display_id": "DISPLAY_1",
      "source_region": { "x": 0, "y": 0, "width": 3840, "height": 1080 }
    },
    {
      "display_id": "DISPLAY_2",
      "source_region": { "x": 3840, "y": 0, "width": 3840, "height": 1080 }
    }
  ]
}`;

export default function AssistantPage() {
  return (
    <div className="space-y-5">
      <PhaseNotice
        phase={4}
        title="AI assistant"
        summary="Instruction entry is disabled. This server has no language-model client and no tool executor, so a prompt cannot change displays, media, or playback."
        planned={[
          "Ollama or another configured model",
          "A fixed tool registry",
          "Deterministic layout math outside the model",
          "A preview and an approval step before disruptive changes",
        ]}
      />
      <section className="mx-auto max-w-3xl border border-line bg-panel">
        <header className="border-b border-line px-5 py-3 text-[11px] uppercase tracking-[0.16em] text-mist">
          Contract example for Phase 4
        </header>
        <p className="px-5 pt-4 text-sm leading-6 text-mist">
          The JSON below is a written example of a future validated plan. A model did not produce it, and nothing in this build will execute it.
        </p>
        <pre className="overflow-x-auto px-5 py-4 font-mono text-xs leading-5 text-paper">{EXAMPLE}</pre>
        <label className="block border-t border-line px-5 py-4 text-sm text-mist" htmlFor="prompt">
          Instruction
          <textarea
            id="prompt"
            disabled
            rows={4}
            placeholder="Unavailable until Phase 4"
            className="mt-2 w-full cursor-not-allowed border border-line bg-ink px-3 py-2 text-mist"
          />
        </label>
      </section>
    </div>
  );
}
