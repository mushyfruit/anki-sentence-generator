from aqt import gui_hooks, mw
from .editor_hook import ReibunEditorHook
from .options import init_options

def setup_hooks():
    editor_hook = ReibunEditorHook()
    gui_hooks.editor_will_show_context_menu.append(editor_hook.on_editor_context_menu)
    gui_hooks.main_window_did_init.append(on_main_window)

def on_main_window():
    """Executed after the main window is fully initialized"""

    # Override the default config action for the addon.
    init_options()
