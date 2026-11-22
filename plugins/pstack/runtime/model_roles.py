"""The upstream role menu and labels accepted from previous port versions."""


ROLES = ["feature, refactoring", "bug-fix", "perf-issue", "hillclimb", "judgment and prose",
         "arena runners", "arena cross-judge pool", "swarm workers", "interrogate reviewers"]
LEGACY_ROLES = {"hardest tasks", "how explorer", "how explainer", "why investigators", "why synthesizer",
                "reflect tooling", "reflect judgment, divergent, synthesizer", "architect runners"}
PANELS = {"arena runners", "arena cross-judge pool", "interrogate reviewers", "architect runners"}


def validate_roles(roles: dict) -> None:
    missing = set(ROLES) - roles.keys()
    unknown = roles.keys() - set(ROLES) - LEGACY_ROLES
    if missing or unknown:
        raise ValueError(f"configure every current role; missing {sorted(missing)}, unknown {sorted(unknown)}")


def preserve_retired_choices(previous: dict, configured: dict) -> dict:
    """Keep omitted choices for inspection without selecting a retired model for new work."""
    old = {**previous.get("retired_roles", {}), **previous.get("roles", {})}
    return {role: old[role] for role in LEGACY_ROLES if role in old and role not in configured}
