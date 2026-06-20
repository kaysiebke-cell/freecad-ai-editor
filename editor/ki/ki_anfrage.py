# -*- coding: utf-8 -*-
"""
ki_anfrage.py
─────────────
KIAnfrage – Prompt-Aufbau und Versand aller KI-Anfragen.

Enthält:
  - refresh_models: Modell-Liste laden (Ollama + statische Listen)
  - ki_fragen:       Haupt-Anfrage mit Verlauf-Verwaltung
  - auto_analyse:    1-Klick-Analyse des gesamten Editor-Inhalts
  - ki_fehler_erklaeren: Fehler-Panel-Inhalt an KI senden
"""

import time
import threading

from core.qt_compat import requests as _requests, HAS_REQUESTS as _HAS_REQUESTS
from core.params import KI_PRESETS
from editor.ki.provider_daten import _MODELLE
from editor.ki.ki_verlauf import _VERLAUF_MAX_NACHRICHTEN
from editor.ki.kod_analyse import erstelle_code_sitemap, extrahiere_fehler_kontext


class KIAnfrage:
    """Baut KI-Prompts auf und startet Worker-Threads."""

    def __init__(self, controller):
        self._c = controller

    # ── Modelle laden ─────────────────────────────────────────────────────

    def refresh_models(self):
        """Modell-Liste für den aktuell gewählten Anbieter laden."""
        self._c._model_box.clear()
        src = self._c._src_box.currentText()
        if src.startswith("Ollama"):
            if not _HAS_REQUESTS:
                self._c._model_box.addItem("requests fehlt")
                self._c._set_status("⚠  requests nicht installiert – KI nicht verfügbar")
                return
            try:
                r = _requests.get("http://localhost:11434/api/tags", timeout=3)
                r.raise_for_status()
                models = [m["name"] for m in r.json().get("models", [])]
                self._c._model_box.addItems(models or ["(keine Modelle)"])
                hat_coder = any("coder" in m.lower() for m in models)
                if not models:
                    self._c._set_status("⚠  Ollama: keine Modelle gefunden")
                elif not hat_coder:
                    self._c._set_status(
                        f"🔄 Ollama: {len(models)} Modell(e) geladen — "
                        "💡 Tipp: 'ollama pull qwen2.5-coder:7b' für bessere FreeCAD-Code-Ergebnisse")
                else:
                    self._c._set_status(f"🔄 Ollama: {len(models)} Modell(e) geladen")
            except Exception as e:
                self._c._model_box.addItem(f"Ollama: {e}")
                self._c._set_status(f"⚠  Ollama nicht erreichbar: {e}")
            return
        for pfx, (label, models) in _MODELLE.items():
            if src.startswith(pfx):
                self._c._model_box.addItems(models)
                self._c._set_status(f"🔄 {label}: {len(models)} Modelle geladen")
                return
        models = ["anthropic/claude-sonnet-4-5", "anthropic/claude-haiku-4-5",
                  "google/gemini-pro-1.5", "openai/gpt-4o-mini"]
        self._c._model_box.addItems(models)
        self._c._set_status(f"🔄 OpenRouter: {len(models)} Modelle geladen")

    # ── 1-Klick-Analyse ───────────────────────────────────────────────────

    def auto_analyse(self):
        """Lädt den gesamten Editor-Inhalt und startet KI-Erklärung."""
        code = self._c._editor.toPlainText().strip()
        if not code:
            self._c._set_status("⚠  Editor ist leer – zuerst eine Datei laden")
            return
        self._c.find_area.setPlainText(code)
        preset_name = "★ Was macht dieser Code?"
        idx = self._c._preset_box.findText(preset_name)
        if idx >= 0:
            self._c._preset_box.setCurrentIndex(idx)
        self._c._set_status("🔎 Code geladen – KI-Anfrage läuft …")
        self.ki_fragen()

    # ── Haupt-Anfrage ─────────────────────────────────────────────────────

    def ki_fragen(self):
        """Baut den vollständigen Prompt und startet den passenden Worker-Thread."""
        if not _HAS_REQUESTS:
            self._c._set_status("❌ requests-Modul nicht installiert")
            return

        # Code-Quelle bestimmen
        code = self._c.find_area.toPlainText().strip()
        code_quelle = "suchfeld"
        if not code:
            alle_zeilen = self._c._editor.toPlainText().splitlines()
            if not alle_zeilen:
                # Kein Code — nur erlaubt wenn eine eigene Frage vorhanden ist
                _fq_check = getattr(self._c, "_frage_feld", None)
                if not (_fq_check and _fq_check.toPlainText().strip()):
                    self._c._set_status("⚠  KI-Input und Editor sind leer – bitte Frage oder Code eingeben")
                    return
                code_quelle = "nur_frage"
            elif len(alle_zeilen) > 200:
                code = "\n".join(alle_zeilen[:200]) + "\n# … [gekürzt auf 200 Zeilen]"
                self._c._set_status("ℹ  Suchfeld leer – sende erste 200 Zeilen des Editors")
                code_quelle = "editor"
            else:
                code = "\n".join(alle_zeilen)
                self._c._set_status("ℹ  Suchfeld leer – sende gesamten Editor-Inhalt")
                code_quelle = "editor"

        from editor.ki.nl_generator import (NL_SYSTEM_PROMPT, NL_SYSTEM_PROMPT_OLLAMA,
                                            NL_PRESET_SCHLUESSEL,
                                            NL_SYSTEM_PROMPT_PARTDESIGN, NL_PRESET_SCHLUESSEL_PD,
                                            NL_SYSTEM_PROMPT_SCHRITTWEISE, NL_PRESET_SCHLUESSEL_SW,
                                            NL_PRESET_SCHLUESSEL_TC)
        preset_name  = self._c._preset_box.currentText()
        ist_nl_modus = preset_name == NL_PRESET_SCHLUESSEL
        ist_pd_modus = preset_name == NL_PRESET_SCHLUESSEL_PD
        ist_sw_modus = preset_name == NL_PRESET_SCHLUESSEL_SW
        ist_tc_modus = preset_name == NL_PRESET_SCHLUESSEL_TC

        # FC12/FC13: Harte Sperre bei Ollama
        if ist_sw_modus and self._c._src_box.currentText().startswith("Ollama"):
            from core.qt_compat import QtWidgets
            QtWidgets.QMessageBox.critical(
                self._c,
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
            self._c._btn_ki.setEnabled(True)
            self._c._set_status(
                "❌ FC13 benötigt ein stärkeres Modell – bitte Backend wechseln")
            return

        if ist_pd_modus and self._c._src_box.currentText().startswith("Ollama"):
            from core.qt_compat import QtWidgets
            QtWidgets.QMessageBox.critical(
                self._c,
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
            self._c._btn_ki.setEnabled(True)
            self._c._set_status(
                "❌ FC12 benötigt Claude oder GPT-4o – bitte Backend wechseln")
            return

        # Eigene Fragestellung hat Vorrang vor dem Preset
        _frage_widget = getattr(self._c, "_frage_feld", None)
        eigene_frage = _frage_widget.toPlainText().strip() if _frage_widget else ""

        prompt = KI_PRESETS.get(preset_name, "").strip()
        if not prompt:
            prompt = "Verbessere und kommentiere diesen Python-Code auf Deutsch."
        if eigene_frage:
            prompt = eigene_frage

        # Barrierefreiheit: Sprach-Zusätze an Prompt anhängen
        try:
            from ui.barrierefreiheit import BarrierefreiheitPanel as _BF
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

        kontext = self._c._kontext.toPlainText().strip()
        if kontext:
            prompt = f"Projektkontext: {kontext}\n\n{prompt}"

        self._c._btn_ki.setEnabled(False)
        self._c._btn_ersetzen.setEnabled(False)
        self._c._ki_area.clear()
        self._c._chunk_buffer.clear()
        self._c._stream_token_count = 0
        self._c._warte_dots  = 0
        self._c._warte_aktiv = True
        self._c._stream_start_time = time.monotonic()
        self._c._flush_timer.start()
        self._c._status_timer.start()
        if hasattr(self._c, "_warte_timer"):
            self._c._warte_timer.start()

        verlauf_kb = self._c._verlauf.groesse() // 1024
        self._c._status.setText(
            f"🤖 Warte auf ersten Token … | Verlauf: {verlauf_kb} KB")

        # Sitemap: nur Struktur-Übersicht, kein voller Code-Text
        sitemap = erstelle_code_sitemap(self._c._editor.toPlainText())
        sitemap_block = (
            "Struktur der aktuell geöffneten Datei:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{sitemap}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        ) if sitemap else ""

        from editor.ki.ki_modi import MODUS_PROMPTS, MODUS_DEFAULT
        modus_prefix = MODUS_PROMPTS.get(
            getattr(self._c, "_ki_modus", MODUS_DEFAULT), "")

        if code_quelle == "nur_frage":
            # Reine Frage ohne Code — kein Code-Block im Prompt
            full_prompt = (
                f"{sitemap_block}"
                f"{prompt}\n\n"
                f"{modus_prefix}"
            )
        else:
            herkunft = "Markierter Block" if code_quelle == "suchfeld" else "Editor-Inhalt"
            full_prompt = (
                f"{sitemap_block}"
                f"Aufgabe: {prompt}\n\n"
                f"{herkunft}:\n```python\n{code}\n```\n\n"
                "Antworte ausschließlich mit fertigem Python-Code ohne Markdown.\n"
                f"{modus_prefix}"
            )

        # Verlauf erweitern + absolutes Limit prüfen
        if not hasattr(self._c, "_chat_verlauf"):
            self._c._verlauf.reset()

        while len(self._c._chat_verlauf) >= _VERLAUF_MAX_NACHRICHTEN:
            self._c._chat_verlauf.pop(0)

        self._c._chat_verlauf.append({"role": "user", "content": full_prompt})

        # UI-Werte VOR dem Thread-Start im Hauptthread sichern
        source_text   = self._c._src_box.currentText()
        model_text    = self._c._model_box.currentText()
        temp_val      = self._c._temp_box.value()
        verlauf_kopie = list(self._c._chat_verlauf)
        ki_modus_wert = getattr(self._c, "_ki_modus", None)

        nl_inhalt = code or eigene_frage  # bei reiner Frage ohne Code: Frage direkt senden

        # FreeCAD-Dokumentzustand einbauen — kompakt für Ollama, voll für Cloud
        try:
            from editor.ki.dokument_kontext import (get_dokument_kontext_kompakt,
                                                     get_dokument_kontext)
            ist_ollama = source_text.startswith("Ollama")
            if ist_ollama:
                dok_info = get_dokument_kontext_kompakt()
                if dok_info:
                    nl_inhalt = f"{dok_info}\n\n{nl_inhalt}"
            else:
                dok_info = get_dokument_kontext()
                if dok_info and "nicht verfügbar" not in dok_info and "Objekte: (keine)" not in dok_info:
                    nl_inhalt = f"Aktueller FreeCAD-Zustand:\n{dok_info}\n\n{nl_inhalt}"
        except Exception:
            pass

        if ist_nl_modus:
            from editor.ki.nl_generator import NL_TEMPERATURE
            ist_ollama_nl = source_text.startswith("Ollama")
            fc11_prompt = (NL_SYSTEM_PROMPT_OLLAMA if ist_ollama_nl else NL_SYSTEM_PROMPT)

            # Tipp: qwen2.5-coder empfehlen wenn kein Code-Modell gewählt
            if ist_ollama_nl and "coder" not in model_text.lower():
                self._c._set_status(
                    "💡 Tipp: qwen2.5-coder:7b liefert bessere FreeCAD-Code-Ergebnisse "
                    "als allgemeine Modelle (ollama pull qwen2.5-coder:7b)")

            # AGENTS.md neben geöffneter Datei oder im Home-Verzeichnis laden
            try:
                import os as _os
                _pfad = getattr(self._c, "_pfad", None)
                if _pfad:
                    _agents_pfad = _os.path.join(_os.path.dirname(_pfad), "AGENTS.md")
                else:
                    _agents_pfad = _os.path.join(_os.path.expanduser("~"), "AGENTS.md")
                from editor.ki.dokument_kontext import _lade_agents_md
                _agents_text = _lade_agents_md(_agents_pfad)
                if _agents_text:
                    fc11_prompt = fc11_prompt + "\n━━━ PROJEKTANWEISUNGEN ━━━\n" + _agents_text
            except Exception:
                pass

            self._c._nl_antwort_aktiv = True
            threading.Thread(
                target=self._c._streaming.worker_mit_system,
                args=(source_text, model_text, fc11_prompt, nl_inhalt,
                      NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()
        elif ist_pd_modus:
            from editor.ki.nl_generator import NL_TEMPERATURE
            self._c._nl_antwort_aktiv = True
            threading.Thread(
                target=self._c._streaming.worker_mit_system,
                args=(source_text, model_text, NL_SYSTEM_PROMPT_PARTDESIGN,
                      nl_inhalt, NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()
        elif ist_sw_modus:
            from editor.ki.nl_generator import NL_TEMPERATURE
            vorhandener_code = self._c._editor.toPlainText().strip()
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
            self._c._nl_antwort_aktiv = True
            self._c._sw_modus_aktiv   = True
            threading.Thread(
                target=self._c._streaming.worker_mit_system,
                args=(source_text, model_text, NL_SYSTEM_PROMPT_SCHRITTWEISE,
                      sw_user_prompt, NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()
        elif ist_tc_modus:
            from editor.ki.nl_generator import NL_TEMPERATURE
            from editor.ki.fc14_tool_calling import FC14_SYSTEM_PROMPT
            self._c._nl_antwort_aktiv = True
            self._c._tc_modus_aktiv   = True
            threading.Thread(
                target=self._c._streaming.worker_mit_system,
                args=(source_text, model_text, FC14_SYSTEM_PROMPT,
                      nl_inhalt, NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()
        else:
            self._c._nl_antwort_aktiv = False
            threading.Thread(
                target=self._c._streaming.worker_mit_verlauf,
                args=(source_text, model_text, verlauf_kopie, temp_val),
                daemon=True
            ).start()

    # ── Fehler-Erklärung ──────────────────────────────────────────────────

    def ki_fehler_erklaeren(self):
        """Fehlertext aus _fehler_eingabe mit Code-Ausschnitt an KI senden."""
        if not _HAS_REQUESTS:
            self._c._set_status("❌ requests-Modul nicht installiert")
            return

        fehler_widget = getattr(self._c, "_fehler_eingabe", None)
        if fehler_widget is None:
            self._c._set_status("⚠  Fehler-Panel nicht gefunden")
            return

        fehler_text = fehler_widget.toPlainText().strip()
        if not fehler_text:
            self._c._set_status("⚠  Fehler-Panel ist leer")
            return

        aktueller_code  = self._c._editor.toPlainText()
        code_ausschnitt = extrahiere_fehler_kontext(aktueller_code, fehler_text)

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

        source_text = self._c._src_box.currentText()
        model_text  = self._c._model_box.currentText()
        temp_val    = self._c._temp_box.value()

        self._c._ki_area.clear()
        self._c._chunk_buffer.clear()
        self._c._stream_token_count = 0
        self._c._stream_start_time  = time.monotonic()
        self._c._flush_timer.start()
        self._c._status_timer.start()
        self._c._set_status("⏳ Verbinde mit KI ...")
        self._c._btn_ki.setEnabled(False)
        self._c._btn_ersetzen.setEnabled(False)

        threading.Thread(
            target=self._c._streaming.worker_mit_system,
            args=(source_text, model_text, system, user_prompt, temp_val),
            daemon=True
        ).start()
