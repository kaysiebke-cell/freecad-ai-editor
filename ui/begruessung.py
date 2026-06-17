# -*- coding: utf-8 -*-
"""
begruessung.py
──────────────
Einmaliger Begrüßungs-Assistent beim ersten Start.

Ablauf:
  Seite 0 – Demo-GIF + Willkommen
  Seite 1 – Anbieter wählen
  Seite 2 – API-Key eingeben  (entfällt bei Ollama / Später)
  Seite 3 – Fertig
"""

import os

from qt_compat import QtWidgets, QtCore, QtGui
import theme
import schrift
from params import speichere_api_key, erststart_erledigt

# ── GIF-Pfad: sucht erst assets/, dann direkt nebenan ────────────────────────
_HIER = os.path.dirname(os.path.abspath(__file__))
_GIF  = next(
    (p for p in [
        os.path.join(_HIER, "assets", "ki_makro_editor_demo.gif"),
        os.path.join(_HIER, "ki_makro_editor_demo.gif"),
    ] if os.path.isfile(p)),
    ""
)


# ── Hilfsfunktion: einheitliche Buttons ───────────────────────────────────────
def _mkbtn(text, primary=False, parent=None):
    b = QtWidgets.QPushButton(text, parent)
    b.setMinimumHeight(36)
    b.setCursor(QtCore.Qt.PointingHandCursor)
    if primary:
        b.setStyleSheet(theme.STY_PRIMARY_BTN(schrift.pt(schrift.STUFE_XL)))
    else:
        b.setStyleSheet(theme.STY_SECONDARY_BTN(schrift.pt(schrift.STUFE_LG)))
    return b


# ── Anbieter-Karten ────────────────────────────────────────────────────────────
_ANBIETER = [
    {"id": "ollama",    "icon": "🖥️", "name": "Ollama  (Lokal)",       "sub": "Kein API-Key · läuft auf deinem PC",    "color": "", "border": ""},
    {"id": "anthropic", "icon": "🤖", "name": "Anthropic  (Claude)",    "sub": "sk-ant-…  ·  claude-sonnet / haiku",    "color": "", "border": ""},
    {"id": "openai",    "icon": "✨", "name": "OpenAI  (ChatGPT)",      "sub": "sk-…  ·  gpt-4o / gpt-4o-mini",        "color": "", "border": ""},
    {"id": "github",    "icon": "🐙", "name": "GitHub Copilot",         "sub": "ghp_…  ·  gpt-4o / o1-mini",           "color": "", "border": ""},
    {"id": "later",     "icon": "⏭",  "name": "Später einrichten",      "sub": "Ohne KI starten – jederzeit nachholbar","color": "", "border": ""},
]


class AnbieterKarte(QtWidgets.QFrame):
    """Klickbare Anbieter-Auswahl-Karte."""
    geklickt = QtCore.Signal(str)

    def __init__(self, daten: dict, parent=None):
        super().__init__(parent)
        self._id     = daten["id"]
        self._color  = daten["color"]
        self._border = daten["border"]
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._apply_style(False)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        icon = QtWidgets.QLabel(daten["icon"])
        icon.setStyleSheet(theme.STY_ICON_BTN_BORDERLESS(schrift.pt(schrift.STUFE_ICON)))
        icon.setFixedWidth(32)
        layout.addWidget(icon)

        texte = QtWidgets.QVBoxLayout()
        texte.setSpacing(2)
        name = QtWidgets.QLabel(daten["name"])
        name.setStyleSheet(theme.STY_ABSCHNITT_LABEL_LG(schrift.pt(schrift.STUFE_XL)))
        sub = QtWidgets.QLabel(daten["sub"])
        sub.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
        texte.addWidget(name)
        texte.addWidget(sub)
        layout.addLayout(texte)
        layout.addStretch()

    def _apply_style(self, aktiv: bool):
        rand = "" if aktiv else self._border
        bg   = "" if aktiv else self._color
    def setAktiv(self, ja: bool):
        self._apply_style(ja)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.geklickt.emit(self._id)


# ── Haupt-Dialog ───────────────────────────────────────────────────────────────
class BegrüssungsDialog(QtWidgets.QDialog):

    _S_DEMO     = 0
    _S_ANBIETER = 1
    _S_APIKEY   = 2
    _S_FERTIG   = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Willkommen beim FreeCAD MultiAI Panel")
        self.setModal(True)
        self.setFixedWidth(460)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(
            QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setFont(QtGui.QFont("Ubuntu", 10))
        self.setStyleSheet(theme.STY_BEGRUESSUNG_DIALOG(schrift.pt(schrift.STUFE_LG)))

        self._anbieter_id = None
        self._karten: dict[str, AnbieterKarte] = {}
        self._movie = None

        self._stack = QtWidgets.QStackedWidget()
        self._stack.addWidget(self._seite_demo())
        self._stack.addWidget(self._seite_anbieter())
        self._stack.addWidget(self._seite_apikey())
        self._stack.addWidget(self._seite_fertig())

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._stack)

    # ── Seite 0: GIF-Intro ────────────────────────────────────────────────────
    def _seite_demo(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── GIF-Bereich ──────────────────────────────────────────────────────
        gif_wrap = QtWidgets.QWidget()
        gif_wrap.setFixedHeight(220)
        gif_box = QtWidgets.QVBoxLayout(gif_wrap)
        gif_box.setContentsMargins(0, 0, 0, 0)
        gif_box.setAlignment(QtCore.Qt.AlignCenter)

        self._gif_label = QtWidgets.QLabel()
        self._gif_label.setAlignment(QtCore.Qt.AlignCenter)
        self._gif_label.setFixedSize(460, 220)

        if os.path.isfile(_GIF):
            self._movie = QtGui.QMovie(_GIF)
            self._movie.setScaledSize(QtCore.QSize(460, 220))
            self._gif_label.setMovie(self._movie)
            self._movie.start()
        else:
            # Fallback: Pfad-Hinweis damit der User weiß wo das GIF hin muss
            self._gif_label.setText(
                "⚙️  FreeCAD MultiAI Panel\n\n"
                f"GIF nicht gefunden:\n{_GIF}"
            )
            self._gif_label.setStyleSheet(
                theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
            self._gif_label.setWordWrap(True)

        gif_box.addWidget(self._gif_label)
        v.addWidget(gif_wrap)

        # ── Trennlinie ───────────────────────────────────────────────────────
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(theme.STY_BORDER_NONE)
        v.addWidget(sep)

        # ── Info-Bereich ─────────────────────────────────────────────────────
        info = QtWidgets.QWidget()
        info.setStyleSheet(theme.STY_BORDER_NONE)
        ib = QtWidgets.QVBoxLayout(info)
        ib.setContentsMargins(28, 18, 28, 20)
        ib.setSpacing(0)

        titel = QtWidgets.QLabel("⚙️  FreeCAD MultiAI Panel")
        titel.setStyleSheet(theme.STY_ABSCHNITT_LABEL_LG(schrift.pt(schrift.STUFE_XL)))
        sub = QtWidgets.QLabel(
            "Schreibe, analysiere und debugge FreeCAD-Makros\n"
            "mit KI-Unterstützung — lokal oder in der Cloud."
        )
        sub.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
        sub.setWordWrap(True)

        ib.addWidget(titel)
        ib.addSpacing(5)
        ib.addWidget(sub)
        ib.addSpacing(12)

        merkmale = QtWidgets.QLabel("🤖 KI  ·  📦 Snippets  ·  💡 API-Hints  ·  ⚠ Fehler-Debug")
        merkmale.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_BASE)))
        ib.addWidget(merkmale)
        ib.addSpacing(16)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)
        btn_skip = _mkbtn("Überspringen")
        btn_los  = _mkbtn("Einrichten →", primary=True)
        btn_row.addWidget(btn_skip)
        btn_row.addWidget(btn_los, stretch=1)
        ib.addLayout(btn_row)

        v.addWidget(info)

        # Verbindungen — NACH dem Aufbau, damit self._stack garantiert existiert
        def _zu_anbieter():
            if self._movie:
                self._movie.stop()
            self._stack.setCurrentIndex(self._S_ANBIETER)

        btn_skip.clicked.connect(_zu_anbieter)
        btn_los.clicked.connect(_zu_anbieter)

        return w

    # ── Seite 1: Anbieter ─────────────────────────────────────────────────────
    def _seite_anbieter(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(28, 28, 28, 24)
        v.setSpacing(0)

        schritt = QtWidgets.QLabel("SCHRITT 1 VON 2")
        schritt.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_BASE)))
        titel = QtWidgets.QLabel("Welchen KI-Anbieter möchtest du nutzen?")
        titel.setStyleSheet(theme.STY_ABSCHNITT_LABEL_LG(schrift.pt(schrift.STUFE_XL)))
        titel.setWordWrap(True)
        hint = QtWidgets.QLabel("Kann jederzeit über die Toolbar oben links geändert werden.")
        hint.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
        hint.setWordWrap(True)

        v.addWidget(schritt)
        v.addSpacing(6)
        v.addWidget(titel)
        v.addSpacing(4)
        v.addWidget(hint)
        v.addSpacing(18)

        for daten in _ANBIETER:
            karte = AnbieterKarte(daten)
            karte.geklickt.connect(self._anbieter_gewaehlt)
            self._karten[daten["id"]] = karte
            v.addWidget(karte)
            v.addSpacing(6)

        v.addStretch(1)
        return w

    # ── Seite 2: API-Key ──────────────────────────────────────────────────────
    def _seite_apikey(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(28, 28, 28, 24)
        v.setSpacing(0)

        schritt = QtWidgets.QLabel("SCHRITT 2 VON 2")
        schritt.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_BASE)))
        self._key_titel = QtWidgets.QLabel("API-Schlüssel eingeben")
        self._key_titel.setStyleSheet(theme.STY_ABSCHNITT_LABEL_LG(schrift.pt(schrift.STUFE_XL)))
        self._key_hint = QtWidgets.QLabel("Wird in den FreeCAD-Einstellungen gespeichert.")
        self._key_hint.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
        self._key_hint.setWordWrap(True)

        v.addWidget(schritt)
        v.addSpacing(6)
        v.addWidget(self._key_titel)
        v.addSpacing(4)
        v.addWidget(self._key_hint)
        v.addSpacing(22)

        self._key_label = QtWidgets.QLabel("Anthropic API-Key (sk-ant-…)")
        self._key_label.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
        self._key_feld = QtWidgets.QLineEdit()
        self._key_feld.setEchoMode(QtWidgets.QLineEdit.Password)
        self._key_feld.setPlaceholderText("sk-ant-api03-…")
        self._key_feld.setMinimumHeight(38)

        self._toggle_vis = QtWidgets.QCheckBox("Schlüssel anzeigen")
        self._toggle_vis.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
        self._toggle_vis.stateChanged.connect(
            lambda s: self._key_feld.setEchoMode(
                QtWidgets.QLineEdit.Normal if s == QtCore.Qt.Checked
                else QtWidgets.QLineEdit.Password
            )
        )

        warnung = QtWidgets.QLabel(
            "⚠  Schlüssel werden unverschlüsselt in den FreeCAD-Einstellungen\n"
            "    gespeichert. Keine Schlüssel mit vollen Konto-Berechtigungen nutzen."
        )
        warnung.setStyleSheet(theme.STY_WARN_BOX(schrift.pt(schrift.STUFE_BASE)))
        warnung.setWordWrap(True)

        v.addWidget(self._key_label)
        v.addSpacing(6)
        v.addWidget(self._key_feld)
        v.addSpacing(6)
        v.addWidget(self._toggle_vis)
        v.addSpacing(16)
        v.addWidget(warnung)
        v.addStretch(1)
        v.addSpacing(16)

        btn_row = QtWidgets.QHBoxLayout()
        btn_zurueck = _mkbtn("← Zurück")
        btn_zurueck.clicked.connect(lambda: self._stack.setCurrentIndex(self._S_ANBIETER))
        btn_weiter  = _mkbtn("Speichern & starten →", primary=True)
        btn_weiter.clicked.connect(self._key_speichern)
        btn_row.addWidget(btn_zurueck)
        btn_row.addWidget(btn_weiter, stretch=1)
        v.addLayout(btn_row)
        return w

    # ── Seite 3: Fertig ───────────────────────────────────────────────────────
    def _seite_fertig(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(28, 40, 28, 32)
        v.setSpacing(0)
        v.setAlignment(QtCore.Qt.AlignCenter)

        check = QtWidgets.QLabel("✅")
        check.setStyleSheet(theme.STY_ICON_BTN_BORDERLESS(schrift.pt(schrift.STUFE_ICON)))
        check.setAlignment(QtCore.Qt.AlignCenter)

        self._fertig_titel = QtWidgets.QLabel("Alles bereit!")
        self._fertig_titel.setStyleSheet(theme.STY_ABSCHNITT_LABEL_LG(schrift.pt(schrift.STUFE_XL)))
        self._fertig_titel.setAlignment(QtCore.Qt.AlignCenter)

        self._fertig_text = QtWidgets.QLabel("")
        self._fertig_text.setStyleSheet(theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_LG)))
        self._fertig_text.setAlignment(QtCore.Qt.AlignCenter)
        self._fertig_text.setWordWrap(True)

        tipp = QtWidgets.QLabel(
            "💡 Tipp: Trage einmalig einen Projekt-Kontext\n"
            "im gelben Feld ein — dann kennt die KI dein Projekt."
        )
        tipp.setStyleSheet(theme.STY_TIPP_BOX(schrift.pt(schrift.STUFE_LG)))
        tipp.setAlignment(QtCore.Qt.AlignCenter)
        tipp.setWordWrap(True)

        btn_los = _mkbtn("Editor öffnen →", primary=True)
        btn_los.clicked.connect(self._abschluss)

        v.addWidget(check)
        v.addSpacing(14)
        v.addWidget(self._fertig_titel)
        v.addSpacing(8)
        v.addWidget(self._fertig_text)
        v.addSpacing(28)
        v.addWidget(tipp)
        v.addStretch(1)
        v.addWidget(btn_los)
        return w

    # ── Logik ─────────────────────────────────────────────────────────────────
    def _anbieter_gewaehlt(self, anbieter_id: str):
        for k in self._karten.values():
            k.setAktiv(False)
        self._karten[anbieter_id].setAktiv(True)
        self._anbieter_id = anbieter_id

        if anbieter_id in ("ollama", "later"):
            self._zeige_fertig(anbieter_id)
        else:
            texte = {
                "anthropic": ("Anthropic API-Key (sk-ant-…)", "sk-ant-api03-…"),
                "openai":    ("OpenAI API-Key (sk-…)",         "sk-…"),
                "github":    ("GitHub Copilot Token (ghp_…)",  "ghp_…"),
            }
            label, placeholder = texte.get(anbieter_id, ("API-Key", ""))
            self._key_label.setText(label)
            self._key_feld.setPlaceholderText(placeholder)
            self._key_feld.clear()
            self._stack.setCurrentIndex(self._S_APIKEY)

    def _key_speichern(self):
        key = self._key_feld.text().strip()
        if self._anbieter_id and key:
            speichere_api_key(self._anbieter_id, key)
        self._zeige_fertig(self._anbieter_id)

    def _zeige_fertig(self, anbieter_id: str):
        texte = {
            "ollama":    "Ollama auf localhost:11434 wird verwendet.\nKein API-Key benötigt.",
            "anthropic": "Dein Anthropic-Schlüssel wurde gespeichert.\nClaude ist jetzt einsatzbereit.",
            "openai":    "Dein OpenAI-Schlüssel wurde gespeichert.\nGPT-4o ist jetzt einsatzbereit.",
            "github":    "Dein GitHub-Token wurde gespeichert.\nCopilot ist jetzt einsatzbereit.",
            "later":     "Du kannst die KI jederzeit über\ndie Toolbar oben links einrichten.",
        }
        self._fertig_text.setText(texte.get(anbieter_id or "later", ""))
        self._stack.setCurrentIndex(self._S_FERTIG)

    def _abschluss(self):
        erststart_erledigt()
        self.accept()


# ── Öffentliche Start-Funktion ────────────────────────────────────────────────
def zeige_begruessung(parent=None):
    erststart_erledigt()  # sofort markieren – egal wie der Dialog geschlossen wird
    dlg = BegrüssungsDialog(parent)
    dlg.exec()
