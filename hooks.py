"""AZPowers-Skills Agent Zero plugin lifecycle hooks."""
import sys
import shutil
import subprocess
from pathlib import Path


def install(plugin_dir: str, data_dir: str) -> None:
    """Install AZPowers-Skills: deploy skill directories and runtime deps."""
    plugin_path = Path(plugin_dir)
    # Skills live at usr/skills/ — two levels up from usr/plugins/azpowers_skills/
    skills_target = Path(plugin_dir).parent.parent / "skills"
    skills_target.mkdir(parents=True, exist_ok=True)

    skills_src = plugin_path / "skills"
    if skills_src.is_dir():
        for skill_dir in skills_src.iterdir():
            if skill_dir.is_dir() and skill_dir.name.startswith("azpowers-"):
                dest = skills_target / skill_dir.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(skill_dir, dest)
                print(f"[AZPowers] Installed skill: {skill_dir.name}")
    else:
        print("[AZPowers] WARNING: skills/ directory not found in plugin dir")

    # Create ~/.clawpowers runtime directories
    home = Path.home()
    for sub in ["memory", "metrics", "logs", "wallet", "state/checkpoints", "data", "skills"]:
        (home / ".clawpowers" / sub).mkdir(parents=True, exist_ok=True)
    print("[AZPowers] ~/.clawpowers runtime directories ready")

    # Install clawpowers npm package if npm is available
    try:
        npm_prefix = home / ".clawpowers" / "runtime"
        npm_prefix.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["npm", "install", "clawpowers@2.2.6", "--prefix", str(npm_prefix)],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"[AZPowers] clawpowers@2.2.6 installed at {npm_prefix}")
    except FileNotFoundError:
        print("[AZPowers] WARNING: npm not found — skipping clawpowers npm install")
    except subprocess.CalledProcessError as exc:
        print(f"[AZPowers] WARNING: npm install failed: {exc.stderr.strip()}")

    # Install ITP service Python deps if requirements.txt present
    itp_req = plugin_path / "itp-service" / "requirements.txt"
    if itp_req.is_file():
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", str(itp_req)],
                check=True,
            )
            print("[AZPowers] ITP service Python dependencies installed")
        except subprocess.CalledProcessError as exc:
            print(f"[AZPowers] WARNING: pip install failed: {exc}")

    print("[AZPowers] Installation complete.")


def uninstall(plugin_dir: str, data_dir: str) -> None:
    """Uninstall AZPowers-Skills: remove deployed azpowers-* skill directories."""
    skills_target = Path(plugin_dir).parent.parent / "skills"
    if not skills_target.is_dir():
        print("[AZPowers] No skills directory found — nothing to remove")
        return

    removed = []
    for skill_dir in list(skills_target.iterdir()):
        if skill_dir.is_dir() and skill_dir.name.startswith("azpowers-"):
            shutil.rmtree(skill_dir)
            removed.append(skill_dir.name)

    if removed:
        print(f"[AZPowers] Removed skills: {', '.join(removed)}")
    else:
        print("[AZPowers] No azpowers-* skills found to remove")

    print("[AZPowers] Uninstall complete.")
