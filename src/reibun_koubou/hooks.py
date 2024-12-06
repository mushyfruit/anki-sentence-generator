from aqt import gui_hooks
from .handler import ReibunHookHandler


def setup_hooks():
    handler = ReibunHookHandler()
    gui_hooks.editor_will_show_context_menu.append(handler.on_editor_context_menu)
