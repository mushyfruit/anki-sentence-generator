import re

from .reibun import ReibunGenerator
from .config import Config

from aqt import QAction, QMenu, editor, mw
from anki.notes import Note


class ReibunHookHandler:
    def __init__(self):
        self.config = Config()
        self.generator = ReibunGenerator()

    def on_editor_context_menu(
        self, editor_web_view: editor.EditorWebView, menu: QMenu
    ):
        editor = editor_web_view.editor
        if not editor or not editor.note:
            return

        generate_field_item = QAction("📝 Generate Smart Reibun", menu)
        generate_field_item.triggered.connect(
            lambda: self.handle_current_field_generation(editor)
        )
        menu.addAction(generate_field_item)
        menu.addSeparator()

    def handle_current_field_generation(self, editor: editor.Editor):
        note = editor.note
        field_index = editor.currentField

        if not note or field_index is None:
            return

        model = mw.col.models.by_name(get_note_type(note))
        if not model:
            return []

        fields = [
            field["name"] for field in sorted(model["flds"], key=lambda x: x["ord"])
        ]
        target_field_name = fields[field_index]
        target_field_value = self.clean_target_field_value(note[target_field_name])
        if not target_field_value and not self.config.debug_mode:
            return

        context = self.get_context(note, target_field_name)
        self.generator.update_note_field(
            note,
            target_field_value,
            target_field_name,
            context=context,
            on_success_callback=lambda x: self.post_field_update(x, editor),
        )

    def clean_target_field_value(self, target_field_value):
        clean = re.compile("<.*?>")
        return re.sub(clean, "", target_field_value)

    def post_field_update(self, note: Note, editor: editor.Editor):
        if note.id:
            note.load()

        editor.loadNote()

    def get_context(self, note, exclude_field: str) -> dict:
        return {
            name: value
            for name, value in note.items()
            if value and name != exclude_field
        }


def get_note_type(note: Note) -> str:
    note_info = note.note_type()
    if not note_info:
        raise RuntimeError("Note type not found")
    return note_info["name"]
