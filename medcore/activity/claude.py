"""Claude Code sessions that were active during the window."""
import json
from pathlib import Path

from ._util import parse_time

PROJECTS = Path.home() / ".claude" / "projects"
MAX_TRANSCRIPTS = 60
MIN_MESSAGES = 2      # a lone line is a resume marker, not a session
MAX_PROMPTS = 6       # enough to recall the session, not a transcript
PROMPT_CHARS = 90


class Provider:
    name = "claude"

    def collect(self, window, found):
        """Transcripts with activity inside the window.

        Matched on per-line timestamps rather than file mtime: Claude
        sessions are long-lived and resumed, so one transcript can span
        days and only partly overlap a Session.
        """
        start, end = window
        if not PROJECTS.is_dir():
            return []
        files = [p for p in PROJECTS.glob("*/*.jsonl")
                 if p.stat().st_mtime >= start.timestamp()]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        out = []
        for path in files[:MAX_TRANSCRIPTS]:
            found_one = _read(path, start, end)
            if found_one:
                out.append(found_one)
        return sorted(out, key=lambda s: -s["messages"])


def _read(path, start, end):
    """One transcript: its title, the prompts typed inside the window, and
    where it lives so the session can be looked up later."""
    hits, cwd, branch, title = 0, None, None, None
    prompts = []
    try:
        with path.open(errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Claude Code names each session; that line carries no
                # timestamp, so take it wherever it appears.
                if d.get("type") == "ai-title" and d.get("aiTitle"):
                    title = d["aiTitle"]
                    continue
                t = parse_time(d.get("timestamp"))
                if not (t and start <= t <= end):
                    continue
                hits += 1
                cwd = cwd or d.get("cwd")
                branch = branch or d.get("gitBranch")
                if d.get("type") == "user" and not d.get("isMeta"):
                    text = (_first_text(d) or "").strip()
                    if text and len(prompts) < MAX_PROMPTS:
                        prompts.append(text[:PROMPT_CHARS].replace("\n", " "))
    except OSError:
        return None
    if hits < MIN_MESSAGES:
        return None
    return {"id": path.stem, "cwd": cwd, "branch": branch, "messages": hits,
            "title": title, "prompts": prompts, "path": str(path)}


def _first_text(entry):
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text", "")
    return None
