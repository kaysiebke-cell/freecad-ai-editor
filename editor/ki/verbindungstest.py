# -*- coding: utf-8 -*-
"""
verbindungstest.py
──────────────────
Hintergrund-Thread zum Testen der aktuell gewählten KI-Verbindung.
Ergebnis wird als Signal zurückgegeben.
"""

from core.qt_compat import QtCore


class VerbindungsTest(QtCore.QThread):
    """Testet die Verbindung zur aktuell gewählten KI-Quelle im Hintergrund."""

    ergebnis = QtCore.Signal(str)   # gibt die Status-Meldung zurück

    def __init__(self, quelle: str, api_key: str, parent=None):
        super().__init__(parent)
        self._quelle  = quelle
        self._api_key = api_key

    def run(self):
        quelle_lower = self._quelle.lower()
        if "ollama" in quelle_lower or "lokal" in quelle_lower:
            self._teste_ollama()
        else:
            self._teste_api_key()

    def _teste_ollama(self):
        try:
            import urllib.request
            req = urllib.request.urlopen(
                "http://localhost:11434/api/tags", timeout=5)
            if req.status == 200:
                self.ergebnis.emit("✅ Verbunden")
            else:
                self.ergebnis.emit("❌ Nicht erreichbar")
        except Exception:
            self.ergebnis.emit("❌ Nicht erreichbar")

    def _teste_api_key(self):
        key = self._api_key.strip()
        if key:
            self.ergebnis.emit("🔑 Key vorhanden")
        else:
            self.ergebnis.emit("⚠ Kein API-Key")
