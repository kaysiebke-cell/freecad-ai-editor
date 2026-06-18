# -*- coding: utf-8 -*-
"""
dock_builder.py
───────────────
Baut alle Dock-Panels des MakroEditors auf und registriert sie.
Aufgerufen einmalig aus MakroEditor.__init__.
"""

from qt_compat import QtWidgets, QtCore, QtGui

import theme
import schrift
from highlighter import PythonHighlighter
from params import lade_kontext, speichere_kontext
from barrierefreiheit import BarrierefreiheitPanel
from freecad_helfer_panel import FreecadHelferPanel
from hilfe import HilfeTab
from assistent import AssistentPanel
from snippet_controller import SnipCommandEdit


# ── Dock-Infrastruktur ─────────────────────────────────────────────────────

def make_dock(editor, title, obj_name, area, widget, closable=True):
    dock = QtWidgets.QDockWidget(title, editor)
    dock.setObjectName(obj_name)
    dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
    features = (QtWidgets.QDockWidget.DockWidgetMovable |
                QtWidgets.QDockWidget.DockWidgetFloatable)
    if closable:
        features |= QtWidgets.QDockWidget.DockWidgetClosable
    dock.setFeatures(features)
    widget.setMinimumSize(0, 0)
    dock.setMinimumSize(0, 0)
    widget.minimumSizeHint = lambda: QtCore.QSize(0, 0)
    dock.minimumSizeHint   = lambda: QtCore.QSize(0, 0)
    dock.setWidget(widget)
    editor.addDockWidget(area, dock)
    return dock


def belegt(editor, area) -> bool:
    return any(
        d.isVisible() and not d.isFloating()
        and editor.dockWidgetArea(d) == area
        for d in editor.findChildren(QtWidgets.QDockWidget)
    )


def zeige_panel(editor, dock, standard_area):
    _L = QtCore.Qt.LeftDockWidgetArea
    _R = QtCore.Qt.RightDockWidgetArea
    _B = QtCore.Qt.BottomDockWidgetArea
    _GEGENUEBER = {_L: _R, _R: _L, _B: _B}
    if standard_area == _B:
        if editor.dockWidgetArea(dock) != _B:
            editor.addDockWidget(_B, dock)
        dock.show()
        dock.raise_()
        return
    ziel = standard_area
    if belegt(editor, ziel):
        gegenseite = _GEGENUEBER[ziel]
        if belegt(editor, gegenseite):
            vorhandene = [
                d for d in editor.findChildren(QtWidgets.QDockWidget)
                if d.isVisible() and not d.isFloating()
                and editor.dockWidgetArea(d) == gegenseite
                and d is not dock
            ]
            if vorhandene:
                editor.tabifyDockWidget(vorhandene[0], dock)
                dock.show()
                dock.raise_()
                return
        ziel = gegenseite
    if editor.dockWidgetArea(dock) != ziel:
        editor.addDockWidget(ziel, dock)
    dock.show()
    dock.raise_()


# ── Haupt-Builder ──────────────────────────────────────────────────────────

def init_docks(editor) -> None:
    """Erstellt alle Dock-Panels und setzt sie als Attribute am editor."""
    _L = QtCore.Qt.LeftDockWidgetArea
    _R = QtCore.Qt.RightDockWidgetArea
    _B = QtCore.Qt.BottomDockWidgetArea

    # Binde Infrastruktur-Methoden
    editor._make_dock   = lambda *a, **kw: make_dock(editor, *a, **kw)
    editor._belegt      = lambda area: belegt(editor, area)
    editor._zeige_panel = lambda dock, area: zeige_panel(editor, dock, area)

    # ── Einstellungs-Dock ──────────────────────────────────────────────────
    _cfg_widget = QtWidgets.QWidget()
    _cfg_l = QtWidgets.QVBoxLayout(_cfg_widget)
    _cfg_l.setContentsMargins(6, 6, 6, 6)
    _cfg_l.setSpacing(5)

    def _cfg_lbl(text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_XS)))
        return l

    _cfg_l.addWidget(_cfg_lbl("KI-QUELLE"))
    _r1 = QtWidgets.QHBoxLayout()
    _r1.setSpacing(3)
    _r1.addWidget(editor._src_box, stretch=1)
    _rl_btn = QtWidgets.QPushButton("🔄")
    _rl_btn.setFixedSize(26, 24)
    _rl_btn.setToolTip("Modelle neu laden")
    _rl_btn.clicked.connect(editor._refresh_models)
    _r1.addWidget(_rl_btn)
    _cfg_l.addLayout(_r1)
    _r1b = QtWidgets.QHBoxLayout()
    _r1b.setSpacing(3)
    _r1b.addWidget(QtWidgets.QLabel("Modell:"))
    _r1b.addWidget(editor._model_box, stretch=1)
    _cfg_l.addLayout(_r1b)
    _cfg_l.addWidget(_cfg_lbl("TEMPERATUR"))
    _r2 = QtWidgets.QHBoxLayout()
    _r2.setSpacing(3)
    _r2.addWidget(QtWidgets.QLabel("T:"))
    _r2.addWidget(editor._temp_box)
    _r2.addStretch()
    _cfg_l.addLayout(_r2)
    _cfg_l.addWidget(_cfg_lbl("MODUS"))
    _r3 = QtWidgets.QHBoxLayout()
    _r3.setSpacing(6)
    _r3.addWidget(editor._btn_modus_anfaenger)
    _r3.addWidget(editor._btn_modus_experte)
    _r3.addStretch()
    _cfg_l.addLayout(_r3)
    _cfg_l.addWidget(_cfg_lbl("FARBSCHEMA"))
    _r_farbe = QtWidgets.QHBoxLayout()
    _r_farbe.setSpacing(6)
    editor._btn_farbe_dunkel = QtWidgets.QPushButton("🌙 Dunkel")
    editor._btn_farbe_hell   = QtWidgets.QPushButton("☀ Hell")
    editor._btn_farbe_dunkel.setCheckable(True)
    editor._btn_farbe_hell.setCheckable(True)
    _farbe_gruppe = QtWidgets.QButtonGroup(editor)
    _farbe_gruppe.addButton(editor._btn_farbe_dunkel)
    _farbe_gruppe.addButton(editor._btn_farbe_hell)

    import params as _params
    _ist_dunkel = _params.farbschema_dunkel()
    editor._btn_farbe_dunkel.setChecked(_ist_dunkel)
    editor._btn_farbe_hell.setChecked(not _ist_dunkel)
    editor._btn_farbe_dunkel.clicked.connect(lambda: editor._on_farbschema(True))
    editor._btn_farbe_hell.clicked.connect(lambda: editor._on_farbschema(False))
    _r_farbe.addWidget(editor._btn_farbe_dunkel)
    _r_farbe.addWidget(editor._btn_farbe_hell)
    _r_farbe.addStretch()
    _cfg_l.addLayout(_r_farbe)
    _cfg_l.addWidget(_cfg_lbl("API-SCHLÜSSEL"))
    _cfg_l.addWidget(editor._key_anbieter)
    _cfg_l.addWidget(editor._key_feld)
    _cfg_l.addStretch()
    editor._dock_cfg = editor._make_dock(
        "⚙  Einstellungen", "dock_einstellungen", _L, _cfg_widget)

    # ── KI-Dock ────────────────────────────────────────────────────────────
    ki_widget = QtWidgets.QWidget()
    ki_layout = QtWidgets.QVBoxLayout(ki_widget)
    ki_layout.setContentsMargins(4, 4, 4, 4)
    ki_layout.setSpacing(3)
    _ki_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

    def _alle_snippets() -> dict:
        from freecad_data import SNIPPETS as _SNIPS
        alle = {}
        for kat_dict in _SNIPS.values():
            alle.update(kat_dict)
        alle.update(getattr(editor, "_user_snippets", {}))
        return alle

    _preset_zeile = QtWidgets.QHBoxLayout()
    _preset_zeile.setSpacing(3)
    _preset_zeile.addWidget(QtWidgets.QLabel("Preset:"))
    _preset_zeile.addWidget(editor._preset_btn, stretch=1)
    ki_layout.addLayout(_preset_zeile)

    _input_w = QtWidgets.QWidget()
    _input_l = QtWidgets.QVBoxLayout(_input_w)
    _input_l.setContentsMargins(0, 0, 0, 0)
    _input_l.setSpacing(2)
    _input_hdr = QtWidgets.QHBoxLayout()
    _input_hdr.addWidget(QtWidgets.QLabel("🔍 KI-Input"))
    _input_hdr.addStretch()
    for ico, tip, slot in [
        ("🧹", "Gesprächsverlauf zurücksetzen",                           editor._ki_verlauf_reset),
        ("💾", "Sitzung speichern\n(Chat-Verlauf + KI-Antwort als .json)", editor._sitzung_speichern),
        ("📂", "Sitzung laden\n(gespeicherten Chat-Verlauf wiederherstellen)", editor._sitzung_laden),
    ]:
        _b = QtWidgets.QPushButton(ico)
        _b.setFixedSize(22, 18)
        _b.setToolTip(tip)
        _b.setStyleSheet(theme.STY_ICON_BTN_BORDERLESS(schrift.pt(schrift.STUFE_LG)))
        _b.clicked.connect(slot)
        _input_hdr.addWidget(_b)
    _input_l.addLayout(_input_hdr)

    editor.find_area = SnipCommandEdit(_alle_snippets)
    editor.find_area.snip_gewaehlt.connect(editor._on_snip_slash_cmd)
    editor.find_area.setFont(QtGui.QFont("Courier New", 10))
    editor.find_area.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
    _opt = editor.find_area.document().defaultTextOption()
    _opt.setAlignment(QtCore.Qt.AlignLeft)
    editor.find_area.document().setDefaultTextOption(_opt)
    editor.find_area.setStyleSheet(theme.STY_KI_INPUT_FIELD())
    theme.apply_input_bg_suche(editor.find_area)
    editor.find_area.setPlaceholderText(
        "Suchbegriff oder Codeblock …\n/ + Snippet-Name → Autocomplete")
    editor._hl_find = PythonHighlighter(editor.find_area.document())
    QtCore.QTimer.singleShot(200, editor._hl_find.aktualisiere_theme)
    _input_l.addWidget(editor.find_area)
    _ki_splitter.addWidget(_input_w)

    _output_w = QtWidgets.QWidget()
    _output_l = QtWidgets.QVBoxLayout(_output_w)
    _output_l.setContentsMargins(0, 0, 0, 0)
    _output_l.setSpacing(2)
    _output_l.addWidget(QtWidgets.QLabel("🤖 KI-Antwort"))
    editor._ki_area = QtWidgets.QPlainTextEdit()
    editor._ki_area.setFont(QtGui.QFont("Courier New", 10))
    editor._ki_area.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
    _opt2 = editor._ki_area.document().defaultTextOption()
    _opt2.setAlignment(QtCore.Qt.AlignLeft)
    editor._ki_area.document().setDefaultTextOption(_opt2)
    editor._ki_area.setStyleSheet(theme.STY_KI_OUTPUT_FIELD())
    theme.apply_input_bg_ki(editor._ki_area)
    editor._ki_area.setPlaceholderText("KI-Antwort erscheint hier …")
    editor._hl_ki = PythonHighlighter(editor._ki_area.document())
    QtCore.QTimer.singleShot(200, editor._hl_ki.aktualisiere_theme)
    _output_l.addWidget(editor._ki_area)
    _ki_splitter.addWidget(_output_w)

    _kontext_w = QtWidgets.QWidget()
    _kontext_w.setMinimumHeight(80)
    _kontext_l = QtWidgets.QVBoxLayout(_kontext_w)
    _kontext_l.setContentsMargins(0, 0, 0, 0)
    _kontext_l.setSpacing(2)
    _kontext_l.addWidget(QtWidgets.QLabel("📌 Projekt-Kontext"))
    editor._kontext = QtWidgets.QPlainTextEdit()
    editor._kontext.setFont(QtGui.QFont("Courier New", 10))
    editor._kontext.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
    _opt3 = editor._kontext.document().defaultTextOption()
    _opt3.setAlignment(QtCore.Qt.AlignLeft)
    _opt3.setWrapMode(QtGui.QTextOption.WordWrap)
    editor._kontext.document().setDefaultTextOption(_opt3)
    theme.apply_input_bg_kontext(editor._kontext)
    editor._kontext.setPlaceholderText(
        "Kurze Beschreibung deines Projekts …\nWird bei jedem KI-Aufruf mitgeschickt.")
    editor._kontext.setPlainText(lade_kontext())
    editor._kontext.textChanged.connect(
        lambda: speichere_kontext(editor._kontext.toPlainText()))
    _kontext_l.addWidget(editor._kontext)
    _ki_splitter.addWidget(_kontext_w)

    _ki_splitter.setSizes([260, 220, 100])
    ki_layout.addWidget(_ki_splitter, stretch=1)
    editor._dock_ki = editor._make_dock("🤖  KI", "dock_ki", _L, ki_widget)

    # ── Aktionen-Dock ──────────────────────────────────────────────────────
    _akt_scroll = QtWidgets.QScrollArea()
    _akt_scroll.setWidgetResizable(True)
    _akt_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    _akt_inner = QtWidgets.QWidget()
    _akt_l = QtWidgets.QVBoxLayout(_akt_inner)
    _akt_l.setContentsMargins(4, 4, 4, 4)
    _akt_l.setSpacing(2)
    _akt_scroll.setWidget(_akt_inner)

    def _abschnitt(text):
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_XS)))
        _akt_l.addWidget(lbl)

    def _abtn(label, tip, slot=None, enabled=True, h=28):
        b = QtWidgets.QPushButton(label)
        b.setToolTip(tip)
        b.setMinimumHeight(h)
        b.setEnabled(enabled)
        b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        if slot:
            b.clicked.connect(slot)
        return b

    def _agrid(*buttons):
        g = QtWidgets.QGridLayout()
        g.setSpacing(2)
        g.setContentsMargins(0, 0, 0, 0)
        for i, b in enumerate(buttons):
            g.addWidget(b, i // 2, i % 2)
        _akt_l.addLayout(g)

    try:
        import autopep8 as _ap8
        _fmt_lbl = "✨  autopep8"
    except ImportError:
        _fmt_lbl = "🪄  Einrückung"

    _abschnitt("SUCHFELD / KI-INPUT")
    _agrid(
        _abtn("📥  Laden",     "Markierten Text ins Suchfeld laden",  editor._copy_from_editor),
        _abtn("🔍  Markieren", "Suchfeld-Inhalt im Editor markieren", editor._find_and_highlight),
        _abtn("🗑  Leeren",    "Suchfeld leeren", lambda: editor.find_area.clear()),
    )
    _abschnitt("KI-AKTIONEN")
    editor._btn_ki    = _abtn("🤖  Fragen",  "KI befragen", editor._ki_fragen, h=30)
    _btn_analyse      = _abtn("🔎  Analyse", "Code automatisch analysieren", editor._auto_analyse)
    editor._plan_modus_aktiv = False
    editor._btn_plan  = QtWidgets.QPushButton("🔍  Plan")
    editor._btn_plan.setCheckable(True)
    editor._btn_plan.setToolTip(
        "Plan-Modus: Code vor dem Ersetzen prüfen\n"
        "Wenn aktiv → zeigt neuen Code zur Bestätigung bevor er eingefügt wird")
    editor._btn_plan.setFixedHeight(22)
    editor._btn_plan.toggled.connect(editor._plan_modus_umschalten)
    editor._btn_ersetzen  = _abtn("✅  Ersetzen", "Block durch KI-Antwort ersetzen",
                                  editor._ersetzen_und_speichern, enabled=False)
    editor._btn_einfuegen = _abtn("➕  Einfügen", "KI-Antwort nach Block einfügen",
                                  editor._einfuegen_nach_fundstelle, enabled=False)

    def _vorschau_mit_ki_code():
        ki_code = editor._ki_area.toPlainText().strip()
        if ki_code and not ki_code.startswith("# ⏳") and not ki_code.startswith("🧠"):
            editor.vorschau_starten(code=ki_code)
        else:
            editor.vorschau_starten()

    _btn_vorschau = _abtn(
        "👁  Vorschau",
        "KI-Code direkt in FreeCAD ausführen und 3D-Viewport anzeigen",
        _vorschau_mit_ki_code)
    _agrid(editor._btn_ki, _btn_analyse, editor._btn_plan,
           editor._btn_ersetzen, editor._btn_einfuegen, _btn_vorschau)

    _abschnitt("DATEI")
    _agrid(
        _abtn("💾  Speichern",   "Datei speichern",            editor.speichern),
        _abtn("💾✕  Schließen", "Speichern & Schließen",      editor.speichern_und_schliessen),
        _abtn("↺  Neu laden",   "Letzten Speicherstand laden", editor.neu_laden),
        _abtn("↩  Backup",      "Backup wiederherstellen",     editor._backup_wiederherstellen),
    )
    _abschnitt("EDITOR")
    _agrid(
        _abtn("☰  Alles",   "Alles markieren",  editor.alles_auswaehlen),
        _abtn("✕  Löschen", "Auswahl löschen",  editor.loeschen_auswahl),
        _abtn(_fmt_lbl,     "Code formatieren", editor._formatieren),
        _abtn("❓  Hilfe",  "Hilfe öffnen",     editor._zeige_hilfe),
    )
    _abschnitt("BIBLIOTHEK")
    _agrid(
        _abtn("📚  Speichern", "In Bibliothek speichern",
              lambda: editor.bibliothek_speichern(code=editor._get_editor_code(),
                                                  ki_generiert=False)),
        _abtn("🤖📚  KI→Bib", "KI-Antwort in Bibliothek",
              lambda: editor.bibliothek_speichern(code=editor._ki_area.toPlainText(),
                                                  ki_generiert=True)),
    )
    _akt_l.addStretch()
    editor._dock_akt = editor._make_dock("⚙  Aktionen", "dock_aktionen", _R, _akt_scroll)

    # ── Weitere Docks (tabifiziert) ────────────────────────────────────────
    editor._dock_snip  = editor._make_dock("📦  Snippets",  "dock_snippets",  _L,
                                           editor._baue_snippet_tab())
    editor.tabifyDockWidget(editor._dock_ki, editor._dock_snip)
    editor._dock_hints = editor._make_dock("💡  API-Hints", "dock_hints",     _L,
                                           editor._baue_hints_tab())
    editor.tabifyDockWidget(editor._dock_ki, editor._dock_hints)
    editor._dock_files = editor._make_dock("📂  Dateien",   "dock_dateien",   _L,
                                           editor._baue_dateibrowser_tab())
    editor.tabifyDockWidget(editor._dock_ki, editor._dock_files)
    editor._dock_kitools = editor._make_dock("🛠  KI-Tools", "dock_kitools",  _R,
                                             editor._baue_ki_tools_tab())
    editor.tabifyDockWidget(editor._dock_akt, editor._dock_kitools)
    editor._dock_bib = editor._make_dock("📚  Bibliothek", "dock_bibliothek", _R,
                                         editor._baue_bibliothek_tab())
    editor.tabifyDockWidget(editor._dock_akt, editor._dock_bib)

    # ── Hilfe + Barrierefreiheit Dock ─────────────────────────────────────
    _bf_gruppe_widget = QtWidgets.QWidget()
    _bg_lay = QtWidgets.QVBoxLayout(_bf_gruppe_widget)
    _bg_lay.setContentsMargins(0, 0, 0, 0)
    _bg_lay.setSpacing(0)
    _bg_leiste = QtWidgets.QWidget()
    _bg_leiste_lay = QtWidgets.QHBoxLayout(_bg_leiste)
    _bg_leiste_lay.setContentsMargins(4, 2, 4, 2)
    _bg_leiste_lay.setSpacing(2)
    _bg_separator = QtWidgets.QFrame()
    _bg_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
    _bg_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

    editor._bf_stack        = QtWidgets.QStackedWidget()
    editor._assistent_panel = AssistentPanel(editor)
    editor._assistent_panel.widget_blinken.connect(editor._widget_blinken)
    editor._bf_stack.addWidget(editor._assistent_panel)   # 0
    editor._helfer_panel = FreecadHelferPanel()
    editor._bf_stack.addWidget(editor._helfer_panel)      # 1
    editor._bf_panel = BarrierefreiheitPanel()
    editor._bf_panel.geaendert.connect(editor._on_barrierefreiheit)
    editor._bf_stack.addWidget(editor._bf_panel)          # 2
    editor._bf_stack.addWidget(HilfeTab())                # 3

    _fs_bg = schrift.pt(schrift.STUFE_BASE)
    _bg_btn_gruppe = QtWidgets.QButtonGroup(_bf_gruppe_widget)
    _bg_btn_gruppe.setExclusive(True)

    def _bg_btn(label, index):
        btn = QtWidgets.QPushButton(label)
        btn.setCheckable(True)
        btn.setFixedHeight(26)
        btn.setStyleSheet(theme.STY_MINI_TAB_BTN(_fs_bg))
        btn.clicked.connect(lambda: editor._bf_stack.setCurrentIndex(index))
        _bg_btn_gruppe.addButton(btn)
        _bg_leiste_lay.addWidget(btn)
        return btn

    _bg_btn("🤝 Assist.", 0).setChecked(True)
    _bg_btn("🔧 Helfer",  1)
    _bg_btn("♿ Zugang",  2)
    _bg_btn("❓ Hilfe",   3)
    _bg_leiste_lay.addStretch()
    _bg_lay.addWidget(_bg_leiste)
    _bg_lay.addWidget(_bg_separator)
    _bg_lay.addWidget(editor._bf_stack, 1)
    editor._dock_bf_gruppe = editor._make_dock(
        "♿  Hilfe+Zugang", "dock_bf_gruppe", _R, _bf_gruppe_widget, closable=True)
    editor._dock_bf_gruppe.hide()

    # ── Fehler-Dock ────────────────────────────────────────────────────────
    fehler_panel_widget = QtWidgets.QWidget()
    fp = QtWidgets.QVBoxLayout(fehler_panel_widget)
    fp.setContentsMargins(0, 0, 0, 0)
    fp.setSpacing(0)
    editor._fehler_inhalt = editor._baue_fehler_panel()
    editor._fehler_inhalt.setVisible(True)
    fp.addWidget(editor._fehler_inhalt)
    editor._btn_fehler_toggle = QtWidgets.QPushButton()
    editor._btn_fehler_toggle.hide()
    editor._dock_fehler = editor._make_dock(
        "⚠  Fehler-Übersetzer", "dock_fehler", _B, fehler_panel_widget)
    editor._dock_fehler.hide()

    def _sandbox_toggle_cb(sandbox_aktiv: bool):
        if sandbox_aktiv:
            editor._dock_fehler.show()

    editor._fehler_inhalt.setze_sandbox_toggle_cb(_sandbox_toggle_cb)
    editor._fehler_inhalt._btn_sb_run.clicked.disconnect()
    editor._fehler_inhalt._btn_sb_run.clicked.connect(editor._on_sandbox_run)

    editor._rechte_tabs = QtWidgets.QStackedWidget()
    editor._rechte_tabs.hide()
