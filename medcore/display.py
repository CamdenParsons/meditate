"""Drawing to the terminal. Rendering only - no domain logic lives here."""
import os
from pathlib import Path

ART_DIR = Path(__file__).resolve().parent.parent / "art"

def _c(n):
    return f"\033[38;5;{n}m"


# A warm palette, because the thing it is imitating is a struck bell.
# Colour marks category and intensity, never quality: the app does not
# know whether your session was good.
RESET, DIM = "\033[0m", "\033[2m"
FIGURE = _c(137)     # the Buddha, sitting behind everything
RAYS = _c(94)        # the halo, dimmer than the figure
GOLD = _c(179)       # the clock
BRIGHT = _c(222)     # the struck note: bar, live numbers
WHITE = _c(253)
GREY = _c(244)
FAINT = _c(238)
TEAL = _c(73)        # status
MAUVE = _c(176)      # claude
BLUE = _c(110)       # linear
GREEN = _c(108)      # commits
ART = FIGURE

# the sparkline runs cold to warm with the amount of input
LADDER = [_c(238), _c(94), _c(136), _c(137), _c(179), _c(179), _c(214),
          _c(214), _c(222)]
HIDE, SHOW, CLEAR, HOME = "\033[?25l", "\033[?25h", "\033[2J", "\033[H"
BARS = " ▁▂▃▄▅▆▇█"

GLYPHS = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": ["██ ", " █ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    # dots on rows 2 and 4 so they land centred once the font is halved
    ":": ["   ", "   ", " █ ", "   ", " █ "],
}


def mmss(seconds):
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def hhmm(seconds):
    seconds = max(0, int(round(seconds)))
    if seconds < 60:
        return f"{seconds}s"
    h, m = divmod(seconds // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def sparkline(buckets, colour=True):
    """Render a stored bucket string ('0'-'8' per column) as bars.

    Coloured cold to warm by how much input each column held, so the shape
    of a session is legible before you read either number.
    """
    out = []
    for c in buckets or "":
        if not c.isdigit():
            out.append(" ")
            continue
        n = min(8, int(c))
        out.append(f"{LADDER[n]}{BARS[n]}{RESET}" if colour else BARS[n])
    return "".join(out)


_art_cache = None


def art_options():
    """Art to show above the clock, largest first.

    Three tiers so the screen degrades instead of clipping: the haloed
    Buddha, the plain figure, then nothing. MEDITATE_ART overrides with a
    single file of your own.
    """
    global _art_cache
    if _art_cache is None:
        override = os.environ.get("MEDITATE_ART")
        names = [Path(override)] if override else [
            ART_DIR / "buddha.txt", ART_DIR / "figure.txt"]
        out = []
        for path in names:
            try:
                out.append(path.read_text().rstrip("\n").split("\n"))
            except OSError:
                pass
        _art_cache = out
    return _art_cache


def _fits(art, width, height):
    w = max((len(l) for l in art), default=0)
    return width >= w + 2 and height >= len(art) + 12


def clock_face(text):
    """Render the 3x5 font at half height using half-block characters.

    Each output row carries two rows of the glyph - upper half, lower
    half, both, or neither - so the clock is three rows tall while
    keeping the shape of a five-row font.
    """
    glyphs = [GLYPHS.get(c, GLYPHS[":"]) for c in text]
    rows = []
    for top in range(0, 6, 2):
        line = []
        for g in glyphs:
            upper = g[top] if top < len(g) else "   "
            lower = g[top + 1] if top + 1 < len(g) else "   "
            line.append("".join(
                "█" if u != " " and l != " " else "▀" if u != " "
                else "▄" if l != " " else " "
                for u, l in zip(upper, lower)))
        rows.append(" ".join(line))
    return rows


def screen(session, width, height=None):
    """The live frame. Counts down for a fixed length, up for open-ended.

    The whole composition is centred vertically, and the art is dropped
    entirely rather than clipped when the terminal is too small for it.
    """
    remaining = session.remaining
    if remaining is None:
        clock, done = mmss(session.elapsed), None
    else:
        clock = mmss(remaining)
        done = 1.0 - (remaining / session.duration if session.duration else 0)

    body = []

    for art in art_options():
        if _fits(art, width, height or 0):
            art_w = max(len(l) for l in art)
            pad = " " * ((width - art_w) // 2)
            body += [ART + pad + line + RESET for line in art]
            body.append("")
            break

    for line in clock_face(clock):
        body.append(GOLD + line.center(width).rstrip() + RESET)
    body.append("")

    if done is not None:
        bar_w = max(20, min(46, width - 12))
        filled = int(round(done * bar_w))
        bar = (BRIGHT + "━" * filled + FAINT + "━" * (bar_w - filled) + RESET)
        body.append(" " * max(0, (width - bar_w) // 2) + bar)
        body.append("")

    if session.paused:
        status = "paused"
    elif session.next_gong is None:
        status = "no gong"
    else:
        status = f"next gong in {mmss(session.next_gong)}"
    body.append(TEAL + status.center(width).rstrip() + RESET)

    if len(session.presence):
        still = f"still for {mmss(session.presence.still_for)}"
        body.append(DIM + still.center(width).rstrip() + RESET)

    body.append("")
    body.append(DIM + "[space] pause   [q] end".center(width).rstrip() + RESET)

    top = max(0, ((height or len(body) + 2) - len(body)) // 2)
    return CLEAR + HOME + "\n" * top + "\n".join(body)


def rollup(prog, colour=True):
    """One readable line of counts, for the session list.

    Detail belongs in `meditate show`; this only has to say what kinds of
    work a session touched, and how much.
    """
    if not prog:
        return ""
    C = (lambda code: code) if colour else (lambda code: "")
    parts = []

    n = len(prog.get("claude", []))
    if n:
        parts.append(f"{C(MAUVE)}claude{C(RESET)} ({n} session{_s(n)})")

    n = len(prog.get("linear", []))
    if n:
        parts.append(f"{C(BLUE)}linear{C(RESET)} ({n} issue{_s(n)})")

    gh = prog.get("github", {})
    bits = []
    for key, one, many in (("prs", "PR", "PRs"),
                           ("reviews", "review", "reviews"),
                           ("issues", "comment", "comments"),
                           ("pushes", "push", "pushes"),
                           ("branches", "branch", "branches")):
        k = len(gh.get(key, []))
        if k:
            bits.append(f"{k} {one if k == 1 else many}")
    if bits:
        parts.append(f"{C(WHITE)}github{C(RESET)} ({', '.join(bits)})")

    n = len(prog.get("commits", []))
    if n:
        parts.append(f"{C(GREEN)}{n} commit{_s(n)}{C(RESET)}")

    # ids are short and identify the work, so show them until there are
    # too many to read at a glance
    tix = [t for t in prog.get("tickets", [])]
    if tix:
        shown = " ".join(tix) if len(tix) <= 3 else f"{len(tix)} tickets"
        parts.append(f"{C(GOLD)}{shown}{C(RESET)}")

    return "  ".join(parts)


def _s(n):
    return "" if n == 1 else "s"


def short_path(p):
    """A transcript path with the home directory folded to ~."""
    home = str(Path.home())
    return p.replace(home, "~", 1) if p and p.startswith(home) else (p or "")


def progress_detail(prog):
    """The full picture, for `meditate show`."""
    if not prog:
        return "  Nothing recorded.\n"
    gh = prog.get("github", {})
    out = []
    if prog.get("tickets"):
        out.append(f"  {GOLD}{' '.join(prog['tickets'])}{RESET}")
    for iss in prog.get("linear", []):
        status = f" [{iss['status']}]" if iss.get("status") else ""
        out.append(f"  {GOLD}{iss['id']}{RESET}{DIM}{status}{RESET}  {iss.get('title','')[:64]}")
    for pr in gh.get("prs", []):
        out.append(f"  {WHITE}PR{RESET} {pr['action']} {pr['repo']}#{pr['number']}"
                   f"  {pr['title']}")
    for rv in gh.get("reviews", []):
        out.append(f"  {WHITE}review{RESET} {rv['repo']}#{rv['number']}  {rv.get('title') or ''}")
    for iss in gh.get("issues", []):
        out.append(f"  {WHITE}comment{RESET} {iss['repo']}#{iss['number']}  {iss.get('title') or ''}")
    for br in gh.get("branches", []):
        out.append(f"  {WHITE}branch{RESET} {br['repo']}  {br['ref']}")
    for push in gh.get("pushes", []):
        out.append(f"  {WHITE}push{RESET}   {push['repo']}  {push['ref']}")
    for c in prog.get("commits", []):
        out.append(f"  {GREY}{c['sha']}{RESET} {c['repo']}  {c['subject']}")
    for cs in prog.get("claude", []):
        where = (cs.get("cwd") or "").split("/")[-1]
        # Claude Code titles its own sessions; older rows only kept the
        # opening prompt
        label = cs.get("title") or cs.get("opened_with") or "(continued)"
        out.append(f"  {GREY}claude{RESET} {cs['messages']:>4} msgs  {where}"
                   f"  {WHITE}{label[:60]}{RESET}")
        for prompt in cs.get("prompts", []):
            out.append(f"  {DIM}         · {prompt[:70]}{RESET}")
        if cs.get("path"):
            out.append(f"  {DIM}         {short_path(cs['path'])}{RESET}")
    return "\n".join(out) + "\n"


def farewell(row, ended_by):
    from .presence import describe, read_summary
    if row is None:
        return "\n  Too short to log.\n"
    why = {"you": "Ended.", "duration": "Complete.",
           "expired": "Expired — you left."}.get(ended_by, "Ended.")
    s = read_summary(row)
    lines = [f"\n  {GOLD}{why}{RESET}  {mmss(row['seconds'])}, {row['gongs']} gongs."]
    if s:
        lines += [f"\n  {GREY}{sparkline(s['buckets'])}{RESET}", f"  {describe(s)}"]
    summary = rollup(row.get("progress"))
    if summary:
        lines.append(f"  {summary}")
    return "\n".join(lines) + "\n"
