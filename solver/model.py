"""Core data model for nonogram puzzles and solver results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

Cell = int  # -1 empty, 0 unknown, 1 filled
Grid = List[List[Cell]]
Clues = Sequence[Sequence[int]]


@dataclass(frozen=True)
class NonogramPuzzle:
    """Static puzzle description.

    Attributes:
        row_clues: Sequence of row clue groups.
        col_clues: Sequence of column clue groups.
        initial_grid: Optional starting grid with known cell states.
    """

    row_clues: Clues
    col_clues: Clues
    initial_grid: Optional[Grid] = None

    @property
    def height(self) -> int:
        return len(self.row_clues)

    @property
    def width(self) -> int:
        return len(self.col_clues)

    def validate(self) -> None:
        """Validate clues, dimensions, and optional initial grid."""
        if self.height == 0 or self.width == 0:
            raise ValueError("Puzzle must have at least one row and one column")

        for clue_set in list(self.row_clues) + list(self.col_clues):
            if any(block <= 0 for block in clue_set):
                raise ValueError("Clues must be positive integers")

        for clues, size, axis in (
            (self.row_clues, self.width, "row"),
            (self.col_clues, self.height, "column"),
        ):
            for idx, group in enumerate(clues):
                minimum_size = sum(group) + max(0, len(group) - 1)
                if minimum_size > size:
                    raise ValueError(
                        f"{axis.capitalize()} clue at index {idx} does not fit line length"
                    )

        if self.initial_grid is not None:
            if len(self.initial_grid) != self.height:
                raise ValueError("Initial grid row count does not match row clues")
            for row in self.initial_grid:
                if len(row) != self.width:
                    raise ValueError("Initial grid column count does not match column clues")
                for cell in row:
                    if cell not in (-1, 0, 1):
                        raise ValueError("Grid cells must be one of -1, 0, 1")


@dataclass
class SolveResult:
    """Result object for solver output."""

    solved: bool
    has_multiple_solutions: bool
    no_solution: bool
    grid: Optional[Grid]
    solutions_checked: int
