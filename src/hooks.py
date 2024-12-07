from aqt import gui_hooks
from .editor_hook import ReibunEditorHook


def setup_hooks():
    editor_hook = ReibunEditorHook()
    gui_hooks.editor_will_show_context_menu.append(editor_hook.on_editor_context_menu)
