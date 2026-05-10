import { useEffect, useMemo, useState } from "react";

const apiBase = process.env.NEXT_PUBLIC_DASHBOARD_API_BASE || "http://localhost:8787";

function parsePars(input) {
  return input
    .split(",")
    .map((value) => Number.parseInt(value.trim(), 10))
    .filter((value) => Number.isInteger(value) && value > 0)
    .map((par, index) => ({ number: index + 1, par }));
}

function scoreLabel(scoreToPar) {
  if (scoreToPar === 0) {
    return "E";
  }
  return scoreToPar > 0 ? `+${scoreToPar}` : `${scoreToPar}`;
}

export default function GolfTracker() {
  const [courses, setCourses] = useState([]);
  const [rounds, setRounds] = useState([]);
  const [courseName, setCourseName] = useState("");
  const [coursePars, setCoursePars] = useState("4,4,3,5,4,4,3,5,4");
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [playedOn, setPlayedOn] = useState("");
  const [scoreDrafts, setScoreDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const selectedCourse = useMemo(
    () => courses.find((course) => String(course.id) === String(selectedCourseId)),
    [courses, selectedCourseId]
  );

  async function request(path, options) {
    const response = await fetch(`${apiBase}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options && options.headers ? options.headers : {}),
      },
      ...options,
    });

    if (!response.ok) {
      let message = `Request failed with ${response.status}`;
      try {
        const payload = await response.json();
        message = payload.detail || message;
      } catch {
        // Keep the status-based message when the API does not return JSON.
      }
      throw new Error(Array.isArray(message) ? message.map((item) => item.msg).join(", ") : message);
    }

    return response.json();
  }

  async function loadData() {
    setError("");
    setLoading(true);
    try {
      const [nextCourses, nextRounds] = await Promise.all([
        request("/courses"),
        request("/rounds"),
      ]);
      setCourses(nextCourses);
      setRounds(nextRounds);
      if (!selectedCourseId && nextCourses.length > 0) {
        setSelectedCourseId(String(nextCourses[0].id));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // The first load should run once; follow-up form changes should not refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createCourse(event) {
    event.preventDefault();
    const holes = parsePars(coursePars);
    if (!courseName.trim() || holes.length === 0) {
      setError("Enter a course name and comma-separated pars.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      const course = await request("/courses", {
        method: "POST",
        body: JSON.stringify({ name: courseName, holes }),
      });
      setCourseName("");
      setSelectedCourseId(String(course.id));
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function createRound(event) {
    event.preventDefault();
    if (!selectedCourseId || !playerName.trim()) {
      setError("Select a course and enter a player name.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await request("/rounds", {
        method: "POST",
        body: JSON.stringify({
          course_id: Number.parseInt(selectedCourseId, 10),
          player_name: playerName,
          played_on: playedOn || undefined,
        }),
      });
      setPlayerName("");
      setPlayedOn("");
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function saveScore(roundId, holeNumber) {
    const draftKey = `${roundId}-${holeNumber}`;
    const strokes = Number.parseInt(scoreDrafts[draftKey], 10);
    if (!Number.isInteger(strokes) || strokes < 1) {
      setError("Enter strokes as a positive number.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await request(`/rounds/${roundId}/scores/${holeNumber}`, {
        method: "PUT",
        body: JSON.stringify({ strokes }),
      });
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Golf score tracker</p>
        <h1>Courses, rounds, and per-hole scores</h1>
        <p>
          API base: <code>{apiBase}</code>
        </p>
      </section>

      {error ? <div className="notice error">{error}</div> : null}
      {loading ? <div className="notice">Loading golf data...</div> : null}

      <div className="grid two">
        <section className="card">
          <h2>Add course</h2>
          <form onSubmit={createCourse} className="stack">
            <label>
              Course name
              <input
                value={courseName}
                onChange={(event) => setCourseName(event.target.value)}
                placeholder="Municipal Front 9"
              />
            </label>
            <label>
              Hole pars
              <input
                value={coursePars}
                onChange={(event) => setCoursePars(event.target.value)}
                placeholder="4,4,3,5,4,4,3,5,4"
              />
            </label>
            <button className="button" disabled={saving}>
              Save course
            </button>
          </form>
        </section>

        <section className="card">
          <h2>Start round</h2>
          <form onSubmit={createRound} className="stack">
            <label>
              Course
              <select
                value={selectedCourseId}
                onChange={(event) => setSelectedCourseId(event.target.value)}
              >
                <option value="">Choose a course</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name} ({course.holes.length} holes, par {course.total_par})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Player
              <input
                value={playerName}
                onChange={(event) => setPlayerName(event.target.value)}
                placeholder="Ada Lovelace"
              />
            </label>
            <label>
              Played on
              <input
                type="date"
                value={playedOn}
                onChange={(event) => setPlayedOn(event.target.value)}
              />
            </label>
            <button className="button" disabled={saving || !selectedCourse}>
              Create round
            </button>
          </form>
        </section>
      </div>

      <section className="card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Courses</p>
            <h2>Saved courses</h2>
          </div>
          <button className="button secondary" onClick={loadData} disabled={loading}>
            Refresh
          </button>
        </div>
        {courses.length === 0 ? (
          <p>No courses yet. Add one above to start tracking rounds.</p>
        ) : (
          <div className="course-list">
            {courses.map((course) => (
              <article key={course.id} className="course">
                <h3>{course.name}</h3>
                <p>
                  {course.holes.length} holes / par {course.total_par}
                </p>
                <div className="holes">
                  {course.holes.map((hole) => (
                    <span key={hole.number}>
                      {hole.number}: par {hole.par}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <p className="eyebrow">Rounds</p>
        <h2>Scorecards</h2>
        {rounds.length === 0 ? (
          <p>No rounds yet. Create a round to enter per-hole scores.</p>
        ) : (
          <div className="round-list">
            {rounds.map((round) => (
              <article key={round.id} className="round">
                <div className="round-summary">
                  <div>
                    <h3>{round.player_name}</h3>
                    <p>
                      {round.course_name} · {round.played_on}
                    </p>
                  </div>
                  <div className="score-total">
                    <strong>{round.total_strokes || "-"}</strong>
                    <span>{round.completed_holes}/{round.scores.length} holes</span>
                    <span>{scoreLabel(round.score_to_par)}</span>
                  </div>
                </div>

                <div className="score-grid">
                  {round.scores.map((score) => {
                    const draftKey = `${round.id}-${score.hole_number}`;
                    const draftValue = scoreDrafts[draftKey] ?? score.strokes ?? "";
                    return (
                      <div key={score.hole_number} className="score-cell">
                        <span>
                          Hole {score.hole_number} · par {score.par}
                        </span>
                        <div>
                          <input
                            inputMode="numeric"
                            value={draftValue}
                            onChange={(event) =>
                              setScoreDrafts((current) => ({
                                ...current,
                                [draftKey]: event.target.value,
                              }))
                            }
                            placeholder="-"
                          />
                          <button
                            className="button compact"
                            onClick={() => saveScore(round.id, score.hole_number)}
                            disabled={saving}
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
