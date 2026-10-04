from __future__ import annotations

from frontier import frontier
from worktrees import audit, cleanup
import time

import json
from pathlib import Path
import re

import benny
import artifacts
from controls import Controls
from engine import Engine, execute
import github
import providers
import harnesses
from store import ROOT, Store, identity, now, workspace

DESCRIPTION = {
    "environment": "Environment-local harness discovery and native agent planning. Actions scan/preferences/setup/catalog/budget/configure/plan/record/jobs. Discovery reads executable presence only. preferences reports the user's chosen budget or requires_budget_choice; no default budget is selected. setup host auto/local/cloud, mode native/local-cli, enabled_cli,confirmation. Native is default; cloud always native OpenAI. catalog models and source must come from actual host tools. budget stores budget,confirmation; configure stores all 17 roles,confirmation. plan role,seats,require_cross_provider requires a chosen budget. record workspace,native_id,state,evidence saves actual host results, never dispatches. No remote connection.",
    "artifact": "Read actual scoped runtime evidence, including image pixels. Action get data workspace,kind(job/control/verification),id,name optional. Without name lists owned files. Only runtime-owned evidence sets are accessible; private credentials/state are excluded. Images return native MCP image content; recordings/traces return embedded resources. Maximum artifact size is 8 MiB.",
    "worktree": "Audit Git worktrees without scanning unrelated Cursor histories. Actions audit/cleanup. data workspace; cleanup path,user_authorization. Cleanup only clean inactive runtime-owned trees. Native app-managed trees must use archive_worktree for recoverable snapshots.",
    "context": "Sticky poteto-mode, task-to-playbook selection, persistent per-role models and session context. Actions get/activate/deactivate/select. data: workspace; optional session, playbook, prompt. activate requires explicit user mode request. Read returned playbook and leaf principles.",
    "models": "Current native host catalog or explicitly selected local provider discovery and live inference probes. Actions discover/list/probe. probe data: provider (codex/claude/grok/gemini), model, effort; requires enabled local adapter. grok uses authenticated Grok Build CLI. Direct API providers are disabled. Explicit CLI selector/backend identities are checked. No fallback. Catalog presence alone is not verification.",
    "config": "Persistent pstack model/budget configuration outside the plugin cache. Actions get/set. set data: budget (unlimited/large/medium/small), roles mapping ALL upstream role labels to lists of provider:model keys or auto/inherit-parent, confirmation from user's explicit selection. Never choose budget or roles silently.",
    "agent": "Durable detached agents, coordination, reuse and cancellation. Actions spawn/get/list/wait/resume/cancel/message/inbox. spawn data: workspace,prompt,role,seat,readonly,agent_type,context_paths,timeout,ref; optional image_paths attaches scoped images through native Codex image input. Other providers image inputs are not silently substituted. Writers use separate Git worktrees. get/wait/resume/cancel data id; resume prompt. message data workspace,from,to,text. For in-flight messages recipient reads inbox; resume injects pending mail. Never claim immediate steering of a running native inference.",
    "panel": "Distinct verified model/provider panels for arena, architect and adversarial review. Actions start/results/record. start data workspace,prompt,role (arena runners/architect runners/interrogate reviewers),kind,readonly,rubric,require_cross_provider. results id. record id,synthesis,evidence,verification_ids. Parent reads all results, scores rubric, deduplicates, judges and verifies. Repeated calls to one model cannot satisfy diverse review.",
    "task": "Persistent dependency-aware task list, upstream playbook steps and explicit skips. Actions start/add/set/list. start data workspace,playbook. add workspace,title,depends_on. set id,state (pending/running/done/skipped/blocked),evidence or reason. Evidence required for done; preserve skipped steps.",
    "decision": "Append-only auditable decision trail. Actions append/list/export. append data workspace,phase,decision,why,evidence,result. Audit evidence against scoped history; export returns TSV path.",
    "checkpoint": "Interrupted-work recovery and scoped event history. Actions save/get/list/recover/history. save data workspace,intent,progress,verified,next_steps,key_files,gotchas. recover data workspace returns checkpoints, tasks, jobs, loops, history. Reverify inherited claims.",
    "loop": "Durable /loop equivalent, event wake plus heartbeat, continuation and explicit stop conditions. Actions start/get/list/pause/resume/cancel. start data workspace,prompt,done_command (argv; exit 0 means DONE),max_seconds,max_iterations,role,readonly,interval_seconds; optional wake_command and heartbeat_seconds. Budget exhaustion is BLOCKED. Never relax predicate. pause/cancel kill active owner and watcher.",
    "verify": "Run real commands and save receipts pinned to actual repository HEAD. Action run data workspace,argv,method,lane(unit/live/perf),head,verifier_job,timeout. Action get id. Compilation is not live verification; choose actual user surface and expected proof.",
    "pr": "GitHub snapshot, exact-head CI/review threads, upstream watch-pr monitoring and gated authorized shipping. Actions snapshot/watch/prepare/ship. snapshot/watch workspace,repo owner/name,number; watch mode check/drive/background/threads-only and timeout. prepare author_job,verifier_job,receipt_ids,verdict_evidence,required_lanes. ship plan_id,user_authorization. Babysit never grants merge authority; shipping must process stack bottom-up.",
    "orch": "Preserved upstream orchestration CLI for units, standing orders, inbox, gates and verification ledger. Action run data workspace,argv,store_path optional. Native frontier adapter uses GitHub PRs and supplied bottom-to-top order instead of mandatory Graphite. argv is an argument list, not shell text.",
    "control_cli": "Persistent PTY harness. Actions start/snapshot/send/resize/stop. start workspace,argv. Others id. send text,after_snapshot digest. snapshot pattern,wait_seconds. Each action captures real transcript and saves evidence; resize rows,columns.",
    "control_ui": "Persistent Playwright/Chrome or Electron CDP harness with fresh snapshots, screenshots, traces, video and profiling. Actions start/snapshot/click/fill/press/navigate/resize/inspect/profile-start/profile-stop/heap/stop. start workspace,url,record_video; or cdp_url,marker. Workspace is required for Benny-owned captures. Structural action id,after_snapshot,selector,text/key/url. inspect reads state without forcing it.",
    "benny": "Benny immutable-thread coordination and actual reproduction/fix gates. Actions setup/get/plan/ingest/verdict/acknowledge/repro_gate/evidence/launch/confirm_repro/fix_gate/draft_gate/reconsider/cancel/runs. setup requires repository,default_branch,source_channel,triage_identity,tracker,control_skill,feature_map,four verified model roles and eight explicit budgets. plan workspace,configuration_path validates committed inputs and returns two native schedule prompts. evidence id,phase(baseline/patched),control_id,expected,broken consumes actual workspace-owned completed UI recordings at configured control_url. launch id,role,prompt dispatches an isolated model worker; media_review uses native Codex image attachments. confirm_repro id requires two distinct recordings and actual media verdict. fix_gate id,parent_preflight,root_cause_evidence enforces rejection window/ownership and one fix. draft_gate id,receipt_ids requires actual before/after UI and pinned unit/live proof. Native coordinator alone delivers outbox in the original thread; no worker gets posting credentials. Real connector activation remains explicit.",
}
ACTIONS = {
    "environment": ["scan", "preferences", "setup", "catalog", "budget", "configure", "plan", "record", "jobs"],
    "artifact": ["get"],
    "worktree": ["audit", "cleanup"],
    "context": ["get", "activate", "deactivate", "select"], "models": ["discover", "list", "probe"], "config": ["get", "set"], "agent": ["spawn", "get", "list", "wait", "resume", "cancel", "message", "inbox"], "panel": ["start", "results", "record"], "task": ["start", "add", "set", "list"], "decision": ["append", "list", "export"], "checkpoint": ["save", "get", "list", "recover", "history"], "loop": ["start", "arm_foreground", "get", "list", "pause", "resume", "cancel"], "verify": ["run", "get"], "pr": ["snapshot", "watch", "prepare", "ship"], "orch": ["run"], "control_cli": ["start", "snapshot", "send", "resize", "stop"], "control_ui": ["start", "snapshot", "click", "fill", "press", "navigate", "resize", "inspect", "profile-start", "profile-stop", "heap", "stop"], "benny": ["setup", "get", "plan", "ingest", "verdict", "acknowledge", "repro_gate", "evidence", "launch", "confirm_repro", "fix_gate", "draft_gate", "reconsider", "cancel", "runs"],
}


def tools_list() -> list[dict]:
    return [{"name": "pstack_" + name, "description": description, "inputSchema": {"type": "object", "properties": {"action": {"type": "string", "enum": ACTIONS[name]}, "data": {"type": "object", "description": "Action parameters described in the tool documentation."}}, "required": ["action", "data"], "additionalProperties": False}} for name, description in DESCRIPTION.items()]


def select_playbook(prompt: str) -> str:
    patterns = [(r"pause|suspend|stop safely", "pause-safely"), (r"resume|pick.?up|interrupted", "session-pickup"), (r"autopilot.?stack", "autopilot-stack"), (r"autopilot.?full", "autopilot-full"), (r"orchestrat|multi.day|whole project", "orchestrate"), (r"ship|land|merge.*stack", "shipping"), (r"pr\b.*status|babysit|review comments|\bci\b|merge.ready", "babysit"), (r"trace|cpuprofile|heap snapshot|spindump", "trace-forensics"), (r"leak|idle.cpu|live symptom", "runtime-forensics"), (r"hillclimb|metric.*target|at least.*iterations", "hillclimb"), (r"perf|slow|latency", "perf-issue"), (r"bug|broken|defect|repro", "bug-fix"), (r"refactor|rename|behavior.preserv", "refactoring"), (r"pixel|visual parity", "visual-parity"), (r"prototype|sketch|mock", "prototype"), (r"skill\.md|author.*skill", "authoring-a-skill"), (r"eval|blinded", "eval"), (r"worktree.*clean|prune|reclaim disk", "worktree-cleanup"), (r"multi.phase|stacked.*pr", "multi-phase-plan"), (r"loop|until done|long.running|autonomous", "autonomous-run"), (r"how|why|read.only|investigat|are we sure", "investigation")]
    return next((book for pattern, book in patterns if re.search(pattern, prompt, re.I)), "feature")


def context(store: Store, args: dict, action="get") -> dict:
    scope = workspace(args["workspace"])
    key = scope + "::" + args.get("session", "workspace")
    candidates = [x for x in store.list("mode", scope) if x["id"] in {scope + "::workspace", key}]
    mode = next((x for x in candidates if x["id"] == key), candidates[-1] if candidates else None) or {"id": key, "workspace": scope, "enabled": False}
    if action in {"activate", "deactivate"}:
        mode = {**mode, "id": key, "enabled": action == "activate", "playbook": args.get("playbook") or select_playbook(args.get("prompt", "")), "updated": now()}
        store.put("mode", key, mode, scope)
    book = args.get("playbook") or (select_playbook(args["prompt"]) if args.get("prompt") else mode.get("playbook", "feature"))
    path = ROOT / "skills/poteto-mode/playbooks" / (book + ".md")
    if not path.exists():
        raise ValueError("unknown playbook")
    try:
        config = store.get("config", "models")
    except KeyError:
        config = {"state": "unconfigured", "required_action": "Run setup-pstack and read environment preferences for the chosen native budget. Configure optional CLI roles only if selected. Do not infer unavailable defaults."}
    text = path.read_text()
    steps = re.findall(r"^\d+\. (.*)", text, re.M)
    if not steps:
        steps = re.findall(r"^\*\*[^\n]+", text, re.M)
    result = {"mode": mode, "selected_playbook": book, "playbook_path": str(path), "steps": steps, "config": config, "adapter_contract": str(ROOT / "references/runtime-contract.md"), "note": "A new task reselects its playbook; active mode survives turns and compaction. Casual turns and explicit opt-out skip the workflow."}
    result["execution"] = harnesses.settings(store)
    result["preferences"] = harnesses.preferences(store)
    result["configuration_note"] = "Saved CLI role preferences are inactive in native mode; use environment plan with the current host catalog."
    if args.get("include_content"):
        result["playbook_text"] = text
        result["adapter_contract_text"] = (ROOT / "references/runtime-contract.md").read_text()
        result["leaf_principles"] = {name: (ROOT / "skills" / name / "SKILL.md").read_text() for name in sorted(set(re.findall(r"\bprinciple-[a-z0-9-]+\b", text))) if (ROOT / "skills" / name / "SKILL.md").is_file()}
    return result


class API:
    def __init__(self, store: Store):
        self.store = store
        self._engine = None
        self.controls = Controls(store.home)

    @property
    def engine(self):
        if self._engine is None:
            self._engine = Engine(self.store)
        return self._engine

    def call(self, name: str, action: str, args: dict):
        op = name.removeprefix("pstack_")
        if op not in ACTIONS or action not in ACTIONS[op]:
            raise ValueError("unknown tool/action")
        if "workspace" in args:
            args = {**args, "workspace": workspace(args["workspace"])}
        scope = args.get("workspace", "")
        if op == "loop" and action in {"start", "resume", "arm_foreground"} and harnesses.settings(self.store)["mode"] == "native":
            raise ValueError("Use native host continuation; local CLI loops are disabled")
        if op == "environment":
            data = {k: v for k, v in args.items() if k != "workspace"}
            if action == "scan": return harnesses.scan(self.store)
            if action == "preferences": return harnesses.preferences(self.store)
            if action == "setup": return harnesses.setup(self.store, **data)
            if action == "catalog": return harnesses.catalog(self.store, **data)
            if action == "budget": return harnesses.budget(self.store, **data)
            if action == "configure": return harnesses.configure_native(self.store, allowed_roles=providers.ROLES, panel_roles=providers.PANELS, **data)
            if action == "plan": return harnesses.native_plan(self.store, **data)
            if action == "record": return harnesses.native_record(self.store, args)
            return self.store.list("native_job", scope)
        if op == "artifact": return artifacts.read(self.store, args)
        if op == "worktree":

            return audit(self.store, scope) if action == "audit" else cleanup(self.store, args)
        if op == "context":
            return context(self.store, args, action)
        if op == "models":
            if action == "discover": return providers.discover(self.store)
            if action == "probe": return providers.probe(self.store, **{k: v for k, v in args.items() if k != 'workspace'})
            return self.store.list("model")
        if op == "config":
            return providers.configure(self.store, **{k: v for k, v in args.items() if k != 'workspace'}) if action == "set" else self.store.get("config", "models")
        if op == "agent":
            if action == "spawn": return self.engine.spawn(args)
            if action == "get": return self.store.get("job", args["id"])
            if action == "list": return self.store.list("job", scope)
            if action == "wait": return self.engine.wait(args["id"], args.get("seconds", 30))
            if action == "resume": return self.engine.resume(args["id"], args["prompt"])
            if action == "cancel": return self.engine.cancel(args["id"])
            if action == "message":
                recipient = self.store.get("job", args["to"])
                if recipient["workspace"] != scope:
                    raise ValueError("message recipient is outside the declared workspace")
                key = identity()
                return self.store.put("message", key, {**args, "id": key, "time": now(), "read": False}, scope)
            return [x for x in self.store.list("message", scope) if x.get("to") == args["to"]]
        if op == "panel":
            if action == "start": return self.engine.panel(args)
            if action == "results": return self.engine.panel_results(args["id"])
            row = self.engine.panel_results(args["id"])
            if row["state"] != "completed": raise ValueError("every required panel seat must complete")
            for key in args.get("verification_ids", []):
                if self.store.get("verification", key)["state"] != "PASS": raise ValueError("synthesis verification failed")
            if row["kind"] in {"arena", "generation"} and not args.get("verification_ids"):
                raise ValueError("arena synthesis requires real verification receipts")
            return self.store.put("panel", row["id"], {**row, "synthesis": args["synthesis"], "evidence": args["evidence"], "verification_ids": args.get("verification_ids", []), "state": "synthesized"}, row["workspace"])
        if op == "task":
            if action == "list": return self.store.list("task", scope)
            if action == "start":
                ctx = context(self.store, args)
                return [self.call("pstack_task", "add", {"workspace": scope, "title": step, "playbook": ctx["selected_playbook"], "index": i}) for i, step in enumerate(ctx["steps"])]
            if action == "add":
                return self.store.put("task", ident := identity(), {**args, "id": ident, "state": "pending", "created": now(), "depends_on": args.get("depends_on", [])}, scope)
            row = self.store.get("task", args["id"])
            state = args["state"]
            if state not in {"pending", "running", "done", "skipped", "blocked"}: raise ValueError("invalid task state")
            if state == "done" and not args.get("evidence"): raise ValueError("done requires evidence")
            if state in {"skipped", "blocked"} and not args.get("reason"): raise ValueError("skip/block requires a reason")
            if state in {"running", "done"} and any(self.store.get("task", dep)["state"] not in {"done", "skipped"} for dep in row["depends_on"]): raise ValueError("task dependencies are unfinished")
            return self.store.put("task", row["id"], {**row, **args, "updated": now()}, row["workspace"])
        if op == "decision":
            if action == "append":
                for key in ["phase", "decision", "why", "evidence", "result"]:
                    if key not in args: raise ValueError("missing decision " + key)
                return self.store.event("decision", args, scope)
            if action == "export": return {"path": self.store.decisions(scope)}
            return [e for e in self.store.history(scope) if e["kind"] == "decision"]
        if op == "checkpoint":
            if action == "save":
                return self.store.put("checkpoint", ident := identity(), {**args, "id": ident, "time": now()}, scope)
            if action == "get": return self.store.get("checkpoint", args["id"])
            if action == "list": return self.store.list("checkpoint", scope)
            if action == "history": return self.store.history(scope, args.get("after", 0))
            return {k: self.store.list(kind, scope) for k, kind in [("checkpoints", "checkpoint"), ("tasks", "task"), ("jobs", "job"), ("loops", "loop"), ("native_jobs", "native_job")]} | {"history": self.store.history(scope), "instruction": "Read latest checkpoint and artifacts. Verify inherited claims on the current head before resuming."}
        if op == "loop":
            if action == "arm_foreground":

                if not args.get("session") or not args.get("done_command") or args.get("max_seconds", 0) <= 0 or args.get("max_iterations", 0) <= 0:
                    raise ValueError("foreground continuation requires session, predicate and explicit budgets")
                return self.store.put("foreground", key := identity(), {**args, "id": key, "state": "running", "iteration": 0, "started_at": time.time()}, scope)
            if action == "start": return self.engine.loop_start(args)
            if action == "get":
                try: return self.store.get("loop", args["id"])
                except KeyError: return self.store.get("foreground", args["id"])
            if action == "list": return self.store.list("loop", scope)
            if action == "resume": return self.engine.loop_resume(args["id"])
            try: self.store.get("loop", args["id"])
            except KeyError:
                row = self.store.get("foreground", args["id"])
                return self.store.put("foreground", row["id"], {**row, "state": "paused" if action == "pause" else "cancelled"}, row["workspace"])
            return self.engine.loop_stop(args["id"], "paused" if action == "pause" else "cancelled")
        if op == "verify": return github.verification(self.store, args) if action == "run" else self.store.get("verification", args["id"])
        if op == "pr":
            if action == "snapshot": return github.pr_snapshot(args["repo"], args["number"], scope)
            if action == "prepare": return github.prepare_shipping(self.store, args)
            if action == "ship": return github.ship(self.store, args)
            owner, repo = args["repo"].split("/")
            argv = ["bun", str(ROOT / "skills/poteto-mode/scripts/watch-pr/watch-pr"), "--owner", owner, "--repo", repo, "--pr", str(args["number"])]
            mode = args.get("mode", "check")
            if mode in {"check", "threads-only"}: argv += ["--status-only"]
            else: argv += ["--timeout", str(args.get("timeout", 300))]
            if args.get("stack_prs"): argv += ["--queued-stack", "--stack-prs", ",".join(map(str, args["stack_prs"]))]
            if mode == "background":
                return self.engine.command_job(scope, argv, args.get("timeout", 300) + 15)
            return execute(argv, scope, args.get("timeout", 300) + 15)
        if op == "orch":
            argv = args["argv"]
            prefix = 0
            while prefix < len(argv) and argv[prefix] in {"--json", "--force"}: prefix += 1
            if argv[prefix:prefix + 2] == ["frontier", "set"]:

                return frontier(args)
            command = ["bun", str(ROOT / "skills/poteto-mode/scripts/orch/orch.ts")]
            if args.get("store_path"): command += ["--store", args["store_path"]]
            return execute(command + argv, scope)
        if op == "control_cli": return self.controls.cli(action, args)
        if op == "control_ui": return self.controls.ui(action, args)
        if op == "benny":
            if action == "setup": return benny.setup(self.store, args)
            if action == "get": return self.store.get("benny", scope)
            if action == "runs": return self.store.list("benny_run", scope)
            if action in {"launch", "cancel"}: return getattr(benny, action)(self.store, args, self.engine)
            return getattr(benny, action)(self.store, args)
        raise ValueError("unhandled operation")
