import logging
from logging.handlers import RotatingFileHandler
from PyQt5.QtCore import QStandardPaths
from pathlib import Path

log_root = Path(QStandardPaths.writableLocation(
    QStandardPaths.AppDataLocation
))
log_dir = log_root / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

handler = RotatingFileHandler(
    log_dir / "app.log",
    maxBytes=5_000_000,
    backupCount=10,
    encoding="utf-8"
)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler],
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

import sys
from PyQt5.QtWidgets import QApplication

from graph.node_controller import NodeEditorWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NodeEditorWindow()
    window.show()

    sys.exit(app.exec())
