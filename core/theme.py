# -*- coding: utf-8 -*-
"""
theme.py  –  Zentrales Design-Modul für den KI-Makro-Editor.

Alle Schriften, Farben, Stylesheets und UI-Texte werden hier definiert.
Kein anderes Modul darf Schriftnamen, CSS-Strings oder UI-Texte
direkt hartkodieren  →  immer aus diesem Modul laden.

Verwendung:
    import theme

    # Globale Schrift auf ein Widget anwenden
    theme.apply_global_font(self)

    # Label layoutstabil machen
    self.label = QtWidgets.QLabel(theme.TEXTS["mein_schluessel"])
    theme.stabilize_label(self.label)

    # Texteditor bombensicher konfigurieren (nach setPlainText aufrufen)
    self.editor = QtWidgets.QPlainTextEdit()
    self.editor.setPlainText(inhalt)
    theme.stabilize_text_editor(self.editor)
"""

from qt_compat import QtWidgets, QtCore, QtGui
import schrift


# ═══════════════════════════════════════════════════════════════════════════════
# SCHRIFT-KONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
_FONT_UI_FAMILY   = schrift.FAMILIE_UI
_FONT_MONO_FAMILY = schrift.FAMILIE_MONO
_FONT_UI_SIZE     = schrift.pt(schrift.STUFE_BASE)
_FONT_MONO_SIZE   = schrift.pt(schrift.STUFE_BASE)


def _wrap_emoji(f: QtGui.QFont) -> QtGui.QFont:
    """Delegiert an main.emoji_font (System-fontconfig-Fallback für Emoji)."""
    try:
        from main import emoji_font
        return emoji_font(f)
    except Exception:
        return f


def ui_font() -> QtGui.QFont:
    """Gibt die Standard-UI-Schrift zurück, fluid-skaliert, Emoji-sicher."""
    return _wrap_emoji(schrift.ui_font())


def mono_font() -> QtGui.QFont:
    """Gibt die Monospace-Schrift zurück, fluid-skaliert, Emoji-sicher."""
    return _wrap_emoji(schrift.mono_font())


# ═══════════════════════════════════════════════════════════════════════════════
# UI-TEXTE  –  nie hartkodiert im Widget-Code
# ═══════════════════════════════════════════════════════════════════════════════
TEXTS: dict[str, str] = {
    # Hilfe-Tab
    "hilfe_suche_placeholder": "Hilfe durchsuchen …",
    "hilfe_version_label":     "KI-Makro-Editor  •  v1.1",
    "hilfe_tab_titel":         "❓ Hilfe",
    "hilfe_suche_icon":        "🔍",
}


# ═══════════════════════════════════════════════════════════════════════════════
# FARBEN & ABSCHNITTS-AKZENTE  (Hilfe-Tab)
# ═══════════════════════════════════════════════════════════════════════════════
# Jedes Tupel: (Titel-Präfix, Textfarbe, Hintergrundfarbe)
HILFE_FARBEN: list[tuple[str, str, str]] = [
    ("⚠",          "", ""),   # orange  – Warnungen
    ("📦 Install",  "", ""),   # türkis  – Installation
    ("🔧",          "", ""),   # grün    – Skript anpassen
    ("✂️",          "", ""),   # grün    – Code-Blöcke
    ("🎨",          "", ""),   # grün    – Darstellung
]
HILFE_FARBE_DEFAULT: tuple[str, str] = ("", "")  # hellblau


# ═══════════════════════════════════════════════════════════════════════════════
# STYLESHEET-KONSTANTEN
# ═══════════════════════════════════════════════════════════════════════════════
# QPlainTextEdit-Body in Hilfe-Abschnitten
STY_PLAIN_TEXT_BODY: str = (
    "QPlainTextEdit{"
    f"font-family:'{_FONT_MONO_FAMILY}', monospace; font-size:{schrift.pt(schrift.STUFE_BASE)}pt;"
    "text-align:left;"
    "border-radius:0 0 4px 4px;"
    "border:1px solid;}"
)

# Such-/Eingabezeile
STY_SEARCH_LINE: str = (
    "QLineEdit{ "
    "border:1px solid ; border-radius:3px; padding:3px;}"
)

# Versions-Stempel
def STY_VERSION_LABEL() -> str:
    return f" font-size:{schrift.pt(schrift.STUFE_SM)}pt; padding-top:4px;"

# Hilfe-Abschnitts-Button (akzentfarbig, Werte werden via f-string eingesetzt)
_STY_ABSCHNITT_BTN_TMPL: str = (
    "QPushButton{{text-align:left; padding:5px 8px;"
    "font-family:'{ui_family}','Noto Color Emoji';"
    f"font-size:{schrift.pt(schrift.STUFE_LG)}pt; font-weight:bold;"
    "border:none; border-radius:4px;"
    "}}"
    "QPushButton:hover{{ }}"
    "QPushButton:pressed{{}}"
)


def abschnitt_btn_style(fg: str, bg: str) -> str:
    """Gibt das Stylesheet für einen Hilfe-Abschnitts-Button zurück."""
    return _STY_ABSCHNITT_BTN_TMPL.format(
        ui_family=_FONT_UI_FAMILY,
        fg=fg,
        bg=bg,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STABILISIERUNGS-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════════

def apply_global_font(widget: QtWidgets.QWidget) -> None:
    """
    Setzt die UI-Schrift auf das Widget und aktiviert Emoji-sicheren Font.
    Im Konstruktor einer UI-Klasse als erstes aufrufen.
    """
    widget.setFont(ui_font())


def stabilize_label(label: QtWidgets.QLabel) -> None:
    """
    Verhindert Blocksatz, Zerhacken und vertikales Auseinanderreißen bei QLabel.
    Setzt Schrift, Ausrichtung, Zeilenumbruch und SizePolicy explizit.
    """
    label.setFont(ui_font())
    label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    label.setWordWrap(True)
    label.setSizePolicy(
        QtWidgets.QSizePolicy.Preferred,
        QtWidgets.QSizePolicy.Preferred,
    )


def stabilize_text_editor(editor: QtWidgets.QPlainTextEdit) -> None:
    """
    Macht einen QPlainTextEdit bombensicher gegen Qt-Blocksatz und Auseinanderreißen.

    Aufrufen NACHDEM setPlainText() gesetzt wurde, damit die Block-Format-
    Erzwingung auf dem gesamten Dokumentinhalt wirkt.

    Konfiguriert:
      • Monospace-Schrift (Emoji-sicher)
      • Text-Option: linksbündig, WordWrap
      • Block-Format aller Blöcke: AlignLeft (Sicherheitsnetz)
      • LineWrapMode: NoWrap (horizontales Scrollen statt Umbruch)
      • FrameShape: NoFrame
      • Scroll-Bars: vertikal aus, horizontal nach Bedarf
      • SizePolicy: Expanding × Fixed
    """
    editor.setFont(mono_font())

    # ── Linksbündig auf Dokument-Ebene ────────────────────────────────────
    _txt_opt = editor.document().defaultTextOption()
    _txt_opt.setAlignment(QtCore.Qt.AlignLeft)
    _txt_opt.setWrapMode(QtGui.QTextOption.WordWrap)
    editor.document().setDefaultTextOption(_txt_opt)

    # ── Erzwinge AlignLeft in jedem Block (Sicherheitsnetz) ──────────────
    _bfmt = QtGui.QTextBlockFormat()
    _bfmt.setAlignment(QtCore.Qt.AlignLeft)
    _cur = editor.textCursor()
    _cur.select(QtGui.QTextCursor.Document)
    _cur.mergeBlockFormat(_bfmt)
    _cur.clearSelection()
    editor.setTextCursor(_cur)

    # ── Widget-Konfiguration ──────────────────────────────────────────────
    editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
    editor.setFrameShape(QtWidgets.QFrame.NoFrame)
    editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    editor.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
    editor.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding,
        QtWidgets.QSizePolicy.Fixed,
    )
def calc_plain_text_height(
    font: QtGui.QFont,
    text: str,
    doc_margin: int = 8,
) -> int:
    """
    Berechnet die pixelgenaue Fixed-Höhe für einen QPlainTextEdit mit
    dem gegebenen Font und Inhalt (Zeilenanzahl × lineSpacing + Ränder).
    """
    fm = QtGui.QFontMetrics(font)
    n_zeilen = text.count("\n") + 1
    return fm.lineSpacing() * n_zeilen + doc_margin * 2 + 4


# ── Strukturelle Hintergrundfarben (Container / ScrollArea) ──────────────────
STY_SCROLL_AREA_BG: str = "QScrollArea{}"
STY_CONTAINER_BG:   str = ""

# ── Semantische Eingabefeld-Hintergründe ─────────────────────────────────────
# Feste Hue-Werte behalten die ursprünglichen Farb-Charakter:
#   Grün (130°) für das Eingabe-/Suchfeld
#   Blau (220°) für KI-Antwort und Kontext
# Sättigung und Helligkeit werden aus QPalette.Base berechnet, damit der Tint
# im Hell- und Dunkel-Modus gleich gut sichtbar und nie stumpf wirkt.

_HUE_SUCHE   = 130   # Grün
_HUE_KI      = 220   # Blau
_HUE_KONTEXT = 220   # Blau


def _semantik_tint_hex(widget: "QtWidgets.QWidget", hue: int) -> str:
    """
    Erzeugt einen sichtbaren, nicht-stumpfen Tint mit dem angegebenen Farbton.
    Helligkeit und Sättigung werden aus QPalette.Base berechnet:
      Dunkel-Modus: kräftiger Tint auf dunklem Grund
      Hell-Modus:   pastelliger aber sichtbarer Tint auf hellem Grund
    Kein einziger Hex-Wert hartkodiert.
    """
    base   = widget.palette().color(QtGui.QPalette.Base)
    dunkel = base.lightness() < 128

    if dunkel:
        # Auf dunklem Grund: mittlere Sättigung, etwas heller als Hintergrund
        tint = QtGui.QColor.fromHsl(hue, 160, min(255, base.lightness() + 55))
        alpha = 0.25
    else:
        # Auf hellem Grund: hohe Sättigung, helle Farbe → klares Pastell
        tint = QtGui.QColor.fromHsl(hue, 200, 185)
        alpha = 0.35

    nr = int(base.red()   * (1 - alpha) + tint.red()   * alpha)
    ng = int(base.green() * (1 - alpha) + tint.green() * alpha)
    nb = int(base.blue()  * (1 - alpha) + tint.blue()  * alpha)
    return f"#{nr:02x}{ng:02x}{nb:02x}"


def _apply_semantik_tint(widget: "QtWidgets.QWidget", hue: int) -> None:
    """Schreibt den semantischen Tint als background-color ins StyleSheet."""
    def _do():
        col = _semantik_tint_hex(widget, hue)
        cls = type(widget).__name__
        if cls in ("QPlainTextEdit", "LinksTextEdit", "SnipCommandEdit", "CodeEditor"):
            sel = "QPlainTextEdit"
        elif cls == "QLabel":
            sel = "QLabel"
        elif cls == "QLineEdit":
            sel = "QLineEdit"
        else:
            sel = "QPlainTextEdit"
        snippet = f"{sel} {{ background-color: {col}; }}"
        existing = widget.styleSheet()
        widget.setStyleSheet((existing + "\n" + snippet) if existing else snippet)
    QtCore.QTimer.singleShot(50, _do)


def apply_input_bg_suche(widget: "QtWidgets.QWidget") -> None:
    """Grüner Tint für das Such-/Eingabefeld – im Hell- und Dunkelmode sichtbar."""
    _apply_semantik_tint(widget, _HUE_SUCHE)


def apply_input_bg_ki(widget: "QtWidgets.QWidget") -> None:
    """Blauer Tint für KI-Antwort-Felder."""
    _apply_semantik_tint(widget, _HUE_KI)


def apply_input_bg_kontext(widget: "QtWidgets.QWidget") -> None:
    """Blauer Tint für Kontext-Felder."""
    _apply_semantik_tint(widget, _HUE_KONTEXT)



# ═══════════════════════════════════════════════════════════════════════════════
# KLAPPSEKTION-LEISTE  –  Farben zur Laufzeit aus der echten System-Palette.
# Kein 'palette(...)' im QSS-String: das wird unter FreeCADs globalem
# Stylesheet (AppImage) falsch aufgelöst und wirkt dann wie hartkodiert hell.
# Look angelehnt an die Buttons der rechten Aktionen-Leiste:
# abgerundet, dezenter Rand, mittlerer Grauton — kein Trennstrich,
# kein tiefschwarzer Button-Hintergrund.
# ═══════════════════════════════════════════════════════════════════════════════

def _misch_hex(widget: "QtWidgets.QWidget", faktor: float) -> str:
    """
    Mischt die Fenster-Hintergrundfarbe um `faktor` (0…1) in Richtung
    Textfarbe. Ergibt in dunklen Paletten ein helleres Grau, in hellen
    ein dunkleres — immer dezent, nie weiß, nie tiefschwarz.
    """
    pal = widget.palette()
    bg = pal.color(QtGui.QPalette.Window)
    fg = pal.color(QtGui.QPalette.WindowText)
    nr = int(bg.red()   * (1 - faktor) + fg.red()   * faktor)
    ng = int(bg.green() * (1 - faktor) + fg.green() * faktor)
    nb = int(bg.blue()  * (1 - faktor) + fg.blue()  * faktor)
    return f"#{nr:02x}{ng:02x}{nb:02x}"


def apply_klappsektion_style(btn: "QtWidgets.QPushButton") -> None:
    btn.setStyleSheet(STY_TAB_BTN())


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS-FARBEN  –  hier zentral, nie im Widget-Code.
# Werden abhängig von der hell/dunkel-Palette des Widgets gewählt.
# ═══════════════════════════════════════════════════════════════════════════════

def _ist_dunkel(widget: "QtWidgets.QWidget") -> bool:
    """True, wenn die System-Palette des Widgets dunkel ist."""
    return widget.palette().color(QtGui.QPalette.Window).lightness() < 128


def farbe_ok(widget: "QtWidgets.QWidget") -> str:
    """Erfolgs-Grün aus der Palette abgeleitet – kein Hex hartkodiert."""
    base = widget.palette().color(QtGui.QPalette.Base)
    dunkel = base.lightness() < 128
    # Grün-Ton: Helligkeit an Hintergrund anpassen
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
    basis = f"font-size:{schrift.pt(schrift.STUFE_BASE)}pt; padding:4px;"
    if art == "ok":
        return basis + f" color:{farbe_ok(widget)};"
    if art == "fehler":
        return basis + f" color:{farbe_fehler(widget)};"
    return basis


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTAX-HIGHLIGHT-FARBEN
# Zwei feste Farbthemen: DUNKEL (Originalfarben des Benutzers) + HELL.
# Syntax-Farben sind bewusste Designentscheidungen wie in VS Code oder Sublime –
# sie gehören zum Syntax-Theme, nicht zu den adaptiven UI-Farben.
# ═══════════════════════════════════════════════════════════════════════════════

def _c(hex6: str) -> "QtGui.QColor":
    return QtGui.QColor(hex6)


_DUNKEL_FARBEN = {
    "keyword":    _c("#4FC1E9"),   # hellblau  – def, class, if, return …
    "builtin":    _c("#56B6C2"),   # cyan      – print, len, range …
    "self":       _c("#E06C75"),   # rot       – self, cls
    "decorator":  _c("#C678DD"),   # lila      – @decorator
    "def_name":   _c("#61AFEF"),   # blau      – Funktionsname
    "class_name": _c("#E5C07B"),   # gold      – Klassenname
    "zahl":       _c("#98C379"),   # grün      – 42, 3.14
    "string":     _c("#D19A66"),   # orange    – "text"
    "operator":   _c("#ABB2BF"),   # hellgrau  – + - * /
    "kommentar":  _c("#6A9955"),   # graugrün  – # Kommentar
    "fstring":    _c("#D19A66"),
    "triple":     _c("#D19A66"),
}
_DUNKEL_TEXT = _c("#D4D4D4")

_HELL_FARBEN = {
    "keyword":    _c("#0000CC"),   # dunkelblau
    "builtin":    _c("#007080"),   # teal
    "self":       _c("#A31515"),   # dunkelrot
    "decorator":  _c("#795E26"),   # braun
    "def_name":   _c("#001080"),   # navy
    "class_name": _c("#267F99"),   # blaugrün
    "zahl":       _c("#098658"),   # grün
    "string":     _c("#A31515"),   # dunkelrot
    "operator":   _c("#383838"),   # dunkelgrau
    "kommentar":  _c("#3A7212"),   # olivgrün
    "fstring":    _c("#A31515"),
    "triple":     _c("#A31515"),
}
_HELL_TEXT = _c("#1E1E1E")


def syntax_farben() -> "tuple[dict[str, QtGui.QColor], QtGui.QColor]":
    """Gibt (farb_dict, text_farbe) passend zum aktuellen Theme zurück."""
    from qt_compat import QtWidgets, QtGui as _QtGui
    app = QtWidgets.QApplication.instance()
    pal = app.palette() if app else _QtGui.QPalette()
    dunkel = pal.color(_QtGui.QPalette.Base).lightness() < 128
    if dunkel:
        return _DUNKEL_FARBEN, _DUNKEL_TEXT
    return _HELL_FARBEN, _HELL_TEXT


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

# ── Tab-Leisten-Stylesheet  (links & rechts identisch) ───────────────────────
STY_TABBAR: str = (
    "QTabWidget::pane{border:none;}"
    f"QTabBar::tab{{padding:4px 6px;font-size:{schrift.pt(schrift.STUFE_BASE)}pt;min-width:0px;"
    f"font-family:'{_FONT_UI_FAMILY}','Noto Color Emoji','Segoe UI Emoji','Apple Color Emoji';}}"
    "QTabBar::tab:selected{border-bottom:2px solid ;}"
    "QTabBar::scroller{width:16px;}"
    "QTabBar QToolButton{border:none;}"
    "QTabBar QToolButton:hover{}"
)

def STY_TAB_BTN() -> str:
    size = schrift.pt(schrift.STUFE_BASE)
    return (
        f"QPushButton {{ padding: 4px 6px; font-size: {size}pt; min-width: 0px; "
        f"font-family: '{_FONT_UI_FAMILY}', 'Noto Color Emoji', 'Segoe UI Emoji', 'Apple Color Emoji'; "
        f"border: none; border-bottom: 2px solid transparent; border-radius: 0; }}"
        f"QPushButton:hover {{ border-bottom: 2px solid palette(mid); }}"
        f"QPushButton:checked {{ border-bottom: 2px solid palette(mid); font-weight: bold; }}"
    )