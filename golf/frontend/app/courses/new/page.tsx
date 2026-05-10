import Link from "next/link";

import { CourseForm } from "./course-form";

export default function NewCoursePage() {
  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
            New course
          </p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-950">
            Add a course
          </h1>
          <p className="mt-4 max-w-2xl text-slate-600">
            Capture the course details you need before tracking rounds and
            scores.
          </p>
        </div>
        <Link
          href="/courses"
          className="inline-flex items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-emerald-700 hover:bg-emerald-50 hover:text-emerald-800"
        >
          Back to courses
        </Link>
      </div>

      <CourseForm />
    </section>
  );
}
