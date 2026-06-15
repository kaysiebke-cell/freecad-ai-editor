# -*- coding: utf-8 -*-
"""
skills.py
──────────
Skills-System — nach dem Vorbild von ghbalf/freecad-ai.

Skills sind wiederverwendbare Schritt-für-Schritt-Anleitungen für die KI.
Jeder Skill ist eine SKILL.md-Datei in einem Unterordner von:
  ~/.config/FreeCAD/FreeCADAI/skills/<skill-name>/SKILL.md

Die KI bekommt bei jedem Aufruf eine Liste aller verfügbaren Skills.
Wenn der Nutzer z.B. fragt "Erstelle ein Gehäuse", lädt die KI den
passenden Skill und folgt seinen Anweisungen Schritt für Schritt.

Nutzer können eigene Skills schreiben und im skills/-Ordner ablegen.
Das ist das eigentliche "Dazulernen" — du lehrst die KI neue Fähigkeiten
indem du SKILL.md-Dateien schreibst.
"""

import os
import re
from dataclasses import dataclass, field

SKILLS_DIR = os.path.expanduser("~/.config/FreeCAD/FreeCADAI/skills")


@dataclass
class Skill:
    name:        str
    beschreibung: str = ""
    pfad:        str = ""
    inhalt:      str = ""   # SKILL.md Inhalt
    trigger:     str = ""   # Slash-Befehl z.B. "/gehaeuse"


class SkillsRegistry:
    """Verwaltet alle verfügbaren Skills."""

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._laden()

    def _laden(self):
        if not os.path.isdir(SKILLS_DIR):
            return
        for eintrag in os.listdir(SKILLS_DIR):
            skill_dir  = os.path.join(SKILLS_DIR, eintrag)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isdir(skill_dir) or not os.path.isfile(skill_file):
                continue
            try:
                with open(skill_file, encoding="utf-8") as f:
                    inhalt = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            beschreibung = ""
            trigger      = ""

            # YAML-Frontmatter auslesen
            if inhalt.startswith("---\n"):
                end = inhalt.find("\n---\n", 4)
                if end != -1:
                    for zeile in inhalt[4:end].splitlines():
                        if zeile.startswith("description:"):
                            beschreibung = zeile[12:].strip().strip("\"'")[:100]
                        elif zeile.startswith("trigger:"):
                            trigger = zeile[8:].strip().strip("\"'")

            if not beschreibung:
                for zeile in inhalt.splitlines():
                    zeile = zeile.strip()
                    if zeile and not zeile.startswith("#") and not zeile.startswith("---"):
                        beschreibung = zeile[:100]
                        break

            self._skills[eintrag] = Skill(
                name=eintrag,
                beschreibung=beschreibung,
                pfad=skill_dir,
                inhalt=inhalt,
                trigger=trigger or f"/{eintrag}",
            )

    def get_descriptions(self) -> str:
        """Gibt eine Übersicht aller Skills für den System-Prompt zurück."""
        if not self._skills:
            return ""
        zeilen = []
        for skill in self._skills.values():
            zeilen.append(f"- `{skill.trigger}` — {skill.beschreibung}")
        return "\n".join(zeilen)

    def get_skill(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def alle_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def find_by_trigger(self, text: str) -> Skill | None:
        """Findet einen Skill anhand eines Slash-Befehls im Text."""
        for skill in self._skills.values():
            if skill.trigger and skill.trigger in text:
                return skill
        return None


def get_skill_descriptions() -> str:
    """Schnellzugriff: gibt Skill-Beschreibungen für den System-Prompt zurück."""
    try:
        return SkillsRegistry().get_descriptions()
    except Exception:
        return ""


def create_example_skill():
    """Erstellt einen Beispiel-Skill damit der Nutzer die Struktur sieht."""
    skill_dir = os.path.join(SKILLS_DIR, "beispiel-gehaeuse")
    os.makedirs(skill_dir, exist_ok=True)
    skill_file = os.path.join(skill_dir, "SKILL.md")
    if os.path.isfile(skill_file):
        return skill_file

    inhalt = """\
---
description: Erstellt ein parametrisches Gehäuse mit Deckel und Schraubenlöchern
trigger: /gehaeuse
---

# Skill: Parametrisches Gehäuse

## Aufgabe
Erstelle ein rechteckiges Gehäuse (Unterteil + Deckel) mit PartDesign.

## Parameter
- Länge (L), Breite (B), Höhe (H) — aus der Nutzerbeschreibung entnehmen
- Wandstärke (T) = 2.0 mm (Standard)
- Schraubenlöcher Radius = 1.5 mm an allen 4 Ecken

## Schritte

### 1. Unterteil
1. Body erstellen: `doc.addObject("PartDesign::Body", "Unterteil")`
2. Sketch auf XY-Ebene: Außenrechteck L×B
3. Pad mit Höhe H
4. Innen-Sketch auf Deckfläche: Innenrechteck (L-2T)×(B-2T)
5. Pocket mit Tiefe H-T (lässt Boden stehen)

### 2. Schraubenlöcher
- 4 Kreise Radius 1.5mm an Positionen (T/2, T/2), (L-T/2, T/2) usw.
- Pocket durchgehend (Through All)

### 3. Deckel
- Neuer Body "Deckel"
- Sketch: Außenrechteck L×B
- Pad mit Höhe T (flacher Deckel)

## Ausgabe
Nach dem Code: 3 kurze Sätze was erstellt wurde.
"""
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write(inhalt)
    return skill_file
