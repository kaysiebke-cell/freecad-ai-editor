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

    # ── Part::Cylinder.RadiusInner → äußerer minus innerer Zylinder (Part::Cut) ──
    # RadiusInner gibt es in FreeCAD nicht — KI erfindet dieses Attribut häufig.
    if '.RadiusInner' in code:
        _ri_vars = {
            m.group(1): m.group(2).strip()
            for m in _re.finditer(
                r'^\s*(\w+)\.RadiusInner\s*=\s*(.+)$', code, _re.MULTILINE)
        }
        for var, inner_r in _ri_vars.items():
            m_r = _re.search(
                rf'^\s*{_re.escape(var)}\.Radius\s*=\s*(.+)$', code, _re.MULTILINE)
            m_h = _re.search(
                rf'^\s*{_re.escape(var)}\.Height\s*=\s*(.+)$', code, _re.MULTILINE)
            m_a = _re.search(
                rf'^(\s*){_re.escape(var)}\s*=\s*doc\.addObject\s*\(["\']Part::Cylinder["\']',
                code, _re.MULTILINE)
            outer_r = m_r.group(1).strip() if m_r else "40.0"
            height  = m_h.group(1).strip() if m_h else "10.0"
            ind     = m_a.group(1)         if m_a else ""
            neu = (
                f"{ind}{var}_aussen = doc.addObject('Part::Cylinder', '{var}Aussen')\n"
                f"{ind}{var}_aussen.Radius = {outer_r}\n"
                f"{ind}{var}_aussen.Height = {height}\n"
                f"{ind}{var}_innen = doc.addObject('Part::Cylinder', '{var}Innen')\n"
                f"{ind}{var}_innen.Radius = {inner_r}\n"
                f"{ind}{var}_innen.Height = {height}\n"
                f"{ind}{var} = doc.addObject('Part::Cut', '{var}')\n"
                f"{ind}{var}.Base = {var}_aussen\n"
                f"{ind}{var}.Tool = {var}_innen"
            )
            # addObject-Zeile durch neuen Block ersetzen
            code = _re.sub(
                rf'^[ \t]*{_re.escape(var)}\s*=\s*doc\.addObject\s*\(["\']Part::Cylinder["\'][^\n]*',
                neu, code, flags=_re.MULTILINE)
            # Alte Eigenschafts-Zeilen entfernen (Radius/Height/RadiusInner)
            code = _re.sub(
                rf'^[ \t]*{_re.escape(var)}\.(Radius|Height|RadiusInner)[^\n]*\n?',
                '', code, flags=_re.MULTILINE)
            geaendert = True

    # ── FreeCAD.Vector() → App.Vector() ─────────────────────────────────────────
    if 'FreeCAD.Vector(' in code:
        code = code.replace('FreeCAD.Vector(', 'App.Vector(')
        geaendert = True

    # ── FreeCAD.* Namespace-Aliase → App.* ──────────────────────────────────────
    _FC_API_ALIASE = [
        ('FreeCAD.ActiveDocument',     'App.ActiveDocument'),
        ('FreeCAD.newDocument(',       'App.newDocument('),
        ('FreeCAD.setActiveDocument(', 'App.setActiveDocument('),
        ('FreeCAD.Placement(',         'App.Placement('),
        ('FreeCAD.Rotation(',          'App.Rotation('),
    ]
    for alt, korrekt in _FC_API_ALIASE:
        if alt in code:
            code = code.replace(alt, korrekt)
            geaendert = True

    # ── App.activeDocument() (lowercase a) → App.ActiveDocument ─────────────────
    _ACTIVE_LC = _re.compile(r'App\.activeDocument\s*\(\s*\)')
    if _ACTIVE_LC.search(code):
        code = _ACTIVE_LC.sub('App.ActiveDocument', code)
        geaendert = True

    # ── Fehlendes import math einfügen wenn math.* benutzt ──────────────────────
    _MATH_USE = _re.compile(
        r'\bmath\.(cos|sin|tan|radians|degrees|pi|sqrt|atan2?|floor|ceil)\b')
    if _MATH_USE.search(code) and 'import math' not in code:
        _zm = code.splitlines()
        _letzter_import = next(
            (i for i in reversed(range(len(_zm)))
             if _zm[i].strip().startswith('import ')
             or _zm[i].strip().startswith('from ')),
            -1)
        _zm.insert(_letzter_import + 1, 'import math')
        code = '\n'.join(_zm)
        geaendert = True

    # ── Redundante obj.Placement = App.Placement(...) entfernen ────────────────────
    # Wenn danach obj.Placement.Base = App.Vector(...) steht, ist die erste
    # Zuweisung nutzlos — sie wird sofort überschrieben.
    _PLACE_FULL_ASSIGN = _re.compile(
        r'^(\s*)(\w+)\.Placement\s*=\s*App\.Placement\s*\(')
    _PLACE_BASE_ASSIGN = _re.compile(r'\b(\w+)\.Placement\.Base\s*=')
    _doppelt_placed: set = set()
    for _z in code.splitlines():
        _m = _PLACE_BASE_ASSIGN.search(_z)
        if _m:
            _doppelt_placed.add(_m.group(1))
    if _doppelt_placed:
        _tmp_zeilen = []
        for _z in code.splitlines():
            _m = _PLACE_FULL_ASSIGN.match(_z)
            if _m and _m.group(2) in _doppelt_placed:
                geaendert = True
            else:
                _tmp_zeilen.append(_z)
        code = '\n'.join(_tmp_zeilen)

    # ── Part::Torus .Radius = X → .Radius1 = X ───────────────────────────────────
    _torus_vars = set(_re.findall(
        r'(\w+)\s*=\s*doc\.addObject\s*\(["\']Part::Torus["\']', code))
    if _torus_vars:
        _torus_zeilen = []
        for z in code.splitlines():
            ersetzt = False
            for tv in _torus_vars:
                if _re.match(rf'^\s*{_re.escape(tv)}\.Radius[12]\s*=', z):
                    break  # .Radius1/.Radius2 — schon korrekt
                m = _re.match(rf'^(\s*{_re.escape(tv)})\.Radius(\s*=\s*.+)$', z)
                if m:
                    _torus_zeilen.append(f"{m.group(1)}.Radius1{m.group(2)}")
                    geaendert = True
                    ersetzt = True
                    break
            if not ersetzt:
                _torus_zeilen.append(z)
        code = '\n'.join(_torus_zeilen)

    # ── App.Placement(pos, rot, center) → obj.Placement.Base = pos ─────────────────
    # KI verwechselt das 3. Argument (Rotationszentrum) mit der Z-Position.
    # Erkennung: App.Placement(App.Vector(x,y,z1), App.Rotation(), App.Vector(cx,cy,cz))
    # Nur wenn das Objekt NOCH KEIN späteres .Placement.Base = ... hat.
    _PLACE3_PAT = _re.compile(
        r'^(\s*)(\w+)\.Placement\s*=\s*App\.Placement\s*\(\s*'
        r'App\.Vector\s*\(\s*([^\)]+)\)\s*,\s*'
        r'App\.Rotation\s*\(\s*\)\s*,\s*'
        r'App\.Vector\s*\(\s*([^\)]+)\)\s*\)\s*$'
    )
    _has_base_assign = set(_re.findall(r'\b(\w+)\.Placement\.Base\s*=', code))
    _place3_zeilen = []
    for _z in code.splitlines():
        _m3 = _PLACE3_PAT.match(_z)
        if _m3 and _m3.group(2) not in _has_base_assign:
            ind, obj = _m3.group(1), _m3.group(2)
            pos_args = [v.strip() for v in _m3.group(3).split(',')]
            ctr_args = [v.strip() for v in _m3.group(4).split(',')]
            if len(pos_args) == 3 and len(ctr_args) == 3:
                try:
                    x  = float(pos_args[0]); y  = float(pos_args[1])
                    z1 = float(pos_args[2]); cz = float(ctr_args[2])
                    combined_z = z1 + cz
                    # Schöne Darstellung: 10.0 → 10, 10.5 → 10.5
                    def _fmt(v: float) -> str:
                        return str(int(v)) if v == int(v) else str(v)
                    _place3_zeilen.append(
                        f"{ind}{obj}.Placement.Base = "
                        f"App.Vector({_fmt(x)}, {_fmt(y)}, {_fmt(combined_z)})"
                    )
                    geaendert = True
                    continue
                except (ValueError, IndexError):
                    pass
        _place3_zeilen.append(_z)
    code = '\n'.join(_place3_zeilen)

    # ── Standalone obj.Shape.fuse(other.Shape) entfernen ──────────────────────────
    # Part::Fuse-Objekte brauchen .Base/.Tool — kein direkter Shape-Aufruf.
    # Nur entfernen wenn die Zeile NICHT als Zuweisung (x = ...) vorliegt.
    _SHAPE_FUSE_STANDALONE = _re.compile(
        r'^\s*\w+\.Shape\.(fuse|cut|common)\s*\(\s*\w+(?:\.Shape)?\s*\)\s*$'
    )
    _sf_zeilen = []
    for _z in code.splitlines():
        if _SHAPE_FUSE_STANDALONE.match(_z):
            geaendert = True
        else:
            _sf_zeilen.append(_z)
    code = '\n'.join(_sf_zeilen)

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

    # ── QMessageBox-Importe entfernen ────────────────────────────────────────
    # Prompt verbietet QMessageBox — Importe und try/except-Zeilen entfernen
    if 'QMessageBox' in code:
        _QMSG_ZEILEN = _re.compile(
            r'^\s*(?:try\s*:\s*)?from\s+PySide[26]\.QtWidgets\s+import\s+QMessageBox\s*$'
            r'|^\s*except\s+ImportError\s*:\s*from\s+PySide[26]\.QtWidgets\s+import\s+QMessageBox\s*$'
            r'|^\s*import\s+QMessageBox\s*$',
            _re.MULTILINE
        )
        neuer = _QMSG_ZEILEN.sub('', code)
        if neuer != code:
            code = neuer.strip()
            geaendert = True

    # ── Part::Feature + .Shape= Zeilen entfernen ─────────────────────────────
    # addObject("Part::Feature", ...) erzeugt unnötige Kopien — beide Zeilen weg
    if 'Part::Feature' in code or '.Shape =' in code:
        _FEAT_LINE = _re.compile(
            r'^\s*\w+.*addObject\s*\(\s*["\']Part::Feature["\'][^)]*\).*$'
            r'|^\s*\w+(?:\.\w+)+\.Shape\s*=\s*.+$',
            _re.MULTILINE
        )
        neuer = _FEAT_LINE.sub('', code)
        if neuer != code:
            code = neuer
            geaendert = True

    # ── Part::Compound → Part::Fuse wenn Kontext auf Verschmelzung hindeutet ──
    # Part::Compound ist real, aber falsch für Fuse/Kreuz/Union-Operationen.
    # Nur ersetzen wenn Variablenname oder Kommentar auf Fuse-Absicht hindeutet.
    if "Part::Compound" in code:
        _FUSE_KONTEXT = _re.compile(
            r'\b(fuse|kreuz|cross|union|verschmelz|kombinier|verbind|join|merge)\b',
            _re.IGNORECASE)
        if _FUSE_KONTEXT.search(code):
            code = code.replace("Part::Compound", "Part::Fuse")
            # .Links = [...] → .Base/.Tool aufteilen (Fuse erwartet Base+Tool)
            _LINKS = _re.compile(r'^(\s*)(\w+)\.Links\s*=\s*\[(\w+)\s*,\s*(\w+)\]', _re.MULTILINE)
            def _links_zu_base_tool(m: _re.Match) -> str:
                ind, obj, a, b = m.group(1), m.group(2), m.group(3), m.group(4)
                return f"{ind}{obj}.Base = {a}\n{ind}{obj}.Tool = {b}"
            neuer = _LINKS.sub(_links_zu_base_tool, code)
            if neuer != code:
                code = neuer
            geaendert = True
        else:
            # Part::Compound ohne Fuse-Kontext = Stacking-Szenario (z.B. Pyramide).
            # Das Compound-Objekt und seine .Links-Zuweisung sind überflüssig —
            # die Einzelobjekte sind bereits im Dokument sichtbar.
            # Strategie: addObject("Part::Compound",...)-Zeile + .Links-Zeile entfernen.
            _COMPOUND_VAR = _re.compile(
                r'^\s*(\w+)\s*=\s*doc\.addObject\s*\(["\']Part::Compound["\'][^)]*\)')
            _compound_vars: set = set()
            for _z in code.splitlines():
                _mc = _COMPOUND_VAR.match(_z)
                if _mc:
                    _compound_vars.add(_mc.group(1))
            if _compound_vars:
                _LINKS_ANY = _re.compile(r'^\s*\w+\.Links\s*=\s*\[')
                _cmp_zeilen = []
                for _z in code.splitlines():
                    _mc = _COMPOUND_VAR.match(_z)
                    if _mc:
                        geaendert = True
                        continue   # Compound-addObject-Zeile entfernen
                    # .Links-Zuweisung auf Compound-Variable entfernen
                    if _LINKS_ANY.match(_z):
                        _obj_m = _re.match(r'^\s*(\w+)\.Links\s*=', _z)
                        if _obj_m and _obj_m.group(1) in _compound_vars:
                            geaendert = True
                            continue
                    _cmp_zeilen.append(_z)
                code = '\n'.join(_cmp_zeilen)

    # ── Part::Compound.Shapes = [...x.Shape...] → .Links = [...x...] ─────────
    _COMPOUND_SHAPES = _re.compile(r'(\w+)\.Shapes\s*=\s*\[([^\]]+)\]')
    def _fix_compound_shapes(m: _re.Match) -> str:
        obj   = m.group(1)
        items = _re.sub(r'(\w+)\.Shape\b', r'\1', m.group(2))
        return f"{obj}.Links = [{items}]"
    neuer = _COMPOUND_SHAPES.sub(_fix_compound_shapes, code)
    if neuer != code:
        code = neuer
        geaendert = True

    # ── try/except QMessageBox-Wrapper entfernen ──────────────────────────────
    # KI wickelt Code oft in try/except+QMessageBox ein — das versteckt
    # Laufzeitfehler vor der Sandbox. Wrapper entfernen, Körper beibehalten.
    if 'QMessageBox' in code:
        zeilen = code.splitlines()
        neue_zeilen: list = []
        i = 0
        while i < len(zeilen):
            z = zeilen[i]
            if z.strip() == 'try:' and not z[0:1] in (' ', '\t'):
                # Top-level try: — Körper sammeln
                j = i + 1
                while j < len(zeilen) and (not zeilen[j].strip() or zeilen[j][:1] in (' ', '\t')):
                    j += 1
                try_koerper = zeilen[i + 1:j]
                # Nachfolgendes except prüfen
                if j < len(zeilen) and zeilen[j].strip().startswith('except'):
                    k = j + 1
                    while k < len(zeilen) and (not zeilen[k].strip() or zeilen[k][:1] in (' ', '\t')):
                        k += 1
                    except_body = zeilen[j + 1:k]
                    if any('QMessageBox' in ez for ez in except_body) and try_koerper:
                        min_ind = min(
                            (len(l) - len(l.lstrip()) for l in try_koerper if l.strip()),
                            default=4)
                        for kz in try_koerper:
                            neue_zeilen.append(kz[min_ind:] if kz.strip() else '')
                        geaendert = True
                        i = k
                        continue
                neue_zeilen.append(z)
                i += 1
            else:
                neue_zeilen.append(z)
                i += 1
        code = "\n".join(neue_zeilen)

    # ── .Base = xxx.Shape / .Tool = xxx.Shape → .Base = xxx ─────────────────
    # Part::Fuse/Cut/Common erwarten DocumentObject, nicht Part.Shape
    _BASE_TOOL_SHAPE = _re.compile(
        r'^(\s*\w+\.(?:Base|Tool)\s*=\s*\w+)\.Shape(\s*)$'
    )
    _bt_zeilen = []
    for z in code.splitlines():
        m = _BASE_TOOL_SHAPE.match(z)
        if m:
            z = m.group(1) + m.group(2)
            geaendert = True
        _bt_zeilen.append(z)
    code = "\n".join(_bt_zeilen)

    # ── Part.show(obj) / Part.show(obj.Shape) entfernen wenn obj per addObject ─
    # Objekte die per doc.addObject() erstellt wurden sind bereits im Dokument —
    # Part.show() darauf erzeugt Duplikate.
    _add_obj_vars = set(_re.findall(r'(\w+)\s*=\s*doc\.addObject\s*\(', code))
    if _add_obj_vars:
        _PART_SHOW_LINE = _re.compile(r'^\s*Part\.show\((\w+)(?:\.Shape)?\)\s*$')
        ps_zeilen = []
        for z in code.splitlines():
            m = _PART_SHOW_LINE.match(z)
            if m and m.group(1) in _add_obj_vars:
                geaendert = True
            else:
                ps_zeilen.append(z)
        code = "\n".join(ps_zeilen)

    zeilen = code.splitlines()

    # ── Reguläre Ausdrücke für API-Muster ─────────────────────────────────
    _MAKE = _re.compile(
        r'^(\s*)(\w+)\s*=\s*Part\.(makeBox|makeCylinder|makeSphere|makeCone|makeTorus)'
        r'\(([^)]*)\)'
    )
    _CUT          = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.cut\((\w+)\)')
    _FUSE         = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.fuse\((\w+)\)')
    _SHAPE_CUT    = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.Shape\.cut\((\w+)(?:\.Shape)?\)')
    _SHAPE_FUSE   = _re.compile(r'^(\s*)(\w+)\s*=\s*(\w+)\.Shape\.fuse\((\w+)(?:\.Shape)?\)')
    _PART_FEATURE = _re.compile(r'^(\s*)(\w+)\s*=\s*doc\.addObject\(["\']Part::Feature["\']')
    _SHAPE_ASSIGN = _re.compile(r'^(\s*)(\w+)\.Shape\s*=\s*(\w+)\s*$')
    _DIM_SET          = _re.compile(r'(\w+)\.(Length|Width)\s*=\s*([\d.]+(?:e[\d.]+)?)')
    _PLACEMENT_FULL   = _re.compile(r'^(\s*)(\w+)\.Placement\.Base\s*=\s*App\.Vector\(')
    _PLACEMENT_PART   = _re.compile(r'^(\s*)(\w+)\.Placement\.Base\.[xyz]\s*=')
    _APP_GUI          = _re.compile(r'(App|FreeCAD)\.Gui\b')
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
    _feature_vars: set = set()
    _box_dims:     dict = {}   # {varname: {Length: str, Width: str}}
    _hat_placement: set = set()  # vars mit explizitem Placement.Base

    def _fuse_mit_zentrierung(indent, result, basis, tool):
        """Gibt Zeilen für Part::Fuse zurück, mit auto-Zentrierung wenn nötig."""
        zeilen_out = []
        for var in (basis, tool):
            if var in _box_dims and var not in _hat_placement:
                dims = _box_dims[var]
                l = dims.get("Length", f"{var}.Length")
                w = dims.get("Width",  f"{var}.Width")
                zeilen_out.append(
                    f"{indent}{var}.Placement.Base = "
                    f"App.Vector(-({l}) / 2, -({w}) / 2, 0)")
        zeilen_out.append(f"{indent}{result} = doc.addObject('Part::Fuse', '{result}')")
        zeilen_out.append(f"{indent}{result}.Base = {basis}")
        zeilen_out.append(f"{indent}{result}.Tool = {tool}")
        return zeilen_out

    for z in zeilen:
        if _APP_SHOW.match(z):
            geaendert = True
            continue

        # ── App.Gui-Aufrufe entfernen (halluziniert, schlägt im Makro fehl) ──
        if _APP_GUI.search(z):
            mv = _re.match(r'^\s*(\w+)\s*=', z)
            if mv:
                _feature_vars.add(mv.group(1))
            geaendert = True
            continue
        # Folgeaufrufe auf entfernte Gui-Variablen ebenfalls entfernen
        if _feature_vars:
            first_word = _re.match(r'^\s*(\w+)\.', z)
            if first_word and first_word.group(1) in _feature_vars:
                geaendert = True
                continue

        # ── Teilweise Placement-Zuweisung (.Base.x/y/z) entfernen ────────
        # Diese werden durch korrekte App.Vector-Zentrierung ersetzt
        if _PLACEMENT_PART.match(z):
            geaendert = True
            continue

        # ── Dimensionen und Placement tracken ─────────────────────────────
        for varname, dim, val in _DIM_SET.findall(z):
            _box_dims.setdefault(varname, {})[dim] = val.strip()

        if _PLACEMENT_FULL.match(z):
            m2 = _PLACEMENT_FULL.match(z)
            _hat_placement.add(m2.group(2))

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
            neue_zeilen.extend(_fuse_mit_zentrierung(indent, result, basis, tool))
            geaendert = True
            continue

        m = _SHAPE_FUSE.match(z)
        if m:
            indent, result, basis, tool = m.groups()
            neue_zeilen.extend(_fuse_mit_zentrierung(indent, result, basis, tool))
            geaendert = True
            continue

        m = _SHAPE_CUT.match(z)
        if m:
            indent, result, basis, tool = m.groups()
            neue_zeilen.append(f"{indent}{result} = doc.addObject('Part::Cut', '{result}')")
            neue_zeilen.append(f"{indent}{result}.Base = {basis}")
            neue_zeilen.append(f"{indent}{result}.Tool = {tool}")
            geaendert = True
            continue

        m = _PART_FEATURE.match(z)
        if m:
            _feature_vars.add(m.group(2))
            geaendert = True
            continue

        m = _SHAPE_ASSIGN.match(z)
        if m and m.group(2) in _feature_vars:
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
            neue_zeilen.extend(_fuse_mit_zentrierung(indent, result, basis, tool))
            geaendert = True
            continue

        m = _FUSE_AUG.match(z)
        if m:
            indent, varname, tool = m.groups()
            tmp = f"{varname}_fuse"
            neue_zeilen.extend(_fuse_mit_zentrierung(indent, tmp, varname, tool))
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

    # ── 2. Durchlauf: Zentrierung für Part::Fuse ohne Placement ──────────────
    # Erkennt korrekt geschriebene Part::Fuse-Blöcke und fügt fehlende
    # Placement.Base-Zeilen ein (gilt auch wenn Modell Fuse korrekt schrieb).
    _FUSE_ADD  = _re.compile(
        r'^(\s*)(\w+)\s*=\s*doc\.addObject\(["\']Part::Fuse["\']')
    _BASE_TOOL = _re.compile(r'^(\s*)(\w+)\.(Base|Tool)\s*=\s*(\w+)')

    # Zweiter Durchlauf: Dimensionen + Placements nochmal aus dem (evtl.
    # bereits korrigierten) Code sammeln, dann Zentrierung einfügen.
    dims2: dict = {}
    placed2: set = set()
    # z_only_placed: Vars die nur App.Vector(0, 0, X) haben (falsche Zentrierung)
    _Z_ONLY = _re.compile(
        r'^(\s*)(\w+)\.Placement\.Base\s*=\s*App\.Vector\(\s*0\s*,\s*0\s*,')
    z_only_placed: set = set()
    for z in neue_zeilen:
        for vn, dim, val in _DIM_SET.findall(z):
            dims2.setdefault(vn, {})[dim] = val.strip()
        if _PLACEMENT_FULL.match(z):
            placed2.add(_PLACEMENT_FULL.match(z).group(2))
        mz = _Z_ONLY.match(z)
        if mz:
            z_only_placed.add(mz.group(2))

    # Fuse-Objekte und ihre Base/Tool ermitteln
    fuse_vars: dict = {}   # {fuse_varname: (index_der_fuse_zeile, indent)}
    base_tool_info: dict = {}  # {fuse_varname: {Base: var, Tool: var}}
    for i, z in enumerate(neue_zeilen):
        m = _FUSE_ADD.match(z)
        if m:
            fuse_vars[m.group(2)] = (i, m.group(1))
        m = _BASE_TOOL.match(z)
        if m:
            _, obj, attr, val = m.groups()
            if obj in fuse_vars:
                base_tool_info.setdefault(obj, {})[attr] = val

    # Falsche z-only Placements für Fuse-Vars ersetzen
    _Z_ONLY_REPL = _re.compile(
        r'^(\s*\w+\.Placement\.Base\s*=\s*App\.Vector\s*\(\s*0\s*,\s*0\s*,)[^)]*\)')
    for i, z in enumerate(neue_zeilen):
        mz = _Z_ONLY.match(z)
        if mz:
            var = mz.group(2)
            # Prüfen ob var als Base/Tool in einem Fuse verwendet wird
            for bt in base_tool_info.values():
                if var in bt.values() and var in dims2:
                    d = dims2[var]
                    l = d.get("Length", f"{var}.Length")
                    w = d.get("Width",  f"{var}.Width")
                    ind = mz.group(1)
                    neue_zeilen[i] = (
                        f"{ind}{var}.Placement.Base = "
                        f"App.Vector(-({l}) / 2, -({w}) / 2, 0)")
                    placed2.discard(var)
                    z_only_placed.discard(var)
                    geaendert = True
                    break

    # Zentrierung vor der Fuse-Zeile einfügen (rückwärts damit Indizes stimmen)
    for fuse_var in reversed(list(fuse_vars)):
        idx, indent = fuse_vars[fuse_var]
        info = base_tool_info.get(fuse_var, {})
        basis = info.get("Base")
        tool  = info.get("Tool")
        zeilen_einfuegen = []
        for var in (basis, tool):
            if var and var in dims2 and var not in placed2:
                d = dims2[var]
                l = d.get("Length", f"{var}.Length")
                w = d.get("Width",  f"{var}.Width")
                zeilen_einfuegen.append(
                    f"{indent}{var}.Placement.Base = "
                    f"App.Vector(-({l}) / 2, -({w}) / 2, 0)")
                placed2.add(var)
        if zeilen_einfuegen:
            for j, zl in enumerate(zeilen_einfuegen):
                neue_zeilen.insert(idx + j, zl)
            geaendert = True

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
