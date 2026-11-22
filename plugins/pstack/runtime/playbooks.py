"""Resolve installed playbooks and extract the instructions tracked as tasks."""

from pathlib import Path
import re


def current_playbook(name: str) -> str:
    # Saved mode records and clients may still request the removed orchestration playbook.
    return "figure-it-out" if name == "orchestrate" else name


def playbook_path(plugin_root: Path, name: str) -> Path:
    name = current_playbook(name)
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise ValueError("unknown playbook")
    if name == "figure-it-out":
        path = plugin_root / "skills/figure-it-out/SKILL.md"
    else:
        path = plugin_root / "skills/poteto-mode/playbooks" / (name + ".md")
    if not path.is_file():
        raise ValueError("unknown playbook")
    return path


def playbook_steps(text: str) -> list[str]:
    if re.search(r"^## Phase A: ", text, re.M):
        sections = re.split(r"(?=^## )", text, flags=re.M)
        return [section.removeprefix("## ").split("\n**Reply:**", 1)[0].strip()
                for section in sections if re.match(r"^## (?:Start\n|Phase [A-Z]: )", section)]
    for marker in (r"^\d+\. ", r"^- "):
        steps = []
        current = []
        for line in text.splitlines():
            match = re.match(marker, line)
            if match:
                if current:
                    steps.append("\n".join(current).rstrip())
                current = [line[match.end():]]
            elif current and (not line or line[0].isspace()):
                current.append(line)
            elif current:
                steps.append("\n".join(current).rstrip())
                current = []
        if current:
            steps.append("\n".join(current).rstrip())
        if steps:
            return steps
    # Opening a PR is written as procedural paragraphs after a heading and invocation note.
    return [p for p in text.strip().split("\n\n")
            if p and not p.startswith(("#", "Invoked at "))]
