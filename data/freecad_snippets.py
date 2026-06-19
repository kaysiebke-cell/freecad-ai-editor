# -*- coding: utf-8 -*-
"""FreeCAD-Codevorlagen nach Kategorie."""

SNIPPETS: dict[str, dict[str, str]] = {

    "📄 Dokument": {
        "Neues Dokument erstellen": """\
import FreeCAD as App

doc = App.newDocument("MeinDokument")
App.setActiveDocument("MeinDokument")
print("Dokument erstellt:", doc.Name)
""",
        "Aktives Dokument prüfen": """\
import FreeCAD as App

doc = App.ActiveDocument
if doc is None:
    raise RuntimeError("Kein aktives Dokument geöffnet.")
print("Aktives Dokument:", doc.Name)
""",
        "Dokument speichern": """\
import FreeCAD as App

doc = App.ActiveDocument
doc.save()
# Alternativ: doc.saveAs("/pfad/zur/datei.FCStd")
print("Gespeichert.")
""",
        "Alle Objekte auflisten": """\
import FreeCAD as App

doc = App.ActiveDocument
for obj in doc.Objects:
    print(f"{obj.Name:30s}  {obj.TypeId}")
""",
        "Objekt per Name holen": """\
import FreeCAD as App

doc = App.ActiveDocument
name = "MeinObjekt"
obj = doc.getObject(name)
if obj is None:
    raise ValueError(f"Objekt '{name}' nicht gefunden.")
print("Gefunden:", obj.Label)
""",
    },

    "🔷 Part": {
        "Box erstellen": """\
import FreeCAD as App

doc = App.ActiveDocument or App.newDocument()
box = doc.addObject("Part::Box", "MeineBox")
box.Length = 20.0   # mm
box.Width  = 15.0
box.Height = 10.0
doc.recompute()
""",
        "Zylinder erstellen": """\
import FreeCAD as App

doc = App.ActiveDocument or App.newDocument()
zyl = doc.addObject("Part::Cylinder", "MeinZylinder")
zyl.Radius = 8.0
zyl.Height = 25.0
doc.recompute()
""",
        "Kugel erstellen": """\
import FreeCAD as App

doc = App.ActiveDocument or App.newDocument()
kugel = doc.addObject("Part::Sphere", "MeineKugel")
kugel.Radius = 12.0
doc.recompute()
""",
        "Kegel erstellen": """\
import FreeCAD as App

doc = App.ActiveDocument or App.newDocument()
kegel = doc.addObject("Part::Cone", "MeinKegel")
kegel.Radius1 = 10.0   # Basis-Radius
kegel.Radius2 =  0.0   # Spitze (0 = echter Kegel)
kegel.Height  = 30.0
doc.recompute()
""",
        "Torus erstellen": """\
import FreeCAD as App

doc = App.ActiveDocument or App.newDocument()
torus = doc.addObject("Part::Torus", "MeinTorus")
torus.Radius1 = 20.0   # Ring-Radius
torus.Radius2 =  5.0   # Rohr-Radius
doc.recompute()
""",
        "Boolean Union (Vereinigung)": """\
import FreeCAD as App

doc = App.ActiveDocument
fusion = doc.addObject("Part::Fuse", "Vereinigung")
fusion.Base = doc.getObject("Box")
fusion.Tool = doc.getObject("Cylinder")
fusion.Refine = True
doc.recompute()
""",
        "Boolean Cut (Subtraktion)": """\
import FreeCAD as App

doc = App.ActiveDocument
cut = doc.addObject("Part::Cut", "Schnitt")
cut.Base = doc.getObject("Box")
cut.Tool = doc.getObject("Cylinder")
doc.recompute()
""",
        "Boolean Common (Durchschnitt)": """\
import FreeCAD as App

doc = App.ActiveDocument
common = doc.addObject("Part::Common", "Durchschnitt")
common.Base = doc.getObject("Box")
common.Tool = doc.getObject("Cylinder")
doc.recompute()
""",
        "Extrude aus Polygon": """\
import FreeCAD as App
import Part

# Rechteck als Wire definieren
p = [App.Vector(x, y, 0) for x, y in
     [(0,0),(20,0),(20,10),(0,10),(0,0)]]
wire  = Part.makePolygon(p)
face  = Part.Face(wire)
solid = face.extrude(App.Vector(0, 0, 15))
Part.show(solid)
App.ActiveDocument.recompute()
""",
        "Shape aus Datei laden": """\
import FreeCAD as App
import Part

pfad = "/pfad/zur/datei.step"   # STEP, IGES, STL …
shape = Part.Shape()
shape.read(pfad)
doc = App.ActiveDocument or App.newDocument()
obj = doc.addObject("Part::Feature", "ImportShape")
obj.Shape = shape
doc.recompute()
""",
        "Fillet (Verrundung)": """\
import FreeCAD as App

doc = App.ActiveDocument
fillet = doc.addObject("Part::Fillet", "Verrundung")
fillet.Base = doc.getObject("MeinObjekt")
# Kanten-Index + (min_radius, max_radius)
fillet.Edges = [(1, 2.0, 2.0), (2, 2.0, 2.0)]
doc.recompute()
""",
        "Chamfer (Fase)": """\
import FreeCAD as App

doc = App.ActiveDocument
chamfer = doc.addObject("Part::Chamfer", "Fase")
chamfer.Base = doc.getObject("MeinObjekt")
chamfer.Edges = [(1, 1.0, 1.0)]
doc.recompute()
""",
    },

    "✏️ Sketcher": {
        "Neuen Sketch erstellen (XY)": """\
import FreeCAD as App

doc = App.ActiveDocument or App.newDocument()
sketch = doc.addObject("Sketcher::SketchObject", "MeinSketch")
# Placement auf der XY-Ebene (Standard)
sketch.Placement = App.Placement(
    App.Vector(0, 0, 0),
    App.Rotation(App.Vector(0, 0, 1), 0)
)
doc.recompute()
""",
        "Linie im Sketch": """\
import FreeCAD as App
import Part

sketch = App.ActiveDocument.getObject("MeinSketch")
sketch.addGeometry(
    Part.LineSegment(
        App.Vector(0,  0, 0),
        App.Vector(20, 0, 0)
    ), False
)
App.ActiveDocument.recompute()
""",
        "Kreis im Sketch": """\
import FreeCAD as App
import Part

sketch = App.ActiveDocument.getObject("MeinSketch")
sketch.addGeometry(
    Part.Circle(
        App.Vector(0, 0, 0),    # Mittelpunkt
        App.Vector(0, 0, 1),    # Normale
        10.0                    # Radius
    ), False
)
App.ActiveDocument.recompute()
""",
        "Rechteck im Sketch": """\
import FreeCAD as App
import Part

sketch = App.ActiveDocument.getObject("MeinSketch")
b, h = 20.0, 10.0
punkte = [
    App.Vector(0, 0, 0), App.Vector(b, 0, 0),
    App.Vector(b, h, 0), App.Vector(0, h, 0),
]
for i in range(4):
    sketch.addGeometry(
        Part.LineSegment(punkte[i], punkte[(i+1) % 4]), False
    )
App.ActiveDocument.recompute()
""",
        "Constraint Horizontal": """\
import Sketcher
sketch = App.ActiveDocument.getObject("MeinSketch")
sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
App.ActiveDocument.recompute()
""",
        "Constraint Vertikal": """\
import Sketcher
sketch = App.ActiveDocument.getObject("MeinSketch")
sketch.addConstraint(Sketcher.Constraint("Vertical", 0))
App.ActiveDocument.recompute()
""",
        "Constraint DistanceX": """\
import Sketcher
sketch = App.ActiveDocument.getObject("MeinSketch")
# Geo-Index 0, Punkt 1 → Punkt 2, Abstand 20 mm
sketch.addConstraint(
    Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 20.0)
)
App.ActiveDocument.recompute()
""",
        "Sketch → Pad (PartDesign)": """\
import FreeCAD as App

doc = App.ActiveDocument
body   = doc.addObject("PartDesign::Body", "Body")
sketch = doc.getObject("MeinSketch")
body.addObject(sketch)
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length  = 15.0
doc.recompute()
""",
        "Sketch → Pocket (PartDesign)": """\
import FreeCAD as App

doc = App.ActiveDocument
body   = doc.getObject("Body")
sketch = doc.getObject("MeinSketch")
pocket = body.newObject("PartDesign::Pocket", "Pocket")
pocket.Profile = sketch
pocket.Length  = 5.0
doc.recompute()
""",
    },

    "🕸️ Mesh": {
        "STL importieren": """\
import FreeCAD as App
import Mesh

pfad = "/pfad/zur/datei.stl"
Mesh.insert(pfad)
App.ActiveDocument.recompute()
""",
        "STL exportieren": """\
import FreeCAD as App
import Mesh

obj  = App.ActiveDocument.getObject("MeinMesh")
pfad = "/pfad/ausgabe.stl"
Mesh.export([obj], pfad)
print("Exportiert nach:", pfad)
""",
        "Mesh programmatisch erstellen": """\
import FreeCAD as App
import Mesh

v = [App.Vector(*p) for p in
     [(0,0,0),(10,0,0),(5,10,0),(5,5,10)]]
dreiecke = [(0,1,2),(0,1,3),(1,2,3),(0,2,3)]
mesh = Mesh.Mesh()
for d in dreiecke:
    mesh.addFacet(v[d[0]], v[d[1]], v[d[2]])
doc = App.ActiveDocument or App.newDocument()
obj = doc.addObject("Mesh::Feature", "MeinMesh")
obj.Mesh = mesh
doc.recompute()
""",
        "Mesh → Part (Shape)": """\
import FreeCAD as App
import Part
import MeshPart

mesh_obj = App.ActiveDocument.getObject("MeinMesh")
shape = MeshPart.meshToShape(mesh_obj.Mesh)
Part.show(shape)
App.ActiveDocument.recompute()
""",
        "Mesh-Infos ausgeben": """\
import FreeCAD as App

obj = App.ActiveDocument.getObject("MeinMesh")
m = obj.Mesh
print("Facets :", m.CountFacets)
print("Punkte :", m.CountPoints)
print("Volumen:", m.Volume)
print("Fläche :", m.Area)
""",
    },

    "📐 Draft": {
        "Linie zeichnen": """\
import FreeCAD as App
import Draft

linie = Draft.make_line(
    App.Vector(0,   0, 0),
    App.Vector(100, 50, 0)
)
App.ActiveDocument.recompute()
""",
        "Rechteck zeichnen": """\
import FreeCAD as App
import Draft

rect = Draft.make_rectangle(length=200, height=100)
rect.Placement.Base = App.Vector(0, 0, 0)
App.ActiveDocument.recompute()
""",
        "Kreis zeichnen": """\
import FreeCAD as App
import Draft

kreis = Draft.make_circle(radius=50)
App.ActiveDocument.recompute()
""",
        "BSpline-Kurve": """\
import FreeCAD as App
import Draft

punkte = [
    App.Vector(  0,  0, 0),
    App.Vector( 30, 40, 0),
    App.Vector( 60, 10, 0),
    App.Vector(100, 50, 0),
]
spline = Draft.make_bspline(punkte, closed=False)
App.ActiveDocument.recompute()
""",
        "Polygon (regelmäßig)": """\
import FreeCAD as App
import Draft

poly = Draft.make_polygon(
    nfaces=6,           # Sechseck
    radius=30
)
App.ActiveDocument.recompute()
""",
        "Text einfügen": """\
import FreeCAD as App
import Draft

pos  = App.Vector(0, 0, 0)
text = Draft.make_text(["Zeile 1", "Zeile 2"], pos)
App.ActiveDocument.recompute()
""",
        "Objekt klonen": """\
import FreeCAD as App
import Draft

original = App.ActiveDocument.getObject("MeinObjekt")
klon = Draft.make_clone(original,
                        delta=App.Vector(30, 0, 0))
App.ActiveDocument.recompute()
""",
        "Array erstellen": """\
import FreeCAD as App
import Draft

basis = App.ActiveDocument.getObject("MeinObjekt")
arr = Draft.make_ortho_array(
    base=basis,
    v_x=App.Vector(30,  0, 0),  # Schritt X
    v_y=App.Vector( 0, 30, 0),  # Schritt Y
    v_z=App.Vector( 0,  0, 0),
    n_x=3, n_y=3, n_z=1
)
App.ActiveDocument.recompute()
""",
    },

    "🎯 Selektion": {
        "Auswahl abfragen": """\
import FreeCADGui as Gui

auswahl = Gui.Selection.getSelection()
if not auswahl:
    print("Nichts ausgewählt.")
else:
    for obj in auswahl:
        print(f"  {obj.Name:25s}  {obj.TypeId}")
""",
        "Sub-Elemente abfragen": """\
import FreeCADGui as Gui

for sel in Gui.Selection.getSelectionEx():
    print("Objekt:", sel.ObjectName)
    for sub in sel.SubElementNames:
        print("  →", sub)
""",
        "Objekt selektieren": """\
import FreeCAD as App
import FreeCADGui as Gui

Gui.Selection.clearSelection()
Gui.Selection.addSelection(
    App.ActiveDocument.Name, "MeinObjekt"
)
""",
        "Alle Objekte eines Typs finden": """\
import FreeCAD as App

doc = App.ActiveDocument
typ = "Part::Box"
gefunden = [o for o in doc.Objects if o.TypeId == typ]
print(f"{len(gefunden)} Objekt(e) vom Typ {typ}:")
for o in gefunden:
    print(" ", o.Name)
""",
        "Selektion aufheben": """\
import FreeCADGui as Gui
Gui.Selection.clearSelection()
""",
    },

    "🔧 Placement & Transform": {
        "Objekt verschieben": """\
import FreeCAD as App

obj = App.ActiveDocument.getObject("MeinObjekt")
obj.Placement.Base = App.Vector(10, 20, 30)
App.ActiveDocument.recompute()
""",
        "Objekt rotieren (Achse + Winkel)": """\
import FreeCAD as App

obj = App.ActiveDocument.getObject("MeinObjekt")
obj.Placement.Rotation = App.Rotation(
    App.Vector(0, 0, 1),    # Achse (Z)
    45.0                    # Winkel in Grad
)
App.ActiveDocument.recompute()
""",
        "Placement kombinieren": """\
import FreeCAD as App

obj = App.ActiveDocument.getObject("MeinObjekt")
pos = App.Vector(10, 0, 0)
rot = App.Rotation(App.Vector(0, 0, 1), 90)
obj.Placement = App.Placement(pos, rot)
App.ActiveDocument.recompute()
""",
        "Bounding Box ausgeben": """\
import FreeCAD as App

obj = App.ActiveDocument.getObject("MeinObjekt")
bb = obj.Shape.BoundBox
print(f"X: {bb.XMin:.2f} … {bb.XMax:.2f}  ΔX={bb.XLength:.2f}")
print(f"Y: {bb.YMin:.2f} … {bb.YMax:.2f}  ΔY={bb.YLength:.2f}")
print(f"Z: {bb.ZMin:.2f} … {bb.ZMax:.2f}  ΔZ={bb.ZLength:.2f}")
""",
        "Objekt spiegeln": """\
import FreeCAD as App
import Part

obj   = App.ActiveDocument.getObject("MeinObjekt")
shape = obj.Shape
# An der YZ-Ebene spiegeln (X → -X)
spiegel = shape.mirror(App.Vector(0,0,0), App.Vector(1,0,0))
Part.show(spiegel)
App.ActiveDocument.recompute()
""",
    },

    "🖥️ GUI & View": {
        "Isometrische Ansicht + Einpassen": """\
import FreeCADGui as Gui

view = Gui.ActiveDocument.ActiveView
view.viewIsometric()
view.fitAll()
""",
        "Standardansichten": """\
import FreeCADGui as Gui

view = Gui.ActiveDocument.ActiveView
# view.viewTop()    # Draufsicht
# view.viewFront()  # Vorderansicht
# view.viewRight()  # Rechtsansicht
view.viewIsometric()
""",
        "Farbe und Transparenz setzen": """\
import FreeCADGui as Gui

vobj = Gui.ActiveDocument.getObject("MeinObjekt")
vobj.ShapeColor   = (0.2, 0.6, 1.0)   # RGB 0..1
vobj.Transparency = 30                 # 0 (opak) … 100 (unsichtbar)
""",
        "Sichtbarkeit umschalten": """\
import FreeCADGui as Gui

vobj = Gui.ActiveDocument.getObject("MeinObjekt")
vobj.Visibility = not vobj.Visibility
""",
        "Alle Objekte einblenden": """\
import FreeCAD as App
import FreeCADGui as Gui

for obj in App.ActiveDocument.Objects:
    vobj = Gui.ActiveDocument.getObject(obj.Name)
    if vobj:
        vobj.Visibility = True
""",
        "Screenshot speichern": """\
import FreeCADGui as Gui

pfad = "/tmp/screenshot.png"
Gui.ActiveDocument.ActiveView.saveImage(
    pfad, 1920, 1080, "White"
)
print("Screenshot:", pfad)
""",
        "Fortschrittsbalken": """\
import FreeCAD as App

pi = App.Base.ProgressIndicator
pi.start("Verarbeitung läuft …", 100)
try:
    for i in range(100):
        pi.next(True)   # True = abbrechbar
        # ... eigene Arbeit ...
finally:
    pi.stop()
""",
    },
}
