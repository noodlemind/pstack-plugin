#!/usr/bin/env python3
from __future__ import annotations

from api import API

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import socketserver
import subprocess
import sys
import time
import signal

from store import Store, data_home, VERSION
import harnesses


def socket_path(home: Path) -> str:
    folder = Path("/tmp") / ("pstack-" + str(os.getuid()) + "-" + hashlib.sha256(str(home).encode()).hexdigest()[:16])
    folder.mkdir(mode=0o700, exist_ok=True)
    folder.chmod(0o700)
    return str(folder / "runtime.sock")


def exchange(home: Path, payload: dict) -> dict:
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(180)
        s.connect(socket_path(home))
        s.sendall((json.dumps(payload) + "\n").encode())
        stream = s.makefile("rb")
        raw = stream.readline(16 * 1024 * 1024)
        if not raw: raise RuntimeError("runtime disconnected")
        result = json.loads(raw)
        if "error" in result: raise RuntimeError(result["error"])
        return result["result"]


def call(name: str, action: str, data: dict):
    home = data_home()
    # Run metadata and verification inside the invoking host process.
    # Only optional local CLI/control sessions need a supervisor.
    op = name.removeprefix("pstack_")
    if op in {"agent", "panel", "loop"} and action in {"spawn", "start", "resume", "arm_foreground"} and harnesses.settings(Store(home))["mode"] == "native":
        raise ValueError("Use the current host native agents and continuation tools; local CLI execution is disabled.")
    if op in {"environment", "context", "models", "config", "task", "decision", "checkpoint", "verify", "artifact", "worktree"}:
        return API(Store(home)).call(name, action, data)
    payload = {"tool": name, "action": action, "data": data}
    try:
        return exchange(home, payload)
    except (FileNotFoundError, ConnectionRefusedError):
        pass
    with open(home / "startup.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            return exchange(home, payload)
        except (FileNotFoundError, ConnectionRefusedError):
            log = open(home / "supervisor.log", "a")
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "daemon"], stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    return exchange(home, payload)
                except (FileNotFoundError, ConnectionRefusedError): time.sleep(.1)
            raise RuntimeError("supervisor did not start; inspect " + str(home / "supervisor.log"))


def daemon():

    home = data_home()
    lock = open(home / "daemon.lock", "a")
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: return
    api = API(Store(home))
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                request = json.loads(self.rfile.readline(16 * 1024 * 1024))
                result = {"result": api.call(request["tool"], request["action"], request["data"])}
            except Exception as e: result = {"error": str(e)}
            self.wfile.write((json.dumps(result) + "\n").encode())
    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True
    path = socket_path(home)
    Path(path).unlink(missing_ok=True)
    with Server(path, Handler) as server:
        os.chmod(path, 0o600)
        (home / "supervisor.json").write_text(json.dumps({"pid": os.getpid(), "socket": path, "plugin_root": str(Path(__file__).resolve().parents[1])}))
        server.serve_forever()



def main():
    parser = argparse.ArgumentParser(description="pstack persistent runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("daemon")
    command = sub.add_parser("call")
    command.add_argument("tool")
    command.add_argument("action")
    command.add_argument("data", nargs="?", default="{}")
    sub.add_parser("doctor")
    setup = sub.add_parser("setup", help="Detect coding harnesses; default to native execution")
    setup.add_argument("--host", choices=["auto", "local", "cloud"], default="auto")
    setup.add_argument("--budget", choices=list(harnesses.BUDGETS), help="Save your chosen reasoning budget; omitted means keep an existing choice or ask during setup")
    setup.add_argument("--enable-cli", action="append", choices=list(harnesses.HARNESSES), default=[])
    setup.add_argument("--confirmation", default="")
    service = sub.add_parser("service")
    service.add_argument("action", choices=["status", "stop"])
    args = parser.parse_args()
    if args.command == "setup":
        store = Store()
        harnesses.setup(store, host=args.host, mode="local-cli" if args.enable_cli else "native", enabled_cli=args.enable_cli, confirmation=args.confirmation)
        if args.budget:
            harnesses.budget(store, args.budget, args.confirmation or "Explicit --budget choice at setup")
        print(json.dumps(harnesses.scan(store), indent=2))
    elif args.command == "daemon": daemon()
    elif args.command == "doctor":

        print(json.dumps(harnesses.scan(Store()), indent=2))
    elif args.command == "service":
        store = Store()
        active = [j["id"] for j in store.list("job") if j["state"] in {"queued", "running"}]
        loops = [j["id"] for j in store.list("loop") if j["state"] in {"running", "recovering"}]
        record = store.home / "supervisor.json"
        metadata = json.loads(record.read_text()) if record.exists() else None
        if args.action == "stop" and (active or loops):
            raise ValueError("active work remains; drain or explicitly pause/cancel its jobs and loops before stopping")
        if args.action == "stop" and metadata:
            command = subprocess.run(["ps", "-p", str(metadata["pid"]), "-o", "command="], capture_output=True, text=True).stdout
            if metadata["plugin_root"] + "/runtime/pstack.py daemon" in command:
                os.kill(metadata["pid"], signal.SIGTERM)
            else: raise ValueError("supervisor PID identity changed; no process was stopped")
        print(json.dumps({"supervisor": metadata, "active_jobs": active, "active_loops": loops, "action": args.action}, indent=2))
    else:
        try: print(json.dumps(call(args.tool, args.action, json.loads(args.data)), indent=2))
        except Exception as e: print(json.dumps({"error": str(e)})); sys.exit(1)


if __name__ == "__main__": main()
