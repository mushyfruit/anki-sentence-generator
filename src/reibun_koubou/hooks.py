from typing import Callable, List, Sequence
from aqt import QAction, QMenu, browser, editor, gui_hooks, mw


def setup_hooks():
    gui_hooks.editor_did_init_buttons.append(add_editor_top_button)


def add_editor_top_button(buttons: List[str], e: editor.Editor):
    button = e.addButton(
        cmd="Generate Reibun",
        label="✨",
        func=generate_reibun,
        icon=None,
        tip="Ctrl+Shift+G: Generate Smart Fields",
        id="generate_smart_fields",
        keys="Ctrl+Shift+G",
    )
    buttons.append(button)

def generate_reibun(e: editor.Editor):
    card = e.card
    note = e.note

    if card is None:
        card = note.ephemeral_card()

    print(card)
    print(note)


# dev: https://forums.ankiweb.net/t/pycharm-setup-for-add-on-debugging/17733
# ref: https://github.com/piazzatron/anki-smart-notes/blob/a80b1b16aeb0fd1321186b207e3167cad3c3f4c7/src/hooks.py#L277