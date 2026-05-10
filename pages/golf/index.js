import { useEffect, useMemo, useState } from "react";

const apiBase = process.env.NEXT_PUBLIC_DASHBOARD_API_BASE || "http://localhost:8787";

function parsePars(input) {
  return input
    .split(",")
    .map((value) => Number.parseInt(value.trim(), 10))
    .filter((value) => Number.isInteger(value) && value > 0)
    .map((par, index) => ({ number: index + 1, par, handicap_rank: index + 1 }));
}

function parseTeeSets(input) {
  return input
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value) => {
      const [name, color, yards] = value.split(":").map((part) => part.trim());
      const totalYards = Number.parseInt(yards, 10);
      return {
        name,
        color: color || undefined,
        total_yards: Number.isInteger(totalYards) ? totalYards : undefined,
      };
    });
}

function scoreLabel(scoreToPar) {
  if (scoreToPar === 0) {
    return "E";
  }
  return scoreToPar > 0 ? `+${scoreToPar}` : `${scoreToPar}`;
}

function formatHandicap(value) {
  return value === null || value === undefined || value === "" ? "HCP stub" : `HCP ${value}`;
}

export default function GolfTracker() {
  const [players, setPlayers] = useState([]);
  const [courses, setCourses] = useState([]);
  const [rounds, setRounds] = useState([]);
  const [activity, setActivity] = useState([]);
  const [newPlayerName, setNewPlayerName] = useState("");
  const [newPlayerHandicap, setNewPlayerHandicap] = useState("");
  const [courseName, setCourseName] = useState("");
  const [coursePars, setCoursePars] = useState("4,4,3,5,4,4,3,5,4");
  const [courseTeeSets, setCourseTeeSets] = useState(
    "Championship:Black:6900, Member:White:6200, Forward:Gold:5200"
  );
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [selectedTeeSetId, setSelectedTeeSetId] = useState("");
  const [selectedPlayerId, setSelectedPlayerId] = useState("");
  const [playedOn, setPlayedOn] = useState("");
  const [scoreDrafts, setScoreDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const selectedCourse = useMemo(
    () => courses.find((course) => String(course.id) === String(selectedCourseId)),
    [courses, selectedCourseId]
  );

  const selectedPlayer = useMemo(
    () => players.find((player) => String(player.id) === String(selectedPlayerId)),
    [players, selectedPlayerId]
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

  function chooseCourse(courseId, nextCourses = courses) {
    setSelectedCourseId(String(courseId));
    const course = nextCourses.find((item) => String(item.id) === String(courseId));
    setSelectedTeeSetId(course && course.tee_sets[0] ? String(course.tee_sets[0].id) : "");
  }

  async function loadData(preferredSelection = {}) {
    setError("");
    setLoading(true);
    try {
      const [nextPlayers, nextCourses, nextRounds, nextActivity] = await Promise.all([
        request("/players"),
        request("/courses"),
        request("/rounds"),
        request("/activity"),
      ]);
      setPlayers(nextPlayers);
      setCourses(nextCourses);
      setRounds(nextRounds);
      setActivity(nextActivity);

      const nextPlayerId = preferredSelection.playerId || selectedPlayerId;
      const nextCourseId = preferredSelection.courseId || selectedCourseId;
      const nextTeeSetId = preferredSelection.teeSetId || selectedTeeSetId;

      if (nextPlayerId && nextPlayers.some((player) => String(player.id) === String(nextPlayerId))) {
        setSelectedPlayerId(String(nextPlayerId));
      } else if (nextPlayers.length > 0) {
        setSelectedPlayerId(String(nextPlayers[0].id));
      }

      const nextCourse = nextCourses.find((course) => String(course.id) === String(nextCourseId));
      if (nextCourse) {
        setSelectedCourseId(String(nextCourse.id));
        if (
          nextTeeSetId &&
          nextCourse.tee_sets.some((teeSet) => String(teeSet.id) === String(nextTeeSetId))
        ) {
          setSelectedTeeSetId(String(nextTeeSetId));
        } else {
          setSelectedTeeSetId(nextCourse.tee_sets[0] ? String(nextCourse.tee_sets[0].id) : "");
        }
      } else if (nextCourses.length > 0) {
        chooseCourse(nextCourses[0].id, nextCourses);
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

  async function createPlayer(event) {
    event.preventDefault();
    if (!newPlayerName.trim()) {
      setError("Enter a player name.");
      return;
    }

    const parsedHandicap = Number.parseFloat(newPlayerHandicap);
    setSaving(true);
    setError("");
    try {
      const player = await request("/players", {
        method: "POST",
        body: JSON.stringify({
          name: newPlayerName,
          handicap_index: Number.isFinite(parsedHandicap) ? parsedHandicap : null,
        }),
      });
      setNewPlayerName("");
      setNewPlayerHandicap("");
      setSelectedPlayerId(String(player.id));
      await loadData({ playerId: player.id });
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function createCourse(event) {
    event.preventDefault();
    const holes = parsePars(coursePars);
    const tee_sets = parseTeeSets(courseTeeSets);
    if (!courseName.trim() || holes.length === 0 || tee_sets.length === 0) {
      setError("Enter a course name, comma-separated pars, and at least one tee set.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      const course = await request("/courses", {
        method: "POST",
        body: JSON.stringify({ name: courseName, holes, tee_sets }),
      });
      setCourseName("");
      chooseCourse(course.id, [course, ...courses]);
      await loadData({ courseId: course.id, teeSetId: course.tee_sets[0]?.id });
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function createRound(event) {
    event.preventDefault();
    if (!selectedCourseId || !selectedPlayerId || !selectedTeeSetId) {
      setError("Select a player, course, and tee set.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await request("/rounds", {
        method: "POST",
        body: JSON.stringify({
          course_id: Number.parseInt(selectedCourseId, 10),
          player_id: Number.parseInt(selectedPlayerId, 10),
          tee_set_id: Number.parseInt(selectedTeeSetId, 10),
          played_on: playedOn || undefined,
          scoring_mode: "stableford",
        }),
      });
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
        <p className="eyebrow">Golf demo flow</p>
        <h1>Players, tee sets, Stableford rounds, and activity</h1>
        <p>
          Build a larger demo journey from setup to scoring. API base: <code>{apiBase}</code>
        </p>
        <nav className="golf-nav" aria-label="Golf sections">
          <a href="#setup">Setup</a>
          <a href="#start-round">Start round</a>
          <a href="#scorecards">Scorecards</a>
          <a href="#activity">Activity</a>
        </nav>
      </section>

      {error ? <div className="notice error">{error}</div> : null}
      {loading ? <div className="notice">Loading golf data...</div> : null}

      <section className="stats-row" aria-label="Golf demo totals">
        <div>
          <strong>{players.length}</strong>
          <span>players</span>
        </div>
        <div>
          <strong>{courses.length}</strong>
          <span>courses</span>
        </div>
        <div>
          <strong>{rounds.length}</strong>
          <span>rounds</span>
        </div>
        <div>
          <strong>{activity.length}</strong>
          <span>feed items</span>
        </div>
      </section>

      <div id="setup" className="grid two">
        <section className="card">
          <p className="eyebrow">Players</p>
          <h2>Add player + handicap stub</h2>
          <form onSubmit={createPlayer} className="stack">
            <label>
              Player name
              <input
                value={newPlayerName}
                onChange={(event) => setNewPlayerName(event.target.value)}
                placeholder="Ada Lovelace"
              />
            </label>
            <label>
              Handicap index
              <input
                inputMode="decimal"
                value={newPlayerHandicap}
                onChange={(event) => setNewPlayerHandicap(event.target.value)}
                placeholder="14.2 (optional)"
              />
            </label>
            <button className="button" disabled={saving}>
              Save player
            </button>
          </form>
          <div className="pill-list">
            {players.map((player) => (
              <span key={player.id} className="pill">
                {player.name} / {formatHandicap(player.handicap_index)}
              </span>
            ))}
          </div>
        </section>

        <section className="card">
          <p className="eyebrow">Courses</p>
          <h2>Add course + tee sets</h2>
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
            <label>
              Tee sets
              <input
                value={courseTeeSets}
                onChange={(event) => setCourseTeeSets(event.target.value)}
                placeholder="Member:White:6200, Forward:Gold:5200"
              />
            </label>
            <button className="button" disabled={saving}>
              Save course
            </button>
          </form>
        </section>
      </div>

      <section id="start-round" className="card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Round setup</p>
            <h2>Start a Stableford round</h2>
          </div>
          <button className="button secondary" onClick={loadData} disabled={loading}>
            Refresh
          </button>
        </div>
        <form onSubmit={createRound} className="grid three">
          <label>
            Player
            <select
              value={selectedPlayerId}
              onChange={(event) => setSelectedPlayerId(event.target.value)}
            >
              <option value="">Choose a player</option>
              {players.map((player) => (
                <option key={player.id} value={player.id}>
                  {player.name} ({formatHandicap(player.handicap_index)})
                </option>
              ))}
            </select>
          </label>
          <label>
            Course
            <select value={selectedCourseId} onChange={(event) => chooseCourse(event.target.value)}>
              <option value="">Choose a course</option>
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.name} ({course.holes.length} holes, par {course.total_par})
                </option>
              ))}
            </select>
          </label>
          <label>
            Tee set
            <select
              value={selectedTeeSetId}
              onChange={(event) => setSelectedTeeSetId(event.target.value)}
            >
              <option value="">Choose tees</option>
              {(selectedCourse?.tee_sets || []).map((teeSet) => (
                <option key={teeSet.id} value={teeSet.id}>
                  {teeSet.name}
                  {teeSet.color ? ` / ${teeSet.color}` : ""}
                  {teeSet.total_yards ? ` / ${teeSet.total_yards} yds` : ""}
                </option>
              ))}
            </select>
          </label>
          <label>
            Played on
            <input
              type="date"
              value={playedOn}
              onChange={(event) => setPlayedOn(event.target.value)}
            />
          </label>
          <div className="round-preview">
            <strong>{selectedPlayer ? selectedPlayer.name : "No player selected"}</strong>
            <span>{selectedCourse ? selectedCourse.name : "No course selected"}</span>
            <span>Stableford: 2 par, 3 birdie, 4 eagle</span>
          </div>
          <button className="button" disabled={saving || !selectedCourse || !selectedPlayer}>
            Create round
          </button>
        </form>
      </section>

      <section className="card">
        <p className="eyebrow">Course library</p>
        <h2>Saved courses and tee sets</h2>
        {courses.length === 0 ? (
          <p>No courses yet. Add one above to start tracking rounds.</p>
        ) : (
          <div className="course-list">
            {courses.map((course) => (
              <article key={course.id} className="course">
                <div className="section-heading">
                  <div>
                    <h3>{course.name}</h3>
                    <p>
                      {course.holes.length} holes / par {course.total_par}
                    </p>
                  </div>
                  <span className="pill">{course.tee_sets.length} tee sets</span>
                </div>
                <div className="tee-list">
                  {course.tee_sets.map((teeSet) => (
                    <span key={teeSet.id}>
                      {teeSet.name}
                      {teeSet.color ? ` / ${teeSet.color}` : ""}
                      {teeSet.total_yards ? ` / ${teeSet.total_yards} yds` : ""}
                    </span>
                  ))}
                </div>
                <div className="holes">
                  {course.holes.map((hole) => (
                    <span key={hole.number}>
                      {hole.number}: par {hole.par} / HCP {hole.handicap_rank}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section id="scorecards" className="card">
        <p className="eyebrow">Rounds</p>
        <h2>Round summary and scorecards</h2>
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
                      {round.course_name} / {round.tee_set?.name || "No tees"} / {round.played_on}
                    </p>
                    <p>
                      {formatHandicap(round.player?.handicap_index)} / {round.summary.handicap}
                    </p>
                  </div>
                  <div className="score-total">
                    <strong>{round.total_strokes || "-"}</strong>
                    <span>{round.completed_holes}/{round.scores.length} holes</span>
                    <span>{scoreLabel(round.score_to_par)}</span>
                    <span>{round.stableford_points} Stableford pts</span>
                  </div>
                </div>

                <div className="summary-strip">
                  <span>{round.summary.scorecard}</span>
                  <span>{round.summary.stableford}</span>
                  <span>{round.summary.completion}</span>
                </div>

                <div className="score-grid">
                  {round.scores.map((score) => {
                    const draftKey = `${round.id}-${score.hole_number}`;
                    const draftValue = scoreDrafts[draftKey] ?? score.strokes ?? "";
                    return (
                      <div key={score.hole_number} className="score-cell">
                        <span>
                          Hole {score.hole_number} / par {score.par} / HCP {score.handicap_rank}
                        </span>
                        <strong>
                          {score.stableford_points === null
                            ? "No score"
                            : `${score.stableford_points} pts (${scoreLabel(score.score_to_par)})`}
                        </strong>
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

      <section id="activity" className="card">
        <p className="eyebrow">Activity API</p>
        <h2>Recent activity feed</h2>
        {activity.length === 0 ? (
          <p>No activity yet. Add a player, course, round, or score to populate the feed.</p>
        ) : (
          <ol className="activity-feed">
            {activity.map((item) => (
              <li key={item.id}>
                <strong>{item.summary}</strong>
                <span>
                  {item.event_type} / {item.created_at}
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}
