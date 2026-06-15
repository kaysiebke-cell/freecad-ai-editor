# -*- coding: utf-8 -*-
"""
editor_ki_mixin.py
──────────────────
KIMixin – Mixin-Klasse für MakroEditor mit der gesamten KI-Kommunikation:
  - Modell-Liste laden (Ollama, Anthropic, OpenAI, GitHub, OpenRouter)
  - 1-Klick-Analyse
  - Streaming-Worker-Thread + Chunk-Batching (50 ms Flush-Timer)
  - Antwort-Verarbeitung + Syntaxprüfung
  - Fehler-Anzeige
  [NEU] _erstelle_code_sitemap      – kompakter AST-Kontext für KI-Prompt
  [NEU] _extrahiere_fehler_kontext  – Code-Ausschnitt um Fehlerzeile
  [NEU] _ki_fehler_erklaeren        – 1-Klick Fehler an KI senden
  [NEU] _worker_mit_system          – Thread-sicherer Worker mit System-Prompt
  [FIX] _ki_fragen liest UI-Werte vor Thread-Start (Thread-Safety)
"""

import ast
import json
import os
import time
import threading

import re as _re

from qt_compat import QtCore, QtWidgets, QtGui

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

_RE_CODE_FENCE = _re.compile(r"```python|```")

# ── Context-Compacting-Parameter ──────────────────────────────────────────────
# Ungefähre Token-Schätzung: 1 Token ≈ 4 Zeichen
_ZEICHEN_PRO_TOKEN = 4
# Schwellwert: ab dieser Zeichenzahl im Verlauf wird komprimiert
_COMPACT_SCHWELLE  = 5_000    # ≈ 1 250 Token — früher komprimieren (war 12 000)
# Wie viele der neuesten Nachrichten werden NICHT komprimiert (immer erhalten)
_COMPACT_BEHALTEN  = 4
# Absolutes Nachrichten-Limit: älteste werden entfernt wenn überschritten
_VERLAUF_MAX_NACHRICHTEN = 20


def _schaetze_token(text: str) -> int:
    """Grobe Token-Schätzung: Zeichenlänge / 4."""
    return max(1, len(text) // _ZEICHEN_PRO_TOKEN)


from params import KI_PRESETS, lade_api_key


class KiController:
    """Mixin mit der gesamten KI-Funktionalität für MakroEditor."""

    # ── Modelle laden ─────────────────────────────────────────────────────
    def _refresh_models(self):
        self._model_box.clear()
        src = self._src_box.currentText()
        if src.startswith("Ollama"):
            if not _HAS_REQUESTS:
                self._model_box.addItem("requests fehlt")
                self._set_status("⚠  requests nicht installiert – KI nicht verfügbar")
                return
            try:
                r = _requests.get("http://localhost:11434/api/tags", timeout=3)
                r.raise_for_status()
                models = [m["name"] for m in r.json().get("models", [])]
                self._model_box.addItems(models or ["(keine Modelle)"])
                self._set_status(
                    f"🔄 Ollama: {len(models)} Modell(e) geladen" if models
                    else "⚠  Ollama: keine Modelle gefunden")
            except Exception as e:
                self._model_box.addItem(f"Ollama: {e}")
                self._set_status(f"⚠  Ollama nicht erreichbar: {e}")
        elif src.startswith("Anthropic"):
            models = [
                "claude-opus-4-6",
                "claude-sonnet-4-6",
                "claude-haiku-4-5-20251001",
            ]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Anthropic: {len(models)} Modelle geladen")
        elif src.startswith("OpenAI"):
            models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 OpenAI: {len(models)} Modelle geladen")
        elif src.startswith("GitHub"):
            models = ["gpt-4o", "gpt-4o-mini", "o1-mini"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 GitHub Copilot: {len(models)} Modelle geladen")
        elif src.startswith("DeepSeek"):
            models = ["deepseek-coder", "deepseek-chat", "deepseek-reasoner"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 DeepSeek: {len(models)} Modelle geladen")
        elif src.startswith("Gemini"):
            models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Gemini: {len(models)} Modelle geladen")
        elif src.startswith("Groq"):
            models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                      "mixtral-8x7b-32768", "gemma2-9b-it"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Groq: {len(models)} Modelle geladen")
        elif src.startswith("Mistral"):
            models = ["mistral-large-latest", "mistral-small-latest", "codestral-latest"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Mistral: {len(models)} Modelle geladen")
        elif src.startswith("Together"):
            models = ["meta-llama/Llama-3.3-70B-Instruct-Turbo",
                      "mistralai/Mixtral-8x7B-Instruct-v0.1",
                      "codellama/CodeLlama-34b-Instruct-hf"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Together AI: {len(models)} Modelle geladen")
        elif src.startswith("HuggingFace"):
            models = ["meta-llama/Llama-3.2-3B-Instruct",
                      "Qwen/Qwen2.5-Coder-32B-Instruct",
                      "mistralai/Mistral-7B-Instruct-v0.3"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 HuggingFace: {len(models)} Modelle geladen")
        elif src.startswith("xAI"):
            models = ["grok-3", "grok-3-mini", "grok-2"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 xAI: {len(models)} Modelle geladen")
        elif src.startswith("Fireworks"):
            models = ["accounts/fireworks/models/llama-v3p3-70b-instruct",
                      "accounts/fireworks/models/deepseek-coder-v2-instruct",
                      "accounts/fireworks/models/qwen2p5-coder-32b-instruct"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Fireworks AI: {len(models)} Modelle geladen")
        elif src.startswith("Moonshot"):
            models = ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Moonshot: {len(models)} Modelle geladen")
        elif src.startswith("Qwen"):
            models = ["qwen-coder-plus", "qwen-plus", "qwen-max",
                      "qwen2.5-coder-32b-instruct"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Qwen (Alibaba): {len(models)} Modelle geladen")
        elif src.startswith("Cohere"):
            models = ["command-a-03-2025", "command-r-plus", "command-r"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Cohere: {len(models)} Modelle geladen")
        elif src.startswith("SambaNova"):
            models = ["DeepSeek-R1", "Meta-Llama-3.3-70B-Instruct",
                      "Qwen2.5-Coder-32B-Instruct"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 SambaNova: {len(models)} Modelle geladen")
        elif src.startswith("MiniMax"):
            models = ["MiniMax-Text-01", "abab6.5s-chat"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 MiniMax: {len(models)} Modelle geladen")
        elif src.startswith("Llama"):
            models = ["Llama-4-Scout-17B-16E-Instruct-FP8",
                      "Llama-4-Maverick-17B-128E-Instruct-FP8",
                      "Llama-3.3-70B-Instruct"]
            self._model_box.addItems(models)
            self._set_status(f"🔄 Llama API: {len(models)} Modelle geladen")
        else:  # OpenRouter
            models = [
                "anthropic/claude-sonnet-4-5",
                "anthropic/claude-haiku-4-5",
                "google/gemini-pro-1.5",
                "openai/gpt-4o-mini",
            ]
            self._model_box.addItems(models)
            self._set_status(f"🔄 OpenRouter: {len(models)} Modelle geladen")

    # ── 1-Klick-Analyse ───────────────────────────────────────────────────
    def _auto_analyse(self):
        """Lädt den gesamten Editor-Inhalt und startet KI-Erklärung."""
        code = self._editor.toPlainText().strip()
        if not code:
            self._set_status("⚠  Editor ist leer – zuerst eine Datei laden")
            return
        self.find_area.setPlainText(code)
        preset_name = "★ Was macht dieser Code?"
        idx = self._preset_box.findText(preset_name)
        if idx >= 0:
            self._preset_box.setCurrentIndex(idx)
        self._set_status("🔎 Code geladen – KI-Anfrage läuft …")
        self._ki_fragen()

    # ══ Kontext-Helfer ════════════════════════════════════════════════════

    def _erstelle_code_sitemap(self, code_text: str) -> str:
        """
        Parst den Editor-Code per AST und liefert ein kompaktes Inhaltsverzeichnis
        (Klassen + Methoden + globale Funktionen).

        Wird von _ki_fragen() automatisch in den Prompt eingebettet, sodass
        die KI die Dateistruktur kennt ohne den Volltext zu sehen.
        Gibt "" zurück wenn der Code leer oder syntaktisch unvollständig ist.
        """
        if not code_text.strip():
            return ""
        try:
            root = ast.parse(code_text)
        except SyntaxError:
            return ""

        linien = []
        for node in root.body:
            if isinstance(node, ast.ClassDef):
                linien.append(f"Klasse {node.name} (Zeile {node.lineno}):")
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [a.arg for a in sub.args.args if a.arg != "self"]
                        linien.append(f"   └─ {sub.name}({', '.join(args)})")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                linien.append(
                    f"Funktion {node.name}({', '.join(args)}) (Zeile {node.lineno})")

        return "\n".join(linien) if linien else ""

    def _extrahiere_fehler_kontext(self, code_text: str, fehler_meldung: str,
                                    puffer: int = 5) -> str:
        """
        Sucht die Zeilennummer aus einem Traceback ('line 42' oder 'Zeile 42')
        und gibt den umgebenden Code-Ausschnitt zurück.
        Die fehlerhafte Zeile ist mit '──▶' markiert.
        Gibt "" zurück wenn keine Zeilennummer gefunden wird.
        """
        match = _re.search(r"(?:line|Zeile)\s+(\d+)", fehler_meldung, _re.IGNORECASE)
        if not match:
            return ""

        ziel   = int(match.group(1))
        zeilen = code_text.splitlines()
        start  = max(0, ziel - 1 - puffer)
        ende   = min(len(zeilen), ziel + puffer)

        block = []
        for i in range(start, ende):
            nr     = i + 1
            prefix = "──▶ " if nr == ziel else "    "
            block.append(f"{prefix}{nr:4d}: {zeilen[i]}")

        return "\n".join(block)

    def _ki_fehler_erklaeren(self):
        """
        Liest die Fehlermeldung aus _fehler_eingabe und sendet sie mit dem
        betroffenen Code-Ausschnitt an die KI.

        Button im Fehler-Panel ergänzen:
            btn_ki = QtWidgets.QPushButton('🐛 KI erklärt')
            btn_ki.clicked.connect(self._ki_fehler_erklaeren)
        """
        if not _HAS_REQUESTS:
            self._set_status("❌ requests-Modul nicht installiert")
            return

        fehler_widget = getattr(self, "_fehler_eingabe", None)
        if fehler_widget is None:
            self._set_status("⚠  Fehler-Panel nicht gefunden")
            return

        fehler_text = fehler_widget.toPlainText().strip()
        if not fehler_text:
            self._set_status("⚠  Fehler-Panel ist leer")
            return

        aktueller_code  = self._editor.toPlainText()
        code_ausschnitt = self._extrahiere_fehler_kontext(aktueller_code, fehler_text)

        if code_ausschnitt:
            system = (
                "Du bist ein FreeCAD-Python-Debugger. "
                "Der User hat einen Laufzeitfehler erhalten.\n"
                "Hier ist der relevante Code-Ausschnitt "
                "(──▶ markiert die fehlerhafte Zeile):\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{code_ausschnitt}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Erkläre kurz auf Deutsch, warum dieser Fehler auftritt, "
                "und liefere die korrigierte Fassung nur dieses Code-Blocks."
            )
        else:
            system = (
                "Du bist ein FreeCAD-Python-Debugger. "
                "Erkläre auf Deutsch, warum dieser Fehler auftritt und wie man ihn behebt."
            )

        user_prompt = f"Fehlermeldung:\n{fehler_text}"

        # UI-Werte VOR dem Thread-Start im Hauptthread sichern
        source_text = self._src_box.currentText()
        model_text  = self._model_box.currentText()
        temp_val    = self._temp_box.value()

        self._ki_area.clear()
        self._chunk_buffer.clear()
        self._stream_token_count = 0
        self._stream_start_time  = time.monotonic()
        self._flush_timer.start()
        self._status_timer.start()
        self._set_status("⏳ Verbinde mit KI ...")
        self._btn_ki.setEnabled(False)
        self._btn_ersetzen.setEnabled(False)

        threading.Thread(
            target=self._worker_mit_system,
            args=(source_text, model_text, system, user_prompt, temp_val),
            daemon=True
        ).start()

    def _worker_mit_system(self, source, model, system_prompt, user_prompt,
                            temperature=0.2, preset_name="", ki_modus=None):
        """Worker für Aufrufe mit separatem System-Prompt.

        preset_name und ki_modus werden im Hauptthread gesichert übergeben —
        niemals aus dem Worker-Thread von Qt-Widgets lesen.
        """
        from ki_modi import MODUS_DEFAULT, MODUS_ANFAENGER
        from nl_generator import (NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_PD,
                                   NL_PRESET_SCHLUESSEL_SW)
        if ki_modus is None:
            ki_modus = MODUS_DEFAULT
        ist_nl = preset_name in (
            NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_PD, NL_PRESET_SCHLUESSEL_SW)
        if ist_nl and ki_modus == MODUS_ANFAENGER:
            system_prompt = system_prompt.replace(
                "Nur reinen Python-Code ausgeben. Kein Erklärungstext nach dem Code.",
                "Nach dem Code: Genau 3 kurze deutsche Saetze als #-Kommentare:\n"
                "# 1. Was wurde erstellt\n"
                "# 2. Welche Standardwerte gewaehlt wurden\n"
                "# 3. Welche Konstante der Nutzer anpassen muss"
            )
        # "FreeCAD Part Workbench:" vorne — wenige Tokens, aber Ollama weiß sofort den Kontext
        from nl_generator import NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_SW
        if preset_name == NL_PRESET_SCHLUESSEL:
            user_prompt = f"FreeCAD Part Workbench:\n{user_prompt}"
        elif preset_name == NL_PRESET_SCHLUESSEL_SW:
            user_prompt = f"FreeCAD Part Workbench (Erweiterung):\n{user_prompt}"
        full = f"{system_prompt}\n\nFrage des Users:\n{user_prompt}"
        try:
            if self._alive:
                self._ki_chunk.emit("# ⏳ Anfrage an KI gesendet ...\n\n")
            self._stream_fuer_anbieter(source, model, full, temperature)
            if self._alive:
                self._ki_stream_done.emit()
        except Exception as e:
            if self._alive:
                self._ki_error.emit(f"# ❌ Fehler:\n{e}")

    # ── KI anfragen ───────────────────────────────────────────────────────
    def _ki_fragen(self):
        if not _HAS_REQUESTS:
            self._set_status("❌ requests-Modul nicht installiert")
            return

        # ── Code-Quelle bestimmen ──────────────────────────────────────
        code = self.find_area.toPlainText().strip()
        code_quelle = "suchfeld"
        if not code:
            # Fallback: Editor – aber max. 200 Zeilen (Speicher-Schutz)
            alle_zeilen = self._editor.toPlainText().splitlines()
            if not alle_zeilen:
                self._set_status("⚠  Suchfeld und Editor sind leer")
                return
            if len(alle_zeilen) > 200:
                code = "\n".join(alle_zeilen[:200]) + "\n# … [gekürzt auf 200 Zeilen]"
                self._set_status("ℹ  Suchfeld leer – sende erste 200 Zeilen des Editors")
            else:
                code = "\n".join(alle_zeilen)
                self._set_status("ℹ  Suchfeld leer – sende gesamten Editor-Inhalt")
            code_quelle = "editor"

        from nl_generator import (NL_SYSTEM_PROMPT, NL_PRESET_SCHLUESSEL,
                                   NL_SYSTEM_PROMPT_PARTDESIGN, NL_PRESET_SCHLUESSEL_PD,
                                   NL_SYSTEM_PROMPT_SCHRITTWEISE, NL_PRESET_SCHLUESSEL_SW)
        preset_name  = self._preset_box.currentText()
        ist_nl_modus = preset_name == NL_PRESET_SCHLUESSEL
        ist_pd_modus = preset_name == NL_PRESET_SCHLUESSEL_PD
        ist_sw_modus = preset_name == NL_PRESET_SCHLUESSEL_SW

        # ── FC12 + FC13: Harte Sperre bei Ollama ──────────────────────────
        if ist_sw_modus and self._src_box.currentText().startswith("Ollama"):
            from qt_compat import QtWidgets
            QtWidgets.QMessageBox.critical(
                self,
                "❌  FC13 · Schrittweise — Modell nicht unterstützt",
                "FC13 · Schrittweise aufbauen funktioniert nicht\n"
                "mit lokalen Ollama-Modellen (zu schwach für Teil-Blöcke).\n\n"
                "Bitte wechsle zu einem dieser Backends:\n"
                "  • Anthropic (Claude)\n"
                "  • OpenAI (GPT-4o)\n"
                "  • Llama API (Llama-3.3-70B)\n"
                "  • Groq\n\n"
                "Für einfache Part-Modelle mit Ollama: FC11 verwenden."
            )
            self._btn_ki.setEnabled(True)
            self._set_status("❌ FC13 benötigt ein stärkeres Modell – bitte Backend wechseln")
            return

        if ist_pd_modus:
            src_text = self._src_box.currentText()
            if src_text.startswith("Ollama"):
                from qt_compat import QtWidgets
                QtWidgets.QMessageBox.critical(
                    self,
                    "❌  FC12 · PartDesign — Modell nicht unterstützt",
                    "FC12 · PartDesign aus Beschreibung funktioniert nicht\n"
                    "mit lokalen Ollama-Modellen.\n\n"
                    "Bitte wechsle zu einem dieser Backends:\n"
                    "  • Anthropic (Claude)\n"
                    "  • OpenAI (GPT-4o)\n"
                    "  • GitHub Copilot\n"
                    "  • OpenRouter\n\n"
                    "Für einfache Part-Modelle steht FC11 zur Verfügung."
                )
                self._btn_ki.setEnabled(True)
                self._set_status(
                    "❌ FC12 benötigt Claude oder GPT-4o – bitte Backend wechseln")
                return

        prompt = KI_PRESETS.get(preset_name, "").strip()
        if not prompt:
            prompt = "Verbessere und kommentiere diesen Python-Code auf Deutsch."

        # Barrierefreiheit: Sprach-Zusätze an den Prompt anhängen
        try:
            from barrierefreiheit import BarrierefreiheitPanel as _BF
            if _BF.einfache_sprache():
                prompt += (
                    "\n\nWICHTIG: Antworte in einfacher Sprache. "
                    "Kurze Sätze. Einfache Wörter. Keine komplizierten Begriffe.")
            if _BF.fachbegriffe_erklaeren():
                prompt += (
                    "\nWenn du einen Fachbegriff verwendest, "
                    "erkläre ihn sofort danach in Klammern einfach.")
            if _BF.antwort_kurz():
                prompt += (
                    "\nHalte deine Antwort kurz und auf das Wesentliche beschränkt.")
        except Exception:
            pass

        kontext = self._kontext.toPlainText().strip()
        if kontext:
            prompt = f"Projektkontext: {kontext}\n\n{prompt}"

        self._btn_ki.setEnabled(False)
        self._btn_ersetzen.setEnabled(False)
        self._ki_area.clear()
        self._chunk_buffer.clear()
        self._stream_token_count = 0
        self._warte_dots = 0
        self._warte_aktiv = True
        self._stream_start_time  = time.monotonic()
        self._flush_timer.start()
        self._status_timer.start()
        if hasattr(self, "_warte_timer"):
            self._warte_timer.start()

        # ── Verlauf-Größe live in Statuszeile anzeigen (Fix C) ────────
        verlauf_kb = self._ki_verlauf_groesse() // 1024
        self._status.setText(
            f"🤖 Warte auf ersten Token … | Verlauf: {verlauf_kb} KB")

        # ── Sitemap: nur Struktur-Übersicht, kein voller Code-Text ────
        sitemap = self._erstelle_code_sitemap(self._editor.toPlainText())
        sitemap_block = (
            "Struktur der aktuell geöffneten Datei:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{sitemap}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        ) if sitemap else ""

        # ── Prompt bauen (Code-Quelle explizit benennen) ──────────────
        from ki_modi import MODUS_PROMPTS, MODUS_DEFAULT
        modus_prefix = MODUS_PROMPTS.get(
            getattr(self, "_ki_modus", MODUS_DEFAULT), "")

        herkunft = "Markierter Block" if code_quelle == "suchfeld" else "Editor-Inhalt"
        full_prompt = (
            f"{sitemap_block}"
            f"Aufgabe: {prompt}\n\n"
            f"{herkunft}:\n```python\n{code}\n```\n\n"
            "Antworte ausschließlich mit fertigem Python-Code ohne Markdown.\n"
            f"{modus_prefix}"
        )

        # ── Verlauf erweitern + absolutes Limit prüfen (Fix A) ────────
        if not hasattr(self, "_chat_verlauf"):
            self._ki_verlauf_reset()

        # Absolutes Limit: älteste Nachrichten rauswerfen wenn zu viele
        while len(self._chat_verlauf) >= _VERLAUF_MAX_NACHRICHTEN:
            self._chat_verlauf.pop(0)

        self._chat_verlauf.append({"role": "user", "content": full_prompt})

        # UI-Werte VOR dem Thread-Start im Hauptthread sichern — niemals aus Worker lesen
        source_text   = self._src_box.currentText()
        model_text    = self._model_box.currentText()
        temp_val      = self._temp_box.value()
        verlauf_kopie = list(self._chat_verlauf)
        ki_modus_wert = getattr(self, "_ki_modus", None)  # thread-sicher übergeben

        if ist_nl_modus:
            # ── NL-Modus FC11: Part-Workbench ─────────────────────────────────
            from nl_generator import NL_TEMPERATURE
            self._nl_antwort_aktiv = True
            threading.Thread(
                target=self._worker_mit_system,
                args=(source_text, model_text, NL_SYSTEM_PROMPT, code,
                      NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()
        elif ist_pd_modus:
            # ── NL-Modus FC12: PartDesign ─────────────────────────────────────
            from nl_generator import NL_TEMPERATURE
            self._nl_antwort_aktiv = True
            threading.Thread(
                target=self._worker_mit_system,
                args=(source_text, model_text, NL_SYSTEM_PROMPT_PARTDESIGN,
                      code, NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()
        elif ist_sw_modus:
            # ── NL-Modus FC13: Schrittweise aufbauen ──────────────────────────
            from nl_generator import NL_TEMPERATURE
            vorhandener_code = self._editor.toPlainText().strip()
            if vorhandener_code:
                sw_user_prompt = (
                    f"Vorhandener Code (NICHT wiederholen):\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{vorhandener_code}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Neuer Schritt (NUR diesen Code-Block zurueckgeben):\n{code}"
                )
            else:
                sw_user_prompt = code
            self._nl_antwort_aktiv = True
            self._sw_modus_aktiv = True
            threading.Thread(
                target=self._worker_mit_system,
                args=(source_text, model_text, NL_SYSTEM_PROMPT_SCHRITTWEISE,
                      sw_user_prompt, NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()
        else:
            self._nl_antwort_aktiv = False
            threading.Thread(
                target=self._worker_mit_verlauf,
                args=(source_text, model_text, verlauf_kopie, temp_val),
                daemon=True
            ).start()

    # ── Worker-Thread ─────────────────────────────────────────────────────
    # ── Zentrale Anbieter-Weiche ──────────────────────────────────────────
    _OAI_URLS = {
        "OpenAI":      ("https://api.openai.com/v1",                               "openai"),
        "GitHub":      ("https://models.inference.ai.azure.com",                   "github"),
        "DeepSeek":    ("https://api.deepseek.com/v1",                             "deepseek"),
        "Gemini":      ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini"),
        "Groq":        ("https://api.groq.com/openai/v1",                          "groq"),
        "Mistral":     ("https://api.mistral.ai/v1",                               "mistral"),
        "Together":    ("https://api.together.xyz/v1",                             "together"),
        "HuggingFace": ("https://api-inference.huggingface.co/v1",                 "huggingface"),
        "xAI":         ("https://api.x.ai/v1",                                     "xai"),
        "Fireworks":   ("https://api.fireworks.ai/inference/v1",                   "fireworks"),
        "Moonshot":    ("https://api.moonshot.cn/v1",                              "moonshot"),
        "Qwen":        ("https://dashscope.aliyuncs.com/compatible-mode/v1",       "qwen"),
        "Cohere":      ("https://api.cohere.com/compatibility/v1",                 "cohere"),
        "SambaNova":   ("https://api.sambanova.ai/v1",                             "sambanova"),
        "MiniMax":     ("https://api.minimax.chat/v1",                             "minimax"),
        "Llama":       ("https://api.llama.com/compat/v1",                         "llama"),
    }

    def _stream_fuer_anbieter(self, source, model, prompt, temperature):
        """Zentrale Anbieter-Weiche — nur hier pflegen."""
        if source.startswith("Ollama"):
            self._stream_ollama(model, prompt, temperature)
        elif source.startswith("Anthropic"):
            self._stream_anthropic(lade_api_key("anthropic"), model, prompt, temperature)
        else:
            base, kid = next(
                ((u, k) for pfx, (u, k) in self._OAI_URLS.items()
                 if source.startswith(pfx)),
                ("https://openrouter.ai/api/v1", "openrouter")
            )
            self._stream_openai_compat(base, lade_api_key(kid), model, prompt, temperature)

    def _worker(self, source, model, prompt, temperature=0.2):
        try:
            self._stream_fuer_anbieter(source, model, prompt, temperature)
            if self._alive:
                self._ki_stream_done.emit()
        except Exception as e:
            if self._alive:
                self._ki_error.emit(f"# ❌ Fehler:\n{e}")

    # ── Sitzung speichern / laden ─────────────────────────────────────────
    def _sitzung_speichern(self):
        """Chat-Verlauf, KI-Antwort und Einstellungen in JSON-Datei speichern."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self if hasattr(self, "parentWidget") else None,
            "Sitzung speichern", "",
            "Sitzungsdateien (*.json);;Alle Dateien (*)")
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"

        import json as _json
        daten = {
            "anbieter":   getattr(self, "_src_box",   None) and self._src_box.currentText()   or "",
            "modell":     getattr(self, "_model_box", None) and self._model_box.currentText() or "",
            "verlauf":    getattr(self, "_chat_verlauf", []),
            "ki_antwort": getattr(self, "_ki_area",   None) and self._ki_area.toPlainText()   or "",
            "ki_eingabe": getattr(self, "find_area",  None) and self.find_area.toPlainText()  or "",
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                _json.dump(daten, f, ensure_ascii=False, indent=2)
            import os as _os
            self._set_status(f"💾 Sitzung gespeichert: {_os.path.basename(path)}")
        except Exception as e:
            self._set_status(f"❌ Speichern fehlgeschlagen: {e}")

    def _sitzung_laden(self):
        """Gespeicherte Sitzung aus JSON-Datei wiederherstellen."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self if hasattr(self, "parentWidget") else None,
            "Sitzung laden", "",
            "Sitzungsdateien (*.json);;Alle Dateien (*)")
        if not path:
            return

        import json as _json
        try:
            with open(path, "r", encoding="utf-8") as f:
                daten = _json.load(f)
        except Exception as e:
            self._set_status(f"❌ Laden fehlgeschlagen: {e}")
            return

        # Verlauf wiederherstellen
        self._chat_verlauf = daten.get("verlauf", [])

        # KI-Antwort wiederherstellen
        ki_text = daten.get("ki_antwort", "")
        if ki_text and hasattr(self, "_ki_area"):
            self._ki_area.setPlainText(ki_text)

        # Eingabe wiederherstellen
        ki_eingabe = daten.get("ki_eingabe", "")
        if ki_eingabe and hasattr(self, "find_area"):
            self.find_area.setPlainText(ki_eingabe)

        # Anbieter wiederherstellen
        anbieter = daten.get("anbieter", "")
        if anbieter and hasattr(self, "_src_box"):
            idx = self._src_box.findText(anbieter)
            if idx >= 0:
                self._src_box.setCurrentIndex(idx)

        import os as _os
        n = len(self._chat_verlauf)
        self._set_status(
            f"📂 Sitzung geladen: {_os.path.basename(path)} · {n} Nachrichten")

    # ── Chat-Verlauf-Verwaltung ────────────────────────────────────────────
    def _ki_verlauf_reset(self):
        """Gesprächsverlauf leeren (z.B. bei neuer Datei oder manuell)."""
        self._chat_verlauf: list = []
        self._compact_zusammenfassung: str = ""
        self._korrektur_verlauf: list = []
        if hasattr(self, "_ki_area"):
            self._ki_area.clear()
        if hasattr(self, "_chunk_buffer"):
            self._chunk_buffer.clear()
        self._set_status("🧹 Gesprächsverlauf geleert")

    def _ki_verlauf_groesse(self) -> int:
        """Gibt die geschätzte Zeichenzahl des gesamten Verlaufs zurück."""
        return sum(len(m["content"]) for m in self._chat_verlauf)

    def _ki_verlauf_komprimieren(self, source, model, temperature):
        """
        Komprimiert ältere Nachrichten im Verlauf zu einer Zusammenfassung.
        Die neuesten _COMPACT_BEHALTEN Nachrichten bleiben erhalten.
        Läuft SYNCHRON (blocking) im Worker-Thread – kein eigener Thread nötig.
        """
        if len(self._chat_verlauf) <= _COMPACT_BEHALTEN:
            return
        alte   = self._chat_verlauf[:-_COMPACT_BEHALTEN]
        neue   = self._chat_verlauf[-_COMPACT_BEHALTEN:]
        inhalt = "\n\n".join(
            f"[{m['role'].upper()}]: {m['content'][:600]}" for m in alte)
        zusammen_prompt = (
            "Fasse das folgende Gespräch auf Deutsch in maximal 5 Sätzen zusammen. "
            "Behalte alle wichtigen Code-Änderungen, Entscheidungen und Aufgaben. "
            "Antworte NUR mit der Zusammenfassung, kein Intro, keine Überschriften.\n\n"
            f"{inhalt}"
        )
        try:
            zusammenfassung = self._einmaliger_aufruf(
                source, model, zusammen_prompt, temperature)
        except Exception:
            zusammenfassung = (
                f"[Zusammenfassung von {len(alte)} Nachrichten – Details nicht verfügbar]")

        self._compact_zusammenfassung = zusammenfassung
        self._chat_verlauf = neue
        self._chat_verlauf.insert(0, {
            "role": "user",
            "content": f"[KONTEXT-ZUSAMMENFASSUNG früherer Nachrichten]:\n{zusammenfassung}"
        })
        self._chat_verlauf.insert(1, {
            "role": "assistant",
            "content": "Verstanden, ich berücksichtige diesen Kontext."
        })
        self._ki_compact_signal.emit(len(alte))

    def _einmaliger_aufruf(self, source, model, prompt, temperature) -> str:
        """
        Blockierender (nicht-streamender) API-Aufruf für interne Zwecke.
        Gibt den Antworttext zurück.
        """
        import urllib.request as _urllib
        headers = {"Content-Type": "application/json"}
        if source.startswith("Anthropic"):
            key = lade_api_key("anthropic")
            url = "https://api.anthropic.com/v1/messages"
            headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
            body = json.dumps({
                "model": model, "max_tokens": 512, "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()
            req = _urllib.Request(url, data=body, headers=headers)
            with _urllib.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["content"][0]["text"].strip()
        elif source.startswith("Ollama"):
            url = "http://localhost:11434/api/generate"
            body = json.dumps({
                "model": model, "prompt": prompt,
                "stream": False, "options": {
                    "temperature": temperature,
                    "num_ctx": 2048, "num_predict": 512,
                    "num_thread": __import__("os").cpu_count() or 4,
                }
            }).encode()
            req = _urllib.Request(url, data=body, headers=headers)
            with _urllib.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read()).get("response", "").strip()
        else:
            if source.startswith("OpenAI"):
                base, key = "https://api.openai.com/v1", lade_api_key("openai")
            elif source.startswith("GitHub"):
                base, key = "https://models.inference.ai.azure.com", lade_api_key("github")
            else:
                base, key = "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY", "")
            headers["Authorization"] = f"Bearer {key}"
            body = json.dumps({
                "model": model, "temperature": temperature, "stream": False,
                "messages": [
                    {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                    {"role": "user", "content": prompt}
                ]
            }).encode()
            req = _urllib.Request(f"{base}/chat/completions", data=body, headers=headers)
            with _urllib.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"].strip()

    # ── Worker-Thread mit Verlauf + Context Compacting ────────────────────
    def _worker_mit_verlauf(self, source, model, verlauf, temperature=0.2):
        """
        Worker-Thread mit Gesprächsverlauf + automatischem Context Compacting.
        Prüft vor dem API-Aufruf ob der Verlauf zu groß ist und komprimiert ihn ggf.
        """
        gesamt_zeichen = sum(len(m["content"]) for m in verlauf)
        if gesamt_zeichen > _COMPACT_SCHWELLE:
            self._ki_verlauf_komprimieren(source, model, temperature)
            verlauf = list(self._chat_verlauf)

        try:
            if source.startswith("Ollama"):
                kompakt = "\n\n".join(
                    f"[{m['role'].upper()}]:\n{m['content']}" for m in verlauf)
                self._stream_ollama(model, kompakt, temperature)
            elif source.startswith("Anthropic"):
                self._stream_anthropic_verlauf(
                    lade_api_key("anthropic"), model, verlauf, temperature)
            elif source.startswith("OpenAI"):
                self._stream_openai_verlauf(
                    "https://api.openai.com/v1",
                    lade_api_key("openai"), model, verlauf, temperature)
            elif source.startswith("GitHub"):
                self._stream_openai_verlauf(
                    "https://models.inference.ai.azure.com",
                    lade_api_key("github"), model, verlauf, temperature)
            else:
                self._stream_openai_verlauf(
                    "https://openrouter.ai/api/v1",
                    os.getenv("OPENROUTER_API_KEY", ""), model, verlauf, temperature)
            if self._alive:
                self._ki_stream_done.emit()
        except Exception as e:
            if self._alive:
                self._ki_error.emit(f"# ❌ Fehler:\n{e}")

    # ── Verlauf-Streaming: Anthropic ──────────────────────────────────────
    def _stream_anthropic_verlauf(self, key, model, verlauf, temperature):
        """Anthropic-Streaming mit vollständigem Nachrichtenverlauf."""
        if not key:
            raise RuntimeError(
                "Kein Anthropic API-Schlüssel hinterlegt.\n"
                "Bitte unten rechts 'Anthropic (Claude)' wählen und sk-ant-… eintragen.")
        r = self._session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": model, "max_tokens": 4096, "temperature": temperature,
                  "stream": True,
                  "system": "Du bist ein Python-Experte für FreeCAD-Makros. "
                             "Antworte nur mit Python-Code ohne Markdown-Fences.",
                  "messages": verlauf},
            stream=True, timeout=120)
        r.raise_for_status()
        antwort_teile = []
        for line in r.iter_lines():
            if not self._alive:
                break
            if line and line.startswith(b"data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta":
                        chunk = data.get("delta", {}).get("text", "")
                        if chunk:
                            antwort_teile.append(chunk)
                            self._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError):
                    pass
        if antwort_teile:
            self._chat_verlauf.append(
                {"role": "assistant", "content": "".join(antwort_teile)})

    # ── Verlauf-Streaming: OpenAI-kompatibel ──────────────────────────────
    def _stream_openai_verlauf(self, base_url, key, model, verlauf, temperature):
        """OpenAI-kompatibles Streaming mit vollständigem Nachrichtenverlauf."""
        if not key:
            raise RuntimeError(f"Kein API-Schlüssel für {base_url} hinterlegt.")
        nachrichten = [
            {"role": "system",
             "content": "Du bist ein Python-Experte für FreeCAD-Makros. "
                        "Antworte nur mit Python-Code ohne Markdown-Fences."},
            *verlauf
        ]
        r = self._session.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": model, "temperature": temperature, "stream": True,
                  "messages": nachrichten},
            stream=True, timeout=120)
        r.raise_for_status()
        antwort_teile = []
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
                        antwort_teile.append(chunk)
                        self._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        if antwort_teile:
            self._chat_verlauf.append(
                {"role": "assistant", "content": "".join(antwort_teile)})

    # ── Streaming-Implementierungen ───────────────────────────────────────
    def _stream_ollama(self, model, prompt, temperature):
        import os as _os
        _cpu_kerne = _os.cpu_count() or 4
        r = self._session.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": True,
                  "options": {
                      "temperature": temperature,
                      "num_ctx":     2048,   # Kontextfenster: kleiner = schneller
                      "num_predict": 1024,   # Max. Ausgabe-Token
                      "num_thread":  _cpu_kerne,  # alle CPU-Kerne nutzen
                  }},
            stream=True, timeout=None)
        r.raise_for_status()
        for line in r.iter_lines():
            if not self._alive:
                break
            if line:
                data  = json.loads(line)
                chunk = data.get("response", "")
                if chunk:
                    self._ki_chunk.emit(chunk)

    def _stream_anthropic(self, key, model, prompt, temperature):
        if not key:
            raise RuntimeError(
                "Kein Anthropic API-Schlüssel hinterlegt.\n"
                "Bitte unten rechts 'Anthropic (Claude)' wählen und sk-ant-… eintragen.")
        r = self._session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": model, "max_tokens": 4096, "temperature": temperature,
                  "stream": True,
                  "system": "Du bist ein Python-Experte. Antworte nur mit Python-Code.",
                  "messages": [{"role": "user", "content": prompt}]},
            stream=True, timeout=120)
        r.raise_for_status()
        for line in r.iter_lines():
            if not self._alive:
                break
            if line and line.startswith(b"data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta":
                        chunk = data.get("delta", {}).get("text", "")
                        if chunk:
                            self._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError):
                    pass

    def _stream_openai_compat(self, base_url, key, model, prompt, temperature):
        if not key:
            raise RuntimeError(
                f"Kein API-Schlüssel für {base_url} hinterlegt.\n"
                "Bitte unten rechts den passenden Anbieter wählen und den Key eintragen.")
        r = self._session.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": model, "temperature": temperature, "stream": True,
                  "messages": [
                      {"role": "system",
                       "content": "Du bist ein Python-Experte. Antworte nur mit Python-Code."},
                      {"role": "user", "content": prompt}]},
            stream=True, timeout=120)
        r.raise_for_status()
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
                        self._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

    # ── Chunk-Batching ────────────────────────────────────────────────────
    @QtCore.Slot(str)
    def _on_ki_chunk(self, chunk: str):
        """Chunk puffern – das Schreiben übernimmt _flush_chunks alle 50 ms."""
        self._chunk_buffer.append(chunk)
        self._stream_token_count += 1

    def _flush_chunks(self):
        """Alle gepufferten Chunks in einem Rutsch in ki_area schreiben."""
        if not self._chunk_buffer:
            return
        text = "".join(self._chunk_buffer)
        self._chunk_buffer.clear()
        # Erster echter Chunk: Warteanimation stoppen und Feld leeren
        if getattr(self, "_warte_aktiv", False):
            self._warte_aktiv = False
            if hasattr(self, "_warte_timer"):
                self._warte_timer.stop()
            self._ki_area.clear()
        cursor = self._ki_area.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self._ki_area.setTextCursor(cursor)
        self._ki_area.ensureCursorVisible()

    def _update_stream_status(self):
        """Live-Anzeige auch wenn noch kein erster Token angekommen ist."""
        elapsed = time.monotonic() - self._stream_start_time
        if self._stream_token_count <= 0:
            self._status.setText(
                f"🧠 Modell denkt nach ... ({elapsed:.1f} s)")
        else:
            self._status.setText(
                f"✍️ Generiere Code ... "
                f"{self._stream_token_count} Token "
                f"({elapsed:.1f} s)")

    def _stop_stream_timers(self):
        self._flush_timer.stop()
        self._status_timer.stop()
        self._warte_aktiv = False
        if hasattr(self, "_warte_timer"):
            self._warte_timer.stop()
        self._flush_chunks()

    @QtCore.Slot()
    def _on_ki_stream_done(self):
        """Nach dem letzten Chunk: Code-Fences entfernen, Buttons aktivieren."""
        self._stop_stream_timers()
        elapsed = time.monotonic() - self._stream_start_time
        full  = self._ki_area.toPlainText()

        # Raw-Log: ungefilterte Ollama-Antwort für Diagnose
        import os as _os
        _log_pfad = _os.path.join(_os.path.expanduser("~"), "ollama_raw.txt")
        try:
            with open(_log_pfad, "w", encoding="utf-8") as _f:
                _f.write(full)
        except Exception:
            pass

        clean = _RE_CODE_FENCE.sub("", full).strip().replace("\t", "    ")
        if not clean:
            self._ki_area.setPlainText("# ❌ Leere Antwort")
            self._btn_ki.setEnabled(True)
            return

        # Text-Filterung nur bei NL-Modi (FC11/FC12/FC13) — reguläre Preset-Antworten
        # enthalten bereits reinen Code und dürfen nicht umgeschrieben werden.
        if getattr(self, "_nl_antwort_aktiv", False):
            self._nl_antwort_aktiv = False
            clean = self._extrahiere_code_aus_nl_antwort(clean)
            clean = self._schneide_erklaerung_ab(clean)

        clean, korrigiert = self._freecad_code_korrigieren(clean)
        self._ki_area.setPlainText(clean)
        self._btn_ki.setEnabled(True)
        self._btn_einfuegen.setEnabled(True)
        self._btn_ersetzen.setEnabled(True)
        hinweis = "  ⚠ KI-Code automatisch korrigiert" if korrigiert else ""

        # FC13 Schrittweise: neuen Block automatisch ans Ende anhängen
        if getattr(self, "_sw_modus_aktiv", False):
            self._sw_modus_aktiv = False
            vorhandener = self._editor.toPlainText().rstrip()
            # Deutschen Text / Einleitungssätze herausfiltern die Ollama trotzdem schreibt
            clean = self._extrahiere_code_aus_nl_antwort(clean)
            clean = self._schneide_erklaerung_ab(clean)
            # Prüfen ob KI versehentlich import/doc wiederholt hat → diese Zeilen filtern
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
                # Syntax-Check bevor der Block in den Editor kommt
                import ast as _ast
                try:
                    _ast.parse(neuer_block)
                except SyntaxError as _se:
                    self._ki_area.setPlainText(
                        f"# ❌ Syntax-Fehler in KI-Antwort — NICHT angehängt\n"
                        f"# Zeile {_se.lineno}: {_se.msg}\n"
                        f"# Bitte Beschreibung umformulieren oder stärkeres Modell wählen.\n\n"
                        f"{neuer_block}")
                    self._set_status(
                        f"❌ Syntax-Fehler im neuen Block – Editor unverändert")
                    return
                if vorhandener:
                    self._editor.setPlainText(vorhandener + "\n\n" + neuer_block)
                else:
                    self._editor.setPlainText(neuer_block)
                self._set_status(
                    f"✅ Schritt angehängt – {self._stream_token_count} Token "
                    f"in {elapsed:.1f} s{hinweis}")
            else:
                self._set_status("⚠ Neuer Block war leer – nichts angehängt")
            return

        self._set_status(
            f"✅ Fertig – {self._stream_token_count} Token in {elapsed:.1f} s  "
            f"→ ✅ Ersetzen{hinweis}")

    def _freecad_code_korrigieren(self, code: str):
        """
        Erkennt und ersetzt fehlerhafte Part.make*()-Aufrufe durch doc.addObject().
        Gibt (korrigierter_code, wurde_geaendert) zurück.
        """
        import re as _r

        # ── Kein doc.addObject() obwohl FreeCAD importiert ───────────────────
        # Ollama generiert manchmal Python-Dicts statt FreeCAD-Objekte
        hat_freecad_import = any(
            "import FreeCAD" in z or "import App" in z for z in code.splitlines())
        hat_add_object = "doc.addObject(" in code or "addObject(" in code
        if hat_freecad_import and not hat_add_object:
            return (
                "# ❌ UNGÜLTIGER FREECAD-CODE — KI hat Python-Datenstrukturen generiert\n"
                "#    statt echter FreeCAD-Geometrie-Aufrufe.\n"
                "#\n"
                "# Kein einziges doc.addObject() gefunden!\n"
                "# Beispiel für korrekte Kugel:\n"
                "#   kugel = doc.addObject('Part::Sphere', 'Kugel')\n"
                "#   kugel.Radius = 30\n"
                "#   doc.recompute()\n"
                "#\n"
                "# Bitte KI-Beschreibung erneut senden.", True)

        # ── Blender-API-Erkennung (sofortiger Abbruch) ────────────────────
        _FALSCHE_APIS = {
            "bpy":     "Blender",
            "bmesh":   "Blender",
            "maya":    "Maya",
            "rhino":   "Rhino",
            "cadquery":"CadQuery",
            "numpy":   "NumPy (kein FreeCAD)",
            "stl":     "STL-Bibliothek (kein FreeCAD)",
            "trimesh": "Trimesh (kein FreeCAD)",
            "open3d":  "Open3D (kein FreeCAD)",
        }
        for zeile in code.splitlines():
            s = zeile.strip()
            for api, name in _FALSCHE_APIS.items():
                if _r.match(rf'^import\s+{api}\b', s) or _r.match(rf'^from\s+{api}\b', s):
                    fehler_code = (
                        f"# ❌ FALSCHE API — KI hat {name}-Code generiert statt FreeCAD-Code!\n"
                        f"#\n"
                        f"# Die KI hat 'import {api}' verwendet. Das ist die {name}-API\n"
                        f"# und funktioniert NICHT in FreeCAD.\n"
                        f"#\n"
                        f"# Lösung: Beschreibung erneut an die KI schicken und dabei\n"
                        f"# explizit auf FreeCAD hinweisen, z.B.:\n"
                        f"#   \"Erstelle FreeCAD-Python-Makro für: ...\"\n"
                        f"#\n"
                        f"# Originaler (fehlerhafter) Code wurde nicht ausgeführt."
                    )
                    return fehler_code, True

        geaendert = False
        zeilen = code.splitlines()
        neue_zeilen = []
        # Variablen-Tracking: name → Part-Typ
        var_typ: dict = {}

        # Verschachtelte Part.make*() inline ersetzen (z.B. in .cut() / .fuse())
        def _ersetze_inline(z):
            """Ersetzt Part.makeXxx(...) inline durch einen Temp-Aufruf — markiert für spätere Expansion."""
            return z  # Inline-Ersetzung zu komplex für Regex; wird als Ganzes gefangen
        # Muster für Part.makeXxx(...)
        _MAKE = _r.compile(
            r'^(\s*)(\w+)\s*=\s*Part\.(makeBox|makeCylinder|makeSphere|makeCone|makeTorus)'
            r'\(([^)]*)\)'
        )
        # Muster für obj.cut(other) und obj.fuse(other)
        _CUT      = _r.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.cut\((\w+)\)')
        _FUSE     = _r.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.fuse\((\w+)\)')
        # Python-Operatoren: a = b - c  /  a -= b  →  Part::Cut
        _CUT_OP   = _r.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\s*-\s*(\w+)\s*$')
        _CUT_AUG  = _r.compile(r'^(\s*)(\w+)\s*-=\s*(\w+)\s*$')
        # Python-Operatoren: a = b + c  /  a += b  →  Part::Fuse
        _FUSE_OP  = _r.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)\s*$')
        _FUSE_AUG = _r.compile(r'^(\s*)(\w+)\s*\+=\s*(\w+)\s*$')
        # obj.append(other)  →  Part::Fuse (KI verwechselt Part.Feature mit Liste)
        _APPEND = _r.compile(r'^(\s*)(\w+)\.append\((\w+)\)\s*$')
        # shapes = []; shapes.append(x)  →  Liste bleibt Liste (kein Eingriff nötig)
        # Erfundene FreeCAD-Objekte die Ollama gerne halluziniert → ersetzen
        _FAKE_OBJECTS = {
            # Falsche Union-Varianten → Part::Fuse
            "Part::UnionForTwoVolumes": "Part::Fuse",
            "Part::Union":              "Part::Fuse",
            "Part::BooleanUnion":       "Part::Fuse",
            "Part::Merge":              "Part::Fuse",
            # Falsche Cut-Varianten → Part::Cut
            "Part::BooleanCut":         "Part::Cut",
            "Part::Subtract":           "Part::Cut",
            "Part::Difference":         "Part::Cut",
            # Falsche Common-Varianten → Part::Common
            "Part::Intersection":       "Part::Common",
            "Part::BooleanIntersection":"Part::Common",
        }
        for falsch, richtig in _FAKE_OBJECTS.items():
            if falsch in code:
                code = code.replace(falsch, richtig)
                geaendert = True

        # Falsche Eigenschaftsnamen bei bekannten FreeCAD-Objekten korrigieren
        # Erkennung: .Length bei Cylinder-Variablen → .Height
        _PROP_FIXES = [
            # Part::Cylinder: .Length ist falsch, korrekt ist .Height
            (_r.compile(r'^(\s*\w+)\.Length(\s*=\s*\d)'), r'\1.Height\2',
             lambda z: any(k in z for k in ("Cylinder", "Zylinder", "zyl", "cylinder", "bohrung", "Bohrung"))),
        ]
        prop_zeilen = []
        for z in code.splitlines():
            geaendert_zeile = False
            for muster, ersatz, bedingung in _PROP_FIXES:
                if bedingung(z) and muster.search(z):
                    z = muster.sub(ersatz, z)
                    geaendert = geaendert_zeile = True
            prop_zeilen.append(z)
        code = "\n".join(prop_zeilen)

        # obj.Add(x) → obj.Base/obj.Tool (Ollama verwechselt Fuse/Cut mit Liste)
        # Erster .Add()-Aufruf pro Objekt → .Base, zweiter → .Tool
        _ADD = _r.compile(r'^(\s*)(\w+)\.Add\((\w+)\)\s*$')
        _add_zaehler: dict = {}
        _add_zeilen = []
        for z in code.splitlines():
            m = _ADD.match(z)
            if m:
                indent, obj, arg = m.group(1), m.group(2), m.group(3)
                n = _add_zaehler.get(obj, 0)
                _add_zaehler[obj] = n + 1
                attr = "Base" if n == 0 else "Tool"
                _add_zeilen.append(f"{indent}{obj}.{attr} = {arg}")
                geaendert = True
            else:
                _add_zeilen.append(z)
        code = "\n".join(_add_zeilen)

        zeilen = code.splitlines()  # neu einlesen nach Ersetzungen

        # Muster für ungültige FreeCAD-API
        _IMP      = _r.compile(r'^\s*import\s+Part\s*$')
        _APP_SHOW = _r.compile(r'^\s*App\.show\s*\(')

        _TYP_MAP = {
            "makeBox":      ("Part::Box",      ["Length", "Width", "Height"]),
            "makeCylinder": ("Part::Cylinder", ["Radius", "Height"]),
            "makeSphere":   ("Part::Sphere",   ["Radius"]),
            "makeCone":     ("Part::Cone",     ["Radius1", "Radius2", "Height"]),
            "makeTorus":    ("Part::Torus",    ["Radius1", "Radius2"]),
        }

        # Sicherstellen dass import FreeCAD as App oben steht
        hat_app_import = any("import FreeCAD as App" in z for z in zeilen)
        hat_doc        = any("doc = App." in z or "doc=App." in z for z in zeilen)

        prefix_zeilen = []
        if not hat_app_import:
            prefix_zeilen.append("import FreeCAD as App")
            geaendert = True
        if not hat_doc:
            prefix_zeilen.append(
                "doc = App.ActiveDocument or App.newDocument('Neu')")
            geaendert = True

        # Vorpass: verschachtelte Part.make*(…) in eigene Zeilen aufsplitten
        # z.B.: x = a.cut(Part.makeCylinder(5, 40))
        # →     _tmp0 = Part.makeCylinder(5, 40)
        #        x = a.cut(_tmp0)
        _INLINE_MAKE = _r.compile(
            r'Part\.(makeBox|makeCylinder|makeSphere|makeCone|makeTorus)\(([^)]*)\)')
        tmp_zaehler = [0]
        neue_zeilen_pre = []
        for z in zeilen:
            treffer = list(_INLINE_MAKE.finditer(z))
            if treffer and not _MAKE.match(z):
                indent = len(z) - len(z.lstrip())
                ind = " " * indent
                for t in treffer:
                    tmp_name = f"_tmp{tmp_zaehler[0]}"
                    tmp_zaehler[0] += 1
                    neue_zeilen_pre.append(f"{ind}{tmp_name} = {t.group(0)}")
                    z = z.replace(t.group(0), tmp_name)
                    geaendert = True
            neue_zeilen_pre.append(z)
        zeilen = neue_zeilen_pre

        zaehler = {}  # zählt pro Typ wie viele schon angelegt wurden

        for z in zeilen:
            # App.show() ist keine gültige FreeCAD-API — entfernen
            if _APP_SHOW.match(z):
                geaendert = True
                continue

            # "import Part" bleibt — wird für Part::Cut/.Base/.Tool benötigt

            m = _MAKE.match(z)
            if m:
                indent, varname, fn, args = m.groups()
                typ, felder = _TYP_MAP[fn]
                short = typ.split("::")[-1]
                zaehler[short] = zaehler.get(short, 0) + 1
                obj_name = f"{varname}"
                arg_liste = [a.strip() for a in args.split(",") if a.strip()]

                neue_zeilen.append(f"{indent}{varname} = doc.addObject('{typ}', '{obj_name}')")
                for i, feld in enumerate(felder):
                    if i < len(arg_liste):
                        neue_zeilen.append(f"{indent}{varname}.{feld} = {arg_liste[i]}")
                var_typ[varname] = typ
                geaendert = True
                continue

            m = _CUT.match(z)
            if m:
                indent, result, basis, tool = m.groups()
                neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Cut', '{result}')")
                neue_zeilen.append(f"{indent}{result}.Base = {basis}")
                neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
                geaendert = True
                continue

            m = _FUSE.match(z)
            if m:
                indent, result, basis, tool = m.groups()
                neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Fuse', '{result}')")
                neue_zeilen.append(f"{indent}{result}.Base = {basis}")
                neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
                geaendert = True
                continue

            # obj.append(other) → Part::Fuse — aber NUR wenn obj bekanntes Part-Objekt
            m = _APPEND.match(z)
            if m:
                indent, varname, tool = m.groups()
                if varname in var_typ:
                    tmp = f"{varname}_fuse"
                    neue_zeilen.append(f"{indent}{tmp} = doc.addObject('Part::Fuse', '{tmp}')")
                    neue_zeilen.append(f"{indent}{tmp}.Base = {varname}")
                    neue_zeilen.append(f"{indent}{tmp}.Tool = {tool}")
                    neue_zeilen.append(f"{indent}{varname} = {tmp}")
                    geaendert = True
                    continue

            # Python-Operator: a = b - c  →  Part::Cut
            m = _CUT_OP.match(z)
            if m:
                indent, result, basis, tool = m.groups()
                neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Cut', '{result}')")
                neue_zeilen.append(f"{indent}{result}.Base = {basis}")
                neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
                geaendert = True
                continue

            # Python-Augmented-Assignment: a -= b  →  Part::Cut
            m = _CUT_AUG.match(z)
            if m:
                indent, varname, tool = m.groups()
                tmp = f"{varname}_cut"
                neue_zeilen.append(f"{indent}{tmp} = doc.addObject('Part::Cut', '{tmp}')")
                neue_zeilen.append(f"{indent}{tmp}.Base = {varname}")
                neue_zeilen.append(f"{indent}{tmp}.Tool = {tool}")
                neue_zeilen.append(f"{indent}{varname} = {tmp}")
                geaendert = True
                continue

            # Python-Operator: a = b + c  →  Part::Fuse
            m = _FUSE_OP.match(z)
            if m:
                indent, result, basis, tool = m.groups()
                neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Fuse', '{result}')")
                neue_zeilen.append(f"{indent}{result}.Base = {basis}")
                neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
                geaendert = True
                continue

            # Python-Augmented-Assignment: a += b  →  Part::Fuse
            m = _FUSE_AUG.match(z)
            if m:
                indent, varname, tool = m.groups()
                tmp = f"{varname}_fuse"
                neue_zeilen.append(f"{indent}{tmp} = doc.addObject('Part::Fuse', '{tmp}')")
                neue_zeilen.append(f"{indent}{tmp}.Base = {varname}")
                neue_zeilen.append(f"{indent}{tmp}.Tool = {tool}")
                neue_zeilen.append(f"{indent}{varname} = {tmp}")
                geaendert = True
                continue

            neue_zeilen.append(z)

        # Prefix-Zeilen NACH dem letzten Import einfügen, nicht ganz oben
        # (verhindert NameError wenn import FreeCAD as App schon vorhanden ist
        #  und nur doc = App.ActiveDocument... fehlt)
        if prefix_zeilen:
            letzter_import = -1
            for i, z in enumerate(neue_zeilen):
                s = z.strip()
                if s.startswith("import ") or s.startswith("from "):
                    letzter_import = i
            einfuge = letzter_import + 1
            for j, pz in enumerate(prefix_zeilen):
                neue_zeilen.insert(einfuge + j, pz)

        ergebnis = "\n".join(neue_zeilen)
        return ergebnis, geaendert

    def _kommentiere_text_zeilen(self, text: str) -> str:
        """
        Zeilen die kein Python sind und nicht mit # beginnen → # voranstellen.
        Verhindert SyntaxError durch deutschen Erklärungstext von Ollama.
        """
        _CODE_STARTS = (
            "#", "import ", "from ", "def ", "class ", "try:", "except",
            "finally:", "if ", "elif ", "else:", "for ", "while ", "with ",
            "return ", "yield ", "raise ", "pass", "break", "continue",
            "doc", "App.", "FreeCAD", "Gui.", "Part.", "Sketcher.",
            "print(", "```",
        )
        ergebnis = []
        for zeile in text.splitlines():
            s = zeile.strip()
            if not s:
                ergebnis.append(zeile)
                continue
            # Eingerückte Zeilen und bekannte Python-Tokens → unverändert
            ist_eingerueckt = zeile.startswith("    ") or zeile.startswith("\t")
            ist_code = (
                ist_eingerueckt
                or any(s.startswith(t) for t in _CODE_STARTS)
                or _re.match(r"^[A-Za-z_]\w*\s*[=\(\[]", s)  # Zuweisung oder Aufruf
            )
            if ist_code:
                ergebnis.append(zeile)
            else:
                ergebnis.append(f"# {s}")
        return "\n".join(ergebnis)

    def _extrahiere_code_aus_nl_antwort(self, text: str) -> str:
        """
        Filtert aus einer gemischten NL-Antwort (Text + Code) den Python-Code.
        Strategie:
          1. Wenn ein ```python```-Block vorhanden → nur den nehmen
          2. Sonst: zeilenweise klassifizieren, Text als #-Kommentare anhängen
          3. Fallback: Originaltext unverändert zurückgeben
        """
        # ── Strategie 1: expliziter ```python```-Block ────────────────────
        fence_match = _re.search(
            r"```(?:python)?\s*\n(.*?)```", text, _re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip().replace("\t", "    ")

        # ── Strategie 2: zeilenweise klassifizieren ───────────────────────
        # Python-Zeilen erkennen — erweiterte Musterliste
        _CODE_STARTS = (
            "#", "import ", "from ", "def ", "class ", "try:", "except",
            "finally:", "if ", "elif ", "else:", "for ", "while ", "with ",
            "return ", "yield ", "raise ", "pass", "break", "continue",
            "doc", "box", "zyl", "cut", "fuse", "obj", "pad", "body",
            "sketch", "pocket", "result", "shape", "mesh", "part",
            "print(", "App.", "FreeCAD", "Gui.", "Part.", "Sketcher.",
        )
        _AUFZAEHLUNG = _re.compile(r"^\s*[\*\-\d]+[\.\)]\s")  # "* text" oder "1. text"

        zeilen      = text.splitlines()
        code_zeilen = []
        text_zeilen = []
        in_code     = False

        for zeile in zeilen:
            stripped = zeile.strip()

            # Leerzeile: im Code behalten, außerhalb überspringen
            if not stripped:
                if in_code:
                    code_zeilen.append("")
                continue

            # Aufzählungszeichen sind definitiv kein Code
            ist_aufzaehlung = bool(_AUFZAEHLUNG.match(zeile))

            # Eingerückter Code (4+ Leerzeichen) → immer Code
            ist_eingerueckt = zeile.startswith("    ") or zeile.startswith("\t")

            # Startet mit bekanntem Python-Token?
            ist_code_token = any(stripped.startswith(s) for s in _CODE_STARTS)

            # Konstante: GROSSBUCHSTABEN = Zahl/String
            ist_konstante = bool(
                _re.match(r"^[A-Z_]{2,}\s*=\s*[\d\"\'\-]", stripped))

            # Python-Ausdruck: identifier[.attr]* gefolgt von = ( [ oder Kettenzugriff
            # Erkennt: "cylinder = ...", "obj.Placement.Base = ...", "my_list.append(x)"
            # Schließt Satzanfänge aus: "Erstelle einen ...", "Die Box ..."
            ist_zuweisung = bool(
                _re.match(
                    r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*[\(\[=]",
                    stripped)
            ) and not _re.match(r"^[A-Z][a-z]", stripped)

            ist_code = (
                (ist_code_token or ist_eingerueckt or ist_konstante or ist_zuweisung)
                and not ist_aufzaehlung
            )

            if ist_code:
                in_code = True
                code_zeilen.append(zeile)
            elif in_code:
                # Nach dem Code: Erklärungstext als Kommentar anhängen
                if stripped and not ist_aufzaehlung:
                    text_zeilen.append(f"# {stripped}")
                elif ist_aufzaehlung:
                    # Aufzählungspunkte sauber als Kommentar
                    sauber = _AUFZAEHLUNG.sub("", stripped)
                    text_zeilen.append(f"# {sauber}")
            # Vor dem Code: Intro-Sätze überspringen

        ergebnis = "\n".join(code_zeilen).strip().replace("\t", "    ")

        if text_zeilen:
            ergebnis += "\n\n" + "\n".join(text_zeilen)

        # ── Strategie 3: Fallback ─────────────────────────────────────────
        return ergebnis if ergebnis.strip() else text

    def _schneide_erklaerung_ab(self, text: str) -> str:
        """Experten-Modus: Erklärungstext und Zusammenfassungs-Kommentare abschneiden."""
        _ZUSAMMENFASSUNG = (
            "# zusammenfassung", "# das skript", "# hinweis",
            "# erklärung", "# ergebnis", "# dieser code",
            "# note:", "# summary:", "# this script",
        )
        _CODE_STARTS = (
            "import ", "from ", "def ", "class ", "try:", "except",
            "finally:", "if ", "elif ", "else:", "for ", "while ", "with ",
            "return ", "yield ", "raise ", "pass", "break", "continue",
            "print(", "App.", "doc", "box", "zyl", "cut", "fuse",
            "obj", "pad", "body", "sketch", "result",
        )
        zeilen = text.splitlines()
        letzte_code_zeile = 0
        for i, zeile in enumerate(zeilen):
            s = zeile.strip()
            if not s:
                continue
            if s.startswith("#") and any(
                    s.lower().startswith(k) for k in _ZUSAMMENFASSUNG):
                continue
            ist_code = (
                any(s.startswith(k) for k in _CODE_STARTS)
                or zeile.startswith("    ")
                or zeile.startswith("\t")
                or bool(_re.match(r"^[A-Z_]{2,}\s*=", s))
                or bool(
                    _re.match(
                        r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*[\(\[=]",
                        s)
                    and not _re.match(r"^[A-Z][a-z]", s))
                or (s.startswith("#") and not any(
                    s.lower().startswith(k) for k in _ZUSAMMENFASSUNG))
            )
            if ist_code:
                letzte_code_zeile = i
        return "\n".join(zeilen[:letzte_code_zeile + 1]).strip()
    @QtCore.Slot(str)
    def fehler_anzeigen(self, fehlertext: str):
        """
        Öffnet das Fehler-Panel und füllt Fehlermeldung ein.
        Wird von manager.py und intern bei KI-Fehlern aufgerufen.
        """
        if not self._fehler_inhalt.isVisible():
            self._fehler_inhalt.setVisible(True)
            self._btn_fehler_toggle.setText("▼")
            splitter = self._fehler_inhalt.parent().parent()
            if isinstance(splitter, QtWidgets.QSplitter):
                h = splitter.height()
                splitter.setSizes([int(h * 0.65), int(h * 0.35)])

        self._fehler_eingabe.setPlainText(fehlertext)

        from fehler import uebersetze_text
        self._fehler_ausgabe.setPlainText(uebersetze_text(fehlertext))

        self._set_status("⚠ Fehler erkannt → Fehler-Panel geöffnet")

    @QtCore.Slot(str)
    def _on_ki_error(self, msg):
        self._stop_stream_timers()
        self._ki_area.setPlainText(msg)
        self._btn_ki.setEnabled(True)
        self._set_status("❌ Fehler – Details in der KI-Antwort")
        fehlertext = msg.replace("# ❌ Fehler:\n", "").strip()
        if fehlertext:
            self.fehler_anzeigen(fehlertext)

    @QtCore.Slot(str, str)
    def _on_self_correction_needed(self, code: str, fehler: str):
        """Sandbox-Fehler an KI schicken – läuft vollständig im GUI-Thread."""
        import threading, time as _time
        if not hasattr(self, "_fehler_panel"):
            return

        source = self._src_box.currentText()
        model  = self._model_box.currentText()
        temp   = self._temp_box.value() if hasattr(self, "_temp_box") else 0.1

        if not source or not model:
            self._fehler_panel._sb_status.setText("⚠ Kein KI-Anbieter konfiguriert")
            return

        # Fehler-Verlauf akkumulieren (wie im Referenzprojekt freecad-ai)
        # Verlauf wird bei neuem KI-Aufruf (_ki_senden) automatisch zurückgesetzt
        if not hasattr(self, "_korrektur_verlauf"):
            self._korrektur_verlauf = []
        self._korrektur_verlauf.append((code, fehler))

        from data.nl_generator import NL_SYSTEM_PROMPT
        system_prompt = (
            NL_SYSTEM_PROMPT
            + "\n\n━━━ KORREKTUR-MODUS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Antworte NUR mit dem korrigierten Python-Code.\n"
            "Kein erklärender Text, keine Markdown-Fences (``` oder ```python).\n"
            "Behalte alle Konstanten und Variablennamen aus dem Original."
        )

        # Alle vorherigen Versuche mit einschließen damit KI denselben Fehler
        # nicht wiederholt — entspricht conversation history im Referenzprojekt
        verlauf_text = ""
        for i, (v_code, v_fehler) in enumerate(self._korrektur_verlauf[:-1], 1):
            verlauf_text += (
                f"\n━━━ Fehlgeschlagener Versuch {i} ━━━\n"
                f"Code:\n{v_code}\n"
                f"Fehler: {v_fehler}\n"
            )

        versuch_nr  = len(self._korrektur_verlauf)
        max_vers    = self._fehler_panel._max_korrekturen
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

        self._ki_area.clear()
        self._chunk_buffer.clear()
        self._stream_token_count = 0
        self._stream_start_time  = _time.monotonic()
        self._flush_timer.start()
        self._status_timer.start()
        self._btn_ki.setEnabled(False)
        self._set_status("🔧 KI korrigiert Sandbox-Fehler …")

        fehler_panel_ref = self._fehler_panel
        ki_area_ref      = self._ki_area
        set_status_ref   = self._set_status

        def _nach_stream():
            import re as _re2
            korrigiert = ki_area_ref.toPlainText().strip()
            korrigiert = _re2.sub(r"```python|```", "", korrigiert).strip()
            # Auto-Fixer auch auf KI-Korrekturen anwenden
            if korrigiert:
                korrigiert, _ = self._freecad_code_korrigieren(korrigiert)

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

            # singleShot(0) stellt die Ausführung in die Qt-Ereignis-Schleife
            # → thread-sicher, ohne QMetaObject.invokeMethod
            QtCore.QTimer.singleShot(0, _gui_update)
            try:
                self._ki_stream_done.disconnect(_nach_stream)
            except Exception:
                pass

        self._ki_stream_done.connect(_nach_stream)
        threading.Thread(
            target=self._worker_mit_system,
            args=(source, model, system_prompt, user_prompt, temp),
            daemon=True,
        ).start()
