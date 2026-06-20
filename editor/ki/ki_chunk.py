# -*- coding: utf-8 -*-
"""
ki_chunk.py
───────────
KIChunkUI – Chunk-Puffer, Stream-Statusanzeige und Stream-Done-Verarbeitung.
"""

import time
import re as _re

from core.qt_compat import QtGui
from editor.ki.kod_korrektor import freecad_code_korrigieren, extrahiere_code_aus_nl_antwort, schneide_erklaerung_ab

_RE_CODE_FENCE = _re.compile(r"```python|```")


class KIChunkUI:
    """Puffert eingehende KI-Chunks und verarbeitet das Stream-Ende."""

    def __init__(self, controller):
        self._c = controller

    # ── Chunk-Puffer ──────────────────────────────────────────────────────

    def on_chunk(self, chunk: str):
        """Chunk puffern – das Schreiben übernimmt flush_chunks alle 30 ms."""
        self._c._chunk_buffer.append(chunk)
        self._c._stream_token_count += 1

    def flush_chunks(self):
        """Alle gepufferten Chunks in einem Rutsch in ki_area schreiben."""
        if not self._c._chunk_buffer:
            return
        text = "".join(self._c._chunk_buffer)
        self._c._chunk_buffer.clear()
        if getattr(self._c, "_warte_aktiv", False):
            self._c._warte_aktiv = False
            if hasattr(self._c, "_warte_timer"):
                self._c._warte_timer.stop()
            self._c._ki_area.clear()
        cursor = self._c._ki_area.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self._c._ki_area.setTextCursor(cursor)
        self._c._ki_area.ensureCursorVisible()

    # ── Status-Anzeige ────────────────────────────────────────────────────

    def update_stream_status(self):
        """Live-Anzeige auch wenn noch kein erster Token angekommen ist."""
        elapsed = time.monotonic() - self._c._stream_start_time
        if self._c._stream_token_count <= 0:
            self._c._status.setText(
                f"🧠 Modell denkt nach ... ({elapsed:.1f} s)")
        else:
            self._c._status.setText(
                f"✍️ Generiere Code ... "
                f"{self._c._stream_token_count} Token "
                f"({elapsed:.1f} s)")

    def stop_stream_timers(self):
        """Alle Stream-Timer anhalten und letzten Chunk flushen."""
        self._c._flush_timer.stop()
        self._c._status_timer.stop()
        self._c._warte_aktiv = False
        if hasattr(self._c, "_warte_timer"):
            self._c._warte_timer.stop()
        self.flush_chunks()

    # ── Stream-Ende ───────────────────────────────────────────────────────

    def on_stream_done(self):
        """Nach dem letzten Chunk: Code-Fences entfernen, Buttons aktivieren."""
        self.stop_stream_timers()
        elapsed = time.monotonic() - self._c._stream_start_time
        full    = self._c._ki_area.toPlainText()

        # Raw-Log für Diagnose
        import os as _os
        _log_pfad = _os.path.join(_os.path.expanduser("~"), "ollama_raw.txt")
        try:
            with open(_log_pfad, "w", encoding="utf-8") as _f:
                _f.write(full)
        except Exception:
            pass

        clean = _RE_CODE_FENCE.sub("", full).strip().replace("\t", "    ")
        if not clean:
            self._c._ki_area.setPlainText("# ❌ Leere Antwort")
            self._c._btn_ki.setEnabled(True)
            return

        if getattr(self._c, "_nl_antwort_aktiv", False):
            self._c._nl_antwort_aktiv = False
            clean = extrahiere_code_aus_nl_antwort(clean)
            clean = schneide_erklaerung_ab(clean)

        # FC14: Tool-Calls → FreeCAD-Python-Code
        if getattr(self._c, "_tc_modus_aktiv", False):
            self._c._tc_modus_aktiv = False
            from editor.ki.fc14_tool_calling import ist_tool_call_antwort, parse_und_generiere_code
            if ist_tool_call_antwort(clean):
                python_code = parse_und_generiere_code(clean)
                if python_code:
                    self._c._ki_area.setPlainText(python_code)
                    self._c._btn_ki.setEnabled(True)
                    self._c._btn_einfuegen.setEnabled(True)
                    self._c._btn_ersetzen.setEnabled(True)
                    self._c._set_status(
                        f"✅ Fertig – {self._c._stream_token_count} Token "
                        f"in {elapsed:.1f} s  → ✅ Ersetzen")
                    return
                else:
                    clean = f"# ❌ Tool-Calls konnten nicht konvertiert werden:\n{clean}"

        clean, korrigiert = freecad_code_korrigieren(clean)
        self._c._ki_area.setPlainText(clean)
        self._c._btn_ki.setEnabled(True)
        self._c._btn_einfuegen.setEnabled(True)
        self._c._btn_ersetzen.setEnabled(True)
        hinweis = "  ⚠ KI-Code automatisch korrigiert" if korrigiert else ""

        # FC13 Schrittweise: neuen Block automatisch anhängen
        if getattr(self._c, "_sw_modus_aktiv", False):
            self._c._sw_modus_aktiv = False
            vorhandener = self._c._editor.toPlainText().rstrip()
            clean = extrahiere_code_aus_nl_antwort(clean)
            clean = schneide_erklaerung_ab(clean)
            neue_zeilen = []
            for zeile in clean.splitlines():
                s = zeile.strip()
                if s.startswith("import FreeCAD") or s.startswith("import App"):
                    continue
                if s.startswith("doc = App.") or s.startswith("doc=App."):
                    continue
                neue_zeilen.append(zeile)
            neuer_block = "\n".join(neue_zeilen).strip()
            if neuer_block:
                import ast as _ast
                try:
                    _ast.parse(neuer_block)
                except SyntaxError as _se:
                    self._c._ki_area.setPlainText(
                        f"# ❌ Syntax-Fehler in KI-Antwort — NICHT angehängt\n"
                        f"# Zeile {_se.lineno}: {_se.msg}\n"
                        f"# Bitte Beschreibung umformulieren oder stärkeres Modell wählen.\n\n"
                        f"{neuer_block}")
                    self._c._set_status(
                        "❌ Syntax-Fehler im neuen Block – Editor unverändert")
                    return
                if vorhandener:
                    self._c._editor.setPlainText(vorhandener + "\n\n" + neuer_block)
                else:
                    self._c._editor.setPlainText(neuer_block)
                self._c._set_status(
                    f"✅ Schritt angehängt – {self._c._stream_token_count} Token "
                    f"in {elapsed:.1f} s{hinweis}")
            else:
                self._c._set_status("⚠ Neuer Block war leer – nichts angehängt")
            return

        self._c._set_status(
            f"✅ Fertig – {self._c._stream_token_count} Token in {elapsed:.1f} s  "
            f"→ ✅ Ersetzen{hinweis}")
