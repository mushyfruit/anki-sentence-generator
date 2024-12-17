from typing import Optional, Dict, Any, List

import logging
from dataclasses import dataclass

from .reibun import ReibunGenerator
from .config import AnkiConfig
from .utils import (
    get_note_type,
    get_current_field_name,
    strip_html_tags,
    execute_in_background_thread,
)
from .constants import ConfigKeys, NoteConfig
from .ui.field_dialog import FieldMappingDialog

from aqt import (
    QAction,
    QMenu,
    editor,
    QLabel,
    QWidgetAction,
    QComboBox,
    QWidget,
    QHBoxLayout,
)

from PyQt6.QtCore import Qt

from aqt.utils import showWarning
from anki.notes import Note

log = logging.getLogger(__name__)


@dataclass
class ReibunContext:
    """Contains all necessary context for sentence generation operations."""

    note: Note
    note_type: str
    target_field_name: str
    target_field_value: str
    difficulty: int
    context_type: str


class ReibunEditorHook:
    """Handles Anki editor hook operations for Reibun generation."""

    def __init__(self):
        self.config = AnkiConfig()
        self.generator = ReibunGenerator(self.config)

        # Store current note state
        self._current_note_type = None
        self._current_field_name = None

    def on_editor_context_menu(
        self, editor_web_view: editor.EditorWebView, menu: QMenu
    ) -> None:
        """Called before the context menu is shown from the editor window.

        Handles adding the "Generate Smart Reibun" menu item to the context menu.
        """
        try:
            editor_instance = editor_web_view.editor
            if not editor_instance:
                log.error("No valid editor instance was found. Skipping menu creation.")
                return

            # Only show actions when a valid field is selected.
            current_field_index = editor_instance.currentField
            if current_field_index is None:
                return

            self._current_note_type = get_note_type(editor_instance.note)

            # Add the reibun generation actions to context menu.
            generate_field_item = QAction("📝 Generate Smart Reibun", menu)
            configure_fields_item = QAction("📝 Configure Smart Fields", menu)

            generate_field_item.triggered.connect(
                lambda: self.handle_field_generation(editor_instance)
            )
            configure_fields_item.triggered.connect(
                lambda: self.configure_field_mapping(editor_instance)
            )

            note_type = get_note_type(editor_instance.note)
            existing_config = self.config.get_note_type_config(note_type)

            context_options = getattr(self.config, ConfigKeys.CONTEXT_OPTIONS)
            difficulty_levels = getattr(self.config, ConfigKeys.DIFFICULTY_OPTIONS)

            default_context = existing_config.get(NoteConfig.CONTEXT, "")
            default_difficulty = existing_config.get(NoteConfig.DIFFICULTY, "")

            context_action = self._add_combobox(
                "Context:", context_options, default_context, NoteConfig.CONTEXT, menu
            )
            difficulty_action = self._add_combobox(
                "Difficulty:",
                difficulty_levels,
                default_difficulty,
                NoteConfig.DIFFICULTY,
                menu,
            )

            menu.addSeparator()
            menu.addAction(generate_field_item)
            menu.addAction(configure_fields_item)
            menu.addAction(context_action)
            menu.addAction(difficulty_action)
            menu.addSeparator()

        except Exception as e:
            log.exception("Failed to generate Smart Reibun menu: %s", e)
            showWarning(f"Failed to generate Smart Reibun menu: {str(e)}")

    def get_current_field(self):
        return self._current_field_name

    def _add_combobox(
        self, label: str, items: List[str], value: str, config_key: str, parent: QMenu
    ) -> QAction:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 2, 8, 2)
        label = QLabel(label)
        combo = QComboBox()
        combo.addItems(items)

        if value and value in items:
            combo.setCurrentText(value)

        layout.addWidget(label)
        layout.addWidget(combo)
        context_action = QWidgetAction(parent)
        context_action.setDefaultWidget(widget)

        combo.setItemData(0, config_key, Qt.ItemDataRole.UserRole)
        combo.currentTextChanged.connect(
            lambda text, cb=combo: self._on_combo_changed(text, cb)
        )

        return context_action

    def _on_combo_changed(self, current_text: str, combo: QComboBox) -> None:
        config_entry_key = combo.itemData(0, Qt.ItemDataRole.UserRole)
        if self._current_note_type is not None:
            existing_config = self.config.get_note_type_config(self._current_note_type)
            existing_config[config_entry_key] = current_text
            self.config.set_note_type_config(self._current_note_type, existing_config)

    def configure_field_mapping(
        self, editor: editor.Editor, target_field_name: Optional[str] = None
    ) -> bool:
        """Launches the `FieldMappingDialog` allowing the user to configure
        the target smart reibun fields.

        :param editor: Editor instance.
        :param target_field_name: Name of the current field.
        :returns: True if configuration was successful, False otherwise.
        """
        note = editor.note

        # Launch the Field Mapping Dialog to associate LLM outputs -> note fields.
        dialog = FieldMappingDialog(
            note,
            self.config,
            target_field_name=target_field_name,
            parent=editor.parentWindow,
        )

        if dialog.exec():
            note_type = get_note_type(note)

            # Retrieve the field mappings as set by the user.
            updated_note_type_config = dialog.get_note_config()

            # Store these mappings per note in the addon config.
            self.config.set_note_type_config(note_type, updated_note_type_config)

            log.debug("Field mapping configuration saved for {0}!".format(note_type))
            return True

        return False

    def handle_field_generation(self, editor: editor.Editor) -> None:
        """Generates values for the fields defined by the editor's note type via
        the configured LLM API configuration.

        :param editor: Editor instance.
        """
        note_type = get_note_type(editor.note)
        self._current_field_name = get_current_field_name(editor.note, editor)
        if self._current_field_name is None:
            log.error("Unable to retrieve target field name.")
            return

        # Try to get existing config or configure a new one.
        field_mappings = self._get_or_create_field_mappings(
            editor, note_type, self._current_field_name
        )
        if not field_mappings:
            return

        context = self._prepare_reibun_context(editor)
        if context is None:
            log.error("Unable to create valid reibun context.")
            return

        self._generate_field_content(context, editor, field_mappings)

    def _prepare_reibun_context(self, editor: editor.Editor) -> Optional[ReibunContext]:
        note = editor.note
        if not note:
            log.error("Invalid note was provided. Unable to generate field.")
            return None

        note_type = get_note_type(note)
        target_field_name = self.get_current_field()
        existing_config = self.config.get_note_type_config(note_type)
        difficulty = existing_config.get(NoteConfig.DIFFICULTY, None)
        context_type = existing_config.get(NoteConfig.CONTEXT, None)

        return ReibunContext(
            note=note,
            note_type=get_note_type(note),
            target_field_name=target_field_name,
            target_field_value=strip_html_tags(note[target_field_name]),
            difficulty=difficulty,
            context_type=context_type,
        )

    def _get_or_create_field_mappings(
        self, editor: editor.Editor, note_type: str, field_name: str
    ) -> Optional[Dict[str, Any]]:
        field_mappings = self.config.get_note_type_config(note_type)
        if not field_mappings and not self.configure_field_mapping(
            editor, target_field_name=field_name
        ):
            return None
        return self.config.get_note_type_config(note_type)

    def _validate_field_values(self, value: str) -> bool:
        # TODO further validation?
        if not value and not self.config.debug_mode:
            showWarning("Please enter the word to generate a reibun from!")
            return False
        return True

    def _generate_field_content(
        self,
        context: ReibunContext,
        editor: editor.Editor,
        field_mappings: dict,
    ) -> None:
        """Generates the field content via the selected LLM's API.

        :param context: ReibunContext instance containing relevant note field information.
        :param editor: Editor instance.
        :param field_mappings: Mapping of generated field names to note fields.
        """
        # Execute query to LLM in background thread via QueryOp.
        execute_in_background_thread(
            lambda: self.generator.update_note_field(
                context.note,
                context.target_field_value,
                field_mappings,
                difficulty=context.difficulty,
                generation_context=context.context_type,
            ),
            lambda _: self.post_field_update(context.note, editor),
        )

    def post_field_update(self, note: Note, editor: editor.Editor) -> None:
        """Callback to handle post-field update operations.

        :param note: Note instance.
        :param editor: Editor instance.
        """
        log.debug("Post-field update.")
        if note.id:
            note.load()
        editor.loadNote()
