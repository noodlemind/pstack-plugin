"""Environment-local execution policy. Discovery never invokes a coding CLI.

Native agents are dispatched by the current host, not from this Python process.
Optional local CLI execution requires a machine-bound explicit setup choice.
There is no remote transport or credential forwarding in this module.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil

from store import Store, now, workspace


HARNESSES = {
    "codex": ("Codex CLI", "codex", True),
    "claude": ("Claude Code", "claude", True),
    "grok": ("Grok Build", "grok", True),
    "gemini": ("Gemini CLI", "gemini", True),
    "cursor": ("Cursor Agent", "agent", False),
    "opencode": ("OpenCode", "opencode", False),
    "aider": ("Aider", "aider", False),
    "copilot": ("GitHub Copilot CLI", "copilot", False),
}
EFFORTS = ["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"]
BUDGETS = {"unlimited": "max", "large": "xhigh", "medium": "high", "small": "medium"}


def fingerprint() -> str:
    return hashlib.sha256((platform.node() + "\0" + platform.system()).encode()).hexdigest()


def settings(store: Store) -> dict:
    try:
        value = store.get("config", "execution")
    except KeyError:
        value = {"host": "auto", "mode": "native", "enabled_cli": []}
    declared = os.environ.get("PSTACK_EXECUTION_HOST")
    if declared not in {None, "local", "cloud"}:
        raise ValueError("PSTACK_EXECUTION_HOST must be local or cloud")
    if declared == "cloud" or value["host"] == "cloud":
        return {**value, "host": "cloud", "mode": "native", "enabled_cli": []}
    if value.get("machine") != fingerprint() and value["mode"] != "native":
        return {**value, "mode": "native", "enabled_cli": [],
                "notice": "Local CLI consent belongs to a different machine; using the current host."}
    return value


def scan(store: Store) -> dict:
    policy = settings(store)
    entries = []
    for key, (label, command, supported) in HARNESSES.items():
        path = shutil.which(command)
        entries.append({"id": key, "name": label, "executable": path,
                        "installed": path is not None, "adapter_supported": supported,
                        "enabled": key in policy["enabled_cli"],
                        "authentication": "not checked", "models": "not probed"})
    return {"execution": policy, "preferences": preferences(store), "harnesses": entries,
            "default": "Use the current host's native agent, shell, browser and model tools.",
            "network_listener": False, "remote_access": False,
            "note": "Executable presence is not authenticated model access. Discovery does not run these programs or read their credentials. Unlisted harnesses remain unavailable until an adapter is verified."}


def setup(store: Store, host: str = "auto", mode: str = "native",
          enabled_cli: list[str] | None = None, confirmation: str = "") -> dict:
    if host not in {"auto", "local", "cloud"} or mode not in {"native", "local-cli"}:
        raise ValueError("invalid host or execution mode")
    enabled = list(dict.fromkeys(enabled_cli or []))
    if host == "cloud" or os.environ.get("PSTACK_EXECUTION_HOST") == "cloud":
        if mode != "native" or enabled:
            raise ValueError("Cloud execution uses native OpenAI models; local CLI adapters cannot be enabled")
        host = "cloud"
    if mode == "native" and enabled:
        raise ValueError("native mode does not launch optional CLIs")
    if mode == "local-cli":
        if host != "local" or not enabled or not confirmation.strip():
            raise ValueError("local CLI use requires a local host, selected harnesses and the user's choice")
        for key in enabled:
            entry = HARNESSES.get(key)
            if not entry or not entry[2] or not shutil.which(entry[1]):
                raise ValueError("no installed verified adapter for " + key)
    value = {"host": host, "mode": mode, "enabled_cli": enabled,
             "machine": fingerprint(), "confirmation": confirmation, "updated": now()}
    store.put("config", "execution", value)
    store.event("execution_configuration", value)
    return scan(store)


def require_cli(store: Store, provider: str) -> None:
    policy = settings(store)
    if policy["host"] == "cloud" or policy["mode"] != "local-cli" or provider not in policy["enabled_cli"]:
        raise ValueError("Use the current host's native agents. Optional CLI " + provider + " is disabled in this execution environment.")
    spec = HARNESSES.get(provider)
    if not spec or not spec[2] or not shutil.which(spec[1]):
        raise ValueError("Selected coding harness is no longer available: " + provider)


def catalog(store: Store, models: list[dict], source: str) -> dict:
    if not source.strip() or not isinstance(models, list):
        raise ValueError("current host catalog and its evidence source are required")
    result = []
    for entry in models:
        if entry.get("provider") != "openai" or not isinstance(entry.get("model"), str) or not entry["model"].strip():
            raise ValueError("native policy accepts only actual OpenAI host model identifiers")
        efforts = entry.get("efforts", [])
        if not isinstance(efforts, list) or any(e not in EFFORTS for e in efforts):
            raise ValueError("invalid host reasoning options")
        result.append({"provider": "openai", "model": entry["model"], "efforts": efforts})
    if len({m["model"] for m in result}) != len(result):
        raise ValueError("duplicate host model")
    value = {"models": result, "source": source, "machine": fingerprint(),
             "host": settings(store)["host"], "observed_at": now(),
             "evidence_kind": "host catalog; not an inference probe"}
    return store.put("config", "native_catalog", value)


def current_catalog(store: Store) -> dict:
    try:
        value = store.get("config", "native_catalog")
    except KeyError:
        return {}
    return value if value.get("machine") == fingerprint() and value.get("host") == settings(store)["host"] else {}


def preferences(store: Store) -> dict:
    """Read a user's choice without seeding configuration from distribution files."""
    selected = None
    origin = "unconfigured"
    for key in ["native_budget", "models"]:
        try:
            saved = store.get("config", key)
        except KeyError:
            continue
        if saved.get("budget") in BUDGETS:
            selected = saved["budget"]
            origin = key
            break
    return {"budget": selected, "reasoning_target": BUDGETS.get(selected),
            "source": origin, "requires_budget_choice": selected is None,
            "budget_options": dict(BUDGETS)}


def budget(store: Store, budget: str, confirmation: str) -> dict:
    if budget not in BUDGETS or not confirmation.strip():
        raise ValueError("a user-selected reasoning budget and confirmation are required")
    value = {"budget": budget, "confirmation": confirmation, "updated": now()}
    store.event("native_budget", value)
    return store.put("config", "native_budget", value)


def configure_native(store: Store, roles: dict, confirmation: str,
                     allowed_roles: list[str], panel_roles: set[str]) -> dict:
    if not confirmation.strip() or set(roles) != set(allowed_roles):
        raise ValueError("explicit choices for every native role are required")
    available = {m["model"] for m in current_catalog(store).get("models", [])}
    for role, seats in roles.items():
        if not isinstance(seats, list) or not 1 <= len(seats) <= 16 or (role not in panel_roles and len(seats) != 1):
            raise ValueError("invalid native role seats: " + role)
        if any(not isinstance(model, str) or model not in available for model in seats):
            raise ValueError("native role model is absent from this host's current catalog")
    value = {"roles": roles, "confirmation": confirmation, "machine": fingerprint(),
             "host": settings(store)["host"], "updated": now()}
    store.event("native_role_configuration", value)
    return store.put("config", "native_models", value)


def native_plan(store: Store, role: str, seats: int = 1,
                require_cross_provider: bool = False) -> dict:
    if not isinstance(seats, int) or isinstance(seats, bool) or not 1 <= seats <= 16:
        raise ValueError("request 1 to 16 seats")
    policy = settings(store)
    available = current_catalog(store)
    models = available.get("models", [])
    try:
        legacy_preferences = store.get("config", "models")
    except KeyError:
        legacy_preferences = {}
    selected_budget = preferences(store)["budget"]
    if selected_budget is None:
        raise ValueError("Choose a reasoning budget in setup-pstack before planning model work; no budget is selected by default")
    target = BUDGETS.get(selected_budget)
    preferred = [p.get("model") for p in legacy_preferences.get("roles", {}).get(role, []) if p.get("family") == "openai"]
    try:
        native_roles = store.get("config", "native_models")
    except KeyError:
        native_roles = {}
    explicit = native_roles.get("roles", {}).get(role) if native_roles.get("machine") == fingerprint() and native_roles.get("host") == policy["host"] else None
    if explicit:
        by_model = {m["model"]: m for m in models}
        if any(model not in by_model for model in explicit):
            raise ValueError("A configured native model is no longer advertised; update the role choice explicitly")
        models = [by_model[model] for model in explicit]
        seats = len(models)
        preferred = explicit
    models = sorted(models, key=lambda m: preferred.index(m["model"]) if m["model"] in preferred else len(preferred))
    selected = []
    for index in range(seats):
        model = models[index % len(models)] if models else None
        efforts = [e for e in model["efforts"] if target and EFFORTS.index(e) <= EFFORTS.index(target)] if model else []
        selected.append({"seat": index, "provider": "openai", "model": model["model"] if model else None,
                         "effort": max(efforts, key=EFFORTS.index) if efforts else None,
                         "dispatch": "current host native agent tool",
                         "selection": "explicit host model" if model else "inherit the current host model; identity unavailable"})
    distinct = len({s["model"] for s in selected if s["model"]})
    return {"state": "planned", "role": role, "host": policy["host"], "seats": selected,
            "budget": selected_budget or "current host default", "distinct_models": distinct,
            "cross_provider": False, "cross_provider_requirement_met": not require_cross_provider,
            "limitations": (["Cross-provider review is unavailable under the native OpenAI policy."] if require_cross_provider else []) +
                           (["Repeated or inherited model seats provide separate perspectives, not verified model diversity."] if seats > distinct else []),
            "catalog_source": available.get("source"),
            "instruction": "Dispatch with the host's actual agent tools and inherited permissions. Do not treat this plan as execution. If delegation is unavailable or forbidden, use sequential review and disclose that limitation. Never contact another machine."}


def native_record(store: Store, data: dict) -> dict:
    scope = workspace(data["workspace"])
    native_id = data.get("native_id")
    if not isinstance(native_id, str) or not native_id.strip():
        raise ValueError("actual host agent/task ID is required")
    state = data.get("state", "running")
    if state not in {"running", "completed", "failed", "cancelled", "interrupted"}:
        raise ValueError("invalid native task state")
    if state == "completed" and not data.get("evidence"):
        raise ValueError("completion needs the host result or verification receipt")
    key = hashlib.sha256((scope + "\0" + native_id).encode()).hexdigest()
    row = {**data, "id": key, "workspace": scope, "state": state, "updated": now(),
           "origin": "current host tool result recorded by coordinator"}
    store.event("native_agent", row, scope)
    return store.put("native_job", key, row, scope)
