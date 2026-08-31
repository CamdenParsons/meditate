"""Reading how long since the human last touched the machine.

Only the *timing* of input is available through this interface - key
identities are not, which is exactly why it needs no permissions and
captures no content.
"""
import re
import subprocess

_CMD = ["ioreg", "-r", "-d", "1", "-c", "IOHIDSystem"]
_PAT = re.compile(r'"HIDIdleTime"\s*=\s*(\d+)')


def idle_seconds():
    """Seconds since the last keyboard/mouse/trackpad event, or None."""
    try:
        out = subprocess.run(_CMD, capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return None
    m = _PAT.search(out)
    return int(m.group(1)) / 1e9 if m else None


def available():
    return idle_seconds() is not None
