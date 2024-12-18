from aqt import mw
from aqt.qt import QAction

def init_options():
    # Override the default config action for the addon.
    mw.addonManager.setConfigAction(__name__, on_reibun_options)

    options_action = QAction("&Reibun Options...", mw)
    options_action.triggered.connect(lambda _: on_reibun_options())
    mw.form.menuTools.addAction(options_action)


def on_reibun_options():
    from .ui.options_dialog import OptionsDialog
    dialog = OptionsDialog()
    dialog.exec()
