"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError, createCourse } from "@/lib/api";
import type { CourseCreate } from "@/lib/api";

type FormValues = {
  name: string;
  location: string;
  holes: string;
  par: string;
};

type FormErrors = Partial<Record<keyof FormValues, string>> & {
  form?: string;
};

const initialValues: FormValues = {
  name: "",
  location: "",
  holes: "18",
  par: "72",
};

function getApiErrorMessage(error: unknown): string {
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

  return "Course could not be created.";
}

function validateCourse(values: FormValues): {
  errors: FormErrors;
  course?: CourseCreate;
} {
  const errors: FormErrors = {};
  const name = values.name.trim();
  const location = values.location.trim();
  const holes = Number(values.holes);
  const par = Number(values.par);

  if (!name) {
    errors.name = "Enter a course name.";
  } else if (name.length > 120) {
    errors.name = "Course name must be 120 characters or fewer.";
  }

  if (!location) {
    errors.location = "Enter a location.";
  } else if (location.length > 120) {
    errors.location = "Location must be 120 characters or fewer.";
  }

  if (!Number.isInteger(holes)) {
    errors.holes = "Enter a whole number of holes.";
  } else if (holes < 1 || holes > 18) {
    errors.holes = "Holes must be between 1 and 18.";
  }

  if (!Number.isInteger(par)) {
    errors.par = "Enter a whole-number par.";
  } else if (par < 1 || par > 100) {
    errors.par = "Par must be between 1 and 100.";
  }

  if (Object.keys(errors).length > 0) {
    return { errors };
  }

  return {
    errors,
    course: {
      name,
      location,
      holes,
      par,
    },
  };
}

export function CourseForm() {
  const router = useRouter();
  const [values, setValues] = useState<FormValues>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateValue(field: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined, form: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const result = validateCourse(values);
    setErrors(result.errors);

    if (!result.course) {
      return;
    }

    setIsSubmitting(true);

    try {
      await createCourse(result.course);
      router.push("/courses");
      router.refresh();
    } catch (error) {
      setErrors({ form: getApiErrorMessage(error) });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200"
      noValidate
    >
      <div className="border-b border-slate-200 bg-emerald-50 px-6 py-5 sm:px-8">
        <h2 className="text-lg font-semibold text-emerald-950">
          Course details
        </h2>
        <p className="mt-1 text-sm text-emerald-900/70">
          All fields are required.
        </p>
      </div>

      <div className="grid gap-6 px-6 py-8 sm:grid-cols-2 sm:px-8">
        {errors.form ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-900 sm:col-span-2">
            {errors.form}
          </div>
        ) : null}

        <div className="sm:col-span-2">
          <label
            htmlFor="name"
            className="text-sm font-semibold text-slate-900"
          >
            Course name
          </label>
          <input
            id="name"
            name="name"
            type="text"
            value={values.name}
            onChange={(event) => updateValue("name", event.target.value)}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? "name-error" : undefined}
            className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
            placeholder="Pebble Beach Golf Links"
            maxLength={120}
          />
          {errors.name ? (
            <p id="name-error" className="mt-2 text-sm text-red-700">
              {errors.name}
            </p>
          ) : null}
        </div>

        <div className="sm:col-span-2">
          <label
            htmlFor="location"
            className="text-sm font-semibold text-slate-900"
          >
            Location
          </label>
          <input
            id="location"
            name="location"
            type="text"
            value={values.location}
            onChange={(event) => updateValue("location", event.target.value)}
            aria-invalid={Boolean(errors.location)}
            aria-describedby={errors.location ? "location-error" : undefined}
            className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
            placeholder="Pebble Beach, CA"
            maxLength={120}
          />
          {errors.location ? (
            <p id="location-error" className="mt-2 text-sm text-red-700">
              {errors.location}
            </p>
          ) : null}
        </div>

        <div>
          <label
            htmlFor="holes"
            className="text-sm font-semibold text-slate-900"
          >
            Holes
          </label>
          <input
            id="holes"
            name="holes"
            type="number"
            inputMode="numeric"
            min={1}
            max={18}
            step={1}
            value={values.holes}
            onChange={(event) => updateValue("holes", event.target.value)}
            aria-invalid={Boolean(errors.holes)}
            aria-describedby={errors.holes ? "holes-error" : undefined}
            className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
          />
          {errors.holes ? (
            <p id="holes-error" className="mt-2 text-sm text-red-700">
              {errors.holes}
            </p>
          ) : null}
        </div>

        <div>
          <label
            htmlFor="par"
            className="text-sm font-semibold text-slate-900"
          >
            Par
          </label>
          <input
            id="par"
            name="par"
            type="number"
            inputMode="numeric"
            min={1}
            max={100}
            step={1}
            value={values.par}
            onChange={(event) => updateValue("par", event.target.value)}
            aria-invalid={Boolean(errors.par)}
            aria-describedby={errors.par ? "par-error" : undefined}
            className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
          />
          {errors.par ? (
            <p id="par-error" className="mt-2 text-sm text-red-700">
              {errors.par}
            </p>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col-reverse gap-3 border-t border-slate-200 bg-slate-50 px-6 py-5 sm:flex-row sm:justify-end sm:px-8">
        <Link
          href="/courses"
          className="inline-flex items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-white"
        >
          Cancel
        </Link>
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex items-center justify-center rounded-full bg-emerald-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isSubmitting ? "Creating..." : "Create course"}
        </button>
      </div>
    </form>
  );
}
