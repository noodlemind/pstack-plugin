"""Run one Grok CLI owner with an exclusive leader and bounded file permissions."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from providers import grok_env, grok_native_command


def process_identity(pid: int) -> str:
    return subprocess.run(["ps", "-p", str(pid), "-o", "lstart="],
                          capture_output=True, text=True).stdout.strip()


def stop_owned_leader(pid: int | None, identity: str | None):
    if not pid or not identity or process_identity(pid) != identity:
        return
    try:
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline and process_identity(pid) == identity:
            time.sleep(.05)
        if process_identity(pid) == identity:
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--resume")
    parser.add_argument("--session-id")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--readonly", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.resume and args.session_id:
        parser.error("new session ID and resume are mutually exclusive")
    child = None
    leader_pid = None
    leader_identity = None
    interrupted = False

    def interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True
        if child and child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    with tempfile.TemporaryDirectory(prefix="pstack-grok-", dir="/tmp") as folder:
        socket = Path(folder) / "leader.sock"
        lock = socket.with_suffix(".lock")
        cmd = grok_native_command(args.model, args.effort, args.prompt, args.readonly,
                                  args.resume, str(Path.cwd())) + ["--leader-socket", str(socket)]
        if not args.resume:
            cmd += ["--session-id", args.session_id or str(uuid.uuid4())]
        try:
            child = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, env=grok_env())
            print(json.dumps({"pstack_grok_cli_start": {"cli_pid": child.pid,
                  "cli_identity": process_identity(child.pid), "exclusive_socket": str(socket)}}),
                  file=sys.stderr, flush=True)
            deadline = time.monotonic() + 3
            while child.poll() is None and time.monotonic() < deadline and not interrupted:
                if lock.is_file():
                    content = lock.read_text().strip()
                    if content.isdecimal():
                        leader_pid = int(content)
                        leader_identity = process_identity(leader_pid)
                        if leader_identity:
                            print(json.dumps({"pstack_grok_owner_start": {
                                  "leader_pid": leader_pid, "leader_identity": leader_identity,
                                  "exclusive_socket": str(socket)}}), file=sys.stderr, flush=True)
                            break
                time.sleep(.02)
            stdout, stderr = child.communicate()
            print(stdout, end="")
            print(stderr, end="", file=sys.stderr)
            print(json.dumps({"pstack_grok_owner": {"leader_pid": leader_pid,
                  "leader_identity": leader_identity, "exclusive_socket": str(socket),
                  "interrupted": interrupted}}), file=sys.stderr)
            code = 130 if interrupted else child.returncode
        finally:
            if child and child.poll() is None:
                child.terminate()
                try:
                    child.wait(1)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            stop_owned_leader(leader_pid, leader_identity)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
