# -*- coding: utf-8 -*-
"""
theme.py  –  Öffentliches API des Design-Systems.

Importiert alles aus den Sub-Modulen.
Bestehender Code (import theme; theme.STY_X) läuft weiterhin unverändert.

Sub-Module:
    theme_schrift  – Schriften, apply_global_font, stabilize_*
    theme_farben   – Farbschema, ist_dunkel, syntax_farben, STY_CODE_EDITOR
    theme_styles   – UI-Texte, alle anderen STY_* Funktionen und Konstanten
"""

from theme_schrift import *   # noqa: F401, F403
from theme_farben import *    # noqa: F401, F403
from theme_styles import *    # noqa: F401, F403
