# -*- coding: utf-8 -*-
"""
ki_werkzeuge.py
───────────────
Strukturiertes Tool-Calling für FreeCAD-Operationen.

Inspiriert von ghbalf/freecad-ai – statt Raw-Code-Generierung ruft die
KI vordefinierte, validierte Operationen auf. Das macht die Ausgabe
sicherer, schneller und robuster bei schwachen Modellen.

Architektur:
  WerkzeugDefinition  – Beschreibt ein Tool (Name, Parameter, Handler)
  WerkzeugErgebnis    – Ergebnis eines Tool-Aufrufs
  WERKZEUG_REGISTER   – dict[name, WerkzeugDefinition]
  werkzeug_schema()   – JSON-Schema für LLM-Tool-Calling (Anthropic-Format)
  werkzeug_ausfuehren(name, kwargs) → WerkzeugErgebnis

Jeder Handler:
  - Läuft in einer FreeCAD-Undo-Transaktion
  - Gibt ein WerkzeugErgebnis zurück (nie eine Exception)
  - Benötigt kein Qt, kein self, nur einfache Python-Typen

Nutzung in ki_backends.py:
  tools = werkzeug_schema()   # an Anthropic/OpenAI API übergeben
  # Bei tool_use in der Antwort:
  ergebnis = werkzeug_ausfuehren(tool_name, tool_input)
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable


# ══════════════════════════════════════════════════════════════════════════════
# Datenklassen
# ══════════════════════════════════════════════════════════════════════════════

@dataclasses.dataclass
class WerkzeugParam:
    """Ein einzelner Parameter eines Werkzeugs."""
    name: str
    typ: str                        # "string" | "number" | "boolean"
    beschreibung: str
    pflicht: bool = True
    standard: Any = None
    enum: list[str] | None = None


@dataclasses.dataclass
class WerkzeugDefinition:
    """Vollständige Beschreibung eines KI-aufrufbaren Werkzeugs."""
    name: str
    beschreibung: str
    parameter: list[WerkzeugParam]
    handler: Callable[..., "WerkzeugErgebnis"]
    kategorie: str = "allgemein"


@dataclasses.dataclass
class WerkzeugErgebnis:
    """Ergebnis eines Werkzeugaufrufs."""
    erfolg: bool
    ausgabe: str
    fehler: str = ""
    daten: dict[str, Any] = dataclasses.field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
# Undo-Helfer
# ══════════════════════════════════════════════════════════════════════════════

def _hole_dokument():
    """Gibt das aktive FreeCAD-Dokument zurück — mit mehreren Fallbacks."""
    try:
        import FreeCAD as App
    except ImportError:
        return None

    doc = App.ActiveDocument
    if doc is not None:
        return doc

    # Fallback 1: über FreeCADGui
    try:
        import FreeCADGui as Gui
        if Gui.ActiveDocument:
            doc = App.getDocument(Gui.ActiveDocument.Document.Name)
            if doc:
                return doc
    except Exception:
        pass

    # Fallback 2: erstes geöffnetes Dokument
    try:
        docs = App.listDocuments()
        if docs:
            return App.getDocument(list(docs.keys())[0])
    except Exception:
        pass

    return None


def _mit_undo(bezeichnung: str, func: Callable) -> WerkzeugErgebnis:
    """Führt func in einer FreeCAD-Undo-Transaktion aus."""
    try:
        import FreeCAD as App  # noqa: N813
    except ImportError:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe="",
            fehler="FreeCAD ist nicht verfügbar.")

    doc = _hole_dokument()
    if doc is None:
        # Fallback 3: neues Dokument anlegen (wie in FreeCAD-Makros üblich)
        try:
            doc = App.newDocument("Neues_Modell")
            App.setActiveDocument(doc.Name)
        except Exception as e:
            return WerkzeugErgebnis(
                erfolg=False, ausgabe="",
                fehler=f"Kein Dokument gefunden und newDocument() fehlgeschlagen: {e}")

    doc.openTransaction(bezeichnung)
    try:
        ergebnis = func(doc)
        doc.recompute()
        doc.commitTransaction()
        return ergebnis
    except Exception as exc:
        try:
            doc.abortTransaction()
            doc.recompute()
        except Exception:
            pass
        return WerkzeugErgebnis(erfolg=False, ausgabe="", fehler=str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Werkzeug-Handler
# ══════════════════════════════════════════════════════════════════════════════

# ── Grundkörper erstellen ──────────────────────────────────────────────────

def _grundkoerper_erstellen(
    typ: str,
    bezeichnung: str = "",
    laenge: float = 20.0,
    breite: float = 20.0,
    hoehe: float = 20.0,
    radius: float = 10.0,
    radius2: float = 3.0,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
) -> WerkzeugErgebnis:
    """Erstellt einen Part-Grundkörper (Box, Zylinder, Kugel, Kegel, Torus)."""
    typ_map = {
        "box":      "Part::Box",
        "zylinder": "Part::Cylinder",
        "kugel":    "Part::Sphere",
        "kegel":    "Part::Cone",
        "torus":    "Part::Torus",
    }
    typ_norm = typ.lower()
    fc_typ = typ_map.get(typ_norm)
    if not fc_typ:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe="",
            fehler=f"Unbekannter Typ: '{typ}'. Erlaubt: {list(typ_map.keys())}")

    import FreeCAD as App  # noqa: N813

    def do(doc):
        label = bezeichnung or typ.capitalize()
        obj = doc.addObject(fc_typ, label)
        obj.Label = label

        if typ_norm == "box":
            obj.Length = laenge
            obj.Width  = breite
            obj.Height = hoehe
        elif typ_norm == "zylinder":
            obj.Radius = radius
            obj.Height = hoehe
        elif typ_norm == "kugel":
            obj.Radius = radius
        elif typ_norm == "kegel":
            obj.Radius1 = radius
            obj.Radius2 = radius2
            obj.Height  = hoehe
        elif typ_norm == "torus":
            obj.Radius1 = radius
            obj.Radius2 = radius2

        if x != 0 or y != 0 or z != 0:
            obj.Placement.Base = App.Vector(x, y, z)

        return WerkzeugErgebnis(
            erfolg=True,
            ausgabe=f"Erstellt: {obj.Label} ({obj.Name}, TypeId: {fc_typ})",
            daten={"name": obj.Name, "label": obj.Label, "type_id": fc_typ},
        )

    return _mit_undo(f"Erstelle {typ}", do)


# ── Boolean-Operation ──────────────────────────────────────────────────────

def _boolean_operation(
    operation: str,
    basis_name: str,
    werkzeug_name: str,
    ergebnis_bezeichnung: str = "",
) -> WerkzeugErgebnis:
    """Führt eine Boolean-Operation (Cut, Fuse, Common) durch."""
    op_map = {
        "cut":    "Part::Cut",
        "fuse":   "Part::Fuse",
        "common": "Part::Common",
    }
    op_norm = operation.lower()
    fc_op = op_map.get(op_norm)
    if not fc_op:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe="",
            fehler=f"Unbekannte Operation: '{operation}'. Erlaubt: cut, fuse, common")

    def do(doc):
        basis = doc.getObject(basis_name)
        if basis is None:
            return WerkzeugErgebnis(
                erfolg=False, ausgabe="",
                fehler=f"Basis-Objekt '{basis_name}' nicht gefunden.")
        werkzeug = doc.getObject(werkzeug_name)
        if werkzeug is None:
            return WerkzeugErgebnis(
                erfolg=False, ausgabe="",
                fehler=f"Werkzeug-Objekt '{werkzeug_name}' nicht gefunden.")

        label = ergebnis_bezeichnung or f"{op_norm.capitalize()}_{basis_name}"
        result = doc.addObject(fc_op, label)
        result.Label = label
        result.Base = basis
        result.Tool = werkzeug

        return WerkzeugErgebnis(
            erfolg=True,
            ausgabe=(f"Boolean {operation}: '{result.Label}' erstellt "
                     f"(Base={basis.Label}, Tool={werkzeug.Label})"),
            daten={"name": result.Name, "label": result.Label,
                   "base": basis.Name, "tool": werkzeug.Name},
        )

    return _mit_undo(f"Boolean {operation}", do)


# ── Platzierung setzen ─────────────────────────────────────────────────────

def _platzierung_setzen(
    objekt_name: str,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    drehachse: str = "Z",
    drehwinkel: float = 0.0,
) -> WerkzeugErgebnis:
    """Setzt Position und optionale Rotation eines Objekts."""
    def do(doc):
        import FreeCAD as App  # noqa: N813
        obj = doc.getObject(objekt_name)
        if obj is None:
            return WerkzeugErgebnis(
                erfolg=False, ausgabe="",
                fehler=f"Objekt '{objekt_name}' nicht gefunden.")

        obj.Placement.Base = App.Vector(x, y, z)

        if drehwinkel != 0.0:
            achsen_map = {
                "X": App.Vector(1, 0, 0),
                "Y": App.Vector(0, 1, 0),
                "Z": App.Vector(0, 0, 1),
            }
            achse = achsen_map.get(drehachse.upper(), App.Vector(0, 0, 1))
            obj.Placement.Rotation = App.Rotation(achse, drehwinkel)

        return WerkzeugErgebnis(
            erfolg=True,
            ausgabe=(f"Platzierung gesetzt: {obj.Label} → "
                     f"({x}, {y}, {z})"
                     + (f", Drehung {drehwinkel}° um {drehachse}"
                        if drehwinkel else "")),
        )

    return _mit_undo("Platzierung setzen", do)


# ── Objekte auflisten ──────────────────────────────────────────────────────

def _objekte_auflisten() -> WerkzeugErgebnis:
    """Listet alle Objekte im aktiven Dokument auf."""
    try:
        import FreeCAD as App  # noqa: N813
    except ImportError:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe="", fehler="FreeCAD nicht verfügbar.")

    doc = App.ActiveDocument
    if doc is None:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe="", fehler="Kein aktives Dokument.")

    zeilen = []
    for obj in doc.Objects:
        zeilen.append(f"  {obj.Name:25s} {obj.TypeId:40s} {obj.Label}")

    ausgabe = f"Dokument '{doc.Name}' — {len(doc.Objects)} Objekt(e):\n"
    ausgabe += "\n".join(zeilen) if zeilen else "  (keine)"

    return WerkzeugErgebnis(
        erfolg=True, ausgabe=ausgabe,
        daten={"count": len(doc.Objects),
               "objects": [{"name": o.Name, "label": o.Label,
                             "type_id": o.TypeId}
                           for o in doc.Objects]},
    )


# ── Makro ausführen (Code-Fallback) ───────────────────────────────────────

def _makro_ausfuehren(code: str) -> WerkzeugErgebnis:
    """Führt beliebigen FreeCAD-Python-Code als Fallback aus.

    Nur verwenden wenn kein spezialisiertes Werkzeug passt.
    Der Code wird in exec() ausgeführt — kein Sandbox!
    """
    import io
    import contextlib

    ausgabe_buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(ausgabe_buf):
            exec(code, {"__builtins__": __builtins__})  # noqa: S102
        ausgabe = ausgabe_buf.getvalue() or "(kein Ausgabe)"
        return WerkzeugErgebnis(erfolg=True, ausgabe=ausgabe)
    except Exception as exc:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe=ausgabe_buf.getvalue(),
            fehler=str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Werkzeug-Register
# ══════════════════════════════════════════════════════════════════════════════

WERKZEUG_REGISTER: dict[str, WerkzeugDefinition] = {}


def _registrieren(defn: WerkzeugDefinition) -> None:
    WERKZEUG_REGISTER[defn.name] = defn


_registrieren(WerkzeugDefinition(
    name="grundkoerper_erstellen",
    beschreibung=(
        "Erstellt einen FreeCAD Part-Grundkörper (Box, Zylinder, Kugel, Kegel, Torus). "
        "Alle Maße in mm. Verwende dieses Werkzeug für einfache 3D-Primitive."
    ),
    kategorie="modellierung",
    handler=_grundkoerper_erstellen,
    parameter=[
        WerkzeugParam("typ", "string",
                      "Art des Grundkörpers",
                      enum=["box", "zylinder", "kugel", "kegel", "torus"]),
        WerkzeugParam("bezeichnung", "string",
                      "Anzeigename des Objekts", pflicht=False, standard=""),
        WerkzeugParam("laenge", "number",
                      "Länge in mm (nur Box)", pflicht=False, standard=20.0),
        WerkzeugParam("breite", "number",
                      "Breite in mm (nur Box)", pflicht=False, standard=20.0),
        WerkzeugParam("hoehe", "number",
                      "Höhe in mm (Box/Zylinder/Kegel)", pflicht=False, standard=20.0),
        WerkzeugParam("radius", "number",
                      "Radius in mm (Zylinder/Kugel/Kegel R1/Torus Ring)",
                      pflicht=False, standard=10.0),
        WerkzeugParam("radius2", "number",
                      "Zweiter Radius in mm (Kegel R2/Torus Rohr)",
                      pflicht=False, standard=3.0),
        WerkzeugParam("x", "number", "X-Position", pflicht=False, standard=0.0),
        WerkzeugParam("y", "number", "Y-Position", pflicht=False, standard=0.0),
        WerkzeugParam("z", "number", "Z-Position", pflicht=False, standard=0.0),
    ],
))

_registrieren(WerkzeugDefinition(
    name="boolean_operation",
    beschreibung=(
        "Führt eine Boolean-Operation zwischen zwei Objekten aus. "
        "'cut' = subtrahiert Werkzeug von Basis, "
        "'fuse' = vereinigt beide, "
        "'common' = Schnittmenge beider Objekte. "
        "Verwende Object.Name (nicht Label) als basis_name und werkzeug_name."
    ),
    kategorie="modellierung",
    handler=_boolean_operation,
    parameter=[
        WerkzeugParam("operation", "string", "Art der Boolean-Operation",
                      enum=["cut", "fuse", "common"]),
        WerkzeugParam("basis_name", "string", "Name (nicht Label) des Basis-Objekts"),
        WerkzeugParam("werkzeug_name", "string", "Name des Werkzeug-Objekts"),
        WerkzeugParam("ergebnis_bezeichnung", "string",
                      "Anzeigename des Ergebnis-Objekts", pflicht=False, standard=""),
    ],
))

_registrieren(WerkzeugDefinition(
    name="platzierung_setzen",
    beschreibung=(
        "Setzt die Position (x, y, z in mm) und optionale Drehung eines Objekts. "
        "Verwende App.Vector-kompatible Werte."
    ),
    kategorie="modellierung",
    handler=_platzierung_setzen,
    parameter=[
        WerkzeugParam("objekt_name", "string", "Name des zu platzierenden Objekts"),
        WerkzeugParam("x", "number", "X-Position in mm", pflicht=False, standard=0.0),
        WerkzeugParam("y", "number", "Y-Position in mm", pflicht=False, standard=0.0),
        WerkzeugParam("z", "number", "Z-Position in mm", pflicht=False, standard=0.0),
        WerkzeugParam("drehachse", "string",
                      "Drehachse (X/Y/Z)", pflicht=False, standard="Z",
                      enum=["X", "Y", "Z"]),
        WerkzeugParam("drehwinkel", "number",
                      "Drehwinkel in Grad", pflicht=False, standard=0.0),
    ],
))

_registrieren(WerkzeugDefinition(
    name="objekte_auflisten",
    beschreibung=(
        "Listet alle Objekte im aktiven FreeCAD-Dokument auf mit Name, TypeId und Label. "
        "Nützlich um den aktuellen Dokumentzustand zu inspizieren."
    ),
    kategorie="inspektion",
    handler=_objekte_auflisten,
    parameter=[],
))

_registrieren(WerkzeugDefinition(
    name="makro_ausfuehren",
    beschreibung=(
        "Führt beliebigen FreeCAD-Python-Code aus. Nur verwenden wenn kein "
        "spezialisiertes Werkzeug die Aufgabe erfüllen kann (z.B. Sketcher, Mesh, "
        "komplexe PartDesign-Operationen). Code ohne Markdown-Fences übergeben."
    ),
    kategorie="code",
    handler=_makro_ausfuehren,
    parameter=[
        WerkzeugParam("code", "string",
                      "Vollständiger, ausführbarer Python/FreeCAD-Code ohne Markdown-Fences"),
    ],
))


# ══════════════════════════════════════════════════════════════════════════════
# Schema-Export & Ausführung
# ══════════════════════════════════════════════════════════════════════════════

def werkzeug_schema(format: str = "anthropic") -> list[dict]:
    """Gibt das Tool-Schema im Format der LLM-API zurück.

    Parameters
    ----------
    format : str
        "anthropic" (default) oder "openai"
    """
    tools = []
    for defn in WERKZEUG_REGISTER.values():
        properties = {}
        pflicht_liste = []

        for param in defn.parameter:
            prop: dict[str, Any] = {
                "type": param.typ,
                "description": param.beschreibung,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.standard is not None:
                prop["default"] = param.standard
            properties[param.name] = prop
            if param.pflicht:
                pflicht_liste.append(param.name)

        schema_objekt = {
            "type": "object",
            "properties": properties,
        }
        if pflicht_liste:
            schema_objekt["required"] = pflicht_liste

        if format == "openai":
            tools.append({
                "type": "function",
                "function": {
                    "name": defn.name,
                    "description": defn.beschreibung,
                    "parameters": schema_objekt,
                },
            })
        else:  # anthropic
            tools.append({
                "name": defn.name,
                "description": defn.beschreibung,
                "input_schema": schema_objekt,
            })

    return tools


def werkzeug_ausfuehren(name: str, kwargs: dict[str, Any]) -> WerkzeugErgebnis:
    """Führt ein registriertes Werkzeug aus.

    Parameters
    ----------
    name : str
        Werkzeugname (wie in WERKZEUG_REGISTER)
    kwargs : dict
        Parameter-Dict (direkt aus dem LLM-Tool-Call)

    Returns
    -------
    WerkzeugErgebnis
        Immer ein Ergebnis-Objekt, nie eine Exception.
    """
    defn = WERKZEUG_REGISTER.get(name)
    if defn is None:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe="",
            fehler=f"Unbekanntes Werkzeug: '{name}'. "
                   f"Verfügbar: {list(WERKZEUG_REGISTER.keys())}")
    try:
        # Standard-Werte für optionale Parameter einsetzen
        gefuellte_kwargs: dict[str, Any] = {}
        for param in defn.parameter:
            if param.name in kwargs:
                gefuellte_kwargs[param.name] = kwargs[param.name]
            elif not param.pflicht and param.standard is not None:
                gefuellte_kwargs[param.name] = param.standard

        return defn.handler(**gefuellte_kwargs)
    except Exception as exc:
        return WerkzeugErgebnis(
            erfolg=False, ausgabe="",
            fehler=f"Fehler beim Ausführen von '{name}': {exc}")
