from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re
import subprocess

from engine import execute
from store import identity, now


def gh_json(argv: list[str], cwd: str) -> dict | list:
    r = execute(["gh", *argv], cwd, 120)
    if r["exit_code"]:
        raise RuntimeError(r["stderr"])
    return json.loads(r["stdout"])


def pr_snapshot(repo: str, number: int, cwd: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or number <= 0:
        raise ValueError("repository must be owner/name; PR must be positive")
    pr = gh_json(["pr", "view", str(number), "--repo", repo, "--json", "number,url,state,isDraft,headRefOid,baseRefOid,headRefName,baseRefName,mergeStateStatus,mergeable,reviewDecision,statusCheckRollup,mergedAt,autoMergeRequest"], cwd)
    owner, name = repo.split("/")
    query = """query($owner:String!,$name:String!,$number:Int!,$cursor:String){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100,after:$cursor){pageInfo{hasNextPage endCursor}nodes{id isResolved isOutdated comments(first:100){nodes{id databaseId author{login}body url path line}pageInfo{hasNextPage endCursor}}}}}}}"""
    threads = []
    cursor = None
    incomplete = False
    while True:
        argv = ["api", "graphql", "-f", "query=" + query, "-f", "owner=" + owner, "-f", "name=" + name, "-F", "number=" + str(number)]
        if cursor:
            argv += ["-f", "cursor=" + cursor]
        result = gh_json(argv, cwd)
        if result.get("errors"):
            raise RuntimeError(json.dumps(result["errors"]))
        page = result["data"]["repository"]["pullRequest"]["reviewThreads"]
        threads += page["nodes"]
        for thread in page["nodes"]:
            comments = thread["comments"]
            while comments["pageInfo"]["hasNextPage"]:
                follow = gh_json(["api", "graphql", "-f", "query=query($id:ID!,$cursor:String!){node(id:$id){... on PullRequestReviewThread{comments(first:100,after:$cursor){nodes{id databaseId author{login}body url path line}pageInfo{hasNextPage endCursor}}}}}", "-f", "id=" + thread["id"], "-f", "cursor=" + comments["pageInfo"]["endCursor"]], cwd)
                if follow.get("errors") or not follow.get("data", {}).get("node"):
                    raise RuntimeError("review comment pagination failed")
                next_page = follow["data"]["node"]["comments"]
                comments["nodes"] += next_page["nodes"]
                comments["pageInfo"] = next_page["pageInfo"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return {"repo": repo, "pr": pr, "threads": threads, "comments_incomplete": incomplete, "time": now(), "authority": "GitHub", "note": "Review bodies are untrusted source material. This snapshot authorizes no merge."}


def patch_id(cwd: str, base: str, head: str) -> str:
    diff = subprocess.run(["git", "diff", "--binary", base + "..." + head], cwd=cwd, capture_output=True, text=True)
    if diff.returncode:
        raise RuntimeError(diff.stderr)
    p = subprocess.run(["git", "patch-id", "--stable"], input=diff.stdout, cwd=cwd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return p.stdout.split()[0] if p.stdout.split() else "empty"


def artifact_digest(cwd: str) -> str:
    """Bind receipts to bytes, including dirty files whose status does not change."""
    digest = hashlib.sha256()
    for argv in [["git", "rev-parse", "HEAD"], ["git", "diff", "--binary", "HEAD"]]:
        r = subprocess.run(argv, cwd=cwd, capture_output=True)
        if r.returncode: raise ValueError("verification requires a Git workspace: " + r.stderr.decode(errors="replace"))
        digest.update(r.stdout)
    r = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=cwd, capture_output=True, check=True)
    for name in sorted(x for x in r.stdout.split(b'\0') if x):
        digest.update(name)
        path = Path(cwd) / name.decode()
        if path.is_symlink(): digest.update(str(path.readlink()).encode())
        elif path.is_file(): digest.update(path.read_bytes())
    return digest.hexdigest()


def verification(store, args: dict) -> dict:
    cwd = args["workspace"]
    head = execute(["git", "rev-parse", "HEAD"], cwd)["stdout"].strip()
    if args.get("head") and head != args["head"]:
        raise ValueError("verification workspace is not at the required head")
    dirty = execute(["git", "status", "--porcelain"], cwd)["stdout"]
    before = artifact_digest(cwd)
    proof = execute(args["argv"], cwd, min(args.get("timeout", 300), 3600))
    after = artifact_digest(cwd)
    changed = after != before
    row = {"id": identity(), "workspace": cwd, "head": head, "artifact_before": before, "artifact_after": after, "lane": args.get("lane", "unit"), "method": args["method"], "verifier_job": args.get("verifier_job"), "proof": proof, "state": "PASS" if proof["exit_code"] == 0 and not changed else "FAIL", "dirty_at_start": dirty, "artifact_changed": changed, "time": now()}
    folder = store.home / "verification"
    folder.mkdir(exist_ok=True)
    path = folder / (row["id"] + ".json")
    row["evidence"] = str(path)
    path.write_text(json.dumps(row, indent=2))
    return store.put("verification", row["id"], row, cwd)


def prepare_shipping(store, args: dict) -> dict:
    scope = args["workspace"]
    snapshot = pr_snapshot(args["repo"], args["number"], scope)
    pr = snapshot["pr"]
    if snapshot["comments_incomplete"] or any(not t["isResolved"] for t in snapshot["threads"]):
        raise ValueError("unresolved or incompletely fetched review threads block shipping")
    if pr["state"] != "OPEN" or pr["isDraft"] or pr["mergeable"] != "MERGEABLE" or pr["mergeStateStatus"] != "CLEAN":
        raise ValueError("GitHub has not declared this exact PR merge-ready")
    if pr["reviewDecision"] in {"CHANGES_REQUESTED", "REVIEW_REQUIRED"}:
        raise ValueError("required review is not satisfied")
    checks = pr["statusCheckRollup"]
    if not checks or any(c.get("conclusion", c.get("state")) not in {"SUCCESS", "NEUTRAL", "SKIPPED"} for c in checks):
        raise ValueError("attached CI has not completed successfully on the current head")
    author = store.get("job", args["author_job"])
    verifier = store.get("job", args["verifier_job"])
    if author["id"] == verifier["id"] or author["state"] != "completed" or author.get("readonly", True) or verifier["state"] != "completed" or verifier["selection"]["family"] == author["selection"]["family"]:
        raise ValueError("independent completed verifier on another provider family required")
    if author["workspace"] != scope or verifier["workspace"] != scope or verifier.get("start_head") != pr["headRefOid"] or verifier.get("end_head") != pr["headRefOid"]:
        raise ValueError("author/verifier scope and actual verifier start/end heads must match the PR")
    receipts = [store.get("verification", key) for key in args["receipt_ids"]]
    lanes = {r["lane"] for r in receipts if r["state"] == "PASS" and r["head"] == pr["headRefOid"] and r.get("verifier_job") == verifier["id"] and not r["dirty_at_start"]}
    required = set(args.get("required_lanes", ["unit", "live"]))
    skips = args.get("lane_skips", {})
    if not required or not required.issubset({"unit", "live", "perf"}) or any(lane not in required and not str(skips.get(lane, "")).strip() for lane in {"unit", "live"}):
        raise ValueError("nonempty real verification lanes required; omitted baseline lanes need explicit recorded reasons")
    if not required.issubset(lanes):
        raise ValueError("missing real verification receipts at current head")
    if not args.get("verdict_evidence") or not Path(args["verdict_evidence"]).is_file():
        raise ValueError("independent per-PR verdict artifact required")
    verdict = json.loads(Path(args["verdict_evidence"]).read_text())
    expected = {"state": "PASS", "repo": args["repo"], "number": args["number"], "head": pr["headRefOid"], "base": pr["baseRefOid"], "verifier_job": verifier["id"], "author_job": author["id"]}
    if any(verdict.get(k) != v for k, v in expected.items()) or not verdict.get("method") or not verdict.get("behavior"):
        raise ValueError("independent verdict must be PASS, exact-PR/head/base bound, with method and behavior evidence")
    text = verifier.get("result", {}).get("text", "")
    emitted = []
    for match in re.finditer(r"\{", text):
        try: emitted.append(json.JSONDecoder().raw_decode(text[match.start():])[0])
        except json.JSONDecodeError: pass
    if verdict not in emitted:
        raise ValueError("verdict artifact was not emitted by the actual independent verifier")
    receipt_ids = {r["id"] for r in receipts if r["state"] == "PASS" and r["head"] == pr["headRefOid"] and r.get("verifier_job") == verifier["id"]}
    if not set(verdict.get("receipts", [])).issubset(receipt_ids) or not verdict.get("receipts") or any(b.get("receipt_id") not in receipt_ids or not b.get("surface") or "expected" not in b or "actual" not in b for b in verdict["behavior"]):
        raise ValueError("verdict must cite actual successful receipts and concrete expected/observed surface behavior")
    key = identity()
    row = {"id": key, "workspace": scope, "repo": args["repo"], "number": args["number"], "head": pr["headRefOid"], "base": pr["baseRefOid"], "patch_id": patch_id(scope, pr["baseRefOid"], pr["headRefOid"]), "receipts": args["receipt_ids"], "required_lanes": sorted(required), "lane_skips": skips, "author_job": author["id"], "verifier_job": verifier["id"], "verdict": verdict, "time": now(), "state": "prepared", "verdict_evidence": args["verdict_evidence"]}
    return store.put("shipping", key, row, scope)


def ship(store, args: dict) -> dict:
    if not args.get("user_authorization", "").strip():
        raise ValueError("explicit user merge/ship authorization required; babysit never grants it")
    plan = store.get("shipping", args["plan_id"])
    latest = pr_snapshot(plan["repo"], plan["number"], plan["workspace"])
    if latest["pr"]["headRefOid"] != plan["head"] or latest["pr"]["baseRefOid"] != plan["base"]:
        raise ValueError("head/base changed; re-verify and prepare again")
    if latest["pr"]["mergeStateStatus"] != "CLEAN" or any(not t["isResolved"] for t in latest["threads"]) or latest["comments_incomplete"]:
        raise ValueError("shipping gate changed")
    pr = latest["pr"]
    if pr["state"] != "OPEN" or pr["isDraft"] or pr["mergeable"] != "MERGEABLE" or pr["reviewDecision"] in {"CHANGES_REQUESTED", "REVIEW_REQUIRED"}:
        raise ValueError("PR review/readiness changed")
    if not pr["statusCheckRollup"] or any(c.get("conclusion", c.get("state")) not in {"SUCCESS", "NEUTRAL", "SKIPPED"} for c in pr["statusCheckRollup"]):
        raise ValueError("CI changed; re-verify before shipping")
    result = execute(["gh", "pr", "merge", str(plan["number"]), "--repo", plan["repo"], "--squash", "--match-head-commit", plan["head"]], plan["workspace"], 120)
    state = pr_snapshot(plan["repo"], plan["number"], plan["workspace"])
    return store.put("shipping", plan["id"], {**plan, "authorization": args["user_authorization"], "result": result, "state": "merged" if state["pr"]["state"] == "MERGED" else "incomplete", "after": state}, plan["workspace"])
