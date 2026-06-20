# -*- coding: utf-8 -*-
"""
editor_datei.py
───────────────
Datei-I/O und Backup-Verwaltung für den MakroEditor.
"""

import os
import glob
import shutil
from datetime import datetime

from core.qt_compat import QtWidgets, QtCore

from ui.fehler import uebersetze_fehler


class DateiLogik:
    """Kapselt alle Datei- und Backup-Operationen."""

    __slots__ = ("_e",)

    def __init__(self, editor):
        self._e = editor

    # ── Datei-I/O ─────────────────────────────────────────────────────────

    def speichern(self):
        e = self._e
        idx = e._editor_tab_widget.currentIndex()
        if idx < 0 or idx >= len(e._tabs):
            return
        tab = e._tabs[idx]
        try:
            e._watcher_pause = True
            with open(tab["pfad"], "w", encoding="utf-8") as f:
                f.write(tab["editor"].toPlainText())
            tab["geaendert"] = False
            e._geaendert = False
            name = os.path.basename(tab["pfad"])
            e._editor_tab_widget.setTabText(idx, name)
            e.setWindowTitle(f"Makro-Editor  –  {name}")
            e._set_status("✔  Gespeichert")
            QtCore.QTimer.singleShot(500, lambda: setattr(e, "_watcher_pause", False))
            if tab["pfad"] not in e._datei_watcher.files():
                e._datei_watcher.addPath(tab["pfad"])
        except Exception as ex:
            e._watcher_pause = False
            QtWidgets.QMessageBox.critical(
                e, "Fehler beim Speichern", uebersetze_fehler(ex))

    def speichern_und_schliessen(self):
        e = self._e
        self.speichern()
        if not e._geaendert:
            e._tab_schliessen(e._editor_tab_widget.currentIndex())

    def neu_laden(self):
        e = self._e
        idx = e._editor_tab_widget.currentIndex()
        if idx < 0 or idx >= len(e._tabs):
            return
        tab = e._tabs[idx]
        try:
            with open(tab["pfad"], "r", encoding="utf-8") as f:
                tab["editor"].setPlainText(f.read())
            tab["geaendert"] = False
            e._geaendert = False
            name = os.path.basename(tab["pfad"])
            e._editor_tab_widget.setTabText(idx, name)
            e.setWindowTitle(f"Makro-Editor  –  {name}")
            e._set_status("↺  Neu geladen")
        except Exception as ex:
            QtWidgets.QMessageBox.critical(
                e, "Fehler beim Laden", uebersetze_fehler(ex))

    def datei_extern_geaendert(self, pfad: str):
        e = self._e
        if e._watcher_pause:
            return
        QtCore.QTimer.singleShot(100, lambda: e._datei_watcher.addPath(e._pfad))
        e._set_status(
            "⚠  Datei wurde extern geändert  –  [↺ Neu laden] um zu aktualisieren", ms=0)

    def alles_auswaehlen(self):
        e = self._e
        e._editor.selectAll()
        e._editor.setFocus()

    def loeschen_auswahl(self):
        e = self._e
        c = e._editor.textCursor()
        if c.hasSelection():
            c.removeSelectedText()
        elif QtWidgets.QMessageBox.question(
            e, "Leeren", "Gesamten Inhalt löschen?",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            e._editor.clear()

    # ── Backup ────────────────────────────────────────────────────────────

    def backup_ordner(self) -> str:
        ordner = os.path.join(os.path.dirname(self._e._pfad), "__backups__")
        os.makedirs(ordner, exist_ok=True)
        return ordner

    def backup_erstellen(self) -> str:
        e = self._e
        dateiname = os.path.basename(e._pfad)
        bak_name  = f"{dateiname}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        bak_pfad  = os.path.join(self.backup_ordner(), bak_name)
        try:
            shutil.copy2(e._pfad, bak_pfad)
            alle = sorted(glob.glob(
                os.path.join(self.backup_ordner(), f"{dateiname}.*.bak")))
            for alt in alle[:-3]:
                os.remove(alt)
            e._set_status(f"💾 Backup: {bak_name}", ms=3000)
            return bak_pfad
        except Exception as ex:
            e._set_status(f"⚠ Backup fehlgeschlagen: {ex}")
            return ""

    def backup_wiederherstellen(self):
        e = self._e
        dateiname = os.path.basename(e._pfad)
        alle = sorted(glob.glob(
            os.path.join(self.backup_ordner(), f"{dateiname}.*.bak")))
        if not alle:
            e._set_status("⚠ Kein Backup gefunden")
            return
        neuestes = alle[-1]
        antwort = QtWidgets.QMessageBox.question(
            e, "Backup wiederherstellen",
            f"Neuestes Backup laden?\n\n{os.path.basename(neuestes)}",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No)
        if antwort != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            with open(neuestes, "r", encoding="utf-8") as f:
                e._editor.setPlainText(f.read())
            e._set_status(f"↩ Backup geladen: {os.path.basename(neuestes)}")
        except Exception as ex:
            QtWidgets.QMessageBox.critical(e, "Fehler", uebersetze_fehler(ex))
