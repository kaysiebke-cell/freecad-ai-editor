# KI-Makro-Editor für FreeCAD

Ein moderner, KI-gestützter Python-Editor als FreeCAD-Plugin mit frei anordenbaren Panels,
Syntax-Highlighting, 19 unterstützten KI-Anbietern und umfangreichen Werkzeugen zur
FreeCAD-Automatisierung.

---

## Vorschau

![KI-Makro-Editor Demo](assets/demo_begruessung.gif)

> *Weitere Aufnahmen folgen – Tool: [Peek](https://github.com/phw/peek) unter Linux*

---

## Inhaltsverzeichnis

### Kurzübersicht (diese Seite)
- [Features im Überblick](#features-im-überblick)
- [Voraussetzungen & Installation](#voraussetzungen--installation)
- [KI-Anbieter einrichten](#ki-anbieter-einrichten)
- [Tastenkürzel](#tastenkürzel)
- [Projektstruktur](#projektstruktur)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)

### Ausführliche Dokumentation – Kapitel für Kapitel

| # | Kapitel | Inhalt |
|---|---------|--------|
| 1 | [Erststart & Willkommen-Dialog](docs/erststart.md) | KI-Anbieter beim ersten Start einrichten |
| 2 | [Die Benutzeroberfläche](docs/oberflaeche.md) | Layout, Panels, intelligente Panel-Steuerung |
| 3 | [Panels im Detail](docs/panels.md) | Alle 11 Panels ausführlich erklärt |
| 4 | [KI-Workflow & Presets](docs/ki-workflow.md) | Mit der KI arbeiten, 40+ Presets |
| 5 | [FC11, FC12 & FC13 – Makro-Generator](docs/makro-generator.md) | Natürlichsprache → FreeCAD-Code |
| 6 | [Snippets, API-Hints & Werkzeuge](docs/snippets-und-werkzeuge.md) | Hilfsmittel für FreeCAD-Entwicklung |
| 7 | [Makro-Bibliothek](docs/makro-bibliothek.md) | Eigene Makros verwalten & wiederverwenden |
| 8 | [Fehler-Übersetzer & Backup-System](docs/fehler-und-backup.md) | Fehler verstehen, Backups nutzen |
| 9 | [Ollama – Erfahrungsbericht](docs/OLLAMA_ERFAHRUNGEN.md) | Lokale KI: Chancen, Grenzen & Lösungen |

[→ Dokumentation starten: Kapitel 1 – Erststart](docs/erststart.md)

---

## Features im Überblick

### Editor
- Mehrere Dateien gleichzeitig als Tabs mit Drag & Drop
- Python-Syntax-Highlighting (automatisch hell/dunkel-adaptiv)
- Zeilennummern, Einrückungs-Guides, Cursor-Position
- Jedi-basierte Autovervollständigung (optional)
- Suche & Ersetzen mit Strg+F
- Unbegrenzte Undo/Redo-Transaktionen
- Automatische Backups vor jeder KI-Ersetzung (max. 3 je Datei)
- autopep8-Formatierung (optional)

### KI-Integration
- **19 KI-Anbieter** unterstützt (Ollama, Claude, ChatGPT, Gemini, DeepSeek, Groq …)
- **40+ Presets** für alle gängigen Code-Aufgaben
- Streaming-Antworten in Echtzeit (50 ms Chunk-Batching)
- Chat-Verlauf mit Auto-Kompacting ab 5 000 Zeichen
- **Sitzung speichern & laden** – Chat-Verlauf, KI-Antwort und Anbieter-Auswahl als JSON-Datei sichern und wiederherstellen
- **Plan-Modus** – KI-Antwort vor dem Einfügen anzeigen und bestätigen (kein versehentliches Überschreiben)
- Zwei Modi: 🟢 Anfänger (ausführlich, Deutsch) / 🔵 Experte (knapp, technisch)
- Makro aus natürlichsprachlicher Beschreibung generieren (FC11 / FC12 / FC13)
- KI-Tool-Calling für strukturierte FreeCAD-Operationen

### Vision & Bild-Unterstützung (Helfer-Panel)
- **Text + Bild gemeinsam an die KI** senden (Skizze, Foto, Handzeichnung)
- Bilder per Datei-Dialog, Drag & Drop oder Zwischenablage (Strg+V) einfügen
- Automatische Erkennung ob das gewählte Modell Vision unterstützt
- **Anbieter-spezifische Formate** – erlaubte Bildformate und Größen werden automatisch aus einer zentralen Datenbank geladen (kein Hardcoding)
- Unterstützte Vision-Modelle: llava, bakllava, moondream, minicpm-v (Ollama) und alle Vision-Modelle der Cloud-Anbieter

### Benutzeroberfläche
- 11 frei anordnbare Dock-Panels (verschieben, abdocken, zu Tabs zusammenfassen)
- Hell- und Dunkel-Modus vollständig unterstützt – keine hartkodieren Farben
- Alle Panels einzeln per Toolbar ein-/ausschaltbar
- Begrüßungs-Dialog bei Erststart (KI-Anbieter direkt einrichten)
- Gewählter KI-Anbieter wird zwischen FreeCAD-Starts gespeichert

---

## Voraussetzungen & Installation

### Voraussetzungen
- **FreeCAD 0.21** oder neuer
- **Python 3.10+**

### Pflicht-Paket
```bash
pip install requests
```
*Wird für alle KI-Anbindungen benötigt. Ohne `requests` startet der Editor, alle KI-Funktionen sind aber deaktiviert.*

### Optionale Pakete
```bash
pip install jedi            # Python-Autovervollständigung im Editor
pip install autopep8        # automatische PEP-8-Formatierung (Button wechselt zu "✨ autopep8")
pip install pyspellchecker  # Rechtschreibprüfung im Helfer-Panel (reines Python, Flatpak-kompatibel)
```

Alle auf einmal:
```bash
pip install requests jedi autopep8 pyspellchecker
```

> **Flatpak-Nutzer:** Pakete müssen über das eingebettete Python installiert werden:
> ```bash
> flatpak run --command=python3 org.freecad.FreeCAD -m pip install pyspellchecker
> ```

> **FreeCAD AppImage / Flatpak:** Nach `pip install` FreeCAD neu starten.
> Bei AppImages muss `pip` ggf. gegen das eingebettete Python gerichtet werden:
> `/path/to/FreeCAD.AppImage --appimage-extract` → Python aus dem extrahierten Verzeichnis verwenden.

### Plugin installieren

1. Dieses Repository klonen oder als ZIP herunterladen und entpacken
2. Den Ordner umbenennen in `freecad-ai-editor` (ohne Leerzeichen – wichtig!)

#### Linux – AppImage

```bash
mkdir -p ~/.local/share/FreeCAD/v1-1/Mod
ln -s /pfad/zum/freecad-ai-editor ~/.local/share/FreeCAD/v1-1/Mod/freecad-ai-editor
```

#### Linux – Flatpak

```bash
mkdir -p ~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod
ln -s /pfad/zum/freecad-ai-editor ~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod/freecad-ai-editor
```

> **Tipp:** Mit einem Symlink (`ln -s`) bleibt der Ordner am ursprünglichen Speicherort – Änderungen am Code werden sofort wirksam ohne erneutes Kopieren.

> **Flatpak Dateizugriff:** Falls die Workbench im Flatpak nicht lädt, muss FreeCAD Zugriff auf den Home-Ordner erhalten:
> ```bash
> flatpak override --user --filesystem=home org.freecad.FreeCAD
> ```

#### Windows

```
%APPDATA%\FreeCAD\Mod\freecad-ai-editor\
```

#### macOS

```
~/Library/Preferences/FreeCAD/Mod/freecad-ai-editor/
```

> **Wichtig für Linux:** FreeCAD 1.x speichert Benutzerdaten unter `v1-1/` – ältere Anleitungen ohne diesen Unterordner funktionieren nicht.

3. FreeCAD neu starten → die Workbench **„FreeCAD AI Editor"** erscheint im Workbench-Menü

---

## KI-Anbieter einrichten

### Unterstützte Anbieter (19)

| Anbieter | Modelle (Auswahl) | API-Key Format |
|----------|-------------------|----------------|
| **Ollama** (lokal) | codellama, llama3, mistral, … | — (kein Key) |
| **Anthropic (Claude)** | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5 | `sk-ant-…` |
| **OpenAI (ChatGPT)** | gpt-4o, gpt-4o-mini, gpt-4-turbo | `sk-…` |
| **GitHub Copilot** | gpt-4o, gpt-4o-mini, o1-mini | `ghp_…` |
| **DeepSeek** | deepseek-coder, deepseek-chat, deepseek-reasoner | API-Key |
| **Gemini (Google)** | gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash | API-Key |
| **Groq** | llama-3.3-70b, mixtral-8x7b, gemma2-9b | API-Key |
| **Mistral** | mistral-large-latest, codestral-latest | API-Key |
| **Together AI** | llama-3.3-70B, mixtral-8x7B, CodeLlama-34b | API-Key |
| **HuggingFace** | Llama 3.2, Qwen2.5-Coder, Mistral | API-Key |
| **xAI (Grok)** | grok-3, grok-3-mini, grok-2 | API-Key |
| **Fireworks AI** | llama-v3p3-70b, deepseek-coder-v2 | API-Key |
| **Moonshot** | moonshot-v1-8k, v1-32k, v1-128k | API-Key |
| **Qwen (Alibaba)** | qwen-coder-plus, qwen-plus, qwen-max, qwen2.5-coder-32b | API-Key |
| **Cohere** | command-a-03-2025, command-r-plus, command-r | API-Key |
| **SambaNova** | DeepSeek-R1, Meta-Llama-3.3-70B, Qwen2.5-Coder | API-Key |
| **MiniMax** | — | API-Key |
| **Llama API** | — | API-Key |
| **OpenRouter** | (alle unterstützten Modelle) | `sk-or-…` |

### Ollama (lokal, kostenlos)
```bash
# 1. Ollama installieren: https://ollama.ai
# 2. Modell herunterladen
ollama pull codellama
# oder
ollama pull llama3

# 3. Ollama-Dienst starten (läuft auf http://localhost:11434)
ollama serve
```
Im Editor: **⚙ Einstellungen** → Quelle: `Ollama (Lokal)` → kein API-Key nötig → **🔄 Modelle neu laden**

### Anthropic / OpenAI / weitere Cloud-Anbieter
Im Editor: **⚙ Einstellungen** → Anbieter wählen → API-Schlüssel eingeben → **Tab drücken** (wird automatisch in den FreeCAD-Einstellungen gespeichert)

### OpenRouter
```bash
# Umgebungsvariable vor FreeCAD-Start setzen
export OPENROUTER_API_KEY=sk-or-...
```

> ⚠️ **Sicherheitshinweis:** API-Schlüssel werden unverschlüsselt in den FreeCAD-Einstellungen gespeichert. Keine Produktions-Schlüssel verwenden.

---

## Erststart & Willkommen-Dialog

![Willkommen-Dialog](assets/demo_begruessung.gif)

Beim ersten Start erscheint automatisch ein Einrichtungs-Dialog:

**Schritt 1 – KI-Anbieter wählen:**
Klickbare Karten für Ollama, Anthropic, OpenAI, GitHub Copilot oder „Später einrichten".

**Schritt 2 – API-Key eingeben:**
Passwort-Feld mit „Schlüssel anzeigen"-Option (entfällt bei Ollama und „Später").

**Fertig:**
Bestätigung + Tipp zum Projekt-Kontext → Editor öffnet sich direkt.

Der Dialog kann jederzeit übersprungen werden. Alle Einstellungen sind auch im **⚙ Einstellungen-Panel** verfügbar.

---

## Die Benutzeroberfläche

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚙ Einst. │ 🤖 KI │ 🎛 Akt. │ 📦 Snip │ 💡 API │ 📂 Dat. │ … │ ❓ Hilfe │
├──────────────┬──────────────────────────────────────────────────────────┤
│              │                                                          │
│  Dock-Panel  │         Code-Editor (Multi-Tab)                          │
│  (links oder │                                                          │
│   rechts     │                                                          │
│   andockbar) │                                                          │
│              ├──────────────────────────────────────────────────────────┤
│              │  ⚠ Fehler-Panel (unten, einklappbar)                     │
└──────────────┴──────────────────────────────────────────────────────────┘
```

Alle Panels können:
- **Frei verschoben** werden (Titelleiste ziehen)
- **Zu Tabs zusammengefasst** werden (Panel auf Panel ablegen)
- **Als schwebendes Fenster** losgelöst werden (Doppelklick auf Titelleiste)
- Per **Toolbar-Button** ein- und ausgeblendet werden

### Intelligente Panel-Steuerung

Der Editor erkennt automatisch ob ein Panel-Platz bereits belegt ist:

| Situation | Verhalten |
|-----------|-----------|
| Ziel-Seite frei | Panel erscheint auf der bevorzugten Seite (links oder rechts) |
| Ziel-Seite belegt | Panel wechselt automatisch auf die Gegenseite |
| Beide Seiten belegt | Panel wird als Tab an ein vorhandenes Panel angehängt |

**⚠ Fehler-Panel** ist die einzige Konstante — es erscheint immer unten und wechselt nie die Position.

**Panel-Layout wird gespeichert:** Breiten und Positionen aller Panels werden beim Schließen automatisch gesichert und beim nächsten Start wiederhergestellt.

---

## Panels im Detail

### ⚙ Einstellungen-Panel
- **KI-Quelle** wählen (Dropdown mit allen 19 Anbietern)
- **🔄 Modelle neu laden** – frische Modellliste vom Anbieter abrufen
- **Modell** auswählen
- **Preset** wählen (40+ vordefinierte Aufgabenstellungen)
- **Temperatur** 0.0–2.0 (empfohlen: 0.0–0.3 für Code, 0.5–0.8 für Dokumentation)
- **Modus:** 🟢 Anfänger (ausführlich auf Deutsch) / 🔵 Experte (knapp & technisch)
- **API-Schlüssel** pro Anbieter eingeben & automatisch speichern

### 🤖 KI-Panel
- **Eingabefeld** (grün hinterlegt) – Prompt oder zu analysierender Code
  - `/snippetname` tippen → Snippet-Autovervollständigung öffnet sich
- **KI-Antwort** (blau hinterlegt) – Antwort erscheint live gestreamt
- **Projekt-Kontext** – wird bei jedem KI-Aufruf als Hintergrundinfo mitgeschickt
- **Suche/Ersetzen** (Strg+F) – direkt im Panel
- **💾 Sitzung speichern** – Chat-Verlauf + KI-Antwort + Anbieter als `.json` sichern
- **📂 Sitzung laden** – gespeicherte Sitzung wiederherstellen
- **🧹 Verlauf zurücksetzen** – löscht den gesamten Chat-Verlauf und die Anzeige
- Chat-Verlauf mit automatischem Kompacting

### 🎛 Aktionen-Panel
Alle Aktions-Buttons auf einen Blick:

**KI-Aktionen**

| Button | Funktion |
|--------|----------|
| 📥 Laden | Markierten Code aus Editor ins KI-Eingabefeld |
| 🔍 Markieren | KI-Eingabefeld-Inhalt im Editor suchen & markieren |
| 🤖 Fragen | KI abfragen (mit aktuellem Preset) |
| 🔍 Plan | **Plan-Modus** – KI-Antwort vor dem Einfügen anzeigen und bestätigen |
| ✅ Ersetzen | Markierten Block durch KI-Antwort ersetzen |
| ➕ Einfügen | KI-Antwort nach dem markierten Block anhängen |
| 🔎 Auto-Analyse | Gesamten Code sofort erklären lassen |

**Datei-Aktionen**

| Button | Funktion |
|--------|----------|
| 💾 Speichern | Aktuelle Datei speichern |
| 💾✕ Speichern & schließen | Speichern und Tab schließen |
| ↺ Neu laden | Datei neu laden (verwirft ungespeicherte Änderungen) |
| ↩ Backup | Neuestes .bak-Backup in Editor laden |
| 📋 Alles auswählen | Gesamten Code markieren |
| 🗑 Löschen | Editor-Inhalt leeren |
| ✨ autopep8 / 🪄 Einrückung | Code automatisch formatieren |

**Navigation**

| Funktion | Beschreibung |
|----------|-------------|
| Zeile anspringen | Zeilennummer eingeben → Enter |
| Code-Baum | Alle `def` und `class` live als Baum – Doppelklick springt zur Definition |
| Lesezeichen | ＋ setzen · ↑↓ navigieren · 🗑 löschen |

**Edit & Check**

| Button | Funktion |
|--------|----------|
| → Einrücken | Auswahl um 4 Spaces einrücken |
| ← Ausrücken | Auswahl ausrücken |
| # Ein/Aus | Kommentar-Zeichen setzen oder entfernen |
| ⧉ Duplizieren | Auswahl/Zeile duplizieren |
| ✂ Löschen | Auswahl/Zeile löschen |
| ⬆ / ⬇ Verschieben | Zeile(n) nach oben/unten |
| ABC / abc / Abc | Groß-/Kleinschreibung transformieren |
| ↺ Statistiken | Zeilen, Kommentare, def, class, import, Zeichen |
| ▶ Syntax prüfen | Python-Syntax prüfen → Fehlerstelle mit Zeilennummer |

**Bereinigung**

| Button | Funktion |
|--------|----------|
| ␣ Trailing Spaces | Leerzeichen am Zeilenende entfernen |
| ⬜ Max. 2 Leerzeilen | Mehr als 2 aufeinanderfolgende Leerzeilen kürzen |
| ¶ Schluss-Leerzeilen | Leerzeilen am Dateiende entfernen |
| BOM entfernen | Byte-Order-Mark (UTF-8 BOM) aus Datei entfernen |

### 📦 Snippets-Panel

**Lokal (Offline)**
- Kategorien: Dokument · Part · Sketcher · Mesh · Draft · PartDesign
- Snippet anklicken → Vorschau erscheint
- **↪ In Editor** oder **Doppelklick** → an Cursor-Position einfügen
- **📋 Kopieren** → in Zwischenablage

**Eigene Snippets**
- Code im Editor markieren → **💾 Markierten Code als Snippet speichern**
- Namen vergeben → erscheint unter ⭐ Eigene
- Wird dauerhaft in FreeCAD-Einstellungen gespeichert

**Online (GitHub)**
- Lädt echte FreeCAD-Makros direkt aus dem offiziellen FreeCAD-GitHub-Repo
- Vorschau wird asynchron geladen (kein UI-Freeze)
- Preview-Cache (max. 50 Einträge) für schnelle Wiederanzeige

**Schnellzugriff im KI-Eingabefeld**
- `/` tippen → Popup öffnet sich automatisch
- Weitertippen filtert die Liste live
- Enter oder Klick → Snippet wird ins Eingabefeld geladen

### 💡 API-Hints-Panel
Offline-Kurzreferenz aller wichtigen FreeCAD-Python-Befehle:
- **App** · Part · Sketcher · Mesh · Draft · Placement · Selection · GUI/View
- Suchfeld: mehrere Wörter gleichzeitig (z.B. `part shape`, `mesh vector`)
- Befehl anklicken → Beschreibung erscheint darunter
- **📋 Signatur kopieren** → direkt in Editor oder KI-Eingabefeld einfügen

### 📂 Datei-Browser
- Frei skalierbar (Rand des Panels ziehen)
- **Navigation:** `^` Ordner hoch · `Hom` Home-Verzeichnis · `Makr` Makro-Ordner · Pfad-Feld + `GO`
- **Filter:** nur `.py` / nur `.FCMacro` / alle Dateien
- **Doppelklick:** `.py`/`.FCMacro` → im Editor öffnen · andere Dateien → Pfad kopieren
- **Lesezeichen:** ☆-Button → Ordner merken

### 🛠 Tools-Panel

Enthält drei Bereiche als aufklappbare Sektionen:

**📄 FreeCAD-Dokumentkontext**
Aktueller Dokumentzustand (Objekte, Typen, Placement) wird automatisch an jeden KI-Prompt angehängt.
→ Die KI „sieht" was in FreeCAD gerade offen ist.

**🛠 Direkt-Werkzeuge**
Vordefinierte, sichere FreeCAD-Operationen – kein Code nötig:

| Werkzeug | Parameter |
|----------|-----------|
| **Grundkörper erstellen** | Typ (Box/Zylinder/Kugel/Kegel/Torus), Maße, Position |
| **Boolean-Operation** | Typ (Cut/Fuse/Common), Basis-Objekt, Werkzeug-Objekt |
| **Platzierung setzen** | Objekt-Name, X/Y/Z, Drehachse, Drehwinkel |
| **Objekte auflisten** | — (zeigt alle Objekte + TypeId) |
| **Makro ausführen** | Freier Python-Code als Fallback |

Jede Operation läuft in einer FreeCAD-Undo-Transaktion → sicher rückgängig zu machen.
Ergebnis-Buttons: **▶ Ausführen** · **📥 In Editor** · **➕ Anhängen**

**📋 Protokoll**
Alle Ausführungen mit Zeitstempel, ✅/❌-Status und Ausgabe. 🗑 Leeren-Button.

### 📚 Bibliothek-Panel
Eigene Makro-Sammlung dauerhaft speichern und verwalten:

**Speichern**
1. Code im Editor öffnen
2. **💾 In Bibliothek** klicken
3. Dialog: Name, Beschreibung, Tags (kommagetrennt), KI-generiert-Flag
4. Code wird automatisch aus dem Editor übernommen

**Suchen & Filtern**
- Nach Name, Beschreibung oder Tag filtern
- Code-Vorschau direkt in der Liste

**Aktionen pro Eintrag**
| Button | Funktion |
|--------|----------|
| ▶ Ausführen | Direkt in FreeCAD ausführen (Zähler erhöht sich) |
| 📥 In Editor | In aktuellen/neuen Editor-Tab laden |
| 🗑 Löschen | Mit Bestätigung löschen |

**Metadaten je Eintrag:** Name · Beschreibung · Tags · Datum · 🤖 KI-generiert-Flag · Ausführungs-Zähler

### 🔧 Werkzeuge-Panel
- **Code-Baum:** alle `def`/`class` automatisch aufgelistet → Doppelklick springt zur Definition
- **Navigation:** Zeile anspringen · Lesezeichen setzen/navigieren/löschen
- **Edit & Check:** Einrücken, Ausrücken, Kommentieren, Verschieben, Syntax-Prüfung
- **Bereinigung:** Trailing Spaces, Leerzeilen, BOM

### 🔧 Helfer-Panel (Barrierefreiheit & Vision)

Ein eigenständiges Chat-Panel mit zwei Aufgaben:

**1. Legastheniker-Assistent**
Frei geschriebenen deutschen Text (Rechtschreibung egal) in eine saubere FreeCAD-Beschreibung umwandeln:
```
ich brauch einen kasten mit loch zum anschrauben an die wand
→ KI korrigiert → „Eine rechteckige Halterung mit Montageöffnung für Wandbefestigung"
```
- Echtzeit-Rechtschreibprüfung während des Tippens (mit `pyspellchecker`)
- Diff-Anzeige der Korrekturen (rot = entfernt, grün = hinzugefügt)
- Ergebnis direkt in den Editor übernehmen

**2. Text + Bild an die KI senden (Vision)**
- **📎 Bild anhängen** – Datei-Dialog mit anbieter-spezifischen Formaten
- **📋 Aus Zwischenablage** – Strg+V oder Schaltfläche
- **Drag & Drop** – Bilddatei direkt in das Eingabefeld ziehen
- Thumbnail-Vorschau mit Bildgröße-Anzeige und ✕-Button
- Warnung wenn das gewählte Modell kein Vision unterstützt
- Unterstützte Anbieter und Formate werden automatisch aus `data/anbieter_formate.py` geladen

> **Ollama Vision:** Funktioniert nur mit llava, bakllava, moondream, minicpm-v.
> **Cloud-Anbieter:** Claude, GPT-4o, Gemini und weitere unterstützen JPEG, PNG, WebP, GIF.

### ⚠ Fehler-Panel
Zweigeteilt: **Fehler-Tab** (im Dock) + **Fehler-Panel** (unterer Rand, immer sichtbar).

**Fehler-Tab im Dock:**
1. Englische Fehlermeldung / Traceback einfügen
2. **🔍 Übersetzen** oder **Strg+Enter**
3. Deutsche Erklärung + Lösungsvorschlag erscheint

Erkannte Fehlertypen: `AttributeError` · `TypeError` · `NameError` · `ImportError` · `No active document` · Shape-Fehler · Constraint-Fehler

**🔧 KI korrigieren:**
Fehler + aktueller Code werden direkt an die KI gesendet → Korrigierter Code erscheint in der Sandbox (max. 3 Versuche).

---

## KI-Workflow

### Standard-Workflow (Code ändern)
```
1. Block im Editor markieren
2. 📥 Laden  →  Block erscheint im KI-Eingabefeld
3. Preset wählen  (z.B. „Fehler finden & erklären")
4. 🤖 Fragen  →  KI-Antwort erscheint live
5. 🔍 Markieren  →  Block im Editor wird markiert
6. ✅ Ersetzen  →  Backup wird erstellt, Code wird ersetzt
```

### Schnell-Analyse (ohne Markierung)
```
🔎 Auto-Analyse  →  Gesamter Code wird sofort erklärt
```

### Code nach Block einfügen
```
Block markieren → 📥 Laden → 🤖 Fragen → ➕ Einfügen
→  KI-Antwort wird NACH dem Block angehängt (kein Überschreiben)
```

### Plan-Modus (Code vor dem Einfügen prüfen)
```
🔍 Plan  aktivieren (Checkbox im Aktionen-Panel)
→ 🤖 Fragen
→ ✅ Ersetzen  →  Dialog öffnet sich mit dem neuen Code
   → ✅ Ausführen  →  Code wird ersetzt
   → ❌ Abbrechen →  kein Backup, kein Überschreiben
```
Ideal für kritische Stellen — kein versehentliches Überschreiben mehr.

### Sitzung speichern & wiederherstellen
```
💾  →  Datei-Dialog  →  .json speichern
        (Chat-Verlauf + KI-Antwort + Anbieter + Modell)

📂  →  .json öffnen  →  alles wird wiederhergestellt
```
Nächster FreeCAD-Start: Sitzung laden → nahtlos weiterarbeiten.

### Chat-Verlauf nutzen
Der Chat-Verlauf bleibt zwischen Fragen erhalten. Folgefragen bauen auf vorherigen Antworten auf.
Ab 5 000 Zeichen wird der älteste Teil automatisch komprimiert (Zusammenfassung).

---

## KI-Presets

Über 40 vordefinierte Aufgabenstellungen in 7 Kategorien:

### ★ Schnell
- Was macht dieser Code?
- Fehler finden & erklären
- Code verbessern
- Zusammenfassung
- Einfach erklären

### 🔧 Code
- Refactoring · Kommentieren · Performance-Optimierung · Bug-Hunt
- SOLID-Refactoring · Sicherheits-Review · Threading · Produktionsreife

### ⚡ FreeCAD: Performance
- Performance-Analyse · Transaktionen prüfen · Schleifen optimieren

### 🧱 FreeCAD: Erstellen
- Makro erstellen · Parametrisches Modell · PartDesign-Script
- **FC11** – Makro aus Beschreibung (Natural Language → Part-Code)
- **FC12** – PartDesign aus Beschreibung (Natural Language → Body/Sketch/Pad)
- **FC13** – Schrittweise aufbauen (Modell Schritt für Schritt erweitern)
- GUI-Dialog hinzufügen

### 🔍 FreeCAD: Analysieren
- Fehlersuche · Selektions-Makro · Mesh-Verarbeitung

### 📦 FreeCAD: Erweitern
- Workbench-Klasse · STEP/IGES Export · Batch-Verarbeitung · Backup-Erweiterung

### ✍ Dokumentation
- Docstrings generieren · Inline-Kommentare · README-Abschnitt

---

## FC11, FC12 & FC13 – Makro aus Beschreibung

Natürlichsprache direkt in FreeCAD-Python-Code umwandeln.

### FC11 – Makro aus Beschreibung (Part-Workbench)
```
Preset „FC11" wählen
→ Ins KI-Eingabefeld tippen: „Eine Halterung für ein 20mm Rohr"
→ 🤖 Fragen
→ Vollständiges FreeCAD-Part-Makro wird generiert
   (Box, Zylinder, Boolean-Operationen, Placement)
→ Code prüfen → ✅ Ersetzen
```
✅ Funktioniert mit **allen Backends** inkl. Ollama.

### FC12 – PartDesign aus Beschreibung
```
Preset „FC12" wählen
→ Beschreibung eingeben
→ Erzeugt parametrisches PartDesign-Makro:
   Body → Sketch → Constraints → Pad/Pocket
```
⚠️ Empfohlen: **Claude (Anthropic)** oder **GPT-4o** — zu komplex für lokale Modelle.
⚠️ Bei Ollama gesperrt.

### FC13 – Schrittweise aufbauen
```
Preset „FC13" wählen
→ Vorhandenen Code im Editor öffnen
→ Ins KI-Eingabefeld tippen: „Füge oben eine Bohrung mit 5mm Radius hinzu"
→ 🤖 Fragen
→ Nur der neue Code-Block wird generiert (kein Überschreiben des bestehenden Codes)
→ ➕ Einfügen  →  Code wird ans Ende angehängt
```
✅ Funktioniert mit **allen Backends** inkl. Ollama.
Ideal um ein Modell iterativ aufzubauen — Schritt für Schritt ohne neu zu starten.

---

## Snippets & API-Hints

### Snippet-Kategorien
- 📄 **Dokument** – Dokument anlegen/laden/speichern, Objekte abfragen
- 🔷 **Part** – Box, Zylinder, Boolean, Placement, Shape-Operationen
- 📐 **Sketcher** – Sketch erstellen, Constraints, Geometrie
- 🕸 **Mesh** – Mesh importieren/exportieren, konvertieren
- 📏 **Draft** – Linien, Kreise, Bemaßungen
- 🧩 **PartDesign** – Body, Feature-Kette, Pad, Pocket

### API-Hints Bereiche
- `App.*` – Dokument, Objekte, Einstellungen
- `Part.*` – Shapes, Operationen, Geometrie
- `Sketcher.*` – Constraints, Geometrie
- `Mesh.*` – Import/Export, Verarbeitung
- `Draft.*` – 2D-Operationen
- `Placement`, `Vector`, `Rotation`
- `Gui.*`, `FreeCADGui.*` – View, Selection

---

## Werkzeuge-Panel

### Direktoperationen (ohne Code schreiben)

**Grundkörper erstellen**
```
Typ:    Box / Zylinder / Kugel / Kegel / Torus
Maße:   Länge / Breite / Höhe / Radius
Pos.:   X / Y / Z
→ Objekt erscheint direkt in FreeCAD
```

**Boolean-Operation**
```
Typ:        Cut / Fuse / Common
Basis:      Name des Basis-Objekts
Werkzeug:   Name des Werkzeug-Objekts
→ Ergebnis-Objekt wird erstellt
```

**Platzierung setzen**
```
Objekt:     Name des Objekts
Position:   X / Y / Z
Rotation:   Achse (X/Y/Z), Winkel
→ Objekt wird neu positioniert
```

Alle Operationen laufen in einer **FreeCAD-Undo-Transaktion** – vollständig rückgängig machbar.

---

## Makro-Bibliothek

Eigene Makro-Sammlung aufbauen:

```
Makro im Editor öffnen
→ 💾 In Bibliothek  →  Dialog:
   Name (Pflicht)
   Beschreibung
   Tags: Box, Boolean, PartDesign  (kommagetrennt)
   🤖 KI-generiert  (Checkbox)
→ Gespeichert in FreeCAD-Einstellungen (dauerhaft)
```

Jeder Eintrag zeigt: **Name · Datum · Ausführungs-Zähler · KI-Flag · Code-Vorschau**

---

## Fehler-Übersetzer

FreeCAD-Fehlermeldungen auf Deutsch erklären:

```
Fehlermeldung kopieren (z.B. aus der FreeCAD-Konsole):

  AttributeError: 'NoneType' object has no attribute 'Shape'

→ In das Eingabefeld einfügen
→ 🔍 Übersetzen  (oder Strg+Enter)
→ Deutsche Erklärung:
   "Das Objekt existiert nicht oder ist noch nicht vollständig aufgebaut …"
→ Lösungsvorschlag:
   "Prüfe ob doc.getObject('...') nicht None zurückgibt …"
```

Für komplexere Fehler: **🔧 KI korrigieren** sendet Fehler + Code direkt an die KI.

---

## Backup-System

- Vor jedem **✅ Ersetzen** wird automatisch eine `.bak`-Datei erstellt
- Maximal **3 Backups** je Datei (älteste werden automatisch gelöscht)
- **↩ Backup** im Aktionen-Panel lädt das neueste Backup in den Editor
- Beim Schließen mit ungespeicherten Änderungen: Speichern / Verwerfen / Abbrechen

---

## Tastenkürzel

| Kürzel | Aktion |
|--------|--------|
| **Strg+S** | Speichern |
| **Strg+A** | Alles auswählen |
| **Strg+Z** | Rückgängig |
| **Strg+Y** | Wiederholen |
| **Strg+F** | Suche/Ersetzen ein-/ausblenden |
| **Tab** | Autovervollständigung bestätigen |
| **Escape** | Autovervollständigung schließen |
| **Strg+Enter** | Fehler-Übersetzer: sofort übersetzen |

---

## Projektstruktur

```
KI-Makro-Editor/
│
├── main.py              # Einstiegspunkt (FreeCAD-Makro / Seitenleiste)
├── InitGui.py           # FreeCAD-GUI-Integration (Toolbar-Button)
├── Icon.svg             # Plugin-Icon
├── README.md
│
├── core/
│   ├── theme.py         # Farben & Stylesheets (hell/dunkel-adaptiv, keine Hartkodierung)
│   ├── highlighter.py   # Python-Syntax-Highlighter
│   ├── schrift.py       # Schriftgrößen-Konstanten
│   ├── params.py        # Einstellungs-Persistenz (FreeCAD-Parameter)
│   └── qt_compat.py     # PySide6-Kompatibilitäts-Layer
│
├── editor/
│   ├── editor.py        # Hauptfenster (QMainWindow + 11 Dock-Panels + Toolbar, Plan-Modus, Sitzung)
│   ├── freecad_helfer_panel.py  # Helfer-Panel: Legastheniker-Assistent + Vision (Text+Bild)
│   ├── widgets/
│   │   ├── editor_widgets.py   # CodeEditor, LinksTextEdit, LineNumberArea
│   │   └── …
│   ├── controller/
│   │   ├── aktionen_sidebar.py   # Aktionen-Panel (Rechte Werkzeug-Leiste)
│   │   ├── bibliothek_tab.py     # Makro-Bibliothek
│   │   ├── browser_controller.py # Datei-Browser
│   │   ├── hints_controller.py   # API-Hints
│   │   ├── ki_tools_tab.py       # Tools-Panel (Direktoperationen + Protokoll)
│   │   ├── snippet_controller.py # Snippets (lokal + online + Info-Banner)
│   │   ├── suche_controller.py   # Suche & Ersetzen
│   │   ├── vorschau_controller.py
│   │   └── werkzeuge.py          # Werkzeuge-Panel (Code-Baum, Edit, Check)
│   ├── fehler/
│   │   └── fehler_panel.py       # Fehler-Übersetzer + KI-Korrektur
│   └── ki/
│       ├── ki_mixin.py           # KI-Workflow (Laden, Fragen, Ersetzen …)
│       ├── ki_backends.py        # Stream-Backends (19 Anbieter)
│       └── …
│
├── ui/
│   ├── begruessung.py   # Willkommens-Dialog (Erststart, Anbieter einrichten)
│   ├── manager.py       # FreeCAD Makro-Manager
│   └── fehler.py        # Fehler-Anzeige
│
├── data/
│   ├── freecad_data.py      # Snippets (6 Kategorien) + API-Hints
│   ├── nl_generator.py      # System-Prompts für FC11/FC12/FC13 (NL → FreeCAD-Code)
│   ├── anbieter_formate.py  # Bild-/Dateiformat-Datenbank für alle 19 KI-Anbieter
│   ├── hilfe_texte.py       # Eingebaute Hilfetexte (17 Abschnitte)
│   └── hilfe.py             # Hilfe-Panel
│
├── assets/
│   └── …                # Icons, Demo-GIF
│
├── docs/
│   └── OLLAMA_ERFAHRUNGEN.md   # Ehrlicher Erfahrungsbericht: Ollama + FreeCAD
│
└── tests/               # Unit-Tests
```

---

## Bekannte Einschränkungen

| Problem | Ursache | Lösung |
|---------|---------|--------|
| **Emojis als Umriss** im Flatpak | Flatpak-Sandbox blockiert System-Emoji-Fonts | Nativer Paket / AppImage verwenden |
| **FC12 bei Ollama gesperrt** | Zu komplex für lokale Modelle | Claude (Anthropic) oder GPT-4o verwenden |
| **API-Keys unverschlüsselt** | FreeCAD-Einstellungen haben keine Verschlüsselung | Keine Produktions-Keys verwenden |
| **Große Dateien (>2000 Zeilen)** | KI-Kontextfenster begrenzt | Nur relevante Abschnitte ins Eingabefeld laden |
| **Ollama nicht gefunden** | Dienst läuft nicht | `ollama serve` im Terminal starten |
| **Bild wird ignoriert** | Kein Vision-Modell gewählt | llava, bakllava oder moondream in Ollama laden |
| **Vision bei Cloud-Anbietern** | Nur bestimmte Modelle | gpt-4o, claude-3+, gemini-1.5+ verwenden |

---

## Ollama – Erfahrungsbericht

Wer Ollama als lokales KI-Backend einsetzen möchte, findet hier einen ehrlichen Erfahrungsbericht aus dem Projekt — mit allen Fehlern, Umwegen und dem was am Ende wirklich funktioniert hat:

📄 **[docs/OLLAMA_ERFAHRUNGEN.md](docs/OLLAMA_ERFAHRUNGEN.md)**

Inhalt: Installation · Flatpak-Besonderheiten · Was Ollama kann und nicht kann · Halluzinations-Beispiele · Fehler die wir selbst gemacht haben · Gegenmaßnahmen · Empfehlungen

---

## Lizenz

MIT License
