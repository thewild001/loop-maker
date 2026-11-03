from pathlib import Path

import pytest

from loop_maker.evolution_proposals import SkillProposalStore


def _store(tmp_path: Path):
    skills = tmp_path / "skills"
    skill = skills / "demo" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: demo\ndescription: Demo skill\n---\n\nOriginal.\n", encoding="utf-8")
    store = SkillProposalStore(tmp_path / "evolution.sqlite3", skills, tmp_path / "staging")
    return store, skill


def test_proposal_lifecycle_stages_and_requires_explicit_approval(tmp_path):
    store, active = _store(tmp_path)
    original = active.read_text(encoding="utf-8")
    proposed = original.replace("Original.", "Improved.")
    proposal = store.create_proposal(
        skill_path="demo/SKILL.md", proposed_content=proposed,
        rationale="Repeated instruction gap", observation_ids=["obs_a", "obs_b"],
    )
    assert proposal["status"] == "proposed"
    assert active.read_text(encoding="utf-8") == original
    with pytest.raises(ValueError, match="human approval"):
        store.approve_proposal(proposal["id"], approved=True)

    diff = store.diff_proposal(proposal["id"])
    assert "-Original." in diff["diff"]
    staged = store.stage_proposal(proposal["id"])
    assert Path(staged["staged_path"]).read_text(encoding="utf-8") == proposed
    assert active.read_text(encoding="utf-8") == original

    validation = store.validate_proposal(proposal["id"])
    assert validation["valid"] is True

    approved = store.approve_proposal(proposal["id"], approved=True)
    assert approved["status"] == "approved"
    assert approved["published"] is False
    assert active.read_text(encoding="utf-8") == original
    store.close()


def test_stale_active_skill_blocks_staging_and_validation(tmp_path):
    store, active = _store(tmp_path)
    proposal = store.create_proposal(
        skill_path="demo/SKILL.md",
        proposed_content="---\nname: demo\n---\nChanged.\n",
        rationale="A supported change", observation_ids=["obs_a"],
    )
    active.write_text(active.read_text(encoding="utf-8") + "External edit.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="active_skill_changed"):
        store.stage_proposal(proposal["id"])
    result = store.validate_proposal(proposal["id"])
    assert result["valid"] is False
    assert result["checks"]["active_skill_unchanged"] is False
    store.close()


def test_skill_path_rejects_traversal_and_symlinks(tmp_path):
    store, _ = _store(tmp_path)
    with pytest.raises(ValueError):
        store.create_proposal(
            skill_path="../outside.md", proposed_content="changed",
            rationale="reason", observation_ids=["obs_a"],
        )
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "skills" / "linked.md"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="symlinks"):
        store.create_proposal(
            skill_path="linked.md", proposed_content="changed",
            rationale="reason", observation_ids=["obs_a"],
        )
    store.close()


def test_proposal_rejects_empty_evidence_and_identical_content(tmp_path):
    store, active = _store(tmp_path)
    content = active.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="observation"):
        store.create_proposal(
            skill_path="demo/SKILL.md", proposed_content=content,
            rationale="reason", observation_ids=[],
        )
    with pytest.raises(ValueError, match="identical"):
        store.create_proposal(
            skill_path="demo/SKILL.md", proposed_content=content,
            rationale="reason", observation_ids=["obs_a"],
        )
    store.close()
