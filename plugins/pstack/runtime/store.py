from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())["version"]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def identity() -> str:
    return uuid.uuid4().hex


def data_home() -> Path:
    path = Path(os.environ.get("PSTACK_DATA", Path.home() / ".local/share/pstack")).resolve()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def workspace(path: str) -> str:
    target = Path(path).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise ValueError("workspace must be a directory")
    return str(target)


class Store:
    def __init__(self, home: Path | None = None):
        self.home = home or data_home()
        self.home.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS objects (
                    kind TEXT NOT NULL, id TEXT NOT NULL, workspace TEXT NOT NULL,
                    body TEXT NOT NULL, updated TEXT NOT NULL,
                    PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL,
                    workspace TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL);
            """)
        (self.home / "state.sqlite").chmod(0o600)

    @contextlib.contextmanager
    def db(self):
        conn = sqlite3.connect(self.home / "state.sqlite", timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def put(self, kind: str, key: str, body: dict, scope: str = "") -> dict:
        with self.db() as db:
            db.execute("INSERT INTO objects VALUES(?,?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET body=excluded.body, workspace=excluded.workspace, updated=excluded.updated",
                       (kind, key, scope, json.dumps(body), now()))
        return body

    def get(self, kind: str, key: str) -> dict:
        with self.db() as db:
            row = db.execute("SELECT body FROM objects WHERE kind=? AND id=?", (kind, key)).fetchone()
        if row is None:
            raise KeyError(f"unknown {kind}: {key}")
        return json.loads(row[0])

    def compare_put(self, kind: str, key: str, expected: dict, body: dict, scope: str) -> bool:
        """Do not let a completed hook overwrite cancellation or a newer turn."""
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM objects WHERE kind=? AND id=?", (kind, key)).fetchone()
            current = json.loads(row[0]) if row else {}
            if any(current.get(k) != v for k, v in expected.items()): return False
            db.execute("UPDATE objects SET body=?,workspace=?,updated=? WHERE kind=? AND id=?", (json.dumps(body),scope,now(),kind,key))
        return True

    def list(self, kind: str, scope: str | None = None) -> list[dict]:
        with self.db() as db:
            query = "SELECT id,body FROM objects WHERE kind=?"
            args = [kind]
            if scope is not None:
                query += " AND workspace=?"
                args.append(scope)
            query += " ORDER BY updated"
            return [{"id": r["id"], **json.loads(r["body"])} for r in db.execute(query, args)]

    def event(self, kind: str, body: dict, scope: str = "") -> dict:
        with self.db() as db:
            cur = db.execute("INSERT INTO events(time,workspace,kind,body) VALUES(?,?,?,?)",
                             (now(), scope, kind, json.dumps(body)))
        return {"seq": cur.lastrowid, **body}

    def history(self, scope: str, after: int = 0, limit: int | None = 500) -> list[dict]:
        with self.db() as db:
            query = "SELECT * FROM events WHERE workspace=? AND seq>? ORDER BY seq"
            params = [scope, after]
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            rows = db.execute(query, params)
            return [{"seq": r["seq"], "time": r["time"], "kind": r["kind"], **json.loads(r["body"])} for r in rows]

    def decisions(self, scope: str) -> str:
        path = self.home / "trails" / (hashlib.sha256(scope.encode()).hexdigest()[:16] + ".tsv")
        path.parent.mkdir(exist_ok=True)
        rows = ["ts\tphase\tdecision\twhy\tevidence\tresult"]
        for e in self.history(scope, limit=None):
            if e["kind"] != "decision":
                continue
            cells = [e.get(k, "") for k in ["time", "phase", "decision", "why", "evidence", "result"]]
            cells = [str(x).replace("\t", " ").replace("\n", " ") for x in cells]
            cells = [("'" + x) if x.startswith(("=", "+", "-", "@")) else x for x in cells]
            rows.append("\t".join(cells))
        path.write_text("\n".join(rows) + "\n")
        return str(path)
