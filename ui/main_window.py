"""Main UI for editable nonogram board + image import + overlay export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from image_processing.image_loader import ParsedNonogramPuzzle, load_puzzle_from_image
from overlay.overlay_renderer import export_overlay_png, render_overlay_on_image
from solver.nonogram_solver import solve_nonogram
from ui.grid_widget import GridWidget


def parse_clue_text(text: str) -> List[int]:
    stripped = text.strip()
    if not stripped:
        return []
    values: List[int] = []
    for token in stripped.replace(",", " ").split():
        value = int(token)
        if value <= 0:
            raise ValueError("Clue values must be positive integers")
        values.append(value)
    return values


@dataclass
class SolvePayload:
    row_clues: List[List[int]]
    col_clues: List[List[int]]
    initial_grid: List[List[int]]


class SolveWorker(QObject):
    finished = Signal(object, str)

    def __init__(self, payload: SolvePayload) -> None:
        super().__init__()
        self._payload = payload

    def run(self) -> None:
        try:
            result = solve_nonogram(
                row_clues=self._payload.row_clues,
                col_clues=self._payload.col_clues,
                initial_grid=self._payload.initial_grid,
            )
            self.finished.emit(result, "")
        except Exception as exc:
            self.finished.emit(None, str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Nonogram Solver - Phase 4 UI")
        self.setAcceptDrops(True)

        self._thread: QThread | None = None
        self._worker: SolveWorker | None = None
        self._parsed_puzzle: Optional[ParsedNonogramPuzzle] = None
        self._last_solution: Optional[List[List[int]]] = None

        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 30)
        self.size_spin.setValue(10)
        self.size_spin.valueChanged.connect(self._resize_board)

        self.import_button = QPushButton("导入截图")
        self.import_button.clicked.connect(self._import_image)

        self.solve_button = QPushButton("求解")
        self.solve_button.clicked.connect(self._solve)

        self.preview_overlay_button = QPushButton("预览叠加")
        self.preview_overlay_button.clicked.connect(self._preview_overlay)

        self.export_overlay_button = QPushButton("导出 PNG")
        self.export_overlay_button.clicked.connect(self._export_overlay)

        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self._reset)

        self.about_button = QPushButton("关于")
        self.about_button.clicked.connect(self._show_about)

        self.drop_hint = QLabel("拖拽数织截图到窗口，或点击“导入截图”")

        self.row_clue_table = QTableWidget(10, 1)
        self.col_clue_table = QTableWidget(1, 10)
        self._init_clue_tables(10)

        self.grid_widget = GridWidget(10)

        self.overlay_preview = QLabel("叠加预览区")
        self.overlay_preview.setMinimumSize(320, 240)
        self.overlay_preview.setStyleSheet("border: 1px solid #888;")

        controls = QHBoxLayout()
        controls.addWidget(QLabel("尺寸 N:"))
        controls.addWidget(self.size_spin)
        controls.addWidget(self.import_button)
        controls.addStretch(1)
        controls.addWidget(self.solve_button)
        controls.addWidget(self.preview_overlay_button)
        controls.addWidget(self.export_overlay_button)
        controls.addWidget(self.reset_button)
        controls.addWidget(self.about_button)

        board_layout = QVBoxLayout()
        board_layout.addWidget(self.drop_hint)
        board_layout.addWidget(QLabel("列提示（双击编辑，如：2 1 3）"))
        board_layout.addWidget(self.col_clue_table)

        lower = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("行提示（双击编辑）"))
        left.addWidget(self.row_clue_table)
        lower.addLayout(left)
        lower.addWidget(self.grid_widget, stretch=2)
        lower.addWidget(self.overlay_preview, stretch=1)

        board_layout.addLayout(lower)

        root = QVBoxLayout()
        root.addLayout(controls)
        root.addLayout(board_layout)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if not urls:
            return
        local_path = urls[0].toLocalFile()
        if local_path:
            self._load_image(local_path)

    def _init_clue_tables(self, size: int) -> None:
        self.row_clue_table.setRowCount(size)
        self.row_clue_table.setColumnCount(1)
        self.row_clue_table.setHorizontalHeaderLabels(["Row clues"])
        self.row_clue_table.verticalHeader().setVisible(False)
        self.row_clue_table.horizontalHeader().setStretchLastSection(True)

        self.col_clue_table.setRowCount(1)
        self.col_clue_table.setColumnCount(size)
        self.col_clue_table.setVerticalHeaderLabels(["Col clues"])
        self.col_clue_table.verticalHeader().setVisible(True)

        for r in range(size):
            if self.row_clue_table.item(r, 0) is None:
                self.row_clue_table.setItem(r, 0, QTableWidgetItem(""))

        for c in range(size):
            if self.col_clue_table.item(0, c) is None:
                self.col_clue_table.setItem(0, c, QTableWidgetItem(""))

    def _resize_board(self, size: int) -> None:
        self._init_clue_tables(size)
        self.grid_widget.resize_grid(size)

    def _apply_parsed_puzzle(self, puzzle: ParsedNonogramPuzzle) -> None:
        self._parsed_puzzle = puzzle
        self._last_solution = None
        self.overlay_preview.setText("叠加预览区")

        self.size_spin.setValue(puzzle.size)
        self._init_clue_tables(puzzle.size)
        self.grid_widget.resize_grid(puzzle.size)

        for r, clues in enumerate(puzzle.row_clues):
            self.row_clue_table.item(r, 0).setText(" ".join(str(x) for x in clues))

        for c, clues in enumerate(puzzle.col_clues):
            self.col_clue_table.item(0, c).setText(" ".join(str(x) for x in clues))

        self.grid_widget.set_grid(puzzle.initial_grid)

    def _import_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数织截图",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if path:
            self._load_image(path)

    def _load_image(self, path: str) -> None:
        if not Path(path).exists():
            QMessageBox.warning(self, "导入失败", f"文件不存在: {path}")
            return
        try:
            puzzle = load_puzzle_from_image(path)
            self._apply_parsed_puzzle(puzzle)
            self.drop_hint.setText(f"已导入: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "识别失败", str(exc))

    def _read_clues(self) -> tuple[List[List[int]], List[List[int]]]:
        size = self.size_spin.value()
        row_clues: List[List[int]] = []
        col_clues: List[List[int]] = []

        for r in range(size):
            item = self.row_clue_table.item(r, 0)
            row_clues.append(parse_clue_text(item.text() if item else ""))

        for c in range(size):
            item = self.col_clue_table.item(0, c)
            col_clues.append(parse_clue_text(item.text() if item else ""))

        return row_clues, col_clues

    def _toggle_controls(self, enabled: bool) -> None:
        self.solve_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
        self.size_spin.setEnabled(enabled)
        self.import_button.setEnabled(enabled)

    def _solve(self) -> None:
        try:
            row_clues, col_clues = self._read_clues()
            payload = SolvePayload(
                row_clues=row_clues,
                col_clues=col_clues,
                initial_grid=self.grid_widget.get_grid(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "输入错误", str(exc))
            return

        self._toggle_controls(False)
        self._thread = QThread(self)
        self._worker = SolveWorker(payload)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_solved)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_solved(self, result, error: str) -> None:
        self._toggle_controls(True)
        if error:
            QMessageBox.critical(self, "求解失败", error)
            return

        if result.no_solution:
            QMessageBox.information(self, "结果", "无解")
            return

        if result.grid is not None:
            self._last_solution = result.grid
            self.grid_widget.set_grid(result.grid)

        if result.has_multiple_solutions:
            QMessageBox.information(self, "结果", "存在多解，已展示其中一个解")
        else:
            QMessageBox.information(self, "结果", "求解完成")

    def _preview_overlay(self) -> None:
        if self._parsed_puzzle is None:
            QMessageBox.warning(self, "提示", "请先导入原图")
            return
        solution = self._last_solution or self.grid_widget.get_grid()
        try:
            composed = render_overlay_on_image(
                image_path=self._parsed_puzzle.image_path,
                grid_solution=solution,
                grid_bbox=self._parsed_puzzle.grid_bbox,
            )
            self._show_overlay_in_label(composed)
        except Exception as exc:
            QMessageBox.critical(self, "叠加失败", str(exc))

    def _show_overlay_in_label(self, bgr_image) -> None:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise RuntimeError("OpenCV is required for preview rendering.") from exc

        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        scaled = pix.scaled(
            self.overlay_preview.width(),
            self.overlay_preview.height(),
            aspectMode=Qt.KeepAspectRatio,
        )
        self.overlay_preview.setPixmap(scaled)

    def _export_overlay(self) -> None:
        if self._parsed_puzzle is None:
            QMessageBox.warning(self, "提示", "请先导入原图")
            return

        solution = self._last_solution or self.grid_widget.get_grid()
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出叠加图",
            "nonogram_overlay.png",
            "PNG Images (*.png)",
        )
        if not out_path:
            return
        if not out_path.lower().endswith(".png"):
            out_path += ".png"

        try:
            export_overlay_png(
                image_path=self._parsed_puzzle.image_path,
                grid_solution=solution,
                grid_bbox=self._parsed_puzzle.grid_bbox,
                output_path=out_path,
            )
            QMessageBox.information(self, "导出成功", f"已保存: {out_path}")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))

    def _show_about(self) -> None:
        QMessageBox.information(self, "关于", "mxf")

    def _reset(self) -> None:
        size = self.size_spin.value()
        self.grid_widget.clear_grid()
        self._last_solution = None
        self.overlay_preview.setText("叠加预览区")
        for r in range(size):
            self.row_clue_table.item(r, 0).setText("")
        for c in range(size):
            self.col_clue_table.item(0, c).setText("")


def main() -> None:
    app = QApplication([])
    window = MainWindow()
    window.resize(1200, 760)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
