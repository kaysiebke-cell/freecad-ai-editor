# -*- coding: utf-8 -*-
"""
freecad_helfer_panel.py
───────────────────────
Barrierefreiheits-Helfer für Legastheniker und FreeCAD-Einsteiger.

Nimmt frei geschriebenen deutschen Text (Rechtschreibung egal) und
lässt Ollama daraus eine saubere, präzise FreeCAD-Beschreibung machen.
Optional kann ein Bild (Skizze, Foto, Handzeichnung) mitgeschickt werden —
Vision-fähige Modelle (llava, moondream) sehen dann Text + Bild zusammen.

Keine hardkodierten Farben — alles über QPalette (hell + dunkel).
"""

import base64
import difflib
import html
import json
import re
import sys
import threading

from qt_compat import QtCore, QtWidgets, QtGui
import theme

# anbieter_formate liegt in data/ — Pfad einmalig eintragen wenn nötig
try:
    from anbieter_formate import datei_filter, format_info, format_pruefen
except ImportError:
    import os as _os
    _data = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), "..", "data"))
    if _data not in sys.path:
        sys.path.insert(0, _data)
    try:
        from anbieter_formate import datei_filter, format_info, format_pruefen
    except ImportError:
        # Fallback wenn Datei fehlt
        def datei_filter(_): return "Bilder (*.png *.jpg *.jpeg *.webp *.gif *.bmp)"
        def format_info(_):  return ""
        def format_pruefen(_, e): return True

def _aktueller_anbieter() -> str:
    """Liest den aktuell in den Einstellungen gewählten KI-Anbieter."""
    try:
        from params import lade_quelle
        return lade_quelle()
    except Exception:
        return "Ollama (Lokal)"

# ── Rechtschreibprüfung — Fallback-Kette ─────────────────────────────────────
class _SpellBackend:
    def pruefen(self, wort: str) -> bool: return True
    def vorschlaege(self, wort: str) -> list[str]: return []

class _EnchantBackend(_SpellBackend):
    def __init__(self):
        import enchant as _e
        self._d = _e.Dict("de_DE")
    def pruefen(self, wort): return self._d.check(wort)
    def vorschlaege(self, wort): return self._d.suggest(wort)[:8]

class _SpellcheckerBackend(_SpellBackend):
    def __init__(self):
        from spellchecker import SpellChecker
        self._s = SpellChecker(language="de")
    def pruefen(self, wort): return not self._s.unknown([wort])
    def vorschlaege(self, wort):
        c = self._s.candidates(wort)
        return sorted(c)[:8] if c else []

def _lade_backend() -> tuple[_SpellBackend, str]:
    for Klasse, name in [(_EnchantBackend, "enchant"),
                         (_SpellcheckerBackend, "pyspellchecker")]:
        try:
            return Klasse(), name
        except Exception:
            continue
    return _SpellBackend(), ""

_SPELL_BACKEND, _SPELL_NAME = _lade_backend()
_HAT_RECHTSCHREIBUNG = bool(_SPELL_NAME)


class _RechtschreibHighlighter(QtGui.QSyntaxHighlighter):
    """Unterstreicht falsch geschriebene Wörter rot während des Tippens."""

    _WORT_RE = re.compile(r"\b[A-Za-zÄäÖöÜüß]{2,}\b")

    def __init__(self, dokument):
        super().__init__(dokument)
        self._format = QtGui.QTextCharFormat()
        self._format.setUnderlineStyle(
            QtGui.QTextCharFormat.SpellCheckUnderline)
        self._format.setUnderlineColor(QtGui.QColor("red"))

    def highlightBlock(self, text):
        if not _HAT_RECHTSCHREIBUNG:
            return
        for m in self._WORT_RE.finditer(text):
            wort = m.group()
            if not _SPELL_BACKEND.pruefen(wort):
                self.setFormat(m.start(), len(wort), self._format)


# ── Ollama ────────────────────────────────────────────────────────────────────
from qt_compat import requests as _requests, HAS_REQUESTS as _HAS_REQUESTS

OLLAMA_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = (
    "Du korrigierst Text für FreeCAD-Anfragen. Antworte IMMER auf Deutsch. "
    "Keine Erklärungen, keine Anweisungen, keine Kommentare.\n\n"
    "Nimm den Text des Nutzers und gib ihn zurück — grammatikalisch korrekt, "
    "klare Rechtschreibung, präzise deutsche Fachbegriffe für FreeCAD. "
    "Fehlende Maße ergänze sinnvoll. Nichts weiter. "
    "Nur der korrigierte Text, auf Deutsch."
)

# ── Vision-Modell-Erkennung ───────────────────────────────────────────────────
_VISION_SCHLUESSEL = ("llava", "bakllava", "moondream", "vision", "minicpm-v")

def _ist_vision_modell(name: str) -> bool:
    """Gibt True zurück wenn das Ollama-Modell Bilder verarbeiten kann."""
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
    """Konvertiert QPixmap in Base64-String für die Ollama-API (images-Feld)."""
    ba  = QtCore.QByteArray()
    buf = QtCore.QBuffer(ba)
    buf.open(QtCore.QIODevice.WriteOnly)
    pixmap.save(buf, "PNG")
    buf.close()
    return base64.b64encode(bytes(ba)).decode("ascii")


# ── Diff-Anzeige ──────────────────────────────────────────────────────────────
def _berechne_diff_html(original: str, korrigiert: str, widget: QtWidgets.QWidget) -> str:
    pal    = widget.palette()
    dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
    rot    = QtGui.QColor.fromHsl(4,  210, 80 if dunkel else 45).name()
    gruen  = QtGui.QColor.fromHsl(130, 180, 80 if dunkel else 40).name()

    w_orig = original.split()
    w_korr = korrigiert.split()
    matcher = difflib.SequenceMatcher(None, w_orig, w_korr, autojunk=False)
    teile   = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            teile.append(html.escape(" ".join(w_orig[i1:i2])))
        elif tag == "replace":
            for w in w_orig[i1:i2]:
                teile.append(
                    f'<span style="color:{rot};text-decoration:line-through;">'
                    f'{html.escape(w)}</span>')
            for w in w_korr[j1:j2]:
                teile.append(
                    f'<span style="color:{gruen};font-weight:bold;">'
                    f'{html.escape(w)}</span>')
        elif tag == "delete":
            for w in w_orig[i1:i2]:
                teile.append(
                    f'<span style="color:{rot};text-decoration:line-through;">'
                    f'{html.escape(w)}</span>')
        elif tag == "insert":
            for w in w_korr[j1:j2]:
                teile.append(
                    f'<span style="color:{gruen};font-weight:bold;">'
                    f'{html.escape(w)}</span>')
    return " ".join(teile)


class _DiffBlase(QtWidgets.QFrame):
    def __init__(self, original: str, korrigiert: str, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        kopf = QtWidgets.QLabel("✏️ Deine Korrekturen:")
        kopf.setStyleSheet(theme.STY_HELFER_BLASE_KOPF())
        layout.addWidget(kopf)

        self._lbl = QtWidgets.QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setTextFormat(QtCore.Qt.RichText)
        self._lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(self._lbl)

        self._original   = original
        self._korrigiert = korrigiert
        QtCore.QTimer.singleShot(50, self._render)

    def _render(self):
        diff = _berechne_diff_html(self._original, self._korrigiert, self)
        self._lbl.setText(diff)
        pal    = self.palette()
        dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
        bg     = QtGui.QColor.fromHsl(50, 60, 40 if dunkel else 220)
        fg     = pal.color(QtGui.QPalette.WindowText)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg.name()}; border-radius: 8px; }}")
        self._lbl.setStyleSheet(theme.STY_HELFER_DIFF_TEXT(fg.name()))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.PaletteChange:
            self._render()
        super().changeEvent(event)


# ── Chat-Blase ────────────────────────────────────────────────────────────────
class _ChatBubble(QtWidgets.QFrame):
    def __init__(self, text: str, rolle: str, parent=None):
        super().__init__(parent)
        self._rolle = rolle
        self._text  = text

        outer = QtWidgets.QHBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(8)

        avatar = QtWidgets.QLabel("🤖" if rolle == "ki" else "🧑")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(QtCore.Qt.AlignCenter)
        outer.addWidget(avatar) if rolle == "ki" else outer.addSpacing(40)

        bubble = QtWidgets.QFrame()
        blay   = QtWidgets.QVBoxLayout(bubble)
        blay.setContentsMargins(12, 8, 12, 8)
        blay.setSpacing(4)

        self._lbl = QtWidgets.QLabel(text)
        self._lbl.setWordWrap(True)
        self._lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        blay.addWidget(self._lbl)

        if rolle == "ki":
            self._copy_btn = QtWidgets.QPushButton("📋  Kopieren")
            self._copy_btn.setVisible(bool(text))
            self._copy_btn.clicked.connect(self._kopieren)
            blay.addWidget(self._copy_btn)
        else:
            self._copy_btn = None

        outer.addWidget(bubble, 1)
        outer.addWidget(avatar) if rolle == "nutzer" else outer.addSpacing(40)

        self._bubble = bubble
        self._aktualisiere_farben()

    def _aktualisiere_farben(self):
        pal    = self.palette()
        base   = pal.color(QtGui.QPalette.Base)
        dunkel = base.lightness() < 128
        if self._rolle == "ki":
            hue, sat, lit_d, lit_h = 220, 80, 45, 210
        else:
            hue, sat, lit_d, lit_h = 260, 60, 50, 205
        lit = lit_d if dunkel else lit_h
        bg  = QtGui.QColor.fromHsl(hue, sat, lit)
        fg  = pal.color(QtGui.QPalette.WindowText)
        self._bubble.setStyleSheet(
            f"QFrame {{ background-color: {bg.name()}; border-radius: 10px; }}")
        self._lbl.setStyleSheet(theme.STY_HELFER_BUBBLE_TEXT(fg.name()))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.PaletteChange:
            self._aktualisiere_farben()
        super().changeEvent(event)

    def append(self, chunk: str):
        self._text += chunk
        self._lbl.setText(self._text)

    def finalize(self):
        if self._copy_btn:
            self._copy_btn.setVisible(True)

    def _kopieren(self):
        QtWidgets.QApplication.clipboard().setText(self._text)
        self._copy_btn.setText("✅  Kopiert!")
        QtCore.QTimer.singleShot(
            2500, lambda: self._copy_btn.setText("📋  Kopieren"))


# ── Bild-Vorschau ─────────────────────────────────────────────────────────────
class _BildVorschau(QtWidgets.QFrame):
    """Zeigt das angehängte Bild als Thumbnail mit Entfernen-Button."""

    entfernt = QtCore.Signal()

    def __init__(self, pixmap: QtGui.QPixmap, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Thumbnail
        thumb = QtWidgets.QLabel()
        thumb.setFixedSize(72, 72)
        thumb.setAlignment(QtCore.Qt.AlignCenter)
        thumb.setPixmap(pixmap.scaled(
            72, 72,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation))
        layout.addWidget(thumb)

        # Info + Entfernen-Button
        rechts = QtWidgets.QVBoxLayout()
        rechts.setSpacing(4)

        info = QtWidgets.QLabel(f"📎  {pixmap.width()} × {pixmap.height()} px")
        info.setStyleSheet(theme.STY_HELFER_BLASE_KOPF())
        rechts.addWidget(info)

        entf = QtWidgets.QPushButton("✕  Bild entfernen")
        entf.setFixedHeight(26)
        entf.setToolTip("Angehängtes Bild entfernen")
        entf.clicked.connect(self.entfernt)
        rechts.addWidget(entf)
        rechts.addStretch()

        layout.addLayout(rechts)
        layout.addStretch()

        self._aktualisiere_rahmen()

    def _aktualisiere_rahmen(self):
        pal    = self.palette()
        dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
        bg     = QtGui.QColor.fromHsl(200, 60, 38 if dunkel else 230)
        rand   = pal.color(QtGui.QPalette.Mid)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg.name()}; "
            f"border: 1px solid {rand.name()}; border-radius: 8px; }}")

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.PaletteChange:
            self._aktualisiere_rahmen()
        super().changeEvent(event)


# ── Haupt-Panel ───────────────────────────────────────────────────────────────
class FreecadHelferPanel(QtWidgets.QWidget):
    """
    Barrierefreiheits-Panel: frei geschriebener Text (+ optionales Bild)
    → saubere FreeCAD-Beschreibung via Ollama.
    """

    _chunk_signal = QtCore.Signal(str)
    _done_signal  = QtCore.Signal()
    _error_signal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stream_bubble  = None
        self._anhang_pixmap  = None          # QPixmap oder None
        self._letzter_eingabe_text = ""

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

        self._modell_box = QtWidgets.QComboBox()
        self._modell_box.setMinimumWidth(150)
        self._modell_box.setToolTip("Ollama-Modell auswählen")
        self._modell_box.currentTextChanged.connect(
            lambda _: self._pruefe_vision_modell())
        kopf.addWidget(QtWidgets.QLabel("Modell:"))
        kopf.addWidget(self._modell_box)

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

        self._chat_widget  = QtWidgets.QWidget()
        self._chat_layout  = QtWidgets.QVBoxLayout(self._chat_widget)
        self._chat_layout.setContentsMargins(4, 4, 4, 4)
        self._chat_layout.setSpacing(6)
        self._chat_layout.addStretch()
        self._scroll.setWidget(self._chat_widget)
        root.addWidget(self._scroll, 1)

        self._füge_bubble_ein(
            "Hallo! Schreib mir einfach, was du in FreeCAD bauen möchtest. "
            "Rechtschreibung ist egal — ich mache eine fertige Beschreibung daraus.\n\n"
            "Du kannst auch ein Bild (Skizze, Foto, Handzeichnung) anhängen — "
            "dann sehe ich Text und Bild zusammen.", "ki"
        ).finalize()

        # Eingabefeld (mit Drag-Drop)
        self._eingabe = QtWidgets.QPlainTextEdit()
        self._eingabe.setPlaceholderText(
            "z.B.  ich brauch einen kasten mit loch zum anschrauben an die wand …\n"
            "(Shift+Enter = neue Zeile  |  Enter = Senden)\n"
            "Bild hierher ziehen oder Strg+V zum Einfügen")
        self._eingabe.setMinimumHeight(120)
        self._eingabe.setAcceptDrops(True)
        self._eingabe.installEventFilter(self)
        self._highlighter = _RechtschreibHighlighter(self._eingabe.document())
        self._eingabe.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._eingabe.customContextMenuRequested.connect(self._kontext_menu)
        root.addWidget(self._eingabe)

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
        root.addLayout(bild_reihe)

        # Vision-Warnung (nur sichtbar wenn Bild angehängt + falsches Modell)
        self._vision_warnung = QtWidgets.QLabel("")
        self._vision_warnung.setWordWrap(True)
        self._vision_warnung.setStyleSheet(theme.STY_HELFER_VISION_WARN_BASE())
        self._vision_warnung.setVisible(False)
        root.addWidget(self._vision_warnung)

        # Bild-Vorschau-Container
        self._vorschau_container = QtWidgets.QWidget()
        self._vorschau_container.setLayout(QtWidgets.QVBoxLayout())
        self._vorschau_container.layout().setContentsMargins(0, 0, 0, 0)
        self._vorschau_container.setVisible(False)
        root.addWidget(self._vorschau_container)

        # Senden-Button
        self._senden_btn = QtWidgets.QPushButton("➤  Senden")
        self._senden_btn.setFixedHeight(32)
        self._senden_btn.setToolTip("Senden (Enter)")
        self._senden_btn.clicked.connect(self._senden)
        root.addWidget(self._senden_btn)

    # ── Modelle laden ─────────────────────────────────────────────────────────

    def _lade_modelle(self):
        modelle = _ollama_modelle()
        if modelle:
            self._modell_box.addItems(modelle)
            self._status_lbl.setText("✅ verbunden")
        else:
            self._status_lbl.setText("⚠ Ollama nicht gefunden")

    # ── Bild-Handling ─────────────────────────────────────────────────────────

    def _lade_bild(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Bild auswählen", "",
            datei_filter(_aktueller_anbieter()))
        if not path:
            return
        # Format-Prüfung anhand der Dateiendung
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

        # Altes Vorschau-Widget entfernen
        lay = self._vorschau_container.layout()
        for i in reversed(range(lay.count())):
            w = lay.itemAt(i).widget()
            if w:
                w.deleteLater()

        vorschau = _BildVorschau(pixmap)
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
        """Zeigt Warnung wenn Bild angehängt aber Modell kein Vision kann."""
        if self._anhang_pixmap is None:
            self._vision_warnung.setVisible(False)
            return
        modell = self._modell_box.currentText()
        if modell and not _ist_vision_modell(modell):
            pal    = self.palette()
            dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
            bg     = QtGui.QColor.fromHsl(40, 200, 40 if dunkel else 230).name()
            fg     = QtGui.QColor.fromHsl(40, 200, 200 if dunkel else 60).name()
            self._vision_warnung.setStyleSheet(
                theme.STY_HELFER_VISION_WARN(bg, fg))
            self._vision_warnung.setText(
                f"⚠  '{modell}' unterstützt keine Bilder. "
                f"Wechsle zu llava oder moondream — "
                f"das Bild wird sonst ignoriert.")
            self._vision_warnung.setVisible(True)
        else:
            self._vision_warnung.setVisible(False)

    # ── Chat-Blasen ───────────────────────────────────────────────────────────

    def _füge_bubble_ein(self, text: str, rolle: str) -> _ChatBubble:
        bubble = _ChatBubble(text, rolle)
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

        # Nutzer-Bubble (mit Bild-Hinweis wenn Bild angehängt)
        anzeige_text = text
        if self._anhang_pixmap is not None:
            px = self._anhang_pixmap
            anzeige_text = f"📎 {px.width()}×{px.height()} px\n\n{text}"
        self._füge_bubble_ein(anzeige_text, "nutzer")

        self._stream_bubble = self._füge_bubble_ein("", "ki")
        modell = self._modell_box.currentText() or "llama3"

        # Bild als Base64 vorbereiten (nur wenn Vision-Modell)
        bild_b64 = None
        if self._anhang_pixmap is not None and _ist_vision_modell(modell):
            bild_b64 = _pixmap_zu_base64(self._anhang_pixmap)
        elif self._anhang_pixmap is not None:
            self._status_lbl.setText("⚠ Bild ignoriert (kein Vision-Modell)")

        threading.Thread(
            target=self._worker,
            args=(modell, text, bild_b64),
            daemon=True
        ).start()

    def _worker(self, modell: str, text: str, bild_b64: str | None = None):
        nutzer_msg: dict = {"role": "user", "content": text}
        if bild_b64:
            nutzer_msg["images"] = [bild_b64]

        payload = json.dumps({
            "model":    modell,
            "stream":   True,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                nutzer_msg,
            ]
        }).encode("utf-8")

        try:
            import urllib.request as _ul
            req = _ul.Request(
                OLLAMA_URL, data=payload,
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
            self._done_signal.emit()
        except Exception as e:
            self._error_signal.emit(str(e))

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
            diff_blase = _DiffBlase(original, korrigiert)
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

            # Tastendruck
            if t == QtCore.QEvent.KeyPress:
                key  = event.key()
                mods = event.modifiers()

                # Enter = senden
                if (key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
                        and not (mods & QtCore.Qt.ShiftModifier)):
                    self._senden()
                    return True

                # Strg+V: erst auf Bild in Zwischenablage prüfen
                if key == QtCore.Qt.Key_V and (mods & QtCore.Qt.ControlModifier):
                    clipboard = QtWidgets.QApplication.clipboard()
                    if not clipboard.image().isNull():
                        self._bild_aus_zwischenablage()
                        return True   # Bild eingefügt, Text-Paste verhindern

            # Drag-Enter: akzeptieren wenn Bild oder unterstützte Datei
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

            # Drop: Bild laden + Format prüfen
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
