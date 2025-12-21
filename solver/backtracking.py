"""Backtracking search for nonogram solutions."""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

from solver.model import Grid

PropagateFn = Callable[[Grid, Sequence[Sequence[int]], Sequence[Sequence[int]]], Grid]
PickCellFn = Callable[[Grid], Optional[Tuple[int, int]]]


def _clone_grid(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def search_solutions(
    base_grid: Grid,
    row_clues: Sequence[Sequence[int]],
    col_clues: Sequence[Sequence[int]],
    max_solutions: int,
    propagate_fn: PropagateFn,
    pick_cell_fn: PickCellFn,
) -> List[Grid]:
    """Find up to max_solutions for the puzzle."""

    solutions: List[Grid] = []

    def dfs(grid: Grid) -> None:
        if len(solutions) >= max_solutions:
            return

        try:
            reduced = propagate_fn(_clone_grid(grid), row_clues, col_clues)
        except ValueError:
            return

        next_cell = pick_cell_fn(reduced)
        if next_cell is None:
            solutions.append(reduced)
            return

        r, c = next_cell
        for guess in (1, -1):
            branched = _clone_grid(reduced)
            branched[r][c] = guess
            dfs(branched)
            if len(solutions) >= max_solutions:
                return

    dfs(base_grid)
    return solutions
