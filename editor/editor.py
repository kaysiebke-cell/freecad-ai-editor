# -*- coding: utf-8 -*-
"""
editor.py
─────────
Koordinator des Makro-Editors.

Öffentliche API (wird von manager.py genutzt):
  MakroEditor(pfad, parent)         – Hauptfenster
  MakroEditor.fehler_anzeigen(text) – Fehler-Panel öffnen
  MakroEditor.insert_snippet(code)  – Snippet einfügen
"""

import os
import re
import time

from qt_compat import QtWidgets, QtCore, QtGui

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

import theme
import schrift
from fehler import uebersetze_fehler
import params
from params import lade_api_key, speichere_api_key
from aktionen_sidebar import RechteSidebar

from ki_controller import KiController as KIMixin
from browser_controller import BrowserController as BrowserMixin
from snippet_controller import SnippetController as TabsMixin
from ki_tools_tab import KiToolsTabMixin
from bibliothek_tab import BibliothekTabMixin
from vorschau_controller import VorschauController as VorschauMixin

from central_widget_builder import init_central_widget
from ki_widget_builder import init_ki_widgets, get_preset_prompt, baue_preset_menu
from dock_builder import init_docks
from toolbar_builder import init_toolbar

from editor_datei import DateiLogik
from editor_suche import SucheLogik
from editor_code import CodeLogik
from editor_plan import PlanLogik
from editor_tabs import TabLogik
from editor_barrierefreiheit import BarriereLogik

_ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons"
)


class MakroEditor(QtWidgets.QMainWindow, KIMixin, BrowserMixin, TabsMixin,
                  VorschauMixin, KiToolsTabMixin, BibliothekTabMixin):
    """Editor mit frei anordenbaren Dock-Panels (QDockWidget)."""

    _ki_chunk          = QtCore.Signal(str)
    _ki_stream_done    = QtCore.Signal()
    _ki_error          = QtCore.Signal(str)
    _ki_compact_signal = QtCore.Signal(int)
    such_in_dateien    = QtCore.Signal(str)

    # (src_name, key_display_name, key_id, icon_datei)
    _ANBIETER = [
        ("Ollama (Lokal)",      None,                  None,           ""),
        ("Anthropic (Claude)", "Anthropic (Claude)",   "anthropic",    ""),
        ("OpenAI (ChatGPT)",   "OpenAI (ChatGPT)",     "openai",       "openai.svg"),
        ("GitHub Copilot",     "GitHub Copilot",       "github",       "github.svg"),
        ("OpenRouter (Cloud)", "OpenRouter",            "openrouter",   ""),
        ("Gemini (Google)",    "Google Gemini",         "gemini",       "gemini.svg"),
        ("DeepSeek",           "DeepSeek",              "deepseek",     "deepseek.svg"),
        ("Qwen (Alibaba)",     "Qwen (Alibaba)",        "qwen",         "qwen.svg"),
        ("Groq",               "Groq",                  "groq",         "groq.svg"),
        ("Mistral",            "Mistral",               "mistral",      "mistral.svg"),
        ("Together AI",        "Together AI",           "together",     "together.svg"),
        ("Fireworks AI",       "Fireworks AI",          "fireworks",    "fireworks.svg"),
        ("xAI (Grok)",         "xAI (Grok)",            "xai",          "xai.svg"),
        ("Cohere",             "Cohere",                "cohere",       "cohere.svg"),
        ("SambaNova",          "SambaNova",             "sambanova",    "sambanova.svg"),
        ("MiniMax",            "MiniMax",               "minimax",      "minimax.svg"),
        ("Llama API",          "Llama API",             "llama",        "llama.svg"),
        ("Moonshot",           "Moonshot",              "moonshot",     "moonshot.svg"),
        ("HuggingFace",        "Hugging Face",          "huggingface",  "huggingface.svg"),
    ]

    # ── Init ──────────────────────────────────────────────────────────────

    def __init__(self, pfad, parent=None):
        super().__init__(parent)
        self._pfad      = pfad
        self._geaendert = False
        theme.set_farbschema(params.farbschema_dunkel())
        self.setWindowTitle(f"Makro-Editor  –  {os.path.basename(pfad)}")
        _scr = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(min(1080, int(_scr.width()  * 0.80)),
                    min(760,  int(_scr.height() * 0.82)))
        _x = _scr.x() + (_scr.width()  - self.width())  // 2
        _y = _scr.y() + (_scr.height() - self.height()) // 2
        self.move(_x, _y)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setDockNestingEnabled(True)
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
        _f = QtGui.QFont("Ubuntu", 10)
        try:
            from main import emoji_font
            _f = emoji_font(_f)
        except Exception:
            pass
        self.setFont(_f)
        self.setStyleSheet(theme.STY_HAUPTFENSTER_FONT())

        self._alive   = True
        self._session = requests.Session() if _HAS_REQUESTS else None

        self._chunk_buffer: list = []
        self._stream_token_count = 0
        self._stream_start_time  = 0.0
        self._flush_timer = QtCore.QTimer(self)
        self._flush_timer.setInterval(30)
        self._flush_timer.timeout.connect(self._flush_chunks)
        self._status_timer = QtCore.QTimer(self)
        self._status_timer.setInterval(500)
        self._status_timer.timeout.connect(self._update_stream_status)

        self._warte_dots  = 0
        self._warte_aktiv = False
        self._warte_timer = QtCore.QTimer(self)
        self._warte_timer.setInterval(400)
        self._warte_timer.timeout.connect(self._warte_tick)

        self._ki_chunk.connect(self._on_ki_chunk)
        self._ki_stream_done.connect(self._on_ki_stream_done)
        self._ki_error.connect(self._on_ki_error)
        self._ki_compact_signal.connect(self._on_ki_compact)

        self._chat_verlauf: list           = []
        self._compact_zusammenfassung: str = ""

        self._datei_watcher = QtCore.QFileSystemWatcher(self)
        self._datei_watcher.addPath(pfad)
        self._datei_watcher.fileChanged.connect(self._datei_extern_geaendert)
        self._watcher_pause = False

        # Kompositions-Objekte
        self._datei   = DateiLogik(self)
        self._suche   = SucheLogik(self)
        self._code    = CodeLogik(self)
        self._plan    = PlanLogik(self)
        self._tabs_lk = TabLogik(self)
        self._bfrei   = BarriereLogik(self)

        # Builder
        init_ki_widgets(self, _ICONS_DIR)
        init_central_widget(self)
        init_docks(self)
        self._tab_oeffnen(pfad)
        self._werkzeug_leiste = RechteSidebar()
        self._werkzeug_leiste.bind(self)
        init_toolbar(self)

        import json as _json
        _STATE_DATEI    = os.path.join(os.path.expanduser("~"), ".ki_makro_editor_layout.json")
        _GUARD_DATEI    = os.path.join(os.path.expanduser("~"), ".ki_makro_editor_restore_guard")
        _LAYOUT_VERSION = "v6"
        self._layout_state_datei = _STATE_DATEI

        def _lade_layout():
            try:
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
                with open(_GUARD_DATEI, "w", encoding="utf-8") as _gf:
                    _gf.write("restore_in_progress")
                self.restoreState(QtCore.QByteArray.fromBase64(_state.encode("ascii")))
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
            lambda: self._werkzeug_leiste.aktualisiere_code_baum(self._editor.toPlainText()))
        QtCore.QTimer.singleShot(0, lambda: self._werkzeug_leiste.aktualisiere_code_baum(
            self._editor.toPlainText()))

        self._refresh_models()
        self._letzter_editor_cursor = None
        self._vorschau_init()

    # ══ Öffentliche API ════════════════════════════════════════════════════

    def insert_snippet(self, code: str):
        c = self._editor.textCursor()
        if not c.hasSelection() and c.columnNumber() > 0:
            c.movePosition(QtGui.QTextCursor.EndOfBlock)
            c.insertText("\n")
        c.insertText(code)
        self._editor.setTextCursor(c)
        self._editor.setFocus()
        self._set_status(f"📦 Snippet eingefügt ({len(code.splitlines())} Zeilen)")

    def gehe_zu_zeile(self, zeilen_nr: int):
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
        if self._editor is None:
            return False
        self.find_area.setPlainText(suchtext)
        if self._find_in_editor():
            self._btn_ersetzen.setEnabled(True)
            self._set_status("🔍 Gefunden und markiert")
            self._editor.centerCursor()
            return True
        return False

    # ══ Gemeinsame Hilfsmethoden ═══════════════════════════════════════════

    def _key_anbieter_id(self) -> str:
        mapping = {k: kid for _, k, kid, _ in self._ANBIETER if k is not None}
        return mapping.get(self._key_anbieter.currentText(), "anthropic")

    def _update_cursor_info(self):
        c      = self._editor.textCursor()
        zeile  = c.blockNumber() + 1
        spalte = c.columnNumber() + 1
        self._status.setText(f"Zeile {zeile}, Spalte {spalte}")

    @staticmethod
    def _normalize_newlines(text: str) -> str:
        return text.replace(" ", "\n")

    def _set_status(self, text, ms=4000):
        self._status.setText(text)
        if ms > 0:
            QtCore.QTimer.singleShot(ms, self._loesche_status)

    def _loesche_status(self):
        try:
            self._status.setText("")
        except RuntimeError:
            pass

    def _warte_tick(self):
        if not self._warte_aktiv:
            self._warte_timer.stop()
            return
        self._warte_dots = (self._warte_dots + 1) % 4
        punkte = "●" * self._warte_dots + "○" * (3 - self._warte_dots)
        elapsed = time.monotonic() - self._stream_start_time
        self._ki_area.setPlainText(f"🧠 KI denkt nach {punkte}  ({elapsed:.0f} s)")

    def _on_sandbox_run(self):
        code = re.sub(r"```python|```", "", self._ki_area.toPlainText().strip()).strip()
        if code:
            self._fehler_inhalt._geladener_code = code
            self._fehler_inhalt._sandbox_ausfuehren()
        else:
            self._fehler_inhalt._sb_status.setText("⚠ KI-Antwort ist leer")

    # ── Preset-Delegationen (extern genutzt von ki_controller) ────────────

    def _get_preset_prompt(self) -> str:
        return get_preset_prompt(self)

    def _baue_preset_menu(self):
        baue_preset_menu(self)

    # ── Delegationen: DateiLogik ───────────────────────────────────────────

    def speichern(self):                   self._datei.speichern()
    def speichern_und_schliessen(self):    self._datei.speichern_und_schliessen()
    def neu_laden(self):                   self._datei.neu_laden()
    def _datei_extern_geaendert(self, p):  self._datei.datei_extern_geaendert(p)
    def alles_auswaehlen(self):            self._datei.alles_auswaehlen()
    def loeschen_auswahl(self):            self._datei.loeschen_auswahl()
    def _backup_ordner(self):              return self._datei.backup_ordner()
    def _backup_erstellen(self):           return self._datei.backup_erstellen()
    def _backup_wiederherstellen(self):    self._datei.backup_wiederherstellen()

    # ── Delegationen: SucheLogik ───────────────────────────────────────────

    def _toggle_suche(self):               self._suche.toggle_suche()
    def _suche_weiter(self):               self._suche.suche_weiter()
    def _ersetzen_text(self):              self._suche.ersetzen_text()
    def _alles_ersetzen(self):             self._suche.alles_ersetzen()
    def _copy_from_editor(self):           self._suche.copy_from_editor()
    def _find_in_editor(self) -> bool:     return self._suche.find_in_editor()
    def _find_and_highlight(self):         self._suche.find_and_highlight()

    # ── Delegationen: CodeLogik ────────────────────────────────────────────

    def _formatieren(self):                self._code.formatieren()
    def _smart_reindent(self, t):          return self._code.smart_reindent(t)
    def _reindent_block(self, c, i):       return self._code.reindent_block(c, i)
    def _erste_einrueckung(self, t):       return self._code.erste_einrueckung(t)
    def _syntax_bereinigen(self):          self._code.syntax_bereinigen()
    def _on_editor_selection_changed(self):self._code.on_editor_selection_changed()
    def _stelle_selektion_wieder_her(self):return self._code.stelle_selektion_wieder_her()

    # ── Delegationen: PlanLogik ────────────────────────────────────────────

    def _plan_modus_umschalten(self, a):   self._plan.plan_modus_umschalten(a)
    def _plan_dialog_zeigen(self, c):      return self._plan.plan_dialog_zeigen(c)
    def _ersetzen_und_speichern(self):     self._plan.ersetzen_und_speichern()
    def _einfuegen_nach_fundstelle(self):  self._plan.einfuegen_nach_fundstelle()

    # ── Delegationen: TabLogik ─────────────────────────────────────────────

    def _tab_oeffnen(self, p):             self._tabs_lk.tab_oeffnen(p)
    def _tab_gewechselt(self, i):          self._tabs_lk.tab_gewechselt(i)
    def _tab_schliessen(self, i):          self._tabs_lk.tab_schliessen(i)
    def _markiere_geaendert(self):         self._tabs_lk.markiere_geaendert()

    # ── Delegationen: BarriereLogik ────────────────────────────────────────

    def _on_farbschema(self, d):           self._bfrei.on_farbschema(d)
    def _on_barrierefreiheit(self, k, v):  self._bfrei.on_barrierefreiheit(k, v)
    def _zeige_hilfe(self):                self._bfrei.zeige_hilfe()
    def _widget_blinken(self, n):          self._bfrei.widget_blinken(n)

    # ── Slots (KI-Kompakt-Anzeige) ─────────────────────────────────────────

    @QtCore.Slot(str, str)
    def _on_snip_slash_cmd(self, name: str, code: str):
        self.find_area.setPlainText(code)
        cursor = self.find_area.textCursor()
        cursor.movePosition(cursor.End)
        self.find_area.setTextCursor(cursor)
        self._set_status(
            f"📦 Snippet '/{name}' ins Suchfeld geladen – jetzt KI fragen oder markieren")

    @QtCore.Slot(int)
    def _on_ki_compact(self, anzahl: int):
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

    # ══ Qt-Event-Overrides ═════════════════════════════════════════════════

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.ApplicationPaletteChange:
            for tab in getattr(self, "_tabs", []):
                hl = tab.get("highlighter")
                if hl is not None:
                    hl.aktualisiere_theme()

    def closeEvent(self, event):
        self._alive = False
        try:
            import json as _json
            _state = self.saveState().toBase64().data().decode("ascii")
            with open(self._layout_state_datei, "w", encoding="utf-8") as _sf:
                _json.dump({"version": "v6", "state": _state}, _sf)
        except Exception:
            pass
        for attr in ("_flush_timer", "_status_timer", "_baum_timer", "_refresh_timer"):
            timer = getattr(self, attr, None)
            if timer is not None:
                timer.stop()
        for attr in ("_preview_worker", "_snip_worker"):
            worker = getattr(self, attr, None)
            if worker is not None and worker.isRunning():
                worker.quit()
                worker.wait(500)
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
        self._chat_verlauf.clear()
        self._chunk_buffer.clear()
        geaenderte = [(i, t) for i, t in enumerate(self._tabs) if t["geaendert"]]
        if geaenderte:
            namen   = ", ".join(os.path.basename(t["pfad"]) for _, t in geaenderte)
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
                    except Exception as ex:
                        QtWidgets.QMessageBox.critical(
                            self, "Fehler", uebersetze_fehler(ex))
                        event.ignore()
                        return
        event.accept()
