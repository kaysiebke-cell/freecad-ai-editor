# -*- coding: utf-8 -*-
# FreeCAD führt diese Datei per exec(code, globals, locals) aus.
# __file__ landet in exec-locals und ist in Klassen-Methoden unsichtbar,
# weil Methoden nur exec-globals sehen. Lösung: _MODDIR über globals() in
# den globals-Dict schreiben, damit alle Methoden darauf zugreifen können.

import FreeCADGui as Gui
import FreeCAD
import os
import sys

# __file__ ist im FlatPak-FreeCAD nicht gesetzt → Fallback auf getUserAppDataDir.
# globals() schreibt _MODDIR in exec-globals, damit Klassen-Methoden es sehen.
try:
    globals()['_MODDIR'] = os.path.dirname(os.path.abspath(__file__))
except NameError:
    globals()['_MODDIR'] = os.path.join(
        FreeCAD.getUserAppDataDir(), "Mod", "FreeCAD_MultiAI_Panel"
    )


# ── DESIGN DES NEUEN BUTTONS (KI-ASSISTENT) ───────────────────────────────────
class KiAssistentCommand:

    def GetResources(self):
        ki_path = os.path.join(os.path.expanduser("~"), "Schreibtisch",
                               "Macros", "KI Muli source Assistent")
        assets  = os.path.join(_MODDIR, "assets")
        icon = ""
        for kandidat in (os.path.join(ki_path, "ki_icon.svg"),
                         os.path.join(assets, "Icon.svg")):
            if os.path.exists(kandidat):
                icon = kandidat
                break
        res = {
            'MenuText': "KI Multi-Source Assistent",
            'ToolTip' : "Öffnet den KI Multi-Source Assistenten an der Seite",
        }
        if icon:
            res['Pixmap'] = icon
        return res

    def IsActive(self):
        return True

    def Activated(self):
        ki_path = os.path.join(os.path.expanduser("~"), "Schreibtisch",
                               "Macros", "KI Muli source Assistent")
        if ki_path not in sys.path:
            sys.path.insert(0, ki_path)

        sys.modules.pop("main", None)
        sys.modules.pop("panel", None)

        import main
        import theme

        try:
            from qt_compat import QtWidgets, QtCore, QtGui
        except ImportError:
            from PySide6 import QtWidgets, QtCore, QtGui

        mw = Gui.getMainWindow()
        DOCK_TITLE = "KI Multi-Source Assistent"

        for w in mw.findChildren(QtWidgets.QDockWidget):
            if w.windowTitle() == DOCK_TITLE:
                mw.removeDockWidget(w)
                w.deleteLater()

        dock = QtWidgets.QDockWidget(DOCK_TITLE, mw)
        _f = QtGui.QFont("Ubuntu", 10)
        try:
            _f = main.emoji_font(_f)
        except Exception:
            pass
        dock.setFont(_f)
        dock.setStyleSheet(theme.STY_DOCK_FONT_RESET)

        from panel import FreeCAD_MultiAI_Panel
        panel = FreeCAD_MultiAI_Panel()
        dock.setWidget(panel)
        mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        dock.show()


Gui.addCommand('Cmd_KiAssistent', KiAssistentCommand())


# ── Pfade einrichten ───────────────────────────────────────────────────────────
def _pfade_einrichten():
    for sub in ("", "core",
                "editor", "editor/intern",
                "editor/fehler",
                "editor/ki", "editor/ki/intern",
                "editor/controller", "editor/widgets",
                "ui", "data"):
        p = os.path.join(_MODDIR, sub) if sub else _MODDIR
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


def _panel_starten():
    try:
        _pfade_einrichten()
        import main as makro_main
        makro_main.erstelle_leiste()
    except Exception as e:
        FreeCAD.Console.PrintError(f"[MultiAI] Panel-Start fehlgeschlagen: {e}\n")


# ── DIE HAUPT-WORKBENCH ────────────────────────────────────────────────────────
class MeineMakroWorkbench(Gui.Workbench):
    MenuText = "FreeCAD MultiAI Panel"
    ToolTip  = "FreeCAD MultiAI Panel – KI-gestützter Makro-Editor mit 19 KI-Anbietern"

    def __init__(self):
        super().__init__()
        self.Icon = os.path.join(_MODDIR, "Icon.svg")

    def Initialize(self):
        # Immer aufgerufen wenn Workbench zum ersten Mal aktiviert wird
        _panel_starten()
        self.appendToolbar("Eigene Werkzeuge", ["Cmd_KiAssistent"])

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(MeineMakroWorkbench())


# ── Fallback: Panel auch laden wenn FreeCAD auf anderer Workbench startet ─────
# Initialize() läuft nur bei erster Workbench-Aktivierung. Startet FreeCAD
# z.B. auf Part Design, muss der Timer das Panel trotzdem erstellen.
try:
    from PySide6.QtCore import QTimer
    QTimer.singleShot(1500, _panel_starten)
except Exception:
    pass
