# -*- coding: utf-8 -*-
"""Rechtschreib-Backends für den FreeCAD-Helfer (enchant → pyspellchecker → Fallback)."""

import re

from core.qt_compat import QtGui


class _SpellBackend:
    def pruefen(self, wort: str) -> bool: return True
    def vorschlaege(self, wort: str) -> list[str]: return []


class _EnchantBackend(_SpellBackend):
    def __init__(self):
        import enchant as _e
        self._d = _e.Dict("de_DE")

    def pruefen(self, wort): return self._d.check(wort)
    def vorschlaege(self, wort): return self._d.suggest(wort)[:8]


class _SpellcheckerBackend(_SpellBackend):
    def __init__(self):
        from spellchecker import SpellChecker
        self._s = SpellChecker(language="de")

    def pruefen(self, wort): return not self._s.unknown([wort])
    def vorschlaege(self, wort):
        c = self._s.candidates(wort)
        return sorted(c)[:8] if c else []


def _lade_backend() -> tuple[_SpellBackend, str]:
    for Klasse, name in [(_EnchantBackend, "enchant"),
                         (_SpellcheckerBackend, "pyspellchecker")]:
        try:
            return Klasse(), name
        except Exception:
            continue
    return _SpellBackend(), ""


BACKEND, NAME = _lade_backend()
HAT_RECHTSCHREIBUNG = bool(NAME)


class RechtschreibHighlighter(QtGui.QSyntaxHighlighter):
    """Unterstreicht falsch geschriebene Wörter rot während des Tippens."""

    _WORT_RE = re.compile(r"\b[A-Za-zÄäÖöÜüß]{2,}\b")

    def __init__(self, dokument):
        super().__init__(dokument)
        self._format = QtGui.QTextCharFormat()
        self._format.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
        self._format.setUnderlineColor(QtGui.QColor("red"))

    def highlightBlock(self, text):
        if not HAT_RECHTSCHREIBUNG:
            return
        for m in self._WORT_RE.finditer(text):
            wort = m.group()
            if not BACKEND.pruefen(wort):
                self.setFormat(m.start(), len(wort), self._format)
