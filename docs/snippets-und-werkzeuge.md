[← Zurück: Makro aus Beschreibung](makro-generator.md) | [Zur README](../README.md) | Weiter: [Makro-Bibliothek →](makro-bibliothek.md)

# Snippets & API-Hints

## Snippet-Kategorien
- 📄 **Dokument** – Dokument anlegen/laden/speichern, Objekte abfragen
- 🔷 **Part** – Box, Zylinder, Boolean, Placement, Shape-Operationen
- 📐 **Sketcher** – Sketch erstellen, Constraints, Geometrie
- 🕸 **Mesh** – Mesh importieren/exportieren, konvertieren
- 📏 **Draft** – Linien, Kreise, Bemaßungen
- 🧩 **PartDesign** – Body, Feature-Kette, Pad, Pocket

## API-Hints Bereiche
- `App.*` – Dokument, Objekte, Einstellungen
- `Part.*` – Shapes, Operationen, Geometrie
- `Sketcher.*` – Constraints, Geometrie
- `Mesh.*` – Import/Export, Verarbeitung
- `Draft.*` – 2D-Operationen
- `Placement`, `Vector`, `Rotation`
- `Gui.*`, `FreeCADGui.*` – View, Selection

---

# Werkzeuge-Panel

## Direktoperationen (ohne Code schreiben)

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

[← Zurück: Makro aus Beschreibung](makro-generator.md) | [Zur README](../README.md) | Weiter: [Makro-Bibliothek →](makro-bibliothek.md)
