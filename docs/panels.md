[← Zurück: Die Benutzeroberfläche](oberflaeche.md) | [Zur README](../README.md) | Weiter: [KI-Workflow & Presets →](ki-workflow.md)

# Panels im Detail

## ⚙ Einstellungen-Panel
- **KI-Quelle** wählen (Dropdown mit allen 19 Anbietern)
- **🔄 Modelle neu laden** – frische Modellliste vom Anbieter abrufen
- **Modell** auswählen
- **Preset** wählen (40+ vordefinierte Aufgabenstellungen)
- **Temperatur** 0.0–2.0 (empfohlen: 0.0–0.3 für Code, 0.5–0.8 für Dokumentation)
- **Modus:** 🟢 Anfänger (ausführlich auf Deutsch) / 🔵 Experte (knapp & technisch)
- **Farbschema:** 🌙 Dunkel / ☀ Hell – umschaltet alle Farben sofort (Syntax-Highlighting, Eingabefelder, Editor), Auswahl wird dauerhaft gespeichert
- **API-Schlüssel** pro Anbieter eingeben & automatisch speichern

## 🤖 KI-Panel
- **Eingabefeld** (grün hinterlegt) – Prompt oder zu analysierender Code
  - `/snippetname` tippen → Snippet-Autovervollständigung öffnet sich
- **KI-Antwort** (blau hinterlegt) – Antwort erscheint live gestreamt
- **Projekt-Kontext** – wird bei jedem KI-Aufruf als Hintergrundinfo mitgeschickt
- **Suche/Ersetzen** (Strg+F) – direkt im Panel
- **💾 Sitzung speichern** – Chat-Verlauf + KI-Antwort + Anbieter als `.json` sichern
- **📂 Sitzung laden** – gespeicherte Sitzung wiederherstellen
- **🧹 Verlauf zurücksetzen** – löscht den gesamten Chat-Verlauf und die Anzeige
- Chat-Verlauf mit automatischem Kompacting

## 🎛 Aktionen-Panel
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

## 📦 Snippets-Panel

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

## 💡 API-Hints-Panel
Offline-Kurzreferenz aller wichtigen FreeCAD-Python-Befehle:
- **App** · Part · Sketcher · Mesh · Draft · Placement · Selection · GUI/View
- Suchfeld: mehrere Wörter gleichzeitig (z.B. `part shape`, `mesh vector`)
- Befehl anklicken → Beschreibung erscheint darunter
- **📋 Signatur kopieren** → direkt in Editor oder KI-Eingabefeld einfügen

## 📂 Datei-Browser
- Frei skalierbar (Rand des Panels ziehen)
- **Navigation:** `^` Ordner hoch · `Hom` Home-Verzeichnis · `Makr` Makro-Ordner · Pfad-Feld + `GO`
- **Filter:** nur `.py` / nur `.FCMacro` / alle Dateien
- **Doppelklick:** `.py`/`.FCMacro` → im Editor öffnen · andere Dateien → Pfad kopieren
- **Lesezeichen:** ☆-Button → Ordner merken

## 🛠 Tools-Panel

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

## 📚 Bibliothek-Panel

Siehe [Makro-Bibliothek](makro-bibliothek.md) für Details.

## 🔧 Werkzeuge-Panel
- **Code-Baum:** alle `def`/`class` automatisch aufgelistet → Doppelklick springt zur Definition
- **Navigation:** Zeile anspringen · Lesezeichen setzen/navigieren/löschen
- **Edit & Check:** Einrücken, Ausrücken, Kommentieren, Verschieben, Syntax-Prüfung
- **Bereinigung:** Trailing Spaces, Leerzeilen, BOM

## 🔧 Helfer-Panel (Barrierefreiheit & Vision)

Ein eigenständiges Chat-Panel mit zwei Aufgaben:

### Legastheniker-Assistent
Frei geschriebenen deutschen Text (Rechtschreibung egal) in eine saubere FreeCAD-Beschreibung umwandeln:
```
ich brauch einen kasten mit loch zum anschrauben an die wand
→ KI korrigiert → „Eine rechteckige Halterung mit Montageöffnung für Wandbefestigung"
```
- Echtzeit-Rechtschreibprüfung während des Tippens (mit `pyspellchecker`)
- Diff-Anzeige der Korrekturen (rot = entfernt, grün = hinzugefügt)
- Ergebnis direkt in den Editor übernehmen

### Text + Bild an die KI senden (Vision)
- **📎 Bild anhängen** – Datei-Dialog mit anbieter-spezifischen Formaten
- **📋 Aus Zwischenablage** – Strg+V oder Schaltfläche
- **Drag & Drop** – Bilddatei direkt in das Eingabefeld ziehen
- Thumbnail-Vorschau mit Bildgröße-Anzeige und ✕-Button
- Warnung wenn das gewählte Modell kein Vision unterstützt
- Erlaubte Formate werden automatisch pro Anbieter geladen (keine Hartkodierung)

| Anbieter | Vision-Modelle | Formate |
|----------|---------------|---------|
| Ollama (Lokal) | llava, bakllava, moondream, minicpm-v | JPEG, PNG, WebP, GIF, BMP |
| Anthropic (Claude) | claude-3+ | JPEG, PNG, GIF, WebP |
| OpenAI (ChatGPT) | gpt-4o, gpt-4-turbo | JPEG, PNG, GIF, WebP |
| Gemini (Google) | gemini-1.5+ | JPEG, PNG, GIF, WebP, HEIC + mehr |
| OpenRouter (Cloud) | modellabhängig | JPEG, PNG, GIF, WebP |

## ⚠ Fehler-Panel

Siehe [Fehler-Übersetzer & Backup-System](fehler-und-backup.md) für Details.

---

## 🤝 Assistent-Panel

Ein interaktiver Schritt-für-Schritt-Assistent, der Fragen über den Editor auf Deutsch beantwortet
und dabei die relevanten Buttons und Panels direkt aufleuchten lässt.

**Verwendung:**
1. `🤝 Assist.`-Button in der Toolbar klicken
2. Frage ins Eingabefeld tippen, z. B.:
   - *„wie übersetze ich einen Fehler?"*
   - *„wie richte ich Ollama ein?"*
   - *„wie benutze ich den Plan-Modus?"*
3. **❓ Fragen** oder Enter drücken
4. Die KI antwortet auf Deutsch in nummerierten Schritten
5. Die genannten Panels/Buttons leuchten automatisch nacheinander auf (2,2 s Abstand)
   – geschlossene Panels öffnen sich dabei automatisch

**Hinweise:**
- Funktioniert mit dem aktuell eingestellten KI-Anbieter (⚙ Einst.)
- Für Ollama (lokal) wird ein kompakter System-Prompt verwendet – für Cloud-Anbieter der ausführlichere
- **🗑 Verlauf löschen** leert die Chat-Anzeige

---

## ♿ Barrierefreiheit-Panel

Anpassungen für Sehschwäche, Motorik und persönliche Vorlieben. Alle Einstellungen werden
gespeichert und beim nächsten Start automatisch wiederhergestellt.

### 👁 Sehschwäche

| Einstellung | Funktion |
|---|---|
| **UI-Schriftgröße** (Slider 8–24 pt) | Schriftgröße aller Beschriftungen live anpassen |
| **Editor-Schriftgröße** (Slider 8–24 pt) | Schriftgröße im Code-Editor anpassen |
| **Hoher Kontrast** | Alle UI-Elemente: weiß auf schwarz (überschreibt das Theme) |
| **Icons mit Text** | Toolbar-Buttons zeigen Emoji + Kurzname, z. B. `⚙ Einst.` statt nur `⚙` |

### 🖐 Motorik

| Einstellung | Funktion |
|---|---|
| **Button-Größe** Normal / Groß / Sehr groß | Höhe aller Buttons: 26 / 34 / 42 px |
| **Tastaturmodus** | Alt+1 bis Alt+0 öffnen die Panels; Shortcut wird im Tooltip angezeigt |
| **Einfache Ansicht** | Blendet selten genutzte Panels aus der Toolbar aus (Snip, API, Dat., Tools, Bib., Werkz., Helfer bleiben erhalten; Einst., KI, Akt., Fehler, ♿, Assist. bleiben sichtbar) |

### 💬 Einfache Sprache

| Einstellung | Funktion |
|---|---|
| **KI antwortet in einfacher Sprache** | KI verwendet kurze Sätze, vermeidet Fachbegriffe |
| **Fachbegriffe automatisch erklären** | KI erklärt verwendete Begriffe direkt danach |
| **KI-Antworten kürzer halten** | Kompakte Antworten ohne lange Erklärungen |

### ⚙ Allgemein

| Einstellung | Funktion |
|---|---|
| **Tooltips immer sichtbar** | Tooltip erscheint sofort beim Einfahren mit der Maus (kein Wartedelay) |
| **Animationen reduzieren** | Button-Aufleuchten dauert 300 ms statt 1800 ms |

---

[← Zurück: Die Benutzeroberfläche](oberflaeche.md) | [Zur README](../README.md) | Weiter: [KI-Workflow & Presets →](ki-workflow.md)
