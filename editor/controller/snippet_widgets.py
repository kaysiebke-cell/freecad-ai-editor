# -*- coding: utf-8 -*-
"""
snippet_widgets.py
──────────────────
Hilfs-Widgets und Worker-Threads für den Snippet-Tab:
  SnipCommandEdit    – KI-Eingabefeld mit /snip-Autocomplete
  OnlineMakroWorker  – lädt Makro-Liste von GitHub
  OnlinePreviewWorker – lädt einzelnen Makro-Code von GitHub
  _BlauBanner        – Hintergrund-Banner mit Palette-Highlight-Farbe
"""

import json
import urllib.request

from qt_compat import QtWidgets, QtCore, QtGui
import theme
import schrift

import re as _re

_FC_MAKRO_API = "https://api.github.com/repos/FreeCAD/FreeCAD-macros/contents/Utility"


# ══ Snip-Command-Eingabefeld ══════════════════════════════════════════════════

class SnipCommandEdit(QtWidgets.QPlainTextEdit):
    """
    KI-Eingabefeld mit /snip-Autocomplete.

    Workflow:
      1. '/' eintippen → Rahmen wird blau + Popup öffnet sich sofort
      2. Weitere Buchstaben filtern die Liste live
      3. Klick oder Enter → Snippet-Code wird ins Feld geladen
      4. Escape / anderer Text → Popup schließt, Rahmen normal
    """
    snip_gewaehlt = QtCore.Signal(str, str)  # (name, code)

    def __init__(self, snip_getter, parent=None):
        """snip_getter() → dict[name, code] – live abgerufen bei jedem Tastendruck."""
        super().__init__(parent)
        self._snip_getter = snip_getter
        self._slash_modus = False

        # ── Popup ────────────────────────────────────────────────────────
        self._popup = QtWidgets.QListWidget()
        self._popup.setWindowFlags(
            QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
        self._popup.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self._popup.setStyleSheet(
            theme.STY_SNIP_POPUP(schrift.pt(schrift.STUFE_BASE)))
        self._popup.setFocusPolicy(QtCore.Qt.NoFocus)
        self._popup.itemClicked.connect(self._eintrag_gewaehlt)
        self._popup.hide()

        # ── Header-Label über dem Popup ───────────────────────────────────
        self._popup_header = QtWidgets.QLabel()
        self._popup_header.setWindowFlags(
            QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
        self._popup_header.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self._popup_header.setStyleSheet(
            theme.STY_SNIP_POPUP_HEADER(schrift.pt(schrift.STUFE_SM)))
        self._popup_header.hide()

        self.textChanged.connect(self._check_slash_command)

    def _check_slash_command(self):
        text = self.toPlainText()
        match = _re.match(r"^/(\w*)$", text.strip())

        if not match:
            if self._slash_modus:
                self._slash_modus = False
                self._popup.hide()
                self._popup_header.hide()
            return

        if not self._slash_modus:
            self._slash_modus = True
        filter_text = match.group(1).lower()
        snips = self._snip_getter()
        treffer = sorted(
            name for name in snips if filter_text in name.lower())

        self._popup.clear()

        if not treffer:
            if not snips:
                msg = "Noch keine Snippets – im 📦 Snip-Tab anlegen"
            else:
                msg = f"Kein Snippet enthaelt '{filter_text}'"
            item = QtWidgets.QListWidgetItem(msg)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)
            item.setForeground(self.palette().color(QtGui.QPalette.Text))
            self._popup.addItem(item)
        else:
            for name in treffer:
                item = QtWidgets.QListWidgetItem(f"📦  /{name}")
                item.setData(QtCore.Qt.UserRole, name)
                self._popup.addItem(item)
            self._popup.setCurrentRow(0)

        anzahl = len(treffer)
        header_text = (
            f"  Snippets  –  {anzahl} Treffer  ·  ↵ Einfügen  ·  Esc Abbrechen  "
            if treffer else
            "  /snippet-name  –  Snippet ins Suchfeld laden  "
        )
        self._popup_header.setText(header_text)

        pos    = self.mapToGlobal(QtCore.QPoint(0, self.height()))
        breite = max(self.width(), 260)
        zeilen = min(8, max(1, anzahl)) if treffer else 1
        hoehe  = zeilen * 26 + 10

        self._popup_header.move(pos)
        self._popup_header.resize(breite, 18)
        self._popup_header.show()
        self._popup_header.raise_()

        self._popup.move(pos.x(), pos.y() + 18)
        self._popup.resize(breite, hoehe)
        self._popup.show()
        self._popup.raise_()

    def _eintrag_gewaehlt(self, item):
        if not (item.flags() & QtCore.Qt.ItemIsEnabled):
            return
        name = item.data(QtCore.Qt.UserRole)
        code = self._snip_getter().get(name, "")
        self._popup.hide()
        self._popup_header.hide()
        self._slash_modus = False
        self.snip_gewaehlt.emit(name, code)

    def keyPressEvent(self, event):
        if self._popup.isVisible():
            if event.key() == QtCore.Qt.Key_Down:
                row = min(self._popup.currentRow() + 1, self._popup.count() - 1)
                self._popup.setCurrentRow(row)
                return
            if event.key() == QtCore.Qt.Key_Up:
                row = max(self._popup.currentRow() - 1, 0)
                self._popup.setCurrentRow(row)
                return
            if event.key() == QtCore.Qt.Key_Escape:
                self._popup.hide()
                self._popup_header.hide()
                self._slash_modus = False
                return
            if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                item = self._popup.currentItem()
                if item and (item.flags() & QtCore.Qt.ItemIsEnabled):
                    self._eintrag_gewaehlt(item)
                    return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        if self._popup.isVisible():
            QtCore.QTimer.singleShot(250, self._verberge_popup)
        super().focusOutEvent(event)

    def _ist_popup_widget(self, widget) -> bool:
        if widget is None:
            return True
        if widget is self or widget is self._popup or widget is self._popup_header:
            return True
        if self._popup.isAncestorOf(widget):
            return True
        return False

    def _verberge_popup(self):
        focused = QtWidgets.QApplication.focusWidget()
        if self._ist_popup_widget(focused):
            return
        self._popup.hide()
        self._popup_header.hide()
        if self._slash_modus:
            self._slash_modus = False


# ══ Hintergrund-Worker ═══════════════════════════════════════════════════════

class OnlineMakroWorker(QtCore.QThread):
    """Lädt die Makro-Liste vom offiziellen FreeCAD-GitHub-Repo im Hintergrund."""
    liste_geladen = QtCore.Signal(dict)
    fehler        = QtCore.Signal(str)

    def run(self):
        try:
            req = urllib.request.Request(
                _FC_MAKRO_API,
                headers={"User-Agent": "FreeCAD-Macro-Editor",
                         "Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                daten  = json.loads(resp.read().decode())
                makros = {
                    item["name"]: item["download_url"]
                    for item in daten
                    if item.get("name", "").endswith((".FCMacro", ".py"))
                }
                self.liste_geladen.emit(makros)
        except Exception as e:
            self.fehler.emit(str(e))


class OnlinePreviewWorker(QtCore.QThread):
    """
    Lädt den Code eines einzelnen Online-Makros für die Vorschau – blockiert
    nie den UI-Thread. Wird bei jedem Klick auf ein Online-Snippet gestartet.
    """
    code_geladen = QtCore.Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            req = urllib.request.Request(
                self.url, headers={"User-Agent": "FreeCAD-Macro-Editor"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.code_geladen.emit(resp.read().decode("utf-8"))
        except Exception as e:
            self.code_geladen.emit(f"# Download fehlgeschlagen:\n# {e}")


# ══ Hilfs-Widget ══════════════════════════════════════════════════════════════

class _BlauBanner(QtWidgets.QFrame):
    """Banner mit blauem Hintergrund – Farbe kommt aus der Palette (Highlight)."""
    def paintEvent(self, event):
        col = self.palette().color(QtGui.QPalette.Highlight)
        col.setAlpha(60)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(col)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 5, 5)
        painter.end()
