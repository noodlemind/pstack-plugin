from __future__ import annotations

from engine import Engine
import hashlib

import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import termios
import threading
import time

from store import ROOT, identity, now, workspace


class Controls:
    def __init__(self, home: Path):
        self.home = home
        self.terminals = {}
        self.browsers = {}
        self.lock = threading.RLock()

    def cli(self, action: str, args: dict) -> dict:
        if action == "start":
            ident = identity()
            master, slave = pty.openpty()
            env = {**os.environ, "TERM": "xterm-256color"}
            proc = subprocess.Popen(args["argv"], cwd=workspace(args["workspace"]), stdin=slave, stdout=slave, stderr=slave, env=env, start_new_session=True)
            os.close(slave)
            folder = self.home / "controls" / ident
            folder.mkdir(parents=True)
            (folder / "owner.json").write_text(json.dumps({"workspace": workspace(args["workspace"])}))
            row = {"id": ident, "fd": master, "proc": proc, "transcript": "", "path": str(folder / "transcript.txt"), "actions": str(folder / "actions.jsonl")}
            self.terminals[ident] = row
            self.record(row, {"action": "start", "argv": args["argv"]})
            return self.cli("snapshot", {"id": ident, "wait_seconds": .2})
        row = self.terminals[args["id"]]
        if action == "send":
            if not args.get("after_snapshot"):
                raise ValueError("send requires the previous snapshot digest")

            while select.select([row["fd"]], [], [], 0)[0]:
                try: pending = os.read(row["fd"], 65536)
                except OSError: break
                if not pending: break
                row["transcript"] += pending.decode(errors="replace")
            if args["after_snapshot"] != hashlib.sha256(row["transcript"].encode()).hexdigest():
                raise ValueError("stale terminal snapshot")
            os.write(row["fd"], args["text"].encode())
            self.record(row, {"action": "send", "text": args["text"]})
        elif action == "resize":
            fcntl.ioctl(row["fd"], termios.TIOCSWINSZ, struct.pack("HHHH", args["rows"], args["columns"], 0, 0))
            os.killpg(row["proc"].pid, signal.SIGWINCH)
            self.record(row, {"action": "resize", "rows": args["rows"], "columns": args["columns"]})
        elif action == "stop":

            Engine.terminate(row["proc"])
            os.close(row["fd"])
            self.record(row, {"action": "stop"})
            self.terminals.pop(row["id"])
            return {"id": row["id"], "state": "stopped", "transcript_path": row["path"], "actions_path": row["actions"]}
        elif action != "snapshot":
            raise ValueError("unknown CLI action")
        deadline = time.monotonic() + min(args.get("wait_seconds", .2), 30)
        while time.monotonic() < deadline:
            if select.select([row["fd"]], [], [], .05)[0]:
                try:
                    data = os.read(row["fd"], 65536)
                except OSError:
                    break
                if not data:
                    break
                row["transcript"] += data.decode(errors="replace")
            if args.get("pattern") and args["pattern"] in row["transcript"]:
                break
        Path(row["path"]).write_text(row["transcript"])

        return {"id": row["id"], "text": row["transcript"][-30000:], "digest": hashlib.sha256(row["transcript"].encode()).hexdigest(), "transcript_path": row["path"], "actions_path": row["actions"], "exit_code": row["proc"].poll(), "pattern_matched": args.get("pattern", "") in row["transcript"]}

    @staticmethod
    def record(row, event):
        with open(row["actions"], "a") as f:
            f.write(json.dumps({"time": now(), **event}) + "\n")

    def ui(self, action: str, args: dict) -> dict:
        if action == "start":
            ident = identity()
            folder = self.home / "controls" / ident
            folder.mkdir(parents=True)
            (folder / "owner.json").write_text(json.dumps({"workspace": workspace(args["workspace"]) if args.get("workspace") else None}))
            proc = subprocess.Popen(["node", str(ROOT / "runtime/ui.mjs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open(folder / "stderr.txt", "w"), text=True, start_new_session=True)
            self.browsers[ident] = {"id": ident, "proc": proc, "folder": str(folder), "lock": threading.Lock()}
            args = {**args, "id": ident, "artifact_dir": str(folder)}
        row = self.browsers[args["id"]]
        with row["lock"]:
            p = row["proc"]
            p.stdin.write(json.dumps({"action": action, **args}) + "\n")
            p.stdin.flush()
            if not select.select([p.stdout], [], [], 60)[0]:
                raise TimeoutError("browser command timed out")
            result = json.loads(p.stdout.readline())
            if result.get("error"):
                raise RuntimeError(result["error"])
        if action == "stop":
            p.stdin.close()
            p.wait(10)
            self.browsers.pop(row["id"])
        return {"id": row["id"], **result}
