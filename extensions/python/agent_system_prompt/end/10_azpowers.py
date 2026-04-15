"""AZPowers-Skills system prompt injection extension.

Injects available AZPowers skill names into the agent system prompt so the
agent knows which capabilities it can load via skills_tool.
"""
from pathlib import Path


async def extension(agent, prompt, **kwargs):
    """Append AZPowers capabilities block to the agent system prompt."""
    # Skills are at usr/skills/ — navigate from:
    # extensions/python/agent_system_prompt/end/  (4 levels up inside plugin dir)
    # then plugin dir is usr/plugins/azpowers_skills/ (2 more levels up to usr/)
    # full path: <plugin_dir>/extensions/python/agent_system_prompt/end/10_azpowers.py
    # usr/skills/ is at plugin_dir/../../skills/
    skills_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "skills"

    if not skills_dir.is_dir():
        return prompt

    azpowers_skills = sorted(
        d.name for d in skills_dir.iterdir()
        if d.is_dir() and d.name.startswith("azpowers-")
    )

    if not azpowers_skills:
        return prompt

    skills_list = "\n".join(f"- `{s}`" for s in azpowers_skills)
    injection = f"""
## AZPowers Skills Available
You have access to AZPowers-Skills v2.2.6 capabilities. Use `skills_tool:load <skill_name>`:
{skills_list}
"""
    return prompt + injection
