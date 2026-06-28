# -*- coding: utf-8 -*-
"""
hilfe_texte.py  –  Hilfetexte für den KI-Makro-Editor
"""

HILFE_ABSCHNITTE: list[tuple[str, str]] = [

    ("🚀 Schnellstart – 5 Schritte", """\
1. Makro-Manager öffnen → Makro anklicken → öffnet im Editor.
2. Code im Editor markieren (oder ☰ Alles im Aktionen-Panel).
3. 📥 Laden  – markierten Block ins KI-Eingabefeld laden.
4. Preset oben wählen  (z. B. „Fehler finden & erklären").
5. 🤖 Fragen  →  🔍 Markieren  →  ✅ Ersetzen.

Neu mit natürlicher Sprache arbeiten?
→ 🤝 Assistent-Panel → „🔤 Fachsprache-Modus" AN
→ Beschreibung eingeben → Fachsprache kommt raus
→ Fachsprache in FC11 einfügen → Code generieren"""),

    ("🏗️ Layout – Übersicht", """\
Der Editor besteht aus 11 frei anordenbaren Panels (Docks).

TOOLBAR OBEN  –  alle Panels ein-/ausschalten:
  ⚙  Einst.      KI-Quelle, Modell, Preset, Temperatur, API-Schlüssel
  🤖 KI           Eingabefeld, KI-Antwort, Projekt-Kontext, Suche/Ersetzen
  🎛 Akt.         Alle Aktions-Buttons (Laden, Fragen, Ersetzen, Datei …)
  📦 Snip         Code-Snippets nach Kategorie (lokal + Online-GitHub)
  💡 API          FreeCAD API-Kurzreferenz
  📂 Dat.         Datei-Browser (frei skalierbar)
  🛠 Tools        FreeCAD-Dokumentkontext, Direkt-Werkzeuge, Protokoll
  📚 Bib.         Makro-Bibliothek
  🔧 Werkz.       Code-Baum, Navigation, Edit-Funktionen, Bereinigung
  ⚠  Fehler       Fehler-Übersetzer + KI-Selbstkorrektur
  ♿ Hilfe+Zugang  Assistent (🤝) + Barrierefreiheits-Einstellungen

MITTE  –  Editor (immer sichtbar)
  Mehrere Dateien gleichzeitig als Tabs.

Panels können:
  • Frei verschoben werden (Titelleiste ziehen)
  • Zu Tabs zusammengefasst werden (übereinander ablegen)
  • Als schwebendes Fenster losgelöst werden (Doppelklick Titelleiste)
  • Geschlossen und per Toolbar wieder geöffnet werden

Panel-Layout (Breiten + Positionen) wird beim Schließen
gespeichert und beim nächsten Start wiederhergestellt.
Belegter Platz: Panel wechselt automatisch auf die Gegenseite."""),

    ("🤖 KI-Workflow im Detail", """\
Standard-Workflow (Code ändern):
  1. Block im Editor markieren
  2. 📥 Laden   (Aktionen-Panel → Code ins KI-Eingabefeld)
  3. Preset wählen  (z. B. „Fehler finden")
  4. 🤖 Fragen
  5. 🔍 Markieren
  6. ✅ Ersetzen  (Backup wird automatisch erstellt)

Plan-Modus (Code vor dem Einfügen prüfen):
  🔍 Plan  aktivieren  →  🤖 Fragen  →  ✅ Ersetzen
  → Dialog zeigt neuen Code zur Bestätigung
  → ✅ Ausführen  oder  ❌ Abbrechen

Einfügen nach Fundstelle:
  ➕ Einfügen  –  KI-Antwort wird NACH dem markierten
  Block angehängt, kein Überschreiben

Auto-Einfügen:
  ⚙ Einstellungen → AUTO-EINFÜGEN ✓ aktivieren
  → KI-Antwort wird nach Stream-Ende automatisch eingefügt
  → deaktivieren wenn du erst prüfen möchtest

Schnell-Analyse (ohne Markierung):
  🔎 Auto-Analyse (Aktionen-Panel) → ganzen Code erklären

Chat-Verlauf:
  Bleibt zwischen Fragen erhalten (Folgefragen möglich).
  Ab 5.000 Zeichen wird der älteste Teil automatisch
  komprimiert (Zusammenfassung bleibt erhalten).
  🧹 Verlauf zurücksetzen – leert Verlauf und Anzeige.

Sitzung speichern & laden:
  💾  →  Chat-Verlauf + KI-Antwort + Anbieter als .json
  📂  →  Gespeicherte Sitzung wiederherstellen

System-Prompt-Vorlagen:
  ⚙ Einstellungen → SYSTEM-PROMPT-ZUSATZ → 📋-Button
  → Vorlage wählen → optional anpassen
  Beginnt mit „You are" → ersetzt Basis-Prompt vollständig
  Sonst → wird als Zusatz angehängt

Suche/Ersetzen im KI-Panel:
  Strg+F  oder Leiste unten im KI-Panel:
  Suche-Feld → Enter = nächster Treffer
  Ersetzen-Feld → ✍ oder Alle"""),

    ("⚙ Einstellungen-Panel", """\
Panel „⚙ Einst." öffnen (Toolbar).
Das Panel ist scrollbar — alle Abschnitte erreichbar.

KI-QUELLE
  Dropdown mit allen Anbietern (19+):
    Ollama (Lokal)  – kostenlos, läuft auf deinem PC
    Anthropic (Claude) · OpenAI · Mistral · Groq u.v.m.
  🔄 Modelle neu laden  – frische Liste vom Anbieter
  🔌 Verbindungstest    – prüft ob Ollama erreichbar
    oder API-Key hinterlegt ist; Ergebnis als Label

MODELL-PARAMETER
  Temperatur  0.0–2.0
    0.0–0.3 → präzise (empfohlen für Code)
    0.5–0.8 → kreativ (gut für Dokumentation)
  Top-P · Top-K · Max-Token · Kontext (num_ctx)
  → alle Werte werden pro Modell gespeichert
    und beim Wechsel automatisch geladen

MODUS
  🟢 Anfänger  – ausführliche Erklärungen auf Deutsch
  🔵 Experte   – knappe, technische Antworten
  → wird beim nächsten Start automatisch wiederhergestellt

FARBSCHEMA
  🌙 Dunkel / ☀ Hell
  → schaltet alle Farben sofort um, Auswahl wird gespeichert

API-SCHLÜSSEL
  Anbieter wählen → Schlüssel einfügen → Tab drücken
  → wird automatisch gespeichert (FreeCAD-Einstellungen)
  Alternativ: file:/pfad/zur/schluessel-datei
  → Key wird zur Laufzeit aus der Datei gelesen

SYSTEM-PROMPT-ZUSATZ
  Freies Textfeld für eigene Anweisungen an die KI.
  📋-Button öffnet Vorlagen-Menü:
    🧱 FreeCAD Part-Script
    🤖 FreeCAD-KI FC14 JSON-Tools
    🐍 Python-Experte
    🔍 Code-Analyse auf Deutsch
    📐 Parametrisches Modell
    🛡 Sicherheits-Review
  Beginnt der Text mit „You are" → ersetzt Basis-Prompt
  Sonst → wird als Zusatz angehängt

AUFBEWAHRUNG
  Max. Sitzungen – Anzahl gespeicherter Chat-Sitzungen

AUTO-EINFÜGEN
  Wenn aktiv: KI-Antwort wird nach Stream-Ende
  automatisch eingefügt (kein manueller ➕-Klick nötig)
  → deaktivieren wenn du erst prüfen möchtest

THINKING (nur Anthropic)
  Aus (Standard) – normaler Modus
  An  – Extended Thinking, 8.000 Budget-Tokens
  → temperature und top_p werden automatisch weggelassen
  → nur wirksam bei Anthropic-Modellen"""),

    ("🗣️ FC11, FC12 & FC13 – Makro aus Beschreibung", """\
Natürlichsprache direkt in FreeCAD-Code umwandeln.

── FC11 · Makro aus Beschreibung (Part-WB) ──────────
  1. Preset „FC11 · Makro aus Beschreibung" wählen
  2. Ins KI-Eingabefeld tippen:
     „Eine Halterung für ein 20mm Rohr"
  3. 🤖 Fragen
  4. Code prüfen → ✅ Ersetzen
  Funktioniert mit allen Backends inkl. Ollama.
  💡 Empfohlen mit Ollama: qwen2.5-coder:7b
     ollama pull qwen2.5-coder:7b

  Tipp für bessere Ollama-Ergebnisse:
  Erst 🤝 Assistent-Panel → „🔤 Fachsprache-Modus" AN
  → natürliche Beschreibung eingeben
  → strukturierte Fachsprache (Part::Box usw.) kommt raus
  → diese Fachsprache dann in FC11 einfügen
  Das ist zuverlässiger als direktes Freideutsch.

── FC12 · PartDesign aus Beschreibung ───────────────
  Erzeugt parametrisches PartDesign-Makro:
    Body → Sketch → Constraints → Pad/Pocket
  ⚠ Empfohlen: Claude (Anthropic) oder GPT-4o
  ⚠ Ollama gesperrt (zu komplex für lokale Modelle)

── FC13 · Schrittweise aufbauen ─────────────────────
  Baut ein Makro Schritt für Schritt auf:
  Jede Anfrage hängt einen neuen Block an den
  vorhandenen Editor-Code an.
  → Ideal für komplexere Modelle in mehreren Runden
  ⚠ Ollama gesperrt — lokale 7B/8B-Modelle können
    den vorhandenen Kontext nicht zuverlässig
    weiterführen (falsche Variablen, doppelte Imports)
  Empfohlen: Claude · GPT-4o · Groq · Llama API (70B)

AGENTS.md – Projektanweisungen:
  Eine Datei „AGENTS.md" neben deiner geöffneten
  Datei (oder im Home-Verzeichnis) wird automatisch
  erkannt und dem FC11-Prompt angehängt.
  Beispiel ~/AGENTS.md:
    Alle Maße in mm. Standardmaterial: Aluminium.

Tipp: Im Anfänger-Modus erklärt die KI jeden Schritt."""),

    ("📦 Snippets", """\
Panel „📦 Snippets" öffnen (Toolbar):

LOKAL (Offline)
  Kategorie aus der ComboBox wählen:
    Dokument · Part · Sketcher · Mesh · Draft · PartDesign
  Snippet anklicken → Vorschau erscheint
  📋 Kopieren  – in Zwischenablage
  ↪ In Editor  – an Cursor-Position einfügen
  Doppelklick  – ebenfalls einfügen

EIGENE SNIPPETS
  Code im Editor markieren
  → „💾 Markierten Code als Snippet speichern"
  → Namen vergeben → erscheint unter ⭐ Eigene
  → wird dauerhaft in FreeCAD-Einstellungen gespeichert

ONLINE (GitHub)
  Lädt echte FreeCAD-Makros aus dem offiziellen
  FreeCAD-GitHub-Repo
  Vorschau wird asynchron geladen (kein UI-Freeze)
  Preview-Cache (max. 50 Einträge) für schnelle
  Wiederanzeige

SCHNELLZUGRIFF IM KI-EINGABEFELD
  / tippen → Popup öffnet sich automatisch
  Weitertippen filtert die Liste live
  Enter oder Klick → Snippet ins Eingabefeld laden"""),

    ("💡 API-Hints", """\
Panel „💡 API" öffnen (Toolbar):

Offline-Kurzreferenz aller wichtigen FreeCAD-Befehle:
  App · Part · Sketcher · Mesh · Draft
  Placement · Selection · GUI / View

Suche:
  Mehrere Wörter gleichzeitig möglich:
    „part shape"  oder  „mesh vector"
  → alle Treffer die beide Begriffe enthalten

Klick auf Signatur → Beschreibung erscheint darunter
📋 Signatur kopieren → direkt in Editor oder
  KI-Eingabefeld einfügen"""),

    ("📂 Datei-Browser", """\
Panel „📂 Dateien" öffnen (Toolbar):

Das Panel ist frei skalierbar (Rand ziehen).

Navigation:
  ^    – Einen Ordner nach oben
  Hom  – Home-Verzeichnis
  Makr – Aktueller Makro-Ordner
  Pfad-Feld + GO – Direkt zu einem Pfad springen

Filter:
  Nur .py / Nur .FCMacro / Alle Dateien

Aktionen per Doppelklick:
  .py / .FCMacro → Im Editor öffnen
  andere Dateien → Pfad ins KI-Eingabefeld kopieren

Lesezeichen:
  ☆-Button → aktuellen Ordner merken
  gespeicherte Ordner erscheinen als Schnellzugriff"""),

    ("🛠 Tools-Panel", """\
Panel „🛠 Tools" öffnen (Toolbar).
Enthält drei aufklappbare Bereiche:

── FREECAD-DOKUMENTKONTEXT ──────────────────────────
  Zeigt alle Objekte im aktiven FreeCAD-Dokument
  (Name, TypeId, Placement).
  Wird bei jedem KI-Aufruf automatisch als
  Hintergrundinfo mitgeschickt — die KI „sieht"
  was gerade in FreeCAD offen ist.

── DIREKT-WERKZEUGE ─────────────────────────────────
  Vordefinierte, sichere FreeCAD-Operationen —
  kein Code nötig:

  Grundkörper erstellen
    Typ: Box · Zylinder · Kugel · Kegel · Torus
    Parameter: Maße + Position eingeben
  Boolean-Operation
    Typ: Cut · Fuse · Common
    Basis-Objekt + Werkzeug-Objekt wählen
  Platzierung setzen
    Objekt-Name, X/Y/Z, Drehachse, Drehwinkel
  Objekte auflisten
    Zeigt alle Objekte + TypeId
  Makro ausführen
    Freier Python-Code als Fallback

  Jede Operation läuft in einer FreeCAD-Undo-
  Transaktion → sicher rückgängig zu machen.
  Ergebnis-Buttons: ▶ Ausführen · 📥 In Editor
                    · ➕ Anhängen

── PROTOKOLL ────────────────────────────────────────
  Alle Ausführungen mit Zeitstempel, ✅/❌-Status
  und Ausgabe.
  🗑 Leeren-Button löscht den Verlauf."""),

    ("📚 Bibliothek-Panel", """\
Panel „📚 Bib." öffnen (Toolbar):

Persönliche Makro-Bibliothek — Makros speichern,
suchen und per Doppelklick laden.

Makro zur Bibliothek hinzufügen:
  → Aktuellen Editor-Inhalt speichern:
    Name + optionale Beschreibung eingeben → Speichern
  → Oder: Datei aus dem Datei-Browser ziehen

Suche:
  Suchfeld oben → filtert Titel und Beschreibung live

Makro laden:
  Doppelklick → öffnet Makro im Editor
  📋 Kopieren → Inhalt in Zwischenablage

Makro löschen:
  Eintrag markieren → 🗑 Löschen

Bibliothek wird dauerhaft in FreeCAD-Einstellungen
gespeichert und beim nächsten Start wiederhergestellt."""),

    ("⚠ Fehler-Übersetzer & KI-Korrektur", """\
Panel „⚠ Fehler" öffnen (Toolbar):

── FEHLER-ÜBERSETZER ────────────────────────────────
  Englische Fehlermeldung / Traceback einfügen
  → 🔍 Übersetzen  (oder Strg+Enter)
  → Deutsche Erklärung + Lösungsvorschlag erscheint

  Vollständige Tracebacks einfügen —
  Fehlertyp wird automatisch erkannt:
    AttributeError · TypeError · NameError
    ImportError · No active document
    Shape-Fehler · Constraint-Fehler u.v.m.

── KI-KORREKTUR ─────────────────────────────────────
  🔧 KI korrigieren
  → Fehler + aktueller Code werden an die KI geschickt
  → Korrigierter Code erscheint in der Sandbox
  → max. 3 Versuche automatisch

── VORSCHAU-FEHLER (Vorschau-Tab) ───────────────────
  Tritt beim Vorschau-Test ein Laufzeitfehler auf,
  erscheinen zwei Buttons direkt im Vorschau-Tab:
    ⚠ Fehler erklären  – öffnet Fehler-Panel mit
      Fehlertext + Übersetzung vorausgefüllt
    🔧 KI korrigieren  – schickt Fehler + Code
      direkt an die KI-Selbstkorrektur
  Panels bleiben dabei im gewohnten Layout."""),

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
  Zeile anspringen – Zeilennummer eingeben → Enter
  Lesezeichen:
    ＋ setzen · ↑↓ navigieren · 🗑 löschen

EDIT & CHECK
  → Einrücken / Ausrücken (Auswahl, 4 Spaces)
  # Ein/Aus   – Kommentar-Zeichen setzen/entfernen
  ⧉ Duplizieren – Auswahl oder Zeile duplizieren
  ✂ Löschen   – Auswahl oder Zeile löschen
  ⬆ / ⬇ Verschieben – Zeile(n) nach oben/unten
  ABC / abc / Abc – Groß-/Kleinschreibung umwandeln
  ↺ Statistiken – Zeilen, Kommentare, def, class,
    import, Zeichen anzeigen
  ▶ Syntax prüfen – Python-Syntax prüfen
    → Fehler mit Zeilennummer

BEREINIGUNG
  ␣ Trailing Spaces  – Leerzeichen am Zeilenende
  ⬜ Max. 2 Leerzeilen – mehr als 2 aufeinander-
    folgende Leerzeilen kürzen
  ¶ Schluss-Leerzeilen – Leerzeilen am Dateiende
  BOM entfernen – Byte-Order-Mark aus Datei entfernen"""),

    ("🛡️ Backup & Sicherheit", """\
Backup wird automatisch erstellt:
  → vor jedem „✅ Ersetzen"
  → landet in __backups__/ neben der Originaldatei
  → max. 3 Backups je Datei (älteste werden gelöscht)

Dateistruktur:
  mein_skript.py
  __backups__/
    mein_skript.py.20260615_201500.bak
    mein_skript.py.20260615_202100.bak
    mein_skript.py.20260615_203000.bak

↩ Backup  (Aktionen-Panel → DATEI)
  Lädt das neueste .bak-Backup in den Editor.

↺ Neu laden  (Aktionen-Panel → DATEI)
  Verwirft alle ungespeicherten Änderungen
  und lädt die gespeicherte Datei neu.

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
  Groq                →  gsk_…

Schlüssel aus Datei laden:
  file:/pfad/zur/schluessel-datei eingeben
  → Key wird zur Laufzeit aus der Datei gelesen
  → nützlich wenn der Key regelmäßig rotiert wird

OpenRouter:
  Schlüssel aus Umgebungsvariable:
    OPENROUTER_API_KEY=sk-or-…
  Im Terminal vor FreeCAD setzen.

Schlüssel bleiben zwischen FreeCAD-Sitzungen erhalten."""),

    ("⌨️ Tastenkürzel", """\
IM EDITOR
  Strg + S        Speichern
  Strg + A        Alles auswählen
  Strg + Z        Rückgängig
  Strg + Y        Wiederherstellen
  Strg + F        Suche/Ersetzen-Leiste ein-/ausblenden
  Tab             Autovervollständigung bestätigen
  Escape          Autovervollständigung schließen

PANELS (Tastaturmodus, im ♿ Zugang aktivieren)
  Alt + 1         ⚙ Einstellungen
  Alt + 2         🤖 KI-Panel
  Alt + 3         🎛 Aktionen
  Alt + 4         📦 Snippets
  Alt + 5         💡 API-Hints
  Alt + 6         📂 Datei-Browser
  Alt + 7         🛠 Tools
  Alt + 8         📚 Bibliothek
  Alt + 9         🔧 Werkzeuge
  Alt + 0         ⚠ Fehler

IM FEHLER-PANEL
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

🟢 pyspellchecker  (Rechtschreibprüfung im Helfer)
  pip install pyspellchecker
  (reines Python — funktioniert auch im Flatpak)

Alle auf einmal:
  pip install requests jedi autopep8 pyspellchecker

FreeCAD als Flatpak — Pakete richtig installieren:
  flatpak run --command=python3 org.freecad.FreeCAD \\
    -m pip install requests jedi autopep8 pyspellchecker
  (normales pip landet im falschen Python!)

Nach Installation FreeCAD neu starten."""),

    ("🤝 Assistent-Panel", """\
Panel „♿ Hilfe+Zugang" öffnen → Tab „🤝 Assist.":

── NORMALER HILFE-MODUS ─────────────────────────────
Fragen über den Editor auf Deutsch stellen:
  „wie übersetze ich einen Fehler?"
  „wie richte ich Ollama ein?"
  „wie benutze ich den Plan-Modus?"
→ KI antwortet in nummerierten Schritten auf Deutsch
→ Genannte Panels/Buttons leuchten automatisch auf
  (2,2 s Abstand, geschlossene Panels öffnen sich)

Hinweise:
  Funktioniert mit dem aktuell eingestellten Anbieter
  Für Ollama: kompakter Prompt
  Für Cloud (Claude, GPT): ausführlicherer Prompt
  🗑 Verlauf löschen – leert die Chat-Anzeige

── 🔤 FACHSPRACHE-MODUS ─────────────────────────────
Schalter oben aktivieren:
  „🔤 Fachsprache-Modus (Natürliche Sprache →
   FreeCAD-Fachsprache)"

Eingabe (freies Deutsch):
  „Kugel 30mm Radius. Zylinder 10mm Radius 60mm
   Höhe von unten durch die Kugel schneiden."

Ausgabe (strukturierte Fachsprache):
  Part::Sphere Radius=30 mm, Mittelpunkt Ursprung.
  Part::Cylinder Radius=10 mm, Height=60 mm,
    Placement.Base=App.Vector(0, 0, -30).
  Part::Cut: Base=kugel, Tool=zylinder.

→ Diese Fachsprache in FC11 einfügen → 🤖 Fragen
→ Ollama erzeugt daraus deutlich zuverlässigeren
  Code als aus freiem Deutsch direkt."""),

    ("🔧 Helfer-Panel & Vision", """\
Panel „♿ Hilfe+Zugang" öffnen → Tab „♿ Helfer":

── LEGASTHENIKER-ASSISTENT ──────────────────────────
Frei schreiben, Rechtschreibung egal:
  „ich brauch kasten mit loch zum anschrauben an wand"

→ Echtzeit-Rechtschreibprüfung während des Tippens
  (rot unterstrichen = unbekanntes Wort)
→ KI korrigiert zu sauberem Deutsch:
  „Eine rechteckige Halterung mit Montageöffnung
   für Wandbefestigung"
→ Diff-Anzeige der Korrekturen:
  rot = entfernt · grün = hinzugefügt
→ Ergebnis direkt in den Editor übernehmen

── BILD + TEXT AN KI SENDEN (VISION) ───────────────
Bild einfügen:
  📎 Bild anhängen  –  Datei-Dialog öffnen
  📋 Aus Zwischenablage  –  oder Strg+V
  Drag & Drop direkt ins Textfeld

Thumbnail-Vorschau mit Bildgröße-Anzeige
✕-Button entfernt das Bild wieder

Warnung erscheint wenn das gewählte Modell
kein Vision unterstützt.
Erlaubte Formate werden automatisch pro Anbieter
geladen (keine Hartkodierung):

  Ollama (Lokal)  llava · bakllava · moondream
                  minicpm-v          JPEG PNG WebP GIF BMP
  Anthropic       claude-3+          JPEG PNG GIF WebP
  OpenAI          gpt-4o · gpt-4-turbo   JPEG PNG GIF WebP
  Gemini          gemini-1.5+        JPEG PNG GIF WebP HEIC+"""),

    ("♿ Barrierefreiheit-Panel", """\
Panel „♿ Hilfe+Zugang" öffnen → Tab „♿ Zugang":

Alle Einstellungen werden gespeichert und beim
nächsten Start automatisch wiederhergestellt.

── 👁 SEHSCHWÄCHE ───────────────────────────────────
  UI-Schriftgröße (Slider 8–24 pt)
    Schriftgröße aller Beschriftungen live anpassen
  Editor-Schriftgröße (Slider 8–24 pt)
    Schriftgröße im Code-Editor anpassen
  Hoher Kontrast
    Alle Elemente: weiß auf schwarz
    (überschreibt das Theme)
  Icons mit Text
    Toolbar-Buttons zeigen Emoji + Kurzname:
    z. B. „⚙ Einst." statt nur „⚙"

── 🖐 MOTORIK ────────────────────────────────────────
  Button-Größe  Normal / Groß / Sehr groß
    Höhe aller Buttons: 26 / 34 / 42 px
  Tastaturmodus
    Alt+1 bis Alt+0 öffnen die Panels
    Shortcut wird im Tooltip angezeigt
  Einfache Ansicht
    Blendet selten genutzte Panels aus der Toolbar aus
    Einst./KI/Akt./Fehler/♿/Assist. bleiben sichtbar

── 💬 EINFACHE SPRACHE ──────────────────────────────
  KI antwortet in einfacher Sprache
    Kurze Sätze, keine Fachbegriffe
  Fachbegriffe automatisch erklären
    KI erklärt verwendete Begriffe direkt danach
  KI-Antworten kürzer halten
    Kompakte Antworten ohne lange Erklärungen

── ⚙ ALLGEMEIN ──────────────────────────────────────
  Tooltips immer sichtbar
    Tooltip erscheint sofort (kein Wartedelay)
  Animationen reduzieren
    Button-Aufleuchten 300 ms statt 1800 ms"""),

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
  Installierte Modelle im Vergleich:
    qwen2.5-coder:7b  – beste Wahl (32K Kontext)
    llama3.1:8b       – größtes Kontext-Fenster (131K)
    codellama         – Code-Fokus (16K Kontext)
    llama3            – Einstieg (8K Kontext)
  Empfohlen für FreeCAD-Code:
    ollama pull qwen2.5-coder:7b
  Hinweis: Ollama nutzt standardmäßig nur 2.048 Token
    Kontext — num_ctx im Panel höher setzen.

⚠ FC12/FC13 NUR MIT STARKEM MODELL
  FC12 (PartDesign) und FC13 (Schrittweise) bei
  Ollama gesperrt — zu komplex / Kontext zu klein.
  Empfohlen: Claude (Anthropic) · GPT-4o · Groq.

⚠ GROSSE DATEIEN
  Bei > 2000 Zeilen nur den betreffenden
  Abschnitt ins KI-Eingabefeld laden.

⚠ FLATPAK (FreeCAD)
  Python-Pakete müssen über das Flatpak-Python
  installiert werden, nicht über das System-pip.
  Sonst sind sie für FreeCAD nicht sichtbar."""),

]
