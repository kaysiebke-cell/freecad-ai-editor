# -*- coding: utf-8 -*-
"""
ki_controller.py
────────────────
Ki – Koordinator für die gesamte KI-Funktionalität.

Delegiert an Kompositions-Objekte in editor/ki/intern/:
  _streaming  → KIStreaming   (HTTP-Streaming aller Anbieter + Worker-Threads)
  _verlauf    → KIVerlauf     (Chat-Verlauf-Verwaltung)
  _sitzung    → KISitzung     (Sitzung speichern/laden)
  _anfrage    → KIAnfrage     (Prompt-Bau + KI-Anfragen)
  _chunk      → KIChunkUI     (Chunk-Puffer + Stream-Done-Verarbeitung)
  _ki_fehler  → KIFehlerUI    (Fehler-Panel + Selbstkorrektur)
"""


from core.qt_compat import QtCore

from editor.ki.provider_daten import _OAI_URLS, _MODELLE
from editor.ki.ki_streaming import KIStreaming
from editor.ki.ki_verlauf import KIVerlauf
from editor.ki.ki_sitzung import KISitzung
from editor.ki.ki_anfrage import KIAnfrage
from editor.ki.ki_chunk import KIChunkUI
from editor.ki.ki_fehler import KIFehlerUI
from editor.ki.kod_korrektor import (freecad_code_korrigieren,
                                     extrahiere_code_aus_nl_antwort,
                                     schneide_erklaerung_ab,
                                     kommentiere_text_zeilen)
from editor.ki.kod_analyse import erstelle_code_sitemap, extrahiere_fehler_kontext


class Ki:
    """KI-Koordinator – delegiert an Kompositions-Objekte in editor/ki/intern/."""

    # Konstanten – werden von _refresh_models / _ki_fragen genutzt
    _OAI_URLS = _OAI_URLS
    _MODELLE  = _MODELLE

    def __init__(self, editor):
        self._e = editor

    # ── Lazy-Initialisierung ──────────────────────────────────────────────

    def _ki_aufbauen(self):
        """Initialisiert alle Kompositions-Objekte (einmalig beim ersten Aufruf).

        Werden bewusst auf self._e (dem echten Editor) abgelegt, nicht auf
        self: editor/ki/intern/*.py greift selbst über self._c._streaming
        usw. direkt auf den Editor zu (self._c ist dort der Editor).
        """
        self._e._streaming = KIStreaming(self._e)
        self._e._verlauf   = KIVerlauf(self._e)
        self._e._sitzung   = KISitzung(self._e)
        self._e._anfrage   = KIAnfrage(self._e)
        self._e._chunk     = KIChunkUI(self._e)
        self._e._ki_fehler = KIFehlerUI(self._e)

    def _ki_bereit(self):
        """Stellt sicher dass alle Kompositions-Objekte initialisiert sind."""
        if not hasattr(self._e, "_streaming"):
            self._ki_aufbauen()

    # ── Modelle laden ─────────────────────────────────────────────────────

    def _refresh_models(self):
        self._ki_bereit()
        self._e._anfrage.refresh_models()

    # ── 1-Klick-Analyse ───────────────────────────────────────────────────

    def _auto_analyse(self):
        self._ki_bereit()
        self._e._anfrage.auto_analyse()

    # ── Haupt-Anfrage ─────────────────────────────────────────────────────

    def _ki_fragen(self):
        self._ki_bereit()
        self._e._anfrage.ki_fragen()

    # ── Fehler-Erklärung ──────────────────────────────────────────────────

    def _ki_fehler_erklaeren(self):
        self._ki_bereit()
        self._e._anfrage.ki_fehler_erklaeren()

    # ── Worker-Threads (extern verknüpft, z.B. von Fehler-Panel) ─────────

    def _worker_mit_system(self, source, model, system_prompt, user_prompt,
                            temperature=0.2, preset_name="", ki_modus=None):
        self._ki_bereit()
        self._e._streaming.worker_mit_system(
            source, model, system_prompt, user_prompt,
            temperature, preset_name, ki_modus)

    def _worker_mit_verlauf(self, source, model, verlauf, temperature=0.2):
        self._ki_bereit()
        self._e._streaming.worker_mit_verlauf(source, model, verlauf, temperature)

    # ── Sitzung ───────────────────────────────────────────────────────────

    def _sitzung_speichern(self):
        self._ki_bereit()
        self._e._sitzung.speichern()

    def _sitzung_laden(self):
        self._ki_bereit()
        self._e._sitzung.laden()

    # ── Chat-Verlauf ──────────────────────────────────────────────────────

    def _ki_verlauf_reset(self):
        self._ki_bereit()
        self._e._verlauf.reset()

    def _ki_verlauf_groesse(self) -> int:
        self._ki_bereit()
        return self._e._verlauf.groesse()

    def _ki_verlauf_komprimieren(self, source, model, temperature):
        self._ki_bereit()
        self._e._verlauf.komprimieren(source, model, temperature)

    def _einmaliger_aufruf(self, source, model, prompt, temperature) -> str:
        self._ki_bereit()
        return self._e._streaming.einmaliger_aufruf(source, model, prompt, temperature)

    # ── Chunk-Verarbeitung (Signal-Slots) ─────────────────────────────────

    @QtCore.Slot(str)
    def _on_ki_chunk(self, chunk: str):
        self._ki_bereit()
        self._e._chunk.on_chunk(chunk)

    def _flush_chunks(self):
        self._ki_bereit()
        self._e._chunk.flush_chunks()

    def _update_stream_status(self):
        self._ki_bereit()
        self._e._chunk.update_stream_status()

    def _stop_stream_timers(self):
        self._ki_bereit()
        self._e._chunk.stop_stream_timers()

    @QtCore.Slot()
    def _on_ki_stream_done(self):
        self._ki_bereit()
        self._e._chunk.on_stream_done()
        from core.params import lade_auto_einfuegen
        if (lade_auto_einfuegen()
                and getattr(self._e, "_btn_einfuegen", None)
                and self._e._btn_einfuegen.isEnabled()):
            self._e._einfuegen_nach_fundstelle()

    # ── Fehler-Anzeige (Signal-Slots + öffentliche API) ───────────────────

    @QtCore.Slot(str)
    def fehler_anzeigen(self, fehlertext: str):
        self._ki_bereit()
        self._e._ki_fehler.fehler_anzeigen(fehlertext)

    @QtCore.Slot(str)
    def _on_ki_error(self, msg: str):
        self._ki_bereit()
        self._e._ki_fehler.on_ki_error(msg)

    @QtCore.Slot(str, str)
    def _on_self_correction_needed(self, code: str, fehler: str):
        self._ki_bereit()
        self._e._ki_fehler.on_self_correction_needed(code, fehler)

    # ── Reine Funktionen als Methoden (Rückwärts-Kompatibilität) ─────────

    def _freecad_code_korrigieren(self, code: str):
        return freecad_code_korrigieren(code)

    def _extrahiere_code_aus_nl_antwort(self, text: str) -> str:
        return extrahiere_code_aus_nl_antwort(text)

    def _schneide_erklaerung_ab(self, text: str) -> str:
        return schneide_erklaerung_ab(text)

    def _kommentiere_text_zeilen(self, text: str) -> str:
        return kommentiere_text_zeilen(text)

    def _erstelle_code_sitemap(self, code_text: str) -> str:
        return erstelle_code_sitemap(code_text)

    def _extrahiere_fehler_kontext(self, code_text: str, fehler_meldung: str,
                                    puffer: int = 5) -> str:
        return extrahiere_fehler_kontext(code_text, fehler_meldung, puffer)

    # ── Stream-Anbieter-Weiche (wird z.B. von ki_werkzeuge genutzt) ───────

    def _stream_fuer_anbieter(self, source, model, prompt, temperature):
        self._e._streaming.stream_fuer_anbieter(source, model, prompt, temperature)

    def _stream_ollama(self, model, prompt, temperature):
        self._e._streaming.stream_ollama(model, prompt, temperature)

    def _stream_anthropic(self, key, model, prompt, temperature):
        self._e._streaming.stream_anthropic(key, model, prompt, temperature)

    def _stream_openai_compat(self, base_url, key, model, prompt, temperature):
        self._e._streaming.stream_openai_compat(base_url, key, model, prompt, temperature)

    def _stream_anthropic_verlauf(self, key, model, verlauf, temperature):
        self._e._streaming.stream_anthropic_verlauf(key, model, verlauf, temperature)

    def _stream_openai_verlauf(self, base_url, key, model, verlauf, temperature):
        self._e._streaming.stream_openai_verlauf(base_url, key, model, verlauf, temperature)
