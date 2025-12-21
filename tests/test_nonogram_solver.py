import time
import unittest

from solver.nonogram_solver import solve_nonogram


def clues_from_grid(grid):
    def line_clues(line):
        runs = []
        run = 0
        for cell in line:
            if cell == 1:
                run += 1
            elif run:
                runs.append(run)
                run = 0
        if run:
            runs.append(run)
        return runs

    rows = [line_clues(row) for row in grid]
    cols = [line_clues([grid[r][c] for r in range(len(grid))]) for c in range(len(grid[0]))]
    return rows, cols


def assert_grid_matches_clues(testcase, grid, row_clues, col_clues):
    built_rows, built_cols = clues_from_grid(grid)
    testcase.assertEqual(built_rows, row_clues)
    testcase.assertEqual(built_cols, col_clues)


class TestNonogramSolver(unittest.TestCase):
    def assertSolvedMatches(self, expected):
        row_clues, col_clues = clues_from_grid(expected)
        result = solve_nonogram(row_clues, col_clues)
        self.assertTrue(result.solved)
        self.assertFalse(result.no_solution)
        self.assertEqual(result.grid, expected)

    def test_solve_5x5(self):
        expected = [
            [1, 1, 1, 1, 1],
            [1, -1, -1, -1, 1],
            [1, -1, 1, -1, 1],
            [1, -1, -1, -1, 1],
            [1, 1, 1, 1, 1],
        ]
        self.assertSolvedMatches(expected)

    def test_solve_10x10(self):
        template = [
            [1, -1, 1, 1, -1, -1, 1, -1, -1, 1],
            [1, -1, -1, 1, -1, 1, 1, 1, -1, -1],
            [-1, 1, 1, 1, -1, -1, -1, 1, -1, 1],
            [1, -1, -1, -1, 1, 1, -1, -1, 1, -1],
            [1, 1, -1, 1, -1, -1, 1, -1, 1, -1],
            [-1, 1, -1, 1, 1, -1, -1, 1, -1, 1],
            [1, -1, 1, -1, -1, 1, -1, 1, 1, -1],
            [-1, 1, -1, 1, -1, 1, 1, -1, -1, 1],
            [1, -1, -1, 1, 1, -1, -1, 1, -1, 1],
            [-1, 1, 1, -1, -1, 1, -1, -1, 1, -1],
        ]
        row_clues, col_clues = clues_from_grid(template)
        result = solve_nonogram(row_clues, col_clues)

        self.assertTrue(result.solved)
        self.assertFalse(result.no_solution)
        self.assertIsNotNone(result.grid)
        assert_grid_matches_clues(self, result.grid, row_clues, col_clues)

    def test_solve_15x15_under_time_limit(self):
        expected = [
            [-1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, 1, 1, 1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1],
            [-1, -1, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1],
            [-1, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1],
            [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
            [-1, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1],
            [-1, -1, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1],
            [-1, -1, -1, -1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, 1, 1, 1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1],
        ]
        row_clues, col_clues = clues_from_grid(expected)

        start = time.time()
        result = solve_nonogram(row_clues, col_clues)
        elapsed = time.time() - start

        self.assertTrue(result.solved)
        self.assertEqual(result.grid, expected)
        self.assertLess(elapsed, 200)


if __name__ == "__main__":
    unittest.main()
