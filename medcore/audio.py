"""Playing the gong."""
import os
import subprocess
from pathlib import Path

SOUNDS = Path(__file__).resolve().parent.parent / "sounds"
BELL = SOUNDS / "bell.m4a"          # full cathedral gong, for sits
RECENTER = SOUNDS / "recenter.m4a"  # shorter and softer, for desk reminders

_lengths = {}


def seconds(path=BELL):
    """How long a sound runs, read from the file so swapping bells just works."""
    key = str(path)
    if key not in _lengths:
        _lengths[key] = 45.0
        try:
            out = subprocess.run(["afinfo", str(path)],
                                 capture_output=True, text=True).stdout
            for line in out.splitlines():
                if "estimated duration" in line:
                    _lengths[key] = float(line.split(":")[1].strip().split()[0])
                    break
        except Exception:
            pass
    return _lengths[key]


def ring(path=BELL, volume=None):
    """Strike the gong. Non-blocking, so tails overlap naturally."""
    if os.environ.get("MEDITATE_SILENT") or not Path(path).exists():
        return
    cmd = ["afplay"]
    if volume is not None:
        cmd += ["-v", str(volume)]
    try:
        subprocess.Popen(cmd + [str(path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass
