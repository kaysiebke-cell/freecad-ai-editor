# -*- coding: utf-8 -*-
"""Farbschema, semantische Tints, Syntax-Highlight-Farben, Status-Farben."""

from core.qt_compat import QtWidgets, QtCore, QtGui
from core import schrift
from core import farben as _farben_mod

# Standard Dunkelmod; wird beim Start aus Prefs geladen
_FARBSCHEMA_DUNKEL: bool = True


def ist_dunkel() -> bool:
    """Gibt True zurück wenn Dunkelmod aktiv ist."""
    return _FARBSCHEMA_DUNKEL


def set_farbschema(dunkel: bool) -> None:
    """Setzt das Farbschema. Muss nach Änderung rehighlight() auf allen Editoren auslösen."""
    global _FARBSCHEMA_DUNKEL
    _FARBSCHEMA_DUNKEL = dunkel


def _semantik_tint_hex(widget: "QtWidgets.QWidget", schluessel: str) -> str:
    """Gibt die Tint-Farbe für das Eingabefeld aus farben.py zurück."""
    f = _farben_mod.DUNKEL if _FARBSCHEMA_DUNKEL else _farben_mod.HELL
    return f[schluessel]


def _apply_semantik_tint(widget: "QtWidgets.QWidget", schluessel: str) -> None:
    """Setzt Hintergrundfarbe aus farben.py ins Stylesheet. Basis bleibt erhalten."""
    def _do():
        col = _semantik_tint_hex(widget, schluessel)
        f = _farben_mod.DUNKEL if _FARBSCHEMA_DUNKEL else _farben_mod.HELL
        txt = f["text"]
        cls = type(widget).__name__
        if cls in ("QPlainTextEdit", "LinksTextEdit", "SnipCommandEdit", "CodeEditor"):
            sel = "QPlainTextEdit"
        elif cls == "QLabel":
            sel = "QLabel"
        elif cls == "QLineEdit":
            sel = "QLineEdit"
        else:
            sel = "QPlainTextEdit"
        snippet = f"{sel} {{ background-color: {col}; color: {txt}; }}"
        # Basis-Stylesheet einmalig merken – verhindert Stapeln beim Moduswechsel
        if not hasattr(widget, "_tint_basis"):
            widget._tint_basis = widget.styleSheet()
        widget.setStyleSheet((widget._tint_basis + "\n" + snippet) if widget._tint_basis else snippet)
    QtCore.QTimer.singleShot(50, _do)


def apply_input_bg_suche(widget: "QtWidgets.QWidget") -> None:
    _apply_semantik_tint(widget, "tint_suche")


def apply_input_bg_ki(widget: "QtWidgets.QWidget") -> None:
    _apply_semantik_tint(widget, "tint_ki")


def apply_input_bg_kontext(widget: "QtWidgets.QWidget") -> None:
    _apply_semantik_tint(widget, "tint_kontext")


def _misch_hex(widget: "QtWidgets.QWidget", faktor: float) -> str:
    """
    Mischt die Fenster-Hintergrundfarbe um `faktor` (0…1) in Richtung Textfarbe.
    Ergibt in dunklen Paletten ein helleres Grau, in hellen ein dunkleres.
    """
    pal = widget.palette()
    bg = pal.color(QtGui.QPalette.Window)
    fg = pal.color(QtGui.QPalette.WindowText)
    nr = int(bg.red()   * (1 - faktor) + fg.red()   * faktor)
    ng = int(bg.green() * (1 - faktor) + fg.green() * faktor)
    nb = int(bg.blue()  * (1 - faktor) + fg.blue()  * faktor)
    return f"#{nr:02x}{ng:02x}{nb:02x}"


def _ist_dunkel(widget: "QtWidgets.QWidget") -> bool:
    """True, wenn die System-Palette des Widgets dunkel ist."""
    return widget.palette().color(QtGui.QPalette.Window).lightness() < 128


def farbe_ok(widget: "QtWidgets.QWidget") -> str:
    """Erfolgs-Grün aus der Palette abgeleitet – kein Hex hartkodiert."""
    base = widget.palette().color(QtGui.QPalette.Base)
    dunkel = base.lightness() < 128
    l = 80 if dunkel else 35
    return QtGui.QColor.fromHsl(130, 180, l).name()


def farbe_fehler(widget: "QtWidgets.QWidget") -> str:
    """Fehler-Rot aus der Palette abgeleitet – kein Hex hartkodiert."""
    base = widget.palette().color(QtGui.QPalette.Base)
    dunkel = base.lightness() < 128
    l = 90 if dunkel else 45
    return QtGui.QColor.fromHsl(4, 210, l).name()


def farbe_gedaempft(widget: "QtWidgets.QWidget") -> str:
    """Gedämpfter Hinweiston — direkt aus der System-Palette."""
    return widget.palette().color(QtGui.QPalette.Mid).name()


def sty_status(widget: "QtWidgets.QWidget", art: str = "") -> str:
    """
    Stylesheet für Status-Labels: art = 'ok' | 'fehler' | '' (neutral).
    Farbe kommt zur Laufzeit aus der Palette — nichts hartkodiert im Widget.
    """
    basis = f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_BASE)}pt; padding:4px;"
    if art == "ok":
        return basis + f" color:{farbe_ok(widget)}; }}"
    if art == "fehler":
        return basis + f" color:{farbe_fehler(widget)}; }}"
    return basis + " }"


def _c(hex6: str) -> "QtGui.QColor":
    return QtGui.QColor(hex6)


def syntax_farben() -> "tuple[dict[str, QtGui.QColor], QtGui.QColor]":
    """Gibt (farb_dict, text_farbe) passend zum gewählten Farbschema zurück."""
    f = _farben_mod.DUNKEL if _FARBSCHEMA_DUNKEL else _farben_mod.HELL
    farb_dict = {k: _c(v) for k, v in f.items() if k not in ("text", "tint_suche", "tint_ki", "tint_kontext")}
    text_farbe = _c(f["text"])
    return farb_dict, text_farbe


def STY_CODE_EDITOR() -> str:
    f = _farben_mod.DUNKEL if _FARBSCHEMA_DUNKEL else _farben_mod.HELL
    return f"QPlainTextEdit{{font-family:'Courier New',monospace;color:{f['text']};}}"


# Rückwärts-Kompatibilität
farben = {
    "keyword":    "#4FC1E9",
    "builtin":    "#56B6C2",
    "self":       "#E06C75",
    "decorator":  "#C678DD",
    "def_name":   "#61AFEF",
    "class_name": "#E5C07B",
    "zahl":       "#98C379",
    "string":     "#D19A66",
    "operator":   "#ABB2BF",
    "kommentar":  "#6A9955",
    "fstring":    "#D19A66",
    "triple":     "#D19A66",
}
SYNTAX_FARBEN     = farben
SYNTAX_TEXT_FARBE = "#D4D4D4"
