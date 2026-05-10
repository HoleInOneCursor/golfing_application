import Link from "next/link";

import { CoursesList } from "./courses-list";

export default function CoursesPage() {
  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-5 rounded-3xl bg-gradient-to-br from-emerald-900 via-emerald-800 to-lime-700 p-8 text-white shadow-sm sm:flex-row sm:items-end sm:justify-between sm:p-10">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-200">
            Courses
          </p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight">
            Golf courses
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-emerald-50">
            Keep your favorite layouts organized with the essentials for every
            round: location, hole count, and total par.
          </p>
        </div>
        <Link
          href="/courses/new"
          className="inline-flex items-center justify-center rounded-full bg-white px-5 py-3 text-sm font-semibold text-emerald-900 shadow-sm transition hover:bg-lime-50"
        >
          Add course
        </Link>
      </div>

      <CoursesList />
    </section>
  );
}
