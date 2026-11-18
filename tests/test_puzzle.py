import copy
import unittest

from game.puzzle import POINTS_PER_WORD, build_grid, check_answers, load_puzzle, numbers

SOLUTION = {
    "0,0": "P", "0,1": "R", "0,2": "O", "0,3": "M", "0,4": "P", "0,5": "T",
    "1,0": "L", "1,3": "E", "1,5": "E",
    "2,0": "A", "2,2": "A", "2,3": "R", "2,4": "G", "2,5": "S",
    "3,0": "N", "3,3": "G", "3,5": "T",
    "4,1": "O", "4,2": "P", "4,3": "E", "4,4": "N",
}


class PuzzleTests(unittest.TestCase):
    def setUp(self):
        self.puzzle = load_puzzle()

    def test_first_puzzle_is_the_default(self):
        self.assertEqual(self.puzzle["id"], "terminal-1")
        self.assertEqual(load_puzzle("terminal-1")["title"], "Terminal words")

    def test_unknown_puzzle_is_an_error(self):
        with self.assertRaises(KeyError):
            load_puzzle("no-such-puzzle")

    def test_words_fit_together(self):
        grid = build_grid(self.puzzle)
        self.assertEqual(len(grid), len(SOLUTION))
        self.assertEqual(grid[(2, 3)], "R")  # ARGS crosses MERGE

    def test_clashing_words_are_reported(self):
        broken = copy.deepcopy(self.puzzle)
        broken["words"][0]["answer"] = "PROMPS"  # T would clash with TEST
        with self.assertRaises(ValueError):
            build_grid(broken)

    def test_word_off_the_board_is_reported(self):
        broken = copy.deepcopy(self.puzzle)
        broken["words"][0]["col"] = 3
        with self.assertRaises(ValueError):
            build_grid(broken)

    def test_numbers_follow_reading_order(self):
        self.assertEqual(numbers(self.puzzle), {(0, 0): 1, (0, 3): 2, (0, 5): 3, (2, 2): 4, (4, 1): 5})

    def test_empty_board_scores_nothing(self):
        result = check_answers(self.puzzle, {})
        self.assertEqual(result["score"], 0)
        self.assertFalse(result["done"])

    def test_one_right_word_scores_points(self):
        result = check_answers(self.puzzle, {"0,0": "P", "1,0": "L", "2,0": "A", "3,0": "N"})
        self.assertEqual(result["correct"], ["1D"])
        self.assertEqual(result["score"], POINTS_PER_WORD)
        self.assertEqual(result["cells"], ["0,0", "1,0", "2,0", "3,0"])

    def test_lowercase_and_spaces_are_fine(self):
        result = check_answers(self.puzzle, {"0,0": " p", "1,0": "l", "2,0": "a ", "3,0": "n"})
        self.assertEqual(result["correct"], ["1D"])

    def test_full_solution_is_done(self):
        result = check_answers(self.puzzle, SOLUTION)
        self.assertTrue(result["done"])
        self.assertEqual(result["score"], POINTS_PER_WORD * 6)


if __name__ == "__main__":
    unittest.main()
