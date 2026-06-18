# -*- coding: utf-8 -*-
"""
bibliothek.py
──────────────
Makro-Bibliothek für den FreeCAD-Editor.

Speichert getestete FreeCAD-Makros mit Metadaten (Beschreibung, Tags,
Datum, KI-generiert ja/nein) in einer JSON-Datei.

Gespeichert unter: ~/.config/FreeCAD/FreeCADAI/bibliothek.json

Jeder Eintrag hat:
  name         – Anzeigename
  code         – vollständiger Python-Code
  beschreibung – kurze Beschreibung was das Makro macht
  tags         – Liste von Stichwörtern z.B. ["Box", "Boolean", "PartDesign"]
  ki_generiert – True wenn von KI erstellt
  datum        – ISO-Datum wann gespeichert
  ausführungen – wie oft erfolgreich ausgeführt

Die KI bekommt bei jedem Aufruf eine kompakte Übersicht aller Einträge
(ohne Code) damit sie weiß was bereits existiert und darauf aufbauen kann.
"""

from __future__ import annotations

import json
import os
from datetime import datetime


# ── Speicherort ───────────────────────────────────────────────────────────────

def _get_bibliothek_pfad() -> str:
    """Gibt den Pfad zur bibliothek.json zurück."""
    try:
        import FreeCAD as App
        basis = App.getUserAppDataDir()
    except ImportError:
        basis = os.path.expanduser("~/.config/FreeCAD/FreeCADAI")
    os.makedirs(basis, exist_ok=True)
    return os.path.join(basis, "makro_bibliothek.json")


# ── Laden / Speichern ─────────────────────────────────────────────────────────

def laden() -> list[dict]:
    """Lädt alle Bibliotheks-Einträge."""
    pfad = _get_bibliothek_pfad()
    if not os.path.isfile(pfad):
        return []
    try:
        with open(pfad, encoding="utf-8") as f:
            daten = json.load(f)
        if isinstance(daten, list):
            return daten
    except Exception:
        pass
    return []


def speichern(eintraege: list[dict]) -> bool:
    """Speichert alle Bibliotheks-Einträge."""
    try:
        with open(_get_bibliothek_pfad(), "w", encoding="utf-8") as f:
            json.dump(eintraege, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def eintrag_hinzufuegen(
    name: str,
    code: str,
    beschreibung: str = "",
    tags: list[str] | None = None,
    ki_generiert: bool = False,
) -> bool:
    """Fügt einen neuen Eintrag zur Bibliothek hinzu oder überschreibt ihn."""
    eintraege = laden()

    # Bestehenden Eintrag mit gleichem Namen überschreiben
    eintraege = [e for e in eintraege if e.get("name") != name]

    eintraege.append({
        "name":         name,
        "code":         code,
        "beschreibung": beschreibung,
        "tags":         tags or [],
        "ki_generiert": ki_generiert,
        "datum":        datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ausfuehrungen": 0,
    })

    return speichern(eintraege)


def eintrag_loeschen(name: str) -> bool:
    """Löscht einen Eintrag aus der Bibliothek."""
    eintraege = laden()
    neu = [e for e in eintraege if e.get("name") != name]
    if len(neu) == len(eintraege):
        return False
    return speichern(neu)


def ausfuehrung_zaehlen(name: str):
    """Erhöht den Ausführungs-Zähler eines Eintrags."""
    eintraege = laden()
    for e in eintraege:
        if e.get("name") == name:
            e["ausfuehrungen"] = e.get("ausfuehrungen", 0) + 1
            break
    speichern(eintraege)


def suchen(suchbegriff: str) -> list[dict]:
    """Sucht in Name, Beschreibung und Tags."""
    begriff = suchbegriff.lower().strip()
    if not begriff:
        return laden()
    ergebnis = []
    for e in laden():
        if (
            begriff in e.get("name", "").lower()
            or begriff in e.get("beschreibung", "").lower()
            or any(begriff in t.lower() for t in e.get("tags", []))
        ):
            ergebnis.append(e)
    return ergebnis


def ki_kontext() -> str:
    """Gibt eine kompakte Übersicht für den KI-System-Prompt zurück.

    Nur Namen, Beschreibungen und Tags — kein Code.
    Die KI weiß dadurch was bereits existiert und kann darauf aufbauen.
    """
    eintraege = laden()
    if not eintraege:
        return ""

    zeilen = ["## Makro-Bibliothek (bereits getestete Makros)"]
    zeilen.append(
        "Wenn der Nutzer etwas ähnliches braucht, baue auf diesen Makros auf "
        "statt von null zu beginnen:\n"
    )
    for e in eintraege:
        ki_tag = " 🤖" if e.get("ki_generiert") else ""
        tags   = ", ".join(e.get("tags", []))
        zeilen.append(
            f"- **{e['name']}**{ki_tag}: {e.get('beschreibung', '(keine Beschreibung)')}"
            + (f"  [{tags}]" if tags else "")
        )
    return "\n".join(zeilen)
