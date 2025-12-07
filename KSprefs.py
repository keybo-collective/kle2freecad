# -*- coding: utf-8 -*-

import FreeCAD
import FreeCADGui
from PySide2 import QtGui
from KSutils import prefFileName

_PREF_PATH = "User parameter:BaseApp/Preferences/Mod/kle2sketch"
_PREF_KEY = "LayoutJSON"


def _pref_group():
    return FreeCAD.ParamGet(_PREF_PATH)


def get_saved_layout(default=""):
    """Return persisted layout text or a fallback."""
    saved = _pref_group().GetString(_PREF_KEY)
    return saved if saved else default


def set_saved_layout(text: str) -> None:
    """Persist layout text."""
    _pref_group().SetString(_PREF_KEY, text or "")


class KSprefsPage:
    """Preference page wrapper used by FreeCAD to load/save settings."""

    def __init__(self):
        self.form = FreeCADGui.PySideUic.loadUi(prefFileName)
        self._text_edit().setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))

    def _text_edit(self):
        return getattr(self.form, "jsonTextEdit", self.form)

    def saveSettings(self):
        _pref_group().SetString(_PREF_KEY, self._text_edit().toPlainText())

    def loadSettings(self):
        self._text_edit().setPlainText(get_saved_layout())
