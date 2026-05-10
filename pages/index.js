import Link from "next/link";

export default function Dashboard() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Dashboard</p>
        <h1>Golfing Application</h1>
        <p>
          The existing dashboard entry point stays available here. Open the golf score
          tracker to manage courses, rounds, and per-hole scores.
        </p>
        <Link className="button" href="/golf">
          Open golf tracker
        </Link>
      </section>
    </main>
  );
}
