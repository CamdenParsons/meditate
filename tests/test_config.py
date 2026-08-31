"""Reading settings from a .env file."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medcore.config import load, parse


class Parsing(unittest.TestCase):
    def test_plain_pairs(self):
        self.assertEqual(parse("A=1\nB=two"), {"A": "1", "B": "two"})

    def test_ignores_blanks_and_comments(self):
        self.assertEqual(parse("\n# a note\n\nA=1\n  # indented\n"), {"A": "1"})

    def test_tolerates_a_leading_export(self):
        self.assertEqual(parse("export A=1"), {"A": "1"})

    def test_strips_one_layer_of_quotes(self):
        self.assertEqual(parse("A='1'\nB=\"two\""), {"A": "1", "B": "two"})

    def test_keeps_inner_punctuation(self):
        self.assertEqual(parse("URL=https://x/y?a=b"), {"URL": "https://x/y?a=b"})

    def test_skips_lines_that_are_not_assignments(self):
        self.assertEqual(parse("nonsense\n=novalue\nA=1"), {"A": "1"})


class Loading(unittest.TestCase):
    def _file(self, text):
        f = tempfile.NamedTemporaryFile("w", suffix=".env", delete=False)
        f.write(text); f.close()
        return Path(f.name)

    def test_sets_names_that_are_not_already_set(self):
        env = {}
        load([self._file("LINEAR_API_KEY=lin_abc")], env)
        self.assertEqual(env["LINEAR_API_KEY"], "lin_abc")

    def test_the_real_environment_always_wins(self):
        # so `LINEAR_API_KEY=other meditate 20` overrides the file
        env = {"LINEAR_API_KEY": "from_shell"}
        load([self._file("LINEAR_API_KEY=from_file")], env)
        self.assertEqual(env["LINEAR_API_KEY"], "from_shell")

    def test_the_first_file_wins_over_the_second(self):
        env = {}
        load([self._file("A=home"), self._file("A=repo")], env)
        self.assertEqual(env["A"], "home")

    def test_a_missing_file_is_not_an_error(self):
        env = {}
        load([Path("/nope/does/not/exist.env"), self._file("A=1")], env)
        self.assertEqual(env["A"], "1")

    def test_reports_what_it_set(self):
        env = {"B": "shell"}
        applied = load([self._file("A=1\nB=file")], env)
        self.assertEqual(applied, ["A"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
