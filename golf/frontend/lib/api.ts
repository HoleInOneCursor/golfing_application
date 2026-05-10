export const API_BASE_URL = "http://localhost:8000/api";

export interface Course {
  id: number;
  name: string;
  location: string;
  holes: number;
  par: number;
}

export interface CourseCreate {
  name: string;
  location: string;
  holes: number;
  par: number;
}

export interface Round {
  id: number;
  course_id: number;
  player_name: string;
  date: string;
  total_score: number;
}

export interface RoundCreate {
  course_id: number;
  player_name: string;
  date?: string | null;
}

export interface HoleScore {
  id: number;
  round_id: number;
  hole_number: number;
  strokes: number;
}

export interface HoleScoreCreate {
  hole_number: number;
  strokes: number;
}

export interface RoundDetail extends Round {
  hole_scores: HoleScore[];
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

type ApiRequestInit = Omit<RequestInit, "body"> & {
  body?: unknown;
};

async function parseResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

export async function apiFetch<T>(
  path: string,
  { body, headers, ...init }: ApiRequestInit = {},
): Promise<T> {
  const requestHeaders = new Headers(headers);

  if (body !== undefined && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: requestHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = await parseResponseBody(response);
    throw new ApiError(
      response.status,
      `API request failed with status ${response.status}`,
      errorBody,
    );
  }

  return (await parseResponseBody(response)) as T;
}

export function getCourses(): Promise<Course[]> {
  return apiFetch<Course[]>("/courses");
}

export function createCourse(course: CourseCreate): Promise<Course> {
  return apiFetch<Course>("/courses", {
    method: "POST",
    body: course,
  });
}

export function getRounds(): Promise<Round[]> {
  return apiFetch<Round[]>("/rounds");
}

export function createRound(round: RoundCreate): Promise<Round> {
  return apiFetch<Round>("/rounds", {
    method: "POST",
    body: round,
  });
}

export function getRound(roundId: number): Promise<RoundDetail> {
  return apiFetch<RoundDetail>(`/rounds/${roundId}`);
}

export function addHoleScore(
  roundId: number,
  score: HoleScoreCreate,
): Promise<RoundDetail> {
  return apiFetch<RoundDetail>(`/rounds/${roundId}/scores`, {
    method: "POST",
    body: score,
  });
}
