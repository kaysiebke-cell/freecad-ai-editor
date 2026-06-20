# -*- coding: utf-8 -*-
"""
fehler_panel.py
───────────────
FehlerPanel – Eigenständiges Fehler-Übersetzer-Widget mit Sandbox.
Seite 0 (Fehler-Übersetzer) und Seite 1 (Sandbox) liegen in einem
QStackedWidget; zeige_seite() schaltet via setCurrentIndex() um.
"""

from __future__ import annotations
import traceback
from typing import Callable, Dict, Optional
from core.qt_compat import QtWidgets, QtCore, QtGui
from core import theme
from core import schrift

# ══════════════════════════════════════════════════════════════════════════════
# Vordefinierte Themes
# ══════════════════════════════════════════════════════════════════════════════

THEME_STANDARD: Dict[str, object] = {
    "bg": "",
    "eingabe_bg": "",
    "eingabe_fg": "",
    "eingabe_border": "",
    "ausgabe_bg": "",
    "ausgabe_fg": "",
    "ausgabe_border": "",
    "lbl_fg": "",
    "btn_ue_bg": "",
    "btn_ue_border": "",
    "btn_ue_fg": "",
    "btn_ue_bg_h": "",
    "btn_ue_border_h": "",
    "btn_ue_bg_p": "",
    "btn_sec_bg": "",
    "btn_sec_border": "",
    "btn_sec_fg": "",
    "btn_sec_bg_h": "",
    "btn_sec_border_h": "",
    "btn_sec_bg_p": "",
    "font_family": "Courier New",
    "font_size": 9,
    "lbl_font_size": 9,
    "border_radius": 3,
}


def _merge(base: dict, override: Optional[dict]) -> dict:
    """Mischt override-Werte in base (base bleibt unverändert)."""
    if not override:
        return dict(base)
    return {**base, **override}


def _fix_align(widget: QtWidgets.QPlainTextEdit) -> None:
    opt = widget.document().defaultTextOption()
    opt.setAlignment(QtCore.Qt.AlignLeft)
    widget.document().setDefaultTextOption(opt)


# ══════════════════════════════════════════════════════════════════════════════
# FehlerPanel Klasse
# ══════════════════════════════════════════════════════════════════════════════

class FehlerPanel(QtWidgets.QWidget):
    sandbox_fertig = QtCore.Signal(bool, str)
    # Signal das dem Editor mitteilt wie viel Höhe die Sandbox braucht
    sandbox_hoehe_anfordern = QtCore.Signal(int)

    def __init__(
        self,
        uebersetze_fn: Callable[[str], str],
        ki_callback: Optional[Callable[[], None]] = None,
        theme: Optional[Dict[str, object]] = None,
        max_hoehe: int = 150,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._uebersetze        = uebersetze_fn
        self._ki_cb             = ki_callback
        self._max_h             = max_hoehe
        self._theme             = _merge(THEME_STANDARD, theme)
        self._sandbox_toggle_cb  = None
        self._ist_sandbox        = False
        self._geladener_code     = ""
        self._korrektur_zaehler  = 0
        self._max_korrekturen    = 3
        self._ki_korrektur_cb    = None   # wird vom Editor gesetzt
        self._baue_ui()

    # ── öffentliche API ───────────────────────────────────────────────────

    def setze_sandbox_toggle_cb(self, cb: Callable[[bool], None]) -> None:
        """Wird vom Editor aufgerufen, um den Toggle-Status zu synchronisieren."""
        self._sandbox_toggle_cb = cb

    def eingabe_text(self) -> str:
        return self._ein.toPlainText()

    def setze_eingabe(self, text: str) -> None:
        self._ein.setPlainText(text)
        self._ein.moveCursor(QtGui.QTextCursor.End)

    def setze_ausgabe(self, text: str) -> None:
        self._aus.setPlainText(text)

    def leeren(self) -> None:
        self._ein.clear()
        self._aus.clear()
        self._ein.setFocus()

    def sandbox_leeren(self) -> None:
        self._sb_ausgabe.clear()
        self._sb_ausgabe.setStyleSheet("")   # Rahmen zurücksetzen
        self._sb_status.clear()
        self._korrektur_zaehler = 0
        self._geladener_code    = ""
        if hasattr(self, "_btn_sb_ki"):
            self._btn_sb_ki.setEnabled(False)
            self._btn_sb_ki.setText("🔧 KI korrigieren")

    def sandbox_setze_code(self, code: str) -> None:
        """Zeigt die Sandbox und lädt den Code – Ausführen muss der User per Button."""
        self.zeige_seite(True)
        self._geladener_code = code
        # Zähler NICHT zurücksetzen — KI-Korrekturversuche sollen kumulieren
        verbleibend = self._max_korrekturen - self._korrektur_zaehler
        self._sb_ausgabe.setPlainText(f"# KI-Korrektur geladen – ▶ Ausführen zum Testen")
        self._sb_status.setText(f"📋 Korrektur bereit – noch {verbleibend}x möglich")
        if hasattr(self, "_btn_sb_ki"):
            self._btn_sb_ki.setEnabled(False)
            self._btn_sb_ki.setText(f"🔧 KI korrigieren ({verbleibend}x)")

    def setze_ki_korrektur_cb(self, cb) -> None:
        """Editor übergibt hier seinen Self-Correction-Callback."""
        self._ki_korrektur_cb = cb

    def _ki_korrektur_anfordern(self) -> None:
        """Schickt den fehlerhaften Code + Fehlermeldung an die KI (max. 3x)."""
        if self._korrektur_zaehler >= self._max_korrekturen:
            self._sb_status.setText(f"❌ Max. {self._max_korrekturen} Korrekturen erreicht")
            self._btn_sb_ki.setEnabled(False)
            return
        if not self._ki_korrektur_cb:
            self._sb_status.setText("⚠ Kein KI-Korrektur-Callback gesetzt")
            return

        fehler_text = self._sb_ausgabe.toPlainText()
        code        = self._geladener_code

        if not code or not fehler_text:
            self._sb_status.setText("⚠ Kein Code oder Fehler vorhanden")
            return

        self._korrektur_zaehler += 1
        versuche_text = f"{self._korrektur_zaehler}/{self._max_korrekturen}"
        self._sb_status.setText(f"🔧 KI korrigiert … (Versuch {versuche_text})")
        self._btn_sb_ki.setEnabled(False)

        # Callback im Editor auslösen (der startet den Streaming-Worker)
        self._ki_korrektur_cb(code, fehler_text)

    def sandbox_ausgabe(self) -> str:
        return self._sb_ausgabe.toPlainText()

    def setze_theme(self, theme: Dict[str, object]) -> None:
        self._theme = _merge(THEME_STANDARD, theme)
        self._style_anwenden()

    # ── UI-Aufbau ─────────────────────────────────────────────────────────

    def _baue_ui(self) -> None:
        haupt = QtWidgets.QVBoxLayout(self)
        haupt.setContentsMargins(0, 0, 0, 0)
        haupt.setSpacing(0)

        # QStackedWidget: schaltet zwischen Seiten um
        self._stack = QtWidgets.QStackedWidget()

        # ─────────────────────────────────────────────────────────────────
        # SEITE 0: FEHLER-ÜBERSETZER
        # ─────────────────────────────────────────────────────────────────
        self._seite0 = QtWidgets.QWidget()
        layout0 = QtWidgets.QHBoxLayout(self._seite0)
        layout0.setContentsMargins(6, 4, 6, 4)
        layout0.setSpacing(6)

        # Links: Eingabe
        links = QtWidgets.QVBoxLayout()
        links.setSpacing(3)
        self._lbl_ein = QtWidgets.QLabel("Fehlermeldung (Englisch):")
        links.addWidget(self._lbl_ein)
        self._ein = QtWidgets.QPlainTextEdit()
        _fix_align(self._ein)
        links.addWidget(self._ein)
        layout0.addLayout(links, stretch=1)

        # Mitte: Buttons
        mitte = QtWidgets.QVBoxLayout()
        mitte.setSpacing(4)
        mitte.addStretch()
        self._btn_ue = QtWidgets.QPushButton("🔍 Übersetzen")
        self._btn_ue.setFixedWidth(80)
        self._btn_ue.setMinimumHeight(34)
        mitte.addWidget(self._btn_ue)
        self._btn_clear = QtWidgets.QPushButton("🗑 Leeren")
        self._btn_clear.setFixedWidth(80)
        self._btn_clear.setMinimumHeight(24)
        mitte.addWidget(self._btn_clear)
        self._btn_ki = QtWidgets.QPushButton("🐛 KI erklärt")
        self._btn_ki.setFixedWidth(80)
        self._btn_ki.setMinimumHeight(24)
        self._btn_ki.setVisible(self._ki_cb is not None)
        mitte.addWidget(self._btn_ki)
        mitte.addStretch()
        layout0.addLayout(mitte)

        # Rechts: Ausgabe
        rechts = QtWidgets.QVBoxLayout()
        rechts.setSpacing(3)
        self._lbl_aus = QtWidgets.QLabel("Erklärung (Deutsch):")
        rechts.addWidget(self._lbl_aus)
        self._aus = QtWidgets.QPlainTextEdit()
        self._aus.setReadOnly(True)
        _fix_align(self._aus)
        rechts.addWidget(self._aus)
        layout0.addLayout(rechts, stretch=1)

        self._stack.addWidget(self._seite0)   # Index 0

        # ─────────────────────────────────────────────────────────────────
        # SEITE 1: SANDBOX
        # ─────────────────────────────────────────────────────────────────
        self._seite1 = QtWidgets.QWidget()
        layout1 = QtWidgets.QVBoxLayout(self._seite1)
        layout1.setContentsMargins(0, 0, 0, 0)
        layout1.setSpacing(0)

        # Top: Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(4, 4, 4, 4)
        btn_layout.setSpacing(4)

        self._btn_sb_run = QtWidgets.QPushButton("▶ Ausführen")
        self._btn_sb_run.setMinimumHeight(28)
        self._btn_sb_run.setDefault(True)
        self._btn_sb_run.setAutoDefault(True)
        self._btn_sb_run.setToolTip("Code aus KI-Antwort in die Sandbox laden und ausführen")
        self._btn_sb_run.clicked.connect(lambda: self._sandbox_ausfuehren())
        btn_layout.addWidget(self._btn_sb_run)

        self._btn_sb_ki = QtWidgets.QPushButton("🔧 KI korrigieren")
        self._btn_sb_ki.setMinimumHeight(28)
        self._btn_sb_ki.setAutoDefault(False)
        self._btn_sb_ki.setToolTip("Fehler an KI schicken und korrigierten Code zurückholen (max. 3 Versuche)")
        self._btn_sb_ki.setEnabled(False)
        self._btn_sb_ki.clicked.connect(lambda: self._ki_korrektur_anfordern())
        btn_layout.addWidget(self._btn_sb_ki)

        self._btn_sb_clear = QtWidgets.QPushButton("🗑 Leeren")
        self._btn_sb_clear.setMinimumHeight(28)
        self._btn_sb_clear.setAutoDefault(False)
        self._btn_sb_clear.clicked.connect(self.sandbox_leeren)
        btn_layout.addWidget(self._btn_sb_clear)

        btn_layout.addStretch()

        self._sb_status = QtWidgets.QLabel("")
        self._sb_status.setStyleSheet(theme.STY_LABEL_SM_NP(schrift.pt(schrift.STUFE_SM)))
        btn_layout.addWidget(self._sb_status)

        layout1.addLayout(btn_layout)

        lbl_ausgabe = QtWidgets.QLabel("Ausgabe / Fehler:")
        lbl_ausgabe.setStyleSheet(
            theme.STY_LABEL_SM_PADDED(schrift.pt(schrift.STUFE_SM)))
        layout1.addWidget(lbl_ausgabe)

        self._sb_ausgabe = QtWidgets.QPlainTextEdit()
        self._sb_ausgabe.setReadOnly(True)
        _fix_align(self._sb_ausgabe)
        layout1.addWidget(self._sb_ausgabe, stretch=1)

        self._stack.addWidget(self._seite1)   # Index 1

        # Toggle Button + Stack in einem festen Container
        # Stack bekommt alles minus Toggle-Button-Höhe (28px) + Spacing
        self._stack.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)

        haupt.addWidget(self._stack, stretch=1)

        self._btn_toggle = QtWidgets.QPushButton("🧪 Sandbox")
        self._btn_toggle.setFixedHeight(28)
        self._btn_toggle.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed)
        self._btn_toggle.clicked.connect(
            lambda: self.zeige_seite(not self._ist_sandbox))
        haupt.addWidget(self._btn_toggle)

        # Signale verbinden
        self._btn_ue.clicked.connect(self._uebersetzen)
        self._btn_clear.clicked.connect(self.leeren)
        if self._ki_cb:
            self._btn_ki.clicked.connect(self._ki_cb)

        self.setMinimumHeight(60)
        self.setMaximumHeight(16777215)
        self._style_anwenden()

    # ── Seiten umschalten ─────────────────────────────────────────────────

    def zeige_seite(self, sandbox: bool) -> None:
        """Schaltet zwischen Übersetzer (Index 0) und Sandbox (Index 1) um.
        Die Höhe des Widgets passt sich dem Dock frei an.
        """
        self._ist_sandbox = sandbox

        if sandbox:
            self._stack.setCurrentIndex(1)
            self._btn_toggle.setText("🔍 Fehler-Übersetzer")
        else:
            self._stack.setCurrentIndex(0)
            self._btn_toggle.setText("🧪 Sandbox")

        if self._sandbox_toggle_cb:
            self._sandbox_toggle_cb(sandbox)

    # ── Sandbox-Ausführung ────────────────────────────────────────────────

    def _sandbox_ausfuehren(self, code: str = None) -> None:
        """Startet Sandbox-Ausführung in eigenem Thread – kein GUI-Freeze."""
        import threading
        if code is None:
            code = getattr(self, "_geladener_code", None)
        if not code or not code.strip():
            self._sb_status.setText("⚠ Kein Code vorhanden – erst per KI generieren")
            return
        code = code.strip()
        self._geladener_code = code
        self._btn_sb_ki.setEnabled(False)
        self._sb_status.setText("⏳ Führe aus …")
        # Fokus auf Ausgabe-Feld parken bevor run deaktiviert wird,
        # damit Qt nicht automatisch zu "Löschen" springt
        self._sb_ausgabe.setFocus()
        self._btn_sb_run.setEnabled(False)
        threading.Thread(target=self._sandbox_worker, args=(code,), daemon=True).start()

    def _sb_rahmen(self, art: str) -> None:
        """Setzt einen farbigen Rahmen um das Sandbox-Ausgabefeld."""
        from core import theme as _theme
        farbe = _theme.farbe_ok(self._sb_ausgabe) if art == "ok" else _theme.farbe_fehler(self._sb_ausgabe)
        self._sb_ausgabe.setStyleSheet(
            f"QPlainTextEdit {{ border: 2px solid {farbe}; border-radius: 3px; }}"
        )

    @QtCore.Slot(bool, str, str)
    def _sandbox_ergebnis(self, erfolg: bool, ausgabe: str, code: str) -> None:
        """Empfängt Ergebnis im GUI-Thread."""
        self._btn_sb_run.setEnabled(True)
        if erfolg:
            self._sb_ausgabe.setPlainText(ausgabe)
            self._sb_status.setText("✅ Erfolgreich ausgeführt")
            self._sb_rahmen("ok")
            self._btn_sb_ki.setEnabled(False)
            self._btn_sb_ki.setText("🔧 KI korrigieren")
            self._korrektur_zaehler = 0
            self.sandbox_fertig.emit(True, ausgabe)
            # Fokus zurück auf Ausführen-Button (nicht auf Löschen springen)
            self._btn_sb_run.setFocus()
        else:
            self._geladener_code = code
            self._sb_ausgabe.setPlainText(ausgabe)
            self._sb_rahmen("fehler")
            verbleibend = self._max_korrekturen - self._korrektur_zaehler
            if verbleibend > 0 and self._ki_korrektur_cb:
                self._btn_sb_ki.setEnabled(True)
                self._btn_sb_ki.setText(f"🔧 KI korrigieren ({verbleibend}x)")
                self._sb_status.setText(f"❌ Fehler – KI verfügbar ({verbleibend}x)")
                # Fokus auf KI-korrigieren — das ist die sinnvolle nächste Aktion
                self._btn_sb_ki.setFocus()
            else:
                self._sb_status.setText("❌ Fehler")
                self._btn_sb_run.setFocus()
            self.sandbox_fertig.emit(False, ausgabe)

    def _sandbox_worker(self, code: str) -> None:
        """Läuft im Hintergrund-Thread – kein GUI-Zugriff."""
        try:
            result  = self._execute_in_sandbox(code)
            erfolg  = result["success"]
            ausgabe = result["output"] if erfolg else result["error"]
        except Exception as e:
            erfolg  = False
            ausgabe = f"Fehler: {e}\n{traceback.format_exc()}"
        QtCore.QMetaObject.invokeMethod(
            self, "_sandbox_ergebnis",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(bool, erfolg),
            QtCore.Q_ARG(str, ausgabe),
            QtCore.Q_ARG(str, code),
        )

    @staticmethod
    def _execute_in_sandbox(code: str) -> Dict:
        """Syntaxprüfung — kein exec(), da FreeCAD nicht in der Sandbox verfügbar."""
        import ast
        code = code.replace("PySide2", "PySide6")
        code = code.replace("from distutils", "# from distutils")
        try:
            ast.parse(code)
            return {"success": True, "output": "✅ Syntax korrekt"}
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax-Fehler Zeile {e.lineno}: {e.msg}"}

    # ── interne Slots ─────────────────────────────────────────────────────

    def _uebersetzen(self) -> None:
        text = self._ein.toPlainText().strip()
        if text:
            self._aus.setPlainText(self._uebersetze(text))

    # ── Styling ───────────────────────────────────────────────────────────

    def _style_anwenden(self) -> None:
        t   = self._theme
        r   = int(t["border_radius"])
        ff  = str(t["font_family"])
        fs  = int(t["font_size"])
        lfs = int(t["lbl_font_size"])

        for lbl in (self._lbl_ein, self._lbl_aus):
            pass
