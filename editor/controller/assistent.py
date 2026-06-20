# -*- coding: utf-8 -*-
"""
assistent.py
────────────
Interaktiver Schritt-für-Schritt-Assistent für den KI-Makro-Editor.

Der Anwender stellt eine Frage auf Deutsch (Rechtschreibung egal).
Die KI antwortet mit nummerierten Schritten und nennt dabei Buttons/Panels
im Format [WIDGET: Name]. Der Editor lässt diese Widgets kurz aufleuchten,
damit der Anwender sofort sieht wo er klicken muss.

Architektur:
  AssistentKiThread  – QThread: führt KI-Streaming durch, emittiert Chunks
  AssistentPanel     – QWidget: Chat-Anzeige + Eingabe + Highlight-Logik
"""

from __future__ import annotations

import json
import re

from core.qt_compat import QtCore, QtWidgets, QtGui

from core.qt_compat import requests as _requests, HAS_REQUESTS as _HAS_REQUESTS

_RE_BACKTICK = re.compile(r'`([^`]+)`')


# ══════════════════════════════════════════════════════════════════════════════
# KI-Thread
# ══════════════════════════════════════════════════════════════════════════════

class _AssistentKiThread(QtCore.QThread):
    """Führt einen KI-Streaming-Aufruf durch und emittiert Chunks."""

    chunk   = QtCore.Signal(str)
    fertig  = QtCore.Signal(str)   # vollständige Antwort
    fehler  = QtCore.Signal(str)

    def __init__(self, source: str, model: str, api_key: str,
                 system: str, frage: str, parent=None):
        super().__init__(parent)
        self._source  = source
        self._model   = model
        self._api_key = api_key
        self._system  = system
        self._frage   = frage
        self._alive   = True

    def stop(self):
        self._alive = False

    def run(self):
        try:
            teile = []
            if self._source.startswith("Ollama"):
                teile = self._stream_ollama()
            elif self._source.startswith("Anthropic"):
                teile = self._stream_anthropic()
            else:
                teile = self._stream_openai_compat()
            self.fertig.emit("".join(teile))
        except Exception as e:
            self.fehler.emit(str(e))

    def _stream_ollama(self):
        import os as _os
        prompt = f"{self._system}\n\nFrage: {self._frage}"
        r = _requests.post(
            "http://localhost:11434/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": True,
                  "options": {"temperature": 0.3, "num_ctx": 4096,
                               "num_predict": 512, "num_thread": _os.cpu_count() or 4}},
            stream=True, timeout=None)
        r.raise_for_status()
        teile = []
        for line in r.iter_lines():
            if not self._alive:
                break
            if line:
                chunk = json.loads(line).get("response", "")
                if chunk:
                    teile.append(chunk)
                    self.chunk.emit(chunk)
        return teile

    def _stream_anthropic(self):
        if not self._api_key:
            raise RuntimeError("Kein Anthropic API-Schlüssel hinterlegt.")
        r = _requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self._api_key,
                     "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": self._model, "max_tokens": 2048,
                  "temperature": 0.3, "stream": True,
                  "system": self._system,
                  "messages": [{"role": "user", "content": self._frage}]},
            stream=True, timeout=120)
        r.raise_for_status()
        teile = []
        for line in r.iter_lines():
            if not self._alive:
                break
            if line and line.startswith(b"data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta":
                        chunk = data.get("delta", {}).get("text", "")
                        if chunk:
                            teile.append(chunk)
                            self.chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError):
                    pass
        return teile

    def _stream_openai_compat(self):
        _BASES = {
            "OpenAI":      "https://api.openai.com/v1",
            "GitHub":      "https://models.inference.ai.azure.com",
            "DeepSeek":    "https://api.deepseek.com/v1",
            "Gemini":      "https://generativelanguage.googleapis.com/v1beta/openai",
            "Groq":        "https://api.groq.com/openai/v1",
            "Mistral":     "https://api.mistral.ai/v1",
            "Together":    "https://api.together.xyz/v1",
            "OpenRouter":  "https://openrouter.ai/api/v1",
        }
        base = next(
            (v for k, v in _BASES.items() if self._source.startswith(k)),
            "https://api.openai.com/v1")
        if not self._api_key:
            raise RuntimeError(f"Kein API-Schlüssel für {self._source} hinterlegt.")
        r = _requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}",
                     "Content-Type": "application/json"},
            json={"model": self._model, "temperature": 0.3, "stream": True,
                  "messages": [
                      {"role": "system", "content": self._system},
                      {"role": "user",   "content": self._frage},
                  ]},
            stream=True, timeout=120)
        r.raise_for_status()
        teile = []
        for line in r.iter_lines():
            if not self._alive:
                break
            if line and line.startswith(b"data: "):
                raw = line[6:]
                if raw == b"[DONE]":
                    break
                try:
                    chunk = json.loads(raw)["choices"][0]["delta"].get("content", "")
                    if chunk:
                        teile.append(chunk)
                        self.chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        return teile


# ══════════════════════════════════════════════════════════════════════════════
# Panel
# ══════════════════════════════════════════════════════════════════════════════

class AssistentPanel(QtWidgets.QWidget):
    """Interaktives Schritt-für-Schritt-Assistenten-Panel."""

    # Signal an editor.py: Widget mit diesem Namen aufleuchten lassen
    widget_blinken = QtCore.Signal(str)

    def __init__(self, editor_ref, parent=None):
        super().__init__(parent)
        self._editor = editor_ref
        self._thread: _AssistentKiThread | None = None
        self._puffer = []          # Chunks sammeln bis Antwort fertig
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        # Hinweis-Label
        info = QtWidgets.QLabel(
            "Stelle eine Frage – die KI zeigt dir Schritt für Schritt was zu tun ist.")
        info.setWordWrap(True)
        lay.addWidget(info)

        # Chat-Anzeige
        self._anzeige = QtWidgets.QTextEdit()
        self._anzeige.setReadOnly(True)

        # ── Splitter: Chat oben / Eingabe unten (frei skalierbar) ────────
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._anzeige)

        _unten = QtWidgets.QWidget()
        _unten_lay = QtWidgets.QVBoxLayout(_unten)
        _unten_lay.setContentsMargins(0, 4, 0, 0)
        _unten_lay.setSpacing(4)

        # Eingabe (mehrzeilig) + Button
        reihe = QtWidgets.QHBoxLayout()
        self._eingabe = QtWidgets.QPlainTextEdit()
        self._eingabe.setPlaceholderText(
            'z.B. "wie übersetze ich einen Fehler?" oder "wie richte ich Ollama ein?"\n'
            '(Enter = Senden  |  Shift+Enter = neue Zeile)')
        self._eingabe.setMinimumHeight(30)
        self._eingabe.installEventFilter(self)
        reihe.addWidget(self._eingabe)

        self._btn_fragen = QtWidgets.QPushButton("❓ Fragen")
        self._btn_fragen.setFixedWidth(80)
        self._btn_fragen.clicked.connect(self._fragen)
        reihe.addWidget(self._btn_fragen, 0, QtCore.Qt.AlignBottom)
        _unten_lay.addLayout(reihe)

        # Verlauf löschen
        btn_clear = QtWidgets.QPushButton("🗑  Verlauf löschen")
        btn_clear.clicked.connect(self._verlauf_loeschen)
        _unten_lay.addWidget(btn_clear)

        splitter.addWidget(_unten)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        lay.addWidget(splitter, 1)

    # ── Fragen ────────────────────────────────────────────────────────────
    def _fragen(self):
        if not _HAS_REQUESTS:
            self._anzeige.append(
                f"<b style='color:{self.palette().color(QtGui.QPalette.ColorRole.BrightText).name()};'>"
                f"⚠ requests-Modul nicht installiert.</b><br>")
            return
        frage = self._eingabe.toPlainText().strip()
        if not frage:
            return
        if self._thread and self._thread.isRunning():
            self._thread.stop()

        self._eingabe.setPlainText("")
        self._btn_fragen.setEnabled(False)
        self._anzeige.append(f"<b>Du:</b> {frage}<br>")
        self._anzeige.append("<b>Assistent:</b> ")
        self._puffer.clear()

        try:
            # KI-Einstellungen aus dem Editor lesen
            source  = self._editor._src_box.currentText()
            model   = self._editor._model_box.currentText()
            from core.params import lade_api_key
            kid = source.split()[0].lower()
            api_key = lade_api_key(kid)

            from editor.ki.assistent_prompt import (
                ASSISTENT_SYSTEM_PROMPT_OLLAMA,
                ASSISTENT_SYSTEM_PROMPT_CLOUD,
            )
            prompt = (ASSISTENT_SYSTEM_PROMPT_OLLAMA
                      if source.startswith("Ollama")
                      else ASSISTENT_SYSTEM_PROMPT_CLOUD)
            self._thread = _AssistentKiThread(
                source, model, api_key, prompt, frage, self)
            self._thread.chunk.connect(self._on_chunk)
            self._thread.fertig.connect(self._on_fertig)
            self._thread.fehler.connect(self._on_fehler)
        except Exception as e:
            self._on_fehler(f"Start fehlgeschlagen: {e}")
            return
        self._thread.start()

    # ── Chunk-Streaming ──────────────────────────────────────────────────
    def _on_chunk(self, chunk: str):
        self._puffer.append(chunk)
        # Backtick-Namen fett anzeigen
        sauber = _RE_BACKTICK.sub(r'<b>\1</b>', chunk)
        cursor = self._anzeige.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        self._anzeige.setTextCursor(cursor)
        self._anzeige.insertPlainText(sauber)

    def _on_fertig(self, vollstaendig: str):
        self._btn_fragen.setEnabled(True)
        self._anzeige.append("<br>")

        from editor.ki.assistent_prompt import BEKANNTE_WIDGETS

        # 1. Backtick-Format: `Name`
        treffer = [m.group(1).strip() for m in _RE_BACKTICK.finditer(vollstaendig)]

        # 2. Fallback: bekannte Widget-Namen direkt im Text suchen
        if not treffer:
            for w in BEKANNTE_WIDGETS:
                if w in vollstaendig:
                    treffer.append(w)

        # Duplikate entfernen, Reihenfolge beibehalten
        gesehen = set()
        treffer_unique = [x for x in treffer
                          if not (x in gesehen or gesehen.add(x))]

        for i, name in enumerate(treffer_unique):
            QtCore.QTimer.singleShot(
                i * 2200, lambda n=name: self.widget_blinken.emit(n))

    def _on_fehler(self, msg: str):
        self._btn_fragen.setEnabled(True)
        farbe = self.palette().color(QtGui.QPalette.ColorRole.BrightText).name()
        self._anzeige.append(f"<br><b style='color:{farbe};'>⚠ {msg}</b><br>")

    def _verlauf_loeschen(self):
        self._anzeige.clear()

    # ── Event-Filter: Enter = Senden, Shift+Enter = neue Zeile ───────────
    def eventFilter(self, obj, event):
        if obj is self._eingabe and event.type() == QtCore.QEvent.KeyPress:
            key  = event.key()
            mods = event.modifiers()
            if (key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
                    and not (mods & QtCore.Qt.ShiftModifier)):
                self._fragen()
                return True
        return super().eventFilter(obj, event)
