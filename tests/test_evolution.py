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
