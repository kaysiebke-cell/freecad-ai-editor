# -*- coding: utf-8 -*-
"""
schrift.py  –  Zentrale Schrift-Steuerung für den KI-Makro-Editor.

NUR DIESE DATEI anpassen um Schriften projekteweit zu ändern.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCHRIFT-FAMILIEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# UI-Schrift  (Labels, Buttons, Menüs …)
FAMILIE_UI   = "Ubuntu"

# Code-Schrift  (Editoren, Terminal-Ausgaben …)
FAMILIE_MONO = "Courier New"


"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRÖßEN-STUFEN  –  relative Multiplikatoren (px-frei)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Alle Größen sind Vielfache der System-Standardschrift.
1.0 = Systemgröße, 0.9 = etwas kleiner, 1.3 = größer usw.
"""

# ── Bildschirmgröße erkennen und Stufen anpassen ─────────────────────────────
def _bildschirm_klein() -> bool:
    """True wenn der Bildschirm schmaler als 1366px ist (kleiner Laptop/Monitor)."""
    try:
        from core.qt_compat import QtWidgets
        app = QtWidgets.QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen and screen.availableGeometry().width() < 1366:
                return True
    except Exception:
        pass
    return False

# Kompakter Satz für kleine Bildschirme
if _bildschirm_klein():
    STUFE_XS   = 0.72   # Statuszeile, Hinweis-Kursiv
    STUFE_SM   = 0.80   # Tabs, sekundäre Labels
    STUFE_BASE = 0.88   # Standard-UI-Text
    STUFE_LG   = 0.95   # Abschnitts-Buttons, Modus-Label
    STUFE_XL   = 1.10   # Überschriften, Titel
    STUFE_ICON = 2.00   # Große Emoji-Icons
else:
    STUFE_XS   = 0.80   # Statuszeile, Hinweis-Kursiv
    STUFE_SM   = 0.90   # Tabs, sekundäre Labels
    STUFE_BASE = 1.00   # Standard-UI-Text
    STUFE_LG   = 1.10   # Abschnitts-Buttons, Modus-Label
    STUFE_XL   = 1.30   # Überschriften, Titel
    STUFE_ICON = 2.50   # Große Emoji-Icons


# ── Berechnungslogik  (nicht ändern) ──────────────────────────────────────────

from core.qt_compat import QtWidgets, QtGui


def _system_pt() -> int:
    """Liest die Schriftgröße des App-Standardfonts."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        return 10
    size = app.font().pointSize()
    return size if size > 0 else 10


def pt(stufe: float = STUFE_BASE) -> int:
    """
    Fluid-skalierte Schriftgröße in pt.
    Relativ zur aktuellen System-Standardschrift – passt sich
    automatisch an DPI und OS-Zoom an, da Qt das bereits in
    QApplication.font() einrechnet.
    """
    return max(7, min(int(round(_system_pt() * stufe)), 36))


def css(stufe: float = STUFE_BASE) -> str:
    """CSS-Snippet 'font-size: Xpt;' für StyleSheets."""
    return f"font-size:{pt(stufe)}pt;"


def ui_font(stufe: float = STUFE_BASE) -> QtGui.QFont:
    """QFont für UI-Elemente."""
    return QtGui.QFont(FAMILIE_UI, pt(stufe))


def mono_font(stufe: float = STUFE_BASE) -> QtGui.QFont:
    """QFont für Code-Editoren."""
    return QtGui.QFont(FAMILIE_MONO, pt(stufe))
