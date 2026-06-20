# -*- coding: utf-8 -*-
"""
fc14_tool_calling.py
─────────────────────
FC14 · Objekt-Befehle — Tool-Calling-Modus für lokale Modelle.

Statt rohen Python-Code zu generieren gibt das Modell einfache
Befehle aus (box, cylinder, fuse, cut …) die hier in FreeCAD-
Python-Code umgewandelt werden.

Vorteil: Kleine Modelle (7b) müssen keine FreeCAD-Syntax kennen —
nur WELCHE Objekte und WELCHE Operationen gebraucht werden.
"""

from __future__ import annotations
import re as _re
import ast as _ast

# ── System-Prompt (kompakt für Ollama) ────────────────────────────────────────

FC14_SYSTEM_PROMPT = """\
You are a FreeCAD assistant. Output ONLY tool calls — no Python, no text, no explanations.

AVAILABLE TOOLS (one call per line):
box("Name", length, width, height, x=0, y=0, z=0)
cylinder("Name", radius, height, x=0, y=0, z=0)
sphere("Name", radius, x=0, y=0, z=0)
cone("Name", r1, r2, height, x=0, y=0, z=0)
fuse("Name", "base", "tool")
cut("Name", "base", "tool")
common("Name", "base", "tool")

SCREW SIZES — radius in mm:
M3=1.6  M4=2.1  M5=2.6  M6=3.3  M8=4.3  M10=5.3  M12=6.6

RULES:
- L/T/U/Z-profile = multiple box() calls + fuse() to join them
- Every hole = cylinder() + cut() — NEVER leave a cylinder without a cut
- "two M6 holes" = 2 cylinders (r=3.3) + 2 cuts  (M6 is SIZE not count)
- x,y,z = placement of the object corner/origin
- Output ONLY tool calls, one per line, nothing else
"""

# ── Erkennung ──────────────────────────────────────────────────────────────────

_TOOL_NAMES = ("box", "cylinder", "sphere", "cone", "fuse", "cut", "common")
_RE_TOOL_LINE = _re.compile(
    r'^\s*(' + '|'.join(_TOOL_NAMES) + r')\s*\(', _re.IGNORECASE)


def ist_tool_call_antwort(text: str) -> bool:
    """Gibt True zurück wenn der Text hauptsächlich Tool-Calls enthält."""
    zeilen = [z.strip() for z in text.strip().splitlines()
              if z.strip() and not z.strip().startswith('#')]
    if not zeilen:
        return False
    treffer = sum(1 for z in zeilen if _RE_TOOL_LINE.match(z))
    return treffer >= max(1, len(zeilen) * 0.5)


# ── Parser + Code-Generator ────────────────────────────────────────────────────

_RE_CALL = _re.compile(
    r'^\s*(\w+)\s*\((.+)\)\s*$', _re.DOTALL)


def _parse_args(args_str: str) -> tuple | None:
    try:
        return _ast.literal_eval(f"({args_str},)")
    except Exception:
        return None


def _sanitize(name: str) -> str:
    name = _re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    if name and name[0].isdigit():
        name = '_' + name
    return name or 'obj'


def _f(v) -> str:
    """Float-Formatierung: 10.0 → '10.0', 3.3 → '3.3'"""
    return str(float(v))


def _konvertiere(func: str, args: tuple) -> list[str] | None:
    func = func.lower()
    zeilen: list[str] = []

    if func == "box":
        if len(args) < 4:
            return None
        name = _sanitize(args[0])
        l, w, h = _f(args[1]), _f(args[2]), _f(args[3])
        x = _f(args[4]) if len(args) > 4 else "0"
        y = _f(args[5]) if len(args) > 5 else "0"
        z = _f(args[6]) if len(args) > 6 else "0"
        zeilen.append(f'{name} = doc.addObject("Part::Box", "{name}")')
        zeilen.append(f"{name}.Length = {l}; {name}.Width = {w}; {name}.Height = {h}")
        if x != "0" or y != "0" or z != "0":
            zeilen.append(f"{name}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func == "cylinder":
        if len(args) < 3:
            return None
        name = _sanitize(args[0])
        r, h = _f(args[1]), _f(args[2])
        x = _f(args[3]) if len(args) > 3 else "0"
        y = _f(args[4]) if len(args) > 4 else "0"
        z = _f(args[5]) if len(args) > 5 else "0"
        zeilen.append(f'{name} = doc.addObject("Part::Cylinder", "{name}")')
        zeilen.append(f"{name}.Radius = {r}; {name}.Height = {h}")
        if x != "0" or y != "0" or z != "0":
            zeilen.append(f"{name}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func == "sphere":
        if len(args) < 2:
            return None
        name = _sanitize(args[0])
        r = _f(args[1])
        x = _f(args[2]) if len(args) > 2 else "0"
        y = _f(args[3]) if len(args) > 3 else "0"
        z = _f(args[4]) if len(args) > 4 else "0"
        zeilen.append(f'{name} = doc.addObject("Part::Sphere", "{name}")')
        zeilen.append(f"{name}.Radius = {r}")
        if x != "0" or y != "0" or z != "0":
            zeilen.append(f"{name}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func == "cone":
        if len(args) < 4:
            return None
        name = _sanitize(args[0])
        r1, r2, h = _f(args[1]), _f(args[2]), _f(args[3])
        x = _f(args[4]) if len(args) > 4 else "0"
        y = _f(args[5]) if len(args) > 5 else "0"
        z = _f(args[6]) if len(args) > 6 else "0"
        zeilen.append(f'{name} = doc.addObject("Part::Cone", "{name}")')
        zeilen.append(f"{name}.Radius1 = {r1}; {name}.Radius2 = {r2}; {name}.Height = {h}")
        if x != "0" or y != "0" or z != "0":
            zeilen.append(f"{name}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func in ("fuse", "cut", "common"):
        if len(args) < 3:
            return None
        name = _sanitize(args[0])
        base = _sanitize(args[1])
        tool = _sanitize(args[2])
        typ = {"fuse": "Part::Fuse", "cut": "Part::Cut", "common": "Part::Common"}[func]
        zeilen.append(f'{name} = doc.addObject("{typ}", "{name}")')
        zeilen.append(f"{name}.Base = {base}; {name}.Tool = {tool}")
        zeilen.append("doc.recompute()")

    else:
        return None

    return zeilen


def parse_und_generiere_code(text: str) -> str:
    """Wandelt Tool-Call-Antwort in vollständigen FreeCAD-Python-Code um."""
    alle_zeilen: list[str] = []

    for zeile in text.strip().splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith('#'):
            continue
        m = _RE_CALL.match(zeile)
        if not m:
            continue
        func = m.group(1)
        args = _parse_args(m.group(2))
        if args is None:
            continue
        konv = _konvertiere(func, args)
        if konv:
            alle_zeilen.extend(konv)
            alle_zeilen.append("")  # Leerzeile zwischen Operationen

    if not alle_zeilen:
        return ""

    body = "\n".join(f"    {z}" if z else "" for z in alle_zeilen).rstrip()

    return (
        "# -*- coding: utf-8 -*-\n"
        "import FreeCAD as App\n"
        "try:\n"
        "    from PySide2.QtWidgets import QMessageBox\n"
        "except ImportError:\n"
        "    from PySide6.QtWidgets import QMessageBox\n"
        "doc = App.ActiveDocument or App.newDocument(\"Modell\")\n"
        "try:\n"
        f"{body}\n"
        "    doc.recompute()\n"
        "except Exception as e:\n"
        "    QMessageBox.critical(None, \"Fehler\", str(e))\n"
    )
