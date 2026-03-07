"""AEP Viewer — PySide6 GUI for viewing parsed AEP project files."""

from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .theme import COLOR_BG, COLOR_BG_ALT, COLOR_PANEL, COLOR_TEXT, COLOR_ACCENT, DARK_STYLESHEET
from .app import MainWindow


def main():
    from pathlib import Path

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.Window, COLOR_BG)
    palette.setColor(QPalette.WindowText, COLOR_TEXT)
    palette.setColor(QPalette.Base, COLOR_BG)
    palette.setColor(QPalette.AlternateBase, COLOR_BG_ALT)
    palette.setColor(QPalette.Text, COLOR_TEXT)
    palette.setColor(QPalette.Button, COLOR_PANEL)
    palette.setColor(QPalette.ButtonText, COLOR_TEXT)
    palette.setColor(QPalette.Highlight, COLOR_ACCENT)
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = MainWindow()

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.exists():
            if path.suffix.lower() == ".json":
                window._load_json(path)
            else:
                window._load_file(path)

    window.show()
    sys.exit(app.exec())


def main_diff():
    from pathlib import Path
    from .diff_app import DiffMainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.Window, COLOR_BG)
    palette.setColor(QPalette.WindowText, COLOR_TEXT)
    palette.setColor(QPalette.Base, COLOR_BG)
    palette.setColor(QPalette.AlternateBase, COLOR_BG_ALT)
    palette.setColor(QPalette.Text, COLOR_TEXT)
    palette.setColor(QPalette.Button, COLOR_PANEL)
    palette.setColor(QPalette.ButtonText, COLOR_TEXT)
    palette.setColor(QPalette.Highlight, COLOR_ACCENT)
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = DiffMainWindow()

    # CLI: optional file_a and file_b arguments
    path_a = None
    path_b = None
    args = sys.argv[1:]
    if len(args) >= 1:
        p = Path(args[0])
        if p.exists():
            path_a = str(p)
    if len(args) >= 2:
        p = Path(args[1])
        if p.exists():
            path_b = str(p)

    if path_a or path_b:
        window.load_paths(path_a, path_b)

    window.show()
    sys.exit(app.exec())
