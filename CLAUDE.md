# Projektregeln für Claude

## Projektstruktur

```
FreeCAD_MultiAI_Panel/
│
├── main.py                          Einstiegspunkt, FreeCAD-Seitenleiste
├── InitGui.py                       FreeCAD WorkBench-Integration
│
├── core/                            Infrastruktur (kein UI-Code)
│   ├── theme.py                     Öffentliches Theme-API — re-exportiert alles aus den Sub-Modulen
│   ├── theme_styles.py              ALLE STY_*-Funktionen, ALLE Layout-Konstanten (DOCK_*)
│   ├── theme_farben.py              Semantische Tints, apply_input_bg_*(), Syntax-Highlight
│   ├── farben.py                    Hex-Farbwerte Hell/Dunkel (DUNKEL{}/HELL{} Dicts)
│   ├── schrift.py                   Zentrale Schrift-Steuerung, mono_font(), ui_font(), STUFE_*
│   ├── params.py                    FreeCAD-Einstellungen (App.ParamGet), lade_*/speichere_*
│   ├── qt_compat.py                 PySide2/PySide6-Kompatibilität
│   └── highlighter.py              Syntax-Highlighter
│
├── editor/
│   ├── editor.py                    Haupt-Editor-Klasse (QMainWindow), verbindet alles
│   ├── panel.py                     FreeCAD-Dock-Panel-Wrapper
│   │
│   ├── builders/                    Widget-Aufbau (einmalig beim Start)
│   │   ├── dock_builder.py          KI-Dock, Einstellungs-Dock aufbauen
│   │   ├── central_widget_builder.py  Code-Editor Bereich aufbauen
│   │   └── toolbar_builder.py       Toolbar aufbauen
│   │
│   ├── ki/                          KI-Logik
│   │   ├── ki_controller.py         KI-Anfragen koordinieren
│   │   ├── ki_anfrage.py            Anfrage zusammenbauen, Preset/Modus auswerten
│   │   ├── ki_streaming.py          HTTP-Streaming zu Ollama/OpenAI/Anthropic
│   │   ├── ki_chunk.py              Chunk-Buffer, Flush-Timer
│   │   ├── ki_fehler.py             Fehler-Panel-Logik, Selbstkorrektur-Loop
│   │   ├── ki_modi.py               FC11–FC14 Preset-Erkennung
│   │   ├── ki_sitzung.py            Chat-Verlauf, Sitzungs-Verwaltung
│   │   ├── ki_verlauf.py            Verlauf-Anzeige
│   │   ├── ki_werkzeuge.py          KI-Hilfsfunktionen
│   │   ├── ki_widget_builder.py     KI-Panel-Widgets aufbauen
│   │   ├── nl_generator.py          FC11–FC14 System-Prompts, NL→FreeCAD-Code
│   │   ├── kod_analyse.py           Code analysieren
│   │   ├── kod_korrektor.py         Automatische Code-Korrekturen
│   │   ├── provider_daten.py        Anbieter-Konfiguration (Ollama, OpenAI, Anthropic…)
│   │   ├── verbindungstest.py       KI-Verbindung testen
│   │   ├── assistent_prompt.py      Assistent-Modus Prompts
│   │   ├── dokument_kontext.py      Dokument-Kontext für KI
│   │   └── fc14_tool_calling.py     FC14 Tool-Calling-Modus
│   │
│   ├── subsysteme/                  Logik-Subsysteme des Editors
│   │   ├── editor_barrierefreiheit.py  Farbschema-Umschaltung, on_farbschema()
│   │   ├── editor_code.py           Code ausführen, einfügen
│   │   ├── editor_datei.py          Datei öffnen/speichern
│   │   ├── editor_suche.py          Suchen & Ersetzen
│   │   ├── editor_tabs.py           Tab-Verwaltung
│   │   └── editor_plan.py           Plan-Modus
│   │
│   ├── fehler/
│   │   └── fehler_panel.py          Fehler-Panel, Sandbox, Korrektur-Button
│   │
│   ├── controller/                  Tab-/Feature-Controller
│   │   ├── ki_tools_tab.py
│   │   ├── bibliothek_tab.py
│   │   ├── snippet_controller.py
│   │   ├── snippet_widgets.py
│   │   ├── vorschau_controller.py
│   │   ├── browser_controller.py
│   │   ├── assistent.py
│   │   └── werkzeuge.py
│   │
│   └── widgets/
│       └── editor_widgets.py        Spezial-Widgets (CodeEditor, LinksTextEdit…)
│
├── ui/                              Eigenständige UI-Fenster
│   ├── begruessung.py               Willkommens-Dialog, Anbieter-Auswahl
│   ├── manager.py                   Panel-Manager
│   ├── fehler.py                    Fehler-Übersetzung
│   └── barrierefreiheit.py          Barrierefreiheits-Einstellungen
│
└── data/                            Reine Daten, kein UI
    ├── freecad_ki_presets.py        FC-Preset-Definitionen
    ├── freecad_data.py              FreeCAD API-Referenz-Daten
    ├── freecad_api_hints.py         API-Hinweise für KI
    ├── freecad_snippets.py          Code-Snippets
    ├── anbieter_formate.py          API-Format-Definitionen pro Anbieter
    ├── bibliothek.py                Makro-Bibliothek
    ├── hilfe.py                     Hilfe-System
    └── hilfe_texte.py               Hilfe-Texte
```

### Wo was zu finden ist

| Aufgabe | Datei |
|---|---|
| Neue STY_*-Funktion | `core/theme_styles.py` |
| Neue Schrift-Stufe | `core/schrift.py` |
| Hex-Farbe Hell/Dunkel | `core/farben.py` |
| Einstellung speichern/laden | `core/params.py` |
| FC11–FC14 System-Prompts | `editor/ki/nl_generator.py` |
| KI-Anfrage aufbauen | `editor/ki/ki_anfrage.py` |
| Selbstkorrektur-Loop | `editor/ki/ki_fehler.py` |
| Dock-Widgets | `editor/builders/dock_builder.py` |
| Farbschema-Umschaltung | `editor/subsysteme/editor_barrierefreiheit.py` |
| Begrüßungs-Dialog | `ui/begruessung.py` |

---

## ABSOLUTES VERBOT — Layout, Farben und Schriften

**Keine** Layout-Werte, Farben oder Schriften dürfen direkt in Python-Dateien geschrieben werden.
Das gilt für ALLE Dateien außer `core/theme_styles.py`, `core/theme_farben.py`, `core/farben.py` und `core/schrift.py`.

Verboten in allen anderen Dateien:
- `setStyleSheet("color: ...", "background: ...", "font-size: ...", "border: ...", "padding: ...", "margin: ...")`
- Hardcodierte Hex-Farben wie `"#1a2e1a"` oder `"#ffffff"`
- `setFixedWidth(...)`, `setFixedHeight(...)`, `setMinimumHeight(...)` mit Zahlenwerten
- `setSpacing(...)`, `setContentsMargins(...)` mit Zahlenwerten
- `setFont(QtGui.QFont("Courier New", 10))` oder ähnliche direkte Font-Angaben

Stattdessen immer:
- Neue `STY_*`-Funktion in `core/theme_styles.py` definieren und dort aufrufen
- Schriften: `schrift.mono_font()`, `schrift.ui_font()`, `schrift.ui_font(schrift.STUFE_LG)` etc.
- Abstands-/Größen-Konstanten: als `DOCK_*`-Konstante in `core/theme_styles.py` definieren

## Kein Mixin-Klassen

Keine Mixin-Klassen im Projekt. Methoden gehören direkt in die verwendende Klasse.
