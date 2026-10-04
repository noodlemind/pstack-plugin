#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
import harnesses
from api import context
from engine import execute
from store import ROOT, Store, identity, now, workspace


def hook(event: dict) -> dict:
    store = Store()
    scope = workspace(event.get("cwd", str(Path.cwd())))
    session = event.get("session_id", "workspace")
    name = event["hook_event_name"]
    args = {"workspace": scope, "session": session}
    prompt = event.get("prompt", "")
    if name == "UserPromptSubmit":
        if re.search(r"(?:poteto(?:-mode)?|pstack mode)\s+(?:off|disable)|stop poteto", prompt, re.I):
            context(store, args, "deactivate")
            return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": "Poteto mode disabled for this session."}}
        if re.search(r"/poteto-mode|\$poteto-mode|activate poteto|use poteto.mode", prompt, re.I):
            context(store, {**args, "prompt": prompt}, "activate")
    if name in {"SessionStart", "UserPromptSubmit"}:
        rules = "Team kit rules: keep imports at module top except documented strict circular dependencies. TypeScript switches on unions/enums must use a never check in default."
        ctx = context(store, {**args, **({"prompt": prompt} if prompt else {})})
        mode = ctx["mode"]
        if not mode.get("enabled"):
            return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": rules}}
        if name == "UserPromptSubmit" and re.fullmatch(r"\s*(?:thanks|thank you|hello|hi|ok)[.! ]*", prompt, re.I):
            return {}
        text = rules + " Sticky poteto-mode is active. Read " + str(ROOT / "skills/poteto-mode/SKILL.md") + " in full if not loaded, then read " + ctx["playbook_path"] + ". Preserve its exact steps in pstack_task, including explicit skips. Read " + ctx["adapter_contract"] + ". These pstack names are local helper operations, not MCP tools. Read the installed references/runtime-contract.md. Use the current host native agents and its actual OpenAI model catalog; saved CLI preferences are inactive in native mode. Read pstack_environment preferences for the saved reasoning budget; ask if no choice exists. No unverified model fallbacks. User authorization and host permission boundaries govern external actions."
        checkpoints = store.list("checkpoint", scope)
        if checkpoints:
            text += " Latest checkpoint ID " + checkpoints[-1]["id"] + ". Recover with pstack_checkpoint and reverify inherited claims."
        store.event("hook_context", {"session": session, "event": name, "playbook": ctx["selected_playbook"]}, scope)
        return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": text}}
    if name in {"PreCompact", "Interrupt", "SessionEnd"}:
        store.put("checkpoint", key := identity(), {"id": key, "workspace": scope, "session": session, "time": now(), "event": name, "transcript_path": event.get("transcript_path"), "last_assistant_message": event.get("last_assistant_message"), "next_steps": "Read scoped runtime state and exact transcript. Verify the current artifact before continuing."}, scope)
        if name == "Interrupt":
            for row in store.list("foreground", scope):
                if row.get("session") == session and row["state"] == "running": store.put("foreground", row["id"], {**row, "state": "cancelled", "stop_reason": "user interruption"}, scope)
        return {}
    if name == "Stop":
        if harnesses.settings(store)["mode"] == "native":
            return {}
        rows = [r for r in store.list("foreground", scope) if r["session"] == session and r["state"] == "running"]
        if not rows: return {}
        row = rows[-1]
        expected = {"state": "running", "iteration": row["iteration"]}
        remaining = row["max_seconds"] - (time.time() - row["started_at"])
        if remaining <= 0 or row["iteration"] >= row["max_iterations"]:
            changed = store.compare_put("foreground", row["id"], expected, {**row, "state": "blocked", "stop_reason": "budget exhausted; predicate not proven"}, scope)
            return {"systemMessage": "pstack continuation budget exhausted. Work remains incomplete."} if changed else {}
        proof = execute(row["done_command"], scope, min(20, remaining))
        store.event("foreground_predicate", {"loop": row["id"], "proof": proof}, scope)
        if proof["exit_code"] == 124:
            changed = store.compare_put("foreground", row["id"], expected, {**row, "state": "blocked", "proof": proof, "stop_reason": "predicate timeout; proof missing"}, scope)
            return {"systemMessage": "pstack predicate timed out. Work remains incomplete."} if changed else {}
        if proof["exit_code"] == 0:
            store.compare_put("foreground", row["id"], expected, {**row, "state": "completed", "proof": proof}, scope)
            return {}
        if not store.compare_put("foreground", row["id"], expected, {**row, "iteration": row["iteration"] + 1}, scope): return {}
        return {"decision": "block", "reason": "Continue the authorized pstack objective. " + row["prompt"] + " The pinned done predicate failed. Read checkpoints and decision trail. Complete the smallest next unit, verify it, and record evidence. Do not relax the predicate."}
    return {}


if __name__ == "__main__":
    try: print(json.dumps(hook(json.load(sys.stdin))))
    except Exception as e: print(json.dumps({"systemMessage": "pstack hook failed: " + str(e)})); sys.exit(1)
