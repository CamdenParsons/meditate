"""The art ships as two layers that have to stay aligned."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medcore.display import FIGURE, RAYS, art_options, paint

ART = Path(__file__).resolve().parent.parent / "art"


class Layers(unittest.TestCase):
    def setUp(self):
        self.art = ART.joinpath("buddha.txt").read_text().rstrip("\n").split("\n")
        self.halo = ART.joinpath("halo.txt").read_text().rstrip("\n").split("\n")

    def test_the_two_layers_have_the_same_height(self):
        self.assertEqual(len(self.art), len(self.halo))

    def test_every_ray_sits_under_the_same_character(self):
        # they were once two rows out of step, which painted the whole
        # figure gold and no ray silver
        for row, (a, h) in enumerate(zip(self.art, self.halo)):
            for col, ch in enumerate(h):
                if ch != " ":
                    self.assertEqual(a[col], ch, f"row {row} col {col}")

    def test_the_halo_holds_no_part_of_the_figure(self):
        self.assertFalse(set("o8_'`").intersection("".join(self.halo)))

    def test_rays_paint_silver_and_the_figure_gold(self):
        painted = paint("/ o \\", "/   \\")
        self.assertIn(RAYS, painted)
        self.assertIn(FIGURE, painted)

    def test_art_with_no_halo_is_painted_one_colour(self):
        painted = paint("ooo", None)
        self.assertIn(FIGURE, painted)
        self.assertNotIn(RAYS, painted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
