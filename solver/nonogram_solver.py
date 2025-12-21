"""High-level Nonogram solver using propagation and optional backtracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from solver.line_solver import deduce_line
from solver.model import Grid, NonogramPuzzle, SolveResult


@dataclass
class PropagationState:
    grid: Grid
    changed: bool


def create_empty_grid(height: int, width: int) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def clone_grid(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def is_solved(grid: Grid) -> bool:
    return all(cell != 0 for row in grid for cell in row)


def apply_line_deductions(
    grid: Grid,
    row_clues: Sequence[Sequence[int]],
    col_clues: Sequence[Sequence[int]],
) -> PropagationState:
    """Apply one full row/column deduction pass.

    Raises:
        ValueError: when constraints become inconsistent.
    """

    height = len(grid)
    width = len(grid[0])
    changed = False

    for r in range(height):
        deduced = deduce_line(grid[r], row_clues[r])
        for c in range(width):
            if grid[r][c] == 0 and deduced[c] != 0:
                grid[r][c] = deduced[c]
                changed = True
            elif deduced[c] != 0 and grid[r][c] not in (0, deduced[c]):
                raise ValueError("Row contradiction during deduction")

    for c in range(width):
        column = [grid[r][c] for r in range(height)]
        deduced_col = deduce_line(column, col_clues[c])
        for r in range(height):
            if grid[r][c] == 0 and deduced_col[r] != 0:
                grid[r][c] = deduced_col[r]
                changed = True
            elif deduced_col[r] != 0 and grid[r][c] not in (0, deduced_col[r]):
                raise ValueError("Column contradiction during deduction")

    return PropagationState(grid=grid, changed=changed)


def propagate_until_stable(
    grid: Grid,
    row_clues: Sequence[Sequence[int]],
    col_clues: Sequence[Sequence[int]],
) -> Grid:
    while True:
        state = apply_line_deductions(grid, row_clues, col_clues)
        if not state.changed:
            return state.grid


def select_branch_cell(grid: Grid) -> Optional[Tuple[int, int]]:
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == 0:
                return (r, c)
    return None


def solve_nonogram(
    row_clues: Sequence[Sequence[int]],
    col_clues: Sequence[Sequence[int]],
    initial_grid: Optional[Grid] = None,
    max_solutions: int = 2,
) -> SolveResult:
    """Solve nonogram and report if puzzle has zero/one/multiple solutions."""

    puzzle = NonogramPuzzle(row_clues=row_clues, col_clues=col_clues, initial_grid=initial_grid)
    puzzle.validate()

    base_grid = clone_grid(initial_grid) if initial_grid is not None else create_empty_grid(
        puzzle.height, puzzle.width
    )

    from solver.backtracking import search_solutions  # lazy import to avoid circular dep

    solutions = search_solutions(
        base_grid=base_grid,
        row_clues=row_clues,
        col_clues=col_clues,
        max_solutions=max_solutions,
        propagate_fn=propagate_until_stable,
        pick_cell_fn=select_branch_cell,
    )

    if not solutions:
        return SolveResult(
            solved=False,
            has_multiple_solutions=False,
            no_solution=True,
            grid=None,
            solutions_checked=0,
        )

    return SolveResult(
        solved=True,
        has_multiple_solutions=len(solutions) > 1,
        no_solution=False,
        grid=solutions[0],
        solutions_checked=len(solutions),
    )
