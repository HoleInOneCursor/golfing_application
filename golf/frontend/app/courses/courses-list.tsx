"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, getCourses } from "@/lib/api";
import type { Course } from "@/lib/api";

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const detail =
      typeof error.body === "object" && error.body !== null && "detail" in error.body
        ? (error.body as { detail?: unknown }).detail
        : error.body;

    if (typeof detail === "string") {
      return detail;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load courses.";
}

export function CoursesList() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function reloadCourses() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      setCourses(await getCourses());
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isActive = true;

    async function loadInitialCourses() {
      try {
        const nextCourses = await getCourses();

        if (!isActive) {
          return;
        }

        setCourses(nextCourses);
        setErrorMessage(null);
      } catch (error) {
        if (isActive) {
          setErrorMessage(getErrorMessage(error));
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadInitialCourses();

    return () => {
      isActive = false;
    };
  }, []);

  if (isLoading) {
    return (
      <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <p className="text-sm font-medium text-slate-500">Loading courses...</p>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((item) => (
            <div
              key={item}
              className="h-32 animate-pulse rounded-2xl bg-slate-100"
            />
          ))}
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="rounded-3xl border border-red-200 bg-red-50 p-6 text-red-900">
        <h2 className="text-lg font-semibold">Courses could not be loaded</h2>
        <p className="mt-2 text-sm">{errorMessage}</p>
        <button
          type="button"
          onClick={() => void reloadCourses()}
          className="mt-5 rounded-full bg-red-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-800"
        >
          Try again
        </button>
      </div>
    );
  }

  if (courses.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-emerald-300 bg-emerald-50 p-10 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Empty scorecard
        </p>
        <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-950">
          Add your first course
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-slate-600">
          Save the course name, location, number of holes, and total par before
          recording rounds.
        </p>
        <Link
          href="/courses/new"
          className="mt-6 inline-flex rounded-full bg-emerald-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800"
        >
          Create course
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 lg:hidden">
        {courses.map((course) => (
          <article
            key={course.id}
            className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold tracking-tight text-slate-950">
                  {course.name}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {course.location}
                </p>
              </div>
              <span className="rounded-full bg-lime-100 px-3 py-1 text-xs font-semibold text-lime-800">
                Par {course.par}
              </span>
            </div>
            <dl className="mt-6 grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Holes
                </dt>
                <dd className="mt-1 text-2xl font-bold text-slate-950">
                  {course.holes}
                </dd>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Par
                </dt>
                <dd className="mt-1 text-2xl font-bold text-slate-950">
                  {course.par}
                </dd>
              </div>
            </dl>
          </article>
        ))}
      </div>

      <div className="hidden overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200 lg:block">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-emerald-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-emerald-900"
              >
                Course
              </th>
              <th
                scope="col"
                className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-emerald-900"
              >
                Location
              </th>
              <th
                scope="col"
                className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-[0.16em] text-emerald-900"
              >
                Holes
              </th>
              <th
                scope="col"
                className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-[0.16em] text-emerald-900"
              >
                Par
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {courses.map((course) => (
              <tr key={course.id} className="transition hover:bg-lime-50/60">
                <td className="whitespace-nowrap px-6 py-5 text-sm font-semibold text-slate-950">
                  {course.name}
                </td>
                <td className="px-6 py-5 text-sm text-slate-600">
                  {course.location}
                </td>
                <td className="px-6 py-5 text-right text-sm font-medium text-slate-900">
                  {course.holes}
                </td>
                <td className="px-6 py-5 text-right text-sm font-medium text-slate-900">
                  {course.par}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
