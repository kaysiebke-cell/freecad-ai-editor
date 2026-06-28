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


# ── Automatische API-Kontext-Injektion ────────────────────────────────────────

_DE_EN_MAP = {
    "kugel": "sphere",    "zylinder": "cylinder", "kasten": "box",
    "würfel": "box",      "kegel": "cone",         "torus": "torus",
    "schneid": "cut",     "loch": "cut",            "bohrung": "cut",
    "verschmelz": "fuse", "vereinig": "fuse",       "subtrak": "cut",
    "verschieb": "placement", "platz": "placement", "position": "placement",
    "dreh": "rotation",   "vektor": "vector",       "körper": "body",
    "skizze": "sketch",   "aufpolster": "pad",      "tasche": "pocket",
    "netz": "mesh",       "auswahl": "selection",   "ansicht": "view",
}

_STOPP = {
    "und", "oder", "mit", "von", "ein", "eine", "einem", "einen", "einer",
    "der", "die", "das", "dem", "den", "des", "in", "auf", "an", "zu",
    "als", "für", "ist", "wird", "werden", "soll", "durch", "nach",
    "create", "make", "the", "with", "from", "that", "this", "into",
    "using", "erstelle", "erzeuge", "mache", "erstell",
}


def _relevante_api_hints(frage: str, max_hints: int = 5) -> str:
    """Sucht passende API-Hints anhand von Schlüsselwörtern aus der Nutzerfrage."""
    try:
        from data.freecad_api_hints import FC_API_HINTS
    except ImportError:
        return ""

    woerter = set()
    for w in frage.lower().split():
        w = w.strip(".,;:!?()[]'\"")
        if len(w) > 3 and w not in _STOPP:
            woerter.add(w)
            for de, en in _DE_EN_MAP.items():
                if de in w:
                    woerter.add(en)

    if not woerter:
        return ""

    treffer = []
    for signatur, beschreibung in FC_API_HINTS:
        text = (signatur + " " + beschreibung).lower()
        score = sum(1 for w in woerter if w in text)
        if score > 0:
            treffer.append((score, signatur, beschreibung))

    treffer.sort(key=lambda x: x[0], reverse=True)
    if not treffer:
        return ""

    zeilen = ["## FreeCAD API – relevante Funktionen:"]
    for _, sig, desc in treffer[:max_hints]:
        zeilen.append(f"  {sig}\n  # {desc}")
    return "\n".join(zeilen)


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
        ist_nl_modus = NL_PRESET_SCHLUESSEL    in preset_name
        ist_pd_modus = NL_PRESET_SCHLUESSEL_PD in preset_name
        ist_sw_modus = NL_PRESET_SCHLUESSEL_SW in preset_name
        ist_tc_modus = NL_PRESET_SCHLUESSEL_TC in preset_name

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

        # API-Hints automatisch aus Nutzerfrage ableiten
        _hints_block = _relevante_api_hints(eigene_frage or prompt)
        _hints_section = f"\n\n{_hints_block}" if _hints_block else ""

        if code_quelle == "nur_frage":
            full_prompt = (
                f"{sitemap_block}"
                f"{prompt}{_hints_section}\n\n"
                f"{modus_prefix}"
            )
        else:
            herkunft = "Markierter Block" if code_quelle == "suchfeld" else "Editor-Inhalt"
            full_prompt = (
                f"{sitemap_block}"
                f"Aufgabe: {prompt}\n\n"
                f"{herkunft}:\n```python\n{code}\n```"
                f"{_hints_section}\n\n"
                "Antworte ausschließlich mit fertigem Python-Code ohne Markdown.\n"
                f"{modus_prefix}"
            )

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

        # FC11: Nutzerbeschreibung aus frage_feld hat Vorrang — nie alten Editor-Code senden
        ist_ollama_quelle = source_text.startswith("Ollama")
        if ist_nl_modus:
            nl_inhalt = eigene_frage or code
        else:
            nl_inhalt = code or eigene_frage

        # FreeCAD-Dokumentzustand einbauen — nur für Cloud und nicht-FC11
        try:
            from editor.ki.dokument_kontext import (get_dokument_kontext_kompakt,
                                                     get_dokument_kontext)
            if not ist_ollama_quelle and not ist_nl_modus:
                dok_info = get_dokument_kontext()
                if dok_info and "nicht verfügbar" not in dok_info and "Objekte: (keine)" not in dok_info:
                    nl_inhalt = f"Aktueller FreeCAD-Zustand:\n{dok_info}\n\n{nl_inhalt}"
            elif ist_ollama_quelle and not ist_nl_modus:
                dok_info = get_dokument_kontext_kompakt()
                if dok_info:
                    nl_inhalt = f"{dok_info}\n\n{nl_inhalt}"
        except Exception:
            pass

        # API-Hints an NL-Inhalt anhängen — NUR für Cloud
        if _hints_section and not ist_ollama_quelle:
            nl_inhalt = f"{nl_inhalt}{_hints_section}"

        if ist_nl_modus:
            from editor.ki.nl_generator import NL_TEMPERATURE
            from core.params import lade_fc11_regeln, lade_plan_modus
            ist_ollama_nl = ist_ollama_quelle
            _standard = NL_SYSTEM_PROMPT_OLLAMA if ist_ollama_nl else NL_SYSTEM_PROMPT
            fc11_prompt = lade_fc11_regeln(_standard)
            _plan_zusatz = (
                "\n\n[PLAN]\nSchreibe als ERSTE Zeilen Python-Kommentare:\n"
                "# Objekte: [welche Part::-Objekte]\n"
                "# Operationen: [Part::Cut / Part::Fuse / keine]\n"
                "# Platzierung: [wie positioniert]\n"
                "Dann den vollständigen Code."
            ) if lade_plan_modus() else ""

            # Passende Beispiele — NUR für Cloud (Ollama-Prompt hat bereits Vorlagen)
            _beispiel_block = ""
            if not ist_ollama_nl:
                try:
                    from data.freecad_beispiele import beispiele_finden
                    _bsp = beispiele_finden(nl_inhalt, max_beispiele=2)
                    if _bsp:
                        _beispiel_block = f"\n\n{_bsp}"
                except Exception:
                    pass

            if _plan_zusatz:
                nl_inhalt = f"{nl_inhalt}{_plan_zusatz}"
            if _beispiel_block:
                nl_inhalt = f"{nl_inhalt}{_beispiel_block}"

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

            # Skills: passende Skill-Dateien anhand von Stichwörtern anhängen
            try:
                import re as _re, os as _os
                _skills_dir = _os.path.join(
                    _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))),
                    "data", "skills"
                )
                _fastener_pattern = _re.compile(
                    r'\b(M\d+(\.\d+)?|Schraube|Gewinde|hole|loch|'
                    r'counterbore|countersink|Senkung|Kernloch|Durchgangsloch)\b',
                    _re.IGNORECASE
                )
                if _fastener_pattern.search(nl_inhalt):
                    _skill_pfad = _os.path.join(_skills_dir, "fastener-hole.md")
                    if _os.path.isfile(_skill_pfad):
                        with open(_skill_pfad, encoding="utf-8") as _sf:
                            fc11_prompt = (fc11_prompt
                                           + "\n━━━ SKILL: SCHRAUBENLÖCHER ━━━\n"
                                           + _sf.read())
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
            from core.params import lade_nl_regeln
            self._c._nl_antwort_aktiv = True
            threading.Thread(
                target=self._c._streaming.worker_mit_system,
                args=(source_text, model_text,
                      lade_nl_regeln("fc12", NL_SYSTEM_PROMPT_PARTDESIGN),
                      nl_inhalt, NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()

        elif ist_sw_modus:
            from editor.ki.nl_generator import NL_TEMPERATURE
            from core.params import lade_nl_regeln
            schritt = nl_inhalt.strip() if nl_inhalt.strip() else code
            verlauf_eintraege = getattr(self._c, "_sw_verlauf", [])
            if verlauf_eintraege:
                vorhandener_code = self._c._editor.toPlainText().strip()
            else:
                vorhandener_code = ""
                self._c._sw_verlauf = []
            bisherige_schritte = ""
            if verlauf_eintraege:
                zeilen = [f"{i}. {e[0]}" for i, e in enumerate(verlauf_eintraege, 1)]
                bisherige_schritte = "Bisherige Schritte:\n" + "\n".join(zeilen) + "\n\n"
            if vorhandener_code:
                sw_user_prompt = (
                    f"{bisherige_schritte}"
                    f"Vorhandener Code (NICHT wiederholen):\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{vorhandener_code}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Neuer Schritt (NUR diesen Code-Block zurueckgeben):\n{schritt}"
                )
            else:
                sw_user_prompt = schritt
            self._c._nl_antwort_aktiv = True
            self._c._sw_modus_aktiv   = True
            if hasattr(self._c, "_frage_feld"):
                self._c._frage_feld.clear()
            threading.Thread(
                target=self._c._streaming.worker_mit_system,
                args=(source_text, model_text,
                      lade_nl_regeln("fc13", NL_SYSTEM_PROMPT_SCHRITTWEISE),
                      sw_user_prompt, NL_TEMPERATURE),
                kwargs={"preset_name": preset_name, "ki_modus": ki_modus_wert},
                daemon=True
            ).start()

        elif ist_tc_modus:
            from editor.ki.nl_generator import NL_TEMPERATURE
            if ist_ollama_quelle:
                self._c._nl_antwort_aktiv = False
                self._c._tc_modus_aktiv   = False
                threading.Thread(
                    target=self._c._streaming.worker_ollama_tools,
                    args=(model_text, nl_inhalt, NL_TEMPERATURE),
                    daemon=True
                ).start()
            else:
                from editor.ki.fc14_tool_calling import FC14_SYSTEM_PROMPT
                from core.params import lade_nl_regeln
                self._c._nl_antwort_aktiv = True
                self._c._tc_modus_aktiv   = True
                threading.Thread(
                    target=self._c._streaming.worker_mit_system,
                    args=(source_text, model_text,
                          lade_nl_regeln("fc14", FC14_SYSTEM_PROMPT),
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
                "You are a FreeCAD Python debugger. "
                "The user has received a runtime error.\n"
                "Here is the relevant code excerpt "
                "(──▶ marks the faulty line):\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{code_ausschnitt}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Briefly explain in German why this error occurs, "
                "and provide the corrected version of only this code block."
            )
        else:
            system = (
                "You are a FreeCAD Python debugger. "
                "Explain in German why this error occurs and how to fix it."
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
