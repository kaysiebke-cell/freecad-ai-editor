# -*- coding: utf-8 -*-
"""
editor_suche.py
───────────────
Schnellsuche-Leiste und Code-Block-Suche für den MakroEditor.
"""

import re

from qt_compat import QtWidgets, QtGui

_RE_WORD_CHARS = re.compile(r"\w+")


class SucheLogik:
    """Kapselt Schnellsuche und Block-Suche im Editor."""

    __slots__ = ("_e",)

    def __init__(self, editor):
        self._e = editor

    # ── Schnellsuche (Ctrl+F Leiste) ──────────────────────────────────────

    def toggle_suche(self):
        e = self._e
        vis = not e._suche_widget.isVisible()
        e._suche_widget.setVisible(vis)
        if vis:
            sel = e._normalize_newlines(
                e._editor.textCursor().selectedText()).strip()
            if sel and "\n" not in sel:
                e._suche_feld.setText(sel)
            e._suche_feld.selectAll()
            e._suche_feld.setFocus()

    def suche_weiter(self):
        e = self._e
        if not e._editor.find(e._suche_feld.text()):
            c = e._editor.textCursor()
            c.movePosition(QtGui.QTextCursor.Start)
            e._editor.setTextCursor(c)
            if not e._editor.find(e._suche_feld.text()):
                e._set_status("⚠  Begriff nicht gefunden")

    def ersetzen_text(self):
        e = self._e
        c = e._editor.textCursor()
        if (c.hasSelection()
                and e._normalize_newlines(c.selectedText()) == e._suche_feld.text()):
            c.insertText(e._ersatz_feld.text())
            self.suche_weiter()

    def alles_ersetzen(self):
        e = self._e
        alt, neu = e._suche_feld.text(), e._ersatz_feld.text()
        if not alt:
            return
        text = e._editor.toPlainText()
        n = text.count(alt)
        if n:
            e._editor.setPlainText(text.replace(alt, neu))
            e._set_status(f"✔  {n}× ersetzt")
        else:
            e._set_status("⚠  Begriff nicht gefunden")

    # ── Block-Suche (Suchfeld → Editor) ───────────────────────────────────

    def copy_from_editor(self):
        e = self._e
        c = e._editor.textCursor()
        if c.hasSelection():
            text = e._normalize_newlines(c.selectedText())
            e.find_area.setPlainText(text)
            e._set_status(f"📥 {len(text.splitlines())} Zeile(n) ins Suchfeld geladen")
        else:
            text = e._editor.toPlainText()
            e.find_area.setPlainText(text)
            e._set_status("📥 Gesamter Dateiinhalt ins Suchfeld geladen")
        e.find_area.setFocus()

    def find_in_editor(self) -> bool:
        e = self._e
        needle_lines = [l.strip()
                        for l in e.find_area.toPlainText().splitlines() if l.strip()]
        if not needle_lines:
            return False
        full_text = e._normalize_newlines(e._editor.toPlainText())
        if len(needle_lines) == 1:
            needle = needle_lines[0]
            pos = full_text.lower().find(needle.lower())
            if pos >= 0:
                cur = e._editor.textCursor()
                cur.setPosition(pos)
                cur.setPosition(pos + len(needle), QtGui.QTextCursor.KeepAnchor)
                e._editor.setTextCursor(cur)
                e._editor.setFocus()
                return True
            return False

        def _norm(line):
            return "".join(_RE_WORD_CHARS.findall(line))

        norm_needle = [_norm(l) for l in needle_lines]
        haystack    = full_text.splitlines()
        norm_h      = [_norm(l) for l in haystack]
        count       = len(norm_needle)
        for idx in range(len(norm_h) - count + 1):
            if norm_h[idx:idx + count] == norm_needle:
                start = sum(len(haystack[i]) + 1 for i in range(idx))
                end   = sum(len(haystack[i]) + 1 for i in range(idx + count)) - 1
                cursor = e._editor.textCursor()
                cursor.setPosition(start)
                cursor.setPosition(min(end, len(full_text)), QtGui.QTextCursor.KeepAnchor)
                e._editor.setTextCursor(cursor)
                e._editor.setFocus()
                return True
        return False

    def find_and_highlight(self):
        e = self._e
        if self.find_in_editor():
            e._set_status("🔍 Gefunden und markiert → ✅ Ersetzen & speichern")
            e._btn_ersetzen.setEnabled(True)
        else:
            suchtext  = e.find_area.toPlainText().strip()
            if not suchtext:
                e._set_status("❌ Suchfeld ist leer")
                return
            dateiname = e._pfad and __import__("os").path.basename(e._pfad) or "diese Datei"
            antwort = QtWidgets.QMessageBox.question(
                e, "Nicht gefunden",
                f'"{suchtext[:60]}{"…" if len(suchtext) > 60 else ""}"\n\n'
                f'wurde in  {dateiname}  nicht gefunden.\n\n'
                f'Soll in allen anderen Makro-Dateien gesucht werden?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes,
            )
            if antwort == QtWidgets.QMessageBox.Yes:
                e._set_status("🔍 Suche in allen Makros …")
                e.such_in_dateien.emit(suchtext)
            else:
                e._set_status("❌ Nicht gefunden")
