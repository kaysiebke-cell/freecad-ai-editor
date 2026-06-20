# -*- coding: utf-8 -*-
"""
kod_analyse.py
──────────────
Reine Analyse-Funktionen ohne Qt-Abhängigkeiten:
  - erstelle_code_sitemap: AST-basiertes Inhaltsverzeichnis
  - extrahiere_fehler_kontext: Code-Ausschnitt um Fehlerzeile
"""

import ast
import re as _re


def erstelle_code_sitemap(code_text: str) -> str:
    """Parst Code per AST und liefert ein kompaktes Inhaltsverzeichnis.

    Gibt "" zurück wenn der Code leer oder syntaktisch unvollständig ist.
    """
    if not code_text.strip():
        return ""
    try:
        root = ast.parse(code_text)
    except SyntaxError:
        return ""

    linien = []
    for node in root.body:
        if isinstance(node, ast.ClassDef):
            linien.append(f"Klasse {node.name} (Zeile {node.lineno}):")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in sub.args.args if a.arg != "self"]
                    linien.append(f"   └─ {sub.name}({', '.join(args)})")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            linien.append(
                f"Funktion {node.name}({', '.join(args)}) (Zeile {node.lineno})")

    return "\n".join(linien) if linien else ""


def extrahiere_fehler_kontext(code_text: str, fehler_meldung: str,
                               puffer: int = 5) -> str:
    """Sucht Zeilennummer aus Traceback und gibt umgebenden Code-Ausschnitt zurück.

    Die fehlerhafte Zeile wird mit '──▶' markiert.
    Gibt "" zurück wenn keine Zeilennummer gefunden wird.
    """
    match = _re.search(r"(?:line|Zeile)\s+(\d+)", fehler_meldung, _re.IGNORECASE)
    if not match:
        return ""

    ziel   = int(match.group(1))
    zeilen = code_text.splitlines()
    start  = max(0, ziel - 1 - puffer)
    ende   = min(len(zeilen), ziel + puffer)

    block = []
    for i in range(start, ende):
        nr     = i + 1
        prefix = "──▶ " if nr == ziel else "    "
        block.append(f"{prefix}{nr:4d}: {zeilen[i]}")

    return "\n".join(block)
