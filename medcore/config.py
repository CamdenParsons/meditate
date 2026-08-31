"""Settings from a .env file.

Two files are read, in this order, and neither is required:

    ~/.meditate/.env        yours, wherever you run from
    <repo>/.env             handy while working on a clone

A variable already set in the real environment always wins, so a one-off
`LINEAR_API_KEY=... meditate 20` overrides the file without editing it.
The first file to define a name wins over the second.

Deliberately not python-dotenv: this is fifteen lines, and the whole tool
has no dependencies.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def parse(text):
    """Read `KEY=value` lines. Ignores blanks, comments and a leading
    `export`, and strips one layer of matching quotes."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value
    return out


def files():
    from . import store
    return [store.STORE / ".env", REPO / ".env"]


def load(paths=None, environ=None):
    """Apply the .env files. Returns the names actually set."""
    environ = os.environ if environ is None else environ
    applied = []
    for path in (files() if paths is None else paths):
        try:
            text = Path(path).read_text()
        except OSError:
            continue
        for key, value in parse(text).items():
            if key not in environ:            # the real environment wins
                environ[key] = value
                applied.append(key)
    return applied
