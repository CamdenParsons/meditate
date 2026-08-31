"""The activity provider seam: composition, isolation, selection."""
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medcore import activity
from medcore.activity.tickets import Provider as Tickets, ids_in

WINDOW = (datetime(2026, 8, 28, 16), datetime(2026, 8, 28, 18))


class Fake:
    def __init__(self, name, result=None, boom=False):
        self.name, self.result, self.boom = name, result, boom
        self.saw = None

    def collect(self, window, found):
        self.saw = dict(found)
        if self.boom:
            raise RuntimeError("provider exploded")
        return self.result


class Isolation(unittest.TestCase):
    def test_a_provider_that_raises_does_not_stop_the_others(self):
        good = Fake("good", ["a"])
        out = activity.collect(*WINDOW, providers=[Fake("bad", boom=True), good])
        self.assertEqual(out, {"good": ["a"]})

    def test_a_provider_finding_nothing_is_left_out_entirely(self):
        out = activity.collect(*WINDOW, providers=[Fake("empty", []),
                                                   Fake("none", None),
                                                   Fake("some", ["x"])])
        self.assertEqual(out, {"some": ["x"]})

    def test_nothing_found_at_all_is_an_empty_dict(self):
        self.assertEqual(activity.collect(*WINDOW, providers=[Fake("a", [])]), {})


class Composition(unittest.TestCase):
    def test_later_providers_see_what_earlier_ones_found(self):
        second = Fake("second", ["ok"])
        activity.collect(*WINDOW, providers=[Fake("first", ["one"]), second])
        self.assertEqual(second.saw, {"first": ["one"]})

    def test_a_failed_provider_contributes_nothing_downstream(self):
        second = Fake("second", ["ok"])
        activity.collect(*WINDOW, providers=[Fake("first", boom=True), second])
        self.assertEqual(second.saw, {})


class Selection(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("MEDITATE_ACTIVITY", None)

    def test_all_providers_run_by_default(self):
        self.assertEqual(len(activity.enabled()), len(activity.PROVIDERS))

    def test_the_env_var_narrows_them(self):
        os.environ["MEDITATE_ACTIVITY"] = "claude,tickets"
        self.assertEqual([p.name for p in activity.enabled()],
                         ["claude", "tickets"])


class TicketIds(unittest.TestCase):
    def test_reads_ids_from_upper_and_lower_case(self):
        self.assertEqual(ids_in("fix ACME-482"), {"ACME-482"})
        self.assertEqual(ids_in("acme-491-retries"), {"ACME-491"})

    def test_ignores_things_that_merely_look_like_ids(self):
        self.assertEqual(ids_in("bump gpt-4, sha-256, utf-8"), set())

    def test_gathers_across_every_provider_above_it(self):
        found = {
            "github": {"prs": [{"title": "does ACME-1"}],
                       "pushes": [{"ref": "feat-acme-2", "commits": ["and ACME-3"]}],
                       "branches": [{"ref": "acme-4-thing"}]},
            "commits": [{"subject": "local ACME-5"}],
            "claude": [{"branch": "acme-6-branch"}],
        }
        self.assertEqual(Tickets().collect(WINDOW, found),
                         ["ACME-1", "ACME-2", "ACME-3", "ACME-4", "ACME-5", "ACME-6"])


class SessionWindow(unittest.TestCase):
    """The window a Session hands to providers must be comparable to theirs."""

    def test_window_is_timezone_aware(self):
        # Providers parse ISO timestamps carrying an offset. A naive
        # window raises on comparison, and the failure is swallowed - so
        # every provider silently returns nothing. Regression test.
        import time
        from medcore.session import Session
        s = Session(duration=600, interval=0, expire=3600, idle=lambda: 0.0,
                    gong=lambda x: None, sink=lambda r: None)
        s.started_wall = time.time() - 600
        s.ended_by = "duration"
        start, end = s.window()
        self.assertIsNotNone(start.tzinfo)
        self.assertIsNotNone(end.tzinfo)
        aware = datetime.now().astimezone()
        self.assertIsInstance(start <= aware, bool)   # would raise if naive

    def test_window_length_matches_the_recorded_length(self):
        import time
        from medcore.session import Session
        s = Session(duration=600, interval=0, expire=3600, idle=lambda: 0.0,
                    gong=lambda x: None, sink=lambda r: None)
        s.started_wall = time.time() - 600
        s.ended_by = "duration"
        start, end = s.window()
        self.assertAlmostEqual((end - start).total_seconds(), 600, delta=1)


class ShowIndex(unittest.TestCase):
    """`show` and `log` share -n but want different defaults."""

    def _pick(self, rows, number):
        nth = max(number or 1, 1)            # the rule cli._show uses
        return rows[-min(nth, len(rows))]

    def test_show_defaults_to_the_most_recent_session(self):
        rows = list(range(7))
        # -n defaults to 25 for log; reusing it here once returned rows[-7]
        self.assertEqual(self._pick(rows, None), 6)

    def test_show_counts_backwards_when_asked(self):
        rows = list(range(7))
        self.assertEqual(self._pick(rows, 2), 5)

    def test_show_clamps_past_the_oldest(self):
        rows = list(range(3))
        self.assertEqual(self._pick(rows, 99), 0)


class LinearProvider(unittest.TestCase):
    """The one provider needing a credential, and the gap it closes."""

    # the shape Linear's GraphQL actually returns
    RESPONSE = {"data": {"issues": {"nodes": [
        {"identifier": "ACME-480", "title": "Retry the webhook dispatcher on 5xx",
         "url": "https://linear.app/acme/ACME-480", "updatedAt": "2026-08-31T14:25:19Z",
         "state": {"name": "Canceled"}},
        {"identifier": "ACME-675", "title": "Paginate the audit endpoint",
         "url": "https://linear.app/acme/ACME-675", "updatedAt": "2026-08-31T15:33:39Z",
         "state": {"name": "Backlog"}},
    ]}}}

    def setUp(self):
        from medcore.activity.linear import Provider
        self.Provider = Provider

    def tearDown(self):
        os.environ.pop("LINEAR_API_KEY", None)

    def test_without_a_key_it_simply_finds_nothing(self):
        called = []
        p = self.Provider(post=lambda *a: called.append(a) or self.RESPONSE)
        self.assertEqual(p.collect(WINDOW, {}), [])
        self.assertEqual(called, [], "must not call out without a key")

    def test_with_a_key_it_reports_id_title_and_status(self):
        os.environ["LINEAR_API_KEY"] = "lin_api_test"
        p = self.Provider(post=lambda payload, key: self.RESPONSE)
        got = p.collect(WINDOW, {})
        self.assertEqual([i["id"] for i in got], ["ACME-480", "ACME-675"])
        self.assertEqual(got[0]["status"], "Canceled")
        self.assertEqual(got[1]["title"], "Paginate the audit endpoint")

    def test_the_window_is_sent_as_the_filter(self):
        os.environ["LINEAR_API_KEY"] = "lin_api_test"
        seen = {}
        def fake(payload, key):
            seen.update(payload["variables"])
            return self.RESPONSE
        self.Provider(post=fake).collect(WINDOW, {})
        self.assertEqual(seen["from"], WINDOW[0].isoformat())
        self.assertEqual(seen["to"], WINDOW[1].isoformat())

    def test_a_network_failure_is_not_a_failed_session(self):
        os.environ["LINEAR_API_KEY"] = "lin_api_test"
        def boom(payload, key):
            raise OSError("no network")
        self.assertEqual(self.Provider(post=boom).collect(WINDOW, {}), [])

    def test_a_garbled_response_is_not_a_failed_session(self):
        os.environ["LINEAR_API_KEY"] = "lin_api_test"
        p = self.Provider(post=lambda payload, key: {"errors": ["nope"]})
        self.assertEqual(p.collect(WINDOW, {}), [])

    def test_ids_linear_reported_in_full_are_not_repeated_as_bare_tickets(self):
        found = {"linear": [{"id": "ACME-576", "title": "t", "status": "Done"}],
                 "commits": [{"subject": "work on ACME-576 and ACME-999"}]}
        self.assertEqual(Tickets().collect(WINDOW, found), ["ACME-999"])


class Rollup(unittest.TestCase):
    """The session list shows counts; `show` shows the records."""

    def _r(self, prog):
        from medcore.display import rollup
        return rollup(prog, colour=False)

    def test_nothing_found_is_an_empty_line(self):
        self.assertEqual(self._r({}), "")
        self.assertEqual(self._r(None), "")

    def test_counts_each_kind_of_work(self):
        got = self._r({
            "claude": [{}, {}, {}],
            "linear": [{"id": "ACME-1"}, {"id": "ACME-2"}],
            "github": {"prs": [{}], "branches": [{}, {}, {}]},
            "commits": [{}, {}],
        })
        self.assertIn("claude (3 sessions)", got)
        self.assertIn("linear (2 issues)", got)
        self.assertIn("github (1 PR, 3 branches)", got)
        self.assertIn("2 commits", got)

    def test_singular_reads_correctly(self):
        got = self._r({"claude": [{}], "commits": [{}],
                       "github": {"branches": [{}], "prs": [{}]}})
        self.assertIn("claude (1 session)", got)
        self.assertIn("1 commit", got)
        self.assertIn("github (1 PR, 1 branch)", got)

    def test_a_few_ticket_ids_are_shown_but_many_are_counted(self):
        self.assertIn("ACME-1 ACME-2", self._r({"tickets": ["ACME-1", "ACME-2"]}))
        self.assertIn("5 tickets",
                      self._r({"tickets": [f"ACME-{i}" for i in range(5)]}))

    def test_empty_provider_results_are_left_out(self):
        self.assertEqual(self._r({"claude": [], "github": {}, "commits": []}), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
