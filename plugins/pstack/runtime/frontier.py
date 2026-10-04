from __future__ import annotations

import json
import os
from pathlib import Path

from engine import execute
from github import gh_json


def frontier(args: dict) -> dict:
    scope = args["workspace"]
    argv = args["argv"]
    if "--prs" not in argv:
        raise ValueError("native frontier requires an explicit frozen bottom-to-top --prs list")
    numbers = [int(x) for x in argv[argv.index("--prs") + 1].split(",")]
    if not numbers or any(n <= 0 for n in numbers) or len(set(numbers)) != len(numbers): raise ValueError("PR order must be nonempty, positive and unique")
    store = Path(args.get("store_path") or os.environ.get("ORCH_STORE", ""))
    if not str(store) or not (store / "frontier.json").is_file(): raise ValueError("initialize an orch store and provide store_path")
    requested = [argv[argv.index('--repo') + 1]] if '--repo' in argv else []
    repo = gh_json(["repo", "view", *requested, "--json", "nameWithOwner"], scope)["nameWithOwner"]
    prs = [gh_json(["pr", "view", str(n), "--repo", repo, "--json", "number,state,headRefName,baseRefName,headRefOid"], scope) for n in numbers]
    for parent, child in zip(prs, prs[1:]):
        if parent["state"] == "OPEN" and child["baseRefName"] != parent["headRefName"]:
            raise ValueError("PR order is not a contiguous base-branch chain")
    lock = store / ".orch.lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, (str(os.getpid()) + "\n").encode()); os.close(fd)
        old = json.loads((store / "frontier.json").read_text())
        result = {"generation": old.get("generation", 0) + 1, "prs": [{"pr": p["number"], "branches": p["headRefName"], "sha": p["headRefOid"], "state": p["state"]} for p in prs], "lowestUnmerged": next((p["number"] for p in prs if p["state"] == "OPEN"), None)}
        temporary = store / "frontier.json.tmp"
        temporary.write_text(json.dumps(result, indent=2) + "\n"); temporary.replace(store / "frontier.json")
        return result
    finally:
        lock.unlink(missing_ok=True)
