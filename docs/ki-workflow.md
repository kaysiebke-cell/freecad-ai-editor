[← Zurück: Panels im Detail](panels.md) | [Zur README](../README.md) | Weiter: [Makro aus Beschreibung →](makro-generator.md)

# KI-Workflow & Presets

## Standard-Workflow (Code ändern)
```
1. Block im Editor markieren
2. 📥 Laden  →  Block erscheint im KI-Eingabefeld
3. Preset wählen  (z.B. „Fehler finden & erklären")
4. 🤖 Fragen  →  KI-Antwort erscheint live
5. 🔍 Markieren  →  Block im Editor wird markiert
6. ✅ Ersetzen  →  Backup wird erstellt, Code wird ersetzt
```

## Schnell-Analyse (ohne Markierung)
```
🔎 Auto-Analyse  →  Gesamter Code wird sofort erklärt
```

## Code nach Block einfügen
```
Block markieren → 📥 Laden → 🤖 Fragen → ➕ Einfügen
→  KI-Antwort wird NACH dem Block angehängt (kein Überschreiben)
```

## Plan-Modus (Code vor dem Einfügen prüfen)
```
🔍 Plan  aktivieren (Button im Aktionen-Panel)
→ 🤖 Fragen
→ ✅ Ersetzen  →  Dialog öffnet sich mit dem neuen Code zur Prüfung
   → ✅ Ausführen  →  Code wird ersetzt
   → ❌ Abbrechen →  nichts wird verändert, kein Backup
```
Ideal für kritische Stellen — kein versehentliches Überschreiben von wichtigem Code.

## Sitzung speichern & wiederherstellen
```
💾  →  Datei-Dialog  →  .json speichern
        (Chat-Verlauf + KI-Antwort + Anbieter + Modell)

📂  →  .json öffnen  →  alles wird wiederhergestellt
```
Beim nächsten FreeCAD-Start einfach die `.json`-Datei laden und nahtlos weiterarbeiten.

## Chat-Verlauf nutzen
Der Chat-Verlauf bleibt zwischen Fragen erhalten. Folgefragen bauen auf vorherigen Antworten auf.
Ab 5 000 Zeichen wird der älteste Teil automatisch komprimiert (Zusammenfassung).

---

# KI-Presets

Über 40 vordefinierte Aufgabenstellungen in 7 Kategorien:

## ★ Schnell
- Was macht dieser Code?
- Fehler finden & erklären
- Code verbessern
- Zusammenfassung
- Einfach erklären

## 🔧 Code
- Refactoring · Kommentieren · Performance-Optimierung · Bug-Hunt
- SOLID-Refactoring · Sicherheits-Review · Threading · Produktionsreife

## ⚡ FreeCAD: Performance
- Performance-Analyse · Transaktionen prüfen · Schleifen optimieren

## 🧱 FreeCAD: Erstellen
- Makro erstellen · Parametrisches Modell · PartDesign-Script
- **FC11** – Makro aus Beschreibung (Natural Language → Part-Code)
- **FC12** – PartDesign aus Beschreibung (Natural Language → Body/Sketch/Pad)
- **FC13** – Schrittweise aufbauen (Modell Schritt für Schritt erweitern)
- GUI-Dialog hinzufügen

→ Details zu FC11/FC12/FC13: [Makro aus Beschreibung](makro-generator.md)

## 🔍 FreeCAD: Analysieren
- Fehlersuche · Selektions-Makro · Mesh-Verarbeitung

## 📦 FreeCAD: Erweitern
- Workbench-Klasse · STEP/IGES Export · Batch-Verarbeitung · Backup-Erweiterung

## ✍ Dokumentation
- Docstrings generieren · Inline-Kommentare · README-Abschnitt

---

[← Zurück: Panels im Detail](panels.md) | [Zur README](../README.md) | Weiter: [Makro aus Beschreibung →](makro-generator.md)
