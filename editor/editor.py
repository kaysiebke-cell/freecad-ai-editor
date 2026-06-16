# -*- coding: utf-8 -*-
"""
editor.py
─────────
Haupt-Modul des Makro-Editors.  Bindet alle Mixin-Module zusammen:

  editor/widgets/editor_widgets.py   → JediEditor
  editor/ki/ki_controller.py         → KiController  (KI-Streaming, Modelle)
  editor/controller/browser_controller.py → BrowserController (Datei-Browser)
  editor/controller/snippet_controller.py → SnippetController (Snippets, Hints)

Öffentliche API (wird von manager.py genutzt):
  MakroEditor(pfad, parent)  – Hauptfenster des Editors
  MakroEditor.fehler_anzeigen(text) – Fehler-Panel öffnen
  MakroEditor.insert_snippet(code)  – Snippet einfügen
"""

import os
import re
import glob
import shutil
import time
from datetime import datetime

from qt_compat import QtWidgets, QtCore, QtGui

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    import autopep8
    _HAS_AUTOPEP8 = True
except ImportError:
    _HAS_AUTOPEP8 = False

import theme
import schrift
from highlighter import PythonHighlighter
from fehler import uebersetze_fehler
from params import (KI_PRESETS, KI_PRESET_KATEGORIEN, lade_kontext, speichere_kontext,
                    lade_api_key, speichere_api_key, speichere_quelle, lade_quelle)
from hilfe import HilfeTab
from werkzeuge import WerkzeugLeiste

from editor_widgets import JediEditor
from ki_controller import KiController as KIMixin
from browser_controller import BrowserController as BrowserMixin
from snippet_controller import SnippetController as TabsMixin, SnipCommandEdit
from ki_tools_tab import KiToolsTabMixin
from bibliothek_tab import BibliothekTabMixin
from barrierefreiheit import BarrierefreiheitPanel
from freecad_helfer_panel import FreecadHelferPanel
from vorschau_controller import VorschauController as VorschauMixin
from assistent import AssistentPanel

# Vorkompilierte Regex
_RE_WORD_CHARS = re.compile(r"\w+")


class MakroEditor(QtWidgets.QMainWindow, KIMixin, BrowserMixin, TabsMixin, VorschauMixin, KiToolsTabMixin, BibliothekTabMixin):
    """
    Editor mit frei anordenbaren Dock-Panels (QDockWidget).
    Alle Module können per Drag & Drop verschoben, abgedockt
    und als eigenes Fenster genutzt werden.
    """

    _ki_chunk       = QtCore.Signal(str)
    _ki_stream_done = QtCore.Signal()
    _ki_error       = QtCore.Signal(str)
    _ki_compact_signal = QtCore.Signal(int)   # Anzahl komprimierter Nachrichten
    such_in_dateien = QtCore.Signal(str)       # Fallback: Manager soll Dateien durchsuchen

    def __init__(self, pfad, parent=None):
        super().__init__(parent)
        self._pfad      = pfad
        self._geaendert = False
        self.setWindowTitle(f"Makro-Editor  –  {os.path.basename(pfad)}")
        _scr = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(min(1080, int(_scr.width()  * 0.80)),
                    min(760,  int(_scr.height() * 0.82)))
        _x = _scr.x() + (_scr.width()  - self.width())  // 2
        _y = _scr.y() + (_scr.height() - self.height()) // 2
        self.move(_x, _y)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setDockNestingEnabled(True)   # Docks beliebig verschachteln
        self.setWindowFlags(
            QtCore.Qt.Window
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(800, 500)
        self.setMaximumSize(16777215, 16777215)
        if self.layout():
            self.layout().setContentsMargins(6, 6, 6, 6)

        # ── Schrift: Ubuntu + Emoji-Fallback (Regel 1) ────────────────────
        _f = QtGui.QFont("Ubuntu", 10)
        try:
            from main import emoji_font
            _f = emoji_font(_f)
        except Exception:
            pass
        self.setFont(_f)
        # KEIN *-Selektor: überschreibt Qt-interne Spacing-Werte
        # → extremes Wort-Spacing. Nur konkrete Klassen benennen.
        # FIX: 'Noto Color Emoji' aus QPlainTextEdit/QTextEdit entfernt –
        #      auf Linux ersetzt Qt sonst Ziffern durch Emoji-Glyphen
        #      (mit falschem Zeichenabstand / sichtbaren Lücken).
        self.setStyleSheet(
            "QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,"
            "QDoubleSpinBox, QSpinBox, QTabBar::tab, QToolTip,"
            "QGroupBox, QRadioButton, QMenu, QMenuBar {"
            "  font-family: 'Ubuntu', 'Noto Color Emoji'; text-align: left; }"
            "QListWidget, QListView, QTreeWidget, QTreeView {"
            "  font-family: 'Ubuntu', 'Noto Color Emoji'; text-align: left; }"
            "QListWidget::item, QListView::item { text-align: left; }"
            "QPlainTextEdit, QTextEdit {"
            "  font-family: 'Courier New', monospace; text-align: left; }"
            "_BlauBanner { background-color: palette(highlight); }"
        )
        # ──────────────────────────────────────────────────────────────────

        self._alive = True
        self._session = requests.Session() if _HAS_REQUESTS else None

        # Chunk-Batching
        self._chunk_buffer: list = []
        self._stream_token_count  = 0
        self._stream_start_time   = 0.0
        self._flush_timer = QtCore.QTimer(self)
        self._flush_timer.setInterval(30)
        self._flush_timer.timeout.connect(self._flush_chunks)
        self._status_timer = QtCore.QTimer(self)
        self._status_timer.setInterval(500)
        self._status_timer.timeout.connect(self._update_stream_status)

        # Warte-Animation im KI-Antwortfeld (solange noch kein echter Token kam)
        self._warte_dots = 0
        self._warte_aktiv = False
        self._warte_timer = QtCore.QTimer(self)
        self._warte_timer.setInterval(400)
        def _warte_tick():
            if not self._warte_aktiv:
                self._warte_timer.stop()
                return
            self._warte_dots = (self._warte_dots + 1) % 4
            punkte = "●" * self._warte_dots + "○" * (3 - self._warte_dots)
            elapsed = time.monotonic() - self._stream_start_time
            self._ki_area.setPlainText(
                f"🧠 KI denkt nach {punkte}  ({elapsed:.0f} s)")
        self._warte_timer.timeout.connect(_warte_tick)

        self._ki_chunk.connect(self._on_ki_chunk)
        self._ki_stream_done.connect(self._on_ki_stream_done)
        self._ki_error.connect(self._on_ki_error)
        self._ki_compact_signal.connect(self._on_ki_compact)

        # Gesprächsverlauf initialisieren
        self._chat_verlauf: list = []
        self._compact_zusammenfassung: str = ""

        # Datei-Watcher: externe Änderungen erkennen
        self._datei_watcher = QtCore.QFileSystemWatcher(self)
        self._datei_watcher.addPath(pfad)
        self._datei_watcher.fileChanged.connect(self._datei_extern_geaendert)
        self._watcher_pause = False
        # ── Zentrales Widget: Nur der Editor ──────────────────────────────
        def mkbtn(label, tip, slot, w=None, h=28):
            b = QtWidgets.QPushButton(label)
            b.setToolTip(tip)
            b.setMinimumHeight(h)
            if w:
                b.setFixedWidth(w)
            b.clicked.connect(slot)
            return b

        # ── KI-Widgets anlegen (werden in KI-Dock eingesetzt) ─────────────
        from ki_modi import (MODUS_ANFAENGER, MODUS_EXPERTE,
                             MODUS_LABELS, MODUS_TOOLTIPS, MODUS_DEFAULT)
        self._ki_modus = MODUS_DEFAULT

        self._src_box = QtWidgets.QComboBox()
        self._src_box.addItems([
            "Ollama (Lokal)", "Anthropic (Claude)", "OpenAI (ChatGPT)",
            "GitHub Copilot", "OpenRouter (Cloud)", "Gemini (Google)",
            "DeepSeek", "Qwen (Alibaba)", "Groq", "Mistral",
            "Together AI", "Fireworks AI", "xAI (Grok)", "Cohere",
            "SambaNova", "MiniMax", "Llama API", "Moonshot", "HuggingFace",
        ])
        self._src_box.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._src_box.currentIndexChanged.connect(self._refresh_models)
        self._src_box.currentTextChanged.connect(speichere_quelle)
        # Letzten Anbieter wiederherstellen
        _gespeicherte_quelle = lade_quelle()
        if _gespeicherte_quelle in [
                self._src_box.itemText(i)
                for i in range(self._src_box.count())]:
            self._src_box.setCurrentText(_gespeicherte_quelle)

        self._model_box = QtWidgets.QComboBox()
        self._model_box.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._preset_btn = QtWidgets.QToolButton()
        self._preset_btn.setText("── Preset wählen ──")
        self._preset_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self._preset_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._preset_menu = QtWidgets.QMenu(self._preset_btn)
        self._preset_btn.setMenu(self._preset_menu)
        self._baue_preset_menu()

        self._preset_box = QtWidgets.QComboBox()
        self._preset_box.addItems(KI_PRESETS.keys())
        self._preset_box.hide()

        self._temp_box = QtWidgets.QDoubleSpinBox()
        self._temp_box.setRange(0.0, 2.0)
        self._temp_box.setSingleStep(0.1)
        self._temp_box.setValue(0.2)
        self._temp_box.setFixedWidth(58)
        self._temp_box.setToolTip(
            "Temperatur (0.0–2.0)\n"
            "0.0–0.3 = präzise (Code)\n"
            "0.5–0.8 = kreativ\n"
            "1.0+    = sehr kreativ")

        self._btn_modus_anfaenger = QtWidgets.QRadioButton(MODUS_LABELS[MODUS_ANFAENGER])
        self._btn_modus_anfaenger.setToolTip(MODUS_TOOLTIPS[MODUS_ANFAENGER])
        self._btn_modus_anfaenger.setChecked(MODUS_DEFAULT == MODUS_ANFAENGER)

        self._btn_modus_experte = QtWidgets.QRadioButton(MODUS_LABELS[MODUS_EXPERTE])
        self._btn_modus_experte.setToolTip(MODUS_TOOLTIPS[MODUS_EXPERTE])
        self._btn_modus_experte.setChecked(MODUS_DEFAULT == MODUS_EXPERTE)

        def _modus_geaendert():
            self._ki_modus = (MODUS_EXPERTE
                              if self._btn_modus_experte.isChecked()
                              else MODUS_ANFAENGER)
            self._set_status(f"Modus → {MODUS_LABELS[self._ki_modus]}")

        self._btn_modus_anfaenger.toggled.connect(_modus_geaendert)
        self._btn_modus_experte.toggled.connect(_modus_geaendert)

        # ── API-Schlüssel-Widgets (früh anlegen – Einstellungen-Dock braucht sie) ──
        self._key_anbieter = QtWidgets.QComboBox()
        self._key_anbieter.addItems([
            "Anthropic (Claude)", "OpenAI (ChatGPT)", "GitHub Copilot",
            "OpenRouter", "DeepSeek", "Google Gemini", "Groq", "Mistral",
            "Together AI", "Hugging Face", "xAI (Grok)", "Fireworks AI",
            "Moonshot", "Qwen (Alibaba)", "Cohere", "SambaNova", "MiniMax",
            "Llama API",
        ])
        self._key_anbieter.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._key_anbieter.setToolTip("KI-Anbieter wählen")
        self._key_feld = QtWidgets.QLineEdit()
        self._key_feld.setEchoMode(QtWidgets.QLineEdit.Password)
        self._key_feld.setMinimumHeight(26)
        self._key_feld.setPlaceholderText("sk-ant-…")
        self._prev_anbieter_id = "anthropic"
        _PLACEHOLDERS = {
            "anthropic":"sk-ant-…","openai":"sk-…","github":"ghp_…",
            "openrouter":"sk-or-…","deepseek":"sk-…","gemini":"AIza…",
            "groq":"gsk_…","mistral":"…","together":"…","huggingface":"hf_…",
            "xai":"xai-…","fireworks":"fw_…","moonshot":"sk-…","qwen":"sk-…",
            "cohere":"…","sambanova":"…","minimax":"…","llama":"…",
        }
        def _anbieter_gewechselt():
            speichere_api_key(self._prev_anbieter_id, self._key_feld.text().strip())
            self._prev_anbieter_id = self._key_anbieter_id()
            self._key_feld.setText(lade_api_key(self._prev_anbieter_id))
            self._key_feld.setPlaceholderText(_PLACEHOLDERS.get(self._prev_anbieter_id, ""))
        self._key_feld.editingFinished.connect(
            lambda: speichere_api_key(self._key_anbieter_id(), self._key_feld.text().strip()))
        self._key_anbieter.currentIndexChanged.connect(lambda _: _anbieter_gewechselt())
        _anbieter_gewechselt()

        # ── Schnellsuche (im zentralen Widget, standardmäßig verborgen) ───
        self._suche_widget = QtWidgets.QWidget()
        sl = QtWidgets.QHBoxLayout(self._suche_widget)
        sl.setContentsMargins(4, 2, 4, 2)
        sl.setSpacing(6)
        sl.addWidget(QtWidgets.QLabel("Suche:"))
        self._suche_feld = QtWidgets.QLineEdit()
        self._suche_feld.setPlaceholderText("Suchen (Enter = weiter) …")
        self._suche_feld.returnPressed.connect(self._suche_weiter)
        sl.addWidget(self._suche_feld)
        sl.addWidget(QtWidgets.QLabel("Ersetzen:"))
        self._ersatz_feld = QtWidgets.QLineEdit()
        self._ersatz_feld.setPlaceholderText("Ersatztext …")
        sl.addWidget(self._ersatz_feld)
        for lbl, tip, slot in [("→", "Weiter", self._suche_weiter),
                               ("✍", "Ersetzen", self._ersetzen_text),
                               ("Alle", "Alle ersetzen", self._alles_ersetzen)]:
            sl.addWidget(mkbtn(lbl, tip, slot, h=26))
        _bx = QtWidgets.QPushButton("✕")
        _bx.setFixedWidth(26)
        _bx.setToolTip("Suche schließen (Esc)")
        _bx.clicked.connect(lambda: self._suche_widget.setVisible(False))
        sl.addWidget(_bx)
        self._suche_widget.setVisible(False)

        _sc_suche = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F"), self)
        _sc_suche.activated.connect(self._toggle_suche)

        # ── Editor-Tab-Widget (Zentrum) ────────────────────────────────────
        self._tabs: list = []
        self._editor      = None
        self._editor_tab_widget = QtWidgets.QTabWidget()
        self._editor_tab_widget.setTabsClosable(True)
        self._editor_tab_widget.setMovable(True)
        self._editor_tab_widget.setDocumentMode(True)
        self._editor_tab_widget.setStyleSheet(
            "QTabWidget::pane{ border:none; }"
            "QTabBar::tab{ padding:5px 14px;"
            f" font-size:{schrift.pt(schrift.STUFE_BASE)}pt;"
            " border:none; border-right:1px solid ; min-width:60px; max-width:200px;}"
            "QTabBar::tab:selected{ border-bottom:2px solid ;}"
            "QTabBar::tab:hover{}")
        self._editor_tab_widget.tabCloseRequested.connect(self._tab_schliessen)
        self._editor_tab_widget.currentChanged.connect(self._tab_gewechselt)

        central = QtWidgets.QWidget()
        _cl = QtWidgets.QVBoxLayout(central)
        _cl.setContentsMargins(0, 0, 0, 0)
        _cl.setSpacing(0)
        _cl.addWidget(self._editor_tab_widget, stretch=1)
        _cl.addWidget(self._suche_widget)
        self.setCentralWidget(central)

        # ── Status-Leiste ─────────────────────────────────────────────────
        self._status = QtWidgets.QLabel("Bereit.")
        self._status.setStyleSheet(
            f"font-size:{schrift.pt(schrift.STUFE_BASE)}pt;")
        self.statusBar().addWidget(self._status, stretch=1)
        self.statusBar().setSizeGripEnabled(True)

        # ═══ DOCK-WIDGETS ═════════════════════════════════════════════════

        def _make_dock(title, obj_name, area, widget, closable=True):
            dock = QtWidgets.QDockWidget(title, self)
            dock.setObjectName(obj_name)
            dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
            features = QtWidgets.QDockWidget.DockWidgetMovable | \
                       QtWidgets.QDockWidget.DockWidgetFloatable
            if closable:
                features |= QtWidgets.QDockWidget.DockWidgetClosable
            dock.setFeatures(features)
            # Alle Mindestbreiten aufheben damit das Panel frei skalierbar ist
            widget.setMinimumSize(0, 0)
            dock.setMinimumSize(0, 0)
            # minimumSizeHint überschreiben damit Qt keine Mindestbreite erzwingt
            widget.minimumSizeHint = lambda: QtCore.QSize(0, 0)
            dock.minimumSizeHint   = lambda: QtCore.QSize(0, 0)
            dock.setWidget(widget)
            self.addDockWidget(area, dock)
            return dock

        # ── Dock 0: Einstellungen (KI-Quelle, Preset, Modus, API-Key) ────
        _cfg_widget = QtWidgets.QWidget()
        _cfg_l = QtWidgets.QVBoxLayout(_cfg_widget)
        _cfg_l.setContentsMargins(6, 6, 6, 6)
        _cfg_l.setSpacing(5)

        def _cfg_lbl(text):
            l = QtWidgets.QLabel(text)
            l.setStyleSheet(
                f"font-size:{schrift.pt(schrift.STUFE_XS)}pt; font-weight:bold;"
                " padding-top:6px; padding-bottom:2px; border-bottom:1px solid ;")
            return l

        _cfg_l.addWidget(_cfg_lbl("KI-QUELLE"))
        _r1 = QtWidgets.QHBoxLayout()
        _r1.setSpacing(3)
        _r1.addWidget(self._src_box, stretch=1)
        _rl_btn = QtWidgets.QPushButton("🔄")
        _rl_btn.setFixedSize(26, 24)
        _rl_btn.setToolTip("Modelle neu laden")
        _rl_btn.clicked.connect(self._refresh_models)
        _r1.addWidget(_rl_btn)
        _cfg_l.addLayout(_r1)

        _r1b = QtWidgets.QHBoxLayout()
        _r1b.setSpacing(3)
        _r1b.addWidget(QtWidgets.QLabel("Modell:"))
        _r1b.addWidget(self._model_box, stretch=1)
        _cfg_l.addLayout(_r1b)

        _cfg_l.addWidget(_cfg_lbl("TEMPERATUR"))
        _r2 = QtWidgets.QHBoxLayout()
        _r2.setSpacing(3)
        _r2.addWidget(QtWidgets.QLabel("T:"))
        _r2.addWidget(self._temp_box)
        _r2.addStretch()
        _cfg_l.addLayout(_r2)

        _cfg_l.addWidget(_cfg_lbl("MODUS"))
        _r3 = QtWidgets.QHBoxLayout()
        _r3.setSpacing(6)
        _r3.addWidget(self._btn_modus_anfaenger)
        _r3.addWidget(self._btn_modus_experte)
        _r3.addStretch()
        _cfg_l.addLayout(_r3)

        _cfg_l.addWidget(_cfg_lbl("API-SCHLÜSSEL"))
        _cfg_l.addWidget(self._key_anbieter)
        _cfg_l.addWidget(self._key_feld)

        _cfg_l.addStretch()

        _dock_cfg = _make_dock("⚙  Einstellungen", "dock_einstellungen",
                               QtCore.Qt.LeftDockWidgetArea, _cfg_widget)

        # ── Dock 1: KI (nur Input / Antwort / Kontext) ───────────────────
        ki_widget = QtWidgets.QWidget()
        ki_layout = QtWidgets.QVBoxLayout(ki_widget)
        ki_layout.setContentsMargins(4, 4, 4, 4)
        ki_layout.setSpacing(3)

        # KI-Input/Output Splitter
        _ki_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        # Suchfeld / KI-Input
        from snippet_controller import SnippetController as _TM

        def _alle_snippets() -> dict:
            from freecad_data import SNIPPETS as _SNIPS
            alle = {}
            for kat_dict in _SNIPS.values():
                alle.update(kat_dict)
            alle.update(getattr(self, "_user_snippets", {}))
            return alle

        # Preset-Leiste oben im KI-Panel
        _preset_zeile = QtWidgets.QHBoxLayout()
        _preset_zeile.setSpacing(3)
        _preset_zeile.addWidget(QtWidgets.QLabel("Preset:"))
        _preset_zeile.addWidget(self._preset_btn, stretch=1)
        ki_layout.addLayout(_preset_zeile)

        _input_w = QtWidgets.QWidget()
        _input_l = QtWidgets.QVBoxLayout(_input_w)
        _input_l.setContentsMargins(0, 0, 0, 0)
        _input_l.setSpacing(2)
        _input_hdr = QtWidgets.QHBoxLayout()
        _input_hdr.addWidget(QtWidgets.QLabel("🔍 KI-Input"))
        _input_hdr.addStretch()
        _btn_verlauf_reset = QtWidgets.QPushButton("🧹")
        _btn_verlauf_reset.setFixedSize(22, 18)
        _btn_verlauf_reset.setToolTip("Gesprächsverlauf zurücksetzen")
        _btn_verlauf_reset.setStyleSheet(
            f"QPushButton{{border:none;font-size:{schrift.pt(schrift.STUFE_LG)}pt;}}")
        _btn_verlauf_reset.clicked.connect(self._ki_verlauf_reset)
        _input_hdr.addWidget(_btn_verlauf_reset)

        _btn_sitzung_sp = QtWidgets.QPushButton("💾")
        _btn_sitzung_sp.setFixedSize(22, 18)
        _btn_sitzung_sp.setToolTip("Sitzung speichern\n(Chat-Verlauf + KI-Antwort als .json)")
        _btn_sitzung_sp.setStyleSheet(
            f"QPushButton{{border:none;font-size:{schrift.pt(schrift.STUFE_LG)}pt;}}")
        _btn_sitzung_sp.clicked.connect(self._sitzung_speichern)
        _input_hdr.addWidget(_btn_sitzung_sp)

        _btn_sitzung_ld = QtWidgets.QPushButton("📂")
        _btn_sitzung_ld.setFixedSize(22, 18)
        _btn_sitzung_ld.setToolTip("Sitzung laden\n(gespeicherten Chat-Verlauf wiederherstellen)")
        _btn_sitzung_ld.setStyleSheet(
            f"QPushButton{{border:none;font-size:{schrift.pt(schrift.STUFE_LG)}pt;}}")
        _btn_sitzung_ld.clicked.connect(self._sitzung_laden)
        _input_hdr.addWidget(_btn_sitzung_ld)
        _input_l.addLayout(_input_hdr)

        self.find_area = SnipCommandEdit(_alle_snippets)
        self.find_area.snip_gewaehlt.connect(self._on_snip_slash_cmd)
        self.find_area.setFont(QtGui.QFont("Courier New", 10))
        self.find_area.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        _opt = self.find_area.document().defaultTextOption()
        _opt.setAlignment(QtCore.Qt.AlignLeft)
        self.find_area.document().setDefaultTextOption(_opt)
        self.find_area.setStyleSheet(
            "QPlainTextEdit{font-family:'Courier New',monospace;"
            "border:1px solid; border-radius:3px;}"
            "QPlainTextEdit:focus{border:1px solid;}")
        theme.apply_input_bg_suche(self.find_area)
        self.find_area.setPlaceholderText(
            "Suchbegriff oder Codeblock …\n"
            "/ + Snippet-Name → Autocomplete")
        _hl_find = PythonHighlighter(self.find_area.document())
        QtCore.QTimer.singleShot(200, _hl_find.aktualisiere_theme)
        _input_l.addWidget(self.find_area)
        _ki_splitter.addWidget(_input_w)

        # KI-Antwort
        _output_w = QtWidgets.QWidget()
        _output_l = QtWidgets.QVBoxLayout(_output_w)
        _output_l.setContentsMargins(0, 0, 0, 0)
        _output_l.setSpacing(2)
        _output_l.addWidget(QtWidgets.QLabel("🤖 KI-Antwort"))
        self._ki_area = QtWidgets.QPlainTextEdit()
        self._ki_area.setFont(QtGui.QFont("Courier New", 10))
        self._ki_area.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        _opt2 = self._ki_area.document().defaultTextOption()
        _opt2.setAlignment(QtCore.Qt.AlignLeft)
        self._ki_area.document().setDefaultTextOption(_opt2)
        self._ki_area.setStyleSheet(
            "QPlainTextEdit{font-family:'Courier New',monospace; border:1px solid;}")
        theme.apply_input_bg_ki(self._ki_area)
        self._ki_area.setPlaceholderText("KI-Antwort erscheint hier …")
        _hl_ki = PythonHighlighter(self._ki_area.document())
        QtCore.QTimer.singleShot(200, _hl_ki.aktualisiere_theme)
        _output_l.addWidget(self._ki_area)
        _ki_splitter.addWidget(_output_w)

        # Kontext
        _kontext_w = QtWidgets.QWidget()
        _kontext_w.setMinimumHeight(80)
        _kontext_l = QtWidgets.QVBoxLayout(_kontext_w)
        _kontext_l.setContentsMargins(0, 0, 0, 0)
        _kontext_l.setSpacing(2)
        _kontext_l.addWidget(QtWidgets.QLabel("📌 Projekt-Kontext"))
        self._kontext = QtWidgets.QPlainTextEdit()
        self._kontext.setFont(QtGui.QFont("Courier New", 10))
        self._kontext.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        _opt3 = self._kontext.document().defaultTextOption()
        _opt3.setAlignment(QtCore.Qt.AlignLeft)
        _opt3.setWrapMode(QtGui.QTextOption.WordWrap)
        self._kontext.document().setDefaultTextOption(_opt3)
        theme.apply_input_bg_kontext(self._kontext)
        self._kontext.setPlaceholderText(
            "Kurze Beschreibung deines Projekts …\n"
            "Wird bei jedem KI-Aufruf mitgeschickt.")
        self._kontext.setPlainText(lade_kontext())
        self._kontext.textChanged.connect(
            lambda: speichere_kontext(self._kontext.toPlainText()))
        _kontext_l.addWidget(self._kontext)
        _ki_splitter.addWidget(_kontext_w)

        _ki_splitter.setSizes([260, 220, 100])
        ki_layout.addWidget(_ki_splitter, stretch=1)

        _dock_ki = _make_dock("🤖  KI", "dock_ki",
                              QtCore.Qt.LeftDockWidgetArea, ki_widget)

        # ── Dock 2: Aktionen ─────────────────────────────────────────────
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
            lbl.setStyleSheet(
                f"font-size:{schrift.pt(schrift.STUFE_XS)}pt; font-weight:bold;"
                " padding-top:8px; padding-bottom:2px; border-bottom:1px solid ;")
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

        _abschnitt("SUCHFELD / KI-INPUT")
        _agrid(
            _abtn("📥  Laden",     "Markierten Text ins Suchfeld laden",    self._copy_from_editor),
            _abtn("🔍  Markieren", "Suchfeld-Inhalt im Editor markieren",   self._find_and_highlight),
            _abtn("🗑  Leeren",    "Suchfeld leeren", lambda: self.find_area.clear()),
        )

        _abschnitt("KI-AKTIONEN")
        self._btn_ki        = _abtn("🤖  Fragen",   "KI befragen",                        self._ki_fragen,                  h=30)
        _btn_analyse        = _abtn("🔎  Analyse",  "Code automatisch analysieren",        self._auto_analyse)
        self._plan_modus_aktiv = False
        self._btn_plan = QtWidgets.QPushButton("🔍  Plan")
        self._btn_plan.setCheckable(True)
        self._btn_plan.setToolTip(
            "Plan-Modus: Code vor dem Ersetzen prüfen\n"
            "Wenn aktiv → zeigt neuen Code zur Bestätigung bevor er eingefügt wird")
        self._btn_plan.setFixedHeight(22)
        self._btn_plan.toggled.connect(self._plan_modus_umschalten)
        self._btn_ersetzen  = _abtn("✅  Ersetzen", "Block durch KI-Antwort ersetzen",     self._ersetzen_und_speichern,     enabled=False)
        self._btn_einfuegen = _abtn("➕  Einfügen", "KI-Antwort nach Block einfügen",      self._einfuegen_nach_fundstelle,  enabled=False)
        def _vorschau_mit_ki_code():
            ki_code = self._ki_area.toPlainText().strip()
            if ki_code and not ki_code.startswith("# ⏳") and not ki_code.startswith("🧠"):
                self.vorschau_starten(code=ki_code)
            else:
                self.vorschau_starten()
        _btn_vorschau       = _abtn("👁  Vorschau", "KI-Code direkt in FreeCAD ausführen und 3D-Viewport anzeigen", _vorschau_mit_ki_code)
        _agrid(self._btn_ki, _btn_analyse, self._btn_plan, self._btn_ersetzen, self._btn_einfuegen, _btn_vorschau)

        _abschnitt("DATEI")
        _agrid(
            _abtn("💾  Speichern",   "Datei speichern",              self.speichern),
            _abtn("💾✕  Schließen", "Speichern & Schließen",        self.speichern_und_schliessen),
            _abtn("↺  Neu laden",   "Letzten Speicherstand laden",   self.neu_laden),
            _abtn("↩  Backup",      "Backup wiederherstellen",       self._backup_wiederherstellen),
        )

        _abschnitt("EDITOR")
        _fmt_lbl = "✨  autopep8" if _HAS_AUTOPEP8 else "🪄  Einrückung"
        _agrid(
            _abtn("☰  Alles",    "Alles markieren",  self.alles_auswaehlen),
            _abtn("✕  Löschen",  "Auswahl löschen",  self.loeschen_auswahl),
            _abtn(_fmt_lbl,      "Code formatieren", self._formatieren),
            _abtn("❓  Hilfe",   "Hilfe öffnen",      self._zeige_hilfe),
        )

        _abschnitt("BIBLIOTHEK")
        _agrid(
            _abtn("📚  Speichern",   "In Bibliothek speichern",
                  lambda: self.bibliothek_speichern(code=self._get_editor_code(), ki_generiert=False)),
            _abtn("🤖📚  KI→Bib",   "KI-Antwort in Bibliothek",
                  lambda: self.bibliothek_speichern(code=self._ki_area.toPlainText(), ki_generiert=True)),
        )

        _akt_l.addStretch()

        _dock_akt = _make_dock("⚙  Aktionen", "dock_aktionen",
                               QtCore.Qt.RightDockWidgetArea, _akt_scroll)

        # ── Dock 3: Snippets ──────────────────────────────────────────────
        _dock_snip = _make_dock("📦  Snippets", "dock_snippets",
                                QtCore.Qt.LeftDockWidgetArea,
                                self._baue_snippet_tab())
        self.tabifyDockWidget(_dock_ki, _dock_snip)

        # ── Dock 4: API-Hinweise ──────────────────────────────────────────
        _dock_hints = _make_dock("💡  API-Hints", "dock_hints",
                                 QtCore.Qt.LeftDockWidgetArea,
                                 self._baue_hints_tab())
        self.tabifyDockWidget(_dock_ki, _dock_hints)

        # ── Dock 5: Dateibrowser ──────────────────────────────────────────
        _dock_files = _make_dock("📂  Dateien", "dock_dateien",
                                 QtCore.Qt.LeftDockWidgetArea,
                                 self._baue_dateibrowser_tab())
        self.tabifyDockWidget(_dock_ki, _dock_files)

        # ── Dock 6: KI-Werkzeuge ──────────────────────────────────────────
        _dock_kitools = _make_dock("🛠  KI-Tools", "dock_kitools",
                                   QtCore.Qt.RightDockWidgetArea,
                                   self._baue_ki_tools_tab())
        self.tabifyDockWidget(_dock_akt, _dock_kitools)

        # ── Dock 7: Bibliothek ────────────────────────────────────────────
        _dock_bib = _make_dock("📚  Bibliothek", "dock_bibliothek",
                               QtCore.Qt.RightDockWidgetArea,
                               self._baue_bibliothek_tab())
        self.tabifyDockWidget(_dock_akt, _dock_bib)

        # ── Dock 8: FreeCAD Helfer (Legastheniker / Einsteiger) ──────────────
        self._helfer_panel = FreecadHelferPanel()
        _dock_helfer = _make_dock("🔧  Helfer", "dock_helfer",
                                  QtCore.Qt.RightDockWidgetArea,
                                  self._helfer_panel,
                                  closable=True)
        self.tabifyDockWidget(_dock_akt, _dock_helfer)
        _dock_helfer.hide()  # Standardmäßig geschlossen

        # Interaktiver Assistent-Dock
        self._assistent_panel = AssistentPanel(self)
        self._assistent_panel.widget_blinken.connect(self._widget_blinken)
        _dock_assistent = _make_dock("🤝  Assistent", "dock_assistent",
                                     QtCore.Qt.RightDockWidgetArea,
                                     self._assistent_panel,
                                     closable=True)
        self.tabifyDockWidget(_dock_akt, _dock_assistent)
        _dock_assistent.hide()

        # Fehler-Panel als Dock unten
        fehler_panel_widget = QtWidgets.QWidget()
        fp = QtWidgets.QVBoxLayout(fehler_panel_widget)
        fp.setContentsMargins(0, 0, 0, 0)
        fp.setSpacing(0)
        self._fehler_inhalt = self._baue_fehler_panel()
        self._fehler_inhalt.setVisible(True)
        fp.addWidget(self._fehler_inhalt)
        self._btn_fehler_toggle = QtWidgets.QPushButton()  # Dummy, Toggle per Dock-Titel
        self._btn_fehler_toggle.hide()
        _dock_fehler = _make_dock("⚠  Fehler-Übersetzer", "dock_fehler",
                                  QtCore.Qt.BottomDockWidgetArea,
                                  fehler_panel_widget)
        _dock_fehler.hide()   # Standard: zugeklappt

        def _sandbox_toggle_cb(sandbox_aktiv: bool):
            if sandbox_aktiv:
                _dock_fehler.show()
        self._fehler_inhalt.setze_sandbox_toggle_cb(_sandbox_toggle_cb)

        def _sandbox_run():
            import re as _re
            code = self._ki_area.toPlainText().strip()
            code = _re.sub(r"```python|```", "", code).strip()
            if code:
                self._fehler_inhalt._geladener_code = code
                self._fehler_inhalt._sandbox_ausfuehren()
            else:
                self._fehler_inhalt._sb_status.setText("⚠ KI-Antwort ist leer")

        self._fehler_inhalt._btn_sb_run.clicked.disconnect()
        self._fehler_inhalt._btn_sb_run.clicked.connect(lambda: _sandbox_run())

        # Kompatibilität: _rechte_tabs als Dummy-QStackedWidget
        self._rechte_tabs = QtWidgets.QStackedWidget()
        self._rechte_tabs.hide()

        self._tab_oeffnen(pfad)

        # WerkzeugLeiste nach _tab_oeffnen erstellen (braucht self._editor)
        self._werkzeug_leiste = WerkzeugLeiste(self._editor)

        # ── Alle Docks standardmäßig versteckt → Editor bekommt volle Breite
        _dock_werkzeuge = _make_dock("🔧  Werkzeuge", "dock_werkzeuge",
                                     QtCore.Qt.RightDockWidgetArea,
                                     self._werkzeug_leiste)
        self.tabifyDockWidget(_dock_akt, _dock_werkzeuge)

        # ── Barrierefreiheits-Dock ────────────────────────────────────────────
        self._bf_panel = BarrierefreiheitPanel()
        self._bf_panel.geaendert.connect(self._on_barrierefreiheit)
        _dock_bf = _make_dock("♿  Barrierefreiheit", "dock_barrierefreiheit",
                              QtCore.Qt.LeftDockWidgetArea, self._bf_panel)

        for _d in (_dock_cfg, _dock_ki, _dock_snip, _dock_hints, _dock_files,
                   _dock_kitools, _dock_akt, _dock_bib, _dock_werkzeuge,
                   _dock_fehler, _dock_bf):
            _d.hide()

        # ── Panel-Toolbar: Toggle-Buttons komplett neu ────────────────────
        _tb = QtWidgets.QToolBar("Panels", self)
        _tb.setObjectName("toolbar_panels")
        _tb.setMovable(False)
        _tb.setFloatable(False)
        _tb.setStyleSheet("QToolBar { border: none; spacing: 2px; padding: 2px 4px; }")
        self.addToolBar(QtCore.Qt.TopToolBarArea, _tb)

        _fs = schrift.pt(schrift.STUFE_BASE)

        # ── Intelligente Panel-Steuerung ──────────────────────────────────
        _L = QtCore.Qt.LeftDockWidgetArea
        _R = QtCore.Qt.RightDockWidgetArea
        _B = QtCore.Qt.BottomDockWidgetArea
        _GEGENUEBER = {_L: _R, _R: _L, _B: _B}

        def _belegt(area) -> bool:
            """True wenn die Area bereits sichtbare, nicht-schwebende Panels hat."""
            return any(
                d.isVisible() and not d.isFloating()
                and self.dockWidgetArea(d) == area
                for d in self.findChildren(QtWidgets.QDockWidget)
            )

        def _zeige_panel(dock, standard_area):
            """Panel einblenden — Fehler immer unten, alle anderen links/rechts intelligent."""
            # Fehler-Panel: immer unten, keine Ausnahme
            if standard_area == _B:
                if self.dockWidgetArea(dock) != _B:
                    self.addDockWidget(_B, dock)
                dock.show()
                dock.raise_()
                return

            ziel = standard_area
            if _belegt(ziel):
                gegenseite = _GEGENUEBER[ziel]
                # Gegenseite auch belegt → als Tab zum ersten Panel der Gegenseite
                if _belegt(gegenseite):
                    vorhandene = [
                        d for d in self.findChildren(QtWidgets.QDockWidget)
                        if d.isVisible() and not d.isFloating()
                        and self.dockWidgetArea(d) == gegenseite
                        and d is not dock
                    ]
                    if vorhandene:
                        self.tabifyDockWidget(vorhandene[0], dock)
                        dock.show()
                        dock.raise_()
                        return
                ziel = gegenseite
            if self.dockWidgetArea(dock) != ziel:
                self.addDockWidget(ziel, dock)
            dock.show()
            dock.raise_()

        def _panel_btn(dock, icon_text, label, standard_area=_L):
            btn = QtWidgets.QPushButton(icon_text)
            btn.setToolTip(label)
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.setFixedHeight(26)
            btn.setFixedWidth(32)
            btn.setStyleSheet(
                f"QPushButton {{ border:none; border-radius:3px; padding:2px 4px;"
                f" font-size:{_fs}pt; }}"
                f"QPushButton:checked {{ font-weight:bold; border:1px solid; }}"
                f"QPushButton:hover {{ border:1px solid; }}"
            )
            def _on_click(checked, d=dock, a=standard_area):
                if checked:
                    _zeige_panel(d, a)
                else:
                    d.hide()
            btn.toggled.connect(_on_click)
            dock.visibilityChanged.connect(lambda vis, b=btn: b.setChecked(vis))
            _tb.addWidget(btn)
            return btn

        _btn_hilfe = QtWidgets.QPushButton("❓  Hilfe")
        _btn_hilfe.setFixedHeight(26)
        _btn_hilfe.setStyleSheet(theme.STY_TAB_BTN())
        _btn_hilfe.clicked.connect(self._zeige_hilfe)
        _tb.addWidget(_btn_hilfe)
        _tb.addSeparator()

        _panel_btn(_dock_cfg,      "⚙",  "Einst.",  _L)
        _panel_btn(_dock_ki,       "🤖", "KI",       _L)
        _panel_btn(_dock_akt,      "🎛", "Akt.",     _R)
        _panel_btn(_dock_snip,     "📦", "Snip",     _L)
        _panel_btn(_dock_hints,    "💡", "API",      _L)
        _panel_btn(_dock_files,    "📂", "Dat.",     _L)
        _panel_btn(_dock_kitools,  "🛠", "Tools",    _R)
        _panel_btn(_dock_bib,      "📚", "Bib.",     _R)
        _panel_btn(_dock_werkzeuge,"🔧", "Werkz.",   _R)
        _panel_btn(_dock_fehler,   "⚠",  "Fehler",   _B)
        _panel_btn(_dock_bf,       "♿", "Zugang",   _L)
        _panel_btn(_dock_helfer,   "🔧", "Helfer",   _R)
        _panel_btn(_dock_assistent,"🤝", "Assist.",  _R)

        # ── Dock-Layout nach dem ersten Zeigen wiederherstellen ──────────
        import json as _json
        _STATE_DATEI = os.path.join(
            os.path.expanduser("~"), ".ki_makro_editor_layout.json")
        self._layout_state_datei = _STATE_DATEI

        # Version hochzählen wenn Docks/Panels sich ändern — verhindert
        # Qt-Segfault durch inkompatibles gespeichertes Layout
        _LAYOUT_VERSION = "v5"

        _GUARD_DATEI = os.path.join(
            os.path.expanduser("~"), ".ki_makro_editor_restore_guard")

        def _lade_layout():
            try:
                # Crash-Guard: restoreState kann einen C++-Segfault auslösen
                # der nicht von Python abgefangen werden kann. Wenn die Guard-
                # Datei noch existiert, ist der letzte Restore abgestürzt →
                # Layout-Datei löschen und Guard entfernen.
                if os.path.exists(_GUARD_DATEI):
                    os.remove(_GUARD_DATEI)
                    try:
                        os.remove(_STATE_DATEI)
                    except OSError:
                        pass
                    return
                with open(_STATE_DATEI, "r", encoding="utf-8") as _sf:
                    gespeichert = _json.load(_sf)
                if not isinstance(gespeichert, dict):
                    return
                if gespeichert.get("version") != _LAYOUT_VERSION:
                    return
                _state = gespeichert["state"]
                # Guard setzen VOR dem kritischen Qt-Aufruf
                with open(_GUARD_DATEI, "w", encoding="utf-8") as _gf:
                    _gf.write("restore_in_progress")
                self.restoreState(QtCore.QByteArray.fromBase64(
                    _state.encode("ascii")))
                # Erfolg: Guard wieder löschen
                if os.path.exists(_GUARD_DATEI):
                    os.remove(_GUARD_DATEI)
            except Exception:
                if os.path.exists(_GUARD_DATEI):
                    os.remove(_GUARD_DATEI)

        QtCore.QTimer.singleShot(0, _lade_layout)

        self._baum_timer = QtCore.QTimer(self)
        self._baum_timer.setSingleShot(True)
        self._baum_timer.setInterval(500)
        self._editor.textChanged.connect(self._baum_timer.start)
        self._baum_timer.timeout.connect(
            lambda: self._werkzeug_leiste.aktualisiere_code_baum(
                self._editor.toPlainText()))
        QtCore.QTimer.singleShot(0, lambda: self._werkzeug_leiste.aktualisiere_code_baum(
            self._editor.toPlainText()))

        self._refresh_models()
        self._init_selektion_cache()
        self._vorschau_init()


    # ══ Öffentliche API ════════════════════════════════════════════════════
    def insert_snippet(self, code: str):
        """Fügt einen Snippet an der aktuellen Cursor-Position ein."""
        c = self._editor.textCursor()
        if not c.hasSelection() and c.columnNumber() > 0:
            c.movePosition(QtGui.QTextCursor.EndOfBlock)
            c.insertText("\n")
        c.insertText(code)
        self._editor.setTextCursor(c)
        self._editor.setFocus()
        self._set_status(f"📦 Snippet eingefügt ({len(code.splitlines())} Zeilen)")

    def gehe_zu_zeile(self, zeilen_nr: int):
        """Springt zur Zeilennummer (1-basiert) und hebt die Zeile hervor."""
        if self._editor is None:
            return
        block = self._editor.document().findBlockByLineNumber(zeilen_nr - 1)
        if not block.isValid():
            return
        c = QtGui.QTextCursor(block)
        c.select(QtGui.QTextCursor.LineUnderCursor)
        self._editor.setTextCursor(c)
        self._editor.centerCursor()
        self._editor.setFocus()
        self._set_status(f"📍 Zeile {zeilen_nr}")

    def such_und_markiere(self, suchtext: str) -> bool:
        """Suchfeld befüllen und vollständigen Block im Editor markieren.
        Gibt True zurück wenn der Block gefunden wurde."""
        if self._editor is None:
            return False
        self.find_area.setPlainText(suchtext)
        if self._find_in_editor():
            self._btn_ersetzen.setEnabled(True)
            self._set_status("🔍 Gefunden und markiert")
            self._editor.centerCursor()
            return True
        return False

    # ══ Hilfsmethoden ══════════════════════════════════════════════════════
    def _key_anbieter_id(self) -> str:
        return {
            "Anthropic (Claude)": "anthropic",
            "OpenAI (ChatGPT)":   "openai",
            "GitHub Copilot":     "github",
            "OpenRouter":         "openrouter",
            "DeepSeek":           "deepseek",
            "Google Gemini":      "gemini",
            "Groq":               "groq",
            "Mistral":            "mistral",
            "Together AI":        "together",
            "Hugging Face":       "huggingface",
            "xAI (Grok)":         "xai",
            "Fireworks AI":       "fireworks",
            "Moonshot":           "moonshot",
            "Qwen (Alibaba)":     "qwen",
            "Cohere":             "cohere",
            "SambaNova":          "sambanova",
            "MiniMax":            "minimax",
            "Llama API":          "llama",
        }.get(self._key_anbieter.currentText(), "anthropic")

    def _update_cursor_info(self):
        c     = self._editor.textCursor()
        zeile = c.blockNumber() + 1
        spalte = c.columnNumber() + 1
        self._status.setText(f"Zeile {zeile}, Spalte {spalte}")

    @staticmethod
    def _normalize_newlines(text: str) -> str:
        return text.replace("\u2029", "\n")

    def _markiere_geaendert(self):
        """Markiert den aktuellen Tab als geändert (via Sender-Erkennung)."""
        # Sender-Editor ermitteln
        sender_doc = self.sender()
        editor_ref = None
        for tab in self._tabs:
            if tab["editor"].document() is sender_doc:
                editor_ref = tab["editor"]
                break
        # Richtigen Tab-Index finden
        for i, tab in enumerate(self._tabs):
            if tab["editor"] is editor_ref and not tab["geaendert"]:
                tab["geaendert"] = True
                name = os.path.basename(tab["pfad"])
                self._editor_tab_widget.setTabText(i, f"{name}  *")
                if i == self._editor_tab_widget.currentIndex():
                    self._geaendert = True
                    self.setWindowTitle(f"Makro-Editor  –  {name}  *")
                break

    def _set_status(self, text, ms=4000):
        self._status.setText(text)
        if ms > 0:
            QtCore.QTimer.singleShot(ms, self._loesche_status)

    def _loesche_status(self):
        try:
            self._status.setText("")
        except RuntimeError:
            pass

    # ══ Dateioperationen ══════════════════════════════════════════════════════
    def _baue_preset_menu(self):
        """Baut das Preset-Menü aus KI_PRESET_KATEGORIEN auf.

        Jede Kategorie wird zu einem Untermenü. Die ★-Schnell-Kategorie
        erscheint zusätzlich direkt oben im Hauptmenü für schnellen Zugriff.
        """
        self._preset_menu.clear()

        # ── Schnell-Presets direkt im Hauptmenü (kein Untermenü nötig) ───
        schnell = KI_PRESET_KATEGORIEN.get("★ Schnell", {})
        for name, prompt in schnell.items():
            action = self._preset_menu.addAction(f"★ {name}")
            action.triggered.connect(
                lambda checked, n=name, p=prompt: self._preset_gewaehlt(n, p))

        if schnell:
            self._preset_menu.addSeparator()

        # ── Alle anderen Kategorien als Untermenüs ────────────────────────
        for kat, eintraege in KI_PRESET_KATEGORIEN.items():
            if kat == "★ Schnell":
                continue
            if not eintraege:
                continue
            sub = self._preset_menu.addMenu(kat)
            for name, prompt in eintraege.items():
                action = sub.addAction(name)
                action.triggered.connect(
                    lambda checked, n=name, p=prompt, k=kat: self._preset_gewaehlt(
                        f"{k}: {n}", p))

    def _preset_gewaehlt(self, name: str, prompt: str):
        """Wird aufgerufen wenn ein Preset aus dem Menü gewählt wird."""
        self._preset_btn.setText(name)
        # Kompatibilität: versteckte ComboBox synchron halten
        # damit ki_controller._preset_box.currentText() den richtigen Wert gibt
        idx = self._preset_box.findText(name)
        if idx >= 0:
            self._preset_box.setCurrentIndex(idx)
        else:
            # Nicht gefunden (z.B. FC_KI_PRESETS) — direkt einfügen
            self._preset_box.addItem(name)
            self._preset_box.setCurrentText(name)

    def _get_preset_prompt(self) -> str:
        """Gibt den Prompt des aktuell gewählten Presets zurück."""
        return KI_PRESETS.get(self._preset_btn.text(), "")

    def speichern(self):
        idx = self._editor_tab_widget.currentIndex()
        if idx < 0 or idx >= len(self._tabs):
            return
        tab = self._tabs[idx]
        try:
            self._watcher_pause = True
            with open(tab["pfad"], "w", encoding="utf-8") as f:
                f.write(tab["editor"].toPlainText())
            tab["geaendert"] = False
            self._geaendert  = False
            name = os.path.basename(tab["pfad"])
            self._editor_tab_widget.setTabText(idx, name)
            self.setWindowTitle(f"Makro-Editor  –  {name}")
            self._set_status("✔  Gespeichert")
            QtCore.QTimer.singleShot(500, lambda: setattr(self, "_watcher_pause", False))
            if tab["pfad"] not in self._datei_watcher.files():
                self._datei_watcher.addPath(tab["pfad"])
        except Exception as e:
            self._watcher_pause = False
            QtWidgets.QMessageBox.critical(
                self, "Fehler beim Speichern", uebersetze_fehler(e))

    def speichern_und_schliessen(self):
        self.speichern()
        if not self._geaendert:
            self._tab_schliessen(self._editor_tab_widget.currentIndex())

    def neu_laden(self):
        idx = self._editor_tab_widget.currentIndex()
        if idx < 0 or idx >= len(self._tabs):
            return
        tab = self._tabs[idx]
        try:
            with open(tab["pfad"], "r", encoding="utf-8") as f:
                tab["editor"].setPlainText(f.read())
            tab["geaendert"] = False
            self._geaendert  = False
            name = os.path.basename(tab["pfad"])
            self._editor_tab_widget.setTabText(idx, name)
            self.setWindowTitle(f"Makro-Editor  –  {name}")
            self._set_status("↺  Neu geladen")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Fehler beim Laden", uebersetze_fehler(e))

    def _datei_extern_geaendert(self, pfad: str):
        """Wird aufgerufen wenn die Datei extern (z.B. durch KI oder anderen Editor) geändert wurde."""
        if self._watcher_pause:
            return
        # Watcher erneut registrieren (Linux entfernt den Watch nach Änderung)
        QtCore.QTimer.singleShot(100, lambda: self._datei_watcher.addPath(self._pfad))
        self._set_status(
            "⚠  Datei wurde extern geändert  –  [↺ Neu laden] um zu aktualisieren",
            ms=0)   # ms=0 = bleibt stehen bis nächste Aktion

    def alles_auswaehlen(self):
        self._editor.selectAll()
        self._editor.setFocus()

    def loeschen_auswahl(self):
        c = self._editor.textCursor()
        if c.hasSelection():
            c.removeSelectedText()
        elif QtWidgets.QMessageBox.question(
            self, "Leeren", "Gesamten Inhalt löschen?",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            self._editor.clear()

    # ══ Schnellsuche ═══════════════════════════════════════════════════════
    def _toggle_suche(self):
        vis = not self._suche_widget.isVisible()
        self._suche_widget.setVisible(vis)
        if vis:
            sel = self._normalize_newlines(
                self._editor.textCursor().selectedText()).strip()
            if sel and "\n" not in sel:
                self._suche_feld.setText(sel)
            self._suche_feld.selectAll()
            self._suche_feld.setFocus()

    def _suche_weiter(self):
        if not self._editor.find(self._suche_feld.text()):
            c = self._editor.textCursor()
            c.movePosition(QtGui.QTextCursor.Start)
            self._editor.setTextCursor(c)
            if not self._editor.find(self._suche_feld.text()):
                self._set_status("⚠  Begriff nicht gefunden")

    def _ersetzen_text(self):
        c = self._editor.textCursor()
        if c.hasSelection() and self._normalize_newlines(c.selectedText()) == self._suche_feld.text():
            c.insertText(self._ersatz_feld.text())
            self._suche_weiter()

    def _alles_ersetzen(self):
        alt, neu = self._suche_feld.text(), self._ersatz_feld.text()
        if not alt:
            return
        text = self._editor.toPlainText()
        n = text.count(alt)
        if n:
            self._editor.setPlainText(text.replace(alt, neu))
            self._set_status(f"✔  {n}× ersetzt")
        else:
            self._set_status("⚠  Begriff nicht gefunden")

    # ══ Formatieren ════════════════════════════════════════════════════════
    def _formatieren(self):
        text = self._editor.toPlainText()
        if _HAS_AUTOPEP8:
            # autopep8 nur für Leerzeichen/Komma/Operator-Abstände nutzen,
            # NICHT für Einrückung (aggressive=0) — Einrückung macht _smart_reindent
            fixed = autopep8.fix_code(text, options={"aggressive": 0,
                                                      "ignore": ["E1", "W1"]})
            fixed = self._smart_reindent(fixed)
            self._set_status("✨ Formatiert (autopep8 + Smart-Einrückung)")
        else:
            fixed = self._smart_reindent(text)
            self._set_status("🪄 Smart-Einrückung angewendet")
        self._editor.setPlainText(fixed)

    @staticmethod
    def _smart_reindent(text: str) -> str:
        """
        Formatiert den gesamten Code mit denselben Einrück-Regeln wie
        die Live-Einrückung beim Schreiben (editor_widgets.py):

        GRUPPE 1 – EINRÜCKEN: Zeilen die auf ':' enden
        GRUPPE 2 – AUSRÜCKEN nach: pass, return, break, continue, raise, yield
        GRUPPE 3 – BLOCK-FORT: except, else, elif, finally, case
                   → gehören zur gleichen Ebene wie ihr Opener

        Erhält Leerzeilen und Kommentare korrekt.
        """
        _AUSRUECK_KW = frozenset({
            "pass", "return", "break", "continue", "raise", "yield"})
        _BLOCK_FORT_KW = frozenset({
            "except", "else", "elif", "finally", "case"})
        _INDENT = "    "  # 4 Leerzeichen

        out   = []
        lvl   = 0
        naechste_reduzieren = False  # nach AUSRUECK_KW eine Ebene runter

        for zeile in text.splitlines():
            s = zeile.strip()

            # Leerzeilen unverändert übernehmen
            if not s:
                out.append("")
                naechste_reduzieren = False
                continue

            # AUSRUECK_KW der vorherigen Zeile: jetzt eine Ebene runter
            if naechste_reduzieren:
                lvl = max(0, lvl - 1)
                naechste_reduzieren = False

            # BLOCK_FORT_KW: gehört zur gleichen Ebene wie der Opener
            erstes = s.split()[0].rstrip(":(")
            if erstes in _BLOCK_FORT_KW:
                einrueck_lvl = max(0, lvl - 1)
            else:
                einrueck_lvl = lvl

            out.append(_INDENT * einrueck_lvl + s)

            # Nach dieser Zeile einrücken wenn sie auf ':' endet
            if s.rstrip().endswith(":"):
                lvl = einrueck_lvl + 1
            else:
                lvl = einrueck_lvl

            # AUSRUECK_KW: nächste Zeile eine Ebene zurück
            if erstes in _AUSRUECK_KW:
                naechste_reduzieren = True

        return "\n".join(out)

    # ══ Kern-Workflow: Suchfeld ════════════════════════════════════════════
    def _copy_from_editor(self):
        c = self._editor.textCursor()
        if c.hasSelection():
            text = self._normalize_newlines(c.selectedText())
            self.find_area.setPlainText(text)
            self._set_status(f"📥 {len(text.splitlines())} Zeile(n) ins Suchfeld geladen")
        else:
            text = self._editor.toPlainText()
            self.find_area.setPlainText(text)
            self._set_status("📥 Gesamter Dateiinhalt ins Suchfeld geladen")
        self.find_area.setFocus()

    def _find_in_editor(self) -> bool:
        needle_lines = [
            l.strip()
            for l in self.find_area.toPlainText().splitlines()
            if l.strip()
        ]
        if not needle_lines:
            return False

        full_text = self._normalize_newlines(self._editor.toPlainText())

        # ── Einzeilig → einfache case-insensitive Textsuche ──────────────
        if len(needle_lines) == 1:
            needle = needle_lines[0]
            pos = full_text.lower().find(needle.lower())
            if pos >= 0:
                cur = self._editor.textCursor()
                cur.setPosition(pos)
                cur.setPosition(pos + len(needle), QtGui.QTextCursor.KeepAnchor)
                self._editor.setTextCursor(cur)
                self._editor.setFocus()
                return True
            return False

        # ── Mehrzeilig → normalisierter Zeilenvergleich ──────────────────
        def _norm(line):
            return "".join(_RE_WORD_CHARS.findall(line))

        norm_needle = [_norm(l) for l in needle_lines]
        haystack    = full_text.splitlines()
        norm_h      = [_norm(l) for l in haystack]
        count       = len(norm_needle)

        for idx in range(len(norm_h) - count + 1):
            if norm_h[idx:idx + count] == norm_needle:
                start = sum(len(haystack[i]) + 1 for i in range(idx))
                end   = sum(len(haystack[i]) + 1 for i in range(idx + count)) - 1
                cursor = self._editor.textCursor()
                cursor.setPosition(start)
                cursor.setPosition(
                    min(end, len(full_text)),
                    QtGui.QTextCursor.KeepAnchor)
                self._editor.setTextCursor(cursor)
                self._editor.setFocus()
                return True
        return False

    def _find_and_highlight(self):
        if self._find_in_editor():
            self._set_status("🔍 Gefunden und markiert → ✅ Ersetzen & speichern")
            self._btn_ersetzen.setEnabled(True)
        else:
            suchtext = self.find_area.toPlainText().strip()
            if not suchtext:
                self._set_status("❌ Suchfeld ist leer")
                return
            dateiname = os.path.basename(self._pfad) if self._pfad else "diese Datei"
            antwort = QtWidgets.QMessageBox.question(
                self,
                "Nicht gefunden",
                f'"{suchtext[:60]}{"…" if len(suchtext) > 60 else ""}"\n\n'
                f'wurde in  {dateiname}  nicht gefunden.\n\n'
                f'Soll in allen anderen Makro-Dateien gesucht werden?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes,
            )
            if antwort == QtWidgets.QMessageBox.Yes:
                self._set_status("🔍 Suche in allen Makros …")
                self.such_in_dateien.emit(suchtext)
            else:
                self._set_status("❌ Nicht gefunden")

    # ══ Einrückungs-Hilfsmethoden ══════════════════════════════════════════
    @staticmethod
    def _reindent_block(code: str, target_indent: str) -> str:
        """Passt die Einrückung eines Code-Blocks an target_indent an."""
        code = code.replace("\t", "    ")
        zeilen    = code.splitlines()
        non_empty = [l for l in zeilen if l.strip()]
        base      = min((len(l) - len(l.lstrip()) for l in non_empty), default=0)
        return "\n".join(
            "" if not l.strip() else target_indent + l[base:]
            for l in zeilen
        )

    @staticmethod
    def _erste_einrueckung(text: str) -> str:
        for line in text.splitlines():
            if line.strip():
                return line[:len(line) - len(line.lstrip())]
        return ""

    # ══ Ersetzen / Einfügen ════════════════════════════════════════════════
    # ══ Selektion-Cache (Fix: Fokus-Verlust beim Button-Klick) ════════════
    def _init_selektion_cache(self):
        """Initialisiert den Cache – Signal-Connect erfolgt in _tab_gewechselt."""
        self._letzter_editor_cursor = None

    def _on_editor_selection_changed(self):
        c = self._editor.textCursor()
        if c.hasSelection():
            self._letzter_editor_cursor = QtGui.QTextCursor(c)

    def _stelle_selektion_wieder_her(self) -> bool:
        """Stellt letzte Selektion wieder her falls Fokus-Wechsel sie gelöscht hat."""
        c = self._editor.textCursor()
        if c.hasSelection():
            return True
        if getattr(self, "_letzter_editor_cursor", None) and \
                self._letzter_editor_cursor.hasSelection():
            self._editor.setTextCursor(self._letzter_editor_cursor)
            return True
        return False

    def _plan_modus_umschalten(self, aktiv: bool):
        self._plan_modus_aktiv = aktiv
        if aktiv:
            self._btn_plan.setText("🔍  Plan  ✓")
            self._set_status("🔍 Plan-Modus aktiv — Code wird vor dem Ersetzen angezeigt")
        else:
            self._btn_plan.setText("🔍  Plan")
            self._set_status("Plan-Modus deaktiviert")

    def _plan_dialog_zeigen(self, neu_code: str) -> bool:
        """Zeigt den neuen Code zur Bestätigung. Gibt True zurück wenn der Nutzer bestätigt."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("🔍 Plan-Modus — Code prüfen")
        dlg.resize(700, 450)

        lay = QtWidgets.QVBoxLayout(dlg)
        lay.setSpacing(8)

        info = QtWidgets.QLabel(
            "Die KI möchte folgenden Code einfügen. Bitte prüfen und bestätigen:")
        info.setWordWrap(True)
        lay.addWidget(info)

        vorschau = QtWidgets.QPlainTextEdit()
        vorschau.setPlainText(neu_code)
        vorschau.setReadOnly(True)
        vorschau.setFont(QtGui.QFont("Courier New", 10))
        lay.addWidget(vorschau, 1)

        btns = QtWidgets.QHBoxLayout()
        btn_ok  = QtWidgets.QPushButton("✅  Ausführen")
        btn_ab  = QtWidgets.QPushButton("❌  Abbrechen")
        btn_ok.setFixedHeight(30)
        btn_ab.setFixedHeight(30)
        btn_ok.clicked.connect(dlg.accept)
        btn_ab.clicked.connect(dlg.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_ab)
        lay.addLayout(btns)

        return dlg.exec_() == QtWidgets.QDialog.Accepted

    def _ersetzen_und_speichern(self):
        neu_code = self._ki_area.toPlainText().strip()
        if not neu_code:
            self._set_status("⚠  KI-Antwort ist leer")
            return

        # Plan-Modus: erst anzeigen, dann auf Bestätigung warten
        if self._plan_modus_aktiv:
            if not self._plan_dialog_zeigen(neu_code):
                self._set_status("❌ Ersetzen abgebrochen")
                return

        self._backup_erstellen()
        # Selektion wiederherstellen falls Fokus-Wechsel sie gelöscht hat
        hat_selektion = self._stelle_selektion_wieder_her()
        c = self._editor.textCursor()
        if not hat_selektion or not c.hasSelection():
            if not self._find_in_editor():
                # Kein Block markiert, nichts gefunden → gesamten Editor ersetzen
                self._editor.setPlainText(neu_code)
                self.speichern()
                self._btn_ersetzen.setEnabled(False)
                self._letzter_editor_cursor = None
                self._set_status("🎉 KI-Code in Editor übertragen und gespeichert")
                return
            c = self._editor.textCursor()
        target_indent = self._erste_einrueckung(
            self._normalize_newlines(c.selectedText()))
        c.beginEditBlock()
        c.insertText(self._reindent_block(neu_code, target_indent))
        c.endEditBlock()
        self.speichern()
        self._btn_ersetzen.setEnabled(False)
        self._letzter_editor_cursor = None
        self._set_status("🎉 Block ersetzt und gespeichert")

    def _einfuegen_nach_fundstelle(self):
        neu_code = self._ki_area.toPlainText().strip()
        if not neu_code:
            self._set_status("⚠  KI-Antwort ist leer")
            return
        # Selektion wiederherstellen falls Fokus-Wechsel sie gelöscht hat
        hat_selektion = self._stelle_selektion_wieder_her()
        c = self._editor.textCursor()
        if not hat_selektion or not c.hasSelection():
            if not self._find_in_editor():
                self._set_status("⚠  Kein Block markiert und Suchfeld-Inhalt nicht gefunden")
                return
            c = self._editor.textCursor()
        ziel_indent = self._erste_einrueckung(
            self._normalize_newlines(c.selectedText()))
        c.setPosition(c.selectionEnd())
        c.movePosition(QtGui.QTextCursor.EndOfBlock)
        c.beginEditBlock()
        c.insertText("\n\n" + self._reindent_block(neu_code, ziel_indent))
        c.endEditBlock()
        self._editor.setTextCursor(c)
        self.speichern()
        self._btn_einfuegen.setEnabled(False)
        self._letzter_editor_cursor = None
        self._set_status("🎉 Block eingefügt und gespeichert")

    def _syntax_bereinigen(self):
        """Entfernt deutschen Text, Markdown-Fences und Erklärungen aus der KI-Antwort."""
        import ast as _ast
        text = self._ki_area.toPlainText().strip()
        if not text or text.startswith("# ⏳"):
            self._set_status("⚠  KI-Antwort ist leer")
            return
        bereinigt = self._extrahiere_code_aus_nl_antwort(text)
        bereinigt = self._schneide_erklaerung_ab(bereinigt)
        if not bereinigt.strip():
            self._set_status("⚠  Bereinigung: kein Python-Code erkannt")
            return
        try:
            _ast.parse(bereinigt)
            self._ki_area.setPlainText(bereinigt)
            self._set_status("✅ Bereinigt – Syntax korrekt")
        except SyntaxError as e:
            self._ki_area.setPlainText(bereinigt)
            self._set_status(f"⚠ Bereinigt – noch Syntax-Fehler Zeile {e.lineno}: {e.msg}")

    # ══ Backup ═════════════════════════════════════════════════════════════
    def _backup_ordner(self) -> str:
        ordner = os.path.join(os.path.dirname(self._pfad), "__backups__")
        os.makedirs(ordner, exist_ok=True)
        return ordner

    def _backup_erstellen(self) -> str:
        dateiname = os.path.basename(self._pfad)
        bak_name = f"{dateiname}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        bak_pfad = os.path.join(self._backup_ordner(), bak_name)
        try:
            shutil.copy2(self._pfad, bak_pfad)
            alle = sorted(glob.glob(
                os.path.join(self._backup_ordner(), f"{dateiname}.*.bak")))
            for alt in alle[:-3]:
                os.remove(alt)
            self._set_status(f"💾 Backup: {bak_name}", ms=3000)
            return bak_pfad
        except Exception as e:
            self._set_status(f"⚠ Backup fehlgeschlagen: {e}")
            return ""

    def _backup_wiederherstellen(self):
        dateiname = os.path.basename(self._pfad)
        alle = sorted(glob.glob(
            os.path.join(self._backup_ordner(), f"{dateiname}.*.bak")))
        if not alle:
            self._set_status("⚠ Kein Backup gefunden")
            return
        neuestes = alle[-1]
        antwort = QtWidgets.QMessageBox.question(
            self, "Backup wiederherstellen",
            f"Neuestes Backup laden?\n\n{os.path.basename(neuestes)}",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No)
        if antwort != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            with open(neuestes, "r", encoding="utf-8") as f:
                self._editor.setPlainText(f.read())
            self._set_status(f"↩ Backup geladen: {os.path.basename(neuestes)}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler", uebersetze_fehler(e))

    # ══ Assistent-Highlighting ══════════════════════════════════════════════
    def _widget_blinken(self, name: str):
        """Lässt ein Widget kurz in der Highlight-Farbe aufleuchten.

        Sucht automatisch alle QPushButton- und QDockWidget-Kinder nach dem
        Namen — kein manuelles Register nötig. Vergleich ist emoji- und
        leerzeichen-tolerant. Farbe kommt aus QPalette (kein Hardcoding).
        """
        import re as _re
        def _bereinigen(s: str) -> str:
            return _re.sub(r'\s+', ' ', _re.sub(r'[^\w\s]', '', s)).strip().lower()

        ziel_key = _bereinigen(name)
        treffer: list[QtWidgets.QWidget] = []

        for btn in self.findChildren(QtWidgets.QPushButton):
            if _bereinigen(btn.text()) == ziel_key:
                treffer.append(btn)

        for dock in self.findChildren(QtWidgets.QDockWidget):
            if _bereinigen(dock.windowTitle()) == ziel_key:
                treffer.append(dock)
                if not dock.isVisible():
                    dock.show()
                    dock.raise_()

        pal = self.palette()
        farbe = pal.color(QtGui.QPalette.ColorRole.Highlight).name()

        for widget in treffer:
            orig = widget.styleSheet()
            widget.setStyleSheet(
                f"{orig}; background-color: {farbe}; border: 2px solid {farbe};")
            QtCore.QTimer.singleShot(
                1800, lambda w=widget, s=orig: w.setStyleSheet(s))

    # ══ Hilfe-Fenster ══════════════════════════════════════════════════════
    def _on_barrierefreiheit(self, schluessel, wert):
        """Wendet Barrierefreiheits-Einstellungen live an."""
        if schluessel == "schrift_groesse":
            font = self.font()
            font.setPointSize(int(wert))
            self.setFont(font)
            QtWidgets.QApplication.instance().setFont(font)

        elif schluessel == "editor_schrift":
            f = QtGui.QFont("Courier New", int(wert))
            for tab in getattr(self, "_tabs", []):
                editor = tab.get("editor")
                if editor:
                    editor.setFont(f)
            if hasattr(self, "find_area"):
                self.find_area.setFont(f)
            if hasattr(self, "_ki_area"):
                self._ki_area.setFont(f)

        elif schluessel == "button_groesse":
            groessen = {0: 26, 1: 34, 2: 42}
            hoehe = groessen.get(int(wert), 26)
            for btn in self.findChildren(QtWidgets.QPushButton):
                if btn.height() in (26, 34, 42):
                    btn.setFixedHeight(hoehe)

        elif schluessel == "kontrast":
            if wert:
                self.setStyleSheet(
                    "QWidget { color: #ffffff; background-color: #000000; }"
                    "QPushButton { background: #222; border: 2px solid #fff; }"
                    "QPlainTextEdit, QTextEdit { background: #000; color: #fff; }")
            else:
                self.setStyleSheet("")

    def _zeige_hilfe(self):
        """Öffnet das Hilfe-Fenster als schwebendes, nicht-modales Fenster."""
        if hasattr(self, "_hilfe_fenster") and self._hilfe_fenster is not None:
            try:
                self._hilfe_fenster.raise_()
                self._hilfe_fenster.activateWindow()
                return
            except RuntimeError:
                pass

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("❓  Hilfe  –  KI-Makro-Editor")
        _scr = QtWidgets.QApplication.primaryScreen().availableGeometry()
        dlg.resize(520, min(680, int(_scr.height() * 0.82)))
        dlg.setModal(False)
        dlg.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dlg.setWindowFlags(
            QtCore.Qt.Window
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint)
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(HilfeTab())

        dlg.destroyed.connect(lambda: setattr(self, "_hilfe_fenster", None))
        self._hilfe_fenster = dlg
        dlg.show()

    # ══ Theme-Wechsel (Hell ↔ Dunkel) ═════════════════════════════════════════
    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.ApplicationPaletteChange:
            for tab in getattr(self, "_tabs", []):
                hl = tab.get("highlighter")
                if hl is not None:
                    hl.aktualisiere_theme()

    # ══ Fenster schließen ══════════════════════════════════════════════════════
    def closeEvent(self, event):
        self._alive = False
        # ── Dock-Layout speichern (Breiten, Positionen) ──────────────────
        try:
            import json as _json
            _state = self.saveState().toBase64().data().decode("ascii")
            with open(self._layout_state_datei, "w", encoding="utf-8") as _sf:
                _json.dump({"version": "v5", "state": _state}, _sf)
        except Exception:
            pass
        # ── Laufende Timer stoppen ────────────────────────────────────────
        for attr in ("_flush_timer", "_status_timer", "_baum_timer",
                     "_refresh_timer"):
            timer = getattr(self, attr, None)
            if timer is not None:
                timer.stop()
        # ── Preview/Snippet-Worker beenden ───────────────────────────────
        for attr in ("_preview_worker", "_snip_worker"):
            worker = getattr(self, attr, None)
            if worker is not None and worker.isRunning():
                worker.quit()
                worker.wait(500)
        # ── requests-Session schließen ───────────────────────────────────
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
        # ── KI-Verlauf + Chunk-Buffer freigeben ──────────────────────────
        self._chat_verlauf.clear()
        self._chunk_buffer.clear()

        geaenderte = [(i, t) for i, t in enumerate(self._tabs) if t["geaendert"]]
        if geaenderte:
            namen = ", ".join(os.path.basename(t["pfad"]) for _, t in geaenderte)
            antwort = QtWidgets.QMessageBox.question(
                self, "Ungespeicherte Änderungen",
                f"Geändert: {namen}\n\nAlle speichern?",
                QtWidgets.QMessageBox.StandardButton.Save |
                QtWidgets.QMessageBox.StandardButton.Discard |
                QtWidgets.QMessageBox.StandardButton.Cancel)
            if antwort == QtWidgets.QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if antwort == QtWidgets.QMessageBox.StandardButton.Save:
                for _, tab in geaenderte:
                    try:
                        with open(tab["pfad"], "w", encoding="utf-8") as f:
                            f.write(tab["editor"].toPlainText())
                    except Exception as e:
                        QtWidgets.QMessageBox.critical(
                            self, "Fehler", uebersetze_fehler(e))
                        event.ignore()
                        return
        event.accept()

    # ══ Tab-Verwaltung ══════════════════════════════════════════════════════════
    def _tab_oeffnen(self, pfad: str):
        """Öffnet pfad als Tab – oder wechselt zu bestehendem Tab."""
        for i, tab in enumerate(self._tabs):
            if tab["pfad"] == pfad:
                self._editor_tab_widget.setCurrentIndex(i)
                return
        container = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        editor = JediEditor()
        editor.setFont(QtGui.QFont("Courier New", 10))
        editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        # FIX: 'Noto Color Emoji' entfernt – verursacht auf Linux falsche
        #      Zifferndarstellung (Emoji-Glyphen mit Variation-Selector-Lücken)
        editor.setStyleSheet(
            f"QPlainTextEdit{{"
            f"font-family:'Courier New',monospace;"
            f"color:{theme.SYNTAX_TEXT_FARBE};"
            f"}}")
        opt = editor.document().defaultTextOption()
        opt.setAlignment(QtCore.Qt.AlignLeft)
        # WordWrap NICHT setzen: Editor ist NoWrap → Konflikt → Riesenlücken
        editor.document().setDefaultTextOption(opt)
        lay.addWidget(editor)
        tab_data = {"pfad": pfad, "geaendert": False, "editor": editor}
        self._tabs.append(tab_data)
        name = os.path.basename(pfad)
        self._editor_tab_widget.addTab(container, name)
        idx = len(self._tabs) - 1
        # Signale verbinden BEVOR setCurrentIndex (damit _tab_gewechselt den Editor kennt)
        editor.document().contentsChanged.connect(self._markiere_geaendert)
        editor.cursorPositionChanged.connect(self._update_cursor_info)
        # Datei laden – contentsChanged blockieren damit kein "*" erscheint
        editor.document().blockSignals(True)
        highlighter = PythonHighlighter(editor.document())
        tab_data["highlighter"] = highlighter
        # FreeCAD wendet seine Palette erst nach Widget-Erstellung an.
        # Nach 200ms sicherstellen dass das korrekte Theme geladen ist.
        QtCore.QTimer.singleShot(200, highlighter.aktualisiere_theme)
        try:
            with open(pfad, "r", encoding="utf-8") as f:
                inhalt = f.read()
        except UnicodeDecodeError:
            try:
                with open(pfad, "r", encoding="latin-1") as f:
                    inhalt = f.read()
            except Exception as e:
                inhalt = f"# Fehler beim Laden: {e}"
        except Exception as e:
            inhalt = f"# Fehler beim Laden: {e}"
        editor.document().blockSignals(False)
        # Highlighting aktiv lassen: setPlainText NACH blockSignals(False)
        editor.setPlainText(inhalt)
        # geaendert wieder zurücksetzen (setPlainText hat es gesetzt)
        tab_data["geaendert"] = False
        self._editor_tab_widget.setCurrentIndex(idx)
        if pfad not in self._datei_watcher.files():
            self._datei_watcher.addPath(pfad)

    def _tab_gewechselt(self, index: int):
        """Aktualisiert self._editor / _pfad / _geaendert beim Tab-Wechsel."""
        if 0 <= index < len(self._tabs):
            tab = self._tabs[index]
            alter_editor    = self._editor
            self._editor        = tab["editor"]
            self._pfad          = tab["pfad"]
            self._geaendert     = tab["geaendert"]
            name   = os.path.basename(self._pfad)
            suffix = "  *" if self._geaendert else ""
            self.setWindowTitle(f"Makro-Editor  –  {name}{suffix}")

            # ── Selektion-Cache auf neuen Editor umhängen ──────────────────
            if alter_editor is not None and alter_editor is not self._editor:
                try:
                    alter_editor.selectionChanged.disconnect(
                        self._on_editor_selection_changed)
                except RuntimeError:
                    pass
            self._letzter_editor_cursor = None
            # Nur verbinden wenn Editor wirklich gewechselt (kein Mehrfach-Connect)
            if alter_editor is not self._editor:
                self._editor.selectionChanged.connect(self._on_editor_selection_changed)
            # ──────────────────────────────────────────────────────────────

            # ── KI-Verlauf beim Tab-Wechsel leeren (Speicher-Schutz) ──
            # Der Verlauf einer anderen Datei enthält falschen Code-Kontext
            # und würde die KI bei der neuen Datei in die Irre führen.
            if hasattr(self, "_ki_verlauf_reset"):
                self._ki_verlauf_reset()

            # WerkzeugLeiste auf den neuen Editor umschalten
            if hasattr(self, "_werkzeug_leiste"):
                wl = self._werkzeug_leiste
                old_ed = wl._ed
                if old_ed is not self._editor:
                    try:
                        old_ed.cursorPositionChanged.disconnect(wl._cursor_sync)
                        old_ed.cursorPositionChanged.disconnect(wl._lz_highlight)
                        old_ed.cursorPositionChanged.disconnect(wl._selektion_sichern)
                    except RuntimeError:
                        pass
                    # Baum-Timer vom alten auf den neuen Editor umhängen
                    if hasattr(self, "_baum_timer"):
                        try:
                            old_ed.textChanged.disconnect(self._baum_timer.start)
                        except RuntimeError:
                            pass
                        self._editor.textChanged.connect(self._baum_timer.start)
                    wl._ed = self._editor
                    self._editor.cursorPositionChanged.connect(wl._cursor_sync)
                    self._editor.cursorPositionChanged.connect(wl._lz_highlight)
                    self._editor.cursorPositionChanged.connect(wl._selektion_sichern)
                # Baum sofort für den neuen Tab aktualisieren
                wl.aktualisiere_code_baum(self._editor.toPlainText())

    def _tab_schliessen(self, index: int):
        """Schließt einen Tab – bei Änderungen vorher Speicher-Abfrage."""
        if index < 0 or index >= len(self._tabs):
            return
        tab = self._tabs[index]
        if tab["geaendert"]:
            antwort = QtWidgets.QMessageBox.question(
                self, "Ungespeicherte Änderungen",
                f"'{os.path.basename(tab['pfad'])}' speichern?",
                QtWidgets.QMessageBox.StandardButton.Save |
                QtWidgets.QMessageBox.StandardButton.Discard |
                QtWidgets.QMessageBox.StandardButton.Cancel)
            if antwort == QtWidgets.QMessageBox.StandardButton.Cancel:
                return
            if antwort == QtWidgets.QMessageBox.StandardButton.Save:
                try:
                    with open(tab["pfad"], "w", encoding="utf-8") as f:
                        f.write(tab["editor"].toPlainText())
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self, "Fehler", uebersetze_fehler(e))
                    return
        pfad = tab["pfad"]
        restliche = [t for j, t in enumerate(self._tabs) if j != index]
        if not any(t["pfad"] == pfad for t in restliche):
            self._datei_watcher.removePath(pfad)
        self._tabs.pop(index)
        self._editor_tab_widget.removeTab(index)
        if self._editor_tab_widget.count() == 0:
            self.close()

    @QtCore.Slot(str, str)
    def _on_snip_slash_cmd(self, name: str, code: str):
        """
        Wird aufgerufen wenn im Suchfeld '/<name>' eingegeben und ein Snippet
        aus dem Autocomplete-Popup gewählt wurde.
        Lädt den Snippet-Code ins Suchfeld – bereit für die KI oder als Suchbegriff.
        """
        self.find_area.setPlainText(code)
        # Cursor ans Ende setzen
        cursor = self.find_area.textCursor()
        cursor.movePosition(cursor.End)
        self.find_area.setTextCursor(cursor)
        self._set_status(f"📦 Snippet '/{name}' ins Suchfeld geladen – jetzt KI fragen oder markieren")

    @QtCore.Slot(int)
    def _on_ki_compact(self, anzahl: int):
        """Wird aufgerufen wenn Context Compacting stattgefunden hat."""
        self._set_status(
            f"🗜 Context Compacting: {anzahl} ältere Nachrichten zusammengefasst")
        aktuell = self._ki_area.toPlainText()
        hinweis = (
            f"\n\n# ───────────────────────────────────────────────\n"
            f"# 🗜 Context Compacting: {anzahl} ältere Nachrichten wurden\n"
            f"#    automatisch zusammengefasst um den Kontext klein zu halten.\n"
            f"#    [Verlauf zurücksetzen: Knopf '🧹' im KI-Header]\n"
            f"# ───────────────────────────────────────────────\n"
        )
        self._ki_area.setPlainText(aktuell + hinweis)
