# -*- coding: utf-8 -*-
"""FreeCAD-spezifische KI-Presets."""

FC_KI_PRESETS: dict[str, str] = {

    # ── FreeCAD Code erstellen ────────────────────────────────────────────────
    "── FreeCAD: Code erstellen ──": "",

    "FC1 · FreeCAD-Makro erstellen":
        "Schreibe ein vollständiges FreeCAD-Python-Makro für folgende Aufgabe. "
        "Importiere App und Part korrekt. Füge am Ende doc.recompute() ein. "
        "Behandle den Fall dass kein aktives Dokument geöffnet ist. "
        "Alle Maße als Konstanten am Anfang. Antworte nur mit Python-Code.",

    "FC2 · Parametrisches Modell":
        "Wandle das Skript in ein parametrisches FreeCAD-Modell um. "
        "Alle Maße (Längen, Radien, Abstände, Winkel) sollen als benannte Konstanten "
        "am Anfang der Datei stehen. Nutze App.ActiveDocument korrekt "
        "und rufe am Ende recompute() auf. Antworte nur mit Python-Code.",

    "FC3 · Part-Modell (Grundkörper)":
        "Erstelle ein sauberes FreeCAD-Makro mit dem Part-Modul (nicht PartDesign). "
        "Nutze Part::Box, Part::Cylinder, Part::Sphere, Part::Cut und Part::Fuse. "
        "Setze Placement.Base korrekt für jedes Objekt. "
        "Alle Maße als Konstanten am Anfang. Kein PartDesign, kein Body, kein Sketch. "
        "Antworte nur mit Python-Code.",

    "FC4 · Mesh-Verarbeitung":
        "Optimiere das Skript für Mesh-Import und -Export in FreeCAD. "
        "Prüfe ob die Datei existiert bevor du sie öffnest. "
        "Gib nach dem Export Dateipfad und Erfolgsmeldung aus. "
        "Antworte nur mit Python-Code.",

    "FC6 · Selektions-Makro":
        "Überarbeite das Skript so dass es auf der aktuellen FreeCAD-Selektion arbeitet. "
        "Prüfe ob mindestens ein Objekt selektiert ist und gib sonst eine klare "
        "deutsche Fehlermeldung aus. Antworte nur mit Python-Code.",

    "FC9 · STEP-Export":
        "Erweitere das Skript um einen STEP-Export. "
        "Speichere die Datei im gleichen Ordner wie das FCStd-Dokument. "
        "Prüfe ob das Dokument einen Speicherpfad hat. "
        "Gib nach dem Export Dateipfad und Dateigröße aus. "
        "Antworte nur mit Python-Code.",

    "FC10 · Batch-Verarbeitung":
        "Wandle das Skript in ein Batch-Makro um das alle FreeCAD-Dateien "
        "(.FCStd) in einem Verzeichnis nacheinander öffnet, verarbeitet und speichert. "
        "Protokolliere Fehler je Datei ohne den Gesamtdurchlauf abzubrechen. "
        "Antworte nur mit Python-Code.",

    # ── Analyse & Erklärung ───────────────────────────────────────────────────
    "── Analyse & Erklärung ──": "",

    "FC7 · FreeCAD-Fehlersuche":
        "Analysiere dieses FreeCAD-Makro auf typische Fehler: "
        "fehlende recompute()-Aufrufe, fehlendes None-Handling für ActiveDocument, "
        "falsche Placement-Werte, falsche TypeId-Nutzung. "
        "Liste jeden Fehler mit Zeilennummer und zeige die Korrektur. "
        "Antworte auf Deutsch.",

    "LOK1 · Code erklären":
        "Erkläre diesen FreeCAD-Python-Code auf einfachem Deutsch. "
        "Was macht jeder Abschnitt? Welche Objekte werden erstellt? "
        "Welche Maße sind wichtig und wie kann ich sie anpassen? "
        "Erkläre so dass auch Anfänger es verstehen. Antworte auf Deutsch.",

    "LOK2 · Fehler erklären":
        "Ich habe folgenden FreeCAD-Python-Fehler. "
        "Erkläre auf einfachem Deutsch was dieser Fehler bedeutet "
        "und wie ich ihn behebe. Zeige wenn möglich den korrigierten Code. "
        "Antworte auf Deutsch. Mein Fehler: ",

    # ── Lokal / Ollama optimiert ──────────────────────────────────────────────
    "── Lokal (Ollama optimiert) ──": "",

    "FC11 · Makro aus Beschreibung":
        "Erstelle ein FreeCAD-Python-Makro. "
        "Nutze nur das Part-Modul (Part::Box, Part::Cylinder, Part::Cut, Part::Fuse). "
        "Alle Maße als Konstanten am Anfang. Kein PartDesign. "
        "Am Ende: doc.recompute() und fitAll(). "
        "Antworte nur mit Python-Code ohne Erklärung. "
        "Meine Beschreibung: ",

    "FC13 · Schrittweise aufbauen":
        "Der vorhandene Code im Editor ist mein aktuelles Bauteil. "
        "Schreibe NUR den neuen Python-Code-Block für den nächsten Schritt, "
        "keine Wiederholung des bestehenden Codes, kein kompletter Neustart. "
        "Nutze die gleichen Variablennamen wie im bestehenden Code. "
        "Antworte nur mit dem neuen Code-Block. Mein nächster Schritt: ",

    "FC14 · Objekt-Befehle (lokal)":
        "Erstelle ein FreeCAD-Python-Makro für folgendes Objekt. "
        "Benutze nur einfache Part-Befehle: Box, Cylinder, Sphere, Cut, Fuse. "
        "Kein PartDesign, kein Sketch, keine GUI-Dialoge. "
        "Alle Maße als Konstanten am Anfang der Datei. "
        "Antworte nur mit Python-Code. Mein Objekt: ",

    "FC12 · PartDesign aus Beschreibung":
        "Erstelle ein FreeCAD-PartDesign-Makro mit Body, Sketch und Pad oder Pocket. "
        "Nutze FreeCAD.ActiveDocument.addObject('PartDesign::Body', ...) korrekt. "
        "Alle Maße als Konstanten. Am Ende recompute(). "
        "Antworte nur mit Python-Code. Meine Beschreibung: ",
}
