import { API_BASE_URL } from "@/lib/api";

export default function CoursesPage() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
          Courses
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Golf courses
        </h1>
        <p className="mt-3 max-w-2xl text-slate-600">
          Course data is available through the shared API helpers in{" "}
          <code className="rounded bg-white px-1.5 py-0.5 text-sm ring-1 ring-slate-200">
            lib/api.ts
          </code>
          .
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">Endpoint</h2>
        <p className="mt-2 font-mono text-sm text-slate-600">
          GET {API_BASE_URL}/courses
        </p>
      </div>
    </section>
  );
}
