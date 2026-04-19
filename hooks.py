"""AZPowers-Skills Agent Zero plugin lifecycle hooks."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_VERSION = "1.0.0"
DEPLOY_MARKER = ".azpowers-deployed"
CLAWPOWERS_VERSION = "2.2.6"


def _agent_python() -> str:
    """Return path to the agent runtime Python interpreter.

    Prefer /opt/venv/bin/python (standard Agent Zero venv); fall back to
    shutil.which('python3'). Last-resort fallback is sys.executable.
    """
    candidates = ["/opt/venv/bin/python", "/opt/venv/bin/python3"]
    for c in candidates:
        if Path(c).is_file():
            return c
    p = shutil.which("python3") or shutil.which("python")
    return p or sys.executable  # last-resort fallback


def _deploy_skill(skill_dir: Path, dest: Path) -> None:
    """Deploy a single skill directory to dest, guarding user skills.

    If dest exists and does NOT contain the AZPowers deploy marker, back it up
    instead of clobbering. After copy, write the marker file inside dest.
    """
    if dest.exists():
        marker = dest / DEPLOY_MARKER
        if marker.is_file():
            # prior AZPowers deploy — safe to replace
            shutil.rmtree(dest)
        else:
            backup = dest.with_suffix(".user-backup")
            # avoid collision with an existing backup
            idx = 1
            while backup.exists():
                backup = dest.with_suffix(f".user-backup.{idx}")
                idx += 1
            print(f"[AZPowers] Found user-owned {dest.name} at {dest} — renaming to {backup.name}")
            dest.rename(backup)
    shutil.copytree(skill_dir, dest)
    try:
        (dest / DEPLOY_MARKER).write_text(PLUGIN_VERSION + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"[AZPowers] WARNING: could not write deploy marker in {dest}: {exc}")
    print(f"[AZPowers] Installed skill: {skill_dir.name}")


def install(plugin_dir: str | None = None, unused_data_dir: str | None = None, **_kwargs) -> None:
    """Install AZPowers-Skills: deploy skill directories and runtime deps.

    Accepts the 2 positional args the framework *used* to pass, but also
    works when the framework calls us with no args or unexpected kwargs:
    we self-discover plugin_dir from __file__. Any extra kwargs are ignored.
    """
    if plugin_dir is None:
        plugin_dir = str(Path(__file__).parent)
    plugin_path = Path(plugin_dir)
    # Skills live at usr/skills/ — two levels up from usr/plugins/azpowers_skills/
    skills_target = plugin_path.parent.parent / "skills"
    skills_target.mkdir(parents=True, exist_ok=True)

    skills_src = plugin_path / "skills"
    if skills_src.is_dir():
        for skill_dir in skills_src.iterdir():
            if skill_dir.is_dir() and skill_dir.name.startswith("azpowers-"):
                dest = skills_target / skill_dir.name
                _deploy_skill(skill_dir, dest)
    else:
        print("[AZPowers] WARNING: skills/ directory not found in plugin dir")

    # Create ~/.clawpowers runtime directories
    home = Path.home()
    for sub in ["memory", "metrics", "logs", "wallet", "state/checkpoints", "data", "skills"]:
        (home / ".clawpowers" / sub).mkdir(parents=True, exist_ok=True)
    print("[AZPowers] ~/.clawpowers runtime directories ready")

    # Install clawpowers npm package if npm is available and not already installed
    npm_prefix = home / ".clawpowers" / "runtime"
    npm_prefix.mkdir(parents=True, exist_ok=True)

    package_json = npm_prefix / "node_modules" / "clawpowers" / "package.json"
    already_installed = False
    if package_json.is_file():
        try:
            with open(package_json) as f:
                installed_version = json.load(f).get("version", "")
            if installed_version == CLAWPOWERS_VERSION:
                print(f"[AZPowers] clawpowers@{CLAWPOWERS_VERSION} already installed at {npm_prefix}")
                already_installed = True
        except (json.JSONDecodeError, OSError):
            pass  # fall through to reinstall

    if not already_installed:
        try:
            result = subprocess.run(
                ["npm", "install", f"clawpowers@{CLAWPOWERS_VERSION}", "--prefix", str(npm_prefix)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"[AZPowers] clawpowers@{CLAWPOWERS_VERSION} installed at {npm_prefix}")
            else:
                stderr = (result.stderr or "").strip()
                print(
                    f"[AZPowers] WARNING: npm install exited with code {result.returncode} — "
                    f"continuing plugin install. stderr: {stderr}"
                )
                print("[AZPowers] You can run scripts/verify.sh later to retry npm setup.")
                return
        except FileNotFoundError:
            print("[AZPowers] WARNING: npm not found — skipping clawpowers npm install")
            print("[AZPowers] You can run scripts/verify.sh later to retry npm setup.")
            return

    # Install ITP service Python deps if requirements.txt present
    itp_req = plugin_path / "itp-service" / "requirements.txt"
    if itp_req.is_file():
        interp = _agent_python()
        print(f"[AZPowers] Installing ITP deps with {interp}")
        try:
            subprocess.run(
                [interp, "-m", "pip", "install", "-q", "-r", str(itp_req)],
                check=True,
            )
            print("[AZPowers] ITP service Python dependencies installed")
        except subprocess.CalledProcessError as exc:
            print(f"[AZPowers] WARNING: pip install failed: {exc}")

    print("[AZPowers] Installation complete.")


def uninstall(plugin_dir: str | None = None, data_dir: str | None = None, **_kwargs) -> None:
    """Uninstall AZPowers-Skills: remove ONLY directories marked as deployed by AZPowers.

    Accepts optional plugin_dir / data_dir, self-discovers from __file__ when omitted,
    and absorbs any extra kwargs from the framework.
    """
    if plugin_dir is None:
        plugin_dir = str(Path(__file__).parent)
    skills_target = Path(plugin_dir).parent.parent / "skills"
    if not skills_target.is_dir():
        print("[AZPowers] No skills directory found — nothing to remove")
        return

    removed = []
    skipped = []
    for skill_dir in list(skills_target.iterdir()):
        if skill_dir.is_dir() and skill_dir.name.startswith("azpowers-"):
            marker = skill_dir / DEPLOY_MARKER
            if marker.is_file():
                shutil.rmtree(skill_dir)
                removed.append(skill_dir.name)
            else:
                skipped.append(skill_dir.name)

    if removed:
        print(f"[AZPowers] Removed skills: {', '.join(removed)}")
    if skipped:
        print(
            "[AZPowers] Skipped (no AZPowers deploy marker — treating as user-owned): "
            f"{', '.join(skipped)}"
        )
    if not removed and not skipped:
        print("[AZPowers] No azpowers-* skills found to remove")

    print("[AZPowers] Uninstall complete.")


def pre_update(plugin_dir: str | None = None, data_dir: str | None = None, **_kwargs) -> None:
    """Called before plugin update. Runs uninstall to clean staging.

    Accepts optional args like install/uninstall for framework-agnostic calling.
    """
    print("[AZPowers] pre_update: cleaning up deployed skills before upgrade")
    uninstall(plugin_dir, data_dir)
