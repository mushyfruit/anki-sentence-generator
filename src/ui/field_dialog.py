from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QPushButton,
    Qt,
    QHBoxLayout,
    QFrame,
)

from anki.notes import Note

from ..config import AnkiConfig
from ..constants import NoteConfig
from ..utils import get_field_names_from_note, get_note_type


class FieldMappingDialog(QDialog):
    def __init__(
        self, note: Note, config: AnkiConfig, target_field_name=None, parent=None
    ):
        super().__init__(parent)
        self._note = note
        self._config = config

        self._fields = get_field_names_from_note(note)
        self._target_field_name = target_field_name
        self._combos = {}
        self._field_mappings = {}

        self.setup_ui()

        self._populate_combobox_options()

        # Restore existing config settings
        self._populate_existing_config()

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

        layout.addLayout(grid)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        context_label = QLabel("Context:")
        self._context_combo = QComboBox(self)

        difficulty_label = QLabel("Difficulty:")
        self._difficulty_combo = QComboBox(self)

        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        settings_layout.addWidget(context_label)
        settings_layout.addWidget(self._context_combo)
        settings_layout.addSpacing(10)
        settings_layout.addWidget(difficulty_label)
        settings_layout.addWidget(self._difficulty_combo)
        settings_layout.addStretch()

        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_mapping)
        layout.addLayout(settings_layout)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def _populate_combobox_options(self):
        difficulties = self._config.difficulty_options
        contexts = self._config.context_options

        if difficulties:
            self._difficulty_combo.addItems(difficulties)

        if contexts:
            self._context_combo.addItems(contexts)

    def _populate_existing_config(self) -> None:
        note_type = get_note_type(self._note)
        existing_config = self._config.get_note_type_config(note_type)
        if existing_config is None:
            return

        field_mappings = existing_config.get(NoteConfig.FIELDS, {})
        for response_field, target_field in field_mappings.items():
            self.set_combobox_item(response_field, target_field)

        if self._target_field_name:
            self.set_combobox_item("Sentence", self._target_field_name)

        difficulty = existing_config.get(NoteConfig.DIFFICULTY, None)
        if difficulty:
            self._set_combobox_value(self._difficulty_combo, difficulty)

        context = existing_config.get(NoteConfig.CONTEXT, None)
        if context:
            self._set_combobox_value(self._context_combo, context)

    def set_combobox_item(self, combo_name, item_name):
        combo_box = self._combos.get(combo_name.lower())
        if combo_box is None:
            return

        self._set_combobox_value(combo_box, item_name)

    def _set_combobox_value(self, combo_box, value):
        index = combo_box.findText(value, Qt.MatchFlag.MatchExactly)
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

    def get_note_config(self):
        return {
            NoteConfig.FIELDS: self._field_mappings,
            NoteConfig.DIFFICULTY: self._get_difficulty(),
            NoteConfig.CONTEXT: self._get_context(),
        }

    def _get_context(self):
        return self._context_combo.currentText()

    def _get_difficulty(self):
        return self._difficulty_combo.currentText()

    def get_field_mappings(self):
        return self._field_mappings
