from __future__ import annotations

import json
import os
from pathlib import Path

from github import gh_json


def frontier(args: dict) -> dict:
    scope = args["workspace"]
    argv = list(args["argv"])
    json_output = "--json" in argv
    argv = [arg for arg in argv if arg not in {"--json", "--force"}]
    store_arg = args.get("store_path") or os.environ.get("ORCH_STORE")
    if "--store" in argv:
        index = argv.index("--store")
        if index + 1 == len(argv):
            raise ValueError("--store requires a directory")
        store_arg = argv[index + 1]
        del argv[index:index + 2]
    if argv[:2] not in (["frontier", "set"], ["frontier", "show"]):
        raise ValueError("Upstream retired the orch CLI. Existing frontier stores support frontier set/show. "
                         "Use pstack_task, pstack_decision and pstack_checkpoint for new workflows.")
    if not store_arg:
        raise ValueError("provide an existing orch store using store_path, --store or ORCH_STORE")
    store = Path(scope) / store_arg
    path = store / "frontier.json"
    if not path.is_file():
        raise ValueError("no existing frontier.json in the selected orch store")
    if argv == ["frontier", "show"]:
        saved = json.loads(path.read_text())
        if json_output:
            output = json.dumps(saved, indent=2)
        else:
            prs = ",".join(f"{p['branches']}#{p['pr']}@{p['sha']}:{p['state']}" for p in saved['prs']) or "none"
            lowest = saved["lowestUnmerged"] or "none"
            output = f"generation={saved['generation']} prs={prs} lowest-unmerged={lowest}"
        return {"argv": ["pstack_orch", *args["argv"]], "cwd": scope, "exit_code": 0,
                "stdout": output + "\n", "stderr": ""}
    if argv[:2] != ["frontier", "set"]:
        raise ValueError("frontier show does not accept additional arguments")
    if "--prs" not in argv or argv.index("--prs") + 1 >= len(argv):
        raise ValueError("native frontier requires an explicit frozen bottom-to-top --prs list")
    numbers = [int(x) for x in argv[argv.index("--prs") + 1].split(",")]
    if not numbers or any(n <= 0 for n in numbers) or len(set(numbers)) != len(numbers): raise ValueError("PR order must be nonempty, positive and unique")
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
        old = json.loads(path.read_text())
        result = {"generation": old.get("generation", 0) + 1, "prs": [{"pr": p["number"], "branches": p["headRefName"], "sha": p["headRefOid"], "state": p["state"]} for p in prs], "lowestUnmerged": next((p["number"] for p in prs if p["state"] == "OPEN"), None)}
        temporary = store / "frontier.json.tmp"
        temporary.write_text(json.dumps(result, indent=2) + "\n"); temporary.replace(path)
        return result
    finally:
        lock.unlink(missing_ok=True)
