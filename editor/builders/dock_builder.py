# -*- coding: utf-8 -*-
"""
dock_builder.py
───────────────
Baut alle Dock-Panels des MakroEditors auf und registriert sie.
Aufgerufen einmalig aus MakroEditor.__init__.
"""

from core.qt_compat import QtWidgets, QtCore, QtGui

from core import theme
from core import schrift
from core.highlighter import PythonHighlighter
from core.params import (lade_kontext, speichere_kontext,
                         lade_system_prompt_extra, speichere_system_prompt_extra,
                         lade_max_sitzungen, speichere_max_sitzungen,
                         lade_auto_einfuegen, speichere_auto_einfuegen,
                         lade_thinking_modus, speichere_thinking_modus,
                         lade_api_key, SYSTEM_PROMPT_VORLAGEN)
from ui.barrierefreiheit import BarrierefreiheitPanel
from editor.panel import FreecadHelferPanel
from data.hilfe import HilfeTab
from editor.controller.assistent import AssistentPanel
from editor.controller.snippet_widgets import SnipCommandEdit


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
    _cfg_scroll = QtWidgets.QScrollArea()
    _cfg_scroll.setWidgetResizable(True)
    _cfg_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    _cfg_widget = QtWidgets.QWidget()
    _cfg_l = QtWidgets.QVBoxLayout(_cfg_widget)
    _cfg_l.setContentsMargins(theme.DOCK_CFG_RAND, theme.DOCK_CFG_RAND,
                              theme.DOCK_CFG_RAND, theme.DOCK_CFG_RAND)
    _cfg_l.setSpacing(theme.DOCK_CFG_ABSTAND)

    def _cfg_lbl(text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_XS)))
        return l

    # ── Schnellstart ──
    _cfg_l.addWidget(_cfg_lbl("SCHNELLSTART"))

    _SCHNELLSTART_PROFILE = [
        ("🎯 FreeCAD Code", {
            "vorlage":  SYSTEM_PROMPT_VORLAGEN.get("🧱 FreeCAD Part-Script", ""),
            "temp":     0.2,
            "modus":    "experte",
            "thinking": "aus",
        }),
        ("💬 Erklärung", {
            "vorlage":  SYSTEM_PROMPT_VORLAGEN.get("🐍 Python-Experte (Standard)", ""),
            "temp":     0.7,
            "modus":    "anfaenger",
            "thinking": "aus",
        }),
        ("🧠 Thinking", {
            "vorlage":  SYSTEM_PROMPT_VORLAGEN.get("🧱 FreeCAD Part-Script", ""),
            "temp":     0.2,
            "modus":    "experte",
            "thinking": "an",
        }),
    ]

    def _wende_schnellstart_an(cfg):
        vorlage = cfg["vorlage"]
        editor._system_prompt_extra.setPlainText(vorlage)
        speichere_system_prompt_extra(vorlage)
        editor._temp_box.setValue(cfg["temp"])
        if cfg["modus"] == "experte":
            editor._btn_modus_experte.setChecked(True)
        else:
            editor._btn_modus_anfaenger.setChecked(True)
        editor._thinking_box.setCurrentIndex(1 if cfg["thinking"] == "an" else 0)

    _qs_layout = QtWidgets.QHBoxLayout()
    _qs_layout.setSpacing(theme.DOCK_CFG_ZEILEN_ABST)
    for _qs_label, _qs_cfg in _SCHNELLSTART_PROFILE:
        _qs_btn = QtWidgets.QPushButton(_qs_label)
        _qs_btn.setMinimumHeight(theme.SCHNELLSTART_BTN_H)
        _qs_btn.setFont(schrift.ui_font())
        _qs_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        _qs_btn.setToolTip(
            f"Setzt Vorlage, Temperatur, Modus und Thinking\n"
            f"auf bewährte Werte für: {_qs_label}")
        _qs_btn.clicked.connect(lambda checked, c=_qs_cfg: _wende_schnellstart_an(c))
        _qs_layout.addWidget(_qs_btn)
    _cfg_l.addLayout(_qs_layout)

    # ── KI-Quelle ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("KI-QUELLE"))
    _r1 = QtWidgets.QHBoxLayout()
    _r1.setSpacing(theme.DOCK_CFG_ZEILEN_ABST)
    _r1.addWidget(editor._src_box, stretch=1)
    _rl_btn = QtWidgets.QPushButton("🔄")
    _rl_btn.setFixedSize(theme.DOCK_RELOAD_BTN_BREITE, theme.DOCK_RELOAD_BTN_HOEHE)
    _rl_btn.setToolTip("Modelle neu laden")
    _rl_btn.clicked.connect(editor._refresh_models)
    _r1.addWidget(_rl_btn)
    _vt_btn = QtWidgets.QPushButton("🔌")
    _vt_btn.setFixedSize(theme.VERBTEST_BTN_BREITE, theme.VERBTEST_BTN_HOEHE)
    _vt_btn.setToolTip("Verbindung testen")
    _r1.addWidget(_vt_btn)
    _cfg_l.addLayout(_r1)
    _cfg_l.addWidget(editor._model_box)

    editor._verbtest_label = QtWidgets.QLabel("")
    editor._verbtest_label.setFont(schrift.ui_font(schrift.STUFE_XS))
    editor._verbtest_label.setMinimumHeight(theme.VERBTEST_LABEL_MIN_H)
    _cfg_l.addWidget(editor._verbtest_label)

    def _on_verbtest_ergebnis(text: str):
        editor._verbtest_label.setText(text)

    def _starte_verbtest():
        from editor.ki.verbindungstest import VerbindungsTest
        quelle = editor._src_box.currentText() if hasattr(editor._src_box, "currentText") else ""
        anbieter = quelle.split("(")[0].strip().lower().replace(" ", "")
        key = lade_api_key(anbieter)
        editor._verbtest_label.setText("🔄 Teste …")
        vt = VerbindungsTest(quelle, key, parent=editor)
        vt.ergebnis.connect(_on_verbtest_ergebnis)
        vt.finished.connect(vt.deleteLater)
        vt.start()

    _vt_btn.clicked.connect(_starte_verbtest)

    # ── Modell-Parameter (FormLayout: Label | Widget) ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("MODELL-PARAMETER"))

    def _flbl(text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(theme.STY_FORM_LABEL())
        return l

    _param_form = QtWidgets.QFormLayout()
    _param_form.setContentsMargins(
        theme.PARAM_FORM_RAND_REST, theme.PARAM_FORM_RAND_OBEN,
        theme.PARAM_FORM_RAND_REST, theme.PARAM_FORM_RAND_REST)
    _param_form.setSpacing(theme.PARAM_FORM_ABSTAND)
    _param_form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    _param_form.addRow(_flbl("Temperatur:"), editor._temp_box)
    _param_form.addRow(_flbl("Top-P:"),      editor._top_p_box)
    _param_form.addRow(_flbl("Top-K:"),      editor._top_k_box)
    _param_form.addRow(_flbl("Max-Token:"),  editor._max_tokens_box)
    _param_form.addRow(_flbl("Kontext:"),    editor._ctx_box)
    _cfg_l.addLayout(_param_form)

    # ── Modus ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("MODUS"))
    _r3 = QtWidgets.QHBoxLayout()
    _r3.setSpacing(theme.DOCK_CFG_ABSCHN_ABST)
    _r3.addWidget(editor._btn_modus_anfaenger)
    _r3.addWidget(editor._btn_modus_experte)
    _r3.addStretch()
    _cfg_l.addLayout(_r3)

    # ── Farbschema ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("FARBSCHEMA"))
    editor._btn_farbe_dunkel = QtWidgets.QPushButton("🌙 Dunkel")
    editor._btn_farbe_hell   = QtWidgets.QPushButton("☀ Hell")
    editor._btn_farbe_dunkel.setCheckable(True)
    editor._btn_farbe_hell.setCheckable(True)
    _farbe_gruppe = QtWidgets.QButtonGroup(editor)
    _farbe_gruppe.addButton(editor._btn_farbe_dunkel)
    _farbe_gruppe.addButton(editor._btn_farbe_hell)
    import core.params as _params
    _ist_dunkel = _params.farbschema_dunkel()
    editor._btn_farbe_dunkel.setChecked(_ist_dunkel)
    editor._btn_farbe_hell.setChecked(not _ist_dunkel)
    editor._btn_farbe_dunkel.clicked.connect(lambda: editor._on_farbschema(True))
    editor._btn_farbe_hell.clicked.connect(lambda: editor._on_farbschema(False))
    _r_farbe = QtWidgets.QHBoxLayout()
    _r_farbe.setSpacing(theme.DOCK_CFG_ABSCHN_ABST)
    _r_farbe.addWidget(editor._btn_farbe_dunkel)
    _r_farbe.addWidget(editor._btn_farbe_hell)
    _r_farbe.addStretch()
    _cfg_l.addLayout(_r_farbe)

    # ── API-Schlüssel ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("API-SCHLÜSSEL"))
    editor._key_feld.setToolTip(
        "API-Schlüssel für den gewählten Anbieter.\n"
        "Alternativ: file:/pfad/zur/schluessel-datei\n"
        "→ Key wird zur Laufzeit aus der Datei gelesen.")
    _cfg_l.addWidget(editor._key_feld)

    # ── System-Prompt-Zusatz ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _sysp_hdr = QtWidgets.QHBoxLayout()
    _sysp_hdr.setSpacing(theme.DOCK_CFG_ZEILEN_ABST)
    _sysp_hdr.addWidget(_cfg_lbl("SYSTEM-PROMPT-ZUSATZ"), stretch=1)
    _vorlage_btn = QtWidgets.QToolButton()
    _vorlage_btn.setText("📋")
    _vorlage_btn.setFixedSize(theme.CFG_VORLAGE_BTN_W, theme.CFG_VORLAGE_BTN_H)
    _vorlage_btn.setToolTip("Vordefinierte System-Prompt-Vorlage laden")
    _vorlage_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
    _vorlage_menu = QtWidgets.QMenu(_vorlage_btn)
    for _titel, _text in SYSTEM_PROMPT_VORLAGEN.items():
        if _titel.startswith("──"):
            _vorlage_menu.addSeparator()
            continue
        _act = _vorlage_menu.addAction(_titel)
        _act.setEnabled(bool(_text))
        _act.triggered.connect(
            lambda checked, t=_text: (
                editor._system_prompt_extra.setPlainText(t),
                speichere_system_prompt_extra(t)
            )
        )
    _vorlage_btn.setMenu(_vorlage_menu)
    _sysp_hdr.addWidget(_vorlage_btn)
    _cfg_l.addLayout(_sysp_hdr)
    editor._system_prompt_extra = QtWidgets.QPlainTextEdit()
    editor._system_prompt_extra.setFont(schrift.ui_font())
    editor._system_prompt_extra.setPlaceholderText(
        "Optionaler Zusatz zum System-Prompt ...\n"
        "z. B. 'Antworte immer auf Deutsch' oder eigene Regeln.\n"
        "Beginnt der Text mit 'You are', ersetzt er den Basis-Prompt komplett.")
    editor._system_prompt_extra.setMinimumHeight(theme.CFG_SYSPROMPT_MIN_H)
    editor._system_prompt_extra.setMaximumHeight(theme.CFG_SYSPROMPT_MAX_H)
    editor._system_prompt_extra.setPlainText(lade_system_prompt_extra())
    editor._system_prompt_extra.textChanged.connect(
        lambda: speichere_system_prompt_extra(
            editor._system_prompt_extra.toPlainText()))
    _cfg_l.addWidget(editor._system_prompt_extra)

    # ── Aufbewahrung ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("AUFBEWAHRUNG"))
    _aufb_zeile = QtWidgets.QHBoxLayout()
    _aufb_zeile.setSpacing(theme.DOCK_CFG_ZEILEN_ABST)
    _aufb_zeile.addWidget(QtWidgets.QLabel("Max. Sitzungen:"))
    editor._max_sitzungen_box = QtWidgets.QSpinBox()
    editor._max_sitzungen_box.setRange(1, 500)
    editor._max_sitzungen_box.setValue(lade_max_sitzungen())
    editor._max_sitzungen_box.setToolTip(
        "Maximale Anzahl gespeicherter Chat-Sitzungen\n"
        "(gilt für automatische Sitzungs-Rotation)")
    editor._max_sitzungen_box.valueChanged.connect(speichere_max_sitzungen)
    _aufb_zeile.addWidget(editor._max_sitzungen_box)
    _aufb_zeile.addStretch()
    _cfg_l.addLayout(_aufb_zeile)

    # ── Auto-Einfügen ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("AUTO-EINFÜGEN"))
    editor._chk_auto_einfuegen = QtWidgets.QCheckBox("Nach KI-Antwort automatisch einfügen")
    editor._chk_auto_einfuegen.setFont(schrift.ui_font())
    editor._chk_auto_einfuegen.setChecked(lade_auto_einfuegen())
    editor._chk_auto_einfuegen.toggled.connect(speichere_auto_einfuegen)
    _cfg_l.addWidget(editor._chk_auto_einfuegen)

    # ── Thinking (Anthropic) ──
    _cfg_l.addSpacing(theme.DOCK_CFG_SEK_SPACING)
    _cfg_l.addWidget(_cfg_lbl("THINKING (ANTHROPIC)"))
    editor._thinking_box = QtWidgets.QComboBox()
    editor._thinking_box.setFont(schrift.ui_font())
    editor._thinking_box.addItems(["Aus", "An"])
    editor._thinking_box.setCurrentIndex(1 if lade_thinking_modus() == "an" else 0)
    editor._thinking_box.currentIndexChanged.connect(
        lambda idx: speichere_thinking_modus("an" if idx == 1 else "aus"))
    _cfg_l.addWidget(editor._thinking_box)

    _cfg_l.addStretch()
    _cfg_scroll.setWidget(_cfg_widget)
    editor._dock_cfg = editor._make_dock(
        "⚙  Einstellungen", "dock_einstellungen", _L, _cfg_scroll)

    # ── KI-Dock ────────────────────────────────────────────────────────────
    ki_widget = QtWidgets.QWidget()
    ki_layout = QtWidgets.QVBoxLayout(ki_widget)
    ki_layout.setContentsMargins(theme.DOCK_KI_RAND, theme.DOCK_KI_RAND,
                                 theme.DOCK_KI_RAND, theme.DOCK_KI_RAND)
    ki_layout.setSpacing(theme.DOCK_KI_ABSTAND)
    _ki_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

    def _alle_snippets() -> dict:
        from data.freecad_data import SNIPPETS as _SNIPS
        alle = {}
        for kat_dict in _SNIPS.values():
            alle.update(kat_dict)
        alle.update(getattr(editor, "_user_snippets", {}))
        return alle

    _preset_zeile = QtWidgets.QHBoxLayout()
    _preset_zeile.setSpacing(theme.DOCK_KI_PRESET_ABST)
    _preset_zeile.addWidget(QtWidgets.QLabel("Preset:"))
    _preset_zeile.addWidget(editor._preset_btn, stretch=1)
    ki_layout.addLayout(_preset_zeile)

    _input_w = QtWidgets.QWidget()
    _input_l = QtWidgets.QVBoxLayout(_input_w)
    _input_l.setContentsMargins(theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND,
                                theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND)
    _input_l.setSpacing(theme.DOCK_KI_INPUT_ABST)

    # Header-Zeile über dem kombinierten Feld
    _input_hdr = QtWidgets.QHBoxLayout()
    _input_hdr.addWidget(QtWidgets.QLabel("🔍 KI-Input"))
    _input_hdr.addStretch()
    for ico, tip, slot in [
        ("🧹", "Gesprächsverlauf zurücksetzen",                           editor._ki_verlauf_reset),
        ("💾", "Sitzung speichern\n(Chat-Verlauf + KI-Antwort als .json)", editor._sitzung_speichern),
        ("📂", "Sitzung laden\n(gespeicherten Chat-Verlauf wiederherstellen)", editor._sitzung_laden),
    ]:
        _b = QtWidgets.QPushButton(ico)
        _b.setFixedSize(theme.DOCK_ICON_BTN_BREITE, theme.DOCK_ICON_BTN_HOEHE)
        _b.setToolTip(tip)
        _b.setStyleSheet(theme.STY_ICON_BTN_BORDERLESS(schrift.pt(schrift.STUFE_LG)))
        _b.clicked.connect(slot)
        _input_hdr.addWidget(_b)
    _input_l.addLayout(_input_hdr)

    # Ein Feld, ein Rahmen — Label ist der einzige interne Trenner, keine Linien.
    _feld_rahmen = QtWidgets.QFrame()
    _feld_rahmen.setObjectName("ki_eingabe_rahmen")
    _feld_rahmen.setStyleSheet(theme.STY_KI_EINGABE_RAHMEN())
    _feld_rahmen_l = QtWidgets.QVBoxLayout(_feld_rahmen)
    _feld_rahmen_l.setContentsMargins(theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND,
                                      theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND)
    _feld_rahmen_l.setSpacing(theme.DOCK_KI_RAHMEN_ABST)

    editor._frage_feld = QtWidgets.QPlainTextEdit()
    editor._frage_feld.setFont(schrift.mono_font())
    editor._frage_feld.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
    editor._frage_feld.setMinimumHeight(theme.DOCK_KI_FRAGE_MIN_H)
    editor._frage_feld.setStyleSheet(theme.STY_KI_EINGABE_FELD())
    editor._frage_feld.setPlaceholderText("Frage oder Aufgabe … (optional, überschreibt Preset)")
    theme.apply_input_bg_suche(editor._frage_feld)
    _feld_rahmen_l.addWidget(editor._frage_feld, stretch=1)

    editor._ki_trenner_lbl = QtWidgets.QLabel("  Code-Block:")
    editor._ki_trenner_lbl.setFixedHeight(theme.DOCK_TRENNER_LBL_HOEHE)
    theme.apply_input_bg_suche(editor._ki_trenner_lbl)
    _feld_rahmen_l.addWidget(editor._ki_trenner_lbl)

    editor.find_area = SnipCommandEdit(_alle_snippets)
    editor.find_area.snip_gewaehlt.connect(editor._on_snip_slash_cmd)
    editor.find_area.setFont(schrift.mono_font())
    editor.find_area.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
    _opt = editor.find_area.document().defaultTextOption()
    _opt.setAlignment(QtCore.Qt.AlignLeft)
    editor.find_area.document().setDefaultTextOption(_opt)
    editor.find_area.setStyleSheet(theme.STY_KI_EINGABE_FELD())
    theme.apply_input_bg_suche(editor.find_area)
    editor.find_area.setPlaceholderText(
        "Code-Block hier einfügen …\n/ + Snippet-Name → Autocomplete")
    editor._hl_find = PythonHighlighter(editor.find_area.document())
    QtCore.QTimer.singleShot(200, editor._hl_find.aktualisiere_theme)
    _feld_rahmen_l.addWidget(editor.find_area, stretch=1)

    _input_l.addWidget(_feld_rahmen, stretch=1)

    _ki_splitter.addWidget(_input_w)

    _output_w = QtWidgets.QWidget()
    _output_l = QtWidgets.QVBoxLayout(_output_w)
    _output_l.setContentsMargins(theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND,
                                 theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND)
    _output_l.setSpacing(theme.DOCK_KI_OUTPUT_ABST)
    _output_l.addWidget(QtWidgets.QLabel("🤖 KI-Antwort"))
    editor._ki_area = QtWidgets.QPlainTextEdit()
    editor._ki_area.setFont(schrift.mono_font())
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
    _kontext_w.setMinimumHeight(theme.DOCK_KI_KONTEXT_MIN_H)
    _kontext_l = QtWidgets.QVBoxLayout(_kontext_w)
    _kontext_l.setContentsMargins(theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND,
                                  theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND)
    _kontext_l.setSpacing(theme.DOCK_KI_KONTEXT_ABST)
    _kontext_l.addWidget(QtWidgets.QLabel("📌 Projekt-Kontext"))
    editor._kontext = QtWidgets.QPlainTextEdit()
    editor._kontext.setFont(schrift.mono_font())
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

    _ki_splitter.setSizes([320, 220, 100])
    ki_layout.addWidget(_ki_splitter, stretch=1)
    editor._dock_ki = editor._make_dock("🤖  KI", "dock_ki", _L, ki_widget)

    # ── Aktionen-Dock ──────────────────────────────────────────────────────
    _akt_scroll = QtWidgets.QScrollArea()
    _akt_scroll.setWidgetResizable(True)
    _akt_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    _akt_inner = QtWidgets.QWidget()
    _akt_l = QtWidgets.QVBoxLayout(_akt_inner)
    _akt_l.setContentsMargins(theme.DOCK_AKT_RAND, theme.DOCK_AKT_RAND,
                              theme.DOCK_AKT_RAND, theme.DOCK_AKT_RAND)
    _akt_l.setSpacing(theme.DOCK_AKT_ABSTAND)
    _akt_scroll.setWidget(_akt_inner)

    def _abschnitt(text):
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_XS)))
        _akt_l.addWidget(lbl)

    def _abtn(label, tip, slot=None, enabled=True, h=theme.DOCK_AKT_BTN_MIN_H):
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
        g.setSpacing(theme.DOCK_AKT_GRID_ABST)
        g.setContentsMargins(theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND,
                             theme.DOCK_KI_RAHMEN_RAND, theme.DOCK_KI_RAHMEN_RAND)
        for i, b in enumerate(buttons):
            g.addWidget(b, i // 2, i % 2)
        _akt_l.addLayout(g)

    try:
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
    editor._btn_plan.setFixedHeight(theme.DOCK_PLAN_BTN_HOEHE)
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
    _bg_lay.setContentsMargins(theme.DOCK_BF_RAND, theme.DOCK_BF_RAND,
                               theme.DOCK_BF_RAND, theme.DOCK_BF_RAND)
    _bg_lay.setSpacing(theme.DOCK_BF_ABSTAND)
    _bg_leiste = QtWidgets.QWidget()
    _bg_leiste_lay = QtWidgets.QHBoxLayout(_bg_leiste)
    _bg_leiste_lay.setContentsMargins(*theme.DOCK_BF_LEISTE_RAND)
    _bg_leiste_lay.setSpacing(theme.DOCK_BF_LEISTE_ABST)
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
        btn.setFixedHeight(theme.DOCK_BF_BTN_HOEHE)
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
    fp.setContentsMargins(theme.DOCK_FEHLER_RAND, theme.DOCK_FEHLER_RAND,
                          theme.DOCK_FEHLER_RAND, theme.DOCK_FEHLER_RAND)
    fp.setSpacing(theme.DOCK_FEHLER_ABSTAND)
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
