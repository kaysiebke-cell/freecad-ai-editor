# -*- coding: utf-8 -*-
"""
hilfe_texte.py  –  Hilfetexte für den KI-Makro-Editor (aktualisiert)
"""

HILFE_ABSCHNITTE: list[tuple[str, str]] = [

    ("🚀 Schnellstart – 5 Schritte", """\
1. Makro-Manager öffnen → Makro anklicken → öffnet im Editor.
2. Code im Editor markieren (oder ☰ Alles im Aktionen-Panel).
3. 📥 Laden  – markierten Block ins KI-Eingabefeld laden.
4. Preset oben wählen  (z. B. „Fehler finden & erklären").
5. 🤖 Fragen  →  🔍 Markieren  →  ✅ Ersetzen."""),

    ("🏗️ Layout – Übersicht", """\
Der Editor besteht aus frei anordenbaren Panels (Docks).

TOOLBAR OBEN  –  alle Panels ein-/ausschalten:
  ⚙ Einst.   KI-Quelle, Modell, Preset, Temperatur, API-Schlüssel
  🤖 KI       Eingabefeld, KI-Antwort, Projekt-Kontext, Suche/Ersetzen
  🎛 Aktionen Alle Aktions-Buttons (Laden, Fragen, Ersetzen, Datei …)
  📦 Snippets Code-Snippets nach Kategorie
  💡 API      FreeCAD API-Kurzreferenz
  📂 Dateien  Datei-Browser (frei skalierbar)
  🛠 Tools    FreeCAD-Dokumentkontext, Werkzeuge, Protokoll
  📚 Bibliothek Makro-Bibliothek
  🔧 Werkzeuge Code-Baum, Navigation, Edit-Funktionen
  ⚠ Fehler   Fehler-Übersetzer
  ❓ Hilfe    Diese Hilfe (immer sichtbar, ganz rechts)

MITTE  –  Editor (immer sichtbar)
  Mehrere Dateien gleichzeitig als Tabs.

Panels können:
  • Frei verschoben werden (Titelleiste ziehen)
  • Zu Tabs zusammengefasst werden (übereinander ablegen)
  • Als schwebendes Fenster losgelöst werden (doppelklick Titelleiste)
  • Geschlossen und per Toolbar wieder geöffnet werden"""),

    ("🤖 KI-Workflow im Detail", """\
Standard-Workflow (Code ändern):
  1. Block im Editor markieren
  2. 📥 Laden   (Aktionen-Panel → Code ins KI-Eingabefeld)
  3. Preset wählen  (z. B. „Fehler finden")
  4. 🤖 Fragen
  5. 🔍 Markieren
  6. ✅ Ersetzen

Plan-Modus (Code vor dem Einfügen prüfen):
  🔍 Plan  aktivieren  →  🤖 Fragen  →  ✅ Ersetzen
  → Dialog zeigt neuen Code zur Bestätigung
  → ✅ Ausführen  oder  ❌ Abbrechen

Sitzung speichern & laden:
  💾  →  Chat-Verlauf + KI-Antwort als .json sichern
  📂  →  Gespeicherte Sitzung wiederherstellen

Schnell-Analyse:
  → 🔎 Analyse drücken (Aktionen-Panel)
  → Ganzen Code sofort erklären lassen ohne Markierung

Einfügen nach Fundstelle:
  → ➕ Einfügen  –  KI-Antwort nach dem markierten Block anhängen

Suche/Ersetzen im Editor (im KI-Panel):
  Strg+F  oder direkt im KI-Panel unten:
  Suche-Feld → Enter = nächster Treffer
  Ersetzen-Feld → ✍ oder Alle"""),

    ("⚙ Einstellungen-Panel", """\
Panel „⚙ Einst." öffnen (Toolbar):

KI-QUELLE
  Ollama (Lokal) – läuft auf deinem PC, kostenlos
  Anthropic (Claude), OpenAI, Mistral, u.v.m.
  → 🔄 Modelle neu laden falls keine erscheinen

MODELL
  Auswahl der verfügbaren Modelle des gewählten Anbieters

PRESET / TEMPERATUR
  Preset = vordefinierte Aufgabenstellung für die KI
  Temperatur 0.0–1.0 steuert Kreativität der Antwort
    0.0–0.3 → präzise / deterministisch (empfohlen für Code)
    0.5–0.8 → kreativ (gut für Kommentare / Doku)

MODUS
  🟢 Anfänger  – KI erklärt ausführlich auf Deutsch
  🔵 Experte   – KI antwortet knapp & technisch

API-SCHLÜSSEL
  Anbieter wählen → Schlüssel einfügen → Tab drücken
  Wird automatisch gespeichert (FreeCAD-Einstellungen)"""),

    ("🗣️ FC11 & FC12 – Makro aus Beschreibung", """\
Natürlichsprache direkt in FreeCAD-Code umwandeln.

── FC11 · Makro aus Beschreibung (Part-WB) ──────────
  1. Preset „FC11" wählen
  2. Ins KI-Eingabefeld tippen:
     „Eine Halterung für ein 20mm Rohr"
  3. 🤖 Fragen
  4. Code prüfen → ✅ Ersetzen
  Funktioniert mit allen Backends inkl. Ollama.

── FC12 · PartDesign aus Beschreibung ───────────────
  Erzeugt parametrisches PartDesign-Makro:
    Body → Sketch → Constraints → Pad/Pocket
  ⚠ Empfohlen: Claude (Anthropic) oder GPT-4o
  ⚠ Ollama gesperrt (zu komplex für lokale Modelle)

Tipp: Im Anfänger-Modus erklärt die KI jeden Schritt."""),

    ("📦 Snippets", """\
Panel „📦 Snippets" öffnen (Toolbar):

• Kategorie aus der ComboBox wählen
  (Dokument · Part · Sketcher · Mesh …)
• Snippet anklicken → Vorschau erscheint
• 📋 Kopieren  – in Zwischenablage
• ↪ In Editor  – an Cursor-Position einfügen
• Doppelklick  – ebenfalls einfügen

Slash-Befehl im KI-Eingabefeld:
  /snippetname  – Snippet per Autovervollständigung laden"""),

    ("💡 API-Hints", """\
Panel „💡 API" öffnen (Toolbar):

• Suchfeld oben filtern:
  z. B. „mesh", „vector", „placement"
• Klick auf Signatur → Beschreibung erscheint
• 📋 Signatur kopieren – direkt verwendbar

Enthält alle wichtigen FreeCAD-API-Aufrufe:
App · Part · Sketcher · Mesh · Draft
Selektion · Placement · GUI / View"""),

    ("📂 Datei-Browser", """\
Panel „📂 Dateien" öffnen (Toolbar):

Das Panel ist frei skalierbar (Rand ziehen).

Navigation:
  ^    – Einen Ordner nach oben
  Hom  – Home-Verzeichnis
  Makr – Aktueller Makro-Ordner
  Pfad-Feld + GO – Direkt zu einem Pfad

Filter: Nur .py / .FCMacro / alle Dateien

Aktionen per Doppelklick:
  .py / .FCMacro → Im Editor öffnen
  andere Dateien → Pfad ins KI-Eingabefeld kopieren

Lesezeichen: ☆-Button → Ordner merken"""),

    ("⚠ Fehler-Übersetzer", """\
Panel „⚠ Fehler" öffnen (Toolbar):

Englische Fehlermeldung / Traceback einfügen
→ Übersetzen
→ Deutsche Erklärung mit Lösungsvorschlag

Tipp: Vollständige Tracebacks einfügen –
der Fehlertyp wird automatisch erkannt.

KI-Korrektur:
→ „🔧 KI korrigieren" schickt den Fehler
  direkt an die KI die den Code automatisch repariert."""),

    ("🔍 Suche & Ersetzen im Editor", """\
Im KI-Panel (🤖 KI) ganz unten:

  Suche-Feld  +  →  → nächster Treffer
  Ersetzen-Feld  +  ✍ → aktuellen Treffer ersetzen
                 +  Alle → alle ersetzen

Strg+F  öffnet dieselbe Leiste direkt.

„🔍 Markieren" (Aktionen-Panel):
  Sucht den Inhalt des KI-Eingabefelds
  auch mehrzeilig im Editor und markiert ihn.
  Die Markierung bleibt für ✅ Ersetzen erhalten."""),

    ("🗂️ Multi-Tab-Editing", """\
Der Editor unterstützt mehrere offene Dateien gleichzeitig.

Datei öffnen:
  • Doppelklick im 📂 Datei-Browser
  • Rechtsklick im Makro-Manager → Im Editor öffnen

Tab-Verwaltung:
  • Tabs sind schließbar  (× rechts im Tab)
  • Tabs sind verschiebbar (Drag & Drop)
  • Geänderte Tabs zeigen „Dateiname *"

Beim Schließen mit ungespeicherten Änderungen:
  → Speichern / Verwerfen / Abbrechen"""),

    ("🔧 Werkzeuge-Panel", """\
Panel „🔧 Werkzeuge" öffnen (Toolbar):

CODE-BAUM
  Alle def / class automatisch aufgelistet
  → Doppelklick springt zur Definition

NAVIGATION
  • Zeile anspringen
  • Lesezeichen setzen / springen

EDIT & CHECK
  • Einrücken / Ausrücken (Auswahl)
  • Kommentar setzen / entfernen
  • Zeilen verschieben (hoch/runter)
  • ✅ Syntax-Prüfung → Fehler mit Zeilennummer"""),

    ("🛡️ Backup & Sicherheit", """\
↺ Neu laden  (Aktionen-Panel → DATEI)
  Verwirft alle ungespeicherten Änderungen.

↩ Backup  (Aktionen-Panel → DATEI)
  Lädt die neueste .bak-Datei in den Editor.
  (max. 3 Backups je Datei)

Backup wird automatisch erstellt:
  → vor jedem „✅ Ersetzen"
  → landet in __backups__/ neben der Originaldatei
  → max. 3 Backups je Datei

Beim Schließen mit ungespeicherten Änderungen:
  → Speichern / Verwerfen / Abbrechen"""),

    ("🔑 API-Schlüssel einrichten", """\
Panel „⚙ Einst." öffnen → Abschnitt API-SCHLÜSSEL:

1. Anbieter wählen (Dropdown)
2. Schlüssel einfügen  (Passwort-Feld)
3. Tab drücken → wird automatisch gespeichert

Gängige Schlüssel-Formate:
  Anthropic (Claude)  →  sk-ant-…
  OpenAI              →  sk-…
  Mistral             →  …

OpenRouter:
  Schlüssel aus Umgebungsvariable:
    OPENROUTER_API_KEY=sk-or-…
  Im Terminal vor FreeCAD setzen.

Schlüssel bleiben zwischen FreeCAD-Sitzungen erhalten."""),

    ("⌨️ Tastenkürzel", """\
Strg + S        Speichern
Strg + A        Alles auswählen
Strg + Z        Rückgängig
Strg + Y        Wiederherstellen
Strg + F        Suche/Ersetzen-Leiste ein-/ausblenden
Tab             Autovervollständigung bestätigen
Escape          Autovervollständigung schließen

Im Fehler-Panel:
  Strg + Return   Sofort übersetzen"""),

    ("📦 Installation – Optionale Pakete", """\
Der Editor startet auch ohne diese Pakete –
einzelne Funktionen sind dann deaktiviert.

🔵 requests  (Pflicht für KI-Anbindung)
  pip install requests

🟡 jedi  (Python-Autovervollständigung)
  pip install jedi
  Prüfen: Tippe im Editor  App.
  → Popup erscheint nach ~300 ms

🟢 autopep8  (automatische PEP-8-Formatierung)
  pip install autopep8
  Button wechselt: „🪄 Einrückung" → „✨ autopep8"

Alle auf einmal:
  pip install requests jedi autopep8

Nach Installation FreeCAD neu starten."""),

    ("🔧 Helfer-Panel & Vision", """\
Das Helfer-Panel hat zwei Funktionen:

── LEGASTHENIKER-ASSISTENT ──────────────────────────
Frei schreiben, Rechtschreibung egal:
  „ich brauch kasten mit loch für wand"
  → KI korrigiert zu sauberem Deutsch

── BILD + TEXT AN KI SENDEN (VISION) ───────────────
Bild einfügen:
  📎 Bild anhängen  –  Datei-Dialog öffnen
  📋 Aus Zwischenablage  –  oder Strg+V
  Drag & Drop direkt ins Textfeld

Warnung erscheint wenn das Modell kein Vision hat.
Erlaubte Formate werden automatisch pro Anbieter
geladen (PNG, JPEG, WebP usw.)

Vision-Modelle bei Ollama:
  llava · bakllava · moondream · minicpm-v"""),

    ("⚠️ Warnungen & Bekannte Einschränkungen", """\
⚠ API-SCHLÜSSEL
  Werden unverschlüsselt in FreeCAD-Einstellungen
  gespeichert. Keine Produktions-Schlüssel verwenden.

⚠ KI-ANTWORTEN PRÜFEN
  Die KI kann fehlerhaften Code erzeugen.
  Immer lesen bevor du ✅ Ersetzen klickst.
  Tipp: 🔍 Plan-Modus aktivieren → Code erst
  bestätigen bevor er eingefügt wird.
  Automatisches Backup (.bak) fängt Fehler auf.

⚠ OLLAMA (LOKAL)
  Ollama muss laufen: http://localhost:11434
  Modell vorher laden:
    ollama pull codellama

⚠ FC12 NUR MIT STARKEM MODELL
  FC12 bei Ollama gesperrt.
  Empfohlen: Claude (Anthropic) oder GPT-4o.

⚠ GROSSE DATEIEN
  Bei > 2000 Zeilen nur den betreffenden
  Abschnitt ins KI-Eingabefeld laden."""),

]
