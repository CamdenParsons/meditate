"""Shared plumbing for activity providers."""
import os
import subprocess
from datetime import datetime


def run(cmd, timeout, cwd=None):
    """Run a command, returning stdout or None. Never raises."""
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)          # the keyring login is the good one
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd, env=env)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    return p.stdout if p.returncode == 0 else None


def parse_time(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        return None
