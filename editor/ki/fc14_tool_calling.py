# -*- coding: utf-8 -*-
"""
fc14_tool_calling.py
─────────────────────
FC14 · Objekt-Befehle — echtes API Tool-Calling für Ollama.

Ollama /api/chat + tools-Array zwingt das Modell zur strukturierten
JSON-Ausgabe. Kein Text-Prompt mehr — das Protokoll erzwingt das Format.

Für Cloud-Anbieter (Fallback): Text-Prompt mit ist_tool_call_antwort/
parse_und_generiere_code als Erkennung und Konvertierung.
"""

from __future__ import annotations
import re as _re
import ast as _ast

# ══════════════════════════════════════════════════════════════════════════════
# Tool-Schema für Ollama /api/chat (JSON — kein Text-Prompt)
# ══════════════════════════════════════════════════════════════════════════════

FC14_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "box",
            "description": "Create a rectangular box (Part::Box). Use multiple box() + fuse() for L/T/U profiles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":   {"type": "string", "description": "Unique object name"},
                    "length": {"type": "number", "description": "Length in mm (X axis)"},
                    "width":  {"type": "number", "description": "Width in mm (Y axis)"},
                    "height": {"type": "number", "description": "Height in mm (Z axis)"},
                    "x":      {"type": "number", "description": "X position (default 0)"},
                    "y":      {"type": "number", "description": "Y position (default 0)"},
                    "z":      {"type": "number", "description": "Z position (default 0)"},
                },
                "required": ["name", "length", "width", "height"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cylinder",
            "description": "Create a cylinder (Part::Cylinder). For holes: always follow with cut().",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":   {"type": "string"},
                    "radius": {"type": "number", "description": "Radius in mm. M3=1.6 M4=2.1 M5=2.6 M6=3.3 M8=4.3 M10=5.3"},
                    "height": {"type": "number", "description": "Height in mm"},
                    "x":      {"type": "number"},
                    "y":      {"type": "number"},
                    "z":      {"type": "number"},
                },
                "required": ["name", "radius", "height"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sphere",
            "description": "Create a sphere (Part::Sphere).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":   {"type": "string"},
                    "radius": {"type": "number"},
                    "x":      {"type": "number"},
                    "y":      {"type": "number"},
                    "z":      {"type": "number"},
                },
                "required": ["name", "radius"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cone",
            "description": "Create a cone (Part::Cone). r2=0 for pointed tip.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":   {"type": "string"},
                    "r1":     {"type": "number", "description": "Bottom radius in mm"},
                    "r2":     {"type": "number", "description": "Top radius in mm (0 = pointed)"},
                    "height": {"type": "number"},
                    "x":      {"type": "number"},
                    "y":      {"type": "number"},
                    "z":      {"type": "number"},
                },
                "required": ["name", "r1", "r2", "height"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fuse",
            "description": "Join two objects (Part::Fuse / union). Use to combine legs of L/T/U profiles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the result"},
                    "base": {"type": "string", "description": "Name of the base object"},
                    "tool": {"type": "string", "description": "Name of the object to join"},
                },
                "required": ["name", "base", "tool"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cut",
            "description": "Subtract tool from base (Part::Cut / boolean difference). Use for every hole or pocket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the result"},
                    "base": {"type": "string", "description": "Name of the base object"},
                    "tool": {"type": "string", "description": "Name of the object to subtract"},
                },
                "required": ["name", "base", "tool"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "common",
            "description": "Intersection of two objects (Part::Common).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "base": {"type": "string"},
                    "tool": {"type": "string"},
                },
                "required": ["name", "base", "tool"],
            },
        },
    },
]

# ── System-Prompt (Fallback für Cloud-Anbieter) ────────────────────────────────

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

# ══════════════════════════════════════════════════════════════════════════════
# Konvertierung: Ollama tool_calls JSON → FreeCAD Python
# ══════════════════════════════════════════════════════════════════════════════

def tool_calls_zu_code(tool_calls: list) -> str:
    """Wandelt Ollama tool_calls-Liste in FreeCAD-Python-Code um."""
    alle_zeilen: list[str] = []

    for tc in tool_calls:
        func_data = tc.get("function", {})
        func_name = func_data.get("name", "").lower()
        args = func_data.get("arguments", {})

        if isinstance(args, str):
            try:
                import json as _json
                args = _json.loads(args)
            except Exception:
                continue

        konv = _konvertiere_json(func_name, args)
        if konv:
            alle_zeilen.extend(konv)
            alle_zeilen.append("")

    if not alle_zeilen:
        return ""

    body = "\n".join(f"    {z}" if z else "" for z in alle_zeilen).rstrip()
    return _wrap_code(body)


# ══════════════════════════════════════════════════════════════════════════════
# Konvertierung: Text-Tool-Calls (Cloud-Fallback) → FreeCAD Python
# ══════════════════════════════════════════════════════════════════════════════

_TOOL_NAMES = ("box", "cylinder", "sphere", "cone", "fuse", "cut", "common")
_RE_TOOL_LINE = _re.compile(
    r'^\s*(' + '|'.join(_TOOL_NAMES) + r')\s*\(', _re.IGNORECASE)
_RE_CALL = _re.compile(r'^\s*(\w+)\s*\((.+)\)\s*$', _re.DOTALL)


def ist_tool_call_antwort(text: str) -> bool:
    zeilen = [z.strip() for z in text.strip().splitlines()
              if z.strip() and not z.strip().startswith('#')]
    if not zeilen:
        return False
    treffer = sum(1 for z in zeilen if _RE_TOOL_LINE.match(z))
    return treffer >= max(1, len(zeilen) * 0.5)


def parse_und_generiere_code(text: str) -> str:
    """Text-Tool-Calls (Cloud-Fallback) in FreeCAD-Python-Code umwandeln."""
    alle_zeilen: list[str] = []

    for zeile in text.strip().splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith('#'):
            continue
        m = _RE_CALL.match(zeile)
        if not m:
            continue
        args = _parse_text_args(m.group(2))
        if args is None:
            continue
        konv = _konvertiere_text(m.group(1).lower(), args)
        if konv:
            alle_zeilen.extend(konv)
            alle_zeilen.append("")

    if not alle_zeilen:
        return ""

    body = "\n".join(f"    {z}" if z else "" for z in alle_zeilen).rstrip()
    return _wrap_code(body)


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def _wrap_code(body: str) -> str:
    return (
        "# -*- coding: utf-8 -*-\n"
        "import FreeCAD as App\n"
        "try:\n"
        "    from PySide2.QtWidgets import QMessageBox\n"
        "except ImportError:\n"
        "    from PySide6.QtWidgets import QMessageBox\n"
        'doc = App.ActiveDocument or App.newDocument("Modell")\n'
        "try:\n"
        f"{body}\n"
        "    doc.recompute()\n"
        "except Exception as e:\n"
        '    QMessageBox.critical(None, "Fehler", str(e))\n'
    )


def _f(v, default=0.0) -> str:
    try:
        return str(float(v))
    except Exception:
        return str(float(default))


def _sanitize(name: str) -> str:
    name = _re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    if name and name[0].isdigit():
        name = '_' + name
    return name or 'obj'


def _pos(args: dict, keys=("x", "y", "z")) -> tuple[str, str, str]:
    return _f(args.get(keys[0], 0)), _f(args.get(keys[1], 0)), _f(args.get(keys[2], 0))


def _konvertiere_json(func: str, args: dict) -> list[str] | None:
    zeilen: list[str] = []

    if func == "box":
        n = _sanitize(args.get("name", "Box"))
        l, w, h = _f(args.get("length", 10)), _f(args.get("width", 10)), _f(args.get("height", 10))
        x, y, z = _pos(args)
        zeilen.append(f'{n} = doc.addObject("Part::Box", "{n}")')
        zeilen.append(f"{n}.Length = {l}; {n}.Width = {w}; {n}.Height = {h}")
        if x != "0.0" or y != "0.0" or z != "0.0":
            zeilen.append(f"{n}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func == "cylinder":
        n = _sanitize(args.get("name", "Cylinder"))
        r, h = _f(args.get("radius", 5)), _f(args.get("height", 10))
        x, y, z = _pos(args)
        zeilen.append(f'{n} = doc.addObject("Part::Cylinder", "{n}")')
        zeilen.append(f"{n}.Radius = {r}; {n}.Height = {h}")
        if x != "0.0" or y != "0.0" or z != "0.0":
            zeilen.append(f"{n}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func == "sphere":
        n = _sanitize(args.get("name", "Sphere"))
        r = _f(args.get("radius", 5))
        x, y, z = _pos(args)
        zeilen.append(f'{n} = doc.addObject("Part::Sphere", "{n}")')
        zeilen.append(f"{n}.Radius = {r}")
        if x != "0.0" or y != "0.0" or z != "0.0":
            zeilen.append(f"{n}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func == "cone":
        n = _sanitize(args.get("name", "Cone"))
        r1, r2, h = _f(args.get("r1", 5)), _f(args.get("r2", 0)), _f(args.get("height", 10))
        x, y, z = _pos(args)
        zeilen.append(f'{n} = doc.addObject("Part::Cone", "{n}")')
        zeilen.append(f"{n}.Radius1 = {r1}; {n}.Radius2 = {r2}; {n}.Height = {h}")
        if x != "0.0" or y != "0.0" or z != "0.0":
            zeilen.append(f"{n}.Placement.Base = App.Vector({x}, {y}, {z})")

    elif func in ("fuse", "cut", "common"):
        n    = _sanitize(args.get("name", "Result"))
        base = _sanitize(args.get("base", ""))
        tool = _sanitize(args.get("tool", ""))
        if not base or not tool:
            return None
        typ = {"fuse": "Part::Fuse", "cut": "Part::Cut", "common": "Part::Common"}[func]
        zeilen.append(f'{n} = doc.addObject("{typ}", "{n}")')
        zeilen.append(f"{n}.Base = {base}; {n}.Tool = {tool}")
        zeilen.append("doc.recompute()")

    else:
        return None

    return zeilen or None


def _parse_text_args(args_str: str):
    try:
        return _ast.literal_eval(f"({args_str},)")
    except Exception:
        return None


def _konvertiere_text(func: str, args: tuple) -> list[str] | None:
    """Text-Tool-Call-Tupel in Python-Zeilen umwandeln (Cloud-Fallback)."""
    d: dict = {}
    if func == "box" and len(args) >= 4:
        d = {"name": args[0], "length": args[1], "width": args[2], "height": args[3]}
        if len(args) > 4: d["x"] = args[4]
        if len(args) > 5: d["y"] = args[5]
        if len(args) > 6: d["z"] = args[6]
    elif func == "cylinder" and len(args) >= 3:
        d = {"name": args[0], "radius": args[1], "height": args[2]}
        if len(args) > 3: d["x"] = args[3]
        if len(args) > 4: d["y"] = args[4]
        if len(args) > 5: d["z"] = args[5]
    elif func == "sphere" and len(args) >= 2:
        d = {"name": args[0], "radius": args[1]}
        if len(args) > 2: d["x"] = args[2]
        if len(args) > 3: d["y"] = args[3]
        if len(args) > 4: d["z"] = args[4]
    elif func == "cone" and len(args) >= 4:
        d = {"name": args[0], "r1": args[1], "r2": args[2], "height": args[3]}
        if len(args) > 4: d["x"] = args[4]
        if len(args) > 5: d["y"] = args[5]
        if len(args) > 6: d["z"] = args[6]
    elif func in ("fuse", "cut", "common") and len(args) >= 3:
        d = {"name": args[0], "base": args[1], "tool": args[2]}
    else:
        return None
    return _konvertiere_json(func, d)
