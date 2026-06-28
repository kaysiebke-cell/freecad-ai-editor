# -*- coding: utf-8 -*-
"""FreeCAD-spezifische KI-Presets."""

FC_KI_PRESETS: dict[str, str] = {

    # ── FreeCAD Code erstellen ────────────────────────────────────────────────
    "── FreeCAD: Code erstellen ──": "",

    "FC1 · FreeCAD-Makro erstellen":
        "Schreibe ein vollständiges FreeCAD-Python-Makro für folgende Aufgabe. "
        "Importiere App und Part korrekt. Füge am Ende doc.recompute() ein. "
        "Behandle den Fall dass kein aktives Dokument geöffnet ist. "
        "Alle Maße als Konstanten am Anfang. Reply only with Python code.",

    "FC2 · Parametrisches Modell":
        "Wandle das Skript in ein parametrisches FreeCAD-Modell um. "
        "Alle Maße (Längen, Radien, Abstände, Winkel) sollen als benannte Konstanten "
        "am Anfang der Datei stehen. Nutze App.ActiveDocument korrekt "
        "und rufe am Ende recompute() auf. Reply only with Python code.",

    "FC3 · Part-Modell (Grundkörper)":
        "Erstelle ein sauberes FreeCAD-Makro mit dem Part-Modul (nicht PartDesign). "
        "Nutze Part::Box, Part::Cylinder, Part::Sphere, Part::Cut und Part::Fuse. "
        "Setze Placement.Base korrekt für jedes Objekt. "
        "Alle Maße als Konstanten am Anfang. Kein PartDesign, kein Body, kein Sketch. "
        "Reply only with Python code.",

    "FC4 · Mesh-Verarbeitung":
        "Optimiere das Skript für Mesh-Import und -Export in FreeCAD. "
        "Prüfe ob die Datei existiert bevor du sie öffnest. "
        "Gib nach dem Export Dateipfad und Erfolgsmeldung aus. "
        "Reply only with Python code.",

    "FC6 · Selektions-Makro":
        "Überarbeite das Skript so dass es auf der aktuellen FreeCAD-Selektion arbeitet. "
        "Check whether at least one object is selected and otherwise output a clear "
        "error message. Reply only with Python code.",

    "FC9 · STEP-Export":
        "Erweitere das Skript um einen STEP-Export. "
        "Speichere die Datei im gleichen Ordner wie das FCStd-Dokument. "
        "Prüfe ob das Dokument einen Speicherpfad hat. "
        "Gib nach dem Export Dateipfad und Dateigröße aus. "
        "Reply only with Python code.",

    "FC10 · Batch-Verarbeitung":
        "Wandle das Skript in ein Batch-Makro um das alle FreeCAD-Dateien "
        "(.FCStd) in einem Verzeichnis nacheinander öffnet, verarbeitet und speichert. "
        "Protokolliere Fehler je Datei ohne den Gesamtdurchlauf abzubrechen. "
        "Reply only with Python code.",

    # ── Analyse & Erklärung ───────────────────────────────────────────────────
    "── Analyse & Erklärung ──": "",

    "FC7 · FreeCAD-Fehlersuche":
        "Analyse this FreeCAD macro for typical errors: "
        "missing recompute() calls, missing None-handling for ActiveDocument, "
        "wrong Placement values, wrong TypeId usage. "
        "List each error with line number and show the correction. "
        "Reply in English.",

    "LOK1 · Code erklären":
        "Explain this FreeCAD Python code in simple English. "
        "What does each section do? Which objects are created? "
        "Which dimensions are important and how can I adjust them? "
        "Explain so that beginners can understand too. Reply in English.",

    "LOK2 · Fehler erklären":
        "I have the following FreeCAD Python error. "
        "Explain in simple English what this error means "
        "and how to fix it. Show the corrected code if possible. "
        "Reply in English. My error: ",

    # ── Lokal / Ollama optimiert ──────────────────────────────────────────────
    "── Lokal (Ollama optimiert) ──": "",

    "FC11 · Makro aus Beschreibung":
        "Erstelle ein FreeCAD-Python-Makro. "
        "Nutze nur das Part-Modul (Part::Box, Part::Cylinder, Part::Cut, Part::Fuse). "
        "Alle Maße als Konstanten am Anfang. Kein PartDesign. "
        "Am Ende: doc.recompute() und fitAll(). "
        "Reply only with Python code, no explanation. "
        "My description: ",

    "FC13 · Schrittweise aufbauen":
        "Der vorhandene Code im Editor ist mein aktuelles Bauteil. "
        "Schreibe NUR den neuen Python-Code-Block für den nächsten Schritt, "
        "keine Wiederholung des bestehenden Codes, kein kompletter Neustart. "
        "Nutze die gleichen Variablennamen wie im bestehenden Code. "
        "Reply only with the new code block. My next step: ",

    "FC14 · Objekt-Befehle (lokal)":
        "Erstelle ein FreeCAD-Python-Makro für folgendes Objekt. "
        "Benutze nur einfache Part-Befehle: Box, Cylinder, Sphere, Cut, Fuse. "
        "Kein PartDesign, kein Sketch, keine GUI-Dialoge. "
        "Alle Maße als Konstanten am Anfang der Datei. "
        "Reply only with Python code. My object: ",

    "FC12 · PartDesign aus Beschreibung":
        "Erstelle ein FreeCAD-PartDesign-Makro mit Body, Sketch und Pad oder Pocket. "
        "Nutze FreeCAD.ActiveDocument.addObject('PartDesign::Body', ...) korrekt. "
        "Alle Maße als Konstanten. Am Ende recompute(). "
        "Reply only with Python code. My description: ",
}
