# -*- coding: utf-8 -*-
"""
editor_tabs.py
──────────────
Multi-Tab-Lebenszyklus des MakroEditors: Öffnen, Wechseln, Schließen.
"""

import os

from qt_compat import QtWidgets, QtCore, QtGui

import theme
from highlighter import PythonHighlighter
from fehler import uebersetze_fehler
from editor_widgets import JediEditor


class TabLogik:
    """Verwaltet den Lebenszyklus aller Editor-Tabs."""

    __slots__ = ("_e",)

    def __init__(self, editor):
        self._e = editor

    def tab_oeffnen(self, pfad: str):
        e = self._e
        for i, tab in enumerate(e._tabs):
            if tab["pfad"] == pfad:
                e._editor_tab_widget.setCurrentIndex(i)
                return
        container = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        editor = JediEditor()
        editor.setFont(QtGui.QFont("Courier New", 10))
        editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        editor.setStyleSheet(theme.STY_CODE_EDITOR())
        opt = editor.document().defaultTextOption()
        opt.setAlignment(QtCore.Qt.AlignLeft)
        editor.document().setDefaultTextOption(opt)
        lay.addWidget(editor)
        tab_data = {"pfad": pfad, "geaendert": False, "editor": editor}
        e._tabs.append(tab_data)
        name = os.path.basename(pfad)
        e._editor_tab_widget.addTab(container, name)
        idx = len(e._tabs) - 1
        editor.document().contentsChanged.connect(e._markiere_geaendert)
        editor.cursorPositionChanged.connect(e._update_cursor_info)
        editor.document().blockSignals(True)
        highlighter = PythonHighlighter(editor.document())
        tab_data["highlighter"] = highlighter
        QtCore.QTimer.singleShot(200, highlighter.aktualisiere_theme)
        try:
            with open(pfad, "r", encoding="utf-8") as f:
                inhalt = f.read()
        except UnicodeDecodeError:
            try:
                with open(pfad, "r", encoding="latin-1") as f:
                    inhalt = f.read()
            except Exception as ex:
                inhalt = f"# Fehler beim Laden: {ex}"
        except Exception as ex:
            inhalt = f"# Fehler beim Laden: {ex}"
        editor.document().blockSignals(False)
        editor.setPlainText(inhalt)
        tab_data["geaendert"] = False
        e._editor_tab_widget.setCurrentIndex(idx)
        if pfad not in e._datei_watcher.files():
            e._datei_watcher.addPath(pfad)

    def tab_gewechselt(self, index: int):
        e = self._e
        if 0 <= index < len(e._tabs):
            tab          = e._tabs[index]
            alter_editor = e._editor
            e._editor    = tab["editor"]
            e._pfad      = tab["pfad"]
            e._geaendert = tab["geaendert"]
            name   = os.path.basename(e._pfad)
            suffix = "  *" if e._geaendert else ""
            e.setWindowTitle(f"Makro-Editor  –  {name}{suffix}")
            if alter_editor is not None and alter_editor is not e._editor:
                try:
                    alter_editor.selectionChanged.disconnect(e._on_editor_selection_changed)
                except RuntimeError:
                    pass
            e._letzter_editor_cursor = None
            if alter_editor is not e._editor:
                e._editor.selectionChanged.connect(e._on_editor_selection_changed)
            if hasattr(e, "_ki_verlauf_reset"):
                e._ki_verlauf_reset()
            if hasattr(e, "_werkzeug_leiste"):
                wl = e._werkzeug_leiste
                # alter_editor ist die alte QPlainTextEdit (vor dem Tab-Wechsel)
                if alter_editor is not e._editor:
                    try:
                        alter_editor.cursorPositionChanged.disconnect(wl._cursor_sync)
                        alter_editor.cursorPositionChanged.disconnect(wl._lz_highlight)
                        alter_editor.cursorPositionChanged.disconnect(wl._selektion_sichern)
                    except RuntimeError:
                        pass
                    if hasattr(e, "_baum_timer"):
                        try:
                            alter_editor.textChanged.disconnect(e._baum_timer.start)
                        except RuntimeError:
                            pass
                        e._editor.textChanged.connect(e._baum_timer.start)
                    e._editor.cursorPositionChanged.connect(wl._cursor_sync)
                    e._editor.cursorPositionChanged.connect(wl._lz_highlight)
                    e._editor.cursorPositionChanged.connect(wl._selektion_sichern)
                wl.aktualisiere_code_baum(e._editor.toPlainText())

    def tab_schliessen(self, index: int):
        e = self._e
        if index < 0 or index >= len(e._tabs):
            return
        tab = e._tabs[index]
        if tab["geaendert"]:
            antwort = QtWidgets.QMessageBox.question(
                e, "Ungespeicherte Änderungen",
                f"'{os.path.basename(tab['pfad'])}' speichern?",
                QtWidgets.QMessageBox.StandardButton.Save |
                QtWidgets.QMessageBox.StandardButton.Discard |
                QtWidgets.QMessageBox.StandardButton.Cancel)
            if antwort == QtWidgets.QMessageBox.StandardButton.Cancel:
                return
            if antwort == QtWidgets.QMessageBox.StandardButton.Save:
                try:
                    with open(tab["pfad"], "w", encoding="utf-8") as f:
                        f.write(tab["editor"].toPlainText())
                except Exception as ex:
                    QtWidgets.QMessageBox.critical(e, "Fehler", uebersetze_fehler(ex))
                    return
        pfad      = tab["pfad"]
        restliche = [t for j, t in enumerate(e._tabs) if j != index]
        if not any(t["pfad"] == pfad for t in restliche):
            e._datei_watcher.removePath(pfad)
        e._tabs.pop(index)
        e._editor_tab_widget.removeTab(index)
        if e._editor_tab_widget.count() == 0:
            e.close()

    def markiere_geaendert(self):
        e        = self._e
        sender_doc = e.sender()
        editor_ref = None
        for tab in e._tabs:
            if tab["editor"].document() is sender_doc:
                editor_ref = tab["editor"]
                break
        for i, tab in enumerate(e._tabs):
            if tab["editor"] is editor_ref and not tab["geaendert"]:
                tab["geaendert"] = True
                name = os.path.basename(tab["pfad"])
                e._editor_tab_widget.setTabText(i, f"{name}  *")
                if i == e._editor_tab_widget.currentIndex():
                    e._geaendert = True
                    e.setWindowTitle(f"Makro-Editor  –  {name}  *")
                break
