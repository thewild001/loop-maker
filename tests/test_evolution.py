import pytest

from loop_maker.evolution import EvolutionStore


def test_observation_round_trip_and_filters(tmp_path):
    database = tmp_path / "evolution.sqlite3"
    store = EvolutionStore(database)
    saved = store.add_observation(
        description="The agent missed the repository architecture.",
        domain="software-engineering",
        category="user-correction",
        evidence=["The user requested an architecture scan first."],
        context={"project": "sample", "skill": "architecture"},
        confidence=0.9,
    )
    store.close()

    reopened = EvolutionStore(database)
    loaded = reopened.get_observation(saved["id"])
    assert loaded is not None
    assert loaded["description"] == saved["description"]
    assert loaded["evidence"] == saved["evidence"]
    assert loaded["context"]["skill"] == "architecture"
    assert len(reopened.list_observations(domain="software-engineering")) == 1
    reopened.close()


def test_validation_rejects_invalid_observations():
    store = EvolutionStore(":memory:")
    with pytest.raises(ValueError):
        store.add_observation(description=" ", domain="software", category="other")
    with pytest.raises(ValueError):
        store.add_observation(description="x", domain="software", category="unknown")
    with pytest.raises(ValueError):
        store.add_observation(description="x", domain="software", category="other", confidence=1.2)
    store.close()


def test_groups_are_candidates_and_require_recurrence():
    store = EvolutionStore(":memory:")
    for index in range(2):
        store.add_observation(
            description=f"Repeated correction {index}",
            domain="software-engineering",
            category="user-correction",
            context={"skill": "architecture"},
            confidence=0.8,
        )
    store.add_observation(
        description="Unrelated success",
        domain="writing",
        category="successful-strategy",
    )
    groups = store.observation_groups(min_occurrences=2)
    assert len(groups) == 1
    assert groups[0]["occurrences"] == 2
    assert groups[0]["interpretation"] == "candidate-pattern; requires human review"
    store.close()


def test_grouping_requires_at_least_two_observations():
    store = EvolutionStore(":memory:")
    with pytest.raises(ValueError):
        store.observation_groups(min_occurrences=1)
    store.close()


def test_review_requires_distinct_sessions_and_ranks_evidence(tmp_path):
    store = EvolutionStore(tmp_path / "review.sqlite3")
    for session_id, project in [
        ("session-a", "project-a"),
        ("session-b", "project-b"),
        ("session-c", "project-b"),
    ]:
        store.add_observation(
            description="The agent repeatedly skipped architecture discovery.",
            domain="software-engineering",
            category="user-correction",
            session_id=session_id,
            evidence=["A sanitized correction was recorded."],
            context={"skill": "architecture", "project": project},
            confidence=0.9,
        )
    # Multiple observations from one session must not inflate independent recurrence.
    store.add_observation(
        description="Another correction in the same session.",
        domain="software-engineering",
        category="user-correction",
        session_id="session-a",
        evidence=["Additional evidence."],
        context={"skill": "architecture", "project": "project-a"},
        confidence=0.9,
    )

    review = store.review_patterns(min_sessions=2)
    assert review["candidate_count"] == 1
    candidate = review["candidates"][0]
    assert candidate["independent_sessions"] == 3
    assert candidate["occurrences"] == 4
    assert candidate["project_count"] == 2
    assert candidate["priority"] in {"medium", "high"}
    assert review["review_policy"]["human_review_required"] is True
    store.close()


def test_review_ignores_observations_without_session_ids():
    store = EvolutionStore(":memory:")
    for _ in range(3):
        store.add_observation(
            description="Repeated but unlinked to a session.",
            domain="software-engineering",
            category="repeated-error",
            context={"skill": "architecture"},
        )
    review = store.review_patterns()
    assert review["candidate_count"] == 0
    assert "without session_id" in review["limitations"][0]
    store.close()


def test_review_reports_mixed_signals_without_calling_them_contradictions():
    store = EvolutionStore(":memory:")
    store.add_observation(
        description="A recurring gap was identified.",
        domain="software-engineering",
        category="instruction-gap",
        session_id="session-a",
        context={"skill": "architecture"},
    )
    store.add_observation(
        description="A useful strategy worked.",
        domain="software-engineering",
        category="successful-strategy",
        session_id="session-b",
        context={"skill": "architecture"},
    )
    review = store.review_patterns()
    assert len(review["mixed_signals"]) == 1
    assert "not necessarily contradictory" in review["mixed_signals"][0]["interpretation"]
    store.close()


def test_review_validates_bounds():
    store = EvolutionStore(":memory:")
    with pytest.raises(ValueError):
        store.review_patterns(min_sessions=1)
    with pytest.raises(ValueError):
        store.review_patterns(limit=0)
    store.close()
