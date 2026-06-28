# -*- coding: utf-8 -*-
"""
editor_plan.py
──────────────
Plan-Modus und KI-Code-Einfüge-Operationen für den MakroEditor.
"""

import ast as _ast

from core.qt_compat import QtWidgets, QtGui


def _sandbox_fehler(e, code: str, fehler: str,
                    status: str = "❌ Syntaxfehler — Code in Sandbox geladen, Editor unverändert") -> None:
    """Leitet Code + Fehler in die Sandbox und öffnet den Fehler-Dock."""
    panel = getattr(e, "_fehler_inhalt", None)
    if panel is not None:
        panel._sandbox_ergebnis(False, fehler, code)
        panel._stack.setCurrentIndex(1)
        panel._ist_sandbox = True
        panel._btn_toggle.setText("🔍 Fehler-Übersetzer")
    if hasattr(e, "_dock_fehler"):
        e._dock_fehler.show()
        e._dock_fehler.raise_()
    e._set_status(status)


class PlanLogik:
    """Plan-Modus: Code prüfen bevor er den Editor-Inhalt ersetzt."""

    __slots__ = ("_e",)

    def __init__(self, editor):
        self._e = editor

    def plan_modus_umschalten(self, aktiv: bool):
        e = self._e
        e._plan_modus_aktiv = aktiv
        if aktiv:
            e._btn_plan.setText("🔍  Plan  ✓")
            e._set_status("🔍 Plan-Modus aktiv — Code wird vor dem Ersetzen angezeigt")
        else:
            e._btn_plan.setText("🔍  Plan")
            e._set_status("Plan-Modus deaktiviert")

    def plan_dialog_zeigen(self, neu_code: str) -> bool:
        e = self._e
        dlg = QtWidgets.QDialog(e)
        dlg.setWindowTitle("🔍 Plan-Modus — Code prüfen")
        dlg.resize(700, 450)
        lay = QtWidgets.QVBoxLayout(dlg)
        lay.setSpacing(8)
        info = QtWidgets.QLabel(
            "Die KI möchte folgenden Code einfügen. Bitte prüfen und bestätigen:")
        info.setWordWrap(True)
        lay.addWidget(info)
        vorschau = QtWidgets.QPlainTextEdit()
        vorschau.setPlainText(neu_code)
        vorschau.setReadOnly(True)
        vorschau.setFont(QtGui.QFont("Courier New", 10))
        lay.addWidget(vorschau, 1)
        btns   = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("✅  Ausführen")
        btn_ab = QtWidgets.QPushButton("❌  Abbrechen")
        btn_ok.setFixedHeight(30)
        btn_ab.setFixedHeight(30)
        btn_ok.clicked.connect(dlg.accept)
        btn_ab.clicked.connect(dlg.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_ab)
        lay.addLayout(btns)
        return dlg.exec_() == QtWidgets.QDialog.Accepted

    def ersetzen_und_speichern(self):
        e = self._e
        neu_code = e._ki_area.toPlainText().strip()
        if not neu_code:
            e._set_status("⚠  KI-Antwort ist leer")
            return
        try:
            _ast.parse(neu_code)
        except SyntaxError as _se:
            _sandbox_fehler(e, neu_code, f"SyntaxError Zeile {_se.lineno}: {_se.msg}")
            return
        _vorschau = getattr(e, "_vorschau", None)
        if _vorschau is not None:
            _rt = _vorschau._vorschau_exec(neu_code, nur_pruefen=True)
            if _rt:
                _sandbox_fehler(e, neu_code, _rt,
                                "❌ Laufzeitfehler — Code in Sandbox geladen, Editor unverändert")
                return
        if e._plan_modus_aktiv:
            if not self.plan_dialog_zeigen(neu_code):
                e._set_status("❌ Ersetzen abgebrochen")
                return
        e._backup_erstellen()
        hat_selektion = e._stelle_selektion_wieder_her()
        c = e._editor.textCursor()
        if not hat_selektion or not c.hasSelection():
            if not e._find_in_editor():
                e._editor.setPlainText(neu_code)
                e.speichern()
                e._btn_ersetzen.setEnabled(False)
                e._letzter_editor_cursor = None
                if hasattr(e, "_frage_feld"):
                    e._frage_feld.clear()
                e._set_status("🎉 KI-Code in Editor übertragen und gespeichert")
                return
            c = e._editor.textCursor()
        target_indent = e._erste_einrueckung(
            e._normalize_newlines(c.selectedText()))
        c.beginEditBlock()
        c.insertText(e._reindent_block(neu_code, target_indent))
        c.endEditBlock()
        e.speichern()
        e._btn_ersetzen.setEnabled(False)
        e._letzter_editor_cursor = None
        if hasattr(e, "_frage_feld"):
            e._frage_feld.clear()
        e._set_status("🎉 Block ersetzt und gespeichert")

    def einfuegen_nach_fundstelle(self):
        e = self._e
        neu_code = e._ki_area.toPlainText().strip()
        if not neu_code:
            e._set_status("⚠  KI-Antwort ist leer")
            return
        try:
            _ast.parse(neu_code)
        except SyntaxError as _se:
            _sandbox_fehler(e, neu_code, f"SyntaxError Zeile {_se.lineno}: {_se.msg}")
            return
        _vorschau = getattr(e, "_vorschau", None)
        if _vorschau is not None:
            _rt = _vorschau._vorschau_exec(neu_code, nur_pruefen=True)
            if _rt:
                _sandbox_fehler(e, neu_code, _rt,
                                "❌ Laufzeitfehler — Code in Sandbox geladen, Editor unverändert")
                return
        hat_selektion = e._stelle_selektion_wieder_her()
        c = e._editor.textCursor()
        if not hat_selektion or not c.hasSelection():
            if not e._find_in_editor():
                # Kein Block markiert und nichts gefunden → ans Dateiende einfügen
                c = e._editor.textCursor()
                c.movePosition(QtGui.QTextCursor.End)
                c.beginEditBlock()
                c.insertText("\n\n" + neu_code)
                c.endEditBlock()
                e._editor.setTextCursor(c)
                e.speichern()
                e._btn_einfuegen.setEnabled(False)
                e._letzter_editor_cursor = None
                if hasattr(e, "_frage_feld"):
                    e._frage_feld.clear()
                e._set_status("🎉 Am Dateiende eingefügt und gespeichert")
                return
            c = e._editor.textCursor()
        ziel_indent = e._erste_einrueckung(
            e._normalize_newlines(c.selectedText()))
        c.setPosition(c.selectionEnd())
        c.movePosition(QtGui.QTextCursor.EndOfBlock)
        c.beginEditBlock()
        c.insertText("\n\n" + e._reindent_block(neu_code, ziel_indent))
        c.endEditBlock()
        e._editor.setTextCursor(c)
        e.speichern()
        e._btn_einfuegen.setEnabled(False)
        e._letzter_editor_cursor = None
        if hasattr(e, "_frage_feld"):
            e._frage_feld.clear()
        e._set_status("🎉 Block eingefügt und gespeichert")
