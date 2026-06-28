# -*- coding: utf-8 -*-
"""
farben.py – Explizite Farbdefinitionen für Hell- und Dunkel-Modus.

Jeder Modus hat sein eigenes Dict. Keine Palette-Erkennung, kein Raten.
"""

DUNKEL = {
    # Syntax-Highlighting
    "keyword":    "#4FC1E9",
    "builtin":    "#56B6C2",
    "self":       "#E06C75",
    "decorator":  "#C678DD",
    "def_name":   "#61AFEF",
    "class_name": "#E5C07B",
    "zahl":       "#98C379",
    "string":     "#D19A66",
    "operator":   "#ABB2BF",
    "kommentar":  "#6A9955",
    "fstring":    "#D19A66",
    "triple":     "#D19A66",
    # Standard-Textfarbe im Code-Editor
    "text":       "#D4D4D4",
    # Semantische Hintergrundfärbung für Eingabefelder
    "tint_suche":   "#1a2e1a",
    "tint_ki":      "#1a1a2e",
    "tint_kontext": "#1a1a2e",
    # Trenner-Label "Code-Block:" Textfarbe
    "label_trenner": "#98C379",
}

HELL = {
    # Syntax-Highlighting
    "keyword":    "#0000CC",
    "builtin":    "#007080",
    "self":       "#A31515",
    "decorator":  "#795E26",
    "def_name":   "#001080",
    "class_name": "#267F99",
    "zahl":       "#098658",
    "string":     "#A31515",
    "operator":   "#383838",
    "kommentar":  "#3A7212",
    "fstring":    "#A31515",
    "triple":     "#A31515",
    # Standard-Textfarbe im Code-Editor
    "text":       "#1E1E1E",
    # Semantische Hintergrundfärbung für Eingabefelder
    "tint_suche":   "#e8f5e9",
    "tint_ki":      "#e8eaf6",
    "tint_kontext": "#e8eaf6",
    # Trenner-Label "Code-Block:" Textfarbe
    "label_trenner": "#3A7212",
}
