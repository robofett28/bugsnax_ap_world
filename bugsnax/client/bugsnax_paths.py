"""
bugsnax_paths.py

Locates the Bugsnax randomiser's save file. This was originally meant to find whatever
the active save file was, but I gave up and said fuck it, just do save file 2 lmao.

I may come back to this, but i'm lazy so no promises - Rob

"""

import ctypes
import os
import uuid
from ctypes import wintypes
from pathlib import Path

FOLDERID_SAVED_GAMES = uuid.UUID("{4C5C32FF-BB9D-43b0-B5B4-2D72E54EAAA4}")

RANDOMIZER_SAVE_FILENAME = "Bugsnax2.save"


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __init__(self, uuid_obj: uuid.UUID):
        super().__init__()
        self.Data1, self.Data2, self.Data3, d4a, d4b, rest = uuid_obj.fields
        self.Data4[0] = d4a
        self.Data4[1] = d4b
        for i in range(6):
            self.Data4[2 + i] = (rest >> (8 * (5 - i))) & 0xFF


def _get_known_folder_path(folder_id: uuid.UUID) -> str | None:
    try:
        guid = _GUID(folder_id)
        path_ptr = ctypes.c_wchar_p()
        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(guid), 0, 0, ctypes.byref(path_ptr)
        )
        if result != 0:
            return None
        path = path_ptr.value
        ctypes.windll.ole32.CoTaskMemFree(path_ptr)
        return path
    except Exception:
        return None


def find_save_path() -> Path:
    override = os.environ.get("BUGSNAX_SAVE_PATH")
    if override:
        p = Path(override)
        if p.is_file():
            return p
        print(f"BUGSNAX_SAVE_PATH is set to {p}, but that file doesn't exist. "
              f"Falling back to auto-detection.")

    saved_games = _get_known_folder_path(FOLDERID_SAVED_GAMES)
    if saved_games is None:
        saved_games = str(Path.home() / "Saved Games")

    bugsnax_dir = Path(saved_games) / "Bugsnax"
    if not bugsnax_dir.is_dir():
        raise FileNotFoundError(
            f"Couldn't find a Bugsnax save folder at {bugsnax_dir}. "
            "If your save is somewhere unusual, set the BUGSNAX_SAVE_PATH "
            "environment variable to the exact .save file path."
        )

    save_path = bugsnax_dir / RANDOMIZER_SAVE_FILENAME
    if not save_path.is_file():
        raise FileNotFoundError(
            f"The Bugsnax randomizer is locked to save slot 2, and "
            f"{save_path} doesn't exist yet.\n"
            "Start a brand NEW game in save slot 2 in Bugsnax first (the "
            "randomizer never touches slots 1, 3, 4), then reconnect the client.\n"
            "If your save is somewhere unusual, set the BUGSNAX_SAVE_PATH "
            "environment variable to the exact .save file path instead."
        )

    return save_path