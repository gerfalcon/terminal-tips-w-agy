# Leaderboard

When the player has solved the puzzle, they can save their name and score.
The page shows the five best scores for the puzzle.

- Scores are saved in `data/leaderboard.json`. Git ignores the `data/` folder.
- A name has 1 to 20 characters. Other names are refused.
- Equal scores: the earlier one ranks higher.

Done when: the project check passes, with tests for saving, ranking and a refused name.
