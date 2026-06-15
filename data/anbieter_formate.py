# -*- coding: utf-8 -*-
"""
anbieter_formate.py
───────────────────
Zentrale Datenbank: welcher KI-Anbieter unterstützt welche Bild- und Datei-Formate.

Verwendung:
    from anbieter_formate import ANBIETER_FORMATE, datei_filter, hat_vision

Struktur je Anbieter:
    vision       – bool: unterstützt Bilder überhaupt
    bilder       – Liste der unterstützten Bild-Dateiendungen (ohne Punkt, Kleinbuchstaben)
    max_bild_mb  – maximale Bildgröße in MB (None = kein Limit)
    max_bilder   – maximale Anzahl Bilder pro Anfrage (None = kein Limit)
    pdf          – bool: unterstützt PDF-Dokumente
    dokumente    – weitere Dokumentformate (txt, docx, csv …)
    hinweis      – optionaler Hinweis (z.B. welche Modelle Vision haben)
"""

from __future__ import annotations

ANBIETER_FORMATE: dict[str, dict] = {

    # ── Lokal ─────────────────────────────────────────────────────────────────
    "Ollama (Lokal)": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp", "gif", "bmp"],
        "max_bild_mb": None,    # läuft lokal, kein Server-Limit
        "max_bilder":  None,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit Vision-Modellen: llava, bakllava, moondream, minicpm-v",
    },

    # ── Anthropic ─────────────────────────────────────────────────────────────
    "Anthropic (Claude)": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "gif", "webp"],
        "max_bild_mb": 5,
        "max_bilder":  20,
        "pdf":         True,    # via Files-API / base64
        "dokumente":   ["pdf", "txt"],
        "hinweis":     "GIF: nur erstes Bild wird verarbeitet",
    },

    # ── OpenAI ────────────────────────────────────────────────────────────────
    "OpenAI (ChatGPT)": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "gif", "webp"],
        "max_bild_mb": 20,
        "max_bilder":  10,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit gpt-4o, gpt-4-turbo; gpt-3.5 hat kein Vision",
    },

    # ── GitHub Copilot ────────────────────────────────────────────────────────
    "GitHub Copilot": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "gif", "webp"],
        "max_bild_mb": 20,
        "max_bilder":  10,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Basiert auf gpt-4o — gleiche Limits wie OpenAI",
    },

    # ── Google ────────────────────────────────────────────────────────────────
    "Gemini (Google)": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "gif", "webp", "heic", "heif"],
        "max_bild_mb": 20,
        "max_bilder":  16,
        "pdf":         True,
        "dokumente":   ["pdf", "txt", "csv", "docx", "xlsx", "pptx",
                        "mp3", "mp4", "wav", "avi", "mov"],
        "hinweis":     "Breiteste Format-Unterstützung inkl. Audio und Video",
    },

    # ── DeepSeek ──────────────────────────────────────────────────────────────
    "DeepSeek": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp"],
        "max_bild_mb": 10,
        "max_bilder":  4,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit deepseek-vl2 Modell; andere Modelle kein Vision",
    },

    # ── Groq ──────────────────────────────────────────────────────────────────
    "Groq": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp"],
        "max_bild_mb": 4,
        "max_bilder":  5,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit llama-3.2-11b-vision oder llama-3.2-90b-vision",
    },

    # ── Mistral ───────────────────────────────────────────────────────────────
    "Mistral": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp", "gif"],
        "max_bild_mb": 10,
        "max_bilder":  8,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit Pixtral-12B oder pixtral-large",
    },

    # ── Together AI ───────────────────────────────────────────────────────────
    "Together AI": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp"],
        "max_bild_mb": 5,
        "max_bilder":  4,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit Llama-3.2-Vision oder anderen Vision-Modellen",
    },

    # ── HuggingFace ───────────────────────────────────────────────────────────
    "HuggingFace": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp", "gif", "bmp", "tiff"],
        "max_bild_mb": 10,
        "max_bilder":  4,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit Multimodal-Modellen (Idefics, LLaVA, InternVL …)",
    },

    # ── xAI (Grok) ────────────────────────────────────────────────────────────
    "xAI (Grok)": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "gif", "webp"],
        "max_bild_mb": 10,
        "max_bilder":  5,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit grok-2-vision oder grok-vision-beta",
    },

    # ── Fireworks AI ──────────────────────────────────────────────────────────
    "Fireworks AI": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp"],
        "max_bild_mb": 5,
        "max_bilder":  4,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit firellava oder llama-v3p2-vision Modellen",
    },

    # ── Moonshot ──────────────────────────────────────────────────────────────
    "Moonshot": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp", "gif"],
        "max_bild_mb": 5,
        "max_bilder":  10,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit moonshot-v1-8k-vision",
    },

    # ── Qwen (Alibaba) ────────────────────────────────────────────────────────
    "Qwen (Alibaba)": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp", "gif", "bmp", "tiff"],
        "max_bild_mb": 10,
        "max_bilder":  20,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit Qwen-VL Modellen (qwen-vl-max, qwen-vl-plus)",
    },

    # ── Cohere ────────────────────────────────────────────────────────────────
    "Cohere": {
        "vision":      False,
        "bilder":      [],
        "max_bild_mb": None,
        "max_bilder":  None,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Kein Vision-Support — nur Text",
    },

    # ── SambaNova ─────────────────────────────────────────────────────────────
    "SambaNova": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp"],
        "max_bild_mb": 5,
        "max_bilder":  4,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit Llama-3.2-Vision Modellen",
    },

    # ── MiniMax ───────────────────────────────────────────────────────────────
    "MiniMax": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp"],
        "max_bild_mb": 10,
        "max_bilder":  10,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit MiniMax-VL Modellen",
    },

    # ── Llama API ─────────────────────────────────────────────────────────────
    "Llama API": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "webp"],
        "max_bild_mb": 5,
        "max_bilder":  4,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Nur mit Llama-3.2-Vision Modellen",
    },

    # ── OpenRouter ────────────────────────────────────────────────────────────
    "OpenRouter (Cloud)": {
        "vision":      True,
        "bilder":      ["jpeg", "jpg", "png", "gif", "webp"],
        "max_bild_mb": 20,
        "max_bilder":  20,
        "pdf":         False,
        "dokumente":   [],
        "hinweis":     "Abhängig vom gerouteten Modell — variiert stark",
    },
}


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def hat_vision(anbieter: str) -> bool:
    """Gibt True zurück wenn der Anbieter Bilder unterstützt."""
    info = ANBIETER_FORMATE.get(anbieter)
    return bool(info and info.get("vision"))


def hat_pdf(anbieter: str) -> bool:
    """Gibt True zurück wenn der Anbieter PDFs unterstützt."""
    info = ANBIETER_FORMATE.get(anbieter)
    return bool(info and info.get("pdf"))


def datei_filter(anbieter: str) -> str:
    """
    Gibt einen Qt-Dateifilter-String zurück, z.B. für QFileDialog.
    Beispiel: 'Bilder (*.png *.jpg *.jpeg *.webp)'
    """
    info = ANBIETER_FORMATE.get(anbieter, {})
    endungen = info.get("bilder", [])
    if not endungen:
        return "Alle Dateien (*)"
    muster = " ".join(f"*.{e}" for e in sorted(set(endungen)))
    return f"Bilder ({muster})"


def format_info(anbieter: str) -> str:
    """
    Gibt einen lesbaren Info-Text zurück für Tooltips oder Status-Anzeige.
    Beispiel: 'PNG, JPG, WebP · max 5 MB · max 20 Bilder'
    """
    info = ANBIETER_FORMATE.get(anbieter)
    if not info:
        return "Unbekannter Anbieter"
    if not info.get("vision"):
        return "Kein Bild-Support"

    endungen = ", ".join(e.upper() for e in sorted(set(info.get("bilder", []))))
    max_mb   = info.get("max_bild_mb")
    max_bld  = info.get("max_bilder")
    hinweis  = info.get("hinweis", "")

    teile = [endungen]
    if max_mb:
        teile.append(f"max {max_mb} MB")
    if max_bld:
        teile.append(f"max {max_bld} Bilder")
    result = " · ".join(teile)
    if hinweis:
        result += f"\n{hinweis}"
    return result


def format_pruefen(anbieter: str, dateiendung: str) -> bool:
    """
    Prüft ob eine Dateiendung für diesen Anbieter erlaubt ist.
    dateiendung z.B. 'jpg', '.PNG', 'webp'
    """
    endung = dateiendung.lstrip(".").lower()
    info   = ANBIETER_FORMATE.get(anbieter, {})
    return endung in info.get("bilder", [])
