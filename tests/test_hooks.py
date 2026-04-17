"""Unit tests for AZPowers-Skills hooks.py."""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_hooks():
    """Load hooks.py as a fresh module so tests are isolated."""
    spec = importlib.util.spec_from_file_location("azpowers_hooks", REPO_ROOT / "hooks.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["azpowers_hooks"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def hooks():
    return _load_hooks()


@pytest.fixture
def fake_plugin(tmp_path):
    """Create a fake plugin_dir layout under tmp_path.

    Layout:
        tmp_path/usr/plugins/azpowers_skills/
            skills/azpowers-memory/SKILL.md
            skills/azpowers-wallet/SKILL.md
        tmp_path/usr/skills/  (target)
    """
    plugin_dir = tmp_path / "usr" / "plugins" / "azpowers_skills"
    (plugin_dir / "skills" / "azpowers-memory").mkdir(parents=True)
    (plugin_dir / "skills" / "azpowers-memory" / "SKILL.md").write_text("---\nname: azpowers-memory\n---\n")
    (plugin_dir / "skills" / "azpowers-wallet").mkdir(parents=True)
    (plugin_dir / "skills" / "azpowers-wallet" / "SKILL.md").write_text("---\nname: azpowers-wallet\n---\n")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return plugin_dir, data_dir


# ── _agent_python ─────────────────────────────────────────────────────────────

def test_agent_python_returns_string(hooks):
    result = hooks._agent_python()
    assert isinstance(result, str)
    assert len(result) > 0


def test_agent_python_prefers_opt_venv(hooks, tmp_path):
    fake_python = tmp_path / "python"
    fake_python.write_text("#!/bin/sh\n")
    fake_python.chmod(0o755)

    original_is_file = Path.is_file

    def fake_is_file(self):
        if str(self) == "/opt/venv/bin/python":
            return True
        return original_is_file(self)

    with patch.object(Path, "is_file", fake_is_file):
        result = hooks._agent_python()
    assert result == "/opt/venv/bin/python"


def test_agent_python_fallback_to_which(hooks):
    # Force no /opt/venv candidates to exist
    with patch.object(Path, "is_file", lambda self: False), \
         patch("shutil.which", side_effect=lambda name: "/usr/bin/python3" if name == "python3" else None):
        result = hooks._agent_python()
    assert result == "/usr/bin/python3"


def test_agent_python_last_resort_sys_executable(hooks):
    with patch.object(Path, "is_file", lambda self: False), \
         patch("shutil.which", return_value=None):
        result = hooks._agent_python()
    assert result == sys.executable


# ── install() ─────────────────────────────────────────────────────────────────

def test_install_creates_clawpowers_subdirs(hooks, fake_plugin, tmp_path, monkeypatch):
    plugin_dir, data_dir = fake_plugin
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))

    # Prevent real npm from running
    with patch("subprocess.run", side_effect=FileNotFoundError("no npm")):
        hooks.install(str(plugin_dir), str(data_dir))

    for sub in ["memory", "metrics", "logs", "wallet", "state/checkpoints", "data", "skills"]:
        assert (home / ".clawpowers" / sub).is_dir(), f"missing ~/.clawpowers/{sub}"


def test_install_deploys_skills_with_marker(hooks, fake_plugin, tmp_path, monkeypatch):
    plugin_dir, data_dir = fake_plugin
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))

    with patch("subprocess.run", side_effect=FileNotFoundError("no npm")):
        hooks.install(str(plugin_dir), str(data_dir))

    skills_target = plugin_dir.parent.parent / "skills"
    assert (skills_target / "azpowers-memory" / "SKILL.md").is_file()
    assert (skills_target / "azpowers-memory" / hooks.DEPLOY_MARKER).is_file()
    assert (skills_target / "azpowers-wallet" / hooks.DEPLOY_MARKER).is_file()


def test_install_guards_user_owned_skill(hooks, fake_plugin, tmp_path, monkeypatch):
    plugin_dir, data_dir = fake_plugin
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))

    # Pre-create a user-owned azpowers-memory skill (no marker)
    skills_target = plugin_dir.parent.parent / "skills"
    skills_target.mkdir(parents=True)
    user_skill = skills_target / "azpowers-memory"
    user_skill.mkdir()
    (user_skill / "USER_FILE.md").write_text("user content\n")

    with patch("subprocess.run", side_effect=FileNotFoundError("no npm")):
        hooks.install(str(plugin_dir), str(data_dir))

    # User dir should be backed up, not deleted
    backup = user_skill.with_suffix(".user-backup")
    assert backup.is_dir(), "user-owned skill directory must be backed up"
    assert (backup / "USER_FILE.md").is_file()
    # New deploy with marker should exist
    assert (user_skill / hooks.DEPLOY_MARKER).is_file()


# ── uninstall() ───────────────────────────────────────────────────────────────

def test_uninstall_only_removes_marked(hooks, tmp_path):
    plugin_dir = tmp_path / "usr" / "plugins" / "azpowers_skills"
    plugin_dir.mkdir(parents=True)
    skills_target = tmp_path / "usr" / "skills"
    skills_target.mkdir(parents=True)

    # A marked deploy
    marked = skills_target / "azpowers-memory"
    marked.mkdir()
    (marked / hooks.DEPLOY_MARKER).write_text("1.0.0\n")
    (marked / "SKILL.md").write_text("content")

    # A user-owned azpowers-* dir (no marker) — must NOT be deleted
    user_owned = skills_target / "azpowers-custom"
    user_owned.mkdir()
    (user_owned / "SKILL.md").write_text("user content")

    hooks.uninstall(str(plugin_dir), str(tmp_path / "data"))

    assert not marked.exists(), "marked skill must be removed"
    assert user_owned.exists(), "user-owned skill must NOT be removed"
    assert (user_owned / "SKILL.md").is_file()


def test_uninstall_no_skills_dir(hooks, tmp_path, capsys):
    plugin_dir = tmp_path / "usr" / "plugins" / "azpowers_skills"
    plugin_dir.mkdir(parents=True)
    # No skills_target exists
    hooks.uninstall(str(plugin_dir), str(tmp_path / "data"))
    captured = capsys.readouterr()
    assert "No skills directory found" in captured.out


# ── pre_update() ──────────────────────────────────────────────────────────────

def test_pre_update_invokes_uninstall(hooks, tmp_path):
    plugin_dir = tmp_path / "usr" / "plugins" / "azpowers_skills"
    plugin_dir.mkdir(parents=True)
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    with patch.object(hooks, "uninstall") as mock_uninstall:
        hooks.pre_update(str(plugin_dir), str(data_dir))
        mock_uninstall.assert_called_once_with(str(plugin_dir), str(data_dir))
