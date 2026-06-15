# -*- coding: utf-8 -*-
"""
dokument_kontext.py
────────────────────
FreeCAD-Dokumentzustand für KI-Prompts.

Robuste Version: versucht das aktive Dokument über mehrere API-Wege
zu finden — auch wenn App.ActiveDocument None zurückgibt.
"""

from __future__ import annotations


def _hole_aktives_dokument():
    """Gibt das aktive FreeCAD-Dokument zurück — mit mehreren Fallbacks.

    FreeCAD 1.x gibt App.ActiveDocument manchmal None zurück obwohl
    ein Dokument offen ist. Daher mehrere Wege versuchen.
    """
    try:
        import FreeCAD as App
    except ImportError:
        return None

    # ── Weg 1: Standard-API ───────────────────────────────────────────────
    doc = App.ActiveDocument
    if doc is not None:
        return doc

    # ── Weg 2: Über FreeCADGui aktives Dokument ───────────────────────────
    try:
        import FreeCADGui as Gui
        if Gui.ActiveDocument:
            name = Gui.ActiveDocument.Document.Name
            doc = App.getDocument(name)
            if doc:
                return doc
    except Exception:
        pass

    # ── Weg 3: Erstes geöffnetes Dokument nehmen ──────────────────────────
    try:
        docs = App.listDocuments()
        if docs:
            first_name = list(docs.keys())[0]
            doc = App.getDocument(first_name)
            if doc:
                return doc
    except Exception:
        pass

    return None


def get_dokument_kontext() -> str:
    """Gibt einen Text-Snapshot des aktiven FreeCAD-Dokuments zurück."""
    try:
        import FreeCAD as App
    except ImportError:
        return "(FreeCAD nicht verfügbar)"

    doc = _hole_aktives_dokument()
    if doc is None:
        # Fallback: neues Dokument anlegen
        try:
            doc = App.newDocument("Neues_Modell")
            App.setActiveDocument(doc.Name)
        except Exception:
            pass
    if doc is None:
        return "Kein Dokument geöffnet."

    zeilen: list[str] = []
    zeilen.append(f'Dokument: "{doc.Name}"')
    zeilen.append(f"Datei: {doc.FileName or '(nicht gespeichert)'}")

    # ── Aktiver Body (PartDesign) ──────────────────────────────────────────
    aktiver_body = _aktiver_body()
    if aktiver_body:
        zeilen.append(f"Aktiver Body: {aktiver_body.Label}")

    # ── Objekte ───────────────────────────────────────────────────────────
    objekte = doc.Objects
    if not objekte:
        zeilen.append("Objekte: (keine)")
    else:
        zeilen.append(f"Objekte ({len(objekte)}):")
        kinder_von: dict[str, list[str]] = {}
        hat_elternteil: set[str] = set()
        for obj in objekte:
            kinder = _kinder_holen(obj)
            if kinder:
                kinder_von[obj.Name] = kinder
                hat_elternteil.update(kinder)
        for obj in objekte:
            if obj.Name not in hat_elternteil:
                _format_objekt(obj, zeilen, einzug=1,
                               kinder_von=kinder_von,
                               aktiver_body=aktiver_body,
                               doc=doc)

    # ── Selektion ─────────────────────────────────────────────────────────
    try:
        import FreeCADGui as Gui
        sel = Gui.Selection.getSelectionEx()
        if sel:
            teile = []
            for s in sel:
                if s.SubElementNames:
                    for sub in s.SubElementNames:
                        teile.append(f"{s.ObjectName}.{sub}")
                else:
                    teile.append(s.ObjectName)
            zeilen.append(f"Selektion: {', '.join(teile)}")
    except Exception:
        pass

    return "\n".join(zeilen)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _aktiver_body():
    try:
        import FreeCADGui as Gui
        if Gui.ActiveDocument:
            av = Gui.ActiveDocument.ActiveView
            if hasattr(av, "getActiveObject"):
                return av.getActiveObject("pdbody")
    except Exception:
        pass
    return None


def _kinder_holen(obj) -> list[str]:
    if hasattr(obj, "Group"):
        return [o.Name for o in obj.Group]
    return []


def _format_objekt(obj, zeilen, einzug, kinder_von, aktiver_body, doc):
    prefix = "  " * einzug + "- "
    type_id = getattr(obj, "TypeId", type(obj).__name__)
    aktiv_tag = " [aktiv]" if (aktiver_body and obj.Name == aktiver_body.Name) else ""
    props = _schluessel_eigenschaften(obj)
    props_str = (" — " + ", ".join(props)) if props else ""
    zeilen.append(f"{prefix}{obj.Label} ({type_id}){aktiv_tag}{props_str}")
    for kind_name in kinder_von.get(obj.Name, []):
        kind_obj = doc.getObject(kind_name)
        if kind_obj:
            _format_objekt(kind_obj, zeilen, einzug + 1, kinder_von, aktiver_body, doc)


def _schluessel_eigenschaften(obj) -> list[str]:
    props: list[str] = []
    type_id: str = getattr(obj, "TypeId", "")

    if "Part::Box" in type_id:
        _ap(props, obj, "Length", "L={:.1f}")
        _ap(props, obj, "Width",  "B={:.1f}")
        _ap(props, obj, "Height", "H={:.1f}")
    elif "Part::Cylinder" in type_id:
        _ap(props, obj, "Radius", "R={:.1f}")
        _ap(props, obj, "Height", "H={:.1f}")
    elif "Part::Sphere" in type_id:
        _ap(props, obj, "Radius", "R={:.1f}")
    elif "Part::Cone" in type_id:
        _ap(props, obj, "Radius1", "R1={:.1f}")
        _ap(props, obj, "Radius2", "R2={:.1f}")
        _ap(props, obj, "Height",  "H={:.1f}")
    elif "Part::Torus" in type_id:
        _ap(props, obj, "Radius1", "Ring={:.1f}")
        _ap(props, obj, "Radius2", "Rohr={:.1f}")
    elif any(t in type_id for t in ("Cut", "Fuse", "Common")):
        base = getattr(obj, "Base", None)
        tool = getattr(obj, "Tool", None)
        if base: props.append(f"Base:{base.Label}")
        if tool: props.append(f"Tool:{tool.Label}")
    elif "Sketcher" in type_id:
        try:
            props.append(f"{obj.GeometryCount} Geo")
            fc = getattr(obj, "FullyConstrained", None)
            if fc is not None:
                props.append("OK" if fc else "unter-best.")
        except Exception:
            pass
    elif "Pad" in type_id or "Pocket" in type_id:
        _ap(props, obj, "Length", "L={:.1f}")

    return props


def _ap(props, obj, attr, fmt="{}"):
    try:
        val = getattr(obj, attr)
        props.append(fmt.format(val) if isinstance(val, float) else f"{attr}:{val}")
    except Exception:
        pass


# ── Prompt-Baustein ────────────────────────────────────────────────────────────

def baue_kontext_prompt(basis_system: str, agents_datei: str = "") -> str:
    teile = [basis_system]

    kontext = get_dokument_kontext()
    if kontext and "nicht verfügbar" not in kontext:
        teile.append(
            "\n\u2501\u2501\u2501 AKTUELLER FREECAD-ZUSTAND \u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            + kontext
        )

    agents_text = _lade_agents_md(agents_datei)
    if agents_text:
        teile.append(
            "\n\u2501\u2501\u2501 PROJEKTSPEZIFISCHE ANWEISUNGEN (AGENTS.md) \u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            + agents_text
        )

    return "\n".join(teile)


def _lade_agents_md(pfad: str) -> str:
    if not pfad:
        return ""
    try:
        import os
        if os.path.isfile(pfad):
            with open(pfad, encoding="utf-8") as f:
                inhalt = f.read().strip()
            if len(inhalt) > 2000:
                inhalt = inhalt[:2000] + "\n… (gekürzt)"
            return inhalt
    except Exception:
        pass
    return ""
