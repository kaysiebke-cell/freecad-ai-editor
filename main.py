# -*- coding: utf-8 -*-
"""
Einstiegspunkt für die FreeCAD Makro-Seitenleiste.
Führe diese Datei als FreeCAD-Makro aus oder lade sie über InitGui.py.

Dateistruktur:
  main.py          ← diese Datei (Einstiegspunkt)
  core/            ← params, qt_compat, theme, highlighter
  editor/          ← MakroEditor + Kompositions-Controller
  ui/              ← manager, begruessung, fehler
  data/            ← freecad_data, hilfe, hilfe_texte
"""

import sys
import os

# ── SYSTEM-PACKAGES FÜR DAS APPIMAGE FREIGEBEN ───────────────────────────────
_SYSTEM_DIST_PACKAGES = "/usr/lib/python3/dist-packages"
if os.path.exists(_SYSTEM_DIST_PACKAGES) and _SYSTEM_DIST_PACKAGES not in sys.path:
    sys.path.append(_SYSTEM_DIST_PACKAGES)

# ── Eigenes Verzeichnis + Unterordner zum Python-Pfad hinzufügen ──────────────
# FreeCAD setzt __file__ manchmal relativ — daher mehrere Fallbacks
try:
    _DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _DIR = os.getcwd()

# Wenn das Verzeichnis falsch aufgelöst wurde (kein core/ drin), CWD versuchen
if not os.path.isdir(os.path.join(_DIR, "core")):
    _DIR = os.getcwd()

# Letzter Fallback: bekannte Installationspfade durchsuchen
if not os.path.isdir(os.path.join(_DIR, "core")):
    for _candidate in [
        os.path.expanduser("~/Schreibtisch/Macros/project_fixed"),
        os.path.expanduser("~/Desktop/Macros/project_fixed"),
        os.path.expanduser("~/.FreeCAD/Macro/project_fixed"),
        os.path.join(os.path.expanduser("~"), ".local", "share", "FreeCAD", "Macro", "project_fixed"),
    ]:
        if os.path.isdir(os.path.join(_candidate, "core")):
            _DIR = _candidate
            break
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

# ── Modul-Cache leeren (Hot-Reload ohne FreeCAD-Neustart) ─────────────────────
_EIGENE_MODULE = [
    # core
    "core.params", "core.qt_compat", "core.theme", "core.highlighter", "core.schrift",
    # editor (Haupt)
    "editor.panel", "editor.editor", "editor.widgets.editor_widgets",
    # editor/ki
    "editor.ki.ki_controller", "editor.ki.ki_werkzeuge", "editor.ki.dokument_kontext",
    # editor/controller
    "editor.controller.browser_controller", "editor.controller.snippet_controller",
    "editor.controller.snippet_widgets", "editor.controller.vorschau_controller",
    "editor.controller.werkzeuge", "editor.controller.bibliothek_tab",
    "editor.controller.ki_tools_tab",
    # editor/fehler
    "editor.fehler.fehler_panel", "ui.fehler",
    # editor/builders, editor/subsysteme
    "editor.builders.central_widget_builder", "editor.builders.dock_builder",
    "editor.builders.toolbar_builder", "editor.ki.ki_widget_builder",
    "editor.subsysteme.editor_barrierefreiheit", "editor.subsysteme.editor_code",
    "editor.subsysteme.editor_datei", "editor.subsysteme.editor_plan",
    "editor.subsysteme.editor_suche", "editor.subsysteme.editor_tabs",
    # ui
    "ui.manager", "ui.begruessung", "ui.barrierefreiheit",
    # data
    "data.freecad_data", "data.hilfe", "data.hilfe_texte",
    "data.bibliothek",
    # ki
    "editor.ki.nl_generator", "editor.ki.ki_modi",
    # sandbox_cache bewusst NICHT hier — bleibt persistent für Python-Pfad-Cache
]
for _modul in _EIGENE_MODULE:
    sys.modules.pop(_modul, None)

# ── Imports (nach Cache-Leerung!) ─────────────────────────────────────────────
from core.qt_compat import QtWidgets, QtCore, QtGui
from core import theme

import FreeCADGui as Gui

# ── Emoji-Schrift ─────────────────────────────────────────────────────────────
def emoji_font(f: QtGui.QFont) -> QtGui.QFont:
    """Gibt den Font unverändert zurück (Emoji via System-fontconfig)."""
    return f


from core.params import DOCK_NAME, ist_erststart, fenster_schwebend, set_fenster_schwebend
from ui.manager import MakroLeiste
from ui.begruessung import zeige_begruessung


def erstelle_leiste():
    mw = Gui.getMainWindow()

    altes = mw.findChild(QtWidgets.QDockWidget, DOCK_NAME)
    if altes:
        mw.removeDockWidget(altes)
        altes.deleteLater()

    dock = QtWidgets.QDockWidget("Makro", mw)
    dock.setObjectName(DOCK_NAME)
    dock.setAllowedAreas(
        QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
    dock.setWidget(MakroLeiste())

    # Benutzerdefinierte Titelleiste
    tb = QtWidgets.QWidget()
    tb.setStyleSheet(theme.STY_DOCK_TITLE_BAR)
    tb.setFixedHeight(26)
    tbl = QtWidgets.QHBoxLayout(tb)
    tbl.setContentsMargins(6, 0, 2, 5)
    tbl.setSpacing(8)
    tbl.addWidget(QtWidgets.QLabel("Makro"))
    tbl.addStretch()

    class IconLabel(QtWidgets.QLabel):
        clicked = QtCore.Signal()

        def __init__(self, text, tooltip, rad_l=False, rad_r=False):
            super().__init__(text)
            self.setFixedSize(18, 18)
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setToolTip(tooltip)
            self.setStyleSheet(theme.STY_DOCK_ICON_LABEL(rad_l, rad_r))

        def mousePressEvent(self, e):
            if e.button() == QtCore.Qt.LeftButton:
                self.clicked.emit()

    bf = IconLabel("⧉", "Abdocken", rad_l=True)
    bf.clicked.connect(lambda: dock.setFloating(not dock.isFloating()))
    tbl.addWidget(bf)

    bm = IconLabel("–", "Minimieren")
    bm.clicked.connect(lambda: dock.setFloating(True) or dock.showMinimized())
    tbl.addWidget(bm)

    bc = IconLabel("✕", "Schließen", rad_r=True)
    bc.clicked.connect(lambda: dock.close())
    tbl.addWidget(bc)

    dock.setTitleBarWidget(tb)

    # ── Floating-Signal: native Titelleiste bei abgedocktem Fenster ───────
    def _on_floating_changed(floating: bool):
        if floating:
            # Abgedockt → native OS-Titelleiste mit Maximieren/Minimieren
            dock.setTitleBarWidget(None)
            dock.setWindowFlags(
                dock.windowFlags()
                | QtCore.Qt.WindowMinimizeButtonHint
                | QtCore.Qt.WindowMaximizeButtonHint
            )
            dock.show()
        else:
            # Wieder angedockt → eigene Titelleiste zurück
            dock.setTitleBarWidget(tb)

    dock.topLevelChanged.connect(_on_floating_changed)
    # Letzten Zustand (schwebend/angedockt) merken
    dock.topLevelChanged.connect(set_fenster_schwebend)
    mw.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

    model_dock = mw.findChild(QtWidgets.QDockWidget, "Model")
    if model_dock:
        mw.tabifyDockWidget(model_dock, dock)

    # Gespeicherten Zustand wiederherstellen
    if fenster_schwebend():
        dock.setFloating(True)

    dock.show()
    dock.raise_()

    if ist_erststart():
        QtCore.QTimer.singleShot(300, lambda: zeige_begruessung(mw))


# ── Start-Steuerung ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    erstelle_leiste()
