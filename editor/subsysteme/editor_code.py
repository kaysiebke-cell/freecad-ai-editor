# -*- coding: utf-8 -*-
"""
editor_code.py
──────────────
Code-Formatierung, Einrückung, Selektion-Cache und Syntax-Bereinigung.
"""

try:
    import autopep8
    _HAS_AUTOPEP8 = True
except ImportError:
    _HAS_AUTOPEP8 = False

from core.qt_compat import QtGui


class CodeLogik:
    """Kapselt Code-Transformation und Selektion-Verwaltung."""

    __slots__ = ("_e",)

    def __init__(self, editor):
        self._e = editor
        editor._letzter_editor_cursor = None

    # ── Formatierung ──────────────────────────────────────────────────────

    def formatieren(self):
        e = self._e
        text = e._editor.toPlainText()
        if _HAS_AUTOPEP8:
            fixed = autopep8.fix_code(text, options={"aggressive": 0, "ignore": ["E1", "W1"]})
            fixed = self.smart_reindent(fixed)
            e._set_status("✨ Formatiert (autopep8 + Smart-Einrückung)")
        else:
            fixed = self.smart_reindent(text)
            e._set_status("🪄 Smart-Einrückung angewendet")
        e._editor.setPlainText(fixed)

    @staticmethod
    def smart_reindent(text: str) -> str:
        _AUSRUECK_KW   = frozenset({"pass", "return", "break", "continue", "raise", "yield"})
        _BLOCK_FORT_KW = frozenset({"except", "else", "elif", "finally", "case"})
        _INDENT = "    "
        out, lvl, naechste_reduzieren = [], 0, False
        for zeile in text.splitlines():
            s = zeile.strip()
            if not s:
                out.append("")
                naechste_reduzieren = False
                continue
            if naechste_reduzieren:
                lvl = max(0, lvl - 1)
                naechste_reduzieren = False
            erstes = s.split()[0].rstrip(":(")
            einrueck_lvl = max(0, lvl - 1) if erstes in _BLOCK_FORT_KW else lvl
            out.append(_INDENT * einrueck_lvl + s)
            lvl = einrueck_lvl + 1 if s.rstrip().endswith(":") else einrueck_lvl
            if erstes in _AUSRUECK_KW:
                naechste_reduzieren = True
        return "\n".join(out)

    @staticmethod
    def reindent_block(code: str, target_indent: str) -> str:
        code      = code.replace("\t", "    ")
        zeilen    = code.splitlines()
        non_empty = [l for l in zeilen if l.strip()]
        base      = min((len(l) - len(l.lstrip()) for l in non_empty), default=0)
        return "\n".join(
            "" if not l.strip() else target_indent + l[base:] for l in zeilen)

    @staticmethod
    def erste_einrueckung(text: str) -> str:
        for line in text.splitlines():
            if line.strip():
                return line[:len(line) - len(line.lstrip())]
        return ""

    def syntax_bereinigen(self):
        import ast as _ast
        e = self._e
        text = e._ki_area.toPlainText().strip()
        if not text or text.startswith("# ⏳"):
            e._set_status("⚠  KI-Antwort ist leer")
            return
        bereinigt = e._extrahiere_code_aus_nl_antwort(text)
        bereinigt = e._schneide_erklaerung_ab(bereinigt)
        if not bereinigt.strip():
            e._set_status("⚠  Bereinigung: kein Python-Code erkannt")
            return
        try:
            _ast.parse(bereinigt)
            e._ki_area.setPlainText(bereinigt)
            e._set_status("✅ Bereinigt – Syntax korrekt")
        except SyntaxError as ex:
            e._ki_area.setPlainText(bereinigt)
            e._set_status(f"⚠ Bereinigt – noch Syntax-Fehler Zeile {ex.lineno}: {ex.msg}")

    # ── Selektion-Cache ────────────────────────────────────────────────────

    def on_editor_selection_changed(self):
        e = self._e
        c = e._editor.textCursor()
        if c.hasSelection():
            e._letzter_editor_cursor = QtGui.QTextCursor(c)

    def stelle_selektion_wieder_her(self) -> bool:
        e = self._e
        c = e._editor.textCursor()
        if c.hasSelection():
            return True
        if (getattr(e, "_letzter_editor_cursor", None)
                and e._letzter_editor_cursor.hasSelection()):
            e._editor.setTextCursor(e._letzter_editor_cursor)
            return True
        return False
