"""Local commits, including ones not pushed anywhere."""
import os
from pathlib import Path

from ._util import run

TIMEOUT = 10


class Provider:
    name = "commits"

    def collect(self, window, found):
        """Commits you authored, in the repositories claude was working in.

        The Claude transcripts carry a `cwd`, so the sessions you had also
        say which repositories to search - no configuration. This catches
        work that never reached GitHub, which the events feed cannot see.

        Work does happen outside those directories, so the directory you
        ran from counts too, and MEDITATE_REPOS names any others.
        """
        start, end = window
        repos = {s["cwd"] for s in found.get("claude", [])
                 if s.get("cwd") and Path(s["cwd"]).is_dir()}
        repos.add(os.getcwd())
        repos.update(d for d in os.environ.get("MEDITATE_REPOS", "").split(",")
                     if d.strip() and Path(d.strip()).is_dir())
        out = []
        for repo in sorted(repos):
            root = run(["git", "rev-parse", "--show-toplevel"], TIMEOUT, cwd=repo)
            if not root:
                continue
            root = root.strip()
            email = run(["git", "config", "user.email"], TIMEOUT, cwd=root)
            if not email:
                continue
            log = run(["git", "log", "--all", f"--author={email.strip()}",
                       f"--since={start.isoformat()}",
                       f"--until={end.isoformat()}",
                       "--format=%h%x1f%s"], TIMEOUT, cwd=root)
            if not log:
                continue
            for line in log.strip().splitlines():
                if "\x1f" not in line:
                    continue
                sha, subject = line.split("\x1f", 1)
                out.append({"repo": Path(root).name, "sha": sha,
                            "subject": subject})
        return out
