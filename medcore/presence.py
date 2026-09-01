"""Presence: whether the human was touching the machine, second by second.

The domain module behind the whole app. Callers hand it one boolean per
sample and ask it questions; how those are stored, bucketed and read is
its own business.

Presence is reported, never judged. Whether input during a session is
distraction or engagement depends on what you sat down to do, and the
app does not know that - so it shows the numbers and lets you read them.
"""

BUCKETS = 34        # how many columns a timeline is summarised into
MINUTE = 60         # samples per bucket when measuring steadiness
MIN_MINUTES = 5     # below this there is not enough shape to judge


class PresenceLog:
    """A run of per-sample presence flags.

    Interface: record() one sample at a time, then summary() for the
    stats, or trim() first to drop trailing absence. Cheap to keep in
    memory - one bool per second is 3.6k booleans an hour.
    """

    def __init__(self, samples=None):
        self._samples = list(samples or [])
        self._still = 0
        for s in self._samples:
            self._still = 0 if s else self._still + 1

    def record(self, present):
        present = bool(present)
        self._samples.append(present)
        self._still = 0 if present else self._still + 1

    @property
    def still_for(self):
        """Samples since the last input. Zero means input just now."""
        return self._still

    def __len__(self):
        return len(self._samples)

    def trim(self, keep):
        """Drop everything past `keep` samples - used to cut trailing idle."""
        self._samples = self._samples[:max(1, int(keep))]
        return self

    def evenness(self):
        """How evenly the input was spread, 0 to 100, or None.

        A description of shape, not a score. High is not better: thinking
        then typing is the natural rhythm of programming, and a session
        that reads for ten minutes and writes for five is uneven by
        construction and none the worse for it. It is here because an
        hour of level work and an hour of bursts against empty stretches
        can share an input percentage and look nothing alike.

        None when the arithmetic would outrun the meaning: a session
        under a few minutes, or one with almost no input, where the
        coefficient of variation is mostly noise.
        """
        minutes = [self._samples[i:i + MINUTE]
                   for i in range(0, len(self._samples), MINUTE)]
        minutes = [sum(m) / len(m) for m in minutes if m]
        if len(minutes) < MIN_MINUTES:
            return None
        mean = sum(minutes) / len(minutes)
        if mean < 0.02:
            return None
        var = sum((x - mean) ** 2 for x in minutes) / len(minutes)
        cv = (var ** 0.5) / mean
        return round(max(0.0, min(100.0, (1 - cv) * 100)))

    def summary(self):
        n = len(self._samples)
        if not n:
            return None
        size = max(1, -(-n // BUCKETS))
        buckets = ""
        for i in range(0, n, size):
            chunk = self._samples[i:i + size]
            buckets += str(min(8, int(round(sum(chunk) / len(chunk) * 8))))
        longest = run = 0
        for s in self._samples:
            run = 0 if s else run + 1
            longest = max(longest, run)
        bursts = sum(1 for i, s in enumerate(self._samples)
                     if s and (i == 0 or not self._samples[i - 1]))
        out = {"samples": n, "present": sum(self._samples),
               "longest_still": longest, "bursts": bursts, "buckets": buckets}
        even = self.evenness()
        if even is not None:
            out["even"] = even
        return out


def percent(summary):
    if not summary or not summary.get("samples"):
        return 0.0
    return summary["present"] / summary["samples"] * 100


def describe(summary):
    """A neutral one-line reading. No judgement - just the shape."""
    if not summary:
        return ""
    pct = percent(summary)
    still = summary.get("longest_still", 0)
    line = (f"{pct:.0f}% input, longest still stretch "
            f"{still // 60:d}:{still % 60:02d}, {summary.get('bursts', 0)} bursts")
    if summary.get("even") is not None:
        line += f", {summary['even']}% even"
    return line


def read_summary(row):
    """Pull the summary out of a stored row, tolerating older shapes."""
    a = row.get("presence") or row.get("activity")
    if not a:
        return None
    if "buckets" not in a and "spark" in a:      # rows from before buckets
        table = {" ": "0", "\u2581": "1", "\u2582": "2", "\u2583": "3", "\u2584": "4",
                 "\u2585": "5", "\u2586": "6", "\u2587": "7", "\u2588": "8"}
        a = dict(a, buckets="".join(table.get(c, "0") for c in a["spark"]))
    a.setdefault("present", a.get("active", 0))
    if "even" not in a and "steady" in a:      # rows written before the rename
        a["even"] = a["steady"]
    return a
