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
for _sub in ("", "core", "editor/fehler", "editor/ki", "editor/ki/intern", "editor/controller", "editor/widgets", "editor/intern", "editor", "ui", "data"):
    _p = os.path.join(_DIR, _sub) if _sub else _DIR
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Editor-Pfad explizit sicherstellen ───────────────────────────────────────
_EDITOR_DIR = os.path.join(_DIR, "editor")
if _EDITOR_DIR not in sys.path:
    sys.path.insert(0, _EDITOR_DIR)

# ── Modul-Cache leeren (Hot-Reload ohne FreeCAD-Neustart) ─────────────────────
_EIGENE_MODULE = [
    # core
    "params", "qt_compat", "theme", "highlighter", "schrift",
    # editor (Haupt)
    "editor", "editor_widgets", "freecad_helfer_panel",
    # editor/ki
    "ki_controller", "ki_werkzeuge", "dokument_kontext",
    # editor/controller
    "browser_controller", "snippet_controller", "snippet_widgets",
    "vorschau_controller", "werkzeuge", "bibliothek_tab", "ki_tools_tab",
    # editor/fehler
    "fehler_panel", "fehler",
    # ui
    "manager", "begruessung", "barrierefreiheit",
    # data
    "freecad_data", "hilfe", "hilfe_texte", "nl_generator", "ki_modi", "bibliothek",
    # sandbox_cache bewusst NICHT hier — bleibt persistent für Python-Pfad-Cache
]
for _modul in _EIGENE_MODULE:
    sys.modules.pop(_modul, None)

# ── Imports (nach Cache-Leerung!) ─────────────────────────────────────────────
from qt_compat import QtWidgets, QtCore, QtGui
import theme

import FreeCADGui as Gui

# ── Emoji-Schrift ─────────────────────────────────────────────────────────────
def emoji_font(f: QtGui.QFont) -> QtGui.QFont:
    """Gibt den Font unverändert zurück (Emoji via System-fontconfig)."""
    return f


from params import DOCK_NAME, ist_erststart, fenster_schwebend, set_fenster_schwebend
from manager import MakroLeiste
from begruessung import zeige_begruessung


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
    _leiste = MakroLeiste()
    # Dock-Referenz direkt auf dem Widget speichern – Buttons greifen darüber zu
    _leiste._haupt_dock = dock
    dock.setWidget(_leiste)

    # Buttons im Einstellungs-Tab synchron halten wenn Modus extern wechselt
    def _sync_modus_buttons(floating: bool):
        try:
            editor = next((w for w in _leiste.findChildren(QtWidgets.QWidget)
                           if hasattr(w, "_btn_andockbar")), None)
            if editor:
                editor._btn_frei.setChecked(floating)
                editor._btn_andockbar.setChecked(not floating)
        except Exception:
            pass
    dock.topLevelChanged.connect(_sync_modus_buttons)

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

    def _on_floating_changed_save(floating: bool):
        set_fenster_schwebend(floating)

    dock.topLevelChanged.connect(_on_floating_changed)
    dock.topLevelChanged.connect(_on_floating_changed_save)
    mw.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

    model_dock = mw.findChild(QtWidgets.QDockWidget, "Model")
    if model_dock:
        mw.tabifyDockWidget(model_dock, dock)

    # Gespeicherten Fenstermodus anwenden
    if fenster_schwebend():
        dock.setFloating(True)

    dock.show()
    dock.raise_()

    if ist_erststart():
        QtCore.QTimer.singleShot(300, lambda: zeige_begruessung(mw))


# ── Start-Steuerung ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    erstelle_leiste()
