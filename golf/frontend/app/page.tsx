import Link from "next/link";

export default function Home() {
  return (
    <section className="rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200 sm:p-12">
      <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
        Golf dashboard
      </p>
      <h1 className="mt-4 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
        Manage courses and record every round from one place.
      </h1>
      <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
        This frontend is ready to connect to the FastAPI backend at{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm">
          http://localhost:8000/api
        </code>
        .
      </p>
      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <Link
          href="/courses"
          className="rounded-full bg-emerald-700 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-emerald-800"
        >
          View courses
        </Link>
        <Link
          href="/rounds"
          className="rounded-full border border-slate-300 px-5 py-3 text-center text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100"
        >
          View rounds
        </Link>
      </div>
    </section>
  );
}
