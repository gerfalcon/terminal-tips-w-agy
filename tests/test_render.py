import unittest

from game.puzzle import load_puzzle
from game.render import render_page
from tests.snapshot import assert_matches_snapshot


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.puzzle = load_puzzle()

    def test_page_matches_snapshot(self):
        assert_matches_snapshot(self, "terminal-1.html", render_page(self.puzzle))


if __name__ == "__main__":
    unittest.main()
