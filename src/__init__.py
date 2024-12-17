import os

script_path = os.path.realpath(__file__)


def init():
    # https://stackoverflow.com/questions/1158108/python-importing-a-file-that-is-a-symbolic-link
    # Handle double-imports
    from aqt import mw

    addon_folder = mw.pm.addonFolder()
    if addon_folder not in __file__:
        return

    from . import main

    print("Initializing Reibun Koubou...")
    main.init()


init()
