import { API_BASE_URL } from "@/lib/api";

export default function RoundsPage() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
          Rounds
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Played rounds
        </h1>
        <p className="mt-3 max-w-2xl text-slate-600">
          Round summaries and details can be loaded with the typed helpers in{" "}
          <code className="rounded bg-white px-1.5 py-0.5 text-sm ring-1 ring-slate-200">
            lib/api.ts
          </code>
          .
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">Endpoints</h2>
        <div className="mt-2 space-y-2 font-mono text-sm text-slate-600">
          <p>GET {API_BASE_URL}/rounds</p>
          <p>GET {API_BASE_URL}/rounds/&lt;round_id&gt;</p>
          <p>POST {API_BASE_URL}/rounds/&lt;round_id&gt;/scores</p>
        </div>
      </div>
    </section>
  );
}
