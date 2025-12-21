"""Tri-state nonogram grid widget based on QTableWidget."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

Cell = int  # -1 empty/X, 0 unknown, 1 filled


class GridWidget(QTableWidget):
    """Editable tri-state grid.

    Left-click toggles: unknown <-> filled.
    Right-click toggles: unknown <-> empty(X).
    """

    def __init__(self, size: int = 10, parent=None) -> None:
        super().__init__(size, size, parent)
        self._size = size
        self._init_table()

    def _init_table(self) -> None:
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setDefaultSectionSize(28)
        self.verticalHeader().setDefaultSectionSize(28)
        self.setShowGrid(True)
        for r in range(self._size):
            for c in range(self._size):
                self._set_cell_item(r, c, 0)

    def resize_grid(self, size: int) -> None:
        self._size = size
        self.setRowCount(size)
        self.setColumnCount(size)
        for r in range(size):
            for c in range(size):
                self._set_cell_item(r, c, 0)

    def mousePressEvent(self, event):  # noqa: N802
        item = self.itemAt(event.position().toPoint())
        if item is None:
            super().mousePressEvent(event)
            return

        row = item.row()
        col = item.column()
        current = int(item.data(Qt.UserRole) or 0)

        if event.button() == Qt.LeftButton:
            next_state = 0 if current == 1 else 1
            self._set_cell_item(row, col, next_state)
            return

        if event.button() == Qt.RightButton:
            next_state = 0 if current == -1 else -1
            self._set_cell_item(row, col, next_state)
            return

        super().mousePressEvent(event)

    def _set_cell_item(self, row: int, col: int, state: Cell) -> None:
        item = self.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        item.setData(Qt.UserRole, state)
        if state == 1:
            item.setText("")
            item.setBackground(QBrush(QColor("black")))
            item.setForeground(QBrush(QColor("white")))
        elif state == -1:
            item.setText("X")
            item.setBackground(QBrush(QColor("white")))
            item.setForeground(QBrush(QColor("red")))
        else:
            item.setText("")
            item.setBackground(QBrush(QColor("white")))
            item.setForeground(QBrush(QColor("black")))

    def set_grid(self, grid: List[List[Cell]]) -> None:
        size = len(grid)
        if size != self._size or any(len(row) != self._size for row in grid):
            self.resize_grid(size)
        for r, row in enumerate(grid):
            for c, state in enumerate(row):
                self._set_cell_item(r, c, state)

    def get_grid(self) -> List[List[Cell]]:
        grid: List[List[Cell]] = []
        for r in range(self._size):
            row: List[Cell] = []
            for c in range(self._size):
                item = self.item(r, c)
                row.append(int(item.data(Qt.UserRole) or 0))
            grid.append(row)
        return grid

    def clear_grid(self) -> None:
        for r in range(self._size):
            for c in range(self._size):
                self._set_cell_item(r, c, 0)
