import logging

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTabWidget
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QGridLayout,
    QLabel,
    QComboBox,
    QPushButton,
    Qt,
    QHBoxLayout,
    QFrame,
)

log = logging.getLogger(__name__)


class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._setup_ui()

        # Should show the following tabs
        # basic options
        # choose the model.
        # qtab widget + qgroupbox
        #
        # prompt adjustment
        # prompt, heat, etc.
        # per-deck field adjustments

    def _setup_ui(self):
        self.setWindowTitle("Reibun Koubou Settings")

        layout = QVBoxLayout(self)
        header_label = QLabel(self)
        header_label.setText("Reibun Koubou")
        header_label.setFont(QFont("Arial", 14))

        layout.addWidget(header_label)