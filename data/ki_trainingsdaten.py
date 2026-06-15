# -*- coding: utf-8 -*-
"""
ki_trainingsdaten.py
─────────────────────
Few-Shot-Beispiele für die FreeCAD-KI.

Diese Datei enthält kuratierte Eingabe/Ausgabe-Paare (Few-Shot-Beispiele),
die als Teil des System-Prompts oder als In-Context-Training an die KI
übergeben werden. Dadurch „lernt" das Modell das exakte gewünschte Ausgabe-
format, ohne dass ein Fine-Tuning nötig ist.

Verwendung in ki_backends.py:
    from ki_trainingsdaten import FREECAD_FEW_SHOT, PARTDESIGN_FEW_SHOT

    system = _SYS_CODE + FREECAD_FEW_SHOT  # Part-Workbench
    system = _SYS_CODE + PARTDESIGN_FEW_SHOT  # PartDesign

Exportierte Konstanten:
  FREECAD_FEW_SHOT        – Few-Shot für Part-Makros (FC11)
  PARTDESIGN_FEW_SHOT     – Few-Shot für PartDesign-Makros (FC12)
  FEHLER_FEW_SHOT         – Few-Shot für Fehler-Erklärung
  REFACTOR_FEW_SHOT       – Few-Shot für Code-Refactoring
  WENIGE_BEISPIELE        – Kompakte Version (spart Token)
"""

# ══════════════════════════════════════════════════════════════════════════════
# Helfer
# ══════════════════════════════════════════════════════════════════════════════

def _beispiel(frage: str, antwort: str) -> str:
    """Formatiert ein Frage/Antwort-Paar als Few-Shot-Block."""
    return (
        f"\n\n━━━ BEISPIEL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"NUTZER: {frage.strip()}\n"
        f"ASSISTENT:\n{antwort.strip()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Few-Shot: Part-Workbench (FC11)
# ══════════════════════════════════════════════════════════════════════════════

_B1_FRAGE = "Erstelle einen Quader mit 50×30×20mm mit einem zentrierten Loch von 8mm Radius."

_B1_ANTWORT = """\
# -*- coding: utf-8 -*-
# Konstanten — hier alle Maße anpassen
LAENGE  = 50.0   # Länge in mm
BREITE  = 30.0   # Breite in mm
HOEHE   = 20.0   # Höhe in mm
RADIUS  =  8.0   # Radius des Lochs in mm

import FreeCAD as App

try:
    from PySide2.QtWidgets import QMessageBox
except ImportError:
    from PySide6.QtWidgets import QMessageBox

doc = App.ActiveDocument
if doc is None:
    doc = App.newDocument("Quader_mit_Loch")

try:
    box = doc.addObject("Part::Box", "Quader")
    box.Length = LAENGE
    box.Width  = BREITE
    box.Height = HOEHE

    zyl = doc.addObject("Part::Cylinder", "Bohrung")
    zyl.Radius = RADIUS
    zyl.Height = HOEHE * 2.0
    zyl.Placement.Base = App.Vector(LAENGE / 2, BREITE / 2, -HOEHE / 2)

    cut = doc.addObject("Part::Cut", "Quader_mit_Loch")
    cut.Base = box
    cut.Tool = zyl
    doc.recompute()
    print("Erstellt:", cut.Name)

except Exception as e:
    QMessageBox.critical(None, "Fehler", str(e))

Ein Quader (50×30×20 mm) mit einem zentrierten Durchgangsloch (Radius 8 mm) wurde erstellt. Das Loch wurde als Zylinder modelliert und per Part::Cut subtrahiert. Die Maße können oben in den Konstanten LAENGE, BREITE, HOEHE und RADIUS angepasst werden."""

_B2_FRAGE = "Vereinige eine Kugel mit einem Zylinder."

_B2_ANTWORT = """\
# -*- coding: utf-8 -*-
# Konstanten
KUGEL_RADIUS   = 15.0  # Kugelradius in mm
ZYL_RADIUS     = 10.0  # Zylinderradius in mm
ZYL_HOEHE      = 30.0  # Zylinderhöhe in mm

import FreeCAD as App

try:
    from PySide2.QtWidgets import QMessageBox
except ImportError:
    from PySide6.QtWidgets import QMessageBox

doc = App.ActiveDocument
if doc is None:
    doc = App.newDocument("Kugel_Zylinder")

try:
    kugel = doc.addObject("Part::Sphere", "Kugel")
    kugel.Radius = KUGEL_RADIUS

    zyl = doc.addObject("Part::Cylinder", "Zylinder")
    zyl.Radius = ZYL_RADIUS
    zyl.Height = ZYL_HOEHE
    zyl.Placement.Base = App.Vector(0, 0, -ZYL_HOEHE / 2)

    fuse = doc.addObject("Part::Fuse", "Vereinigung")
    fuse.Base  = kugel
    fuse.Tool  = zyl
    fuse.Refine = True
    doc.recompute()
    print("Erstellt:", fuse.Name)

except Exception as e:
    QMessageBox.critical(None, "Fehler", str(e))

Kugel (R=15 mm) und Zylinder (R=10 mm, H=30 mm) wurden mittig überlagert und vereinigt. Der Zylinder wurde um die halbe Höhe nach unten verschoben damit er durch den Kugelmittelpunkt verläuft. KUGEL_RADIUS, ZYL_RADIUS und ZYL_HOEHE sind oben anpassbar."""


FREECAD_FEW_SHOT: str = (
    "\n\n━━━ FEW-SHOT-BEISPIELE (Part-Workbench) ━━━━━━━━━━━━━━━━━━━━━━━━"
    + _beispiel(_B1_FRAGE, _B1_ANTWORT)
    + _beispiel(_B2_FRAGE, _B2_ANTWORT)
    + "\n━━━ ENDE DER BEISPIELE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
)


# ══════════════════════════════════════════════════════════════════════════════
# Few-Shot: PartDesign (FC12)
# ══════════════════════════════════════════════════════════════════════════════

_PD1_FRAGE = "Erstelle eine 40×25mm Platte mit 10mm Dicke als PartDesign-Makro."

_PD1_ANTWORT = """\
# -*- coding: utf-8 -*-
# Konstanten
LAENGE = 40.0  # Länge in mm
BREITE = 25.0  # Breite in mm
DICKE  = 10.0  # Pad-Dicke in mm

import FreeCAD as App
import Part
import Sketcher

try:
    from PySide2.QtWidgets import QMessageBox
except ImportError:
    from PySide6.QtWidgets import QMessageBox

doc = App.ActiveDocument
if doc is None:
    doc = App.newDocument("Platte")

try:
    body = doc.addObject("PartDesign::Body", "Koerper")

    sketch = doc.addObject("Sketcher::SketchObject", "Profil")
    body.addObject(sketch)
    sketch.MapMode = "FlatFace"
    sketch.Support = (doc.getObject("XY_Plane"), [""])

    sketch.addGeometry(Part.LineSegment(App.Vector(0,0,0),         App.Vector(LAENGE,0,0)),      False)
    sketch.addGeometry(Part.LineSegment(App.Vector(LAENGE,0,0),    App.Vector(LAENGE,BREITE,0)), False)
    sketch.addGeometry(Part.LineSegment(App.Vector(LAENGE,BREITE,0), App.Vector(0,BREITE,0)),    False)
    sketch.addGeometry(Part.LineSegment(App.Vector(0,BREITE,0),    App.Vector(0,0,0)),           False)

    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1))
    sketch.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, LAENGE))
    sketch.addConstraint(Sketcher.Constraint("DistanceY", 1, 1, 1, 2, BREITE))
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Platte")
    pad.Profile = sketch
    pad.Length  = DICKE
    doc.recompute()
    print("Erstellt:", pad.Name)

except Exception as e:
    QMessageBox.critical(None, "Fehler", str(e))

Eine parametrische Platte (40×25 mm, 10 mm Dicke) wurde als PartDesign-Makro mit Body, Sketch und Pad erstellt. Das Rechteck wurde mit vier Coincident-Constraints und zwei Maß-Constraints vollständig definiert. LAENGE, BREITE und DICKE oben anpassen um das Modell zu ändern."""


PARTDESIGN_FEW_SHOT: str = (
    "\n\n━━━ FEW-SHOT-BEISPIELE (PartDesign) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    + _beispiel(_PD1_FRAGE, _PD1_ANTWORT)
    + "\n━━━ ENDE DER BEISPIELE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
)


# ══════════════════════════════════════════════════════════════════════════════
# Few-Shot: Fehler-Erklärung
# ══════════════════════════════════════════════════════════════════════════════

_F1_FRAGE = """\
Erkläre diesen FreeCAD-Fehler:
AttributeError: 'NoneType' object has no attribute 'addObject'
Code-Zeile: box = doc.addObject("Part::Box", "Quader")"""

_F1_ANTWORT = """\
Das Problem: `doc` ist `None`, weil kein FreeCAD-Dokument geöffnet ist.

Ursache: `App.ActiveDocument` gibt `None` zurück wenn kein Dokument aktiv ist.

Lösung:
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("MeinDokument")   # Neues Dokument erstellen
    box = doc.addObject("Part::Box", "Quader")

Prüfen Sie vor jedem `addObject()`-Aufruf ob `doc` nicht `None` ist."""


FEHLER_FEW_SHOT: str = (
    "\n\n━━━ FEW-SHOT-BEISPIEL (Fehler-Erklärung) ━━━━━━━━━━━━━━━━━━━━━━━"
    + _beispiel(_F1_FRAGE, _F1_ANTWORT)
    + "\n━━━ ENDE DER BEISPIELE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
)


# ══════════════════════════════════════════════════════════════════════════════
# Few-Shot: Refactoring
# ══════════════════════════════════════════════════════════════════════════════

_R1_FRAGE = """\
Wandle diesen Code in ein parametrisches Makro um:
    box = doc.addObject("Part::Box", "Quader")
    box.Length = 50
    box.Width = 30
    box.Height = 20"""

_R1_ANTWORT = """\
# -*- coding: utf-8 -*-
# Konstanten — hier alle Maße anpassen
LAENGE = 50.0  # Länge in mm
BREITE = 30.0  # Breite in mm
HOEHE  = 20.0  # Höhe in mm

import FreeCAD as App

doc = App.ActiveDocument
if doc is None:
    doc = App.newDocument("Quader")

box = doc.addObject("Part::Box", "Quader")
box.Length = LAENGE
box.Width  = BREITE
box.Height = HOEHE
doc.recompute()

Alle Maße wurden als benannte Konstanten (LAENGE, BREITE, HOEHE) an den Dateianfang verschoben. Ein Dokument-Null-Check wurde hinzugefügt. Das fehlende doc.recompute() wurde ergänzt."""


REFACTOR_FEW_SHOT: str = (
    "\n\n━━━ FEW-SHOT-BEISPIEL (Refactoring) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    + _beispiel(_R1_FRAGE, _R1_ANTWORT)
    + "\n━━━ ENDE DER BEISPIELE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
)


# ══════════════════════════════════════════════════════════════════════════════
# Kompakte Version (spart Token für schwache/lokale Modelle)
# ══════════════════════════════════════════════════════════════════════════════

WENIGE_BEISPIELE: str = """\

━━━ KOMPAKT-BEISPIEL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NUTZER: Erstelle einen Würfel 30mm.
ASSISTENT:
# -*- coding: utf-8 -*-
SEITE = 30.0  # Kantenlänge in mm
import FreeCAD as App
doc = App.ActiveDocument or App.newDocument()
w = doc.addObject("Part::Box", "Wuerfel")
w.Length = w.Width = w.Height = SEITE
doc.recompute()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
