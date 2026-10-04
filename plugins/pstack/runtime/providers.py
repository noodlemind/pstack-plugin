from __future__ import annotations

from xai_worker import api_request, credential
import sys

import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import queue
import re
import signal
import threading

from store import ROOT, Store, now, data_home, VERSION
import harnesses

ROLES = ["feature, refactoring", "bug-fix", "perf-issue", "hillclimb", "judgment and prose", "hardest tasks", "how explorer", "how explainer", "why investigators", "why synthesizer", "reflect tooling", "reflect judgment, divergent, synthesizer", "arena runners", "arena cross-judge pool", "swarm workers", "architect runners", "interrogate reviewers"]
PANELS = {"arena runners", "arena cross-judge pool", "architect runners", "interrogate reviewers"}
EFFORTS = ["low", "medium", "high", "xhigh", "max", "ultra"]
BUDGETS = {"unlimited": "max", "large": "xhigh", "medium": "high", "small": "medium"}
# Observed and rechecked with Grok Build 1.0.46. This is an explicit CLI selector
# to reported backend identity mapping, not permission to substitute a model.
GROK_BACKENDS = {"grok-4.7": {"grok-4.7-build"}}


def safe_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ["SLACK", "LINEAR", "BENNY", "GITHUB_TOKEN", "GH_TOKEN", "GROK", "XAI"]) and k not in {"CLAUDECODE"}}


def grok_env() -> dict[str, str]:
    env = safe_env()
    env["GROK_DISABLE_AUTOUPDATER"] = "1"
    for vendor in ["CLAUDE", "CURSOR", "CODEX"]:
        for surface in ["SKILLS", "RULES", "AGENTS", "MCPS", "HOOKS", "SESSIONS"]:
            env[f"GROK_{vendor}_{surface}_ENABLED"] = "0"
    env["GROK_MANAGED_MCPS_ENABLED"] = "0"
    env["GROK_MANAGED_MCP_GATEWAY_TOOLS_ENABLED"] = "0"
    return env


def grok_catalog() -> list[str]:
    proc = subprocess.run(["grok", "models"], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, env=grok_env(), timeout=45)
    if proc.returncode:
        raise RuntimeError("Grok CLI catalog failed: " + proc.stderr[-1500:])
    return list(dict.fromkeys(re.findall(r"^\s*[-*]\s+(\S+)", proc.stdout, re.M)))


def model_matches(provider: str, model: str, parsed: dict) -> bool:
    if provider == "grok":
        observed = set(parsed.get("models", []))
        expected = GROK_BACKENDS.get(model, set())
        return observed == {model} or bool(expected) and observed == expected
    return provider not in {"claude", "gemini", "xai"} or model in parsed.get("models", [])


def effort_applied(provider: str, stderr: str) -> bool:
    return provider != "grok" or "model does not support reasoning effort; ignoring" not in stderr


def codex_rpc(method: str, params: dict) -> dict:
    proc = subprocess.Popen(["codex", "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    replies = queue.Queue()
    def read_replies():
        for line in proc.stdout:
            replies.put(line)
        replies.put(None)
    threading.Thread(target=read_replies, daemon=True).start()
    try:
        messages = [(1, "initialize", {"clientInfo": {"name": "pstack", "version": VERSION}, "capabilities": {"experimentalApi": True}}), (2, method, params)]
        result = None
        for ident, name, args in messages:
            proc.stdin.write(json.dumps({"id": ident, "method": name, "params": args}) + "\n")
            proc.stdin.flush()
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                try: line = replies.get(timeout=1)
                except queue.Empty: continue
                if not line:
                    raise RuntimeError("Codex app-server closed")
                reply = json.loads(line)
                if reply.get("id") != ident:
                    continue
                if "error" in reply:
                    raise RuntimeError(json.dumps(reply["error"]))
                result = reply["result"]
                break
            else:
                raise TimeoutError(name)
            if ident == 1:
                proc.stdin.write('{"method":"initialized","params":{}}\n')
                proc.stdin.flush()
        return result
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()


def discover(store: Store) -> dict:
    policy = harnesses.settings(store)
    if policy["mode"] == "native":
        native = harnesses.current_catalog(store) or {"models": [], "source": "Read the current host model tools; do not invoke another CLI."}
        return {"native_catalog": native, **harnesses.scan(store)}
    enabled = policy["enabled_cli"]
    models = []
    errors = {}
    if "codex" in enabled and shutil.which("codex"):
        cursor = None
        while True:
            page = codex_rpc("model/list", {"includeHidden": False, "cursor": cursor})
            for m in page["data"]:
                key = "codex:" + m["model"]
                existing = next((x for x in store.list("model") if x["key"] == key), {})
                entry = {"key": key, "provider": "codex", "model": m["model"], "family": "openai", "efforts": [x["reasoningEffort"] for x in m["supportedReasoningEfforts"]], "catalog_at": now(), "verified": existing.get("verified", False), "proof": existing.get("proof")}
                store.put("model", key, entry)
                models.append(entry)
            cursor = page.get("nextCursor")
            if not cursor:
                break

    if "grok" in enabled and shutil.which("grok"):
        try:
            for model in grok_catalog():
                key = "grok:" + model
                existing = next((x for x in store.list("model") if x["key"] == key), {})
                store.put("model", key, {**existing, "key": key, "provider": "grok",
                          "model": model, "family": "xai", "efforts": existing.get("efforts", []),
                          "verified": existing.get("verified", False), "catalog_at": now(),
                          "transport": "authenticated Grok Build CLI"})
        except Exception as exc:
            errors["grok"] = str(exc)
    if "xai" in enabled and credential(required=False):
        for m in api_request("models")["data"]:
            key = "xai:" + m["id"]
            existing = next((x for x in store.list("model") if x["key"] == key), {})
            store.put("model", key, {**existing, "key": key, "provider": "xai", "model": m["id"], "family": "xai", "efforts": existing.get("efforts", []), "verified": existing.get("verified", False), "catalog_at": now()})
    return {"models": models + [x for x in store.list("model") if x["provider"] != "codex" and x["provider"] in enabled], "clients": {p: shutil.which(p) is not None for p in ["codex", "claude", "grok", "gemini"]}, "errors": errors, "xai_credentials_present": "not inspected", "note": "Catalog presence is distinct from a successful inference probe. Configuration accepts only probed models. Grok CLI and xAI API are explicit separate transports. No provider fallback."}


def grok_native_command(model: str, effort: str, prompt: str, readonly: bool, session: str | None = None, cwd: str | None = None) -> list[str]:
    scope = str(Path(cwd or os.getcwd()).resolve())
    tools = "Read,Glob,Grep" if readonly else "Read,Glob,Grep,Edit,Write"
    cmd = ["grok", "-p", prompt, "-m", model, "--reasoning-effort", effort,
           "--output-format", "json", "--tools", tools, "--sandbox", "workspace",
           "--no-subagents", "--disable-web-search", "--permission-mode", "dontAsk"]
    for tool in ["Read", "Glob", "Grep"]:
        cmd += ["--allow", tool]
    for tool in ["Bash", "MCP", "Agent", "Task", "WebFetch", "WebSearch"] + (["Edit", "Write"] if readonly else []):
        cmd += ["--deny", tool]
    if not readonly:
        for tool in ["Edit", "Write"]:
            cmd += ["--allow", tool + "(" + scope + "/**)" ]
    if session:
        cmd += ["--resume", session]
    return cmd


def command(selection: dict, prompt: str, readonly: bool, session: str | None = None) -> list[str]:
    provider, model, effort = selection["provider"], selection["model"], selection["effort"]
    if provider == "codex":
        cmd = ["codex", "exec"]
        if session:
            cmd += ["resume", session]
        cmd += ["--ignore-user-config", "--skip-git-repo-check", "--json", "-m", model, "-c", "model_reasoning_effort=" + json.dumps(effort), "-c", 'approval_policy="never"', "-c", 'sandbox_mode=' + json.dumps("read-only" if readonly else "workspace-write"), "-c", "features.hooks=false", "-c", "features.plugins=false", "-c", "sandbox_workspace_write.network_access=false"]
        return cmd + [prompt]
    if provider == "claude":
        tools = "Read,Glob,Grep" if readonly else "Read,Glob,Grep,Edit,Write"
        cmd = ["claude", "-p", prompt, "--model", model, "--effort", effort, "--output-format", "json", "--tools", tools, "--allowedTools", tools, "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--setting-sources", "", "--disable-slash-commands"]
        if session:
            cmd += ["--resume", session]
        return cmd
    if provider == "gemini":
        if not readonly:
            raise ValueError("Gemini writer access has not been verified")
        return ["gemini", "-p", prompt, "-m", model, "-o", "json", "--approval-mode", "plan", "--skip-trust"] + (["--resume", session] if session else [])
    if provider == "grok":
        if not readonly and model not in GROK_BACKENDS:
            raise ValueError("Grok writer model has not passed the workspace boundary workflow")
        cmd = [sys.executable, str(ROOT / "runtime/grok_cli_worker.py"), "--model", model,
               "--effort", effort, "--prompt", prompt, "--readonly" if readonly else "--write"]
        if session:
            cmd += ["--resume", session]
        return cmd
    if provider == "xai":

        return [sys.executable, str(ROOT / "runtime/xai_worker.py"), "--model", model, "--effort", effort, "--prompt", prompt, "--readonly" if readonly else "--write"] + (["--resume", session] if session else [])
    raise ValueError("unsupported provider; configure a verified CLI adapter")


def parse_output(provider: str, output: str) -> dict:
    if provider == "xai": return json.loads(output)
    if provider == "grok":
        e = json.loads(output)
        return {"session": e.get("sessionId"), "text": e.get("text", ""),
                "completed": e.get("stopReason") == "end_turn" and e.get("type") != "error",
                "models": list(e.get("modelUsage", {})), "errors": e.get("message") if e.get("type") == "error" else [],
                "usage": e.get("usage", {}), "stop_reason": e.get("stopReason")}
    if provider == "codex":
        items = []
        session = None
        completed = False
        errors = []
        for line in output.splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "thread.started":
                session = e["thread_id"]
            if e.get("type") == "turn.completed":
                completed = True
            if e.get("type") in {"error", "turn.failed"}:
                errors.append(e)
            if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message":
                items.append(e["item"]["text"])
        return {"session": session, "text": "\n".join(items), "completed": completed and not errors, "errors": errors}
    if provider == "claude":
        e = json.loads(output)
        return {"session": e.get("session_id"), "text": e.get("result", ""), "completed": not e.get("is_error", True), "models": list(e.get("modelUsage", {})), "errors": e.get("errors", [])}
    e = json.loads(output)
    return {"session": e.get("session_id"), "text": e.get("response", ""), "completed": "error" not in e, "models": list(e.get("stats", {}).get("models", {})), "errors": e.get("error")}


def capture(argv, cwd, env, timeout=120):
    """Bound a probe's entire owned process group, including native helpers."""
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = proc.communicate(input='', timeout=timeout)
    except subprocess.TimeoutExpired:
        try: os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError: pass
        try: proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.communicate()
        raise RuntimeError('model probe execution deadline exhausted; owned process group cancelled')
    return subprocess.CompletedProcess(argv, proc.returncode, stdout, stderr)


def probe(store: Store, provider: str, model: str, effort: str = "medium") -> dict:
    harnesses.require_cli(store, provider)
    if effort not in EFFORTS:
        raise ValueError("invalid reasoning effort")
    selection = {"provider": provider, "model": model, "effort": effort}
    env = grok_env() if provider == "grok" else safe_env()
    if provider == "grok" and model not in grok_catalog():
        raise ValueError("model is not in the authenticated Grok CLI catalog")
    if provider == "xai":

        env["XAI_API_KEY"] = credential()
    proc = capture(command(selection, "Reply with exactly PSTACK_MODEL_PROBE. Do not use tools.", True), store.home, env)
    parsed = parse_output(provider, proc.stdout) if proc.stdout.strip() else {"completed": False, "text": ""}
    if not effort_applied(provider, proc.stderr):
        raise RuntimeError("Grok CLI ignored the requested effort; refusing to mark it supported")
    if proc.returncode != 0 or not parsed["completed"] or parsed["text"].strip() != "PSTACK_MODEL_PROBE":
        raise RuntimeError(f"model probe failed for {provider}:{model}: " + (proc.stderr[-1500:] or str(parsed)))
    if not model_matches(provider, model, parsed):
        raise RuntimeError("provider returned a different model; refusing to configure alias")
    key = provider + ":" + model
    existing = next((x for x in store.list("model") if x["key"] == key), {})
    efforts = existing.get("efforts", [])
    if effort not in efforts:
        efforts.append(effort)
    return store.put("model", key, {**existing, "key": key, "provider": provider, "model": model, "family": {"codex": "openai", "claude": "anthropic", "gemini": "google", "grok": "xai", "xai": "xai"}[provider], "efforts": efforts, "verified": True, "capabilities": (["read", "resume", "write-workspace"] if model in GROK_BACKENDS else ["read", "resume"]) if provider == "grok" else existing.get("capabilities"), "reported_models": parsed.get("models", []), "proof": {"time": now(), "effort": effort, "session": parsed.get("session"), "output": parsed["text"], "reported_models": parsed.get("models", [])}})


def configure(store: Store, budget: str, roles: dict, confirmation: str) -> dict:
    if budget not in BUDGETS or not confirmation.strip():
        raise ValueError("a user-selected budget and confirmation are required")
    if set(roles) != set(ROLES):
        raise ValueError("configure every upstream role; missing " + str(set(ROLES) - set(roles)))
    catalog = {x["key"]: x for x in store.list("model")}
    mapped = {}
    for role, values in roles.items():
        if not isinstance(values, list) or not values or (role not in PANELS and len(values) != 1):
            raise ValueError(f"invalid role entries: {role}")
        seats = []
        for key in values:
            if key in {"auto", "inherit-parent"}:
                seats.append({"alias": key})
                continue
            entry = catalog.get(key)
            if not entry or not entry.get("verified"):
                raise ValueError("unverified model: " + key)
            target = BUDGETS[budget]
            choices = [x for x in entry["efforts"] if EFFORTS.index(x) <= EFFORTS.index(target)]
            if not choices:
                raise ValueError("no supported effort at selected budget: " + key)
            seats.append({"provider": entry["provider"], "model": entry["model"], "family": entry["family"], "effort": max(choices, key=EFFORTS.index)})
        mapped[role] = seats
    config = {"budget": budget, "roles": mapped, "confirmed_by_user": confirmation, "updated": now()}
    store.event("configuration", config)
    return store.put("config", "models", config)


def selection(store: Store, role: str, seat: int = 0, parent: dict | None = None) -> dict:
    value = store.get("config", "models")["roles"][role][seat]
    if "alias" in value:
        if not parent:
            raise ValueError("inherit-parent requires verified parent model metadata")
        entry = store.get("model", parent["provider"] + ":" + parent["model"])
        if not entry["verified"] or parent["effort"] not in entry["efforts"]:
            raise ValueError("parent model/effort has not been verified")
        return {**parent, "family": entry["family"]}
    return value
