"""Line-level deduction for Nonogram constraints."""

from __future__ import annotations

from functools import lru_cache
from typing import List, Sequence, Tuple

Cell = int


def _line_matches_known(candidate: Sequence[Cell], known: Sequence[Cell]) -> bool:
    return all(k == 0 or c == k for c, k in zip(candidate, known))


@lru_cache(maxsize=None)
def _build_patterns(length: int, clues: Tuple[int, ...]) -> Tuple[Tuple[Cell, ...], ...]:
    """Generate all valid line patterns for a line length and clue set."""

    if not clues:
        return (tuple([-1] * length),)

    patterns: List[Tuple[Cell, ...]] = []
    first_block = clues[0]
    remaining = clues[1:]

    remaining_min = 0
    if remaining:
        remaining_min = sum(remaining) + len(remaining)

    max_start = length - (first_block + remaining_min)

    for start in range(max_start + 1):
        prefix = [-1] * start
        block = [1] * first_block

        if remaining:
            suffix_length = length - (start + first_block + 1)
            for suffix in _build_patterns(suffix_length, remaining):
                patterns.append(tuple(prefix + block + [-1] + list(suffix)))
        else:
            tail = [-1] * (length - start - first_block)
            patterns.append(tuple(prefix + block + tail))

    return tuple(patterns)


def deduce_line(known: Sequence[Cell], clues: Sequence[int]) -> List[Cell]:
    """Return deduced line cells from known states and clues.

    Raises:
        ValueError: if the known cells are inconsistent with clues.
    """

    patterns = _build_patterns(len(known), tuple(clues))
    valid = [pattern for pattern in patterns if _line_matches_known(pattern, known)]

    if not valid:
        raise ValueError("No valid line pattern matches known cells")

    deduced: List[Cell] = []
    for idx in range(len(known)):
        values = {pattern[idx] for pattern in valid}
        deduced.append(values.pop() if len(values) == 1 else 0)

    return deduced
