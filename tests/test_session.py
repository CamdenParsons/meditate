"""Component tests for the Session ending rules, on a fake clock."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medcore.session import Session


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t
    def advance(self, s): self.t += s


class Rig:
    """Drives a Session second by second with scripted presence."""
    def __init__(self, present_until=None, **kw):
        self.clock = Clock()
        self.rows, self.gongs = [], []
        self.present_until = present_until
        self.s = Session(now=self.clock, idle=self.idle,
                         gong=lambda w: self.gongs.append((self.clock.t, w)),
                         sink=self.rows.append, **kw)
        self.s.start()

    def idle(self):
        if self.present_until is None or self.clock.t <= self.present_until:
            return 0.0          # a hand on the keyboard
        return self.clock.t - self.present_until

    def run(self, limit=100000):
        while not self.s.done() and self.clock.t < limit:
            self.clock.advance(1.0)
            self.s.tick()
        return self.s.close()


class FixedDuration(unittest.TestCase):
    def test_ends_by_duration_at_exactly_the_length(self):
        r = Rig(duration=600, interval=0)
        row = r.run()
        self.assertEqual(r.s.ended_by, "duration")
        self.assertEqual(row["seconds"], 600)


class Expiry(unittest.TestCase):
    def test_expired_session_ends_at_last_input_not_at_expiry(self):
        # present for 100s, then walks away. expiry is 60s.
        r = Rig(present_until=100, interval=0, expire=60)
        row = r.run()
        self.assertEqual(r.s.ended_by, "expired")
        self.assertAlmostEqual(row["seconds"], 100, delta=2)
        self.assertLess(r.clock.t, 200)          # it did notice promptly

    def test_a_long_absence_does_not_inflate_the_log(self):
        r = Rig(present_until=60, interval=0, expire=60)
        row = r.run()
        self.assertLess(row["seconds"], 70)

    def test_presence_never_expires_while_you_keep_working(self):
        r = Rig(present_until=None, duration=300, interval=0, expire=60)
        row = r.run()
        self.assertEqual(r.s.ended_by, "duration")


class TooShort(unittest.TestCase):
    def test_a_misfire_is_not_recorded(self):
        r = Rig(present_until=5, interval=0, expire=10)
        self.assertIsNone(r.run())
        self.assertEqual(r.rows, [])


class Gongs(unittest.TestCase):
    def test_interval_gongs_fire_on_schedule(self):
        r = Rig(duration=3600, interval=900)
        r.run()
        times = [t for t, w in r.gongs if w == "interval"]
        self.assertEqual(times, [900, 1800, 2700, 3600][:len(times)])

    def test_no_gong_at_an_empty_desk_when_open_ended(self):
        # walks away at 10s. by the time the 5-minute gong is due the desk
        # has been empty far longer than the "still here" grace, so silence.
        r = Rig(present_until=10, interval=300, expire=3600)
        while r.clock.t < 1200:
            r.clock.advance(1.0); r.s.tick()
        self.assertEqual([w for _, w in r.gongs if w == "interval"], [])

    def test_it_does_gong_while_you_are_actually_there(self):
        r = Rig(present_until=None, interval=300, expire=3600)
        while r.clock.t < 1200:
            r.clock.advance(1.0); r.s.tick()
        self.assertEqual([t for t, w in r.gongs if w == "interval"],
                         [300, 600, 900, 1200])

    def test_a_fixed_sit_still_gongs_even_though_you_are_motionless(self):
        # the whole point of meditation: no input, but the bell must ring
        r = Rig(present_until=0, duration=600, interval=300, expire=3600)
        r.run()
        self.assertGreaterEqual(len([w for _, w in r.gongs if w == "interval"]), 1)


class PresenceShape(unittest.TestCase):
    def test_buckets_reflect_when_you_were_active(self):
        r = Rig(present_until=300, duration=600, interval=0)
        row = r.run()
        b = row["presence"]["buckets"]
        self.assertGreater(int(b[0]), 6)         # busy at the start
        self.assertEqual(int(b[-1]), 0)          # still at the end

    def test_ended_by_is_recorded(self):
        r = Rig(duration=60, interval=0)
        self.assertEqual(r.run()["ended_by"], "duration")


class ClosingGong(unittest.TestCase):
    def test_a_finished_session_rings_at_the_end(self):
        r = Rig(duration=60, interval=0)
        r.run()
        self.assertTrue(r.s.rings_at_end)

    def test_ending_by_hand_rings_at_the_end(self):
        r = Rig(interval=0)
        r.clock.advance(60); r.s.tick(); r.s.end()
        self.assertTrue(r.s.rings_at_end)

    def test_an_expired_session_does_not_ring_into_an_empty_room(self):
        r = Rig(present_until=100, interval=0, expire=60)
        r.run()
        self.assertEqual(r.s.ended_by, "expired")
        self.assertFalse(r.s.rings_at_end)

    def test_the_logged_gong_count_matches_what_you_heard(self):
        r = Rig(duration=600, interval=150)
        heard = 1                                  # the opening gong
        r.run()
        heard += len([w for _, w in r.gongs if w == "interval"])
        if r.s.rings_at_end:
            r.s.gongs += 1                         # what the cli does
            heard += 1
        self.assertEqual(r.s.close()["gongs"], heard)


class BadInput(unittest.TestCase):
    """Nonsense settings should be refused, not obeyed."""

    def _run(self, argv):
        from medcore.cli import main
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_a_negative_interval_is_refused(self):
        # it used to be obeyed: every tick was "overdue", so a one minute
        # session rang sixty times
        code, out = self._run(["10", "-i", "-5"])
        self.assertEqual(code, 1)
        self.assertIn("cannot be negative", out)

    def test_a_negative_expiry_is_refused(self):
        # it used to expire the session on the first tick
        code, out = self._run(["10", "-e", "-5"])
        self.assertEqual(code, 1)
        self.assertIn("cannot be negative", out)

    def test_a_zero_length_session_is_refused(self):
        code, out = self._run(["0"])
        self.assertEqual(code, 1)

    def test_a_word_that_is_not_a_command_is_refused(self):
        code, out = self._run(["banana"])
        self.assertEqual(code, 1)
        self.assertIn("Don't know", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
