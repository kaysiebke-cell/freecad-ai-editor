[← Zurück: Fehler-Übersetzer & Backup-System](fehler-und-backup.md) | [Zur README](../README.md)

# Ollama + FreeCAD — Ehrlicher Erfahrungsbericht

Dieses Dokument ist kein Tutorial. Es ist eine ehrliche Bestandsaufnahme
aus einem realen Entwicklungsprojekt — mit allen Fehlern, Umwegen,
Rückschlägen und dem was am Ende tatsächlich funktioniert hat.

Entstanden ist es in einer Zusammenarbeit zwischen dem Projektentwickler
und **Claude (Anthropic)** — einem KI-Assistenten der beim Schreiben des
Codes, beim Debuggen und beim Ausarbeiten dieser Dokumentation mitgewirkt hat.
Das "wir" in diesem Dokument meint genau das: ein Mensch und eine KI die
gemeinsam gegen die Eigenheiten lokaler Sprachmodelle ankämpfen.

Zielgruppe: Entwickler die Ollama in eine FreeCAD-Werkzeugkette einbauen
wollen und eine realistische Einschätzung suchen, bevor sie anfangen.

---

## Die Ausgangssituation

Das Ziel war einfach formuliert: Der Nutzer beschreibt auf Deutsch was er
bauen möchte ("Erstelle einen Würfel mit einer zentralen Bohrung"), und
Ollama generiert daraus ein lauffähiges FreeCAD-Python-Makro.

Was simpel klingt, hat sich als erheblich schwieriger herausgestellt als erwartet.

---

## Warum überhaupt Ollama?

Ollama läuft vollständig lokal. Kein Account, keine Cloud, keine Datenweitergabe,
keine laufenden Kosten. Das passt zur Linux- und Open-Source-Philosophie
unter der dieses Projekt steht. Wer FreeCAD als Flatpak auf Linux nutzt
und seine CAD-Daten nicht in die Cloud schicken will, hat mit Ollama
eine ernstzunehmende Alternative.

| Eigenschaft | Ollama (lokal) | Claude / GPT-4o (Cloud) |
|---|---|---|
| Kosten | kostenlos | kostenpflichtig |
| Datenschutz | vollständig lokal | Daten verlassen den Rechner |
| Offline-Betrieb | ja | nein |
| FreeCAD-API-Wissen | lückenhaft bis falsch | gut |
| Zuverlässigkeit Code-Generierung | eingeschränkt | deutlich besser |
| Promptfolgetreue | schwach | gut |

---

## Installation

### Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3        # 8B Parameter, ca. 4,7 GB
```

### FreeCAD als Flatpak — eine eigene Welt

FreeCAD wird häufig als Flatpak installiert. Das Flatpak läuft in einer
isolierten Sandbox mit einem eigenen Python-Interpreter unter:

```
~/.var/app/org.freecad.FreeCAD/data/python/lib/python3.13/site-packages/
```

Python-Pakete müssen explizit über diesen Python installiert werden:

```bash
flatpak run --command=python3 org.freecad.FreeCAD -m pip install paketname
```

**Wichtige Erkenntnis aus dem Projekt:**
Pakete die C-Bibliotheken benötigen funktionieren in der Flatpak-Sandbox nicht.
`pyenchant` (Rechtschreibprüfung) schlägt fehl weil `libenchant` fehlt.
Erst der Wechsel zu `pyspellchecker` (reines Python) hat funktioniert:

```bash
flatpak run --command=python3 org.freecad.FreeCAD -m pip install pyspellchecker
```

Testbefehl zum Prüfen ob die Installation wirklich im richtigen Python gelandet ist:

```bash
flatpak run --command=python3 org.freecad.FreeCAD -c \
  "from spellchecker import SpellChecker; s=SpellChecker(language='de'); \
   print(s.unknown(['wandsterke', 'würfel']))"
# Ausgabe: {'wandsterke'}  → korrekt erkannt als Fehler
```

---

## Was Ollama grundsätzlich gut kann

- Syntaktisch gültigen Python-Code ausgeben
- Einfache FreeCAD Part-Workbench Objekte erstellen
  (`Part::Box`, `Part::Cylinder`, `Part::Sphere`)
- Grundlegende Positionierung über `Placement.Base`
- Kurze, klare Beschreibungen korrekt umsetzen

---

## Was Ollama nicht kann — die vollständige Liste

### 1. Die FreeCAD-API kennen

Das ist das Kernproblem. Lokale 7B–14B Modelle kennen die FreeCAD-API
nicht vollständig und **erfinden Objekttypen und Methoden die nicht existieren**.

#### Halluzinierte Objekttypen

Alle folgenden Typen wurden im realen Betrieb von `llama3:latest` generiert
und existieren in FreeCAD nicht:

```python
# Halluzination                    Korrekte Alternative
"Part::UnionForTwoVolumes"     →   "Part::Fuse"
"Part::Union"                  →   "Part::Fuse"
"Part::BooleanUnion"           →   "Part::Fuse"
"Part::Merge"                  →   "Part::Fuse"
"Part::BooleanCut"             →   "Part::Cut"
"Part::Subtract"               →   "Part::Cut"
"Part::Difference"             →   "Part::Cut"
"Part::Intersection"           →   "Part::Common"
"Part::BooleanIntersection"    →   "Part::Common"
"Part::Profile2D"              →   existiert nicht
"Part::Extrude2D"              →   existiert nicht
```

#### Halluzinierte Methoden

```python
# FALSCH — von Ollama generiert:
fusion = doc.addObject("Part::Fuse", "Fusion")
fusion.Add(box)       # .Add() existiert nicht bei Part::Fuse
fusion.Add(cylinder)

# RICHTIG:
fusion.Base = box
fusion.Tool = cylinder
```

#### Falsche Eigenschaftsnamen

```python
# FALSCH — Part::Cylinder hat kein .Length:
cylinder.Length = 80

# RICHTIG:
cylinder.Height = 80
```

#### Falsches API-System komplett

Ein getestetes Modell (C3D-v0) hat statt FreeCAD-Code **CadQuery-Code** generiert —
ein völlig anderes Python-CAD-Framework. Der Code war syntaktisch korrekt
und inhaltlich sinnvoll, aber in FreeCAD nicht verwendbar.

### 2. Anweisungen konsequent befolgen

Trotz explizitem Verbot im System-Prompt erzeugt das Modell regelmäßig
erklärenden Fließtext nach dem Code:

```python
box = doc.addObject("Part::Box", "Box")
box.Length = 40

Die Box wurde erfolgreich erstellt und hat die Maße 40x40x40mm.
# ^ kein Python — verursacht SyntaxError
```

Das ist kein gelegentlicher Fehler — es passiert ständig.

**Was dagegen geholfen hat:**
Die Ausgabe-Anweisung ("Nur Python-Code") muss am **Ende** des System-Prompts
stehen, nicht am Anfang. Lokale Modelle neigen dazu die letzte Anweisung
zu priorisieren. Eine Anweisung die früh im Prompt steht wird durch später
folgende Regeln überschrieben.

### 3. Lange Prompts verarbeiten

Über ~50 Zeilen System-Prompt verliert das Modell den Fokus. Erste Versuche
mit detaillierten Regelwerken (100+ Zeilen) haben die Ergebnisse
**verschlechtert** statt verbessert. Das Modell hat dann mehr Erklärungs-Text
produziert als zuvor, weil die eigentliche Ausgabe-Anweisung zu weit
hinten im Kontext lag.

### 4. Komplexe FreeCAD-Modi

FreeCAD PartDesign mit Sketcher-Constraints (Skizzen, Extrusion, Taschen)
ist für lokale Modelle zu komplex. Der generierte Code enthielt regelmäßig
falsche Constraint-Syntax und fehlende Body-Zuordnungen. Dieser Modus
wurde für Ollama im Projekt gesperrt.

### 5. Boolesche Operationen korrekt zuordnen

"Boole'sche Subtraktion" und "Vereinigung" verwechselt das Modell häufig.
Konkrete Begriffe aus dem Deutschen ("Bohrung", "aushöhlen", "ausschneiden")
funktionieren zuverlässiger als technische Fachbegriffe.

---

## Fehler die WIR gemacht haben

Das ist der Teil den die meisten Dokumentationen weglassen. Nicht alle
Probleme kamen von Ollama. Einige kamen vom eigenen Code.

### Der Filter der Code zerstört hat

Um Erklärungs-Text herauszufiltern wurde eine Funktion geschrieben die
jede Zeile klassifiziert: ist das Python-Code oder Fließtext?

Die Klassifizierung basierte auf einer Token-Liste:
```python
_CODE_STARTS = ("import ", "from ", "def ", "doc", "box", "zyl", ...)
```

**Das Problem:** Zeilen wie `cylinder = doc.addObject(...)` beginnen mit
`cylinder` — einem variablen Namen der nicht in der Liste stand.
Der Filter hat diese Zeile als Text klassifiziert und auskommentiert.

**Das Ergebnis:**

```python
# cylinder = doc.addObject("Part::Cylinder", "Zylinder")  ← auskommentiert
# cylinder.Radius = 5                                       ← auskommentiert

cut = doc.addObject("Part::Cut", "Schnitt")
cut.Tool = cylinder  # ← NameError: name 'cylinder' is not defined
```

Der `NameError` sah aus als käme er von Ollama. Er kam von unserem Filter.
Erkannt wurde das erst durch Raw-Logging der ungefilterten Modell-Antwort.

**Fix:** Erkennung von Python-Zuweisungen über Regex:
```python
# Jede Zeile der Form "identifier = ..." oder "identifier.attr ..."
re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*[\(\[=]", zeile)
```

### Der Filter der auf alle Antworten angewendet wurde

Der Erklärungs-Text-Filter war für FC11/FC12/FC13 (Natürlichsprache-Modi)
gedacht. Er wurde versehentlich auf **alle** KI-Antworten angewendet —
auch auf reguläre Preset-Antworten die ohnehin reinen Python-Code
zurückgaben. Dort hat er Code beschädigt der vorher korrekt war.

**Fix:** Flag `_nl_antwort_aktiv` das nur für FC11/FC12/FC13 gesetzt wird.

### Der Experten-Modus der nicht funktioniert hat

Es gab einen Experten-Modus der Erklärungs-Text unterdrücken sollte.
Der Modus hat nicht funktioniert. Ursache: Die Experten-Anweisung stand
als **Prefix** vor dem System-Prompt. Der lange System-Prompt danach hat
sie überschrieben.

```python
# FALSCH:
full_prompt = f"{experten_prefix}\n{system_prompt}\n{user_prompt}"
# → system_prompt überschreibt experten_prefix

# RICHTIG:
full_prompt = f"{system_prompt}\n{experten_suffix}\n{user_prompt}"
# → experten_suffix steht am Ende, wird zuletzt gelesen
```

### Thread-Safety ignoriert

Die Funktion `_worker_mit_system` lief in einem separaten Thread.
Sie hat trotzdem Qt-Widgets aus dem Haupt-Thread gelesen:

```python
# FALSCH — Qt-Widget-Zugriff aus Worker-Thread:
preset = getattr(self, "_preset_box", None)
preset_name = preset.currentText()  # Race Condition möglich
```

Das kann zu inkonsistenten Zuständen führen wenn der Nutzer während
der KI-Anfrage das Preset wechselt. Die Werte müssen vor dem Thread-Start
im Haupt-Thread gesichert werden.

### Der Viewport der Dock-Panels versteckt hat

Der eingebettete FreeCAD 3D-Viewport wurde per `setParent()` aus FreeCAD
herausgerissen und in den Editor eingebettet. Dieser Qt-Aufruf löst
intern einen kompletten Relayout des Hauptfensters aus — alle Dock-Panels
(KI, Aktionen, etc.) wurden dabei versteckt.

Der Nutzer sah nach Öffnen der Vorschau ein leeres Fenster ohne Panels.

**Fix:** Dock-Zustände vor `setParent()` sichern und danach wiederherstellen.

---

## Was wirklich geholfen hat

### Zweigleisige Strategie

Keine einzelne Maßnahme löst das Problem. Erst die Kombination macht
das System brauchbar:

**Gleis 1 — Prompt-Optimierung:**
- Prompts unter 50 Zeilen halten
- Kontext-Prefix: `"FreeCAD Part Workbench:\n"` vor jede Nutzeranfrage
- Ausgabe-Anweisung am Anfang UND am Ende des Prompts
- Konkrete deutsche Begriffe statt technischer Fachsprache
- Ein gutes Code-Beispiel im Prompt ist wirksamer als zehn Regeln

**Gleis 2 — Automatische Nachbearbeitung:**
- Alle bekannten Fake-Typen automatisch ersetzen
- `.Add(x)` → `.Base = x` / `.Tool = x`
- `cylinder.Length` → `cylinder.Height`
- Pre-Execution-Prüfung: Code wird nicht ausgeführt wenn bekannte
  Phantasie-Typen erkannt werden
- Raw-Logging jeder ungefilterten Modell-Antwort zur Diagnose

### Raw-Logging als Diagnosewerkzeug

Das wichtigste Debugging-Werkzeug: die ungefilterte Antwort loggen
bevor irgendein Filter daran arbeitet.

```python
with open(os.path.expanduser("~/ollama_raw.txt"), "w", encoding="utf-8") as f:
    f.write(full_ollama_antwort)
```

Erst damit war klar ob ein Fehler vom Modell oder vom eigenen Filter kam.
Ohne dieses Log hätte man im Dunkeln gestochert.

### Ollama für bestimmte Modi sperren

Nicht jede Aufgabe ist für Ollama geeignet. Es hilft nichts das Modell
immer wieder mit komplexen Aufgaben zu konfrontieren die es nicht beherrscht.
Klare Grenzen setzen: FC12 (PartDesign) und komplexe Schrittweisen-Modi
sind für Ollama gesperrt — mit einer deutlichen Fehlermeldung für den Nutzer.

---

## Konkrete Empfehlungen

1. **Niemals nur auf den Prompt vertrauen.**
   Lokale Modelle halten sich nicht konsequent an Regeln. Eine nachgelagerte
   Korrektur- und Prüfschicht ist unverzichtbar.

2. **System-Prompts unter 50 Zeilen halten.**
   Ein gutes Code-Beispiel im Prompt ist wirksamer als zehn Verbote.

3. **Die ungefilterte Modell-Antwort loggen.**
   Sonst weiß man nie ob das Modell oder der eigene Filter das Problem ist.

4. **Fake-Typ-Erkennung vor exec() einbauen.**
   Code mit bekannten Phantasie-Typen darf den exec()-Aufruf nie erreichen.
   Ein halbfertiger FreeCAD-Dokumentzustand ist schwer rückgängig zu machen.

5. **Filter-Code gründlich testen.**
   Insbesondere Code-Erkennungs-Heuristiken. Ein Filter der gültigen Code
   auskommentiert ist schlimmer als kein Filter.

6. **Komplexe Modi für Ollama sperren.**
   Nicht jede Funktion muss mit Ollama funktionieren.

7. **Zweigleisig denken.**
   Prompt-Optimierung und Code-Nachbearbeitung zusammen machen aus einem
   unzuverlässigen Modell ein brauchbares Werkzeug.

---

## Fazit

Ollama ist eine gute Wahl wenn Datenschutz, Kosten und Offline-Betrieb
Priorität haben. Für FreeCAD-spezifische Code-Generierung sind die
Grenzen lokaler Modelle spürbar — und manchmal frustrierend.

Die Arbeit hat sich trotzdem gelohnt: Die gesamte Infrastruktur
(Prompts, Filter, Fake-Typ-Erkennung, Korrekturen) ist modell-unabhängig.
Mit Claude oder GPT-4o funktioniert dieselbe Architektur — und produziert
dort deutlich weniger Fehler, weil diese Modelle die FreeCAD-API kennen
und sich an Anweisungen halten.

Wer mit Ollama anfängt sollte realistische Erwartungen mitbringen:
Es wird nicht fehlerfrei sein. Aber mit genug Nachbearbeitung wird es brauchbar.
Und man lernt dabei mehr über die eigene Codebasis als man erwartet —
weil man jeden Fehler des Modells selbst abfangen muss.

---

[← Zurück: Fehler-Übersetzer & Backup-System](fehler-und-backup.md) | [Zur README](../README.md)
