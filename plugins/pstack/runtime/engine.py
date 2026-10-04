from __future__ import annotations

from xai_worker import credential

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time
import uuid

import providers
import harnesses
from store import ROOT, Store, identity, now, workspace

TERMINAL = {"completed", "failed", "cancelled", "interrupted", "blocked"}


def execute(argv: list[str], cwd: str, timeout: float = 60) -> dict:
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) for x in argv):
        raise ValueError("command must be a nonempty argument array; shell strings are unsupported")
    p = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
        code = p.returncode
    except subprocess.TimeoutExpired:
        Engine.terminate(p)
        stdout, stderr = p.communicate()
        code = 124
        stderr += "\ncommand timeout; process group terminated"
    return {"argv": argv, "cwd": cwd, "exit_code": code, "stdout": stdout[-100000:], "stderr": stderr[-15000:], "time": now()}


class Engine:
    def __init__(self, store: Store):
        self.owner_lock = open(store.home / "engine.lock", "a")
        try: fcntl.flock(self.owner_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.owner_lock.close()
            raise RuntimeError("another engine owns this runtime store")
        self.store = store
        self.lock = threading.RLock()
        self.processes: dict[str, subprocess.Popen] = {}
        self.slots = threading.Semaphore(4)
        self.recover()

    def save(self, kind: str, row: dict) -> dict:
        return self.store.put(kind, row["id"], row, row.get("workspace", ""))

    def update(self, kind: str, key: str, **changes) -> dict:
        with self.lock:
            row = self.store.get(kind, key)
            return self.save(kind, {**row, **changes, "updated": now()})

    def recover(self):
        for j in self.store.list("job"):
            if j["state"] not in {"running", "queued"}:
                continue
            pid = j.get("pid")
            if pid and j.get("process_identity"):
                current = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True).stdout.strip()
                if current == j["process_identity"]:
                    try:
                        os.killpg(pid, signal.SIGTERM)
                        deadline = time.monotonic() + 3
                        while time.monotonic() < deadline:
                            try: os.killpg(pid, 0)
                            except ProcessLookupError: break
                            time.sleep(.05)
                        else:
                            os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            events = Path(j["events"])
            if events.exists() and j.get("selection"):
                try:
                    parsed = providers.parse_output(j["selection"]["provider"], events.read_text())
                    j["session"] = parsed.get("session") or j.get("session")
                except (ValueError, KeyError):
                    pass
            self.save("job", {**j, "state": "interrupted", "updated": now(), "recovery": "supervisor restarted; old process reconciled; resume explicitly"})
        for loop in self.store.list("loop"):
            if loop["state"] in {"running", "recovering"}:
                if harnesses.settings(self.store)["mode"] == "native":
                    self.update("loop", loop["id"], state="blocked", stop_reason="Execution policy is native; resume in the current host from its checkpoint")
                    continue
                epoch = loop.get("generation", 0) + 1
                self.update("loop", loop["id"], state="recovering", generation=epoch, recovery_count=loop.get("recovery_count", 0) + 1)
                threading.Thread(target=self.run_loop, args=(loop["id"], epoch), daemon=True).start()

    def spawn(self, args: dict) -> dict:
        scope = workspace(args["workspace"])
        prompt = args["prompt"]
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt is required")
        role = args.get("role", "swarm workers")
        if args.get("reuse_job_id"):
            old = self.store.get("job", args["reuse_job_id"])
            if old["workspace"] != scope:
                raise ValueError("reused agent must remain in its original workspace")
            model = old["selection"]
        elif args.get("_selection"):
            model = args["_selection"]
            entry = self.store.get("model", model["provider"] + ":" + model["model"])
            if not entry.get("verified") or model["effort"] not in entry["efforts"] or model["family"] != entry["family"]:
                raise ValueError("pinned owner model has not been verified")
        else:
            model = providers.selection(self.store, role, args.get("seat", 0), args.get("parent"))
        harnesses.require_cli(self.store, model["provider"])
        readonly = args.get("readonly", True)
        images = args.get("image_paths", [])
        if images and (model['provider'] != 'codex' or not isinstance(images, list) or len(images) > 4):
            raise ValueError('native image input is verified only for Codex, up to four images')
        image_paths = []
        for image in images:
            image = Path(image).resolve(strict=True)
            in_scope = image.is_relative_to(Path(scope))
            controls = (self.store.home / 'controls').resolve()
            if image.is_relative_to(controls):
                control_id = image.relative_to(controls).parts[0]
                owner = controls / control_id / 'owner.json'
                in_scope = owner.is_file() and json.loads(owner.read_text()).get('workspace') == scope
            if not in_scope or image.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'} or image.stat().st_size > 10 * 1024 * 1024:
                raise ValueError('image must be a scoped image file or owned control artifact, at most 10 MiB')
            image_paths.append(str(image))
        if not readonly and model["provider"] == "grok" and model["model"] not in providers.GROK_BACKENDS:
            raise ValueError("Grok writer model has not passed the workspace boundary workflow")
        key = args.get("idempotency_key")
        with self.lock:
            if key:
                existing = [x for x in self.store.list("job", scope) if x.get("idempotency_key") == key]
                if existing:
                    return existing[-1]
            ident = identity()
            cwd = scope
            if not readonly and args.get("isolate", True):
                tree = self.store.home / "worktrees" / ident
                tree.parent.mkdir(exist_ok=True)
                p = execute(["git", "worktree", "add", "--detach", str(tree), args.get("ref", "HEAD")], scope)
                if p["exit_code"]:
                    raise RuntimeError("writer isolation requires a Git repository: " + p["stderr"])
                cwd = str(tree)
            elif args.get("reuse_job_id"):
                cwd = self.store.get("job", args["reuse_job_id"])["cwd"]
            if not readonly and any(j["cwd"] == cwd and not j["readonly"] and j["state"] in {"queued", "running"} for j in self.store.list("job")):
                raise ValueError("another writer already owns this workspace")
            paths = args.get("context_paths", [])
            for path in paths:
                resolved = (Path(scope) / path).resolve(strict=True)
                if not resolved.is_relative_to(Path(scope)):
                    raise ValueError("context must stay in the declared workspace")
            pointers = "\n".join(str((Path(scope) / p).resolve()) for p in paths)
            mode = self.store.list("mode", scope)
            instructions = (ROOT / "references/worker-contract.md").read_text()
            if args.get("agent_type"):
                kind = args["agent_type"]
                skill = "agent-" + kind.removeprefix("agent-")
                if kind in {"generalPurpose", "default", "explorer", "worker"}:
                    skill = None
                if skill and (not re.fullmatch(r"[a-z0-9-]+", skill) or not (ROOT / "skills" / skill / "SKILL.md").is_file()):
                    raise ValueError("unknown bundled agent type")
                if skill:
                    instructions += "\nRead this agent skill in full before work: " + str(ROOT / "skills" / skill / "SKILL.md")
            if mode and mode[-1].get("enabled"):
                instructions += "\nPoteto mode is active. Read the playbook at " + str(ROOT / "skills/poteto-mode/playbooks" / (mode[-1].get("playbook", "feature") + ".md"))
            folder = self.store.home / "jobs" / ident
            folder.mkdir(parents=True)
            row = {"id": ident, "workspace": scope, "cwd": cwd, "prompt": prompt, "instructions": instructions, "context_paths": pointers, "role": role, "seat": args.get("seat", 0), "selection": model, "readonly": readonly, "state": "queued", "session": args.get("session"), "created": now(), "updated": now(), "events": str(folder / "events.jsonl"), "stderr": str(folder / "stderr.txt"), "result_path": str(folder / "result.json"), "timeout": min(max(float(args.get("timeout", 1800)), 1), 86400), "idempotency_key": key, "parent_id": args.get("parent_id")}
            row['image_paths'] = image_paths
            if model["provider"] == "grok" and not row["session"]:
                row["session"] = str(uuid.uuid4())
                row["native_session_new"] = True
            self.save("job", row)
            self.store.event("agent_spawn", {"job": ident, "role": role, "selection": model, "readonly": readonly}, scope)
        threading.Thread(target=self.run_job, args=(ident,), daemon=True).start()
        return row

    def run_job(self, key: str):
        with self.slots:
            j = self.store.get("job", key)
            if j["state"] == "cancelled":
                return
            prompt = j["instructions"] + "\n\nTask:\n" + j["prompt"] + "\nContext file pointers:\n" + j["context_paths"]
            try:
                if not j.get("command"):
                    harnesses.require_cli(self.store, j["selection"]["provider"])
                cmd = j.get("command") or providers.command(j["selection"], prompt, j["readonly"], None if j.get("native_session_new") else j.get("session"))
                for image in j.get('image_paths', []):
                    cmd += ['--image', image]
                if j.get("native_session_new"):
                    cmd += ["--session-id", j["session"]]
                with open(j["events"], "a") as output, open(j["stderr"], "a") as error:
                    env = providers.grok_env() if j.get("selection", {}).get("provider") == "grok" else providers.safe_env()
                    if j.get("selection", {}).get("provider") == "xai":

                        env["XAI_API_KEY"] = credential()
                    with self.lock:
                        if self.store.get("job", key)["state"] != "queued":
                            return
                        start_head = execute(["git", "rev-parse", "HEAD"], j["cwd"])["stdout"].strip() or None
                        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=output, stderr=error, cwd=j["cwd"], env=env, start_new_session=True)
                        self.processes[key] = p
                        started = subprocess.run(["ps", "-p", str(p.pid), "-o", "lstart="], capture_output=True, text=True).stdout.strip()
                        self.update("job", key, state="running", pid=p.pid, process_identity=started, start_head=start_head, supervisor_pid=os.getpid())
                    try:
                        code = p.wait(j["timeout"])
                    except subprocess.TimeoutExpired:
                        self.terminate(p)
                        raise TimeoutError("agent execution budget exhausted")
                parsed = {"text": Path(j["events"]).read_text(), "completed": code == 0, "errors": []} if j.get("command") else providers.parse_output(j["selection"]["provider"], Path(j["events"]).read_text())
                if not j.get("command") and not providers.model_matches(j["selection"]["provider"], j["selection"]["model"], parsed):
                    parsed["completed"] = False
                    parsed["errors"] = ["actual provider model differs from configured model"]
                if not j.get("command") and not providers.effort_applied(j["selection"]["provider"], Path(j["stderr"]).read_text()):
                    parsed["completed"] = False
                    parsed["errors"] = ["provider ignored the requested reasoning effort"]
                if j.get("selection", {}).get("provider") == "grok" and parsed.get("session") != j.get("session"):
                    parsed["completed"] = False
                    parsed["errors"] = ["actual Grok session differs from the persisted session identity"]
                Path(j["result_path"]).write_text(json.dumps(parsed, indent=2))
                with self.lock:
                    current = self.store.get("job", key)
                    state = "cancelled" if current["state"] == "cancelled" else "completed" if code == 0 and parsed["completed"] else "failed"
                    self.update("job", key, state=state, exit_code=code, session=parsed.get("session") or j.get("session"), result=parsed, finished=now(), end_head=execute(["git", "rev-parse", "HEAD"], j["cwd"])["stdout"].strip() or None)
                self.store.event("agent_result", {"job": key, "state": state, "evidence": j["result_path"]}, j["workspace"])
                self.store.put("message", identity(), {"from": key, "to": j.get("parent_id") or "coordinator", "workspace": j["workspace"], "time": now(), "text": "agent " + state, "evidence": j["result_path"], "read": False}, j["workspace"])
            except Exception as e:
                with self.lock:
                    state = "cancelled" if self.store.get("job", key)["state"] == "cancelled" else "failed"
                    parsed = {"completed": False, "text": "", "errors": [str(e)]}
                    Path(j["result_path"]).write_text(json.dumps(parsed, indent=2))
                    self.update("job", key, state=state, error=str(e), result=parsed, finished=now())
                self.store.event("agent_result", {"job": key, "state": state, "evidence": j["result_path"]}, j["workspace"])
                self.store.put("message", identity(), {"from": key, "to": j.get("parent_id") or "coordinator", "workspace": j["workspace"], "time": now(), "text": "agent " + state, "evidence": j["result_path"], "read": False}, j["workspace"])
            finally:
                self.processes.pop(key, None)

    @staticmethod
    def terminate(p):
        if p.poll() is not None:
            return
        try:
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(3)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
        except ProcessLookupError:
            pass

    def cancel(self, key: str) -> dict:
        with self.lock:
            row = self.store.get("job", key)
            if row["state"] in TERMINAL:
                return row
            row = self.update("job", key, state="cancelled")
            p = self.processes.get(key)
            if p:
                self.terminate(p)
            return row

    def resume(self, key: str, prompt: str) -> dict:
        j = self.store.get("job", key)
        if j["state"] not in TERMINAL:
            raise ValueError("cannot resume a running agent; send a durable message or cancel first")
        if not j.get("session"):
            raise ValueError("no native session ID was saved; use checkpoint recovery with a fresh agent")
        mail = [m for m in self.store.list("message", j["workspace"]) if m.get("to") == key and not m.get("read")]
        consolidated = prompt + "\nPending coordinator messages: " + json.dumps(mail) + "\nSaved role and ownership still apply."
        result = self.spawn({"workspace": j["workspace"], "prompt": consolidated, "role": j["role"], "seat": j.get("seat", 0), "session": j["session"], "readonly": j["readonly"], "isolate": False, "reuse_job_id": key, "parent_id": j.get("parent_id") or "coordinator", "timeout": j["timeout"]})
        for m in mail:
            self.store.put("message", m["id"], {**m, "read": True, "delivered_to": result["id"]}, j["workspace"])
            self.store.event("message_delivery", {"from": m.get("from"), "to": result["id"], "text": m["text"]}, j["workspace"])
        return result

    def command_job(self, scope: str, argv: list[str], timeout: float) -> dict:
        key = identity()
        folder = self.store.home / "jobs" / key
        folder.mkdir(parents=True)
        row = {"id": key, "workspace": scope, "cwd": scope, "command": argv, "role": "PR event watcher", "readonly": True, "prompt": "", "instructions": "", "context_paths": "", "state": "queued", "created": now(), "updated": now(), "events": str(folder / "events.jsonl"), "stderr": str(folder / "stderr.txt"), "result_path": str(folder / "result.json"), "timeout": timeout}
        self.save("job", row)
        threading.Thread(target=self.run_job, args=(key,), daemon=True).start()
        return row

    def wait(self, key: str, seconds: float = 30) -> dict:
        deadline = time.monotonic() + min(seconds, 55)
        while time.monotonic() < deadline:
            row = self.store.get("job", key)
            if row["state"] in TERMINAL:
                return row
            time.sleep(.1)
        return self.store.get("job", key)

    def panel(self, args: dict) -> dict:
        role = args.get("role", "interrogate reviewers")
        if role not in providers.PANELS:
            raise ValueError("panel role required")
        seats = self.store.get("config", "models")["roles"][role]
        models = [providers.selection(self.store, role, i, args.get("parent")) for i in range(len(seats))]
        families = {m["family"] for m in models}
        if args.get("require_cross_provider", True) and len(families) < 2:
            raise ValueError("cross-provider review requires at least two verified provider families")
        if len({(m["provider"], m["model"]) for m in models}) < 2 and args.get("kind", "review") != "generation":
            raise ValueError("one repeated model is not a diverse review panel")
        request_key = args.get("idempotency_key")
        with self.lock:
            if request_key:
                existing = [p for p in self.store.list("panel", workspace(args["workspace"])) if p.get("idempotency_key") == request_key]
                if existing: return existing[-1]
            key = identity()
            jobs = [self.spawn({**args, "idempotency_key": (request_key + ":seat:" + str(i)) if request_key else None, "role": role, "seat": i, "parent_id": key, "readonly": args.get("readonly", True)})["id"] for i in range(len(seats))]
            return self.save("panel", {"id": key, "workspace": workspace(args["workspace"]), "idempotency_key": request_key, "jobs": jobs, "models": models, "rubric": args.get("rubric"), "kind": args.get("kind", "review"), "state": "running"})


    def panel_results(self, key: str) -> dict:
        row = self.store.get("panel", key)
        results = [self.store.get("job", j) for j in row["jobs"]]
        state = "completed" if all(j["state"] == "completed" for j in results) else "incomplete" if all(j["state"] in TERMINAL for j in results) else "running"
        self.update("panel", key, state=state)
        return {**row, "state": state, "results": results, "synthesis_required": True, "note": "Coordinator must read every result, grade rubric, deduplicate findings, record disagreements, choose/graft if arena, and verify the synthesis."}

    def loop_start(self, args: dict) -> dict:
        scope = workspace(args["workspace"])
        if not args.get("done_command") or not args.get("prompt"):
            raise ValueError("loop requires a falsifiable done_command and owner prompt")
        if float(args.get("max_seconds", 0)) <= 0 or int(args.get("max_iterations", 0)) <= 0:
            raise ValueError("explicit time and iteration budgets required; exhaustion is BLOCKED, never success")
        selected = providers.selection(self.store, args.get("role", "feature, refactoring"), args.get("seat", 0), args.get("parent"))
        harnesses.require_cli(self.store, selected["provider"])
        key = identity()
        row = {**args, "id": key, "workspace": scope, "state": "running", "iteration": 0, "generation": 0, "created": now(), "started_at": time.time(), "current_job": None, "session": None, "selection": selected}
        self.save("loop", row)
        threading.Thread(target=self.run_loop, args=(key, 0), daemon=True).start()
        return row

    def loop_command(self, key: str, argv: list[str], timeout: float, epoch: int | None = None) -> dict:
        with self.lock:
            row = self.store.get("loop", key)
            if row["state"] not in {"running", "recovering"} or (epoch is not None and row.get("generation", 0) != epoch):
                raise InterruptedError("loop cancelled, paused or superseded")
            p = subprocess.Popen(argv, cwd=row["workspace"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            self.processes["loop:" + key] = p
        try:
            stdout, stderr = p.communicate(timeout=timeout)
            return {"argv": argv, "exit_code": p.returncode, "stdout": stdout[-100000:], "stderr": stderr[-15000:], "time": now()}
        except subprocess.TimeoutExpired:
            self.terminate(p)
            p.communicate()
            return {"argv": argv, "exit_code": 124, "stdout": "", "stderr": "command budget exhausted", "time": now()}
        finally:
            with self.lock:
                if self.processes.get("loop:" + key) is p: self.processes.pop("loop:" + key, None)

    def loop_current(self, key: str, epoch: int) -> dict:
        row = self.store.get("loop", key)
        if row["state"] != "running" or row.get("generation", 0) != epoch:
            raise InterruptedError("loop cancelled, paused or superseded")
        return row

    def run_loop(self, key: str, epoch: int = 0):
        try:
            with self.lock:
                row = self.store.get("loop", key)
                if row["state"] not in {"running", "recovering"} or row.get("generation", 0) != epoch: return
                self.update("loop", key, state="running")
            while True:
                row = self.loop_current(key, epoch)
                remaining = row["max_seconds"] - (time.time() - row["started_at"])
                if remaining <= 0:
                    with self.lock:
                        self.loop_current(key, epoch)
                        self.update("loop", key, state="blocked", stop_reason="time budget exhausted; predicate not proven")
                    return
                proof = self.loop_command(key, row["done_command"], min(remaining, row.get("predicate_timeout", remaining)), epoch)
                with self.lock:
                    row = self.loop_current(key, epoch)
                    self.store.event("loop_predicate", {"loop": key, "iteration": row["iteration"], "proof": proof}, row["workspace"])
                    if proof["exit_code"] == 0:
                        self.update("loop", key, state="completed", proof=proof, stop_reason="predicate passed")
                        return
                    if proof["exit_code"] == 124:
                        self.update("loop", key, state="blocked", proof=proof, stop_reason="predicate timeout; evidence missing, no repair assumption")
                        return
                    if row["iteration"] >= row["max_iterations"]:
                        self.update("loop", key, state="blocked", stop_reason="iteration budget exhausted; predicate not met")
                        return
                    recovered = self.store.get("job", row["current_job"]) if row.get("current_job") else None
                    session = (recovered or {}).get("session") or row.get("session")
                    prompt = row["prompt"] + "\nResume checkpoint: " + json.dumps({"iteration": row["iteration"], "last_proof": proof, "last_job": row.get("current_job")}) + "\nComplete the smallest next unit and verify it. Do not relax the done predicate."
                    job = self.spawn({**row, "_selection": row.get("selection") or (recovered or {}).get("selection"), "prompt": prompt, "session": session, "role": row.get("role", "feature, refactoring"), "readonly": row.get("readonly", False), "isolate": False, "timeout": min(remaining, row.get("agent_timeout", 1800)), "parent_id": key, "idempotency_key": key + ":" + str(row["iteration"]) + ":" + str(epoch)})
                    self.update("loop", key, current_job=job["id"])
                while job["state"] not in TERMINAL:
                    self.loop_current(key, epoch)
                    if time.time() - row["started_at"] >= row["max_seconds"]:
                        with self.lock:
                            self.loop_current(key, epoch)
                            self.cancel(job["id"])
                            self.update("loop", key, state="blocked", stop_reason="time budget exhausted while owner was active; predicate not proven")
                        return
                    job = self.wait(job["id"], 1)
                with self.lock:
                    self.loop_current(key, epoch)
                    self.update("loop", key, iteration=row["iteration"] + 1, session=job.get("session"))
                    self.store.event("decision", {"phase": "loop", "decision": f"iteration {row['iteration'] + 1} returned {job['state']}", "why": "progress against explicit predicate", "evidence": job["result_path"], "result": job["state"]}, row["workspace"])
                    if job["state"] != "completed":
                        self.update("loop", key, state="blocked", stop_reason="owner failed; inspect evidence and replan", error=job.get("error"))
                        return
                if row.get("wake_command"):
                    remaining = row["max_seconds"] - (time.time() - row["started_at"])
                    if remaining <= 0: continue
                    wake = self.loop_command(key, row["wake_command"], min(row.get("heartbeat_seconds", 300), remaining), epoch)
                    self.store.event("loop_wake", {"loop": key, "proof": wake}, row["workspace"])
                else:
                    deadline = time.monotonic() + row.get("interval_seconds", 1)
                    while time.monotonic() < deadline:
                        self.loop_current(key, epoch)
                        time.sleep(.1)
        except InterruptedError:
            return
        except Exception as e:
            with self.lock:
                row = self.store.get("loop", key)
                if row["state"] == "running" and row.get("generation", 0) == epoch:
                    self.update("loop", key, state="blocked", stop_reason=str(e))

    def loop_stop(self, key: str, state: str = "cancelled") -> dict:
        with self.lock:
            current = self.store.get("loop", key)
            row = self.update("loop", key, generation=current.get("generation", 0) + 1, state=state, stop_reason="explicit user " + state)
            if row.get("current_job"): self.cancel(row["current_job"])
            p = self.processes.get("loop:" + key)
            if p: self.terminate(p)
            return row

    def loop_resume(self, key: str) -> dict:
        with self.lock:
            row = self.store.get("loop", key)
            if row["state"] == "completed": raise ValueError("completed loops cannot restart")
            if row["state"] in {"running", "recovering"}: return row
            epoch = row.get("generation", 0) + 1
            row = self.update("loop", key, generation=epoch, state="running", started_at=time.time(), recovery_count=row.get("recovery_count", 0) + 1)
            threading.Thread(target=self.run_loop, args=(key, epoch), daemon=True).start()
            return row
