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
    "hilfe_version_label":     "FreeCAD MultiAI Panel  •  v1.1",
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
    "border:1px solid palette(shadow);}"
)

STY_HILFE_BODY: str = (
    "QLabel{"
    f"font-family:'{_FONT_MONO_FAMILY}', monospace; font-size:{schrift.pt(schrift.STUFE_BASE)}pt;"
    "padding:6px 8px;"
    "border-radius:0 0 4px 4px;"
    "border:1px solid palette(shadow);}"
)

# Such-/Eingabezeile
STY_SEARCH_LINE: str = (
    "QLineEdit{ "
    "border:1px solid palette(shadow); border-radius:3px; padding:3px;}"
)

# Versions-Stempel
def STY_VERSION_LABEL() -> str:
    return f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt; padding-top:4px; }}"

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


# ── Farbschema: explizit gesetzt, kein Palette-Raten ─────────────────────────
_FARBSCHEMA_DUNKEL: bool = True  # Standard Dunkelmod; wird beim Start aus Prefs geladen

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
    basis = f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_BASE)}pt; padding:4px;"
    if art == "ok":
        return basis + f" color:{farbe_ok(widget)}; }}"
    if art == "fehler":
        return basis + f" color:{farbe_fehler(widget)}; }}"
    return basis + " }"


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTAX-HIGHLIGHT-FARBEN  –  kommen aus farben.py (DUNKEL / HELL)
# ═══════════════════════════════════════════════════════════════════════════════

import farben as _farben_mod


def _c(hex6: str) -> "QtGui.QColor":
    return QtGui.QColor(hex6)


def syntax_farben() -> "tuple[dict[str, QtGui.QColor], QtGui.QColor]":
    """Gibt (farb_dict, text_farbe) passend zum gewählten Farbschema zurück."""
    f = _farben_mod.DUNKEL if _FARBSCHEMA_DUNKEL else _farben_mod.HELL
    farb_dict = {k: _c(v) for k, v in f.items() if k not in ("text", "tint_suche", "tint_ki", "tint_kontext")}
    text_farbe = _c(f["text"])
    return farb_dict, text_farbe


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
    "QTabBar::tab:selected{border-bottom:2px solid palette(highlight);}"
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


# ═══════════════════════════════════════════════════════════════════════════════
# NEU: ZENTRALISIERTE STYLESHEETS (Refactoring)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Globale Schrift für das Hauptfenster ─────────────────────────────────────
def STY_HAUPTFENSTER_FONT() -> str:
    """Globaler Font-Stylesheet für MakroEditor (ohne *-Selektor)."""
    return (
        "QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,"
        "QDoubleSpinBox, QSpinBox, QTabBar::tab, QToolTip,"
        "QGroupBox, QRadioButton, QMenu, QMenuBar {"
        "  font-family: 'Ubuntu', 'Noto Color Emoji'; }"
        "QListWidget, QListView, QTreeWidget, QTreeView {"
        "  font-family: 'Ubuntu', 'Noto Color Emoji'; }"
        "QListWidget::item, QListView::item { text-align: left; }"
        "QPlainTextEdit, QTextEdit {"
        "  font-family: 'Courier New', monospace; }"
        "_BlauBanner { background-color: palette(highlight); }"
    )


# ── Editor-Tab-Widget ─────────────────────────────────────────────────────────
def STY_EDITOR_TABS(fs: int) -> str:
    """Stylesheet für das Datei-Tab-Widget im Editor (QTabWidget)."""
    return (
        "QTabWidget::pane{ border:none; }"
        "QTabBar::tab{ padding:5px 14px;"
        f" font-size:{fs}pt;"
        " border:none; border-right:1px solid palette(shadow); min-width:60px; max-width:200px;}"
        "QTabBar::tab:selected{ border-bottom:2px solid palette(highlight);}"
        "QTabBar::tab:hover{}"
    )


# ── Status-Label ──────────────────────────────────────────────────────────────
def STY_STATUS_LABEL(fs: int) -> str:
    """Stylesheet für das Status-Label in der Statusleiste."""
    return f"QLabel, QCheckBox {{ font-size:{fs}pt; }}"


# ── Abschnitts-Label (klein, mit Untertrennstrich) ───────────────────────────
def STY_ABSCHNITT_LABEL(fs: int) -> str:
    """Stylesheet für Abschnitts-Label (kleine Schrift, Unterstrich)."""
    return (
        f"QLabel {{ font-size:{fs}pt; font-weight:bold;"
        f" padding-top:6px; padding-bottom:2px; border-bottom:1px solid palette(shadow); }}"
    )


# ── Abschnitts-Label (größer, für Barrierefreiheit) ──────────────────────────
def STY_ABSCHNITT_LABEL_LG(fs: int) -> str:
    """Stylesheet für größere Abschnitts-Label (Barrierefreiheit)."""
    return (
        f"QLabel {{ font-weight:bold; font-size:{fs}pt;"
        f" border-bottom:1px solid palette(shadow); padding-bottom:2px; margin-top:6px; }}"
    )


# ── Panel-Toggle-Buttons (Toolbar) ───────────────────────────────────────────
def STY_PANEL_BTN(fs: int) -> str:
    """Stylesheet für Panel-Toggle-Buttons in der Toolbar."""
    return (
        f"QPushButton {{ border:none; border-radius:3px; padding:2px 4px;"
        f" font-size:{fs}pt; }}"
        f"QPushButton:checked {{ font-weight:bold;"
        f" border:1px solid palette(shadow); }}"
        f"QPushButton:hover {{ border:1px solid palette(shadow); }}"
    )


# ── Mini-Tab-Buttons (kombiniertes Dock) ─────────────────────────────────────
def STY_MINI_TAB_BTN(fs: int) -> str:
    """Stylesheet für Mini-Tab-Buttons im kombinierten Dock."""
    return (
        f"QPushButton {{ border:none; border-radius:3px; padding:2px 6px;"
        f" font-size:{fs}pt; }}"
        f"QPushButton:checked {{ font-weight:bold;"
        f" border:1px solid palette(shadow); }}"
        f"QPushButton:hover {{ border:1px solid palette(shadow); }}"
    )


# ── Icon-Button ohne Rahmen (Emoji-Button) ───────────────────────────────────
def STY_ICON_BTN_BORDERLESS(fs: int) -> str:
    """Stylesheet für einen randlosen Icon/Emoji-Button."""
    return f"QPushButton{{border:none;font-size:{fs}pt;}}"


# ── KI-Input-Feld (QPlainTextEdit mit Rahmen + Fokus-Highlight) ──────────────
def STY_KI_INPUT_FIELD() -> str:
    """Stylesheet für das KI-Eingabefeld (Suchfeld / find_area)."""
    return (
        "QPlainTextEdit{font-family:'Courier New',monospace;"
        "border:1px solid palette(shadow); border-radius:3px;}"
        "QPlainTextEdit:focus{border:1px solid palette(highlight);}"
    )


# ── KI-Ausgabe-Feld ──────────────────────────────────────────────────────────
def STY_KI_OUTPUT_FIELD() -> str:
    """Stylesheet für das KI-Antwort-Feld."""
    return (
        "QPlainTextEdit{font-family:'Courier New',monospace;"
        " border:1px solid palette(shadow);}"
    )


# ── Editor-Instanz (QPlainTextEdit, Code-Farbe aus theme) ────────────────────
def STY_CODE_EDITOR() -> str:
    """Stylesheet für den Code-Editor (JediEditor). Farbe aus farben.py."""
    f = _farben_mod.DUNKEL if _FARBSCHEMA_DUNKEL else _farben_mod.HELL
    return (
        f"QPlainTextEdit{{"
        f"font-family:'Courier New',monospace;"
        f"color:{f['text']};"
        f"}}"
    )


# ── Toolbar ───────────────────────────────────────────────────────────────────
STY_TOOLBAR: str = "QToolBar { border: none; spacing: 2px; padding: 2px 4px; }"


# ── WerkzeugLeiste-Widget (Schriftfamilien-Reset) ─────────────────────────────
STY_WERKZEUG_LEISTE: str = (
    "#WerkzeugLeiste QLabel, #WerkzeugLeiste QPushButton,"
    "#WerkzeugLeiste QLineEdit, #WerkzeugLeiste QComboBox,"
    "#WerkzeugLeiste QCheckBox, #WerkzeugLeiste QDoubleSpinBox,"
    "#WerkzeugLeiste QSpinBox, #WerkzeugLeiste QTabBar::tab,"
    "#WerkzeugLeiste QGroupBox, #WerkzeugLeiste QRadioButton {"
    "  font-family: 'Ubuntu'; }"
    "#WerkzeugLeiste QPlainTextEdit, #WerkzeugLeiste QTextEdit {"
    "  font-family: 'Courier New', monospace; }"
)


# ── HilfeTab-Widget ───────────────────────────────────────────────────────────
STY_HILFE_TAB: str = (
    "#HilfeTab QLabel, #HilfeTab QPushButton,"
    "#HilfeTab QLineEdit, #HilfeTab QScrollArea {"
    "  font-family: 'Ubuntu'; }"
    "#HilfeTab QPlainTextEdit {"
    "  font-family: 'Courier New', monospace; }"
)


# ── Button mit Rahmen (Standard) ──────────────────────────────────────────────
def STY_BTN_BORDER(fs: int) -> str:
    """Einfacher Button mit palette(shadow)-Rahmen."""
    return (
        f"QPushButton{{border:1px solid palette(shadow);border-radius:3px;"
        f"font-size:{fs}pt;}}"
        "QPushButton:hover{}"
        "QPushButton:pressed{}"
    )


# ── Button mit Rahmen + Fettschrift ──────────────────────────────────────────
def STY_BTN_BORDER_BOLD(fs: int) -> str:
    """Button mit palette(shadow)-Rahmen und fetter Schrift."""
    return (
        f"QPushButton{{border:1px solid palette(shadow);"
        f"border-radius:4px;font-size:{fs}pt;font-weight:bold;}}"
        "QPushButton:hover{}"
        "QPushButton:pressed{}"
    )


# ── Primär-Button (Begrüssung) ────────────────────────────────────────────────
def STY_PRIMARY_BTN(fs: int) -> str:
    """Primär-Button ohne Rahmen, fett (Begrüssungs-Dialog)."""
    return (
        f"QPushButton {{   border:none;"
        f" border-radius:6px; font-weight:bold; font-size:{fs}pt; padding:6px 20px; }}"
        "QPushButton:hover {}"
        "QPushButton:pressed {}"
    )


# ── Sekundär-Button (Begrüssung) ──────────────────────────────────────────────
def STY_SECONDARY_BTN(fs: int) -> str:
    """Sekundär-Button mit Rahmen (Begrüssungs-Dialog)."""
    return (
        f"QPushButton {{   border:1px solid palette(shadow);"
        f" border-radius:6px; font-size:{fs}pt; padding:5px 14px; }}"
        "QPushButton:hover {}"
    )


# ── Begrüssungs-Dialog (QLineEdit) ───────────────────────────────────────────
def STY_BEGRUESSUNG_DIALOG(fs: int) -> str:
    """Stylesheet für den Begrüssungs-Dialog."""
    return (
        "QDialog {}"
        "QWidget {}"
        "QLabel  {}"
        "QFrame  {}"
        f"QLineEdit {{   border:1px solid palette(shadow);"
        f"            border-radius:5px; padding:6px 10px; font-size:{fs}pt;"
        "            font-family:'Courier New', monospace; }"
        "QLineEdit:focus {}"
    )


# ── Begrüssungs-Warnung-Box ───────────────────────────────────────────────────
def STY_WARN_BOX(fs: int) -> str:
    """Stylesheet für eine Warn-Box mit Rahmen und Rundung."""
    return (
        f"QLabel {{ font-size:{fs}pt;"
        f" border:1px solid palette(shadow); border-radius:5px; padding:8px; }}"
    )


# ── Tipp-Box ──────────────────────────────────────────────────────────────────
def STY_TIPP_BOX(fs: int) -> str:
    """Stylesheet für eine Tipp-Box mit Rahmen und Rundung."""
    return (
        f"QLabel {{ font-size:{fs}pt;"
        f" border:1px solid palette(shadow); border-radius:5px; padding:10px; }}"
    )


# ── Datei-Browser: Eingabefeld ───────────────────────────────────────────────
def STY_DB_PFAD_FELD(fs: int) -> str:
    """Stylesheet für das Pfad-Eingabefeld im Datei-Browser."""
    return (
        "QLineEdit{"
        f"border:1px solid palette(shadow);border-radius:3px;"
        f"padding:2px 4px;font-size:{fs}pt;}}"
    )


# ── Datei-Browser: Filter-Feld ───────────────────────────────────────────────
def STY_DB_FILTER_FELD(fs: int) -> str:
    """Stylesheet für das Filter-Eingabefeld im Datei-Browser."""
    return (
        "QLineEdit{"
        f"border:1px solid palette(shadow);border-radius:3px;"
        f"padding:2px 4px;font-size:{fs}pt;}}"
    )


# ── Datei-Browser: Checkbox ───────────────────────────────────────────────────
def STY_DB_CHECKBOX(fs: int) -> str:
    """Stylesheet für die .py-Filter-Checkbox im Datei-Browser."""
    return (
        f"QCheckBox{{font-size:{fs}pt;}}"
        "QCheckBox::indicator{width:12px;height:12px;}"
    )


# ── Datei-Browser: Neue-Datei-Button ─────────────────────────────────────────
def STY_DB_NEU_BTN(fs: int) -> str:
    """Stylesheet für den 'Neue Datei'-Button im Datei-Browser."""
    return (
        f"QPushButton{{border:1px solid palette(shadow);border-radius:3px;"
        f"font-size:{fs}pt;"
        "font-weight:bold;padding:3px 6px;}"
        "QPushButton:hover{}"
        "QPushButton:pressed{}"
    )


# ── Datei-Browser: Lesezeichen-ComboBox ──────────────────────────────────────
def STY_DB_LZ_COMBO(fs: int) -> str:
    """Stylesheet für die Lesezeichen-ComboBox im Datei-Browser."""
    return (
        "QComboBox{"
        f"border:1px solid palette(shadow);border-radius:3px;"
        f"padding:1px 4px;font-size:{fs}pt;}}"
    )


# ── Datei-Browser: Lesezeichen-Buttons ───────────────────────────────────────
def STY_DB_LZ_BTN(fs: int) -> str:
    """Stylesheet für Lesezeichen-Buttons (★ / ✕) im Datei-Browser."""
    return (
        f"QPushButton{{border:1px solid palette(shadow);border-radius:3px;"
        f"font-size:{fs}pt;}}"
        "QPushButton:hover{}"
    )


# ── Datei-Browser: Tree-View ─────────────────────────────────────────────────
def STY_DB_TREE(fs: int) -> str:
    """Stylesheet für den Datei-Tree im Datei-Browser."""
    return (
        "QTreeView{"
        f"border:1px solid palette(shadow);border-radius:3px;font-size:{fs}pt;}}"
        "QTreeView::item:selected{}"
        "QTreeView::item:hover{}"
        "QTreeView::branch:has-children:!has-siblings:closed,"
        "QTreeView::branch:closed:has-children:has-siblings{"
        "border-image:none; image:none;}"
    )


# ── Datei-Browser: Status-Label ──────────────────────────────────────────────
def STY_DB_STATUS(fs: int) -> str:
    """Stylesheet für das Status-Label im Datei-Browser."""
    return f"QLabel {{ font-size:{fs}pt; padding:1px 3px; }}"


# ── Snippet-Liste ─────────────────────────────────────────────────────────────
def STY_SNIPPET_LISTE(fs: int) -> str:
    """Stylesheet für die Snippet-Liste."""
    return (
        f"QListWidget{{border:1px solid palette(shadow);"
        f" font-size:{fs}pt;}}"
        "QListWidget::item{padding:4px 5px;}"
        "QListWidget::item:selected{}"
        "QListWidget::item:alternate{}"
    )


# ── Snippet-Vorschau ──────────────────────────────────────────────────────────
STY_SNIPPET_VORSCHAU: str = (
    "QTextEdit{"
    "border:1px solid palette(shadow); font-family:'Courier New',monospace;}"
)


# ── Hints-Liste ──────────────────────────────────────────────────────────────
STY_HINTS_LISTE: str = (
    "QListWidget{"
    "font-family:'Courier New',monospace;"
    "border:1px solid palette(shadow);}"
    "QListWidget::item{padding:2px 5px; text-align:left;}"
    "QListWidget::item:selected{}"
    "QListWidget::item:alternate{}"
)


# ── Hints-Beschreibung ────────────────────────────────────────────────────────
def STY_HINTS_DESC(fs: int) -> str:
    """Stylesheet für das Hint-Beschreibungs-Label."""
    return (
        "QLabel{"
        f"border:1px solid palette(shadow);padding:5px;"
        f"border-radius:3px;font-size:{fs}pt;min-height:32px;}}"
    )


# ── Fehler-Tab: Eingabe/Ausgabe-Feld ─────────────────────────────────────────
STY_FEHLER_TAB_FELD: str = (
    "QPlainTextEdit{"
    "font-family:'Courier New',monospace;"
    "border:1px solid palette(shadow);border-radius:3px;}"
)


# ── Snippet-Popup (Autocomplete) ──────────────────────────────────────────────
def STY_SNIP_POPUP(fs: int) -> str:
    """Stylesheet für das Snippet-Autocomplete-Popup."""
    return (
        "QListWidget{"
        "   "
        "  border:1px solid palette(shadow); border-bottom-left-radius:4px;"
        "  border-bottom-right-radius:4px;"
        f"  font-size:{fs}pt; padding:2px;}}"
        "QListWidget::item{ padding:4px 8px; }"
        "QListWidget::item:selected{}"
        "QListWidget::item:hover{}"
        "QListWidget::item[disabled='true']{  font-style:italic; }"
    )


# ── Snippet-Popup-Header ──────────────────────────────────────────────────────
def STY_SNIP_POPUP_HEADER(fs: int) -> str:
    """Stylesheet für den Header des Snippet-Autocomplete-Popups."""
    return (
        f"QLabel{{   font-size:{fs}pt;"
        " font-weight:bold; padding:2px 8px;"
        " border-top-left-radius:4px; border-top-right-radius:4px; }"
    )


# ── Info-Banner-Button (_BlauBanner) ─────────────────────────────────────────
def STY_BANNER_BTN(fs: int) -> str:
    """Stylesheet für den Button im Info-Banner."""
    return (
        "#_bannerBtn{text-align:left; padding:4px 8px; border:none;"
        f" font-size:{fs}pt; font-weight:bold;"
        " background:transparent; color:palette(highlighted-text);}"
        "#_bannerBtn:hover{background:transparent;}"
    )


# ── Info-Banner-Body ──────────────────────────────────────────────────────────
STY_BANNER_BODY: str = (
    "#_bannerBody{ font-size:9pt; padding:4px 8px 8px 8px;"
    " border:none; background:transparent;"
    " color:palette(highlighted-text); }"
)


# ── Vorschau-Tab: Titel-Label ─────────────────────────────────────────────────
def STY_VORSCHAU_TITEL(fs: int) -> str:
    """Stylesheet für das Titel-Label im Vorschau-Tab."""
    return f"QLabel {{ font-weight:bold; font-size:{fs}pt; }}"


# ── Vorschau-Tab: Schließen-Button ────────────────────────────────────────────
def STY_VORSCHAU_CLOSE_BTN(fs: int) -> str:
    """Stylesheet für den Schließen-Button im Vorschau-Tab."""
    return (
        f"QPushButton{{border:1px solid palette(shadow);"
        f"border-radius:3px;font-size:{fs}pt;padding:0 8px;}}"
        "QPushButton:hover{}"
    )


# ── Vorschau-Tab: Status-Label ────────────────────────────────────────────────
def STY_VORSCHAU_STATUS(fs: int) -> str:
    """Stylesheet für das Status-Label im Vorschau-Tab."""
    return f"QLabel {{ font-size:{fs}pt; }}"


# ── Vorschau-Tab: Container ────────────────────────────────────────────────────
STY_VORSCHAU_CONTAINER: str = (
    "#VorschauContainer { border:1px solid palette(shadow); border-radius:3px; }"
)


# ── Vorschau-Tab: Platzhalter-Label ──────────────────────────────────────────
STY_VORSCHAU_PLACEHOLDER: str = "QLabel { border:none; }"


# ── Vorschau-Tab: Log-Label ───────────────────────────────────────────────────
def STY_VORSCHAU_LOG_LABEL(fs: int) -> str:
    """Stylesheet für das Ausgabe-Label im Vorschau-Tab."""
    return f"QLabel {{ font-size:{fs}pt; font-weight:bold; letter-spacing:1px; }}"


# ── Vorschau-Tab: Log-Box ─────────────────────────────────────────────────────
STY_VORSCHAU_LOG_BOX: str = (
    "QPlainTextEdit{"
    "font-family:'Courier New',monospace;"
    "border:1px solid palette(shadow);border-radius:3px;}"
)


# ── Vorschau-Tab: Warn-Label ──────────────────────────────────────────────────
def STY_VORSCHAU_WARN(fs: int) -> str:
    """Stylesheet für das Warn-Label im Vorschau-Tab."""
    return f"QLabel {{ font-size:{fs}pt; padding:1px 0; }}"


# ── Werkzeuge: Statuszeile ────────────────────────────────────────────────────
def STY_WERKZEUG_STATUS(fs: int) -> str:
    """Stylesheet für die Statuszeile in der WerkzeugLeiste."""
    return (
        f"QLabel {{ font-size:{fs}pt; padding:2px 4px;"
        f" border-top:1px solid palette(shadow); }}"
    )


# ── Werkzeuge: Zeile-Edit ─────────────────────────────────────────────────────
def STY_ZEILE_EDIT(fs: int) -> str:
    """Stylesheet für das Zeilen-Eingabefeld in der WerkzeugLeiste."""
    return (
        f"QLineEdit{{ font-size:{fs}pt;"
        f"border:1px solid palette(shadow);padding:3px 5px;border-radius:2px;}}"
    )


# ── Werkzeuge: Code-Baum ──────────────────────────────────────────────────────
def STY_CODE_BAUM(fs: int) -> str:
    """Stylesheet für den Code-Baum in der WerkzeugLeiste."""
    return (
        f"QTreeWidget{{font-size:{fs}pt;"
        "border:1px solid palette(shadow);border-radius:2px;"
        "font-family:'Ubuntu','Noto Color Emoji';}"
        "QTreeWidget::item{padding:2px 2px;}"
        "QTreeWidget::item:selected{}"
        "QTreeWidget::item:hover{}"
        "QTreeWidget::branch:has-children:!has-siblings:closed,"
        "QTreeWidget::branch:closed:has-children:has-siblings{"
        "  border-image:none; image:none;}"
    )


# ── Werkzeuge: Code-Statistiken Info-Label ────────────────────────────────────
def STY_CODE_STATISTIKEN_LBL(fs: int) -> str:
    """Stylesheet für das Info-Label der Code-Statistiken."""
    return (
        f"QLabel {{ border:1px solid palette(shadow);"
        f" padding:6px; font-size:{fs}pt; border-radius:2px;"
        f" font-family:'Ubuntu','Noto Color Emoji'; }}"
    )


# ── Werkzeuge: Syntax-Check-Label ─────────────────────────────────────────────
def STY_SYNTAX_CHECK_LBL(fs: int) -> str:
    """Stylesheet für das Syntax-Check-Label in der WerkzeugLeiste."""
    return (
        f"QLabel {{ padding:6px; border-radius:3px; font-size:{fs}pt;"
        f" font-family:'Ubuntu','Noto Color Emoji'; }}"
    )


# ── Werkzeuge: Sektion-Label ──────────────────────────────────────────────────
def STY_WERKZEUG_SEKTION(fs: int) -> str:
    """Stylesheet für Abschnitts-Label (groß) in der WerkzeugLeiste."""
    return (
        f"QLabel {{ font-size:{fs}pt; font-weight:bold;"
        f" font-family:'Ubuntu','Noto Color Emoji';"
        f" padding-top:6px; padding-bottom:4px;"
        f" border-bottom:1px solid palette(shadow); }}"
    )


# ── Sidebar: Abschnitts-Kopf-Button ──────────────────────────────────────────
def STY_SECTION_HEAD_BTN(fs: int) -> str:
    """Stylesheet für Klapp-Abschnitts-Kopf-Buttons in der Sidebar."""
    return (
        f"QPushButton{{text-align:left;padding:4px 6px;"
        f"font-size:{fs}pt;font-weight:500;border:none;border-radius:4px;"
        "background:transparent;color:palette(text);}"
        "QPushButton:hover{background:palette(alternateBase);}"
    )


# ── Sidebar: Normale Aktions-Buttons ─────────────────────────────────────────
def STY_SECTION_BTN(fs: int) -> str:
    """Stylesheet für normale Aktions-Buttons innerhalb von Abschnitten."""
    return (
        f"QPushButton{{text-align:left;padding:3px 8px;font-size:{fs}pt;"
        "border:none;border-radius:4px;background:transparent;color:palette(text);}"
        "QPushButton:hover{background:palette(alternateBase);}"
        "QPushButton:pressed{background:palette(mid);}"
        "QPushButton:disabled{color:palette(mid);}"
    )


# ── Sidebar: Grid-Buttons (2-Spalten) ────────────────────────────────────────
def STY_GRID_BTN(fs: int) -> str:
    """Stylesheet für Grid-Buttons (2-Spalten) in der Sidebar."""
    return (
        f"QPushButton{{text-align:center;padding:2px 4px;font-size:{fs}pt;"
        "border:1px solid palette(mid);border-radius:4px;background:palette(button);color:palette(text);}"
        "QPushButton:hover{background:palette(alternateBase);}"
        "QPushButton:pressed{background:palette(mid);}"
        "QPushButton:disabled{color:palette(mid);}"
    )


# ── Sidebar: Rail-Icon-Buttons ────────────────────────────────────────────────
def STY_RAIL_BTN(fs: int) -> str:
    """Stylesheet für Rail-Icon-Buttons in der Sidebar."""
    return (
        f"QPushButton{{border:none;border-radius:5px;background:transparent;"
        f"font-size:{fs}pt;font-weight:bold;color:palette(buttonText);}}}}"
        f"QPushButton:hover{{background:palette(midlight);}}"
        f"QPushButton:checked{{background:palette(midlight);"
        f"border:1px solid palette(highlight);}}"
    )


# ── Sidebar: Code-Baum (kompakter) ───────────────────────────────────────────
def STY_NAV_BAUM_SIDEBAR(fs: int) -> str:
    """Stylesheet für den Code-Baum in der Sidebar."""
    return (
        f"QTreeWidget{{font-size:{fs}pt;border:1px solid palette(mid);border-radius:3px;}}"
        "QTreeWidget::item{padding:2px;}"
    )


# ── Sidebar: Statistiken Info-Label ──────────────────────────────────────────
def STY_STATISTIKEN_LBL_SIDEBAR(fs: int) -> str:
    """Stylesheet für das Statistiken-Label in der Sidebar."""
    return (
        f"QLabel {{ border:1px solid palette(mid); padding:5px;"
        f" font-size:{fs}pt; border-radius:3px; }}"
    )


# ── Sidebar: Syntax-Check-Label ───────────────────────────────────────────────
def STY_CHECK_LBL_SIDEBAR(fs: int) -> str:
    """Stylesheet für das Syntax-Check-Label in der Sidebar."""
    return f"QLabel {{ padding:5px; font-size:{fs}pt; border-radius:3px; }}"


# ── Sidebar: Status-Label ─────────────────────────────────────────────────────
def STY_SIDEBAR_STATUS(fs: int) -> str:
    """Stylesheet für das Status-Label in der Sidebar."""
    return (
        f"QLabel {{ font-size:{fs}pt; padding:2px 4px;"
        f" border-top:1px solid palette(mid); }}"
    )


# ── Jedi-Completer-Popup ──────────────────────────────────────────────────────
def STY_JEDI_POPUP(fs: int) -> str:
    """Stylesheet für das Jedi-Autocomplete-Popup."""
    return (
        "QListView {"
        "   "
        "  border:1px solid palette(shadow);"
        "  "
        f"  font-family:'Courier New', monospace; font-size:{fs}pt;"
        "}"
    )


# ── Barrierefreiheit: Hinweis-Label ──────────────────────────────────────────
def STY_BF_HINWEIS(fs: int) -> str:
    """Hinweis-Label im Barrierefreiheit-Panel."""
    return f"QLabel {{ color: palette(mid); font-style: italic; font-size:{fs}pt; }}"


# ── Hilfe-Tab: Suche-Feld ─────────────────────────────────────────────────────
STY_HILFE_SUCHE: str = (
    "QLineEdit{"
    "border:1px solid palette(shadow);border-radius:3px;padding:3px;}"
)


# ── Trennlinien ──────────────────────────────────────────────────────────────
STY_SEPARATOR: str = "QFrame { color:palette(mid); margin:2px 0; }"
STY_SEPARATOR_TIGHT: str = "QFrame { color:palette(mid); margin:0; }"

# ── Border-Reset (strukturell, keine Farbe) ───────────────────────────────────
STY_BORDER_NONE: str = "border:none;"


# ── Hochkontrast-Modus ────────────────────────────────────────────────────────
STY_HOCHKONTRAST: str = (
    "QWidget { color: #ffffff; background-color: #000000; }"
    "QPushButton { background: #222; border: 2px solid #fff; }"
    "QPlainTextEdit, QTextEdit { background: #000; color: #fff; }"
)


# ── MakroLeiste: Schrift-Reset ────────────────────────────────────────────────
STY_MAKRO_LEISTE_FONT: str = (
    "QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,"
    "QDoubleSpinBox, QSpinBox, QTabBar::tab, QToolTip,"
    "QGroupBox, QRadioButton, QMenu, QMenuBar {"
    "  font-family: 'Ubuntu', 'Noto Color Emoji'; }"
    "QPlainTextEdit, QTextEdit {"
    "  font-family: 'Courier New', 'Noto Color Emoji'; }"
)


# ── MakroLeiste: Refresh-Button (Kreis-Pfeil, groß) ──────────────────────────
def STY_REFRESH_BTN() -> str:
    """Stylesheet für den ↺-Button in der MakroLeiste."""
    return f"QPushButton {{ font-size:{schrift.pt(schrift.STUFE_XL)}pt; font-weight:bold; }}"


# ── MakroLeiste: Checkbox ─────────────────────────────────────────────────────
def STY_MAKRO_CHECKBOX() -> str:
    """Stylesheet für Checkboxen in der MakroLeiste."""
    return f"QCheckBox {{ font-size:{schrift.pt(schrift.STUFE_BASE)}pt; }}"


# ── MakroLeiste: Such-Feld Abstand ───────────────────────────────────────────
STY_MAKRO_SUCHE: str = "QLineEdit { margin-bottom:4px; }"


# ── MakroLeiste: Status-Label ─────────────────────────────────────────────────
def STY_MAKRO_STATUS() -> str:
    """Stylesheet für das Status-Label in der MakroLeiste."""
    return f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_BASE)}pt; }}"


# ── MakroLeiste: Ordner-Label ─────────────────────────────────────────────────
def STY_MAKRO_ORDNER_LBL(indent_px: int) -> str:
    """Stylesheet für das Ordner-Label in der MakroLeiste."""
    return (
        f"QLabel {{ font-weight: bold; font-size: {schrift.pt(schrift.STUFE_LG)}pt;"
        f" padding-top: 8px; padding-left: {indent_px}px; margin-bottom: 2px; }}"
    )


# ── MakroLeiste: Makro-Button ─────────────────────────────────────────────────
def STY_MAKRO_BTN(indent_px: int) -> str:
    """Stylesheet für einzelne Makro-Buttons in der MakroLeiste."""
    return (
        f"QPushButton {{ text-align: left; padding-left: {indent_px}px;"
        f" font-size: {schrift.pt(schrift.STUFE_BASE)}pt; }}"
    )


# ── KI-Tools: Info-Label (kursiv, klein) ──────────────────────────────────────
def STY_KI_INFO_LABEL() -> str:
    """Stylesheet für Info-Labels in KI-Tool-Sektionen (kursiv, klein)."""
    return f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt; font-style:italic; }}"


# ── KI-Tools: Werkzeug-Button (linksbündig) ──────────────────────────────────
def STY_KI_WERKZEUG_BTN() -> str:
    """Stylesheet für Werkzeug-Buttons in der KI-Tools-Tab."""
    return (
        f"QPushButton{{text-align:left; padding:2px 6px;"
        f"font-size:{schrift.pt(schrift.STUFE_BASE)}pt;}}"
    )


# ── FreecadHelfer: Titel (fett, groß) ────────────────────────────────────────
def STY_HELFER_TITEL() -> str:
    """Stylesheet für den Titel des FreeCAD-Helfer-Panels."""
    return f"QLabel {{ font-weight: bold; font-size: {schrift.pt(schrift.STUFE_LG)}pt; }}"


# ── FreecadHelfer: Status / Info Label (klein) ────────────────────────────────
def STY_HELFER_LABEL_SM() -> str:
    """Stylesheet für kleine Status- und Info-Labels im Helfer-Panel."""
    return f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt; }}"


# ── FreecadHelfer: Diff-/Blase-Kopf (fett, klein) ────────────────────────────
def STY_HELFER_BLASE_KOPF() -> str:
    """Stylesheet für den Kopf einer Diff-Blase."""
    return f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt; font-weight: bold; }}"


# ── FreecadHelfer: Vision-Warnung ─────────────────────────────────────────────
def STY_HELFER_VISION_WARN_BASE() -> str:
    """Basis-Stylesheet für die Vision-Warnmeldung (ohne Farben)."""
    return (
        f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt;"
        f" padding: 3px 6px; border-radius: 4px; }}"
    )


def STY_HELFER_VISION_WARN(bg_hex: str, fg_hex: str) -> str:
    """Stylesheet für die Vision-Warnmeldung (mit Laufzeit-Farben aus der Palette)."""
    return (
        f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt;"
        f" padding: 3px 6px; border-radius: 4px;"
        f" background-color: {bg_hex}; color: {fg_hex}; }}"
    )


# ── main.py: Dock-Titelleiste ─────────────────────────────────────────────────
STY_DOCK_TITLE_BAR: str = "border:none;"


# ── main.py: Dock-Icon-Label ──────────────────────────────────────────────────
def STY_DOCK_ICON_LABEL(rad_l: bool, rad_r: bool) -> str:
    """Stylesheet für Icon-Labels in der Dock-Titelleiste."""
    rl = "4px" if rad_l else "0px"
    rr = "4px" if rad_r else "0px"
    return (
        f"QLabel{{"
        f"border-top-left-radius:{rl};border-bottom-left-radius:{rl};"
        f"border-top-right-radius:{rr};border-bottom-right-radius:{rr};"
        f"font-size:{schrift.pt(schrift.STUFE_LG)}pt;}}"
        "QLabel:hover{}"
    )


# ── InitGui: Dock-Schrift-Reset ───────────────────────────────────────────────
STY_DOCK_FONT_RESET: str = "* { font-family: 'Ubuntu', 'Noto Color Emoji'; }"


# ── KI-Tools: Ausführen-Button (fett, Padding) ───────────────────────────────
STY_KI_AUSFUEHREN_BTN: str = "QPushButton{font-weight:bold; padding:4px 16px;}"


# ── FreecadHelfer: Diff-Blasen-Text (Laufzeit-Farbe + strukturelle Angaben) ──
def STY_HELFER_DIFF_TEXT(fg_hex: str) -> str:
    """Stylesheet für den Text in einer Diff-Blase (fg_hex aus QPalette)."""
    return (
        f"QLabel {{ color: {fg_hex}; background: transparent; "
        f"border: none; font-size: {schrift.pt(schrift.STUFE_BASE)}pt; }}"
    )


# ── FreecadHelfer: Chat-Blasen-Text (Laufzeit-Farbe + strukturelle Angaben) ──
def STY_HELFER_BUBBLE_TEXT(fg_hex: str) -> str:
    """Stylesheet für den Text in einer Chat-Blase (fg_hex aus QPalette)."""
    return (
        f"QLabel {{ color: {fg_hex}; background: transparent; border: none; }}"
    )


# ── Allgemeine Kleintext-Labels (kein Farbwert nötig) ────────────────────────

def STY_LABEL_SM(fs: int) -> str:
    """Kleines Label – Schriftgröße + Innenabstand."""
    return f"QLabel {{ font-size:{fs}pt; padding:2px; }}"


def STY_LABEL_SM_NP(fs: int) -> str:
    """Kleines Label – nur Schriftgröße, kein Padding."""
    return f"QLabel {{ font-size:{fs}pt; }}"


def STY_LABEL_SM_PADDED(fs: int) -> str:
    """Kleines Label mit ungleichmäßigem Padding (z. B. Ausgabe-Überschrift)."""
    return f"QLabel {{ font-size:{fs}pt; padding:4px 4px 0px 4px; }}"


# Fett-Button (Primäraktion ohne Farbe)
STY_BOLD_BTN: str = "QPushButton{font-weight:bold;} QPushButton:hover{}"