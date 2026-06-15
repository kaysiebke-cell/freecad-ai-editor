# -*- coding: utf-8 -*-
"""
Fehlerübersetzer: Englische Python-Fehlermeldungen → Deutsches Klartext-Deutsch.
Verwendung:
    from fehler import uebersetze_fehler, uebersetze_text
    try:
        ...
    except Exception as e:
        meldung = uebersetze_fehler(e)
        QMessageBox.critical(self, "Fehler", meldung)

    # Für rohen Traceback-Text (z.B. aus dem Fehler-Tab):
    meldung = uebersetze_text(raw_traceback_string)

[FIX] Fehlender Komma nach PySide2-Eintrag
[FIX] Unicode-Escape korrigiert
[FIX] Format-String-Escape-Logik vereinfacht
[FIX] Regex-Flag Optionen optimiert
[FIX] Fehlerbehandlung in format() verbessert
"""

import re


# ── Bekannte Fehlermuster ──────────────────────────────────────────────────────
# Jeder Eintrag: (regulärer Ausdruck, deutsche Erklärung)
# {0}, {1} … werden durch die gefundenen Gruppen ersetzt.

_MUSTER = [

    # ── AttributeError ────────────────────────────────────────────────────────
    (r"'NoneType' object has no attribute '(.+?)'",
     "❌ Objekt ist None\n\n"
     "»{0}« wurde auf None aufgerufen.\n"
     "Mögliche Ursachen:\n"
     "  • Funktion gibt None zurück statt ein Objekt\n"
     "  • doc.getObject(name) hat nichts gefunden\n"
     "  • Reihenfolge falsch: Objekt noch nicht erstellt\n"
     "Tipp: Vor der Verwendung prüfen:\n"
     "  if obj is not None:  obj.{0}"),

    (r"'(.+?)' object has no attribute '(.+?)'",
     "❌ Methode oder Variable fehlt\n\n"
     "Das Objekt »{0}« kennt »{1}« nicht.\n"
     "Mögliche Ursachen:\n"
     "  • Methode wurde versehentlich gelöscht\n"
     "  • Tippfehler im Namen\n"
     "  • Methode wurde noch nicht definiert"),

    # ── NameError ─────────────────────────────────────────────────────────────
    (r"name '(.+?)' is not defined",
     "❌ Name nicht bekannt\n\n"
     "»{0}« wurde verwendet, aber nie definiert.\n"
     "Mögliche Ursachen:\n"
     "  • Variable wurde nicht angelegt\n"
     "  • Tippfehler im Namen\n"
     "  • Import fehlt"),

    # ── ImportError / ModuleNotFoundError ─────────────────────────────────────
    (r"No module named '(.+?)'",
     "❌ Modul nicht gefunden\n\n"
     "»{0}« ist nicht installiert oder nicht auffindbar.\n"
     "Tipp: pip install {0}"),

    (r"cannot import name '(.+?)' from '(.+?)'",
     "❌ Import fehlgeschlagen\n\n"
     "»{0}« existiert nicht in »{1}«.\n"
     "Mögliche Ursachen:\n"
     "  • Tippfehler im Namen\n"
     "  • Falsche Modulversion"),

    # ── IndentationError ──────────────────────────────────────────────────────
    (r"unindent does not match any outer indentation level",
     "❌ Einrückungsfehler\n\n"
     "Die Leerzeichen in dieser Zeile passen nicht zur Umgebung.\n"
     "Tipp: Prüfe ob überall 4 Leerzeichen pro Ebene verwendet werden.\n"
     "      Keine Tabs und Leerzeichen mischen!"),

    (r"expected an indented block",
     "❌ Einrückung erwartet\n\n"
     "Nach einem Doppelpunkt (:) muss der nächste Block eingerückt sein.\n"
     "Beispiel:\n"
     "  def meine_funktion():\n"
     "      pass   ← mind. 4 Leerzeichen"),

    (r"unexpected indent",
     "❌ Unerwartete Einrückung\n\n"
     "Diese Zeile ist eingerückt, obwohl sie es nicht sein sollte.\n"
     "Tipp: Überprüfe die Leerzeichen am Zeilenanfang."),

    # ── SyntaxError ───────────────────────────────────────────────────────────
    (r"invalid syntax",
     "❌ Syntaxfehler\n\n"
     "Python versteht diese Zeile nicht.\n"
     "Häufige Ursachen:\n"
     "  • Fehlende Klammer ) ] }\n"
     "  • Fehlender Doppelpunkt nach def / if / for …\n"
     "  • Tippfehler in einem Schlüsselwort"),

    (r"EOL while scanning string literal",
     "❌ Zeichenkette nicht geschlossen\n\n"
     "Ein Anführungszeichen wurde geöffnet aber nie geschlossen.\n"
     "Tipp: Prüfe ob alle ' oder \" paarweise vorhanden sind."),

    (r"EOF while scanning triple-quoted string",
     "❌ Mehrzeiliger Text nicht geschlossen\n\n"
     "Ein dreifaches Anführungszeichen ''' oder \"\"\" wurde nicht geschlossen."),

    # ── TypeError ─────────────────────────────────────────────────────────────
    (r"unsupported operand type\(s\) for (.+?): '(.+?)' and '(.+?)'",
     "❌ Falscher Datentyp\n\n"
     "Die Operation »{0}« funktioniert nicht zwischen »{1}« und »{2}«.\n"
     "Tipp: Vielleicht str() oder int() zur Umwandlung verwenden?"),

    (r"'(.+?)' object is not callable",
     "❌ Kein aufrufbares Objekt\n\n"
     "»{0}« ist keine Funktion und kann nicht mit () aufgerufen werden."),

    (r"'(.+?)' object is not subscriptable",
     "❌ Kein Index-Zugriff möglich\n\n"
     "»{0}« unterstützt keinen []-Zugriff.\n"
     "Tipp: Nur Listen, Dicts, Strings und Tuples erlauben obj[index]."),

    (r"'NoneType' object is not iterable",
     "❌ None ist nicht durchlaufbar\n\n"
     "Es wurde versucht, über None zu iterieren (for … in None).\n"
     "Tipp: Prüfe ob die Variable überhaupt einen Wert hat:\n"
     "  if meine_liste is not None:\n"
     "      for item in meine_liste: …"),

    (r"argument of type '(.+?)' is not iterable",
     "❌ Nicht durchsuchbar\n\n"
     "»{0}« kann nicht mit »in« durchsucht werden.\n"
     "Tipp: Nur Listen, Strings und ähnliche Typen sind durchsuchbar."),

    (r"takes (\d+) positional argument[s]* but (\d+) (?:was|were) given",
     "❌ Falsche Anzahl an Argumenten\n\n"
     "Die Funktion erwartet {0} Argument(e), bekommen hat sie {1}.\n"
     "Tipp: Parameteranzahl im Funktionskopf prüfen."),

    # ── ValueError ────────────────────────────────────────────────────────────
    (r"invalid literal for int\(\) with base \d+: '(.+?)'",
     "❌ Ungültige Zahl\n\n"
     "»{0}« kann nicht in eine Ganzzahl umgewandelt werden.\n"
     "Tipp: Enthält der Text Buchstaben oder Leerzeichen?"),

    # ── UnicodeDecodeError ────────────────────────────────────────────────────
    (r"'(.+?)' codec can't decode byte",
     "❌ Zeichenkodierung fehlgeschlagen\n\n"
     "Die Datei enthält Zeichen, die mit »{0}« nicht lesbar sind.\n"
     "Tipp: Datei mit encoding='utf-8' oder encoding='latin-1' öffnen.\n"
     "  with open(pfad, 'r', encoding='utf-8') as f: …"),

    # ── FileNotFoundError / OSError ───────────────────────────────────────────
    (r"No such file or directory: '(.+?)'",
     "❌ Datei nicht gefunden\n\n"
     "»{0}« existiert nicht.\n"
     "Mögliche Ursachen:\n"
     "  • Pfad falsch geschrieben\n"
     "  • Datei wurde verschoben oder gelöscht"),

    (r"Permission denied: '(.+?)'",
     "❌ Zugriff verweigert\n\n"
     "»{0}« kann nicht geöffnet werden.\n"
     "Tipp: Prüfe die Dateirechte oder ob die Datei gerade von einem\n"
     "      anderen Programm verwendet wird."),

    (r"[Ii]s a directory: '(.+?)'",
     "❌ Ist ein Ordner, keine Datei\n\n"
     "»{0}« ist ein Verzeichnis.\n"
     "Tipp: Vollständigen Dateipfad inkl. Dateiname angeben."),

    # ── RecursionError ────────────────────────────────────────────────────────
    (r"maximum recursion depth exceeded",
     "❌ Endlosschleife (Rekursion)\n\n"
     "Eine Funktion ruft sich zu oft selbst auf.\n"
     "Tipp: Prüfe ob eine Abbruchbedingung fehlt."),

    # ── ZeroDivisionError ─────────────────────────────────────────────────────
    (r"division by zero",
     "❌ Division durch Null\n\n"
     "Es wurde versucht durch 0 zu dividieren.\n"
     "Tipp: Vor der Division prüfen ob der Nenner ≠ 0 ist."),

    # ── KeyError ──────────────────────────────────────────────────────────────
    (r"KeyError:\s*['\"]?(.+?)['\"]?$",
     "❌ Schlüssel nicht gefunden\n\n"
     "»{0}« existiert nicht im Dictionary.\n"
     "Tipp: dict.get(schlüssel) verwenden um Abstürze zu vermeiden."),

    # ── IndexError ────────────────────────────────────────────────────────────
    (r"list index out of range",
     "❌ Listenindex außerhalb des Bereichs\n\n"
     "Es wurde auf eine Position zugegriffen, die nicht existiert.\n"
     "Tipp: Erst prüfen ob len(liste) > index ist."),

    # ── RuntimeError – Qt ─────────────────────────────────────────────────────
    (r"wrapped C/C\+\+ object of type (.+?) has been deleted",
     "❌ Qt-Objekt wurde bereits gelöscht\n\n"
     "Das Widget »{0}« existiert nicht mehr.\n"
     "Mögliche Ursachen:\n"
     "  • Fenster wurde geschlossen, aber eine Referenz blieb erhalten\n"
     "  • Signal/Slot verweist auf ein zerstörtes Objekt\n"
     "Tipp: Vor dem Zugriff prüfen ob das Objekt noch lebt:\n"
     "  try: widget.isVisible()\n"
     "  except RuntimeError: return"),

    # ── Netzwerk / requests ───────────────────────────────────────────────────
    (r"(?:ConnectionError|NewConnectionError|Failed to establish a new connection)",
     "❌ Verbindung fehlgeschlagen\n\n"
     "Der Server ist nicht erreichbar.\n"
     "Mögliche Ursachen:\n"
     "  • Kein Internet / falsche URL\n"
     "  • Server offline oder falscher Port\n"
     "  • Firewall blockiert die Verbindung\n"
     "Tipp: URL prüfen und ggf. Ollama / API-Server starten."),

    (r"(?:ReadTimeout|ConnectTimeout|Timeout)",
     "❌ Zeitüberschreitung (Timeout)\n\n"
     "Der Server hat nicht rechtzeitig geantwortet.\n"
     "Tipp: Timeout-Wert erhöhen oder prüfen ob der Server ausgelastet ist."),

    (r"(?:401|Unauthorized|Invalid API key|authentication)",
     "❌ Authentifizierung fehlgeschlagen\n\n"
     "Der API-Schlüssel ist ungültig oder fehlt.\n"
     "Tipp: Schlüssel in der rechten Sidebar prüfen\n"
     "  (Anthropic → sk-ant-…  |  OpenAI → sk-…)"),

    (r"(?:429|Too Many Requests|rate.?limit)",
     "❌ Zu viele Anfragen (Rate Limit)\n\n"
     "Das API-Kontingent ist vorübergehend ausgeschöpft.\n"
     "Tipp: Kurz warten und erneut versuchen."),

    # ── OverflowError ─────────────────────────────────────────────────────────
    (r"(?:int too large to convert|OverflowError|math range error)",
     "❌ Zahl zu groß\n\n"
     "Der berechnete Wert überschreitet den darstellbaren Bereich.\n"
     "Tipp: Zwischenergebnisse prüfen oder float statt int verwenden."),

    # ── FreeCAD-spezifisch ────────────────────────────────────────────────────
    (r"No module named 'PySide2'",
     "❌ PySide2 nicht gefunden\n\n"
     "FreeCAD verwendet PySide6, nicht PySide2.\n"
     "Ersetze im Code alle PySide2-Imports:\n"
     "  from PySide2.QtWidgets ...  →  from PySide6.QtWidgets ...\n"
     "  from PySide2.QtCore ...     →  from PySide6.QtCore ...\n"
     "  from PySide2.QtGui ...      →  from PySide6.QtGui ...\n\n"
     "Tipp: Beim nächsten Mal im Suchfeld schreiben:\n"
     "      'Benutze PySide6, nicht PySide2'"),

    (r"No active document",
     "❌ Kein aktives FreeCAD-Dokument\n\n"
     "Es ist kein Dokument geöffnet.\n"
     "Tipp: App.newDocument() aufrufen oder zuerst eine Datei öffnen."),

    (r"Object '(.+?)' not found",
     "❌ FreeCAD-Objekt nicht gefunden\n\n"
     "»{0}« existiert nicht im aktiven Dokument.\n"
     "Tipp: doc.getObject(name) gibt None zurück wenn das Objekt fehlt.\n"
     "      Vor der Verwendung auf None prüfen!"),

    (r"Shape is Null",
     "❌ FreeCAD-Shape ist leer\n\n"
     "Das Shape-Objekt enthält keine Geometrie.\n"
     "Tipp: Sicherstellen dass Part.makeBox() / makeCompound() etc.\n"
     "      erfolgreich ausgeführt wurde und das Ergebnis nicht leer ist."),

    (r"Links go out of allowed scope",
     "❌ FreeCAD-Link außerhalb des Gültigkeitsbereichs\n\n"
     "Ein Objekt verweist auf etwas, das nicht im selben Dokument liegt.\n"
     "Tipp: Alle referenzierten Objekte im gleichen Dokument erstellen."),
]

# Einmalig beim Import kompilieren – spart Overhead bei jedem Aufruf
# WICHTIG: re.IGNORECASE nur bei Text-Matching, nicht bei Struktur (z.B. KeyError)
_COMPILED = [(re.compile(muster, re.IGNORECASE | re.MULTILINE), vorlage)
             for muster, vorlage in _MUSTER]

# Regex für bekannte Fehlertyp-Namen (für Traceback-Erkennung)
_RE_FEHLERTYP = re.compile(
    r'(\w+(?:Error|Exception|Warning|Fault|Interrupt|Stop|Exit)):\s*',
    re.MULTILINE)


def _escape_format_groups(gruppen: tuple) -> tuple:
    """Escapet Gruppen für sichere format()-Verwendung.
    
    Alle { und } in den Gruppen werden escaped, damit sie nicht
    von format() als Platzhalter interpretiert werden.
    """
    return tuple(
        g.replace("{", "{{").replace("}", "}}") if isinstance(g, str) else g
        for g in gruppen
    )


def uebersetze_fehler(fehler: Exception) -> str:
    """
    Übersetzt eine Python-Exception in eine deutsche Klartextmeldung.
    Gibt bei unbekannten Fehlern den Originaltext zurück.
    """
    fehler_typ  = type(fehler).__name__
    fehler_text = str(fehler)

    for regex, vorlage in _COMPILED:
        treffer = regex.search(fehler_text)
        if treffer:
            try:
                # Gruppen escapen für sicheres format()
                gruppen = _escape_format_groups(treffer.groups())
                deutsch = vorlage.format(*gruppen)
            except (IndexError, ValueError, KeyError) as e:
                # Fallback: Template-Fehler → Original
                deutsch = vorlage
            return f"{fehler_typ}:\n\n{deutsch}"

    # Kein Muster gefunden → Originaltext mit Typ
    return (
        f"{fehler_typ}: {fehler_text}\n\n"
        "──────────────────────────────\n"
        "Dieser Fehlertyp ist noch nicht übersetzt.\n"
        "Beschreibe ihn gerne – dann ergänze ich ihn."
    )


def uebersetze_text(text: str) -> str:
    """
    Übersetzt einen rohen Fehlertext oder Traceback in eine deutsche Klartextmeldung.
    Erkennt den Fehlertyp automatisch aus dem Traceback.
    Nützlich für den Fehler-Tab, wo kein Exception-Objekt vorliegt.

    Beispiel:
        result = uebersetze_text(traceback_string)
    """
    if not text:
        return ""

    # ERSTER Fehlertyp im Text suchen (nicht der letzte!)
    # Der erste ist meistens der relevante
    treffer_fehlertyp = _RE_FEHLERTYP.search(text)
    err_typ = treffer_fehlertyp.group(1) if treffer_fehlertyp else None

    # Über alle Muster suchen
    for regex, vorlage in _COMPILED:
        treffer = regex.search(text)
        if treffer:
            try:
                # Gruppen escapen für format()
                gruppen = _escape_format_groups(treffer.groups())
                deutsch = vorlage.format(*gruppen)
            except (IndexError, ValueError, KeyError) as e:
                # Fallback auf Original-Vorlage
                deutsch = vorlage
            typ_prefix = (err_typ + ":") if err_typ else "Fehler:"
            return f"{typ_prefix}\n\n{deutsch}"

    # Kein Muster gefunden → Originaltext
    typ_prefix = (err_typ + ":") if err_typ else "Unbekannter Fehler:"
    return (
        f"{typ_prefix} {text}\n\n"
        "──────────────────────────────\n"
        "Dieser Fehlertyp ist noch nicht übersetzt.\n"
        "Beschreibe ihn gerne – dann ergänze ich ihn."
    )

