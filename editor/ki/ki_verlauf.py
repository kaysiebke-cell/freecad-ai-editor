# -*- coding: utf-8 -*-
"""
ki_verlauf.py
─────────────
KIVerlauf – Chat-Verlauf-Verwaltung mit Context Compacting.
"""

# Ungefähre Token-Schätzung: 1 Token ≈ 4 Zeichen
_ZEICHEN_PRO_TOKEN = 4
_COMPACT_SCHWELLE  = 5_000
_COMPACT_BEHALTEN  = 4
_VERLAUF_MAX_NACHRICHTEN = 20


class KIVerlauf:
    """Verwaltet den Chat-Verlauf und komprimiert ihn bei Bedarf."""

    def __init__(self, controller):
        self._c = controller

    def reset(self):
        """Gesprächsverlauf leeren (z.B. bei neuer Datei oder manuell)."""
        self._c._chat_verlauf               = []
        self._c._compact_zusammenfassung    = ""
        self._c._korrektur_verlauf          = []
        if hasattr(self._c, "_ki_area"):
            self._c._ki_area.clear()
        if hasattr(self._c, "_chunk_buffer"):
            self._c._chunk_buffer.clear()
        self._c._set_status("🧹 Gesprächsverlauf geleert")

    def groesse(self) -> int:
        """Gibt die geschätzte Zeichenzahl des gesamten Verlaufs zurück."""
        return sum(len(m["content"]) for m in self._c._chat_verlauf)

    def komprimieren(self, source, model, temperature):
        """Komprimiert ältere Nachrichten zu einer Zusammenfassung.

        Die neuesten _COMPACT_BEHALTEN Nachrichten bleiben erhalten.
        Läuft SYNCHRON (blocking) im Worker-Thread.
        """
        if len(self._c._chat_verlauf) <= _COMPACT_BEHALTEN:
            return
        alte   = self._c._chat_verlauf[:-_COMPACT_BEHALTEN]
        neue   = self._c._chat_verlauf[-_COMPACT_BEHALTEN:]
        inhalt = "\n\n".join(
            f"[{m['role'].upper()}]: {m['content'][:600]}" for m in alte)
        zusammen_prompt = (
            "Fasse das folgende Gespräch auf Deutsch in maximal 5 Sätzen zusammen. "
            "Behalte alle wichtigen Code-Änderungen, Entscheidungen und Aufgaben. "
            "Antworte NUR mit der Zusammenfassung, kein Intro, keine Überschriften.\n\n"
            f"{inhalt}"
        )
        try:
            zusammenfassung = self._c._streaming.einmaliger_aufruf(
                source, model, zusammen_prompt, temperature)
        except Exception:
            zusammenfassung = (
                f"[Zusammenfassung von {len(alte)} Nachrichten – Details nicht verfügbar]")

        self._c._compact_zusammenfassung = zusammenfassung
        self._c._chat_verlauf = neue
        self._c._chat_verlauf.insert(0, {
            "role": "user",
            "content": f"[KONTEXT-ZUSAMMENFASSUNG früherer Nachrichten]:\n{zusammenfassung}"
        })
        self._c._chat_verlauf.insert(1, {
            "role": "assistant",
            "content": "Verstanden, ich berücksichtige diesen Kontext."
        })
        self._c._ki_compact_signal.emit(len(alte))
