"""Where sessions are kept.

One JSON object per line in ~/.meditate/sessions.jsonl. Rows carry the
device name so logs from several machines can be merged later without a
migration.
"""
import json
import os
import socket
from datetime import datetime
from pathlib import Path

STORE = Path(os.environ.get("MEDITATE_HOME", Path.home() / ".meditate"))
SESSIONS = STORE / "sessions.jsonl"

DEVICE = socket.gethostname().split(".")[0]


def append(row):
    STORE.mkdir(parents=True, exist_ok=True)
    row.setdefault("device", DEVICE)
    with SESSIONS.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def load():
    if not SESSIONS.exists():
        return []
    rows = []
    for line in SESSIONS.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        r.setdefault("kind", "sit")      # rows written before desk tracking
        r.setdefault("device", DEVICE)
        rows.append(r)
    return rows


def iso(ts):
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")
