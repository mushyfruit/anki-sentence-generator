from typing import Optional, Dict, Any

import logging
from dataclasses import dataclass

from .reibun import ReibunGenerator
from .config import AnkiConfig
from .utils import get_note_type, get_current_field_name, strip_html_tags
from .ui.field_dialog import FieldMappingDialog

from aqt import QAction, QMenu, editor
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


class ReibunEditorHook:
    """Handles Anki editor hook operations for Reibun generation."""

    def __init__(self):
        self.config = AnkiConfig()
        self.generator = ReibunGenerator()

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

            # Add the reibun generation actions to context menu.
            generate_field_item = QAction("📝 Generate Smart Reibun", menu)
            configure_fields_item = QAction("📝 Configure Smart Fields", menu)

            generate_field_item.triggered.connect(
                lambda: self.handle_field_generation(editor_instance)
            )
            configure_fields_item.triggered.connect(
                lambda: self.configure_field_mapping(editor_instance)
            )

            menu.addAction(generate_field_item)
            menu.addAction(configure_fields_item)
            menu.addSeparator()

        except Exception as e:
            log.exception("Failed to generate Smart Reibun menu: %s", e)
            showWarning(f"Failed to generate Smart Reibun menu: {str(e)}")

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
        note_type = get_note_type(note)

        # Retrieve any stored configs for the provided note type.
        note_type_config = self.config.get_note_type_config(note_type)

        # Launch the Field Mapping Dialog to associate LLM outputs -> note fields.
        dialog = FieldMappingDialog(
            note,
            target_field_name=target_field_name,
            existing_config=note_type_config,
            parent=editor.parentWindow,
        )

        if dialog.exec():
            # Retrieve the field mappings as set by the user.
            updated_field_mappings = dialog.get_field_mappings()

            # Store these mappings per note in the addon config.
            self.config.set_note_type_config(note_type, updated_field_mappings)

            log.debug("Field mapping configuration saved for {0}!".format(note_type))
            return True

        return False

    def handle_field_generation(self, editor: editor.Editor) -> None:
        """Generates values for the fields defined by the editor's note type via
        the configured LLM API configuration.

        :param editor: Editor instance.
        """
        context = self._prepare_reibun_context(editor)
        if context is None:
            return

        if not self._validate_field_values(context.target_field_value):
            return

        # Try to get existing config or configure a new one.
        field_mappings = self._get_or_create_field_mappings(
            editor, context.note_type, context.target_field_name
        )
        if not field_mappings:
            return

        self._generate_field_content(context, editor, field_mappings)

    def _prepare_reibun_context(self, editor: editor.Editor) -> Optional[ReibunContext]:
        note = editor.note
        if not note:
            log.error("Invalid note was provided. Unable to generate field.")
            return None

        target_field_name = get_current_field_name(note, editor)
        if target_field_name is None:
            log.debug("No field name found")
            return

        return ReibunContext(
            note=note,
            note_type=get_note_type(note),
            target_field_name=target_field_name,
            target_field_value=strip_html_tags(note[target_field_name]),
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
        generation_context = self._get_generation_context(
            context.note, context.target_field_name
        )
        self.generator.update_note_field(
            context.note,
            context.target_field_value,
            field_mappings,
            context=generation_context,
            on_success_callback=lambda x: self.post_field_update(x, editor),
        )

    def post_field_update(self, note: Note, editor: editor.Editor) -> None:
        """Callback to handle post-field update operations.

        :param note: Note instance.
        :param editor: Editor instance.
        """
        if note.id:
            note.load()
        editor.loadNote()

    def _get_generation_context(self, note, exclude_field: str) -> dict:
        return {
            name: value
            for name, value in note.items()
            if value and name != exclude_field
        }
