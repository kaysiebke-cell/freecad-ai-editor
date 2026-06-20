# -*- coding: utf-8 -*-
"""FreeCAD-spezifische KI-Presets."""

FC_KI_PRESETS: dict[str, str] = {
    "── FreeCAD-Presets ──": "",

    "FC1 · FreeCAD-Makro erstellen":
        "Schreibe ein vollständiges FreeCAD-Python-Makro für folgende Aufgabe. "
        "Importiere App, Part und FreeCADGui korrekt. Füge am Ende doc.recompute() ein. "
        "Behandle den Fall, dass kein aktives Dokument geöffnet ist. "
        "Kommentiere alle wichtigen Schritte auf Deutsch.",

    "FC2 · Parametrisches Modell":
        "Wandle das Skript in ein parametrisches FreeCAD-Modell um. "
        "Alle Maße (Längen, Radien, Abstände) sollen als benannte Konstanten "
        "am Anfang der Datei stehen. Nutze App.ActiveDocument korrekt "
        "und rufe am Ende recompute() auf.",

    "FC3 · Part-Design Script":
        "Erstelle ein sauberes PartDesign-Script mit Body, Sketch-Geometrie "
        "und mindestens einem Pad oder Pocket. Nutze die PartDesign-API korrekt "
        "(body.newObject), vermeide veraltete Methoden und füge deutsche Kommentare ein.",

    "FC4 · Mesh-Verarbeitung":
        "Optimiere das Skript für Mesh-Import, -Analyse und -Export in FreeCAD. "
        "Prüfe ob die Datei existiert, behandle UnicodeDecodeError beim Lesen "
        "und gib Mesh-Statistiken (Facets, Volume, Area) aus.",

    "FC5 · GUI-Dialog hinzufügen":
        "Erweitere das Makro um einen PySide2/PySide6-kompatiblen QDialog "
        "für Benutzereingaben. Der Dialog soll OK/Abbrechen haben, "
        "alle Eingaben validieren und die Werte sicher an das Makro übergeben.",

    "FC6 · Selektions-basiertes Makro":
        "Überarbeite das Skript so, dass es auf der aktuellen FreeCAD-Selektion "
        "operiert. Prüfe explizit ob geeignete Objekte selektiert sind, "
        "gib klare deutsche Fehlermeldungen per QMessageBox aus "
        "und verarbeite nur Objekte des erwarteten TypeId.",

    "FC7 · FreeCAD-Fehlersuche":
        "Analysiere dieses FreeCAD-Makro auf typische Fehler: "
        "fehlende recompute()-Aufrufe, fehlendes None-Handling für ActiveDocument, "
        "falsche TypeId-Nutzung, PySide2/6-Inkompatibilitäten, "
        "Placement-Fehler und Race Conditions im GUI-Thread. "
        "Liste jeden Fehler mit Zeilennummer und Korrektur.",

    "FC8 · Workbench-Klasse":
        "Refaktoriere das Makro in eine wiederverwendbare FreeCAD-Workbench. "
        "Erstelle __init__.py mit InitGui, Command-Klassen mit GetResources, "
        "IsActive und Activated, sowie korrekter Gui.addCommand()-Registrierung.",

    "FC9 · STEP/IGES Export-Pipeline":
        "Erweitere das Skript um einen robusten STEP- und IGES-Export. "
        "Prüfe ob der Zielordner existiert, handle Import-Fehler bei fehlendem "
        "Import-Modul, und gib nach dem Export Dateigröße und Pfad aus.",

    "FC10 · Batch-Verarbeitung":
        "Wandle das Skript in ein Batch-Makro um, das alle FreeCAD-Dateien "
        "(.FCStd) in einem Verzeichnis nacheinander öffnet, verarbeitet und "
        "speichert. Zeige einen Fortschrittsbalken und protokolliere Fehler "
        "je Datei ohne den Gesamtdurchlauf abzubrechen.",

    "FC11 · Makro aus Beschreibung":
        "Beschreibe dein Objekt in normalen deutschen Worten – "
        "du musst kein FreeCAD-Experte sein. Beispiele: "
        "'Eine Halterung für ein 20mm Rohr', "
        "'Ein Deckel mit vier Schraubenlöchern', "
        "'Eine Schraube M8 50mm lang'. "
        "Die KI erstellt daraus ein fertiges Makro mit allen Maßen als "
        "Konstanten die du leicht anpassen kannst. "
        "Deine Beschreibung: ",

    "FC12 · PartDesign aus Beschreibung":
        "Beschreibe dein Objekt in normalen deutschen Worten. "
        "Die KI erstellt daraus ein PartDesign-Makro mit Body, Sketch und "
        "Pad/Pocket – so wie FreeCAD es für parametrische Modelle empfiehlt. "
        "Empfohlen: Claude oder GPT-4o als KI-Backend. "
        "Deine Beschreibung: ",

    "FC13 · Schrittweise aufbauen":
        "Beschreibe den nächsten Schritt für dein Bauteil. Der vorhandene Code im "
        "Editor wird als Kontext mitgeschickt – die KI hängt nur den neuen Block ans "
        "Ende, keine Dopplungen, kein Neustart. Dein nächster Schritt: ",

    "FC14 · Objekt-Befehle (lokal)":
        "Describe your object in plain English. "
        "Best for local Ollama models (qwen2.5-coder). "
        "The AI outputs simple commands (box, cylinder, fuse, cut …) "
        "which are automatically converted to FreeCAD Python code. "
        "Your description: ",
}
