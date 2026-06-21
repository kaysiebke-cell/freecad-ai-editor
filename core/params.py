# -*- coding: utf-8 -*-
import FreeCAD as App
from data.freecad_data import FC_KI_PRESETS

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
            "Analyse this Python code and explain in simple English: "
            "What does the code do? What functions are there? How is it structured? "
            "Explain it so that a beginner can understand it.",

        "Fehler finden & erklären":
            "Search this code for errors, bugs and problems. "
            "Explain each error in simple English and show the corrected code.",

        "Code verbessern":
            "Improve this code completely: error handling, readability, structure. "
            "Comment all important sections in English. Return only the finished code.",

        "Zusammenfassung":
            "Summarize in 3-5 English sentences what this code does. "
            "Then list the most important functions as short bullet points.",

        "Einfach erklären":
            "Explain this code step by step in simple English. "
            "Do not use technical terms without explaining them.",
    },

    "🔧 Code": {
        "Refactoring":
            "Refactor the code to modern Python standards and "
            "improve readability, structure and error handling.",
        "Kommentieren":
            "Comment the entire code thoroughly in English and "
            "explain every important function.",
        "Performance":
            "Optimise the code for better performance and reduce "
            "unnecessary loops or duplicate calculations.",
        "Bug-Hunt":
            "Find all hidden bugs, logic errors and potential "
            "crash causes in the code and fix them completely.",
        "SOLID-Refactoring":
            "Convert the code into a modular class structure "
            "following SOLID principles.",
        "Sicherheit":
            "Check the code for security issues, API risks and "
            "possible crashes and fix them.",
        "Threading":
            "Analyse the entire code and find possible race conditions, "
            "memory issues or threading errors.",
        "Produktionsreife":
            "Professionally revise the complete tool for productive "
            "use in FreeCAD. Improve architecture, stability, "
            "error handling, UI, performance and maintainability.",
    },

    "⚡ FC: Performance": {
        "Performance-Analyse":
            "You are a FreeCAD Python performance expert. "
            "Analyse this FreeCAD code for typical performance bottlenecks and deliver "
            "the optimised code with a # PERF: comment at every changed location.\n\n"
            "Look specifically for: recompute() in loops, missing transactions, "
            "shape ops in loops, repeated getObject(), GUI updates in loops.\n\n"
            "Return ONLY the finished optimised Python code.",
        "Transaktionen prüfen":
            "Check this FreeCAD Python code whether all document changes are correctly "
            "wrapped in openTransaction() / commitTransaction(). "
            "Show the corrected code with # TRANSACTION: comments.",
        "Schleifen optimieren":
            "Analyse all loops in this FreeCAD Python code. "
            "Find everything that is unnecessarily executed on every iteration. "
            "Mark every change with # LOOP: <reason>. Return only the finished code.",
    },

    "🧱 FreeCAD: Erstellen": {
        "Makro erstellen":
            "Write a complete FreeCAD Python macro for the following task. "
            "Import App, Part and FreeCADGui correctly. Add doc.recompute() at the end. "
            "Handle the case where no active document is open. "
            "Comment all important steps in English.",
        "Parametrisches Modell":
            "Convert the script into a parametric FreeCAD model. "
            "All dimensions as named constants at the top of the file. "
            "Use App.ActiveDocument correctly and call recompute() at the end.",
        "PartDesign Script":
            "Create a clean PartDesign script with Body, Sketch geometry "
            "and at least one Pad or Pocket. Use the PartDesign API correctly.",
        "GUI-Dialog hinzufügen":
            "Extend the macro with a PySide6-compatible QDialog "
            "for user input with OK/Cancel, validation and safe value passing.",
    },

    "🔍 FreeCAD: Analysieren": {
        "Fehlersuche":
            "Analyse this FreeCAD macro for typical errors: "
            "missing recompute() calls, missing None-handling for ActiveDocument, "
            "wrong TypeId usage, PySide2/6 incompatibilities, Placement errors. "
            "List each error with line number and correction.",
        "Selektions-Makro":
            "Revise the script so that it operates on the current FreeCAD selection. "
            "Check whether suitable objects are selected and "
            "output clear error messages via QMessageBox.",
        "Mesh-Verarbeitung":
            "Optimise the script for mesh import, analysis and export in FreeCAD. "
            "Check whether the file exists and output mesh statistics.",
    },

    "📦 FreeCAD: Erweitern": {
        "Workbench-Klasse":
            "Refactor the macro into a reusable FreeCAD workbench. "
            "Create __init__.py with InitGui, Command classes with GetResources, "
            "IsActive and Activated, plus correct Gui.addCommand() registration.",
        "STEP/IGES Export":
            "Extend the script with a robust STEP and IGES export. "
            "Check whether the target folder exists and output file size and path.",
        "Batch-Verarbeitung":
            "Convert the script into a batch macro that opens, processes and saves "
            "all .FCStd files in a directory one by one. "
            "Show a progress bar and log errors per file.",
        "Backup-Erweiterung":
            "Extend the tool with an automatic backup function "
            "before every code replacement.",
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


# ── Modell-Parameter-Persistenz ────────────────────────────────────────────

import json as _json

_MODELL_PARAMS_KEY = "ModellParamsV1"
_MODELL_PARAMS_STANDARD = {
    "temp": 0.2, "top_p": 0.9, "top_k": 40, "max_tokens": 4096, "num_ctx": 8192
}

def lade_alle_modell_params() -> dict:
    """Gibt das gespeicherte Params-Dict aller Modelle zurück."""
    raw = App.ParamGet(PREF_KEY).GetString(_MODELL_PARAMS_KEY, "{}")
    try:
        return _json.loads(raw)
    except Exception:
        return {}

def lade_modell_params(modell: str) -> dict:
    """Gibt die gespeicherten Parameter für ein konkretes Modell zurück."""
    alle = lade_alle_modell_params()
    gespeichert = alle.get(modell, {})
    result = dict(_MODELL_PARAMS_STANDARD)
    result.update(gespeichert)
    return result

def speichere_modell_params(modell: str, params: dict) -> None:
    """Speichert Parameter für ein konkretes Modell."""
    if not modell:
        return
    alle = lade_alle_modell_params()
    alle[modell] = params
    App.ParamGet(PREF_KEY).SetString(_MODELL_PARAMS_KEY, _json.dumps(alle))


# ── System-Prompt-Zusatz ───────────────────────────────────────────────────

def lade_system_prompt_extra() -> str:
    return App.ParamGet(PREF_KEY).GetString("SystemPromptExtra", "")

def speichere_system_prompt_extra(text: str) -> None:
    App.ParamGet(PREF_KEY).SetString("SystemPromptExtra", text)


SYSTEM_PROMPT_VORLAGEN: dict[str, str] = {
    "── Vorlage wählen ──": "",

    "🧱 FreeCAD Part-Script": (
        "You are a FreeCAD Python scripting expert. "
        "Reply ONLY with complete, runnable Python code. No prose, no explanation, no Markdown fences. "
        "German comments inside the code with # are allowed.\n\n"
        "## Mandatory rules\n"
        "1. Always start with: import FreeCAD as App; import Part\n"
        "2. Get or create document: doc = App.ActiveDocument or App.newDocument('Modell')\n"
        "3. For geometry use Part.makeBox / Part.makeCylinder / Part.makeSphere etc. — "
        "these return Shape objects, NOT Feature objects.\n"
        "4. Boolean operations on shapes: result = shape_a.cut(shape_b) "
        "or shape_a.fuse(shape_b) — never use doc.addObject('Part::Cut').\n"
        "5. To show the result: obj = doc.addObject('Part::Feature', 'Name'); obj.Shape = result\n"
        "6. For positioning use App.Vector and Part.makeCylinder(r, h, App.Vector(x, y, z)).\n"
        "7. Always end with: doc.recompute()\n"
        "8. Wrap everything in try/except and show errors with "
        "from PySide2.QtWidgets import QMessageBox; QMessageBox.critical(None, 'Fehler', str(e))"
    ),

    "🤖 FreeCAD-KI (FC14 JSON-Tools)": (
        "You are a FreeCAD assistant. Output ONLY tool calls as JSON objects — "
        "no text, no explanation, no numbering.\n\n"
        "## Rules\n"
        "1) Create every object BEFORE referencing it in fuse() or cut().\n"
        "2) Use x, y, z parameters for positioning — never use translate.\n"
        "3) For holes: cylinder() first (with correct x, y, z), then cut().\n"
        "4) For L/T/U profiles: box() for each leg (with correct z offset), then fuse().\n"
        "5) Boolean operations can crash on coplanar faces — add a tiny offset (0.01 mm).\n"
        "6) Always call doc.recompute() after changes.\n"
        "7) PartDesign features must be inside a Body."
    ),

    "🐍 Python-Experte (Standard)": (
        "You are a Python expert for FreeCAD macros. "
        "Reply only with Python code, no Markdown fences. "
        "Explanations always in German."
    ),

    "🔍 Code-Analyse (Deutsch)": (
        "You are a senior Python code reviewer specializing in FreeCAD macros. "
        "Analyse the provided code thoroughly: find bugs, logic errors, performance issues, "
        "and security problems. "
        "Reply in German. Structure your answer: "
        "1) Zusammenfassung, 2) Gefundene Probleme (mit Zeilennummer), 3) Verbesserter Code."
    ),

    "📐 Parametrisches Modell": (
        "You are a FreeCAD parametric modelling expert. "
        "All dimensions must be named constants at the top of the script. "
        "Use App.ActiveDocument correctly. Call doc.recompute() at the end. "
        "Add short German comments at every important step. "
        "Reply ONLY with complete, runnable Python code."
    ),

    "🛡 Sicherheits-Review": (
        "You are a Python security expert reviewing FreeCAD macro code. "
        "Check for: unsafe eval/exec usage, file path injection, unvalidated user input, "
        "dangerous shell calls, and API misuse. "
        "Reply in German. List every finding with severity (KRITISCH / MITTEL / GERING) "
        "and provide the fixed code."
    ),
}


# ── API-Key-Auflösung (file:-Präfix) ─────────────────────────────────────

def api_key_resolved(anbieter: str) -> str:
    """Wie lade_api_key, aber löst file:/path-Präfixe auf."""
    raw = lade_api_key(anbieter)
    if raw.startswith("file:"):
        pfad = raw[5:].strip()
        try:
            with open(pfad, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return raw
    return raw


# ── Aufbewahrung ──────────────────────────────────────────────────────────

def lade_max_sitzungen() -> int:
    return App.ParamGet(PREF_KEY).GetInt("MaxSitzungen", 20)

def speichere_max_sitzungen(n: int) -> None:
    App.ParamGet(PREF_KEY).SetInt("MaxSitzungen", max(1, int(n)))


# ── KI-Modus (Anfänger / Experte) ────────────────────────────────────────

def lade_ki_modus() -> str:
    return App.ParamGet(PREF_KEY).GetString("KIModus", "anfaenger")

def speichere_ki_modus(modus: str) -> None:
    App.ParamGet(PREF_KEY).SetString("KIModus", modus)


# ── Auto-Einfügen nach KI-Antwort ────────────────────────────────────────

def lade_auto_einfuegen() -> bool:
    return App.ParamGet(PREF_KEY).GetBool("AutoEinfuegen", False)

def speichere_auto_einfuegen(v: bool) -> None:
    App.ParamGet(PREF_KEY).SetBool("AutoEinfuegen", bool(v))


# ── Thinking-Modus für Anthropic ─────────────────────────────────────────

def lade_thinking_modus() -> str:
    return App.ParamGet(PREF_KEY).GetString("ThinkingModus", "aus")

def speichere_thinking_modus(s: str) -> None:
    App.ParamGet(PREF_KEY).SetString("ThinkingModus", s)
