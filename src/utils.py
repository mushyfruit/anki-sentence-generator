from typing import Optional

import re

from aqt import mw, editor
from anki.notes import Note


def get_note_type(note: Note) -> str:
    note_info = note.note_type()
    if not note_info:
        raise RuntimeError("Note type not found")
    return note_info["name"]


def get_field_names_from_note(note: Note) -> list:
    note_type = get_note_type(note)
    if not note_type:
        return []

    model = mw.col.models.by_name(note_type)
    if not model:
        return []

    return [field["name"] for field in sorted(model["flds"], key=lambda x: x["ord"])]


def get_current_field_name(note: Note, editor: editor.Editor) -> Optional[str]:
    field_index: Optional[int] = editor.currentField
    if field_index is None:
        return None

    fields = get_field_names_from_note(note)
    if fields and field_index < len(fields):
        return fields[field_index]

    return None


def strip_html_tags(target_field_value):
    clean = re.compile("<.*?>")
    return re.sub(clean, "", target_field_value)
