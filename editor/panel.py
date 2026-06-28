# -*- coding: utf-8 -*-
"""
freecad_helfer_panel.py
───────────────────────
Barrierefreiheits-Helfer für Legastheniker und FreeCAD-Einsteiger.

Nimmt frei geschriebenen deutschen Text (Rechtschreibung egal) und
lässt einen KI-Anbieter daraus eine saubere, präzise FreeCAD-Beschreibung machen.
Optional kann ein Bild (Skizze, Foto, Handzeichnung) mitgeschickt werden.

Keine hardkodierten Farben — alles über QPalette (hell + dunkel).
"""

import base64
import json
import threading

from core.qt_compat import QtCore, QtWidgets, QtGui
from core import theme

from editor._helfer_rechtschreibung import (
    BACKEND as _SPELL_BACKEND,
    HAT_RECHTSCHREIBUNG as _HAT_RECHTSCHREIBUNG,
    RechtschreibHighlighter,
)
from editor._helfer_ui import ChatBubble, DiffBlase, BildVorschau

# anbieter_formate liegt in data/
try:
    from data.anbieter_formate import datei_filter, format_info, format_pruefen
except ImportError:
    def datei_filter(_): return "Bilder (*.png *.jpg *.jpeg *.webp *.gif *.bmp)"
    def format_info(_):  return ""
    def format_pruefen(_, e): return True


def _aktueller_anbieter() -> str:
    try:
        from core.params import lade_quelle
        return lade_quelle()
    except Exception:
        return "Ollama (Lokal)"


# ── Ollama ────────────────────────────────────────────────────────────────────
from core.qt_compat import requests as _requests, HAS_REQUESTS as _HAS_REQUESTS

OLLAMA_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = (
    "You correct text for FreeCAD requests. ALWAYS reply in German. "
    "No explanations, no instructions, no comments.\n\n"
    "Take the user's text and return it — grammatically correct, "
    "clear spelling, precise FreeCAD technical terms. "
    "Fill in missing dimensions sensibly. Nothing else. "
    "Only the corrected text, in German."
)

_VISION_SCHLUESSEL = ("llava", "bakllava", "moondream", "vision", "minicpm-v")


def _ist_vision_modell(name: str) -> bool:
    n = name.lower()
    return any(v in n for v in _VISION_SCHLUESSEL)


def _ollama_modelle() -> list[str]:
    if not _HAS_REQUESTS:
        return []
    try:
        r = _requests.get("http://localhost:11434/api/tags", timeout=3)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def _pixmap_zu_base64(pixmap: QtGui.QPixmap) -> str:
    ba  = QtCore.QByteArray()
    buf = QtCore.QBuffer(ba)
    buf.open(QtCore.QIODevice.WriteOnly)
    pixmap.save(buf, "PNG")
    buf.close()
    return base64.b64encode(bytes(ba)).decode("ascii")


# ── Haupt-Panel ───────────────────────────────────────────────────────────────
class FreecadHelferPanel(QtWidgets.QWidget):
    """
    Barrierefreiheits-Panel: frei geschriebener Text (+ optionales Bild)
    → saubere FreeCAD-Beschreibung via KI.
    """

    _chunk_signal = QtCore.Signal(str)
    _done_signal  = QtCore.Signal()
    _error_signal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stream_bubble        = None
        self._anhang_pixmap        = None
        self._letzter_eingabe_text = ""
        self._aktuelles_modell     = ""

        self._chunk_signal.connect(self._on_chunk)
        self._done_signal.connect(self._on_done)
        self._error_signal.connect(self._on_error)
        self._build_ui()
        self._lade_modelle()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Kopfzeile
        kopf = QtWidgets.QHBoxLayout()
        titel = QtWidgets.QLabel("🔧 FreeCAD Helfer")
        titel.setStyleSheet(theme.STY_HELFER_TITEL())
        kopf.addWidget(titel)
        kopf.addStretch()

        self._status_lbl = QtWidgets.QLabel("")
        self._status_lbl.setStyleSheet(theme.STY_HELFER_LABEL_SM())
        kopf.addWidget(self._status_lbl)
        root.addLayout(kopf)

        # Info
        info = QtWidgets.QLabel(
            "Schreib einfach, was du bauen möchtest — Rechtschreibung ist egal. "
            "Der Helfer macht daraus eine saubere Beschreibung für FC11.")
        info.setWordWrap(True)
        info.setStyleSheet(theme.STY_HELFER_LABEL_SM())
        root.addWidget(info)

        # Chat-Bereich
        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        self._chat_widget = QtWidgets.QWidget()
        self._chat_layout = QtWidgets.QVBoxLayout(self._chat_widget)
        self._chat_layout.setContentsMargins(4, 4, 4, 4)
        self._chat_layout.setSpacing(6)
        self._chat_layout.addStretch()
        self._scroll.setWidget(self._chat_widget)

        self._füge_bubble_ein(
            "Hallo! Schreib mir einfach, was du in FreeCAD bauen möchtest. "
            "Rechtschreibung ist egal — ich mache eine fertige Beschreibung daraus.\n\n"
            "Du kannst auch ein Bild (Skizze, Foto, Handzeichnung) anhängen — "
            "dann sehe ich Text und Bild zusammen.", "ki"
        ).finalize()

        # Splitter: Chat oben / Eingabe unten
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._scroll)

        _unten = QtWidgets.QWidget()
        _unten_lay = QtWidgets.QVBoxLayout(_unten)
        _unten_lay.setContentsMargins(0, 4, 0, 0)
        _unten_lay.setSpacing(4)

        # Eingabefeld
        self._eingabe = QtWidgets.QPlainTextEdit()
        self._eingabe.setPlaceholderText(
            "z.B.  ich brauch einen kasten mit loch zum anschrauben an die wand …\n"
            "(Shift+Enter = neue Zeile  |  Enter = Senden)\n"
            "Bild hierher ziehen oder Strg+V zum Einfügen")
        self._eingabe.setMinimumHeight(30)
        self._eingabe.setAcceptDrops(True)
        self._eingabe.installEventFilter(self)
        self._highlighter = RechtschreibHighlighter(self._eingabe.document())
        self._eingabe.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._eingabe.customContextMenuRequested.connect(self._kontext_menu)
        _unten_lay.addWidget(self._eingabe, 1)

        # Bild-Buttons
        bild_reihe = QtWidgets.QHBoxLayout()
        bild_reihe.setSpacing(6)

        _fmt_info = format_info(_aktueller_anbieter())

        self._bild_btn = QtWidgets.QPushButton("📎  Bild anhängen")
        self._bild_btn.setToolTip(
            f"Bilddatei auswählen\n\nUnterstützte Formate ({_aktueller_anbieter()}):\n"
            f"{_fmt_info}")
        self._bild_btn.setFixedHeight(28)
        self._bild_btn.clicked.connect(self._lade_bild)
        bild_reihe.addWidget(self._bild_btn)

        self._clip_btn = QtWidgets.QPushButton("📋  Aus Zwischenablage")
        self._clip_btn.setToolTip(
            f"Bild aus Zwischenablage einfügen (Strg+V)\n\n"
            f"Unterstützte Formate ({_aktueller_anbieter()}):\n{_fmt_info}")
        self._clip_btn.setFixedHeight(28)
        self._clip_btn.clicked.connect(self._bild_aus_zwischenablage)
        bild_reihe.addWidget(self._clip_btn)

        bild_reihe.addStretch()
        _unten_lay.addLayout(bild_reihe)

        # Vision-Warnung
        self._vision_warnung = QtWidgets.QLabel("")
        self._vision_warnung.setWordWrap(True)
        self._vision_warnung.setStyleSheet(theme.STY_HELFER_VISION_WARN_BASE())
        self._vision_warnung.setVisible(False)
        _unten_lay.addWidget(self._vision_warnung)

        # Bild-Vorschau-Container
        self._vorschau_container = QtWidgets.QWidget()
        self._vorschau_container.setLayout(QtWidgets.QVBoxLayout())
        self._vorschau_container.layout().setContentsMargins(0, 0, 0, 0)
        self._vorschau_container.setVisible(False)
        _unten_lay.addWidget(self._vorschau_container)

        # Senden-Button
        self._senden_btn = QtWidgets.QPushButton("➤  Senden")
        self._senden_btn.setFixedHeight(32)
        self._senden_btn.setToolTip("Senden (Enter)")
        self._senden_btn.clicked.connect(self._senden)
        _unten_lay.addWidget(self._senden_btn)

        splitter.addWidget(_unten)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

    # ── Modelle laden ─────────────────────────────────────────────────────────

    def _lade_modelle(self):
        try:
            from core.params import lade_quelle, lade_modell
            quelle = lade_quelle()
            modell = lade_modell()
        except Exception:
            quelle, modell = "Ollama (Lokal)", ""

        if quelle.startswith("Ollama"):
            modelle = _ollama_modelle()
            if modelle:
                self._aktuelles_modell = modell if modell in modelle else modelle[0]
                self._status_lbl.setText(f"✅ {self._aktuelles_modell}")
            else:
                self._aktuelles_modell = modell or ""
                self._status_lbl.setText("⚠ Ollama nicht erreichbar")
        else:
            self._aktuelles_modell = modell
            kurz = quelle.split()[0] if quelle else "?"
            self._status_lbl.setText(f"✅ {kurz} · {modell}" if modell else f"✅ {kurz}")

    # ── Bild-Handling ─────────────────────────────────────────────────────────

    def _lade_bild(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Bild auswählen", "",
            datei_filter(_aktueller_anbieter()))
        if not path:
            return
        endung = path.rsplit(".", 1)[-1] if "." in path else ""
        if endung and not format_pruefen(_aktueller_anbieter(), endung):
            self._status_lbl.setText(
                f"⚠ .{endung.upper()} wird von {_aktueller_anbieter()} nicht unterstützt")
            return
        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            self._status_lbl.setText("⚠ Bild konnte nicht geladen werden")
            return
        self._setze_bild(pixmap)

    def _bild_aus_zwischenablage(self):
        clipboard = QtWidgets.QApplication.clipboard()
        image = clipboard.image()
        if not image.isNull():
            self._setze_bild(QtGui.QPixmap.fromImage(image))
            return
        pixmap = clipboard.pixmap()
        if not pixmap.isNull():
            self._setze_bild(pixmap)
            return
        self._status_lbl.setText("⚠ Kein Bild in der Zwischenablage")

    def _setze_bild(self, pixmap: QtGui.QPixmap):
        self._anhang_pixmap = pixmap

        lay = self._vorschau_container.layout()
        for i in reversed(range(lay.count())):
            w = lay.itemAt(i).widget()
            if w:
                w.deleteLater()

        vorschau = BildVorschau(pixmap)
        vorschau.entfernt.connect(self._bild_entfernen)
        lay.addWidget(vorschau)
        self._vorschau_container.setVisible(True)

        self._pruefe_vision_modell()
        self._status_lbl.setText("📎 Bild bereit")

    def _bild_entfernen(self):
        self._anhang_pixmap = None
        self._vorschau_container.setVisible(False)
        self._vision_warnung.setVisible(False)
        self._status_lbl.setText("")

    def _pruefe_vision_modell(self):
        if self._anhang_pixmap is None:
            self._vision_warnung.setVisible(False)
            return
        modell = self._aktuelles_modell
        if modell and not _ist_vision_modell(modell):
            pal    = self.palette()
            dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
            bg     = QtGui.QColor.fromHsl(40, 200, 40 if dunkel else 230).name()
            fg     = QtGui.QColor.fromHsl(40, 200, 200 if dunkel else 60).name()
            self._vision_warnung.setStyleSheet(theme.STY_HELFER_VISION_WARN(bg, fg))
            self._vision_warnung.setText(
                f"⚠  '{modell}' unterstützt keine Bilder. "
                f"Wechsle zu llava oder moondream — "
                f"das Bild wird sonst ignoriert.")
            self._vision_warnung.setVisible(True)
        else:
            self._vision_warnung.setVisible(False)

    # ── Chat-Blasen ───────────────────────────────────────────────────────────

    def _füge_bubble_ein(self, text: str, rolle: str) -> ChatBubble:
        bubble = ChatBubble(text, rolle)
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        QtCore.QTimer.singleShot(50, self._scroll_unten)
        return bubble

    def _scroll_unten(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Senden ────────────────────────────────────────────────────────────────

    def _senden(self):
        text = self._eingabe.toPlainText().strip()
        if not text:
            return

        self._letzter_eingabe_text = text
        self._eingabe.clear()
        self._senden_btn.setEnabled(False)

        anzeige_text = text
        if self._anhang_pixmap is not None:
            px = self._anhang_pixmap
            anzeige_text = f"📎 {px.width()}×{px.height()} px\n\n{text}"
        self._füge_bubble_ein(anzeige_text, "nutzer")

        self._stream_bubble = self._füge_bubble_ein("", "ki")
        modell = self._aktuelles_modell or "llama3"

        try:
            from core.params import lade_quelle, lade_api_key
            quelle  = lade_quelle()
            kid     = quelle.split()[0].lower()
            api_key = lade_api_key(kid)
        except Exception:
            quelle, api_key = "Ollama (Lokal)", ""

        bild_b64 = None
        if self._anhang_pixmap is not None:
            if quelle.startswith("Ollama") and _ist_vision_modell(modell):
                bild_b64 = _pixmap_zu_base64(self._anhang_pixmap)
            elif quelle.startswith("Ollama"):
                self._status_lbl.setText("⚠ Bild ignoriert (kein Vision-Modell)")
            else:
                self._status_lbl.setText("⚠ Vision nur mit Ollama möglich")

        threading.Thread(
            target=self._worker,
            args=(quelle, modell, api_key, text, bild_b64),
            daemon=True
        ).start()

    # ── Anbieter-Routing ──────────────────────────────────────────────────────

    _BASES = {
        "OpenAI":      "https://api.openai.com/v1",
        "GitHub":      "https://models.inference.ai.azure.com",
        "DeepSeek":    "https://api.deepseek.com/v1",
        "Gemini":      "https://generativelanguage.googleapis.com/v1beta/openai",
        "Groq":        "https://api.groq.com/openai/v1",
        "Mistral":     "https://api.mistral.ai/v1",
        "Together":    "https://api.together.xyz/v1",
        "OpenRouter":  "https://openrouter.ai/api/v1",
        "xAI":         "https://api.x.ai/v1",
        "Fireworks":   "https://api.fireworks.ai/inference/v1",
        "Moonshot":    "https://api.moonshot.cn/v1",
        "Qwen":        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "Cohere":      "https://api.cohere.com/compatibility/v1",
        "SambaNova":   "https://api.sambanova.ai/v1",
        "MiniMax":     "https://api.minimaxi.chat/v1",
        "Llama":       "https://api.llama-api.com",
        "HuggingFace": "https://api-inference.huggingface.co/v1",
    }

    def _worker(self, quelle: str, modell: str, api_key: str,
                text: str, bild_b64: str | None = None):
        try:
            if quelle.startswith("Ollama"):
                self._stream_ollama(modell, text, bild_b64)
            elif quelle.startswith("Anthropic"):
                self._stream_anthropic(modell, api_key, text)
            else:
                base = next(
                    (v for k, v in self._BASES.items() if quelle.startswith(k)),
                    "https://api.openai.com/v1")
                self._stream_openai(base, modell, api_key, text)
            self._done_signal.emit()
        except Exception as e:
            self._error_signal.emit(str(e))

    def _stream_ollama(self, modell: str, text: str, bild_b64: str | None):
        nutzer_msg: dict = {"role": "user", "content": text}
        if bild_b64:
            nutzer_msg["images"] = [bild_b64]
        payload = json.dumps({
            "model": modell, "stream": True,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, nutzer_msg],
        }).encode("utf-8")
        import urllib.request as _ul
        req = _ul.Request(OLLAMA_URL, data=payload,
                          headers={"Content-Type": "application/json"}, method="POST")
        with _ul.urlopen(req, timeout=600) as resp:
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    obj   = json.loads(line)
                    chunk = obj.get("message", {}).get("content", "")
                    if chunk:
                        self._chunk_signal.emit(chunk)
                    if obj.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    def _stream_anthropic(self, modell: str, api_key: str, text: str):
        if not _HAS_REQUESTS:
            raise RuntimeError("requests nicht installiert")
        r = _requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": modell, "max_tokens": 1024, "stream": True,
                  "system": SYSTEM_PROMPT,
                  "messages": [{"role": "user", "content": text}]},
            stream=True, timeout=120)
        r.raise_for_status()
        for line in r.iter_lines():
            if line and line.startswith(b"data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta":
                        chunk = data.get("delta", {}).get("text", "")
                        if chunk:
                            self._chunk_signal.emit(chunk)
                except (json.JSONDecodeError, KeyError):
                    pass

    def _stream_openai(self, base: str, modell: str, api_key: str, text: str):
        if not _HAS_REQUESTS:
            raise RuntimeError("requests nicht installiert")
        r = _requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={"model": modell, "stream": True,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user",   "content": text}]},
            stream=True, timeout=120)
        r.raise_for_status()
        for line in r.iter_lines():
            if line and line.startswith(b"data: "):
                raw = line[6:]
                if raw == b"[DONE]":
                    break
                try:
                    chunk = json.loads(raw)["choices"][0]["delta"].get("content", "")
                    if chunk:
                        self._chunk_signal.emit(chunk)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

    # ── Signal-Handler ────────────────────────────────────────────────────────

    @QtCore.Slot(str)
    def _on_chunk(self, chunk: str):
        if self._stream_bubble:
            self._stream_bubble.append(chunk)
            self._scroll_unten()

    @QtCore.Slot()
    def _on_done(self):
        korrigiert = ""
        if self._stream_bubble:
            korrigiert = self._stream_bubble._text.strip()
            self._stream_bubble.finalize()
            self._stream_bubble = None

        original = self._letzter_eingabe_text
        if original and korrigiert and original.strip() != korrigiert.strip():
            diff_blase = DiffBlase(original, korrigiert)
            self._chat_layout.insertWidget(
                self._chat_layout.count() - 1, diff_blase)
            QtCore.QTimer.singleShot(50, self._scroll_unten)

        self._senden_btn.setEnabled(True)
        self._eingabe.setFocus()
        self._status_lbl.setText("✅ fertig")

    @QtCore.Slot(str)
    def _on_error(self, msg: str):
        if self._stream_bubble:
            self._stream_bubble.append(f"\n❌ {msg}")
            self._stream_bubble.finalize()
            self._stream_bubble = None
        self._senden_btn.setEnabled(True)
        self._status_lbl.setText(f"❌ {msg[:60]}")

    # ── Rechtschreib-Kontextmenü ──────────────────────────────────────────────

    def _kontext_menu(self, pos):
        menu = self._eingabe.createStandardContextMenu()

        if _HAT_RECHTSCHREIBUNG:
            cursor = self._eingabe.cursorForPosition(pos)
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            wort = cursor.selectedText().strip()

            if wort and not _SPELL_BACKEND.pruefen(wort):
                vorschlaege = _SPELL_BACKEND.vorschlaege(wort)
                menu.insertSeparator(menu.actions()[0])

                if vorschlaege:
                    for v in reversed(vorschlaege):
                        def _ersetze(w=v, c=cursor):
                            c.insertText(w)
                        akt = QtWidgets.QAction(v, menu)
                        akt.setFont(QtGui.QFont(
                            akt.font().family(),
                            akt.font().pointSize(),
                            QtGui.QFont.Bold))
                        akt.triggered.connect(_ersetze)
                        menu.insertAction(menu.actions()[0], akt)

                    kopf = QtWidgets.QAction(f'Vorschläge für "{wort}":', menu)
                    kopf.setEnabled(False)
                    menu.insertAction(menu.actions()[0], kopf)
                else:
                    kein = QtWidgets.QAction(
                        f'Keine Vorschläge für "{wort}"', menu)
                    kein.setEnabled(False)
                    menu.insertAction(menu.actions()[0], kein)

                menu.insertSeparator(menu.actions()[len(vorschlaege) + 1])

        menu.exec_(self._eingabe.mapToGlobal(pos))

    # ── Event-Filter: Enter, Drag-Drop, Strg+V ───────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self._eingabe:
            t = event.type()

            if t == QtCore.QEvent.KeyPress:
                key  = event.key()
                mods = event.modifiers()

                if (key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
                        and not (mods & QtCore.Qt.ShiftModifier)):
                    self._senden()
                    return True

                if key == QtCore.Qt.Key_V and (mods & QtCore.Qt.ControlModifier):
                    clipboard = QtWidgets.QApplication.clipboard()
                    if not clipboard.image().isNull():
                        self._bild_aus_zwischenablage()
                        return True

            elif t == QtCore.QEvent.DragEnter:
                md = event.mimeData()
                if md.hasImage():
                    event.acceptProposedAction()
                    return True
                if md.hasUrls():
                    for u in md.urls():
                        ext = u.toLocalFile().rsplit(".", 1)[-1]
                        if format_pruefen(_aktueller_anbieter(), ext):
                            event.acceptProposedAction()
                            return True

            elif t == QtCore.QEvent.Drop:
                md = event.mimeData()
                if md.hasImage():
                    img = QtGui.QImage(md.imageData())
                    if not img.isNull():
                        self._setze_bild(QtGui.QPixmap.fromImage(img))
                        return True
                if md.hasUrls():
                    for url in md.urls():
                        path = url.toLocalFile()
                        ext  = path.rsplit(".", 1)[-1] if "." in path else ""
                        if not format_pruefen(_aktueller_anbieter(), ext):
                            self._status_lbl.setText(
                                f"⚠ .{ext.upper()} wird von "
                                f"{_aktueller_anbieter()} nicht unterstützt")
                            return True
                        px = QtGui.QPixmap(path)
                        if not px.isNull():
                            self._setze_bild(px)
                            return True

        return super().eventFilter(obj, event)
