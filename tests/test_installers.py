from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install-skills.sh"


def run_installer(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(INSTALLER), "--target", str(target), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_installs_skills_and_host_recipes_into_clean_target(tmp_path: Path):
    target = tmp_path / "workspace"

    result = run_installer(target)

    assert result.returncode == 0, result.stderr
    for host_path in (".agents/skills", ".claude/skills", ".opencode/skills"):
        installed = target / host_path / "loop-maker" / "SKILL.md"
        assert installed.is_file()
        assert "Loop Maker" in installed.read_text(encoding="utf-8")

    assert (target / ".opencode/agents/loop-maker-orchestrator.md").is_file()
    assert (target / ".cursor/rules/loop-maker.mdc").is_file()
    assert (target / ".github/instructions/loop-maker.instructions.md").is_file()


def test_preserves_existing_skill_unless_force_is_requested(tmp_path: Path):
    target = tmp_path / "workspace"
    existing = target / ".agents/skills/loop-maker/SKILL.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("user-owned content", encoding="utf-8")

    preserved = run_installer(target)
    assert preserved.returncode == 0, preserved.stderr
    assert existing.read_text(encoding="utf-8") == "user-owned content"

    overwritten = run_installer(target, "--force")
    assert overwritten.returncode == 0, overwritten.stderr
    assert existing.read_text(encoding="utf-8") != "user-owned content"
    assert "Loop Maker" in existing.read_text(encoding="utf-8")


def test_rejects_unknown_installer_option(tmp_path: Path):
    result = run_installer(tmp_path / "workspace", "--not-a-real-option")
    assert result.returncode == 2
    assert "Opción desconocida" in result.stderr
