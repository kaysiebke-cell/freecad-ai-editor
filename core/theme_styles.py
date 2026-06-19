# -*- coding: utf-8 -*-
"""UI-Texte, Stylesheet-Konstanten und alle STY_*-Funktionen."""

from qt_compat import QtWidgets, QtCore, QtGui
import schrift

_FONT_UI_FAMILY   = schrift.FAMILIE_UI
_FONT_MONO_FAMILY = schrift.FAMILIE_MONO


# ═══════════════════════════════════════════════════════════════════════════════
# UI-TEXTE
# ═══════════════════════════════════════════════════════════════════════════════
TEXTS: dict[str, str] = {
    "hilfe_suche_placeholder": "Hilfe durchsuchen …",
    "hilfe_version_label":     "FreeCAD MultiAI Panel  •  v1.1",
    "hilfe_tab_titel":         "❓ Hilfe",
    "hilfe_suche_icon":        "🔍",
}


# ═══════════════════════════════════════════════════════════════════════════════
# FARBEN & ABSCHNITTS-AKZENTE  (Hilfe-Tab)
# ═══════════════════════════════════════════════════════════════════════════════
HILFE_FARBEN: list[tuple[str, str, str]] = [
    ("⚠",          "", ""),
    ("📦 Install",  "", ""),
    ("🔧",          "", ""),
    ("✂️",          "", ""),
    ("🎨",          "", ""),
]
HILFE_FARBE_DEFAULT: tuple[str, str] = ("", "")


# ═══════════════════════════════════════════════════════════════════════════════
# HILFE-TAB STYLESHEET-KONSTANTEN
# ═══════════════════════════════════════════════════════════════════════════════
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

STY_SEARCH_LINE: str = (
    "QLineEdit{ "
    "border:1px solid palette(shadow); border-radius:3px; padding:3px;}"
)


def STY_VERSION_LABEL() -> str:
    return f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt; padding-top:4px; }}"


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
# STRUKTURELLE HINTERGRÜNDE
# ═══════════════════════════════════════════════════════════════════════════════
STY_SCROLL_AREA_BG: str = "QScrollArea{}"
STY_CONTAINER_BG:   str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# TAB-LEISTE
# ═══════════════════════════════════════════════════════════════════════════════
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


def apply_klappsektion_style(btn: "QtWidgets.QPushButton") -> None:
    btn.setStyleSheet(STY_TAB_BTN())


# ═══════════════════════════════════════════════════════════════════════════════
# BASIS-HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _btn(fs, pad="4px 8px", r=3, *, border=False, bold=False, align=""):
    b = "1px solid palette(shadow)" if border else "none"
    bw = "bold" if bold else "normal"
    al = f"text-align:{align};" if align else ""
    return (f"QPushButton{{font-size:{fs}pt;border-radius:{r}px;"
            f"padding:{pad};border:{b};font-weight:{bw};{al}}}")


def _btn_toggle(fs, pad="2px 4px", r=3):
    return (_btn(fs, pad, r) +
            "QPushButton:checked{font-weight:bold;border:1px solid palette(shadow);}"
            "QPushButton:hover{border:1px solid palette(shadow);}")


def _lbl(fs, pad="", *, bold=False, italic=False, border="", radius=0,
         color="", extra="", selector="QLabel"):
    s = f"font-size:{fs}pt;"
    if pad:    s += f"padding:{pad};"
    if bold:   s += "font-weight:bold;"
    if italic: s += "font-style:italic;"
    if border: s += border
    if radius: s += f"border-radius:{radius}px;"
    if color:  s += f"color:{color};"
    if extra:  s += extra
    return f"{selector}{{{s}}}"


def _field(fs, widget="QLineEdit", pad="2px 4px", r=3):
    return (f"{widget}{{font-size:{fs}pt;border:1px solid palette(shadow);"
            f"border-radius:{r}px;padding:{pad};}}")


# ═══════════════════════════════════════════════════════════════════════════════
# STYLESHEET-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════════

def STY_HAUPTFENSTER_FONT() -> str:
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


def STY_EDITOR_TABS(fs: int) -> str:
    return (
        "QTabWidget::pane{ border:none; }"
        "QTabBar::tab{ padding:5px 14px;"
        f" font-size:{fs}pt;"
        " border:none; border-right:1px solid palette(shadow); min-width:60px; max-width:200px;}"
        "QTabBar::tab:selected{ border-bottom:2px solid palette(highlight);}"
        "QTabBar::tab:hover{}"
    )


def STY_STATUS_LABEL(fs: int) -> str:
    return f"QLabel, QCheckBox {{ font-size:{fs}pt; }}"


def STY_ABSCHNITT_LABEL(fs: int) -> str:
    return _lbl(fs, bold=True,
                extra="padding-top:6px;padding-bottom:2px;border-bottom:1px solid palette(shadow);")


def STY_ABSCHNITT_LABEL_LG(fs: int) -> str:
    return _lbl(fs, bold=True,
                extra="border-bottom:1px solid palette(shadow);padding-bottom:2px;margin-top:6px;")


def STY_PANEL_BTN(fs: int) -> str:
    return _btn_toggle(fs, "2px 4px")


def STY_MINI_TAB_BTN(fs: int) -> str:
    return _btn_toggle(fs, "2px 6px")


def STY_ICON_BTN_BORDERLESS(fs: int) -> str:
    return f"QPushButton{{border:none;font-size:{fs}pt;}}"


def STY_KI_INPUT_FIELD() -> str:
    return (
        "QPlainTextEdit{font-family:'Courier New',monospace;"
        "border:1px solid palette(shadow); border-radius:3px;}"
        "QPlainTextEdit:focus{border:1px solid palette(highlight);}"
    )


def STY_KI_OUTPUT_FIELD() -> str:
    return ("QPlainTextEdit{font-family:'Courier New',monospace;"
            " border:1px solid palette(shadow);}")


STY_TOOLBAR: str = "QToolBar { border: none; spacing: 2px; padding: 2px 4px; }"

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

STY_HILFE_TAB: str = (
    "#HilfeTab QLabel, #HilfeTab QPushButton,"
    "#HilfeTab QLineEdit, #HilfeTab QScrollArea {"
    "  font-family: 'Ubuntu'; }"
    "#HilfeTab QPlainTextEdit {"
    "  font-family: 'Courier New', monospace; }"
)


def STY_BTN_BORDER(fs: int) -> str:
    return (f"QPushButton{{border:1px solid palette(shadow);border-radius:3px;font-size:{fs}pt;}}"
            "QPushButton:hover{}QPushButton:pressed{}")


def STY_BTN_BORDER_BOLD(fs: int) -> str:
    return (f"QPushButton{{border:1px solid palette(shadow);border-radius:4px;"
            f"font-size:{fs}pt;font-weight:bold;}}"
            "QPushButton:hover{}QPushButton:pressed{}")


def STY_PRIMARY_BTN(fs: int) -> str:
    return (f"QPushButton{{border:none;border-radius:6px;font-weight:bold;"
            f"font-size:{fs}pt;padding:6px 20px;}}"
            "QPushButton:hover{}QPushButton:pressed{}")


def STY_SECONDARY_BTN(fs: int) -> str:
    return (f"QPushButton{{border:1px solid palette(shadow);border-radius:6px;"
            f"font-size:{fs}pt;padding:5px 14px;}}QPushButton:hover{{}}")


def STY_BEGRUESSUNG_DIALOG(fs: int) -> str:
    return (
        "QDialog{}QWidget{}QLabel{}QFrame{}"
        f"QLineEdit{{border:1px solid palette(shadow);"
        f"border-radius:5px;padding:6px 10px;font-size:{fs}pt;"
        "font-family:'Courier New', monospace;}"
        "QLineEdit:focus{}"
    )


def STY_WARN_BOX(fs: int) -> str:
    return _lbl(fs, "8px", border="border:1px solid palette(shadow);", radius=5)


def STY_TIPP_BOX(fs: int) -> str:
    return _lbl(fs, "10px", border="border:1px solid palette(shadow);", radius=5)


def STY_DB_PFAD_FELD(fs: int) -> str:
    return _field(fs)


def STY_DB_FILTER_FELD(fs: int) -> str:
    return _field(fs)


def STY_DB_CHECKBOX(fs: int) -> str:
    return f"QCheckBox{{font-size:{fs}pt;}}QCheckBox::indicator{{width:12px;height:12px;}}"


def STY_DB_NEU_BTN(fs: int) -> str:
    return (f"QPushButton{{border:1px solid palette(shadow);border-radius:3px;"
            f"font-size:{fs}pt;font-weight:bold;padding:3px 6px;}}"
            "QPushButton:hover{}QPushButton:pressed{}")


def STY_DB_LZ_COMBO(fs: int) -> str:
    return _field(fs, "QComboBox", "1px 4px")


def STY_DB_LZ_BTN(fs: int) -> str:
    return (f"QPushButton{{border:1px solid palette(shadow);border-radius:3px;"
            f"font-size:{fs}pt;}}QPushButton:hover{{}}")


def STY_DB_TREE(fs: int) -> str:
    return (
        "QTreeView{"
        f"border:1px solid palette(shadow);border-radius:3px;font-size:{fs}pt;}}"
        "QTreeView::item:selected{}QTreeView::item:hover{}"
        "QTreeView::branch:has-children:!has-siblings:closed,"
        "QTreeView::branch:closed:has-children:has-siblings{"
        "border-image:none; image:none;}"
    )


def STY_DB_STATUS(fs: int) -> str:
    return _lbl(fs, "1px 3px")


def STY_SNIPPET_LISTE(fs: int) -> str:
    return (
        f"QListWidget{{border:1px solid palette(shadow);font-size:{fs}pt;}}"
        "QListWidget::item{padding:4px 5px;}"
        "QListWidget::item:selected{}QListWidget::item:alternate{}"
    )


STY_SNIPPET_VORSCHAU: str = (
    "QTextEdit{border:1px solid palette(shadow); font-family:'Courier New',monospace;}"
)

STY_HINTS_LISTE: str = (
    "QListWidget{font-family:'Courier New',monospace;border:1px solid palette(shadow);}"
    "QListWidget::item{padding:2px 5px; text-align:left;}"
    "QListWidget::item:selected{}QListWidget::item:alternate{}"
)


def STY_HINTS_DESC(fs: int) -> str:
    return _lbl(fs, "5px", border="border:1px solid palette(shadow);", radius=3,
                extra="min-height:32px;")


STY_FEHLER_TAB_FELD: str = (
    "QPlainTextEdit{font-family:'Courier New',monospace;"
    "border:1px solid palette(shadow);border-radius:3px;}"
)


def STY_SNIP_POPUP(fs: int) -> str:
    return (
        "QListWidget{"
        "border:1px solid palette(shadow); border-bottom-left-radius:4px;"
        "border-bottom-right-radius:4px;"
        f"font-size:{fs}pt; padding:2px;}}"
        "QListWidget::item{ padding:4px 8px; }"
        "QListWidget::item:selected{}QListWidget::item:hover{}"
        "QListWidget::item[disabled='true']{ font-style:italic; }"
    )


def STY_SNIP_POPUP_HEADER(fs: int) -> str:
    return (
        f"QLabel{{font-size:{fs}pt;"
        "font-weight:bold; padding:2px 8px;"
        "border-top-left-radius:4px; border-top-right-radius:4px;}"
    )


def STY_BANNER_BTN(fs: int) -> str:
    return (
        "#_bannerBtn{text-align:left; padding:4px 8px; border:none;"
        f" font-size:{fs}pt; font-weight:bold;"
        " background:transparent; color:palette(highlighted-text);}"
        "#_bannerBtn:hover{background:transparent;}"
    )


STY_BANNER_BODY: str = (
    "#_bannerBody{ font-size:9pt; padding:4px 8px 8px 8px;"
    " border:none; background:transparent;"
    " color:palette(highlighted-text); }"
)


def STY_VORSCHAU_TITEL(fs: int) -> str:
    return _lbl(fs, bold=True)


def STY_VORSCHAU_CLOSE_BTN(fs: int) -> str:
    return (f"QPushButton{{border:1px solid palette(shadow);"
            f"border-radius:3px;font-size:{fs}pt;padding:0 8px;}}QPushButton:hover{{}}")


def STY_VORSCHAU_STATUS(fs: int) -> str:
    return _lbl(fs)


STY_VORSCHAU_CONTAINER: str = (
    "#VorschauContainer { border:1px solid palette(shadow); border-radius:3px; }"
)

STY_VORSCHAU_PLACEHOLDER: str = "QLabel { border:none; }"


def STY_VORSCHAU_LOG_LABEL(fs: int) -> str:
    return f"QLabel {{ font-size:{fs}pt; font-weight:bold; letter-spacing:1px; }}"


STY_VORSCHAU_LOG_BOX: str = (
    "QPlainTextEdit{font-family:'Courier New',monospace;"
    "border:1px solid palette(shadow);border-radius:3px;}"
)


def STY_VORSCHAU_WARN(fs: int) -> str:
    return _lbl(fs, "1px 0")


def STY_WERKZEUG_STATUS(fs: int) -> str:
    return _lbl(fs, "2px 4px", extra="border-top:1px solid palette(shadow);")


def STY_ZEILE_EDIT(fs: int) -> str:
    return _field(fs, pad="3px 5px", r=2)


def STY_CODE_BAUM(fs: int) -> str:
    return (
        f"QTreeWidget{{font-size:{fs}pt;"
        "border:1px solid palette(shadow);border-radius:2px;"
        "font-family:'Ubuntu','Noto Color Emoji';}"
        "QTreeWidget::item{padding:2px 2px;}"
        "QTreeWidget::item:selected{}QTreeWidget::item:hover{}"
        "QTreeWidget::branch:has-children:!has-siblings:closed,"
        "QTreeWidget::branch:closed:has-children:has-siblings{"
        "  border-image:none; image:none;}"
    )


def STY_CODE_STATISTIKEN_LBL(fs: int) -> str:
    return (
        f"QLabel {{ border:1px solid palette(shadow);"
        f" padding:6px; font-size:{fs}pt; border-radius:2px;"
        f" font-family:'Ubuntu','Noto Color Emoji'; }}"
    )


def STY_SYNTAX_CHECK_LBL(fs: int) -> str:
    return (
        f"QLabel {{ padding:6px; border-radius:3px; font-size:{fs}pt;"
        f" font-family:'Ubuntu','Noto Color Emoji'; }}"
    )


def STY_WERKZEUG_SEKTION(fs: int) -> str:
    return (
        f"QLabel {{ font-size:{fs}pt; font-weight:bold;"
        f" font-family:'Ubuntu','Noto Color Emoji';"
        f" padding-top:6px; padding-bottom:4px;"
        f" border-bottom:1px solid palette(shadow); }}"
    )


def STY_SECTION_HEAD_BTN(fs: int) -> str:
    return (
        f"QPushButton{{text-align:left;padding:4px 6px;"
        f"font-size:{fs}pt;font-weight:500;border:none;border-radius:4px;"
        "background:transparent;color:palette(text);}"
        "QPushButton:hover{background:palette(alternateBase);}"
    )


def STY_SECTION_BTN(fs: int) -> str:
    return (
        f"QPushButton{{text-align:left;padding:3px 8px;font-size:{fs}pt;"
        "border:none;border-radius:4px;background:transparent;color:palette(text);}"
        "QPushButton:hover{background:palette(alternateBase);}"
        "QPushButton:pressed{background:palette(mid);}"
        "QPushButton:disabled{color:palette(mid);}"
    )


def STY_GRID_BTN(fs: int) -> str:
    return (
        f"QPushButton{{text-align:center;padding:2px 4px;font-size:{fs}pt;"
        "border:1px solid palette(mid);border-radius:4px;"
        "background:palette(button);color:palette(text);}"
        "QPushButton:hover{background:palette(alternateBase);}"
        "QPushButton:pressed{background:palette(mid);}"
        "QPushButton:disabled{color:palette(mid);}"
    )


def STY_RAIL_BTN(fs: int) -> str:
    return (
        f"QPushButton{{border:none;border-radius:5px;background:transparent;"
        f"font-size:{fs}pt;font-weight:bold;color:palette(buttonText);}}"
        f"QPushButton:hover{{background:palette(midlight);}}"
        f"QPushButton:checked{{background:palette(midlight);"
        f"border:1px solid palette(highlight);}}"
    )


def STY_NAV_BAUM_SIDEBAR(fs: int) -> str:
    return (
        f"QTreeWidget{{font-size:{fs}pt;border:1px solid palette(mid);border-radius:3px;}}"
        "QTreeWidget::item{padding:2px;}"
    )


def STY_STATISTIKEN_LBL_SIDEBAR(fs: int) -> str:
    return _lbl(fs, "5px", border="border:1px solid palette(mid);", radius=3)


def STY_CHECK_LBL_SIDEBAR(fs: int) -> str:
    return _lbl(fs, "5px", radius=3)


def STY_SIDEBAR_STATUS(fs: int) -> str:
    return _lbl(fs, "2px 4px", extra="border-top:1px solid palette(mid);")


def STY_JEDI_POPUP(fs: int) -> str:
    return (
        "QListView{"
        "border:1px solid palette(shadow);"
        f"font-family:'Courier New', monospace; font-size:{fs}pt;}}"
    )


def STY_BF_HINWEIS(fs: int) -> str:
    return _lbl(fs, italic=True, color="palette(mid)")


STY_HILFE_SUCHE: str = "QLineEdit{border:1px solid palette(shadow);border-radius:3px;padding:3px;}"

STY_SEPARATOR:       str = "QFrame { color:palette(mid); margin:2px 0; }"
STY_SEPARATOR_TIGHT: str = "QFrame { color:palette(mid); margin:0; }"
STY_BORDER_NONE:     str = "border:none;"

STY_HOCHKONTRAST: str = (
    "QWidget { color: #ffffff; background-color: #000000; }"
    "QPushButton { background: #222; border: 2px solid #fff; }"
    "QPlainTextEdit, QTextEdit { background: #000; color: #fff; }"
)

STY_MAKRO_LEISTE_FONT: str = (
    "QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,"
    "QDoubleSpinBox, QSpinBox, QTabBar::tab, QToolTip,"
    "QGroupBox, QRadioButton, QMenu, QMenuBar {"
    "  font-family: 'Ubuntu', 'Noto Color Emoji'; }"
    "QPlainTextEdit, QTextEdit {"
    "  font-family: 'Courier New', 'Noto Color Emoji'; }"
)


def STY_REFRESH_BTN() -> str:
    return f"QPushButton {{ font-size:{schrift.pt(schrift.STUFE_XL)}pt; font-weight:bold; }}"


def STY_MAKRO_CHECKBOX() -> str:
    return f"QCheckBox {{ font-size:{schrift.pt(schrift.STUFE_BASE)}pt; }}"


STY_MAKRO_SUCHE: str = "QLineEdit { margin-bottom:4px; }"


def STY_MAKRO_STATUS() -> str:
    return _lbl(schrift.pt(schrift.STUFE_BASE))


def STY_MAKRO_ORDNER_LBL(indent_px: int) -> str:
    return (
        f"QLabel {{ font-weight: bold; font-size: {schrift.pt(schrift.STUFE_LG)}pt;"
        f" padding-top: 8px; padding-left: {indent_px}px; margin-bottom: 2px; }}"
    )


def STY_MAKRO_BTN(indent_px: int) -> str:
    return (
        f"QPushButton {{ text-align: left; padding-left: {indent_px}px;"
        f" font-size: {schrift.pt(schrift.STUFE_BASE)}pt; }}"
    )


def STY_KI_INFO_LABEL() -> str:
    return _lbl(schrift.pt(schrift.STUFE_SM), italic=True)


def STY_KI_WERKZEUG_BTN() -> str:
    return (f"QPushButton{{text-align:left; padding:2px 6px;"
            f"font-size:{schrift.pt(schrift.STUFE_BASE)}pt;}}")


def STY_HELFER_TITEL() -> str:
    return _lbl(schrift.pt(schrift.STUFE_LG), bold=True)


def STY_HELFER_LABEL_SM() -> str:
    return _lbl(schrift.pt(schrift.STUFE_SM))


def STY_HELFER_BLASE_KOPF() -> str:
    return _lbl(schrift.pt(schrift.STUFE_SM), bold=True)


def STY_HELFER_VISION_WARN_BASE() -> str:
    return (
        f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt;"
        f" padding: 3px 6px; border-radius: 4px; }}"
    )


def STY_HELFER_VISION_WARN(bg_hex: str, fg_hex: str) -> str:
    return (
        f"QLabel {{ font-size:{schrift.pt(schrift.STUFE_SM)}pt;"
        f" padding: 3px 6px; border-radius: 4px;"
        f" background-color: {bg_hex}; color: {fg_hex}; }}"
    )


STY_DOCK_TITLE_BAR: str = "border:none;"


def STY_DOCK_ICON_LABEL(rad_l: bool, rad_r: bool) -> str:
    rl = "4px" if rad_l else "0px"
    rr = "4px" if rad_r else "0px"
    return (
        f"QLabel{{"
        f"border-top-left-radius:{rl};border-bottom-left-radius:{rl};"
        f"border-top-right-radius:{rr};border-bottom-right-radius:{rr};"
        f"font-size:{schrift.pt(schrift.STUFE_LG)}pt;}}"
        "QLabel:hover{}"
    )


STY_DOCK_FONT_RESET:  str = "* { font-family: 'Ubuntu', 'Noto Color Emoji'; }"
STY_KI_AUSFUEHREN_BTN: str = "QPushButton{font-weight:bold; padding:4px 16px;}"


def STY_HELFER_DIFF_TEXT(fg_hex: str) -> str:
    return (
        f"QLabel {{ color: {fg_hex}; background: transparent; "
        f"border: none; font-size: {schrift.pt(schrift.STUFE_BASE)}pt; }}"
    )


def STY_HELFER_BUBBLE_TEXT(fg_hex: str) -> str:
    return f"QLabel {{ color: {fg_hex}; background: transparent; border: none; }}"


def STY_LABEL_SM(fs: int) -> str:
    return _lbl(fs, "2px")


def STY_LABEL_SM_NP(fs: int) -> str:
    return _lbl(fs)


def STY_LABEL_SM_PADDED(fs: int) -> str:
    return _lbl(fs, "4px 4px 0px 4px")


STY_BOLD_BTN: str = "QPushButton{font-weight:bold;} QPushButton:hover{}"
