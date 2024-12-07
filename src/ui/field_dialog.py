from aqt.qt import QDialog, QVBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, Qt

from anki.notes import Note
from ..utils import get_field_names_from_note, get_note_type


class FieldMappingDialog(QDialog):
    def __init__(
        self, note: Note, target_field_name=None, existing_config=None, parent=None
    ):
        super().__init__(parent)
        self._note = note
        self._fields = get_field_names_from_note(note)
        self._existing_config = existing_config
        self._target_field_name = target_field_name
        self._combos = {}
        self._field_mappings = {}

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumWidth(300)
        self.setWindowTitle(f"Configure Field Mapping - {get_note_type(self._note)}")

        layout = QVBoxLayout()
        grid = QGridLayout()

        required_fields = ["Sentence", "Reading", "Translation", "Notes"]
        for i, field_type in enumerate(required_fields):
            label = QLabel(f"{field_type} Field:")
            combo = QComboBox()
            combo.addItems(["None"] + self._fields)
            combo.setObjectName(field_type.lower())
            combo.currentTextChanged.connect(
                lambda text, ft=field_type: self.on_selection_changed(ft, text)
            )
            self._combos[field_type.lower()] = combo
            grid.addWidget(label, i, 0)
            grid.addWidget(combo, i, 1)

        if self._existing_config:
            for response_field, target_field in self._existing_config.items():
                print(response_field, target_field)
                self.set_combobox_item(response_field, target_field)

        if self._target_field_name:
            self.set_combobox_item("Sentence", self._target_field_name)

        layout.addLayout(grid)

        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_mapping)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def set_combobox_item(self, combo_name, item_name):
        combo_box = self._combos.get(combo_name.lower())
        if combo_box is None:
            return

        index = combo_box.findText(item_name, Qt.MatchFlag.MatchExactly)

        if index >= 0:
            combo_box.setCurrentIndex(index)

    def on_selection_changed(self, current_field: str, selected_value: str):
        if selected_value == "None":
            return

        for field_type, combo in self._combos.items():
            if (
                field_type.lower() != current_field.lower()
                and combo.currentText() == selected_value
            ):
                combo.setCurrentText("None")

    def save_mapping(self):
        for field_type, combo in self._combos.items():
            selected = combo.currentText()
            if selected != "None":
                self._field_mappings[field_type.lower()] = selected
        self.accept()

    def get_field_mappings(self):
        return self._field_mappings
