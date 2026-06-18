# -*- coding: utf-8 -*-
"""
kod_korrektor.py
────────────────
Reine Code-Korrektur- und Filterungsfunktionen (kein Qt, kein self).

  freecad_code_korrigieren      – erkennt und korrigiert fehlerhafte FreeCAD-API-Aufrufe
  extrahiere_code_aus_nl_antwort – filtert Python-Code aus gemischtem NL+Code-Text
  schneide_erklaerung_ab         – schneidet Erklärungstext nach dem Code ab
  kommentiere_text_zeilen        – kommentiert Nicht-Python-Zeilen mit #
"""

import re as _re


# ── FreeCAD-Code korrigieren ──────────────────────────────────────────────────

def freecad_code_korrigieren(code: str):
    """Erkennt und ersetzt fehlerhafte Part.make*()-Aufrufe durch doc.addObject().

    Gibt (korrigierter_code, wurde_geaendert) zurück.
    """
    # ── Kein doc.addObject() obwohl FreeCAD importiert ───────────────────
    hat_freecad_import = any(
        "import FreeCAD" in z or "import App" in z for z in code.splitlines())
    hat_add_object = "doc.addObject(" in code or "addObject(" in code
    if hat_freecad_import and not hat_add_object:
        return (
            "# ❌ UNGÜLTIGER FREECAD-CODE — KI hat Python-Datenstrukturen generiert\n"
            "#    statt echter FreeCAD-Geometrie-Aufrufe.\n"
            "#\n"
            "# Kein einziges doc.addObject() gefunden!\n"
            "# Beispiel für korrekte Kugel:\n"
            "#   kugel = doc.addObject('Part::Sphere', 'Kugel')\n"
            "#   kugel.Radius = 30\n"
            "#   doc.recompute()\n"
            "#\n"
            "# Bitte KI-Beschreibung erneut senden.", True)

    # ── Blender-API-Erkennung (sofortiger Abbruch) ────────────────────
    _FALSCHE_APIS = {
        "bpy":     "Blender",
        "bmesh":   "Blender",
        "maya":    "Maya",
        "rhino":   "Rhino",
        "cadquery":"CadQuery",
        "numpy":   "NumPy (kein FreeCAD)",
        "stl":     "STL-Bibliothek (kein FreeCAD)",
        "trimesh": "Trimesh (kein FreeCAD)",
        "open3d":  "Open3D (kein FreeCAD)",
    }
    for zeile in code.splitlines():
        s = zeile.strip()
        for api, name in _FALSCHE_APIS.items():
            if _re.match(rf'^import\s+{api}\b', s) or _re.match(rf'^from\s+{api}\b', s):
                fehler_code = (
                    f"# ❌ FALSCHE API — KI hat {name}-Code generiert statt FreeCAD-Code!\n"
                    f"#\n"
                    f"# Die KI hat 'import {api}' verwendet. Das ist die {name}-API\n"
                    f"# und funktioniert NICHT in FreeCAD.\n"
                    f"#\n"
                    f"# Lösung: Beschreibung erneut an die KI schicken und dabei\n"
                    f"# explizit auf FreeCAD hinweisen, z.B.:\n"
                    f"#   \"Erstelle FreeCAD-Python-Makro für: ...\"\n"
                    f"#\n"
                    f"# Originaler (fehlerhafter) Code wurde nicht ausgeführt."
                )
                return fehler_code, True

    geaendert = False

    # ── Erfundene FreeCAD-Objekte ersetzen ────────────────────────────────
    _FAKE_OBJECTS = {
        "Part::UnionForTwoVolumes": "Part::Fuse",
        "Part::Union":              "Part::Fuse",
        "Part::BooleanUnion":       "Part::Fuse",
        "Part::Merge":              "Part::Fuse",
        "Part::BooleanCut":         "Part::Cut",
        "Part::Subtract":           "Part::Cut",
        "Part::Difference":         "Part::Cut",
        "Part::Intersection":       "Part::Common",
        "Part::BooleanIntersection":"Part::Common",
    }
    for falsch, richtig in _FAKE_OBJECTS.items():
        if falsch in code:
            code = code.replace(falsch, richtig)
            geaendert = True

    # ── Falsche Eigenschaftsnamen korrigieren ──────────────────────────────
    _PROP_FIXES = [
        (_re.compile(r'^(\s*\w+)\.Length(\s*=\s*\d)'), r'\1.Height\2',
         lambda z: any(k in z for k in (
             "Cylinder", "Zylinder", "zyl", "cylinder", "bohrung", "Bohrung"))),
    ]
    prop_zeilen = []
    for z in code.splitlines():
        for muster, ersatz, bedingung in _PROP_FIXES:
            if bedingung(z) and muster.search(z):
                z = muster.sub(ersatz, z)
                geaendert = True
        prop_zeilen.append(z)
    code = "\n".join(prop_zeilen)

    # ── obj.Add(x) → obj.Base/obj.Tool ────────────────────────────────────
    _ADD = _re.compile(r'^(\s*)(\w+)\.Add\((\w+)\)\s*$')
    _add_zaehler: dict = {}
    _add_zeilen = []
    for z in code.splitlines():
        m = _ADD.match(z)
        if m:
            indent, obj, arg = m.group(1), m.group(2), m.group(3)
            n = _add_zaehler.get(obj, 0)
            _add_zaehler[obj] = n + 1
            attr = "Base" if n == 0 else "Tool"
            _add_zeilen.append(f"{indent}{obj}.{attr} = {arg}")
            geaendert = True
        else:
            _add_zeilen.append(z)
    code = "\n".join(_add_zeilen)

    zeilen = code.splitlines()

    # ── Reguläre Ausdrücke für API-Muster ─────────────────────────────────
    _MAKE = _re.compile(
        r'^(\s*)(\w+)\s*=\s*Part\.(makeBox|makeCylinder|makeSphere|makeCone|makeTorus)'
        r'\(([^)]*)\)'
    )
    _CUT      = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.cut\((\w+)\)')
    _FUSE     = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.fuse\((\w+)\)')
    _CUT_OP   = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\s*-\s*(\w+)\s*$')
    _CUT_AUG  = _re.compile(r'^(\s*)(\w+)\s*-=\s*(\w+)\s*$')
    _FUSE_OP  = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)\s*$')
    _FUSE_AUG = _re.compile(r'^(\s*)(\w+)\s*\+=\s*(\w+)\s*$')
    _APPEND   = _re.compile(r'^(\s*)(\w+)\.append\((\w+)\)\s*$')
    _APP_SHOW = _re.compile(r'^\s*App\.show\s*\(')

    _TYP_MAP = {
        "makeBox":      ("Part::Box",      ["Length", "Width", "Height"]),
        "makeCylinder": ("Part::Cylinder", ["Radius", "Height"]),
        "makeSphere":   ("Part::Sphere",   ["Radius"]),
        "makeCone":     ("Part::Cone",     ["Radius1", "Radius2", "Height"]),
        "makeTorus":    ("Part::Torus",    ["Radius1", "Radius2"]),
    }

    # ── Prefix prüfen ─────────────────────────────────────────────────────
    hat_app_import = any("import FreeCAD as App" in z for z in zeilen)
    hat_doc        = any("doc = App." in z or "doc=App." in z for z in zeilen)

    prefix_zeilen = []
    if not hat_app_import:
        prefix_zeilen.append("import FreeCAD as App")
        geaendert = True
    if not hat_doc:
        prefix_zeilen.append(
            "doc = App.ActiveDocument or App.newDocument('Neu')")
        geaendert = True

    # ── Vorpass: verschachtelte Part.make*(…) aufsplitten ─────────────────
    _INLINE_MAKE = _re.compile(
        r'Part\.(makeBox|makeCylinder|makeSphere|makeCone|makeTorus)\(([^)]*)\)')
    tmp_zaehler = [0]
    neue_zeilen_pre = []
    for z in zeilen:
        treffer = list(_INLINE_MAKE.finditer(z))
        if treffer and not _MAKE.match(z):
            indent = len(z) - len(z.lstrip())
            ind = " " * indent
            for t in treffer:
                tmp_name = f"_tmp{tmp_zaehler[0]}"
                tmp_zaehler[0] += 1
                neue_zeilen_pre.append(f"{ind}{tmp_name} = {t.group(0)}")
                z = z.replace(t.group(0), tmp_name)
                geaendert = True
        neue_zeilen_pre.append(z)
    zeilen = neue_zeilen_pre

    zaehler = {}
    var_typ: dict = {}
    neue_zeilen = []

    for z in zeilen:
        if _APP_SHOW.match(z):
            geaendert = True
            continue

        m = _MAKE.match(z)
        if m:
            indent, varname, fn, args = m.groups()
            typ, felder = _TYP_MAP[fn]
            short = typ.split("::")[-1]
            zaehler[short] = zaehler.get(short, 0) + 1
            arg_liste = [a.strip() for a in args.split(",") if a.strip()]
            neue_zeilen.append(f"{indent}{varname} = doc.addObject('{typ}', '{varname}')")
            for i, feld in enumerate(felder):
                if i < len(arg_liste):
                    neue_zeilen.append(f"{indent}{varname}.{feld} = {arg_liste[i]}")
            var_typ[varname] = typ
            geaendert = True
            continue

        m = _CUT.match(z)
        if m:
            indent, result, basis, tool = m.groups()
            neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Cut', '{result}')")
            neue_zeilen.append(f"{indent}{result}.Base = {basis}")
            neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
            geaendert = True
            continue

        m = _FUSE.match(z)
        if m:
            indent, result, basis, tool = m.groups()
            neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Fuse', '{result}')")
            neue_zeilen.append(f"{indent}{result}.Base = {basis}")
            neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
            geaendert = True
            continue

        m = _APPEND.match(z)
        if m:
            indent, varname, tool = m.groups()
            if varname in var_typ:
                tmp = f"{varname}_fuse"
                neue_zeilen.append(f"{indent}{tmp} = doc.addObject('Part::Fuse', '{tmp}')")
                neue_zeilen.append(f"{indent}{tmp}.Base = {varname}")
                neue_zeilen.append(f"{indent}{tmp}.Tool = {tool}")
                neue_zeilen.append(f"{indent}{varname} = {tmp}")
                geaendert = True
                continue

        m = _CUT_OP.match(z)
        if m:
            indent, result, basis, tool = m.groups()
            neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Cut', '{result}')")
            neue_zeilen.append(f"{indent}{result}.Base = {basis}")
            neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
            geaendert = True
            continue

        m = _CUT_AUG.match(z)
        if m:
            indent, varname, tool = m.groups()
            tmp = f"{varname}_cut"
            neue_zeilen.append(f"{indent}{tmp} = doc.addObject('Part::Cut', '{tmp}')")
            neue_zeilen.append(f"{indent}{tmp}.Base = {varname}")
            neue_zeilen.append(f"{indent}{tmp}.Tool = {tool}")
            neue_zeilen.append(f"{indent}{varname} = {tmp}")
            geaendert = True
            continue

        m = _FUSE_OP.match(z)
        if m:
            indent, result, basis, tool = m.groups()
            neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Fuse', '{result}')")
            neue_zeilen.append(f"{indent}{result}.Base = {basis}")
            neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
            geaendert = True
            continue

        m = _FUSE_AUG.match(z)
        if m:
            indent, varname, tool = m.groups()
            tmp = f"{varname}_fuse"
            neue_zeilen.append(f"{indent}{tmp} = doc.addObject('Part::Fuse', '{tmp}')")
            neue_zeilen.append(f"{indent}{tmp}.Base = {varname}")
            neue_zeilen.append(f"{indent}{tmp}.Tool = {tool}")
            neue_zeilen.append(f"{indent}{varname} = {tmp}")
            geaendert = True
            continue

        neue_zeilen.append(z)

    # Prefix-Zeilen nach dem letzten Import einfügen
    if prefix_zeilen:
        letzter_import = -1
        for i, z in enumerate(neue_zeilen):
            s = z.strip()
            if s.startswith("import ") or s.startswith("from "):
                letzter_import = i
        einfuge = letzter_import + 1
        for j, pz in enumerate(prefix_zeilen):
            neue_zeilen.insert(einfuge + j, pz)

    return "\n".join(neue_zeilen), geaendert


# ── NL-Antwort-Filter ─────────────────────────────────────────────────────────

def extrahiere_code_aus_nl_antwort(text: str) -> str:
    """Filtert Python-Code aus einer gemischten NL-Antwort (Text + Code).

    Strategie:
      1. Expliziter ```python```-Block → nur den nehmen
      2. Zeilenweise klassifizieren, Text als #-Kommentare anhängen
      3. Fallback: Originaltext unverändert
    """
    # Strategie 1: expliziter ```python```-Block
    fence_match = _re.search(
        r"```(?:python)?\s*\n(.*?)```", text, _re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip().replace("\t", "    ")

    # Strategie 2: zeilenweise klassifizieren
    _CODE_STARTS = (
        "#", "import ", "from ", "def ", "class ", "try:", "except",
        "finally:", "if ", "elif ", "else:", "for ", "while ", "with ",
        "return ", "yield ", "raise ", "pass", "break", "continue",
        "doc", "box", "zyl", "cut", "fuse", "obj", "pad", "body",
        "sketch", "pocket", "result", "shape", "mesh", "part",
        "print(", "App.", "FreeCAD", "Gui.", "Part.", "Sketcher.",
    )
    _AUFZAEHLUNG = _re.compile(r"^\s*[\*\-\d]+[\.\)]\s")

    zeilen      = text.splitlines()
    code_zeilen = []
    text_zeilen = []
    in_code     = False

    for zeile in zeilen:
        stripped = zeile.strip()

        if not stripped:
            if in_code:
                code_zeilen.append("")
            continue

        ist_aufzaehlung = bool(_AUFZAEHLUNG.match(zeile))
        ist_eingerueckt = zeile.startswith("    ") or zeile.startswith("\t")
        ist_code_token  = any(stripped.startswith(s) for s in _CODE_STARTS)
        ist_konstante   = bool(
            _re.match(r"^[A-Z_]{2,}\s*=\s*[\d\"\'\-]", stripped))
        ist_zuweisung   = bool(
            _re.match(
                r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*[\(\[=]",
                stripped)
        ) and not _re.match(r"^[A-Z][a-z]", stripped)

        ist_code = (
            (ist_code_token or ist_eingerueckt or ist_konstante or ist_zuweisung)
            and not ist_aufzaehlung
        )

        if ist_code:
            in_code = True
            code_zeilen.append(zeile)
        elif in_code:
            if stripped and not ist_aufzaehlung:
                text_zeilen.append(f"# {stripped}")
            elif ist_aufzaehlung:
                sauber = _AUFZAEHLUNG.sub("", stripped)
                text_zeilen.append(f"# {sauber}")

    ergebnis = "\n".join(code_zeilen).strip().replace("\t", "    ")
    if text_zeilen:
        ergebnis += "\n\n" + "\n".join(text_zeilen)

    return ergebnis if ergebnis.strip() else text


def schneide_erklaerung_ab(text: str) -> str:
    """Schneidet Erklärungstext und Zusammenfassungs-Kommentare nach dem Code ab."""
    _ZUSAMMENFASSUNG = (
        "# zusammenfassung", "# das skript", "# hinweis",
        "# erklärung", "# ergebnis", "# dieser code",
        "# note:", "# summary:", "# this script",
    )
    _CODE_STARTS = (
        "import ", "from ", "def ", "class ", "try:", "except",
        "finally:", "if ", "elif ", "else:", "for ", "while ", "with ",
        "return ", "yield ", "raise ", "pass", "break", "continue",
        "print(", "App.", "doc", "box", "zyl", "cut", "fuse",
        "obj", "pad", "body", "sketch", "result",
    )
    zeilen = text.splitlines()
    letzte_code_zeile = 0
    for i, zeile in enumerate(zeilen):
        s = zeile.strip()
        if not s:
            continue
        if s.startswith("#") and any(
                s.lower().startswith(k) for k in _ZUSAMMENFASSUNG):
            continue
        ist_code = (
            any(s.startswith(k) for k in _CODE_STARTS)
            or zeile.startswith("    ")
            or zeile.startswith("\t")
            or bool(_re.match(r"^[A-Z_]{2,}\s*=", s))
            or bool(
                _re.match(
                    r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*[\(\[=]",
                    s)
                and not _re.match(r"^[A-Z][a-z]", s))
            or (s.startswith("#") and not any(
                s.lower().startswith(k) for k in _ZUSAMMENFASSUNG))
        )
        if ist_code:
            letzte_code_zeile = i
    return "\n".join(zeilen[:letzte_code_zeile + 1]).strip()


def kommentiere_text_zeilen(text: str) -> str:
    """Stellt Nicht-Python-Zeilen ein '#' voran um SyntaxError zu vermeiden."""
    _CODE_STARTS = (
        "#", "import ", "from ", "def ", "class ", "try:", "except",
        "finally:", "if ", "elif ", "else:", "for ", "while ", "with ",
        "return ", "yield ", "raise ", "pass", "break", "continue",
        "doc", "App.", "FreeCAD", "Gui.", "Part.", "Sketcher.",
        "print(", "```",
    )
    ergebnis = []
    for zeile in text.splitlines():
        s = zeile.strip()
        if not s:
            ergebnis.append(zeile)
            continue
        ist_eingerueckt = zeile.startswith("    ") or zeile.startswith("\t")
        ist_code = (
            ist_eingerueckt
            or any(s.startswith(t) for t in _CODE_STARTS)
            or _re.match(r"^[A-Za-z_]\w*\s*[=\(\[]", s)
        )
        if ist_code:
            ergebnis.append(zeile)
        else:
            ergebnis.append(f"# {s}")
    return "\n".join(ergebnis)
