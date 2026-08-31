"""A Session: one focused seated stretch at the desk.

You start it. It ends one of three ways:

  you        you pressed q, or ctrl-c
  duration   you asked for a fixed length and it elapsed
  expired    you stopped touching the machine for the expiry window,
             so you presumably walked off without ending it

An expired Session is recorded as ending at your *last input*, not at the
moment the expiry fired. Otherwise walking away at 10am and noticing at
6pm would log eight hours at the desk.

The clock and the input source are injectable so the ending rules can be
tested in milliseconds rather than hours.
"""
import time

from . import audio, store
from .presence import PresenceLog

EXPIRE = 3600      # idle seconds before an unattended Session is closed
INTERVAL = 1800    # seconds between recenter gongs (0 disables)
PRESENT_GRACE = 1.5
MIN_SECONDS = 30   # shorter than this is a misfire, not a Session
STILL_HERE = 120   # input this recently means you are at the desk


class Session:
    """Interface: tick() until done(), then close(). Or just run() it."""

    def __init__(self, duration=None, interval=INTERVAL, expire=EXPIRE,
                 now=time.monotonic, idle=None, gong=None, sink=None,
                 sample=1.0):
        from .inputwatch import idle_seconds
        self.duration = duration
        self.interval = interval
        self.expire = expire
        self.sample = sample
        self._now = now
        self._idle = idle or idle_seconds
        self._gong = gong or _default_gong
        self._sink = sink or store.append

        self.presence = PresenceLog()
        self.started_wall = time.time()
        self.started = self._now()
        self.last_input = self.started
        self.gongs = 0
        self._last_gong = self.started
        self._next_sample = self.started + sample
        self.paused = False
        self._paused_at = None
        self.ended_by = None

    # ---- state a caller can read ---------------------------------

    @property
    def elapsed(self):
        return self._now() - self.started

    @property
    def remaining(self):
        return None if self.duration is None else max(0.0, self.duration - self.elapsed)

    @property
    def next_gong(self):
        if not self.interval:
            return None
        return max(0.0, self._last_gong + self.interval - self._now())

    def done(self):
        return self.ended_by is not None

    @property
    def rings_at_end(self):
        """Whether a closing gong is due.

        An expired Session gets none - you walked away, so there is nobody
        in the room to hear it.
        """
        return self.ended_by in ("duration", "you")

    # ---- driving it ----------------------------------------------

    def start(self):
        self._gong("start")
        self.gongs += 1

    def toggle_pause(self):
        self.paused = not self.paused
        self._paused_at = self._now() if self.paused else None
        if not self.paused:
            self.last_input = self._now()

    def tick(self):
        """One pass. Samples presence, rings if due, decides on ending."""
        now = self._now()
        if self.paused:
            self.last_input = now
            self._next_sample = now + self.sample
            return

        if now >= self._next_sample:
            idle = self._idle()
            present = idle is not None and idle < PRESENT_GRACE * self.sample
            self.presence.record(present)
            if present:
                self.last_input = now
            self._next_sample = now + self.sample

        if self.duration is not None and self.elapsed >= self.duration:
            self.ended_by = "duration"
            return
        if self.expire and now - self.last_input >= self.expire:
            self.ended_by = "expired"
            return
        if self.interval and now - self._last_gong >= self.interval:
            # Don't gong into an empty room: an open-ended Session only
            # rings if you touched something recently. A fixed-length sit
            # is *meant* to be motionless, so it always rings.
            here = now - self.last_input < STILL_HERE
            if self.duration is not None or here:
                self._gong("interval")
                self.gongs += 1
                self._last_gong = now

    def end(self):
        self.ended_by = "you"

    # ---- closing --------------------------------------------------

    def recorded_seconds(self):
        """How long this Session counts for, by the rule its ending implies."""
        if self.ended_by == "duration":
            return self.duration
        if self.ended_by == "expired":
            return self.last_input - self.started
        return self.elapsed

    def window(self):
        """The wall-clock span to attribute work to.

        Timezone-aware on purpose: activity providers parse ISO
        timestamps that carry an offset, and comparing those against a
        naive datetime raises.
        """
        from datetime import datetime, timedelta
        start = datetime.fromtimestamp(self.started_wall).astimezone()
        return start, start + timedelta(seconds=self.recorded_seconds())

    def close(self, extra=None):
        """Write the row. Returns it, or None if it was too short to count."""
        seconds = self.recorded_seconds()

        if seconds < MIN_SECONDS:
            return None

        self.presence.trim(round(seconds / self.sample))
        row = {"started": store.iso(self.started_wall),
               "ended": store.iso(self.started_wall + seconds),
               "seconds": int(round(seconds)),
               "gongs": self.gongs,
               "ended_by": self.ended_by or "you",
               "presence": self.presence.summary()}
        if extra:
            row.update(extra)
        self._sink(row)
        return row


def _default_gong(which):
    audio.ring(audio.BELL if which in ("start", "end") else audio.RECENTER)
