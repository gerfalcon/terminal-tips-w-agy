// The crossword in the browser: typing, moving between cells, and the Check button.
const inputs = [...document.querySelectorAll("input[data-cell]")];
const score = document.getElementById("score");
let direction = "across";

function cellAt(row, col) {
  return document.querySelector(`input[data-cell="${row},${col}"]`);
}

function move(input, dRow, dCol) {
  const [row, col] = input.dataset.cell.split(",").map(Number);
  const next = cellAt(row + dRow, col + dCol);
  if (next) next.focus();
}

const ARROWS = {
  ArrowRight: [0, 1, "across"],
  ArrowLeft: [0, -1, "across"],
  ArrowDown: [1, 0, "down"],
  ArrowUp: [-1, 0, "down"],
};

for (const input of inputs) {
  input.addEventListener("input", () => {
    input.value = input.value.slice(-1).toUpperCase();
    input.parentElement.classList.remove("right");
    if (input.value) move(input, direction === "down" ? 1 : 0, direction === "across" ? 1 : 0);
  });
  input.addEventListener("keydown", (event) => {
    if (ARROWS[event.key]) {
      const [dRow, dCol, dir] = ARROWS[event.key];
      direction = dir;
      move(input, dRow, dCol);
      event.preventDefault();
    } else if (event.key === "Backspace" && !input.value) {
      move(input, direction === "down" ? -1 : 0, direction === "across" ? -1 : 0);
    }
  });
}

document.getElementById("check").addEventListener("click", async () => {
  const entries = {};
  for (const input of inputs) {
    if (input.value) entries[input.dataset.cell] = input.value;
  }
  const response = await fetch("api/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ puzzle: document.body.dataset.puzzle, entries }),
  });
  if (!response.ok) {
    score.textContent = "Something went wrong. Look at the terminal that runs serve.py.";
    return;
  }
  const result = await response.json();
  document.querySelectorAll("td.right").forEach((td) => td.classList.remove("right"));
  for (const key of result.cells) cellAt(...key.split(",")).parentElement.classList.add("right");
  score.textContent = result.done
    ? `Solved! ${result.score} points.`
    : `${result.correct.length} of ${result.total} words right. ${result.score} points.`;
});
