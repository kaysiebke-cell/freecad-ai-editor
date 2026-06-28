# Skill: Schraubenlöcher (Fastener Holes)

Verwende diese Tabellen wenn der User Schraubenlöcher, Gewinde oder Senkungen erwähnt.
Alle Maße in mm. Für Part-Workbench: Zylinder-Radius = Durchmesser / 2.

## Durchgangslöcher (Clearance Holes — Schraube geht durch)

| Größe | Eng (enger Sitz) | Normal |
|-------|-------------------|--------|
| M2    | r=1.1             | r=1.2  |
| M2.5  | r=1.35            | r=1.45 |
| M3    | r=1.6             | r=1.7  |
| M4    | r=2.15            | r=2.25 |
| M5    | r=2.65            | r=2.75 |
| M6    | r=3.2             | r=3.3  |
| M8    | r=4.2             | r=4.5  |
| M10   | r=5.3             | r=5.5  |
| M12   | r=6.4             | r=6.6  |

## Kernlöcher (Tap Drill — für Gewinde schneiden)

| Größe | Radius  |
|-------|---------|
| M2    | r=0.8   |
| M2.5  | r=1.05  |
| M3    | r=1.25  |
| M4    | r=1.7   |
| M5    | r=2.1   |
| M6    | r=2.5   |
| M8    | r=3.35  |
| M10   | r=4.25  |
| M12   | r=5.1   |

## Versenkungen (Counterbore — Zylinderkopfschraube)

| Größe | CB-Radius | CB-Tiefe |
|-------|-----------|----------|
| M3    | r=3.25    | t=3.0    |
| M4    | r=4.0     | t=4.0    |
| M5    | r=5.0     | t=5.0    |
| M6    | r=5.75    | t=6.0    |
| M8    | r=7.5     | t=8.0    |
| M10   | r=9.0     | t=10.0   |

## Senkungen (Countersink — Senkkopfschraube, 90°)

| Größe | CS-Radius |
|-------|-----------|
| M3    | r=3.15    |
| M4    | r=4.2     |
| M5    | r=5.2     |
| M6    | r=6.3     |
| M8    | r=8.4     |
| M10   | r=10.5    |

## FreeCAD Part-Workbench Konstruktion

Durchgangsloch bei x=10, y=15 durch ein 10mm dickes Teil:
```python
loch = doc.addObject("Part::Cylinder", "M6_Loch")
loch.Radius = 3.3        # M6 Normal-Durchgang
loch.Height = 12         # etwas länger als Bauteil-Dicke
loch.Placement.Base = App.Vector(10, 15, -1)  # 1mm unterhalb beginnen

schnitt = doc.addObject("Part::Cut", "Bauteil_mit_Loch")
schnitt.Base = bauteil
schnitt.Tool = loch
doc.recompute()
```

Versenkung (Counterbore) M6:
```python
# Erst Durchgangsloch
loch = doc.addObject("Part::Cylinder", "M6_Loch")
loch.Radius = 3.3; loch.Height = 12
loch.Placement.Base = App.Vector(10, 15, -1)

# Dann Versenkung darüber
versenkung = doc.addObject("Part::Cylinder", "M6_CB")
versenkung.Radius = 5.75; versenkung.Height = 7   # CB-Tiefe 6mm + 1mm Überstand
versenkung.Placement.Base = App.Vector(10, 15, 4)  # oben auf dem Bauteil

# Beide vereinigen und ausschneiden
cb_shape = doc.addObject("Part::Fuse", "CB_Form")
cb_shape.Base = loch; cb_shape.Tool = versenkung
doc.recompute()

schnitt = doc.addObject("Part::Cut", "Bauteil_mit_CB")
schnitt.Base = bauteil; schnitt.Tool = cb_shape
doc.recompute()
```
