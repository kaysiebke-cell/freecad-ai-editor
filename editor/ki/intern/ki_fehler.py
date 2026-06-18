# -*- coding: utf-8 -*-
"""
ki_fehler.py
────────────
KIFehlerUI – Fehler-Panel öffnen, KI-Fehler anzeigen, Selbstkorrektur.
"""

import re as _re
import time
import threading

from qt_compat import QtCore, QtWidgets
from kod_korrektor import freecad_code_korrigieren


class KIFehlerUI:
    """Verwaltet die Fehleranzeige und den Selbstkorrektur-Ablauf."""

    def __init__(self, controller):
        self._c = controller

    def fehler_anzeigen(self, fehlertext: str):
        """Öffnet das Fehler-Panel und füllt die Fehlermeldung ein."""
        if not self._c._fehler_inhalt.isVisible():
            self._c._fehler_inhalt.setVisible(True)
            self._c._btn_fehler_toggle.setText("▼")
            splitter = self._c._fehler_inhalt.parent().parent()
            if isinstance(splitter, QtWidgets.QSplitter):
                h = splitter.height()
                splitter.setSizes([int(h * 0.65), int(h * 0.35)])

        self._c._fehler_eingabe.setPlainText(fehlertext)

        from fehler import uebersetze_text
        self._c._fehler_ausgabe.setPlainText(uebersetze_text(fehlertext))

        self._c._set_status("⚠ Fehler erkannt → Fehler-Panel geöffnet")

    def on_ki_error(self, msg: str):
        """Slot für _ki_error-Signal: Fehlermeldung anzeigen und Panel öffnen."""
        self._c._chunk.stop_stream_timers()
        self._c._ki_area.setPlainText(msg)
        self._c._btn_ki.setEnabled(True)
        self._c._set_status("❌ Fehler – Details in der KI-Antwort")
        fehlertext = msg.replace("# ❌ Fehler:\n", "").strip()
        if fehlertext:
            self.fehler_anzeigen(fehlertext)

    def on_self_correction_needed(self, code: str, fehler: str):
        """Sandbox-Fehler an KI schicken – läuft vollständig im GUI-Thread."""
        if not hasattr(self._c, "_fehler_panel"):
            return

        source = self._c._src_box.currentText()
        model  = self._c._model_box.currentText()
        temp   = self._c._temp_box.value() if hasattr(self._c, "_temp_box") else 0.1

        if not source or not model:
            self._c._fehler_panel._sb_status.setText("⚠ Kein KI-Anbieter konfiguriert")
            return

        if not hasattr(self._c, "_korrektur_verlauf"):
            self._c._korrektur_verlauf = []
        self._c._korrektur_verlauf.append((code, fehler))

        from data.nl_generator import NL_SYSTEM_PROMPT
        system_prompt = (
            NL_SYSTEM_PROMPT
            + "\n\n━━━ KORREKTUR-MODUS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Antworte NUR mit dem korrigierten Python-Code.\n"
            "Kein erklärender Text, keine Markdown-Fences (``` oder ```python).\n"
            "Behalte alle Konstanten und Variablennamen aus dem Original."
        )

        verlauf_text = ""
        for i, (v_code, v_fehler) in enumerate(self._c._korrektur_verlauf[:-1], 1):
            verlauf_text += (
                f"\n━━━ Fehlgeschlagener Versuch {i} ━━━\n"
                f"Code:\n{v_code}\n"
                f"Fehler: {v_fehler}\n"
            )

        versuch_nr  = len(self._c._korrektur_verlauf)
        max_vers    = self._c._fehler_panel._max_korrekturen
        user_prompt = (
            f"Ich brauche einen korrekten FreeCAD-Python-Code. "
            f"Dies ist Korrekturversuch {versuch_nr}/{max_vers}.\n"
            + (f"\nVorherige fehlgeschlagene Versuche:{verlauf_text}" if verlauf_text else "")
            + f"\n━━━ Aktueller Code mit Fehler ━━━\n"
            f"{code}\n\n"
            f"Fehlermeldung:\n{fehler}\n\n"
            f"Analysiere den Fehler, beachte die Regeln aus dem System-Prompt "
            f"und gib NUR den vollständig korrigierten Code zurück."
        )

        self._c._ki_area.clear()
        self._c._chunk_buffer.clear()
        self._c._stream_token_count = 0
        self._c._stream_start_time  = time.monotonic()
        self._c._flush_timer.start()
        self._c._status_timer.start()
        self._c._btn_ki.setEnabled(False)
        self._c._set_status("🔧 KI korrigiert Sandbox-Fehler …")

        fehler_panel_ref = self._c._fehler_panel
        ki_area_ref      = self._c._ki_area
        set_status_ref   = self._c._set_status

        def _nach_stream():
            korrigiert = ki_area_ref.toPlainText().strip()
            korrigiert = _re.sub(r"```python|```", "", korrigiert).strip()
            if korrigiert:
                korrigiert, _ = freecad_code_korrigieren(korrigiert)

            def _gui_update():
                if korrigiert:
                    fehler_panel_ref.sandbox_setze_code(korrigiert)
                    set_status_ref("🔧 Korrektur bereit – ▶ Ausführen drücken")
                verbleibend = (fehler_panel_ref._max_korrekturen
                               - fehler_panel_ref._korrektur_zaehler)
                fehler_panel_ref._btn_sb_ki.setEnabled(verbleibend > 0)
                if verbleibend > 0:
                    fehler_panel_ref._btn_sb_ki.setText(
                        f"🔧 KI korrigieren ({verbleibend}x)")

            QtCore.QTimer.singleShot(0, _gui_update)
            try:
                self._c._ki_stream_done.disconnect(_nach_stream)
            except Exception:
                pass

        self._c._ki_stream_done.connect(_nach_stream)
        threading.Thread(
            target=self._c._streaming.worker_mit_system,
            args=(source, model, system_prompt, user_prompt, temp),
            daemon=True,
        ).start()
