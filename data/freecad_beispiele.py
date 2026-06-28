# -*- coding: utf-8 -*-
"""
freecad_beispiele.py
─────────────────────────────────────────────────────────────────────────────
Aufgabe → korrekter FreeCAD-Python-Code Beispiele (Few-Shot RAG für Ollama).

Scoring-Gewichtung:
  exakter Tag-Treffer        = 5 Punkte
  Alias-Treffer (DE↔EN)      = 3 Punkte
  Teilwort-Treffer           = 1 Punkt

Verwendung: beispiele_finden(aufgabe_text) in ki_anfrage.py
"""

# ── Jeder Eintrag: tags (Suchwörter), aufgabe (Beschreibung), code ─────────

FC_BEISPIELE: list[dict] = [

    # ══════════════════════════════════════════════════════════════════════════
    # GRUNDFORMEN
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "quader", "box", "würfel", "rechteck", "kasten", "block",
            "platte", "träger", "balken", "leiste", "rechteckig", "prisma", "bauteil",
        ],
        "aufgabe": "Einfacher Quader 80×50×30mm",
        "code": """\
# -*- coding: utf-8 -*-
LAENGE = 80.0; BREITE = 50.0; HOEHE = 30.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
box = doc.addObject("Part::Box", "Quader")
box.Length = LAENGE; box.Width = BREITE; box.Height = HOEHE
doc.recompute()"""
    },

    {
        "tags": [
            "zylinder", "cylinder", "walze", "rund", "roehre", "stab",
            "welle", "achse", "säule", "zylindrisch", "kreisrund",
            "rundstab", "bolzen",
        ],
        "aufgabe": "Einfacher Zylinder Radius 20mm, Höhe 60mm",
        "code": """\
# -*- coding: utf-8 -*-
RADIUS = 20.0; HOEHE = 60.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
zyl = doc.addObject("Part::Cylinder", "Zylinder")
zyl.Radius = RADIUS
zyl.Height = HOEHE
doc.recompute()"""
    },

    {
        "tags": [
            "kugel", "sphere", "ball", "kugelform", "rund", "kugelförmig",
            "halbkugel", "kugelkopf",
        ],
        "aufgabe": "Kugel mit Radius 35mm",
        "code": """\
# -*- coding: utf-8 -*-
RADIUS = 35.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
kugel = doc.addObject("Part::Sphere", "Kugel")
kugel.Radius = RADIUS
doc.recompute()"""
    },

    {
        "tags": [
            "kegel", "cone", "spitze", "spitzkegel", "pyramide rund",
            "kegelspitze", "verjüngung", "kegelförmig",
        ],
        "aufgabe": "Spitzkegel Radius 25mm unten, Höhe 50mm",
        "code": """\
# -*- coding: utf-8 -*-
R_UNTEN = 25.0; R_OBEN = 0.0; HOEHE = 50.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
kegel = doc.addObject("Part::Cone", "Kegel")
kegel.Radius1 = R_UNTEN   # untere Grundfläche
kegel.Radius2 = R_OBEN    # 0 = Spitze
kegel.Height = HOEHE
doc.recompute()"""
    },

    {
        "tags": [
            "kegelstumpf", "stumpf", "kegel", "cone", "abgeschnitten",
            "trapez rund", "verjüngung", "reduzierung", "übergang",
        ],
        "aufgabe": "Kegelstumpf: Radius unten 30mm, Radius oben 15mm, Höhe 40mm",
        "code": """\
# -*- coding: utf-8 -*-
R_UNTEN = 30.0; R_OBEN = 15.0; HOEHE = 40.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
stumpf = doc.addObject("Part::Cone", "Kegelstumpf")
stumpf.Radius1 = R_UNTEN   # große Grundfläche unten
stumpf.Radius2 = R_OBEN    # kleinere Fläche oben (> 0 = kein Spitzkegel)
stumpf.Height = HOEHE
doc.recompute()"""
    },

    {
        "tags": [
            "torus", "ring", "donut", "kreisring", "reifen", "wulst",
            "dichtring", "o-ring", "reifenform", "ringform",
        ],
        "aufgabe": "Torus/Ring: Außenradius 40mm, Rohrquerschnitt 10mm",
        "code": """\
# -*- coding: utf-8 -*-
AUSSEN_R = 40.0   # Abstand Mittelpunkt zu Rohrachse
ROHR_R   = 10.0   # Querschnitts-Radius des Rohrs
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
ring = doc.addObject("Part::Torus", "Ring")
ring.Radius1 = AUSSEN_R   # großer Radius (Mitte des Rings bis Rohrachse)
ring.Radius2 = ROHR_R     # kleiner Radius (Rohrquerschnitt)
doc.recompute()"""
    },

    # ══════════════════════════════════════════════════════════════════════════
    # VEREINIGUNG — Part::Fuse
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "kreuz", "plus", "cross", "kreuzform", "t-profil", "t_profil",
            "vereinig", "fuse", "verbinden", "zusammen", "zusammenfügen",
            "anbauen", "ansetzen", "aufsetzen", "montieren", "verbaut",
        ],
        "aufgabe": "Kreuzform aus zwei Quadern 100×20 und 20×100, Höhe 10mm",
        "code": """\
# -*- coding: utf-8 -*-
LA = 100.0; BA = 20.0   # Querbalken: Länge und Breite
LB = 20.0; BB = 100.0   # Längsbalken: Länge und Breite
HOEHE = 10.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
# PFLICHT: beide Teile auf Ursprung zentrieren bevor Part::Fuse!
quer = doc.addObject("Part::Box", "Querbalken")
quer.Length = LA; quer.Width = BA; quer.Height = HOEHE
quer.Placement.Base = App.Vector(-LA / 2, -BA / 2, 0)

laengs = doc.addObject("Part::Box", "Laengsbalken")
laengs.Length = LB; laengs.Width = BB; laengs.Height = HOEHE
laengs.Placement.Base = App.Vector(-LB / 2, -BB / 2, 0)

kreuz = doc.addObject("Part::Fuse", "Kreuz")
kreuz.Base = quer; kreuz.Tool = laengs
doc.recompute()"""
    },

    {
        "tags": [
            "t-profil", "t_profil", "tprofil", "t-form", "t profil",
            "querbalken", "steg", "fuse", "t-träger", "t-stück",
        ],
        "aufgabe": "T-Profil: Querbalken 80×15mm, Steg 15×50mm, Höhe 10mm",
        "code": """\
# -*- coding: utf-8 -*-
LA = 80.0; BA = 15.0   # Querbalken (horizontal)
LS = 15.0; BS = 50.0   # Steg (vertikal, hängt nach unten)
HOEHE = 10.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
quer = doc.addObject("Part::Box", "Querbalken")
quer.Length = LA; quer.Width = BA; quer.Height = HOEHE
quer.Placement.Base = App.Vector(-LA / 2, -BA / 2, 0)

steg = doc.addObject("Part::Box", "Steg")
steg.Length = LS; steg.Width = BS; steg.Height = HOEHE
steg.Placement.Base = App.Vector(-LS / 2, -BA / 2 - BS, 0)   # hängt nach unten

t_profil = doc.addObject("Part::Fuse", "TProfil")
t_profil.Base = quer; t_profil.Tool = steg
doc.recompute()"""
    },

    {
        "tags": [
            "l-profil", "l_profil", "lprofil", "l-form", "l profil",
            "winkel", "winkelstück", "ecke", "l-winkel", "winkeleisen",
        ],
        "aufgabe": "L-Profil: Schenkel 1 = 80×10mm, Schenkel 2 = 10×50mm, Höhe 10mm",
        "code": """\
# -*- coding: utf-8 -*-
L1 = 80.0; B1 = 10.0   # langer Schenkel
L2 = 10.0; B2 = 50.0   # kurzer Schenkel
HOEHE = 10.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
s1 = doc.addObject("Part::Box", "SchenkelH")
s1.Length = L1; s1.Width = B1; s1.Height = HOEHE
s1.Placement.Base = App.Vector(0, 0, 0)

s2 = doc.addObject("Part::Box", "SchenkelV")
s2.Length = L2; s2.Width = B2; s2.Height = HOEHE
s2.Placement.Base = App.Vector(0, B1, 0)   # direkt über der linken Kante

l_profil = doc.addObject("Part::Fuse", "LProfil")
l_profil.Base = s1; l_profil.Tool = s2
doc.recompute()"""
    },

    {
        "tags": [
            "dubel", "stift", "dübel", "niet", "pin", "zapfen",
            "kopf", "schaft", "pilz", "nagel", "befestigungsstift",
            "befestigung", "verbindungsstift",
        ],
        "aufgabe": "Dübel/Stift: Kopf Radius 12mm Höhe 5mm, Schaft Radius 6mm Höhe 35mm",
        "code": """\
# -*- coding: utf-8 -*-
KOPF_R = 12.0; KOPF_H = 5.0
SCHAFT_R = 6.0; SCHAFT_H = 35.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
kopf = doc.addObject("Part::Cylinder", "Kopf")
kopf.Radius = KOPF_R; kopf.Height = KOPF_H

schaft = doc.addObject("Part::Cylinder", "Schaft")
schaft.Radius = SCHAFT_R; schaft.Height = SCHAFT_H
schaft.Placement.Base = App.Vector(0, 0, KOPF_H)

dubel = doc.addObject("Part::Fuse", "Duebel")
dubel.Base = kopf; dubel.Tool = schaft
doc.recompute()"""
    },

    {
        "tags": [
            "drei", "mehrere teile", "drei teile", "drei quader",
            "verketten", "kette", "fuse", "verbund", "reihe",
            "aneinanderreihen", "drei objekte", "viele teile",
        ],
        "aufgabe": "Drei Quader zu einer langen Platte verbinden (Fuse-Kette)",
        "code": """\
# -*- coding: utf-8 -*-
A = 30.0; HOEHE = 8.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
q1 = doc.addObject("Part::Box", "Teil1")
q1.Length = A; q1.Width = A; q1.Height = HOEHE

q2 = doc.addObject("Part::Box", "Teil2")
q2.Length = A; q2.Width = A; q2.Height = HOEHE
q2.Placement.Base = App.Vector(A, 0, 0)

q3 = doc.addObject("Part::Box", "Teil3")
q3.Length = A; q3.Width = A; q3.Height = HOEHE
q3.Placement.Base = App.Vector(A * 2, 0, 0)

# Bei 3+ Objekten: Fuse-Kette — immer paarweise!
fuse1 = doc.addObject("Part::Fuse", "Verbund12")
fuse1.Base = q1; fuse1.Tool = q2

fuse2 = doc.addObject("Part::Fuse", "Ergebnis")
fuse2.Base = fuse1; fuse2.Tool = q3
doc.recompute()"""
    },

    # ══════════════════════════════════════════════════════════════════════════
    # SUBTRAKTION — Part::Cut
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "bohrung", "loch", "durchgang", "cut", "bohren", "lochen",
            "durchbohren", "öffnung", "durchgangsloch",
            "schraubenloch", "schraubenbohrung", "befestigungsloch",
            "kernloch", "gewindebohrung", "senkloch", "versenkung",
        ],
        "aufgabe": "Quader 60×40×30mm mit zentraler Durchgangsbohrung Radius 8mm",
        "code": """\
# -*- coding: utf-8 -*-
LAENGE = 60.0; BREITE = 40.0; HOEHE = 30.0; BOHR_R = 8.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
box = doc.addObject("Part::Box", "Quader")
box.Length = LAENGE; box.Width = BREITE; box.Height = HOEHE

# Bohrwerkzeug: DOPPELT so hoch wie Körper, mittig (X/Y) und unterhalb (Z)
zyl = doc.addObject("Part::Cylinder", "Bohrwerkzeug")
zyl.Radius = BOHR_R
zyl.Height = HOEHE * 2.0
zyl.Placement.Base = App.Vector(LAENGE / 2, BREITE / 2, -HOEHE / 2)

cut = doc.addObject("Part::Cut", "Ergebnis")
cut.Base = box; cut.Tool = zyl
doc.recompute()"""
    },

    {
        "tags": [
            "kugel bohrung", "kugel loch", "bohrung kugel", "sphere hole",
            "kugel", "sphere", "ball bohrung", "kugel durchbohrt",
            "schneide", "schneiden", "durch", "durchschneiden",
            "zylinder kugel", "kugel zylinder", "cut kugel",
        ],
        "aufgabe": "Kugel Radius 30mm mit Zylinder-Bohrung Radius 10mm von unten durchschneiden",
        "code": """\
# -*- coding: utf-8 -*-
# WICHTIG: Maße EXAKT aus der Aufgabe übernehmen — NICHT halbieren!
# Radius 30mm bleibt 30mm (kein /2), Radius 10mm bleibt 10mm (kein /2)
KUGEL_R = 30.0   # <-- aus Aufgabe übernehmen (NICHT halbieren!)
BOHR_R = 10.0    # <-- aus Aufgabe übernehmen (NICHT halbieren!)
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
kugel = doc.addObject("Part::Sphere", "Kugel")
kugel.Radius = KUGEL_R   # direkt setzen, exakter Wert aus Aufgabe

# REGEL Kugel-Bohrung "von unten": Base.z = -KUGEL_R, Height = KUGEL_R * 2
# Der Zylinder muss die GESAMTE Kugel (Durchmesser!) durchqueren
zyl = doc.addObject("Part::Cylinder", "Bohrwerkzeug")
zyl.Radius = BOHR_R
zyl.Height = KUGEL_R * 2   # = Kugeldurchmesser — lang genug zum Durchdringen
zyl.Placement.Base = App.Vector(0, 0, -KUGEL_R)   # startet unter der Kugel

cut = doc.addObject("Part::Cut", "KugelMitBohrung")
cut.Base = kugel; cut.Tool = zyl
doc.recompute()"""
    },

    {
        "tags": [
            "mehrere bohrungen", "drei bohrungen", "vier bohrungen",
            "bohrungen", "löcher", "lochplatte", "mehrfach bohrung",
            "schraubenlöcher", "befestigungslöcher", "lochbild",
            "schraube", "verschraubung", "montage", "befestigung",
            "grundplatte", "befestigungsplatte",
        ],
        "aufgabe": "Platte 120×60×15mm mit drei Bohrungen Radius 7mm",
        "code": """\
# -*- coding: utf-8 -*-
LAENGE = 120.0; BREITE = 60.0; HOEHE = 15.0
BOHR_R = 7.0; ABSTAND = 25.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
platte = doc.addObject("Part::Box", "Grundplatte")
platte.Length = LAENGE; platte.Width = BREITE; platte.Height = HOEHE

# Bohrung 1
b1 = doc.addObject("Part::Cylinder", "Bohrung1")
b1.Radius = BOHR_R; b1.Height = HOEHE * 2
b1.Placement.Base = App.Vector(ABSTAND, BREITE / 2, -HOEHE / 2)
c1 = doc.addObject("Part::Cut", "Schritt1")
c1.Base = platte; c1.Tool = b1

# Bohrung 2
b2 = doc.addObject("Part::Cylinder", "Bohrung2")
b2.Radius = BOHR_R; b2.Height = HOEHE * 2
b2.Placement.Base = App.Vector(LAENGE / 2, BREITE / 2, -HOEHE / 2)
c2 = doc.addObject("Part::Cut", "Schritt2")
c2.Base = c1; c2.Tool = b2

# Bohrung 3 — IMMER vorheriges Cut-Ergebnis als Base!
b3 = doc.addObject("Part::Cylinder", "Bohrung3")
b3.Radius = BOHR_R; b3.Height = HOEHE * 2
b3.Placement.Base = App.Vector(LAENGE - ABSTAND, BREITE / 2, -HOEHE / 2)
c3 = doc.addObject("Part::Cut", "Ergebnis")
c3.Base = c2; c3.Tool = b3
doc.recompute()"""
    },

    {
        "tags": [
            "rohr", "hohlzylinder", "hohl", "röhre", "rohrstück",
            "innen", "außen", "wandstärke", "rohrleitung", "rohrprofil",
            "buchse", "lagerbuchse", "hülse", "distanzhülse", "spacer",
            "lager", "gleitlager", "wellenhülse",
        ],
        "aufgabe": "Rohr/Hohlzylinder: Außenradius 25mm, Innenradius 18mm, Höhe 80mm",
        "code": """\
# -*- coding: utf-8 -*-
AUSSEN_R = 25.0; INNEN_R = 18.0; HOEHE = 80.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
aussen = doc.addObject("Part::Cylinder", "Aussenmantel")
aussen.Radius = AUSSEN_R; aussen.Height = HOEHE

innen = doc.addObject("Part::Cylinder", "Innenwerkzeug")
innen.Radius = INNEN_R
innen.Height = HOEHE * 2               # länger für sicheres Durchdringen
innen.Placement.Base = App.Vector(0, 0, -HOEHE / 2)

rohr = doc.addObject("Part::Cut", "Rohr")
rohr.Base = aussen; rohr.Tool = innen
doc.recompute()"""
    },

    {
        "tags": [
            "nut", "schlitz", "einschnitt", "rille", "aussparung",
            "vertiefung", "tasche", "einkerbung", "nut quader",
            "fräsung", "einfräsung",
        ],
        "aufgabe": "Quader 80×50×25mm mit Nut 60×10mm tief 8mm (oben mittig)",
        "code": """\
# -*- coding: utf-8 -*-
LAENGE = 80.0; BREITE = 50.0; HOEHE = 25.0
NUT_L = 60.0; NUT_B = 10.0; NUT_TIEFE = 8.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
box = doc.addObject("Part::Box", "Grundkoerper")
box.Length = LAENGE; box.Width = BREITE; box.Height = HOEHE

nut = doc.addObject("Part::Box", "NutWerkzeug")
nut.Length = NUT_L; nut.Width = NUT_B
nut.Height = NUT_TIEFE + 1.0           # +1mm Sicherheit
nut.Placement.Base = App.Vector(
    (LAENGE - NUT_L) / 2,
    (BREITE - NUT_B) / 2,
    HOEHE - NUT_TIEFE)                 # von oben eintauchen

ergebnis = doc.addObject("Part::Cut", "MitNut")
ergebnis.Base = box; ergebnis.Tool = nut
doc.recompute()"""
    },

    {
        "tags": [
            "hohlkugel", "schale", "kugelschale", "halbschale",
            "kugel hohl", "hohlform", "wandstärke kugel",
        ],
        "aufgabe": "Hohlkugel: Außenradius 30mm, Wandstärke 3mm",
        "code": """\
# -*- coding: utf-8 -*-
AUSSEN_R = 30.0; WAND = 3.0
INNEN_R = AUSSEN_R - WAND
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
aussen = doc.addObject("Part::Sphere", "Aussenform")
aussen.Radius = AUSSEN_R

innen = doc.addObject("Part::Sphere", "Innenform")
innen.Radius = INNEN_R

hohlkugel = doc.addObject("Part::Cut", "Hohlkugel")
hohlkugel.Base = aussen; hohlkugel.Tool = innen
doc.recompute()"""
    },

    # ══════════════════════════════════════════════════════════════════════════
    # GESTAPELTE FORMEN / PYRAMIDE / TREPPE
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "pyramide", "treppe", "stufen", "staffel", "gestapelt",
            "aufeinander", "übereinander", "turm", "stacked",
            "stufenpyramide", "treppenform", "drei", "gestapelte",
        ],
        "aufgabe": "3-stufige Pyramide: Stufen 80/60/40mm Kantenlänge, je 10mm hoch",
        "code": """\
# -*- coding: utf-8 -*-
H = 10.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
# REGEL: jede Stufe zentriert (-L/2, -B/2), z = Summe vorheriger Höhen
s1 = doc.addObject("Part::Box", "Stufe1")
s1.Length = 80.0; s1.Width = 80.0; s1.Height = H
s1.Placement.Base = App.Vector(-40.0, -40.0, 0)

s2 = doc.addObject("Part::Box", "Stufe2")
s2.Length = 60.0; s2.Width = 60.0; s2.Height = H
s2.Placement.Base = App.Vector(-30.0, -30.0, H)

s3 = doc.addObject("Part::Box", "Stufe3")
s3.Length = 40.0; s3.Width = 40.0; s3.Height = H
s3.Placement.Base = App.Vector(-20.0, -20.0, H * 2)
doc.recompute()"""
    },

    {
        "tags": [
            "treppe", "stufen", "stufenform", "stufig",
            "versetzt", "schritt", "treppengeländer", "treppenstruktur",
        ],
        "aufgabe": "4-stufige Treppe, Stufe je 20×30mm, Höhe je 15mm",
        "code": """\
# -*- coding: utf-8 -*-
SW = 20.0; ST = 30.0; SH = 15.0   # Breite, Tiefe, Höhe pro Stufe
STUFEN = 4
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
for i in range(STUFEN):
    stufe = doc.addObject("Part::Box", f"Stufe{i+1}")
    stufe.Length = SW * (i + 1)   # jede Stufe breiter
    stufe.Width  = ST
    stufe.Height = SH
    stufe.Placement.Base = App.Vector(0, 0, SH * i)
doc.recompute()"""
    },

    # ══════════════════════════════════════════════════════════════════════════
    # SCHNITTMENGE — Part::Common
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "common", "schnitt", "schnittmenge", "überschneidung",
            "gemeinsam", "überlappung", "intersection", "schnittbereich",
        ],
        "aufgabe": "Schnittmenge (Part::Common) von Kugel und Zylinder",
        "code": """\
# -*- coding: utf-8 -*-
RADIUS = 25.0; ZYL_HOEHE = 50.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
kugel = doc.addObject("Part::Sphere", "Kugel")
kugel.Radius = RADIUS
kugel.Placement.Base = App.Vector(0, 0, RADIUS)

zyl = doc.addObject("Part::Cylinder", "Zylinder")
zyl.Radius = RADIUS * 0.7
zyl.Height = ZYL_HOEHE

# Part::Common = NUR der gemeinsame Bereich bleibt übrig
schnitt = doc.addObject("Part::Common", "Schnittmenge")
schnitt.Base = kugel; schnitt.Tool = zyl
doc.recompute()"""
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ROTATION / POSITIONIERUNG
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "drehen", "rotation", "winkel", "rotieren", "kippen",
            "neigen", "ausrichten", "dreh", "rotiert", "schräg",
            "verdreht", "gekippt", "geneigt", "schrägstellung",
        ],
        "aufgabe": "Quader 60×30×10mm um 45 Grad um die Z-Achse drehen",
        "code": """\
# -*- coding: utf-8 -*-
LAENGE = 60.0; BREITE = 30.0; HOEHE = 10.0; WINKEL = 45.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
box = doc.addObject("Part::Box", "Quader")
box.Length = LAENGE; box.Width = BREITE; box.Height = HOEHE

drehung = App.Rotation(App.Vector(0, 0, 1), WINKEL)   # Achse, Grad
box.Placement = App.Placement(App.Vector(0, 0, 0), drehung)
doc.recompute()"""
    },

    {
        "tags": [
            "nebeneinander", "reihe", "array", "muster",
            "mehrere", "kopie", "abstand", "gitter", "anordnung",
            "linear", "lineares muster",
        ],
        "aufgabe": "5 Zylinder nebeneinander mit 20mm Abstand",
        "code": """\
# -*- coding: utf-8 -*-
ANZAHL = 5; ABSTAND = 20.0; RADIUS = 6.0; HOEHE = 30.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
for i in range(ANZAHL):
    zyl = doc.addObject("Part::Cylinder", f"Zylinder{i+1}")
    zyl.Radius = RADIUS; zyl.Height = HOEHE
    zyl.Placement.Base = App.Vector(i * ABSTAND, 0, 0)
doc.recompute()"""
    },

    # ══════════════════════════════════════════════════════════════════════════
    # KOMPLEXE FORMEN
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "bowling", "bowlingkugel", "fingerlöcher", "finger",
            "kugel löcher", "kugel bohrungen", "fingerbohrung",
            "dreierloch", "sportgerät",
        ],
        "aufgabe": "Bowlingkugel Radius 55mm mit 3 Fingerlöchern Radius 11mm, Tiefe 40mm",
        "code": """\
# -*- coding: utf-8 -*-
KUGEL_R = 55.0; LOCH_R = 11.0; TIEFE = 40.0; VERSATZ = 16.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
kugel = doc.addObject("Part::Sphere", "Kugel")
kugel.Radius = KUGEL_R

d = doc.addObject("Part::Cylinder", "Daumen")
d.Radius = LOCH_R; d.Height = TIEFE
d.Placement.Base = App.Vector(0, 0, KUGEL_R - TIEFE)
c1 = doc.addObject("Part::Cut", "OhneDaumen")
c1.Base = kugel; c1.Tool = d

z = doc.addObject("Part::Cylinder", "Zeigefinger")
z.Radius = LOCH_R; z.Height = TIEFE
z.Placement.Base = App.Vector(-VERSATZ, 0, KUGEL_R - TIEFE)
c2 = doc.addObject("Part::Cut", "OhneZeige")
c2.Base = c1; c2.Tool = z

m = doc.addObject("Part::Cylinder", "Mittelfinger")
m.Radius = LOCH_R; m.Height = TIEFE
m.Placement.Base = App.Vector(VERSATZ, 0, KUGEL_R - TIEFE)
ergebnis = doc.addObject("Part::Cut", "Bowlingkugel")
ergebnis.Base = c2; ergebnis.Tool = m
doc.recompute()"""
    },

    {
        "tags": [
            "sockel", "pfeiler", "säule", "quader zylinder",
            "plattform", "aufgesetzt", "podest", "postament",
        ],
        "aufgabe": "Sockel: Quader 80×80×20mm + Zylinder Radius 25mm Höhe 50mm oben mittig",
        "code": """\
# -*- coding: utf-8 -*-
SOCKEL_L = 80.0; SOCKEL_B = 80.0; SOCKEL_H = 20.0
SAEULE_R = 25.0; SAEULE_H = 50.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
sockel = doc.addObject("Part::Box", "Sockel")
sockel.Length = SOCKEL_L; sockel.Width = SOCKEL_B; sockel.Height = SOCKEL_H

saeule = doc.addObject("Part::Cylinder", "Saeule")
saeule.Radius = SAEULE_R; saeule.Height = SAEULE_H
saeule.Placement.Base = App.Vector(
    SOCKEL_L / 2, SOCKEL_B / 2, SOCKEL_H)

konstrukt = doc.addObject("Part::Fuse", "Konstruktion")
konstrukt.Base = sockel; konstrukt.Tool = saeule
doc.recompute()"""
    },

    {
        "tags": [
            "ring rahmen", "hohlring", "rechteck ring", "eckiger ring",
            "rahmen", "viereckig", "rechteckrahmen", "fensterrahmen",
            "aussparung mittig", "quadratischer rahmen",
        ],
        "aufgabe": "Rechteckiger Rahmen: außen 80×80mm, innen 60×60mm, Höhe 10mm",
        "code": """\
# -*- coding: utf-8 -*-
A_L = 80.0; A_B = 80.0; I_L = 60.0; I_B = 60.0; HOEHE = 10.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
aussen = doc.addObject("Part::Box", "Aussen")
aussen.Length = A_L; aussen.Width = A_B; aussen.Height = HOEHE
aussen.Placement.Base = App.Vector(-A_L / 2, -A_B / 2, 0)

innen = doc.addObject("Part::Box", "Innen")
innen.Length = I_L; innen.Width = I_B; innen.Height = HOEHE * 2
innen.Placement.Base = App.Vector(-I_L / 2, -I_B / 2, -HOEHE / 2)

rahmen = doc.addObject("Part::Cut", "Rahmen")
rahmen.Base = aussen; rahmen.Tool = innen
doc.recompute()"""
    },

    # ══════════════════════════════════════════════════════════════════════════
    # MASCHINENBAU-KLASSIKER
    # ══════════════════════════════════════════════════════════════════════════

    {
        "tags": [
            "langloch", "schlitzloch", "montageschlitz", "langlochbohrung",
            "langlöcher", "ovalloch", "ovale bohrung", "längsschlitz",
            "oblong", "slot", "elongated hole",
        ],
        "aufgabe": "Platte 100×60×12mm mit Langloch (30mm lang, Radius 5mm), mittig",
        "code": """\
# -*- coding: utf-8 -*-
LAENGE = 100.0; BREITE = 60.0; HOEHE = 12.0
LOCH_L = 30.0   # Abstand der beiden Mittelpunkte
LOCH_R = 5.0    # Radius der Rundungen
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
platte = doc.addObject("Part::Box", "Platte")
platte.Length = LAENGE; platte.Width = BREITE; platte.Height = HOEHE

# Langloch = zwei Zylinder (Rundenden) + Verbindungsquader, dann als Cut
# Alle drei Teile mittig in X/Y der Platte, Z durch die Platte
mx = LAENGE / 2; my = BREITE / 2

zyl1 = doc.addObject("Part::Cylinder", "Runden1")
zyl1.Radius = LOCH_R; zyl1.Height = HOEHE * 2
zyl1.Placement.Base = App.Vector(mx - LOCH_L / 2, my, -HOEHE / 2)

zyl2 = doc.addObject("Part::Cylinder", "Runden2")
zyl2.Radius = LOCH_R; zyl2.Height = HOEHE * 2
zyl2.Placement.Base = App.Vector(mx + LOCH_L / 2, my, -HOEHE / 2)

mitte = doc.addObject("Part::Box", "Mittelteil")
mitte.Length = LOCH_L; mitte.Width = LOCH_R * 2; mitte.Height = HOEHE * 2
mitte.Placement.Base = App.Vector(mx - LOCH_L / 2, my - LOCH_R, -HOEHE / 2)

f1 = doc.addObject("Part::Fuse", "LanglochTool1")
f1.Base = zyl1; f1.Tool = mitte
f2 = doc.addObject("Part::Fuse", "LanglochTool")
f2.Base = f1; f2.Tool = zyl2

ergebnis = doc.addObject("Part::Cut", "MitLangloch")
ergebnis.Base = platte; ergebnis.Tool = f2
doc.recompute()"""
    },

    {
        "tags": [
            "lochkreis", "teilkreis", "bohrungskreis", "schraubenkreis",
            "lochkreisbohrungen", "kreisanordnung", "bolzenkreis",
            "pcd", "bolt circle", "lochbild kreis",
            "flansch bohrungen", "kreis bohrungen", "radial bohrungen",
        ],
        "aufgabe": "Runde Platte Radius 50mm, Höhe 10mm mit 4 Bohrungen Radius 4mm auf Lochkreis R=35mm",
        "code": """\
# -*- coding: utf-8 -*-
import math
PLATTE_R = 50.0; PLATTE_H = 10.0
LOCH_KR = 35.0    # Lochkreis-Radius (Abstand Mitte zu Bohrungs-Mitte)
LOCH_R = 4.0; ANZAHL = 4
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
platte = doc.addObject("Part::Cylinder", "Platte")
platte.Radius = PLATTE_R; platte.Height = PLATTE_H

letztes = platte
for i in range(ANZAHL):
    winkel = math.radians(i * 360.0 / ANZAHL)   # gleichmäßig verteilt
    x = LOCH_KR * math.cos(winkel)
    y = LOCH_KR * math.sin(winkel)
    bohr = doc.addObject("Part::Cylinder", f"Bohrung{i+1}")
    bohr.Radius = LOCH_R; bohr.Height = PLATTE_H * 2
    bohr.Placement.Base = App.Vector(x, y, -PLATTE_H / 2)
    cut = doc.addObject("Part::Cut", f"Schritt{i+1}")
    cut.Base = letztes; cut.Tool = bohr
    letztes = cut   # Cut-Kette weiterführen!
doc.recompute()"""
    },

    {
        "tags": [
            "buchse", "lagerbuchse", "distanzhülse", "spacer",
            "gleitlager", "wellenbuchse", "lagerhülse",
            "wellenhülse", "toleranzhülse", "buchse maschinenbau",
        ],
        "aufgabe": "Lagerbuchse: Außen-Ø 32mm, Innen-Ø 20mm, Höhe 30mm",
        "code": """\
# -*- coding: utf-8 -*-
AUSSEN_R = 16.0   # Außenradius = Ø/2
INNEN_R  = 10.0   # Innenradius = Ø/2
HOEHE    = 30.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
aussen = doc.addObject("Part::Cylinder", "Aussenmantel")
aussen.Radius = AUSSEN_R; aussen.Height = HOEHE

innen = doc.addObject("Part::Cylinder", "Bohrung")
innen.Radius = INNEN_R
innen.Height = HOEHE * 2                          # länger für sicheres Durchdringen
innen.Placement.Base = App.Vector(0, 0, -HOEHE / 2)

buchse = doc.addObject("Part::Cut", "Lagerbuchse")
buchse.Base = aussen; buchse.Tool = innen
doc.recompute()"""
    },

    {
        "tags": [
            "verrundung", "fase", "fillet", "chamfer", "kante",
            "kantenabrundung", "kantenverrundung", "radius kante",
            "abgerundet", "abrundung", "ecke rund", "abrunden",
            "senkung", "anschrägung", "entgraten",
        ],
        "aufgabe": "Quader 60×40×20mm mit Verrundung aller Kanten Radius 3mm",
        "code": """\
# -*- coding: utf-8 -*-
LAENGE = 60.0; BREITE = 40.0; HOEHE = 20.0; RUND_R = 3.0
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")
box = doc.addObject("Part::Box", "Quader")
box.Length = LAENGE; box.Width = BREITE; box.Height = HOEHE
doc.recompute()   # recompute() VOR Fillet nötig!

fillet = doc.addObject("Part::Fillet", "Verrundung")
fillet.Base = box
# Alle 12 Kanten: Liste von (Kanten-Index, Radius-Start, Radius-Ende)
fillet.Edges = [(i, RUND_R, RUND_R) for i in range(1, 13)]
doc.recompute()"""
    },

    {
        "tags": [
            "flansch", "flanschteil", "rohrflansch", "montageflansch",
            "flanschplatte", "befestigungsflansch", "verbindungsflansch",
            "flansch lochkreis", "scheibe bohrungen",
        ],
        "aufgabe": "Flansch: Außen-Ø 100mm, Zentral-Ø 30mm, 4 Schraubenlöcher Ø 8mm auf LK R=38mm, Höhe 12mm",
        "code": """\
# -*- coding: utf-8 -*-
import math
FLANSCH_R  = 50.0   # Außenradius
FLANSCH_H  = 12.0
ZENTRAL_R  = 15.0   # Radius zentrale Bohrung
LOCH_KR    = 38.0   # Lochkreis-Radius für Schrauben
LOCH_R     = 4.0    # Schraubenbohrung-Radius
ANZAHL     = 4
import FreeCAD as App
doc = App.ActiveDocument
if doc is None: doc = App.newDocument("Modell")

flansch = doc.addObject("Part::Cylinder", "FlanschRoh")
flansch.Radius = FLANSCH_R; flansch.Height = FLANSCH_H

# Zentrale Bohrung
z = doc.addObject("Part::Cylinder", "ZentralBohrung")
z.Radius = ZENTRAL_R; z.Height = FLANSCH_H * 2
z.Placement.Base = App.Vector(0, 0, -FLANSCH_H / 2)
letztes = doc.addObject("Part::Cut", "OhneZentrum")
letztes.Base = flansch; letztes.Tool = z

# Schraubenbohrungen auf Lochkreis (Cut-Kette)
for i in range(ANZAHL):
    winkel = math.radians(i * 360.0 / ANZAHL)
    x = LOCH_KR * math.cos(winkel)
    y = LOCH_KR * math.sin(winkel)
    bohr = doc.addObject("Part::Cylinder", f"Schraube{i+1}")
    bohr.Radius = LOCH_R; bohr.Height = FLANSCH_H * 2
    bohr.Placement.Base = App.Vector(x, y, -FLANSCH_H / 2)
    cut = doc.addObject("Part::Cut", f"Flansch{i+1}")
    cut.Base = letztes; cut.Tool = bohr
    letztes = cut
doc.recompute()"""
    },

]


# ══════════════════════════════════════════════════════════════════════════════
# Lookup-Funktion mit gewichtetem Scoring
# ══════════════════════════════════════════════════════════════════════════════

_STOPP = {
    "und", "oder", "mit", "von", "ein", "eine", "einem", "einen", "einer",
    "der", "die", "das", "dem", "den", "des", "in", "auf", "an", "zu",
    "als", "für", "ist", "wird", "werden", "soll", "durch", "nach",
    "zum", "zur", "beim", "am", "im", "ins", "aus",
    "create", "make", "the", "with", "from", "that", "this", "into",
    "erstelle", "erzeuge", "mache", "erstell", "baue", "generiere",
    "eine", "einen", "einer",
}

# Aliases: exaktes Suchwort → Tag-Erweiterungen (Gewicht: 3 bei Exakt, 0.5 bei Teilwort)
# NUR exakter Key-Match (kein Substring-Check) — verhindert Fehlauflösungen wie
# "bohrungen" → "bohrung" → cut/loch → falsches Beispiel gewinnt
_ALIASES: dict[str, list[str]] = {
    # Grundformen
    "kugel":         ["sphere", "ball"],
    "zylinder":      ["cylinder", "walze"],
    "kasten":        ["box", "quader"],
    "würfel":        ["box", "quader"],
    "kegel":         ["cone"],
    "ring":          ["torus", "donut"],
    # Rohr / Hülse / Buchse (alle verweisen aufeinander)
    "rohr":          ["hohlzylinder", "buchse", "hülse", "lagerbuchse"],
    "buchse":        ["rohr", "hohlzylinder", "hülse", "lagerbuchse"],
    "hülse":         ["rohr", "buchse", "hohlzylinder"],
    "lagerbuchse":   ["buchse", "rohr", "hülse"],
    "distanzhülse":  ["buchse", "rohr", "hülse"],
    # Bohrung / Loch (Singular ↔ Plural STRIKT getrennt — kein Singular→Plural-Overflow!)
    "bohrung":             ["loch", "durchgang", "schraubenloch"],
    "loch":                ["bohrung", "durchgang"],
    "bohrungen":           ["lochbild", "schraubenlöcher"],        # kein "mehrere bohrungen"!
    "löcher":              ["bohrungen", "lochbild"],
    # Dativ-Pluralformen (deutsches Flexionssystem)
    "schraubenlöchern":    ["schraubenlöcher", "mehrere bohrungen"],
    "befestigungslöchern": ["befestigungslöcher", "mehrere bohrungen"],
    "bohrungslöchern":     ["bohrungen", "mehrere bohrungen"],
    "schraubenloch":       ["bohrung", "befestigungsloch"],
    "schraubenlöcher":     ["mehrere bohrungen", "befestigungslöcher"],
    "schraube":            ["schraubenloch", "befestigungsloch"],
    "schrauben":           ["schraubenlöcher", "befestigungslöcher"],
    "befestigung":         ["schraubenloch", "befestigungsloch", "montage"],
    "montage":             ["befestigungsloch", "schraubenloch"],
    "verschrauben":        ["schraubenlöcher", "mehrere bohrungen"],
    "verschraubung":       ["schraubenlöcher", "mehrere bohrungen"],
    # Lochkreis / Flansch
    "lochkreis":     ["teilkreis", "kreisanordnung", "lochkreisbohrungen"],
    "teilkreis":     ["lochkreis", "kreisanordnung"],
    "flansch":       ["lochkreis", "flanschplatte", "flansch lochkreis"],
    "flanschplatte": ["flansch", "lochkreis"],
    # Langloch / Schlitz / Nut
    "langloch":      ["schlitzloch", "schlitz", "montageschlitz"],
    "schlitzloch":   ["langloch", "montageschlitz"],
    "montageschlitz": ["langloch", "schlitzloch"],
    "schlitz":       ["nut", "einschnitt", "langloch"],
    "nut":           ["schlitz", "einschnitt", "aussparung"],
    # Verrundung / Fase (auch flektierte Formen)
    "verrundung":    ["fillet", "abrundung", "kantenverrundung", "abgerundet"],
    "fase":          ["chamfer", "anschrägung"],
    "fillet":        ["verrundung", "abrundung", "abgerundet"],
    "abrundung":     ["verrundung", "fillet", "abgerundet"],
    "chamfer":       ["fase", "anschrägung"],
    "abgerundet":    ["verrundung", "fillet", "abrundung", "kantenverrundung"],
    "abgerundete":   ["verrundung", "fillet", "abrundung"],
    "abgerundeten":  ["verrundung", "fillet", "abrundung", "abgerundet"],
    "abrunden":      ["verrundung", "fillet", "abrundung"],
    "gerundet":      ["verrundung", "fillet", "abrundung"],
    # Boolesche Operationen
    "vereinigen":    ["fuse", "verbinden"],
    "verbinden":     ["fuse", "vereinigen"],
    "anbauen":       ["fuse", "aufsetzen", "montieren"],
    "aufsetzen":     ["fuse", "anbauen"],
    "schneiden":     ["cut", "abziehen"],
    "abziehen":      ["cut"],
    "schnitt":       ["common", "schnittmenge"],
    "schneide":      ["cut", "bohrung", "schnitt", "zylinder kugel"],
    "schneiden":     ["cut", "bohrung", "schnitt", "zylinder kugel"],
    "durch":         ["durchschneiden", "kugel bohrung", "cut kugel"],
    "durchbohren":   ["bohrung", "cut", "kugel bohrung"],
    "bowlingkugel":  ["kugel bohrung", "cut", "kugel", "kugel zylinder"],
    # Form-Gruppen
    "stufe":         ["treppe", "pyramide", "gestapelt"],
    "pyramide":      ["stufen", "gestapelt", "treppe"],
    "treppe":        ["stufen", "gestapelt"],
    "drehen":        ["rotation", "winkel"],
    "kippen":        ["rotation", "neigen"],
}


def beispiele_finden(aufgabe: str, max_beispiele: int = 2) -> str:
    """
    Gibt 1-2 passende Beispiele als Prompt-Block zurück.

    Scoring:
      exakter Tag-Treffer  = 5 Punkte
      Alias-Treffer        = 3 Punkte
      Teilwort-Treffer     = 1 Punkt
    """
    # Originalwörter aus der Anfrage
    original: set[str] = set()
    for w in aufgabe.lower().split():
        w = w.strip(".,;:!?()[]'\"")
        if len(w) > 2 and w not in _STOPP:
            original.add(w)

    if not original:
        return ""

    # Alias-Erweiterungen: NUR exakter Key-Match (kein Substring!)
    aliase: set[str] = set()
    for w in original:
        if w in _ALIASES:
            aliase.update(_ALIASES[w])
    aliase -= original  # Keine Doppelzählung

    # Scoring pro Beispiel — jedes Wort zählt maximal einmal pro Beispiel,
    # damit Compound-Tags ("drei quader", "drei teile") kein Mehrfach-Scoring erzeugen.
    treffer: list[tuple[float, dict]] = []
    for bsp in FC_BEISPIELE:
        tags = bsp["tags"]
        score = 0.0

        for w in original:
            exact = any(w == tag for tag in tags)
            if exact:
                score += 5              # exakter Treffer (nur einmal)
            elif any(w in tag or tag in w for tag in tags):
                score += 1              # Teilwort (nur einmal)

        for w in aliase:
            exact = any(w == tag for tag in tags)
            if exact:
                score += 3              # Alias-exakt (nur einmal)
            elif any(w in tag or tag in w for tag in tags):
                score += 0.5            # Alias-Teilwort (nur einmal)

        if score > 0:
            treffer.append((score, bsp))

    treffer.sort(key=lambda x: x[0], reverse=True)
    if not treffer:
        return ""

    zeilen = ["[ÄHNLICHE BEISPIELE — diese Muster verwenden]"]
    for i, (_, bsp) in enumerate(treffer[:max_beispiele], 1):
        zeilen.append(f"\nBeispiel {i}: {bsp['aufgabe']}")
        zeilen.append(bsp["code"])

    return "\n".join(zeilen)
