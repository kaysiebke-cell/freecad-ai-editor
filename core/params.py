# -*- coding: utf-8 -*-
import FreeCAD as App
from freecad_data import FC_KI_PRESETS

DOCK_NAME = "EigeneMakroLeiste"
PREF_KEY  = "User parameter:BaseApp/Preferences/Macros"

def lade_pfad():
    return App.ParamGet(PREF_KEY).GetString(
        "EigenerMakroOrdner", App.getUserMacroDir(True)
    )

def speichere_pfad(pfad):
    App.ParamGet(PREF_KEY).SetString("EigenerMakroOrdner", pfad)

def lade_kontext() -> str:
    return App.ParamGet(PREF_KEY).GetString("ProjektKontext", "")

def speichere_kontext(text: str):
    App.ParamGet(PREF_KEY).SetString("ProjektKontext", text)

_KEY_NAMES = {
    "anthropic":   "ApiKeyAnthropic",
    "openai":      "ApiKeyOpenAI",
    "github":      "ApiKeyGitHub",
    "deepseek":    "ApiKeyDeepSeek",
    "gemini":      "ApiKeyGemini",
    "groq":        "ApiKeyGroq",
    "mistral":     "ApiKeyMistral",
    "together":    "ApiKeyTogether",
    "huggingface": "ApiKeyHuggingFace",
    "xai":         "ApiKeyXAI",
    "fireworks":   "ApiKeyFireworks",
    "openrouter":  "ApiKeyOpenRouter",
    "moonshot":    "ApiKeyMoonshot",
    "qwen":        "ApiKeyQwen",
    "cohere":      "ApiKeyCohere",
    "sambanova":   "ApiKeySambaNova",
    "minimax":     "ApiKeyMiniMax",
    "llama":       "ApiKeyLlama",
}

def lade_api_key(anbieter: str) -> str:
    return App.ParamGet(PREF_KEY).GetString(_KEY_NAMES.get(anbieter, ""), "")

def speichere_api_key(anbieter: str, schluessel: str):
    App.ParamGet(PREF_KEY).SetString(_KEY_NAMES.get(anbieter, ""), schluessel)

# ── Preset-Struktur: Kategorien mit Einträgen ──────────────────────────────
# Format: { "Kategorie": { "Name": "Prompt", ... }, ... }
# Schnell-Presets (★) sind eine eigene Kategorie ganz oben.

KI_PRESET_KATEGORIEN: dict[str, dict[str, str]] = {

    "★ Schnell": {
        "Was macht dieser Code?":
            "Analysiere diesen Python-Code und erkläre auf Deutsch in einfachen Worten: "
            "Was macht der Code? Welche Funktionen gibt es? Wie ist er aufgebaut? "
            "Erkläre es so, dass auch ein Anfänger es versteht.",

        "Fehler finden & erklären":
            "Suche in diesem Code nach Fehlern, Bugs und Problemen. "
            "Erkläre jeden Fehler auf Deutsch in einfachen Worten und zeige den korrigierten Code.",

        "Code verbessern":
            "Verbessere diesen Code vollständig: Fehlerbehandlung, Lesbarkeit, Struktur. "
            "Kommentiere alle wichtigen Stellen auf Deutsch. Gib nur den fertigen Code zurück.",

        "Zusammenfassung":
            "Fasse in 3-5 deutschen Sätzen zusammen was dieser Code macht. "
            "Dann liste die wichtigsten Funktionen als kurze Stichpunkte auf.",

        "Einfach erklären":
            "Erkläre diesen Code Schritt für Schritt auf Deutsch in einfacher Sprache. "
            "Verwende keine Fachbegriffe ohne sie zu erklären.",
    },

    "🔧 Code": {
        "Refactoring":
            "Refaktoriere den Code nach modernen Python-Standards und "
            "verbessere Lesbarkeit, Struktur und Fehlerbehandlung.",
        "Kommentieren":
            "Kommentiere den gesamten Code ausführlich auf Deutsch und "
            "erkläre jede wichtige Funktion.",
        "Performance":
            "Optimiere den Code für bessere Performance und reduziere "
            "unnötige Schleifen oder doppelte Berechnungen.",
        "Bug-Hunt":
            "Finde alle versteckten Bugs, Logikfehler und potenziellen "
            "Absturzursachen im Code und behebe sie vollständig.",
        "SOLID-Refactoring":
            "Wandle den Code in eine modulare Klassenstruktur "
            "nach SOLID-Prinzipien um.",
        "Sicherheit":
            "Prüfe den Code auf Sicherheitsprobleme, API-Risiken und "
            "mögliche Abstürze und behebe diese.",
        "Threading":
            "Analysiere den gesamten Code und finde mögliche Race Conditions, "
            "Speicherprobleme oder Threading-Fehler.",
        "Produktionsreife":
            "Überarbeite das komplette Tool professionell für produktiven "
            "Einsatz in FreeCAD. Verbessere Architektur, Stabilität, "
            "Fehlerbehandlung, UI, Performance und Wartbarkeit.",
    },

    "⚡ FC: Performance": {
        "Performance-Analyse":
            "Du bist ein FreeCAD-Python-Performance-Experte. "
            "Analysiere diesen FreeCAD-Code auf typische Performance-Bremsen und liefere "
            "den optimierten Code mit einem # PERF: Kommentar an jeder geänderten Stelle.\n\n"
            "Suche gezielt nach: recompute() in Schleifen, fehlende Transaktionen, "
            "Shape-Ops in Schleifen, wiederholtes getObject(), GUI-Updates in Schleifen.\n\n"
            "Gib NUR den fertigen optimierten Python-Code zurück.",
        "Transaktionen prüfen":
            "Prüfe diesen FreeCAD-Python-Code ob alle Dokumentänderungen korrekt in "
            "openTransaction() / commitTransaction() eingebettet sind. "
            "Zeige den korrigierten Code mit # TRANSAKTION: Kommentaren.",
        "Schleifen optimieren":
            "Analysiere alle Schleifen in diesem FreeCAD-Python-Code. "
            "Finde alles was unnötigerweise bei jedem Durchlauf ausgeführt wird. "
            "Markiere jede Änderung mit # SCHLEIFE: <Grund>. Gib nur den fertigen Code zurück.",
    },

    "🧱 FreeCAD: Erstellen": {
        "Makro erstellen":
            "Schreibe ein vollständiges FreeCAD-Python-Makro für folgende Aufgabe. "
            "Importiere App, Part und FreeCADGui korrekt. Füge am Ende doc.recompute() ein. "
            "Behandle den Fall, dass kein aktives Dokument geöffnet ist. "
            "Kommentiere alle wichtigen Schritte auf Deutsch.",
        "Parametrisches Modell":
            "Wandle das Skript in ein parametrisches FreeCAD-Modell um. "
            "Alle Maße als benannte Konstanten am Anfang der Datei. "
            "Nutze App.ActiveDocument korrekt und rufe am Ende recompute() auf.",
        "PartDesign Script":
            "Erstelle ein sauberes PartDesign-Script mit Body, Sketch-Geometrie "
            "und mindestens einem Pad oder Pocket. Nutze die PartDesign-API korrekt.",
        "GUI-Dialog hinzufügen":
            "Erweitere das Makro um einen PySide6-kompatiblen QDialog "
            "für Benutzereingaben mit OK/Abbrechen, Validierung und sicherer Wertübergabe.",
    },

    "🔍 FreeCAD: Analysieren": {
        "Fehlersuche":
            "Analysiere dieses FreeCAD-Makro auf typische Fehler: "
            "fehlende recompute()-Aufrufe, fehlendes None-Handling für ActiveDocument, "
            "falsche TypeId-Nutzung, PySide2/6-Inkompatibilitäten, Placement-Fehler. "
            "Liste jeden Fehler mit Zeilennummer und Korrektur.",
        "Selektions-Makro":
            "Überarbeite das Skript so, dass es auf der aktuellen FreeCAD-Selektion "
            "operiert. Prüfe ob geeignete Objekte selektiert sind, "
            "gib klare deutsche Fehlermeldungen per QMessageBox aus.",
        "Mesh-Verarbeitung":
            "Optimiere das Skript für Mesh-Import, -Analyse und -Export in FreeCAD. "
            "Prüfe ob die Datei existiert und gib Mesh-Statistiken aus.",
    },

    "📦 FreeCAD: Erweitern": {
        "Workbench-Klasse":
            "Refaktoriere das Makro in eine wiederverwendbare FreeCAD-Workbench. "
            "Erstelle __init__.py mit InitGui, Command-Klassen mit GetResources, "
            "IsActive und Activated, sowie korrekter Gui.addCommand()-Registrierung.",
        "STEP/IGES Export":
            "Erweitere das Skript um einen robusten STEP- und IGES-Export. "
            "Prüfe ob der Zielordner existiert und gib Dateigröße und Pfad aus.",
        "Batch-Verarbeitung":
            "Wandle das Skript in ein Batch-Makro um, das alle .FCStd-Dateien "
            "in einem Verzeichnis nacheinander öffnet, verarbeitet und speichert. "
            "Zeige einen Fortschrittsbalken und protokolliere Fehler je Datei.",
        "Backup-Erweiterung":
            "Erweitere das Tool um eine automatische Backup-Funktion "
            "vor jedem Ersetzen von Code.",
    },
}

# FC_KI_PRESETS aus freecad_data in passende Kategorie einsortieren
# (für Rückwärts-Kompatibilität mit bestehendem Code)
for _k, _v in FC_KI_PRESETS.items():
    if not _v or _k.startswith("──"):
        continue
    _kat = "🧱 FreeCAD: Erstellen"
    if "FC1" in _k or "FC2" in _k or "FC3" in _k or "FC11" in _k or "FC12" in _k or "FC13" in _k:
        _kat = "🧱 FreeCAD: Erstellen"
    elif "FC4" in _k or "FC6" in _k or "FC7" in _k:
        _kat = "🔍 FreeCAD: Analysieren"
    elif "FC8" in _k or "FC9" in _k or "FC10" in _k:
        _kat = "📦 FreeCAD: Erweitern"
    if _k not in KI_PRESET_KATEGORIEN.get(_kat, {}):
        KI_PRESET_KATEGORIEN.setdefault(_kat, {})[_k] = _v

# Flache KI_PRESETS dict für Rückwärts-Kompatibilität aufbauen
KI_PRESETS: dict[str, str] = {"── Preset wählen ──": ""}
for _kat, _eintraege in KI_PRESET_KATEGORIEN.items():
    KI_PRESETS[f"── {_kat} ──"] = ""
    KI_PRESETS.update(_eintraege)


def speichere_quelle(name: str):
    """Speichert den aktuell gewählten KI-Anbieter."""
    App.ParamGet(PREF_KEY).SetString("AktuelleKIQuelle", name)

def lade_quelle() -> str:
    """Gibt den zuletzt gewählten KI-Anbieter zurück."""
    return App.ParamGet(PREF_KEY).GetString("AktuelleKIQuelle", "Ollama (Lokal)")

def speichere_modell(name: str):
    """Speichert das aktuell gewählte KI-Modell."""
    if name:
        App.ParamGet(PREF_KEY).SetString("AktuellesKIModell", name)

def lade_modell() -> str:
    """Gibt das zuletzt gewählte KI-Modell zurück."""
    return App.ParamGet(PREF_KEY).GetString("AktuellesKIModell", "")

def ist_erststart() -> bool:
    return not App.ParamGet(PREF_KEY).GetBool("ErstStartErledigt", False)

def erststart_erledigt():
    App.ParamGet(PREF_KEY).SetBool("ErstStartErledigt", True)

def fenster_schwebend() -> bool:
    """True = Panel schwebend, False = angedockt (Standard)."""
    return App.ParamGet(PREF_KEY).GetBool("PanelSchwebend", False)

def set_fenster_schwebend(schwebend: bool) -> None:
    App.ParamGet(PREF_KEY).SetBool("PanelSchwebend", schwebend)

def farbschema_dunkel() -> bool:
    """True = Dunkelmod, False = Hellmod."""
    return App.ParamGet(PREF_KEY).GetBool("FarbschemaDunkel", True)

def set_farbschema_dunkel(dunkel: bool) -> None:
    App.ParamGet(PREF_KEY).SetBool("FarbschemaDunkel", dunkel)
