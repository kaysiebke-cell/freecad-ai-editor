#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gif_erstellen.py
────────────────
Erstellt ki_makro_editor_demo.gif aus vorhandenen Screenshots ODER per Live-Aufnahme.

Modus 1 – Demo aus Screenshots:
    python3 gif_erstellen.py --screenshots /pfad/zu/ordner/

Modus 2 – Live-Aufnahme (erfordert xdotool + scrot):
    python3 gif_erstellen.py --live

Ausgabe: ui/assets/ki_makro_editor_demo.gif
"""

import argparse
import os
import sys
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Pfade ─────────────────────────────────────────────────────────────────────
_HIER   = Path(__file__).parent
AUSGABE = _HIER / "ui" / "assets" / "ki_makro_editor_demo.gif"

# ── GIF-Parameter ─────────────────────────────────────────────────────────────
# Verhältnis 16:10 passt zu den 1536×884-Screenshots (≈1.737)
GIF_BREITE  = 960
GIF_HOEHE   = 552          # 960 / 1536 * 884 ≈ 552 → exaktes Verhältnis
FRAME_PAUSE = 25           # 1/100 Sekunden pro Frame (25 = 0.25s)
TITEL_PAUSE = 80           # Pause bei Titel-Frames (0.8s)
SECTION_PAUSE = 120        # Pause bei neuer Sektion (1.2s)

# ── Farben (passend zum dunklen Theme) ────────────────────────────────────────
FARBE_HINTERGRUND = (28, 28, 35)
FARBE_TITEL_BG    = (20, 20, 28, 200)
FARBE_BLAU        = (82, 148, 226)
FARBE_WEISS       = (220, 220, 230)
FARBE_GRAU        = (140, 140, 155)
FARBE_GRUEN       = (80, 200, 120)
FARBE_ORANGE      = (220, 140, 50)

# ── Tab-Positionen (relativ zur App-Breite, aus Screenshots ermittelt) ────────
# Die Tab-Bar liegt bei y ≈ 53px (relativ zum App-Fenster oben)
# X-Positionen der Tab-Mittelpunkte bei 1536px Fensterbreite (Dock-Modus rechts):
TABS = {
    "einst":   {"label": "⚙ Einst.",      "x_rel": 0.058},
    "ki":      {"label": "🤖 KI",          "x_rel": 0.136},
    "akt":     {"label": "📋 Akt.",        "x_rel": 0.225},
    "snip":    {"label": "📌 Snip",        "x_rel": 0.303},
    "api":     {"label": "💡 API",         "x_rel": 0.390},
    "dat":     {"label": "📁 Dat.",        "x_rel": 0.472},
    "tools":   {"label": "🔧 Tools",       "x_rel": 0.554},
    "bib":     {"label": "📚 Bib.",        "x_rel": 0.634},
    "werkz":   {"label": "🔨 Werkz.",      "x_rel": 0.720},
    "fehler":  {"label": "⚠ Fehler",       "x_rel": 0.800},
    "hilfe":   {"label": "📘 Hilfe+Zugang","x_rel": 0.905},
}

# ── Schrift ────────────────────────────────────────────────────────────────────
def _font(groesse: int) -> ImageFont.FreeTypeFont:
    for pfad in [
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        if os.path.exists(pfad):
            try:
                return ImageFont.truetype(pfad, groesse)
            except Exception:
                pass
    return ImageFont.load_default()


def _font_bold(groesse: int) -> ImageFont.FreeTypeFont:
    for pfad in [
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(pfad):
            try:
                return ImageFont.truetype(pfad, groesse)
            except Exception:
                pass
    return ImageFont.load_default()


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def _resize_passend(img: Image.Image, ziel_w: int, ziel_h: int) -> Image.Image:
    """
    Skaliert das Bild proportional so, dass es VOLLSTÄNDIG in den Zielrahmen passt.
    Kein Croppen — eventuell entstehende Ränder werden mit Hintergrundfarbe gefüllt.
    """
    orig_w, orig_h = img.size
    skalierung = min(ziel_w / orig_w, ziel_h / orig_h)
    neue_w = int(orig_w * skalierung)
    neue_h = int(orig_h * skalierung)
    skaliert = img.resize((neue_w, neue_h), Image.LANCZOS)

    rahmen = Image.new("RGB", (ziel_w, ziel_h), FARBE_HINTERGRUND)
    offset_x = (ziel_w - neue_w) // 2
    offset_y = (ziel_h - neue_h) // 2
    rahmen.paste(skaliert, (offset_x, offset_y))
    return rahmen


# Rückwärtskompatibilität (für Live-Modus)
def _resize_crop(img: Image.Image, ziel_w: int, ziel_h: int) -> Image.Image:
    return _resize_passend(img, ziel_w, ziel_h)


def _beschriftung_hinzufuegen(
    img: Image.Image,
    titel: str,
    untertitel: str = "",
    position: str = "unten",
) -> Image.Image:
    """Fügt einen halbtransparenten Beschriftungsbalken hinzu."""
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    balken_h = 64 if untertitel else 44
    if position == "unten":
        y0 = img.height - balken_h
        y1 = img.height
    else:
        y0, y1 = 0, balken_h

    draw.rectangle([0, y0, img.width, y1], fill=(18, 18, 26, 210))

    # Blauer Akzentbalken links
    draw.rectangle([0, y0, 4, y1], fill=(*FARBE_BLAU, 255))

    # Titeltext
    f_titel = _font_bold(18)
    draw.text((16, y0 + 8), titel, font=f_titel, fill=(*FARBE_WEISS, 255))

    if untertitel:
        f_sub = _font(13)
        draw.text((16, y0 + 32), untertitel, font=f_sub, fill=(*FARBE_GRAU, 255))

    kombiniert = Image.alpha_composite(img, overlay)
    return kombiniert.convert("RGB")


def _titel_frame(text: str, untertitel: str = "") -> Image.Image:
    """Erstellt einen Übergangs-Frame mit zentriertem Titeltext."""
    img = Image.new("RGB", (GIF_BREITE, GIF_HOEHE), FARBE_HINTERGRUND)
    draw = ImageDraw.Draw(img)

    # Dekorationslinien
    draw.rectangle([0, 0, GIF_BREITE, 3], fill=FARBE_BLAU)
    draw.rectangle([0, GIF_HOEHE - 3, GIF_BREITE, GIF_HOEHE], fill=FARBE_BLAU)
    draw.rectangle([0, 0, 3, GIF_HOEHE], fill=FARBE_BLAU)
    draw.rectangle([GIF_BREITE - 3, 0, GIF_BREITE, GIF_HOEHE], fill=FARBE_BLAU)

    # Logo / App-Name oben
    f_app = _font(14)
    draw.text((GIF_BREITE // 2, 40), "FreeCAD MultiAI Panel",
              font=f_app, fill=FARBE_GRAU, anchor="mm")

    # Haupttitel
    f_titel = _font_bold(32)
    draw.text((GIF_BREITE // 2, GIF_HOEHE // 2 - (20 if untertitel else 0)),
              text, font=f_titel, fill=FARBE_WEISS, anchor="mm")

    # Untertitel
    if untertitel:
        f_sub = _font(18)
        draw.text((GIF_BREITE // 2, GIF_HOEHE // 2 + 30),
                  untertitel, font=f_sub, fill=FARBE_BLAU, anchor="mm")

    return img


def _prompt_frame(prompt_text: str, code_text: str = "") -> Image.Image:
    """Zeigt Prompt + generierten Code nebeneinander."""
    img = Image.new("RGB", (GIF_BREITE, GIF_HOEHE), FARBE_HINTERGRUND)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, GIF_BREITE, 3], fill=FARBE_BLAU)

    haelfte = GIF_BREITE // 2 - 10

    # Linke Seite: Prompt
    draw.rectangle([10, 10, haelfte, GIF_HOEHE - 10], fill=(35, 35, 45))
    draw.rectangle([10, 10, haelfte, 40], fill=(45, 80, 130))
    draw.text((20, 20), "📝  Anfrage an KI", font=_font_bold(14), fill=FARBE_WEISS)

    f_prompt = _font(12)
    zeilen = _umbruch(prompt_text, 55)
    for i, zeile in enumerate(zeilen[:18]):
        draw.text((18, 50 + i * 22), zeile, font=f_prompt, fill=FARBE_WEISS)

    # Rechte Seite: Code
    if code_text:
        x0 = haelfte + 20
        draw.rectangle([x0, 10, GIF_BREITE - 10, GIF_HOEHE - 10], fill=(28, 35, 28))
        draw.rectangle([x0, 10, GIF_BREITE - 10, 40], fill=(40, 80, 50))
        draw.text((x0 + 10, 20), "✅  Generierter Python-Code",
                  font=_font_bold(14), fill=FARBE_GRUEN)

        f_code = _font(11)
        code_zeilen = code_text.split("\n")
        for i, zeile in enumerate(code_zeilen[:30]):
            draw.text((x0 + 10, 50 + i * 17), zeile, font=f_code, fill=(180, 230, 180))

    return img


def _umbruch(text: str, max_zeichen: int) -> list:
    """Einfacher Zeilenumbruch."""
    woerter = text.split()
    zeilen, zeile = [], ""
    for w in woerter:
        if len(zeile) + len(w) + 1 <= max_zeichen:
            zeile = (zeile + " " + w).strip()
        else:
            if zeile:
                zeilen.append(zeile)
            zeile = w
    if zeile:
        zeilen.append(zeile)
    return zeilen


# ── Frames aus Screenshots ─────────────────────────────────────────────────────

def frames_aus_screenshots(screenshots_ordner: Path) -> list:
    """
    Wählt die besten Screenshots aus und erstellt annotierte Frames.
    Gibt Liste von (Image, delay_cs) Tupeln zurück (delay in 1/100 Sekunden).
    """
    ordner = Path(screenshots_ordner)
    dateien = sorted(ordner.glob("*.png"))
    if not dateien:
        print(f"❌ Keine PNG-Dateien in {ordner}")
        sys.exit(1)

    print(f"📂 {len(dateien)} Screenshots gefunden in {ordner}")

    # Screenshots laden und nach Zeitstempel sortieren
    imgs = []
    for d in dateien:
        try:
            img = Image.open(d)
            imgs.append((d.name, img))
            print(f"  ✓ {d.name}: {img.size}")
        except Exception as e:
            print(f"  ✗ {d.name}: {e}")

    frames = []

    def _add(img, delay, titel="", untertitel="", modus="dock"):
        """Fügt einen Frame zur Liste hinzu — proportional skaliert, kein Croppen."""
        resized = _resize_passend(img, GIF_BREITE, GIF_HOEHE)
        if titel:
            resized = _beschriftung_hinzufuegen(resized, titel, untertitel)
        frames.append((resized, delay))

    def _add_titel(text, untertitel="", wiederholungen=4):
        f = _titel_frame(text, untertitel)
        for _ in range(wiederholungen):
            frames.append((f, TITEL_PAUSE))

    # ── 1. Begrüßung ──────────────────────────────────────────────────────────
    _add_titel("Willkommen!", "FreeCAD KI Multi-Source Assistent", wiederholungen=5)

    # ── 2. App-Übersicht: KI-Tab mit Code-Editor ──────────────────────────────
    _add_titel("KI-gestützter Makro-Editor")

    # Suche nach Screenshots die den KI-Tab zeigen (erste paar)
    ki_screenshots = [img for name, img in imgs if "23-12" in name or "23-13-07" in name]
    for img in ki_screenshots[:2]:
        _add(img, SECTION_PAUSE, "KI-Tab", "Anbieter wählen · Modell · Prompt eingeben")

    # ── 3. Code-Generierung ───────────────────────────────────────────────────
    _add_titel("Code-Generierung", "KI erstellt FreeCAD-Python-Skripte")

    prompt = (
        "Erstelle ein Python-Skript für FreeCAD:\n"
        "Erzeuge einen Würfel (Part.makeBox) mit 40×40×40 mm.\n"
        "Platziere eine zentrale Bohrung (Zylinder) mit\n"
        "10 mm Durchmesser, die den Würfel komplett auf\n"
        "der Z-Achse durchdringt. Zentriere den Zylinder\n"
        "auf X=20 und Y=20. Führe eine Boole'sche\n"
        "Subtraktion durch."
    )
    code = (
        "import FreeCAD as App\n"
        "\n"
        "doc = App.ActiveDocument\n"
        "if doc is None:\n"
        "    doc = App.newDocument(\"WuerfelMitBohrung\")\n"
        "\n"
        "LAENGE = 40.0\n"
        "BREITE = 40.0\n"
        "HOEHE  = 40.0\n"
        "RADIUS =  5.0\n"
        "\n"
        "box = doc.addObject(\"Part::Box\", \"Wuerfel\")\n"
        "box.Length = LAENGE\n"
        "box.Width  = BREITE\n"
        "box.Height = HOEHE\n"
        "\n"
        "zyl = doc.addObject(\"Part::Cylinder\", \"Bohrung\")\n"
        "zyl.Radius = RADIUS\n"
        "zyl.Height = HOEHE\n"
        "zyl.Placement.Base = App.Vector(\n"
        "    LAENGE/2, BREITE/2, 0)\n"
        "\n"
        "cut = doc.addObject(\"Part::Cut\", \"Ergebnis\")\n"
        "cut.Base = box\n"
        "cut.Tool = zyl\n"
        "doc.recompute()\n"
        "print(\"✅ Würfel mit Bohrung erstellt.\")"
    )
    pf = _prompt_frame(prompt, code)
    for _ in range(6):
        frames.append((pf, SECTION_PAUSE))

    # ── 4. Akt.-Tab (Aktionen mit Tooltips) ───────────────────────────────────
    _add_titel("Aktionen-Panel", "Schnellzugriff auf alle Editor-Funktionen")
    akt_imgs = [img for name, img in imgs if "23-13-18" in name]
    for img in akt_imgs:
        _add(img, SECTION_PAUSE, "Aktionen-Tab",
             "KI-Analyse · Vorschau · Speichern · Lesezeichen")

    # ── 5. Snip-Tab ───────────────────────────────────────────────────────────
    snip_imgs = [img for name, img in imgs if "23-13-25" in name]
    for img in snip_imgs:
        _add(img, SECTION_PAUSE, "Snippets",
             "Fertige Code-Bausteine für FreeCAD")

    # ── 6. API-Referenz ───────────────────────────────────────────────────────
    api_imgs = [img for name, img in imgs if "23-13-32" in name]
    for img in api_imgs:
        _add(img, SECTION_PAUSE, "API-Referenz",
             "FreeCAD API-Kurzreferenz direkt im Editor")

    # ── 7. Werkzeuge ──────────────────────────────────────────────────────────
    _add_titel("Werkzeuge", "Navigation · Bearbeitung · Code-Prüfung")
    tools_imgs = [img for name, img in imgs
                  if "23-13-46" in name or "23-14-08" in name or "23-14-24" in name]
    for img in tools_imgs[:3]:
        _add(img, SECTION_PAUSE, "Werkzeuge",
             "Zeile springen · Code-Struktur · Text-Transformation")

    # ── 8. Fehler-Übersetzer ──────────────────────────────────────────────────
    _add_titel("Fehler-Übersetzer", "Englische Python-Fehler → Deutsches Klartext")
    fehler_imgs = [img for name, img in imgs if "23-14-38" in name]
    for img in fehler_imgs:
        _add(img, SECTION_PAUSE,
             "Fehler-Übersetzer",
             "Fehlermeldung eingeben → sofortige deutsche Erklärung",
             modus="voll")

    # Sandbox
    sandbox_imgs = [img for name, img in imgs if "23-14-46" in name]
    for img in sandbox_imgs:
        _add(img, SECTION_PAUSE,
             "Sandbox",
             "Code direkt testen · KI korrigiert bei Fehler (max. 3×)",
             modus="voll")

    # ── 9. Hilfe + Assistent ──────────────────────────────────────────────────
    _add_titel("Hilfe & Assistent", "FreeCAD-Helfer · Barrierefreiheit · Handbuch")
    hilfe_imgs = [img for name, img in imgs
                  if "23-15-05" in name or "23-15-11" in name or "23-15-16" in name]
    for img in hilfe_imgs[:3]:
        _add(img, SECTION_PAUSE,
             "Hilfe + Zugang",
             "KI-Assistent · Barrierefreiheit · Handbuch & F1–F3 Shortcuts")

    # ── 10. Abschluss ─────────────────────────────────────────────────────────
    _add_titel("FreeCAD MultiAI Panel", "19 KI-Anbieter · Deutsch · OpenSource",
               wiederholungen=6)

    print(f"✅ {len(frames)} Frames erstellt")
    return frames


# ── Live-Aufnahme (xdotool + scrot) ──────────────────────────────────────────

def _check_live_tools():
    fehlt = []
    for tool in ["xdotool", "scrot"]:
        if not shutil.which(tool):
            fehlt.append(tool)
    if fehlt:
        print(f"❌ Fehlende Tools: {', '.join(fehlt)}")
        print(f"   Installieren: sudo apt install {' '.join(fehlt)}")
        sys.exit(1)


def _cmd(*args):
    return subprocess.run(list(args), capture_output=True, text=True)


def _fenster_finden():
    for titel in ["Makro-Editor", "FreeCAD MultiAI", "FreeCAD"]:
        r = _cmd("xdotool", "search", "--name", titel)
        ids = [x for x in r.stdout.strip().split("\n") if x]
        if ids:
            print(f"  Fenster gefunden: '{titel}' → ID {ids[-1]}")
            return ids[-1]
    return None


def _geometrie(wid):
    r = _cmd("xdotool", "getwindowgeometry", "--shell", wid)
    info = {}
    for line in r.stdout.strip().split("\n"):
        if "=" in line:
            k, _, v = line.partition("=")
            try:
                info[k.strip()] = int(v.strip())
            except ValueError:
                pass
    return (info.get("X", 0), info.get("Y", 0),
            info.get("WIDTH", 1536), info.get("HEIGHT", 884))


def _aktiviere(wid):
    subprocess.run(["xdotool", "windowactivate", "--sync", wid])
    time.sleep(0.4)


def _klick(wid, rel_x: float, rel_y: float):
    """Klick auf relative Position im Fenster."""
    wx, wy, ww, wh = _geometrie(wid)
    ax = wx + int(ww * rel_x)
    ay = wy + int(wh * rel_y)
    subprocess.run(["xdotool", "mousemove", str(ax), str(ay)])
    time.sleep(0.15)
    subprocess.run(["xdotool", "click", "1"])
    time.sleep(0.1)


def _screenshot_live(pfad: Path, wid: str):
    """Macht Screenshot des gesamten Bildschirms und gibt ihn zurück."""
    subprocess.run(["scrot", str(pfad)])
    img = Image.open(pfad)
    # Nur den Fensterbereich croppen
    wx, wy, ww, wh = _geometrie(wid)
    wx = max(0, wx)
    wy = max(0, wy)
    return img.crop((wx, wy, wx + ww, wy + wh))


def frames_live_aufnahme() -> list:
    """Nimmt den Bildschirm live auf und erstellt Frames."""
    _check_live_tools()

    print("🔍 Suche FreeCAD-Fenster …")
    wid = _fenster_finden()
    if not wid:
        print("❌ FreeCAD-Fenster nicht gefunden. Bitte FreeCAD starten.")
        sys.exit(1)

    _aktiviere(wid)
    frames = []
    tmpdir = Path(tempfile.mkdtemp())

    def _snap(beschriftung="", untertitel=""):
        pfad = tmpdir / f"frame_{len(frames):04d}.png"
        img = _screenshot_live(pfad, wid)
        resized = _resize_crop(img, GIF_BREITE, GIF_HOEHE)
        if beschriftung:
            resized = _beschriftung_hinzufuegen(resized, beschriftung, untertitel)
        return resized

    def _multi_snap(n, beschriftung="", untertitel="", pause=SECTION_PAUSE):
        for _ in range(n):
            frames.append((_snap(beschriftung, untertitel), pause))
            time.sleep(0.08)

    def _tab_klick(tab_name):
        tab = TABS.get(tab_name, {})
        x_rel = tab.get("x_rel", 0.5)
        _klick(wid, x_rel, 0.06)   # Tab-Bar liegt bei ~6% der Fensterhöhe
        time.sleep(0.8)

    print("📸 Starte Aufnahme …")

    # Begrüßung
    for _ in range(5):
        frames.append((_titel_frame("Willkommen!", "FreeCAD KI Multi-Source Assistent"),
                       TITEL_PAUSE))

    # KI-Tab
    print("  → KI-Tab")
    _tab_klick("ki")
    _multi_snap(4, "KI-Tab", "Anbieter · Modell · Prompt")

    # Akt.-Tab
    print("  → Akt.-Tab")
    _tab_klick("akt")
    _multi_snap(4, "Aktionen", "KI-Analyse · Vorschau · Speichern")

    # Snip
    print("  → Snip-Tab")
    _tab_klick("snip")
    _multi_snap(3, "Snippets", "Fertige Code-Bausteine")

    # API
    print("  → API-Tab")
    _tab_klick("api")
    _multi_snap(3, "API-Referenz", "FreeCAD API direkt im Editor")

    # Tools
    print("  → Tools-Tab")
    _tab_klick("tools")
    _multi_snap(4, "Werkzeuge", "Navigation · Bearbeitung · Prüfung")

    # Fehler
    print("  → Fehler-Tab")
    _tab_klick("fehler")
    time.sleep(1.0)
    _multi_snap(5, "Fehler-Übersetzer", "Englische Fehler → Deutsche Erklärung")

    # Hilfe
    print("  → Hilfe-Tab")
    _tab_klick("hilfe")
    _multi_snap(4, "Hilfe + Assistent", "FreeCAD-Helfer · Barrierefreiheit")

    # Abschluss
    for _ in range(6):
        frames.append((_titel_frame("FreeCAD MultiAI Panel",
                                    "19 KI-Anbieter · Deutsch · OpenSource"),
                       TITEL_PAUSE))

    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"✅ {len(frames)} Live-Frames aufgenommen")
    return frames


# ── GIF exportieren ───────────────────────────────────────────────────────────

def gif_exportieren(frames: list, ausgabe: Path):
    """Exportiert die Frames als animiertes GIF."""
    ausgabe.parent.mkdir(parents=True, exist_ok=True)

    pil_frames = []
    delays = []
    for img, delay in frames:
        # RGB → Palette (für kleinere GIF-Dateien)
        pil_frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=128))
        delays.append(delay * 10)  # PIL erwartet Millisekunden

    print(f"💾 Speichere GIF: {ausgabe}")
    pil_frames[0].save(
        ausgabe,
        save_all=True,
        append_images=pil_frames[1:],
        duration=delays,
        loop=0,
        optimize=True,
    )
    groesse_mb = ausgabe.stat().st_size / 1024 / 1024
    print(f"✅ GIF gespeichert: {ausgabe}")
    print(f"   Größe: {groesse_mb:.1f} MB  |  Frames: {len(frames)}  |  {GIF_BREITE}×{GIF_HOEHE}px")


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Erstellt ki_makro_editor_demo.gif für das Begrüßungsfenster")
    gruppe = parser.add_mutually_exclusive_group(required=True)
    gruppe.add_argument("--screenshots", metavar="ORDNER",
                        help="Screenshots-Ordner für Demo-Modus")
    gruppe.add_argument("--live", action="store_true",
                        help="Live-Aufnahme via xdotool+scrot (FreeCAD muss laufen)")
    parser.add_argument("--ausgabe", default=str(AUSGABE),
                        help=f"Ausgabepfad (Standard: {AUSGABE})")
    args = parser.parse_args()

    ausgabe = Path(args.ausgabe)

    if args.screenshots:
        print("🎬 Modus: Demo aus Screenshots")
        frames = frames_aus_screenshots(Path(args.screenshots))
    else:
        print("🎬 Modus: Live-Aufnahme")
        frames = frames_live_aufnahme()

    gif_exportieren(frames, ausgabe)


if __name__ == "__main__":
    main()
