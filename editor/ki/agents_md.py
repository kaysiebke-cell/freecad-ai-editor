# -*- coding: utf-8 -*-
"""
agents_md.py
─────────────
AGENTS.md Loader — nach dem Vorbild von ghbalf/freecad-ai.

Sucht eine AGENTS.md (oder FREECAD_AI.md) Datei in:
  1. Verzeichnis des aktiven FreeCAD-Dokuments
  2. Elternverzeichnisse (bis 3 Ebenen hoch)
  3. ~/.config/FreeCAD/FreeCADAI/AGENTS.md  (globale Anweisungen)

Unterstützt:
  - Include-Direktiven:  <!-- include: andere_datei.md -->
  - Variablen:           {{document_name}}, {{object_count}}, {{active_body}}

So funktioniert das "Dazulernen":
  Du legst eine AGENTS.md neben dein .FCStd-Dokument.
  Darin schreibst du projektspezifische Regeln z.B.:
    "Alle Maße in diesem Projekt sind in mm."
    "Das Projekt ist ein Roboterarm mit 6 Gelenken."
    "Verwende immer PartDesign, niemals Part::Box direkt."
  Die KI liest diese Datei bei JEDEM Aufruf automatisch mit.
"""

import os
import re

INSTRUCTION_FILENAMES = ["AGENTS.md", "FREECAD_AI.md"]
INCLUDE_RE  = re.compile(r"<!--\s*include:\s*(.+?)\s*-->")
VARIABLE_RE = re.compile(r"\{\{(\w+)\}\}")
MAX_PARENT_LEVELS = 3
MAX_INCLUDE_DEPTH = 5

# Globaler Konfig-Pfad
CONFIG_DIR = os.path.expanduser("~/.config/FreeCAD/FreeCADAI")


def load_agents_md() -> str:
    """Lädt AGENTS.md von der besten verfügbaren Position.

    Gibt den verarbeiteten Inhalt zurück (Includes aufgelöst,
    Variablen ersetzt), oder leeren String wenn nicht gefunden.
    """
    content = ""

    # 1. Dokument-Verzeichnis und Eltern
    doc_dir = _get_document_directory()
    if doc_dir:
        content = _search_directory_chain(doc_dir)

    # 2. Fallback: globales Konfig-Verzeichnis
    if not content:
        content = _load_from_directory(CONFIG_DIR)

    if not content:
        return ""

    # Includes auflösen
    base_dir = _find_base_dir(doc_dir)
    content = _resolve_includes(content, base_dir, depth=0)

    # Variablen ersetzen
    content = _substitute_variables(content)

    return content


def get_agents_md_path() -> str:
    """Gibt den Pfad der gefundenen AGENTS.md zurück, oder leeren String."""
    doc_dir = _get_document_directory()
    if doc_dir:
        current = doc_dir
        for _ in range(MAX_PARENT_LEVELS + 1):
            for filename in INSTRUCTION_FILENAMES:
                p = os.path.join(current, filename)
                if os.path.isfile(p):
                    return p
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

    for filename in INSTRUCTION_FILENAMES:
        p = os.path.join(CONFIG_DIR, filename)
        if os.path.isfile(p):
            return p

    return ""


def create_agents_md_template(pfad: str) -> bool:
    """Erstellt eine AGENTS.md-Vorlage am angegebenen Pfad."""
    vorlage = """\
# Projektspezifische KI-Anweisungen

## Projekt-Beschreibung
<!-- Beschreibe hier dein Projekt in 1-3 Sätzen -->
Dieses Projekt ist ...

## Maßeinheiten und Konventionen
- Alle Maße in mm
- Verwende PartDesign für parametrische Teile

## Häufig verwendete Objekte
<!-- Liste hier Objekte die du oft brauchst -->
- ...

## Besondere Regeln für dieses Projekt
<!-- z.B. "Bohrungen immer mit 0.2mm Aufmaß" -->
- ...

## Variablen (werden automatisch ersetzt)
- Aktuelles Dokument: {{document_name}}
- Objekt-Anzahl: {{object_count}}
- Aktiver Body: {{active_body}}
"""
    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(vorlage)
        return True
    except Exception:
        return False


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _get_document_directory() -> str:
    try:
        import FreeCAD as App
        doc = App.ActiveDocument
        if doc and doc.FileName:
            return os.path.dirname(doc.FileName)
    except ImportError:
        pass
    return ""


def _search_directory_chain(start_dir: str) -> str:
    current = start_dir
    for _ in range(MAX_PARENT_LEVELS + 1):
        content = _load_from_directory(current)
        if content:
            return content
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return ""


def _load_from_directory(directory: str) -> str:
    if not directory or not os.path.isdir(directory):
        return ""
    for filename in INSTRUCTION_FILENAMES:
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return f.read()
            except (OSError, UnicodeDecodeError):
                continue
    return ""


def _find_base_dir(doc_dir: str) -> str:
    if doc_dir:
        current = doc_dir
        for _ in range(MAX_PARENT_LEVELS + 1):
            for filename in INSTRUCTION_FILENAMES:
                if os.path.isfile(os.path.join(current, filename)):
                    return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
    for filename in INSTRUCTION_FILENAMES:
        if os.path.isfile(os.path.join(CONFIG_DIR, filename)):
            return CONFIG_DIR
    return ""


def _resolve_includes(content: str, base_dir: str, depth: int) -> str:
    if depth >= MAX_INCLUDE_DEPTH or not base_dir:
        return content

    def replace_include(match):
        include_path = match.group(1).strip()
        full_path = os.path.join(base_dir, include_path)
        if os.path.isfile(full_path):
            try:
                with open(full_path, encoding="utf-8") as f:
                    included = f.read()
                return _resolve_includes(
                    included, os.path.dirname(full_path), depth + 1)
            except (OSError, UnicodeDecodeError):
                return f"<!-- include fehlgeschlagen: {include_path} -->"
        return f"<!-- include nicht gefunden: {include_path} -->"

    return INCLUDE_RE.sub(replace_include, content)


def _substitute_variables(content: str) -> str:
    variables = _get_variables()

    def replace_var(match):
        return variables.get(match.group(1), match.group(0))

    return VARIABLE_RE.sub(replace_var, content)


def _get_variables() -> dict:
    variables = {
        "document_name": "",
        "document_path": "",
        "object_count":  "0",
        "active_body":   "",
    }
    try:
        import FreeCAD as App
        doc = App.ActiveDocument
        if doc is None:
            docs = App.listDocuments()
            if docs:
                doc = App.getDocument(list(docs.keys())[0])
        if doc:
            variables["document_name"] = doc.Name
            variables["document_path"] = doc.FileName or "(nicht gespeichert)"
            variables["object_count"]  = str(len(doc.Objects))
            for obj in doc.Objects:
                if getattr(obj, "TypeId", "") == "PartDesign::Body":
                    if getattr(obj, "IsActive", False):
                        variables["active_body"] = obj.Label
                        break
    except ImportError:
        pass
    return variables
