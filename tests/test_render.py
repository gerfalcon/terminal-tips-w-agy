import unittest

from game.puzzle import build_grid, load_puzzle
from game.render import render_board, render_clues, render_page
from tests.snapshot import assert_matches_snapshot


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.puzzle = load_puzzle()

    def test_one_input_per_letter(self):
        board = render_board(self.puzzle)
        self.assertEqual(board.count("<input"), len(build_grid(self.puzzle)))
        self.assertEqual(board.count('class="block"'), 5 * 6 - len(build_grid(self.puzzle)))

    def test_clues_show_number_and_length(self):
        clues = render_clues(self.puzzle)
        self.assertIn("<b>1</b> What you type to the agent (6)", clues)
        self.assertLess(clues.index("Across"), clues.index("Down"))

    def test_page_matches_snapshot(self):
        assert_matches_snapshot(self, "terminal-1.html", render_page(self.puzzle))


if __name__ == "__main__":
    unittest.main()
