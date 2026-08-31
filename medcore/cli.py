"""The command line. Thin on purpose - the behaviour lives in the modules."""
import argparse
import os
import select
import sys
import termios
import time
import tty
from datetime import datetime, timedelta

from . import activity, audio, config, store
from .display import (CLEAR, DIM, GOLD, GREY, HIDE, HOME, RESET, SHOW, WHITE,
                      farewell, hhmm, mmss, progress_detail, rollup, screen,
                      sparkline)
from .presence import percent, read_summary
from .session import EXPIRE, INTERVAL, Session

USAGE = """meditate - log focused seated sessions at your desk, with a gong.

  meditate            start a session, gong every 30 min
  meditate 20         a 20 minute session
  meditate -i 5       gong every 5 min
  meditate -e 30      expire after 30 min with no input
  meditate log        past sessions
  meditate show       what you did in the last one (show -n 2 for the one before)
  meditate bell       ring the gong once

While running:  [space] pause/resume   [q] end

A session ends when you press q, when a fixed length elapses, or when you
stop touching the machine for the expiry window - in which case it is
recorded as ending at your last input, not when the expiry fired.
"""


def _drive(session, gather=True):
    """Run a Session against a real terminal."""
    interactive = sys.stdin.isatty()
    old = None
    if interactive:
        old = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        sys.stdout.write(HIDE)
    session.start()
    try:
        while not session.done():
            session.tick()
            if interactive:
                size = os.get_terminal_size()
                sys.stdout.write(screen(session, size.columns, size.lines))
                sys.stdout.flush()
                if select.select([sys.stdin], [], [], 0)[0]:
                    k = sys.stdin.read(1)
                    if k == " ":
                        session.toggle_pause()
                    elif k in ("q", "\x03"):
                        session.end()
            time.sleep(0.2)
    except KeyboardInterrupt:
        session.end()
    finally:
        if interactive and old is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
            sys.stdout.write(SHOW + CLEAR + HOME)
            sys.stdout.flush()

    # Count the closing gong before close() so the log matches what you heard.
    end_gong = session.rings_at_end
    if end_gong:
        session.gongs += 1

    extra = {}
    if gather and session.recorded_seconds() >= activity.MIN_SECONDS:
        print(f"  {DIM}gathering what you did...{RESET}", flush=True)
        try:
            found = activity.collect(*session.window())
        except Exception:
            found = {}                      # never let this fail a Session
        if found:
            extra["progress"] = found

    row = session.close(extra)
    print(farewell(row, session.ended_by))

    if end_gong and row:
        audio.ring()
        if session.ended_by == "duration":
            # a sit is meant to close on the gong, so hold the terminal
            print(f"  {DIM}(letting the gong ring out — ctrl-c to cut it short){RESET}\n")
            try:
                time.sleep(audio.seconds() + 0.5)
            except KeyboardInterrupt:
                pass


def _log(limit):
    rows = store.load()
    if not rows:
        print("\n  No sessions yet.\n")
        return
    print()
    by_day = {}
    shown = rows[-limit:]
    for i, r in enumerate(shown):
        if i:
            print()          # entries can run to two lines, so separate them
        when = datetime.fromisoformat(r["started"])
        s = read_summary(r)
        mark = {"expired": "~", "you": " ", "duration": " "}.get(r.get("ended_by"), " ")
        line = f"  {when:%Y-%m-%d %H:%M}  {mark}{mmss(r['seconds']):>8}"
        if s:
            line += f"  {GREY}{sparkline(s['buckets'])}{RESET} {percent(s):3.0f}%"
        print(line)
        summary = rollup(r.get("progress"))
        if summary:
            print(f"  {' ' * 19}{WHITE}{summary}{RESET}")
        by_day.setdefault(when.date(), 0)
        by_day[when.date()] += r["seconds"]
    total = sum(r["seconds"] for r in rows)
    days = len({datetime.fromisoformat(r["started"]).date() for r in rows})
    n = len(rows)
    print(f"\n  {n} session{'' if n == 1 else 's'} over "
          f"{days} day{'' if days == 1 else 's'}, "
          f"{timedelta(seconds=int(total))} total.")
    if by_day:
        last = max(by_day)
        print(f"  {DIM}{last}: {hhmm(by_day[last])}{RESET}\n")


def main(argv=None):
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("target", nargs="?", default="")
    p.add_argument("-i", "--interval", type=float, default=INTERVAL / 60, metavar="MIN")
    p.add_argument("-e", "--expire", type=float, default=EXPIRE / 60, metavar="MIN")
    # no default: `log` wants 25 rows, `show` wants the last one
    p.add_argument("-n", "--number", type=int, default=None)
    p.add_argument("--no-progress", action="store_true",
                   help="skip the end-of-session look at what you did")
    p.add_argument("-h", "--help", action="store_true")
    a = p.parse_args(argv)
    config.load()

    if a.help:
        print(USAGE)
        return 0
    if a.target == "log":
        _log(a.number or 25)
        return 0
    if a.target == "show":
        rows = store.load()
        if not rows:
            print("\n  No sessions yet.\n")
            return 0
        nth = max(a.number or 1, 1)
        r = rows[-min(nth, len(rows))]
        print(f"\n  {r['started']}  {mmss(r['seconds'])}  {r.get('ended_by','')}\n")
        print(progress_detail(r.get("progress")))
        return 0
    if a.target == "bell":
        audio.ring()
        secs = audio.seconds()
        print(f"  {DIM}ringing — {secs:.0f}s, ctrl-c to cut it short{RESET}")
        try:
            time.sleep(secs + 0.5)
        except KeyboardInterrupt:
            print()
        return 0

    duration = None
    if a.target:
        try:
            duration = float(a.target) * 60
        except ValueError:
            print(f"Don't know '{a.target}'. Try minutes, 'log', or 'bell'.")
            return 1
        if duration <= 0:
            print("A session has to be longer than zero.")
            return 1
    if a.interval < 0:
        print("A gong interval cannot be negative. Use 0 for no gong.")
        return 1
    if a.expire < 0:
        print("An expiry cannot be negative. Use 0 to never expire.")
        return 1

    _drive(Session(duration=duration,
                   interval=a.interval * 60,
                   expire=a.expire * 60), gather=not a.no_progress)
    return 0
