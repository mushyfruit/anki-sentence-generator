from typing import Union
from aqt import QAction, QMenu, editor, gui_hooks

from anki.notes import Note

from .reibun import ReibunGenerator
from .handler import ReibunHookHandler


def setup_hooks():
    # To implement later.
    # gui_hooks.editor_did_init_buttons.append(add_editor_top_button)
    handler = ReibunHookHandler()
    gui_hooks.editor_will_show_context_menu.append(handler.on_editor_context_menu)


def get_note_type(note: Note) -> str:
    note_info = note.note_type()
    if not note_info:
        raise RuntimeError("Note type not found")
    return note_info["name"]


def get_fields_from_current_note(note) -> list[tuple[str, str]]:
    return note.items()


def get_field_from_index(note: Note, index: int) -> Union[str, None]:
    """Gets the field name from the index of a note."""
    fields = get_fields_from_current_note(note)
    if index < 0 or index >= len(fields):
        return None
    return fields[index]


def on_editor_context_menu(editor_web_view: editor.EditorWebView, menu: QMenu):
    generate_field_item = QAction("📝 Generate Smart Reibun", menu)

    editor = editor_web_view.editor
    card = editor.card
    note = editor.note
    if note is None:
        return

    current_field_index = editor.currentField
    if current_field_index is None:
        return

    generate_field_item.triggered.connect(
        lambda: generate_reibun(card, note, current_field_index)
    )

    menu.addAction(generate_field_item)
    menu.addSeparator()


def generate_reibun(card, note, target_field_index):
    if card is None:
        card = note.ephemeral_card()

    generator = ReibunGenerator()
    generator.generate_reibun(
        reibun_source_phrase,
        context_for_reibun,
        on_success_callback,
        target_field=target_field,
    )
