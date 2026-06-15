# -*- coding: utf-8 -*-
"""
ki_modi.py
──────────
Expertise-Modus Konstanten — kein UI-Code.
"""

MODUS_ANFAENGER = "anfaenger"
MODUS_EXPERTE   = "experte"
MODUS_DEFAULT   = MODUS_ANFAENGER

MODUS_LABELS = {
    MODUS_ANFAENGER: "🟢 Anfänger",
    MODUS_EXPERTE:   "🔵 Experte",
}

# ── Kurze Modus-Prefixes — nur das Nötigste ───────────────────────────────────
# Bewusst minimalistisch: jedes Wort kostet Ollama Rechenzeit
MODUS_PROMPTS = {
    MODUS_ANFAENGER:
        "Antworte auf Deutsch. Erkläre kurz nach dem Code was er macht. "
        "Keine Fachbegriffe ohne Erklärung.\n\n",

    MODUS_EXPERTE:
        "Antworte auf Deutsch. Nur Code, kein Erklärungstext.\n\n",
}

MODUS_TOOLTIPS = {
    MODUS_ANFAENGER: (
        "Anfänger-Modus:\n"
        "Die KI erklärt alles in einfachen Worten.\n"
        "Keine Fachbegriffe ohne Erklärung.\n"
        "Ideal für FreeCAD-Einsteiger."
    ),
    MODUS_EXPERTE: (
        "Experten-Modus:\n"
        "Die KI antwortet knapp und technisch.\n"
        "Fachbegriffe werden vorausgesetzt.\n"
        "Ideal für erfahrene Python-Entwickler."
    ),
}
