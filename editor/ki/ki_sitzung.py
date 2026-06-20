# -*- coding: utf-8 -*-
"""
ki_sitzung.py
─────────────
KISitzung – Sitzung speichern und laden (JSON).
"""

import json as _json
import os as _os

from core.qt_compat import QtWidgets


class KISitzung:
    """Speichert und lädt Chat-Verlauf, KI-Antwort und Einstellungen."""

    def __init__(self, controller):
        self._c = controller

    def speichern(self):
        """Chat-Verlauf, KI-Antwort und Einstellungen in JSON-Datei speichern."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self._c if hasattr(self._c, "parentWidget") else None,
            "Sitzung speichern", "",
            "Sitzungsdateien (*.json);;Alle Dateien (*)")
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"

        daten = {
            "anbieter":   (getattr(self._c, "_src_box", None)
                           and self._c._src_box.currentText() or ""),
            "modell":     (getattr(self._c, "_model_box", None)
                           and self._c._model_box.currentText() or ""),
            "verlauf":    getattr(self._c, "_chat_verlauf", []),
            "ki_antwort": (getattr(self._c, "_ki_area", None)
                           and self._c._ki_area.toPlainText() or ""),
            "ki_eingabe": (getattr(self._c, "find_area", None)
                           and self._c.find_area.toPlainText() or ""),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                _json.dump(daten, f, ensure_ascii=False, indent=2)
            self._c._set_status(f"💾 Sitzung gespeichert: {_os.path.basename(path)}")
        except Exception as e:
            self._c._set_status(f"❌ Speichern fehlgeschlagen: {e}")

    def laden(self):
        """Gespeicherte Sitzung aus JSON-Datei wiederherstellen."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self._c if hasattr(self._c, "parentWidget") else None,
            "Sitzung laden", "",
            "Sitzungsdateien (*.json);;Alle Dateien (*)")
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                daten = _json.load(f)
        except Exception as e:
            self._c._set_status(f"❌ Laden fehlgeschlagen: {e}")
            return

        self._c._chat_verlauf = daten.get("verlauf", [])

        ki_text = daten.get("ki_antwort", "")
        if ki_text and hasattr(self._c, "_ki_area"):
            self._c._ki_area.setPlainText(ki_text)

        ki_eingabe = daten.get("ki_eingabe", "")
        if ki_eingabe and hasattr(self._c, "find_area"):
            self._c.find_area.setPlainText(ki_eingabe)

        anbieter = daten.get("anbieter", "")
        if anbieter and hasattr(self._c, "_src_box"):
            idx = self._c._src_box.findText(anbieter)
            if idx >= 0:
                self._c._src_box.setCurrentIndex(idx)

        n = len(self._c._chat_verlauf)
        self._c._set_status(
            f"📂 Sitzung geladen: {_os.path.basename(path)} · {n} Nachrichten")
