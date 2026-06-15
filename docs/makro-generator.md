[← Zurück: KI-Workflow & Presets](ki-workflow.md) | [Zur README](../README.md) | Weiter: [Snippets, API-Hints & Werkzeuge →](snippets-und-werkzeuge.md)

# FC11, FC12 & FC13 – Makro aus Beschreibung

Natürlichsprache direkt in FreeCAD-Python-Code umwandeln.

## FC11 – Makro aus Beschreibung (Part-Workbench)
```
Preset „FC11" wählen
→ Ins KI-Eingabefeld tippen: „Eine Halterung für ein 20mm Rohr"
→ 🤖 Fragen
→ Vollständiges FreeCAD-Part-Makro wird generiert
   (Box, Zylinder, Boolean-Operationen, Placement)
→ Code prüfen → ✅ Ersetzen
```
✅ Funktioniert mit **allen Backends** inkl. Ollama.

## FC12 – PartDesign aus Beschreibung
```
Preset „FC12" wählen
→ Beschreibung eingeben
→ Erzeugt parametrisches PartDesign-Makro:
   Body → Sketch → Constraints → Pad/Pocket
```
⚠️ Empfohlen: **Claude (Anthropic)** oder **GPT-4o** — zu komplex für lokale Modelle.
⚠️ Bei Ollama gesperrt.

## FC13 – Schrittweise aufbauen
```
Preset „FC13" wählen
→ Vorhandenen Code im Editor öffnen
→ Ins KI-Eingabefeld tippen: „Füge oben eine Bohrung mit 5mm Radius hinzu"
→ 🤖 Fragen
→ Nur der neue Code-Block wird generiert (kein Überschreiben des bestehenden Codes)
→ ➕ Einfügen  →  Code wird ans Ende angehängt
```
✅ Funktioniert mit **allen Backends** inkl. Ollama.

[← Zurück: KI-Workflow & Presets](ki-workflow.md) | [Zur README](../README.md) | Weiter: [Snippets, API-Hints & Werkzeuge →](snippets-und-werkzeuge.md)
