"""Activity providers: what you did during a Session.

A provider answers one question about a window of time. It has a `name`,
which is the key its answer is stored under, and a `collect(window, found)`
returning whatever it found - or a falsey value for nothing.

Providers run in order and can read what earlier ones found: the git
provider searches the repositories the claude provider discovered, and the
tickets provider reads ids out of everything above it. That ordering is the
only coupling between them.

Every provider is best-effort. One that raises, times out, or finds nothing
is skipped, and the Session is still recorded. Nothing here can fail a
Session.

Adding a source - Linear's API, a calendar, a time tracker - means adding a
module with those two attributes and listing it below.
"""
import os

from . import claude, git, github, linear, tickets

MIN_SECONDS = 120      # below this there is nothing worth looking up

PROVIDERS = [
    claude.Provider(),
    github.Provider(),
    git.Provider(),        # after claude: it uses the repos claude found
    linear.Provider(),     # the only one needing a credential
    tickets.Provider(),    # last: it reads everything above
]


def enabled():
    """All providers, or just those named in MEDITATE_ACTIVITY."""
    wanted = os.environ.get("MEDITATE_ACTIVITY")
    if not wanted:
        return PROVIDERS
    names = {n.strip() for n in wanted.split(",") if n.strip()}
    return [p for p in PROVIDERS if p.name in names]


def collect(start, end, providers=None):
    """Ask every provider about the window. Returns {} when nothing is found.

    Set MEDITATE_DEBUG=1 to see provider failures. They are swallowed by
    default so a broken provider cannot fail a Session, but that silence
    once hid a real bug for a whole release, so it is one env var away.
    """
    found = {}
    for provider in (providers if providers is not None else enabled()):
        try:
            result = provider.collect((start, end), found)
        except Exception as exc:       # a broken provider is not a broken Session
            if os.environ.get("MEDITATE_DEBUG"):
                print(f"  activity provider {provider.name!r} failed: "
                      f"{type(exc).__name__}: {exc}")
            result = None
        if result:
            found[provider.name] = result
    return found
