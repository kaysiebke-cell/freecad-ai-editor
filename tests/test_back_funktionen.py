# -*- coding: utf-8 -*-
"""
test_back_funktionen.py
═══════════════════════
Testdatei für alle "Back"-Funktionen des freecad-ai-editor.

✅  ECHTE TESTS  → laufen durch, prüfen Backup/Navigation/Reload-Logik,
                   NL-Generator-Konstanten, Layout-Persistenz, Panel-Logik
🐛  FEHLER-ZONEN → absichtlich kaputt, um Syntax-Checker & Fehler-Tab
                   des Editors zu testen. Jede Zone ist klar markiert.

Ausführen (ohne FreeCAD/Qt):
    python test_back_funktionen.py
"""

import os
import sys
import glob
import json
import shutil
import base64
import tempfile
import unittest
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# 🐛  FEHLER-ZONE 1: SyntaxError  (für Syntax-Checker-Test im Editor)
# Kommentar entfernen um den Fehler zu aktivieren:
# ══════════════════════════════════════════════════════════════════════════════
# def kaputte_funktion(
#     x, y          # ← fehlendes ')' und ':'
#     return x + y  # SyntaxError: expected ':'


# ══════════════════════════════════════════════════════════════════════════════
# 🐛  FEHLER-ZONE 2: NameError (Laufzeitfehler)
# ══════════════════════════════════════════════════════════════════════════════
def name_fehler_demo():
    """Provoziert NameError: nicht definierte Variable."""
    # Kommentar entfernen um Fehler zu aktivieren:
    # ergebnis = nicht_definierte_variable + 1
    # return ergebnis


# ══════════════════════════════════════════════════════════════════════════════
# 🐛  FEHLER-ZONE 3: TypeError
# ══════════════════════════════════════════════════════════════════════════════
def type_fehler_demo():
    """Provoziert TypeError: int + str."""
    # Kommentar entfernen:
    # return 42 + "hallo"


# ══════════════════════════════════════════════════════════════════════════════
# 🐛  FEHLER-ZONE 4: IndentationError
# ══════════════════════════════════════════════════════════════════════════════
# def einrueck_fehler():
# return "falsch eingerückt"   # ← kein Einzug nach def


# ══════════════════════════════════════════════════════════════════════════════
# 🐛  FEHLER-ZONE 5: AttributeError
# ══════════════════════════════════════════════════════════════════════════════
def attribut_fehler_demo():
    """Provoziert AttributeError auf None."""
    # Kommentar entfernen:
    # wert = None
    # return wert.upper()


# ══════════════════════════════════════════════════════════════════════════════
# 🐛  FEHLER-ZONE 6: ZeroDivisionError
# ══════════════════════════════════════════════════════════════════════════════
def division_demo():
    # Kommentar entfernen:
    # return 1 / 0
    pass


# ══════════════════════════════════════════════════════════════════════════════
# ✅  HILFSFUNKTIONEN – nachgebaute Back-Logik (Qt-frei)
# ══════════════════════════════════════════════════════════════════════════════

def backup_erstellen(pfad: str) -> str:
    """Nachbau von MakroEditor._backup_erstellen(): .bak-Datei, max. 3 Backups."""
    bak_pfad = f"{pfad}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(pfad, bak_pfad)
    alle = sorted(glob.glob(f"{pfad}.*.bak"))
    for alt in alle[:-3]:
        os.remove(alt)
    return bak_pfad


def backup_wiederherstellen(pfad: str) -> str:
    """Nachbau von MakroEditor._backup_wiederherstellen(): neuestes Backup."""
    alle = sorted(glob.glob(f"{pfad}.*.bak"))
    if not alle:
        raise FileNotFoundError("Kein Backup gefunden")
    with open(alle[-1], "r", encoding="utf-8") as f:
        return f.read()


def neu_laden(pfad: str) -> str:
    """Nachbau von MakroEditor.neu_laden() – liest Datei von Disk."""
    with open(pfad, "r", encoding="utf-8") as f:
        return f.read()


def db_hoch(aktueller_pfad: str) -> str:
    """Nachbau von Browser._db_hoch() – ein Verzeichnis nach oben."""
    normiert = aktueller_pfad.rstrip(os.sep) or os.sep
    eltern   = os.path.dirname(normiert)
    return eltern if eltern else os.sep


def lz_nach(alle_lesezeichen: list, aktuelle_zeile: int) -> int:
    """Nachbau von WerkzeugLeiste._lz_nach() – nächstes Lesezeichen."""
    if not alle_lesezeichen:
        raise ValueError("Keine Lesezeichen vorhanden")
    ziel = next((z for z in alle_lesezeichen if z > aktuelle_zeile),
                alle_lesezeichen[0])
    return ziel


def lz_vor(alle_lesezeichen: list, aktuelle_zeile: int) -> int:
    """Nachbau von WerkzeugLeiste._lz_vor() – vorheriges Lesezeichen."""
    if not alle_lesezeichen:
        raise ValueError("Keine Lesezeichen vorhanden")
    ziel = next((z for z in reversed(alle_lesezeichen) if z < aktuelle_zeile),
                alle_lesezeichen[-1])
    return ziel


# ══════════════════════════════════════════════════════════════════════════════
# ✅  HILFSFUNKTIONEN – Layout-Persistenz (Qt-frei nachgebaut)
# ══════════════════════════════════════════════════════════════════════════════

def layout_speichern(datei: str, zustand_bytes: bytes) -> None:
    """Nachbau der closeEvent-Logik: Qt-Bytes → Base64 → JSON."""
    state_str = base64.b64encode(zustand_bytes).decode("ascii")
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(state_str, f)


def layout_laden(datei: str) -> bytes:
    """Nachbau der _lade_layout-Logik: JSON → Base64 → Bytes."""
    with open(datei, "r", encoding="utf-8") as f:
        state_str = json.load(f)
    return base64.b64decode(state_str.encode("ascii"))


# ══════════════════════════════════════════════════════════════════════════════
# ✅  HILFSFUNKTIONEN – Panel-Platzierungslogik (Qt-frei nachgebaut)
# ══════════════════════════════════════════════════════════════════════════════

# Symbole ohne Qt
LINKS  = "left"
RECHTS = "right"
UNTEN  = "bottom"
GEGENUEBER = {LINKS: RECHTS, RECHTS: LINKS, UNTEN: UNTEN}


def panel_zielbereich(standard_bereich: str, belegte_bereiche: set) -> str:
    """
    Nachbau der _zeige_panel-Logik:
    Gibt zurück welchen Bereich ein Panel bekommen soll.
    - UNTEN bleibt immer UNTEN
    - Wenn standard_bereich frei → standard_bereich
    - Wenn standard_bereich belegt → Gegenseite
    - Wenn beide Seiten belegt → Gegenseite (Tabify)
    """
    if standard_bereich == UNTEN:
        return UNTEN
    if standard_bereich not in belegte_bereiche:
        return standard_bereich
    gegenseite = GEGENUEBER[standard_bereich]
    return gegenseite


# ══════════════════════════════════════════════════════════════════════════════
# ✅  TEST-KLASSEN
# ══════════════════════════════════════════════════════════════════════════════

class TestBackupErstellen(unittest.TestCase):
    """Tests für _backup_erstellen()"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.test_datei = os.path.join(self.tmp_dir, "makro_test.py")
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write("# Original-Inhalt\nprint('hallo')\n")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_backup_datei_wird_erstellt(self):
        bak = backup_erstellen(self.test_datei)
        self.assertTrue(os.path.exists(bak))

    def test_backup_hat_bak_endung(self):
        bak = backup_erstellen(self.test_datei)
        self.assertTrue(bak.endswith(".bak"))

    def test_backup_inhalt_identisch(self):
        bak = backup_erstellen(self.test_datei)
        with open(bak, "r", encoding="utf-8") as f:
            inhalt = f.read()
        self.assertEqual(inhalt, "# Original-Inhalt\nprint('hallo')\n")

    def test_maximal_drei_backups(self):
        import time
        for i in range(5):
            time.sleep(0.01)
            backup_erstellen(self.test_datei)
        alle = glob.glob(f"{self.test_datei}.*.bak")
        self.assertLessEqual(len(alle), 3)

    def test_backup_bei_nicht_existenter_datei_schlaegt_fehl(self):
        with self.assertRaises(FileNotFoundError):
            backup_erstellen("/tmp/__existiert_nicht_xyz__.py")


class TestBackupWiederherstellen(unittest.TestCase):
    """Tests für _backup_wiederherstellen()"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.test_datei = os.path.join(self.tmp_dir, "restore_test.py")
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write("# Version 1\n")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_wiederherstellen_laedt_backup_inhalt(self):
        backup_erstellen(self.test_datei)
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write("# Version 2 – geändert!\n")
        wiederhergestellt = backup_wiederherstellen(self.test_datei)
        self.assertEqual(wiederhergestellt, "# Version 1\n")

    def test_wiederherstellen_ohne_backup_schlaegt_fehl(self):
        with self.assertRaises(FileNotFoundError):
            backup_wiederherstellen(self.test_datei)

    def test_neuestes_backup_wird_genommen(self):
        import time
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write("# Erstes Backup\n")
        backup_erstellen(self.test_datei)
        time.sleep(0.02)
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write("# Zweites Backup – das neuere\n")
        backup_erstellen(self.test_datei)
        wiederhergestellt = backup_wiederherstellen(self.test_datei)
        self.assertIn("Zweites Backup", wiederhergestellt)


class TestNeuLaden(unittest.TestCase):
    """Tests für neu_laden()"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.test_datei = os.path.join(self.tmp_dir, "reload_test.py")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_inhalt_korrekt_geladen(self):
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write("x = 42\n")
        self.assertEqual(neu_laden(self.test_datei), "x = 42\n")

    def test_datei_existiert_nicht(self):
        with self.assertRaises(FileNotFoundError):
            neu_laden("/tmp/__kein_makro__.py")

    def test_utf8_umlaute(self):
        sonderzeichen = "# Ärger über Öl und Übergänge\n"
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write(sonderzeichen)
        self.assertEqual(neu_laden(self.test_datei), sonderzeichen)

    def test_leere_datei(self):
        with open(self.test_datei, "w", encoding="utf-8") as f:
            f.write("")
        self.assertEqual(neu_laden(self.test_datei), "")


class TestDbHoch(unittest.TestCase):
    """Tests für Browser._db_hoch()"""

    def test_normaler_pfad_geht_hoch(self):
        self.assertEqual(db_hoch("/home/user/projekte/makros"), "/home/user/projekte")

    def test_pfad_mit_trailing_slash(self):
        self.assertEqual(db_hoch("/home/user/projekte/makros/"), "/home/user/projekte")

    def test_wurzel_bleibt_bei_wurzel(self):
        self.assertEqual(db_hoch("/"), "/")

    def test_tiefe_pfade(self):
        self.assertEqual(db_hoch("/a/b/c/d/e/f"), "/a/b/c/d/e")


class TestLesezeichenNavigation(unittest.TestCase):
    """Tests für _lz_nach() / _lz_vor()"""

    def setUp(self):
        self.lesezeichen = [5, 12, 25, 40, 67]

    def test_lz_nach_springt_zum_naechsten(self):
        self.assertEqual(lz_nach(self.lesezeichen, 12), 25)

    def test_lz_nach_am_ende_springt_zum_anfang(self):
        self.assertEqual(lz_nach(self.lesezeichen, 67), 5)

    def test_lz_nach_vor_erstem(self):
        self.assertEqual(lz_nach(self.lesezeichen, 0), 5)

    def test_lz_vor_springt_zurueck(self):
        self.assertEqual(lz_vor(self.lesezeichen, 25), 12)

    def test_lz_vor_am_anfang_springt_zum_ende(self):
        self.assertEqual(lz_vor(self.lesezeichen, 5), 67)

    def test_lz_nach_bei_leerer_liste_wirft_fehler(self):
        with self.assertRaises(ValueError):
            lz_nach([], 10)

    def test_lz_vor_bei_leerer_liste_wirft_fehler(self):
        with self.assertRaises(ValueError):
            lz_vor([], 10)

    def test_einzelnes_lesezeichen(self):
        self.assertEqual(lz_nach([10], 5),  10)
        self.assertEqual(lz_nach([10], 15), 10)
        self.assertEqual(lz_vor([10], 15),  10)
        self.assertEqual(lz_vor([10], 5),   10)


class TestLayoutPersistenz(unittest.TestCase):
    """Tests für saveState/restoreState JSON-Roundtrip."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.layout_datei = os.path.join(self.tmp_dir, ".ki_makro_editor_layout.json")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_speichern_und_laden_roundtrip(self):
        """Bytes überleben den JSON-Roundtrip identisch."""
        original = b"QMAINWINDOW_STATE_DATA_12345"
        layout_speichern(self.layout_datei, original)
        wiederhergestellt = layout_laden(self.layout_datei)
        self.assertEqual(wiederhergestellt, original)

    def test_datei_wird_als_json_gespeichert(self):
        """Layout-Datei muss gültiges JSON enthalten."""
        layout_speichern(self.layout_datei, b"testdaten")
        with open(self.layout_datei, "r", encoding="utf-8") as f:
            inhalt = json.load(f)
        self.assertIsInstance(inhalt, str)

    def test_base64_string_ist_valide(self):
        """Der gespeicherte String muss gültiges Base64 sein."""
        layout_speichern(self.layout_datei, b"freecad-ai-editor-state")
        with open(self.layout_datei, "r", encoding="utf-8") as f:
            state_str = json.load(f)
        decoded = base64.b64decode(state_str.encode("ascii"))
        self.assertEqual(decoded, b"freecad-ai-editor-state")

    def test_fehlende_datei_wirft_keinen_unkontrollierten_fehler(self):
        """Nicht-existente Layout-Datei muss FileNotFoundError werfen (kein Absturz)."""
        with self.assertRaises(FileNotFoundError):
            layout_laden("/tmp/__kein_layout_xyz__.json")

    def test_leere_bytes_ueberleben_roundtrip(self):
        layout_speichern(self.layout_datei, b"")
        self.assertEqual(layout_laden(self.layout_datei), b"")


class TestPanelPlatzierung(unittest.TestCase):
    """Tests für die intelligente Panel-Platzierungslogik (_zeige_panel)."""

    def test_fehler_panel_immer_unten(self):
        """Fehler-Panel geht immer nach UNTEN, egal was belegt ist."""
        self.assertEqual(panel_zielbereich(UNTEN, set()), UNTEN)
        self.assertEqual(panel_zielbereich(UNTEN, {LINKS}), UNTEN)
        self.assertEqual(panel_zielbereich(UNTEN, {LINKS, RECHTS, UNTEN}), UNTEN)

    def test_freier_standardbereich_wird_genommen(self):
        """Wenn der Standardbereich frei ist, wird er direkt verwendet."""
        self.assertEqual(panel_zielbereich(LINKS, set()), LINKS)
        self.assertEqual(panel_zielbereich(RECHTS, set()), RECHTS)

    def test_belegter_standardbereich_wechselt_auf_gegenseite(self):
        """Wenn LINKS belegt ist → nach RECHTS ausweichen."""
        self.assertEqual(panel_zielbereich(LINKS, {LINKS}), RECHTS)

    def test_belegter_rechts_wechselt_auf_links(self):
        """Wenn RECHTS belegt ist → nach LINKS ausweichen."""
        self.assertEqual(panel_zielbereich(RECHTS, {RECHTS}), LINKS)

    def test_beide_seiten_belegt_geht_zur_gegenseite(self):
        """Wenn beide Seiten belegt sind → Gegenseite (Tabify)."""
        self.assertEqual(panel_zielbereich(LINKS, {LINKS, RECHTS}), RECHTS)
        self.assertEqual(panel_zielbereich(RECHTS, {LINKS, RECHTS}), LINKS)

    def test_standardbereich_frei_ignoriert_anderen(self):
        """LINKS frei, RECHTS belegt → LINKS wird trotzdem genommen."""
        self.assertEqual(panel_zielbereich(LINKS, {RECHTS}), LINKS)


class TestPresets(unittest.TestCase):
    """Tests für KI_PRESETS, KI_PRESET_KATEGORIEN und FC_KI_PRESETS."""

    @classmethod
    def setUpClass(cls):
        for sub in ("data", "core"):
            p = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", sub))
            if p not in sys.path:
                sys.path.insert(0, p)
        # FreeCAD mocken – params.py benötigt es beim Import
        import types
        _fc = types.ModuleType("FreeCAD")
        _fc.getUserAppDataDir = lambda: "/tmp/"
        sys.modules.setdefault("FreeCAD",    _fc)
        sys.modules.setdefault("FreeCADGui", types.ModuleType("FreeCADGui"))
        from params import KI_PRESETS, KI_PRESET_KATEGORIEN
        from freecad_data import FC_KI_PRESETS
        cls.presets     = KI_PRESETS
        cls.kategorien  = KI_PRESET_KATEGORIEN
        cls.fc_presets  = FC_KI_PRESETS

    def test_kategorien_nicht_leer(self):
        """KI_PRESET_KATEGORIEN muss mindestens eine Kategorie enthalten."""
        self.assertGreater(len(self.kategorien), 0)

    def test_pflicht_kategorien_vorhanden(self):
        """Alle Kern-Kategorien müssen existieren."""
        for kat in ("★ Schnell", "🔧 Code", "🧱 FreeCAD: Erstellen"):
            self.assertIn(kat, self.kategorien,
                          f"Kategorie fehlt: {kat}")

    def test_schnell_presets_vollstaendig(self):
        """★ Schnell muss alle 5 Standard-Presets enthalten."""
        schnell = self.kategorien["★ Schnell"]
        for name in ("Was macht dieser Code?", "Fehler finden & erklären",
                     "Code verbessern", "Zusammenfassung", "Einfach erklären"):
            self.assertIn(name, schnell, f"Schnell-Preset fehlt: {name}")

    def test_alle_preset_prompts_nicht_leer(self):
        """Jeder Preset-Prompt muss einen nicht-leeren String enthalten."""
        for kat, eintraege in self.kategorien.items():
            for name, prompt in eintraege.items():
                self.assertIsInstance(prompt, str,
                    f"{kat} → {name}: kein String")
                self.assertGreater(len(prompt.strip()), 10,
                    f"{kat} → {name}: Prompt zu kurz oder leer")

    def test_flache_presets_enthaelt_alle_kategorien(self):
        """KI_PRESETS (flach) muss alle Kategorienamen als Trenner enthalten."""
        for kat in self.kategorien:
            trenn = f"── {kat} ──"
            self.assertIn(trenn, self.presets,
                          f"Kategorie-Trenner fehlt: {trenn}")

    def test_flache_presets_mindestanzahl(self):
        """KI_PRESETS muss mindestens 20 Einträge haben."""
        self.assertGreaterEqual(len(self.presets), 20)

    def test_fc_presets_vorhanden(self):
        """FC_KI_PRESETS muss FreeCAD-spezifische Presets enthalten."""
        self.assertGreater(len(self.fc_presets), 0)

    def test_freecad_presets_haben_prompts(self):
        """Alle FC_KI_PRESETS mit Inhalt müssen einen Prompt haben."""
        for name, prompt in self.fc_presets.items():
            if name.startswith("──"):
                continue
            self.assertGreater(len(prompt.strip()), 0,
                               f"FC-Preset leer: {name}")

    def test_preset_prompts_auf_deutsch(self):
        """Alle Schnell-Prompts müssen deutschsprachige Schlüsselwörter enthalten."""
        deutschen_woerter = ("Code", "erkläre", "zeige", "Deutsch", "Fehler",
                             "verbessere", "Fasse", "Schritt")
        schnell = self.kategorien["★ Schnell"]
        for name, prompt in schnell.items():
            gefunden = any(w in prompt for w in deutschen_woerter)
            self.assertTrue(gefunden,
                f"Preset '{name}' scheint nicht auf Deutsch: {prompt[:60]}")

    def test_fc_kategorien_in_kategorien_eingebunden(self):
        """FC_KI_PRESETS müssen in KI_PRESET_KATEGORIEN eingebettet sein."""
        alle_prompts = set()
        for eintraege in self.kategorien.values():
            alle_prompts.update(eintraege.values())
        for name, prompt in self.fc_presets.items():
            if name.startswith("──") or not prompt.strip():
                continue
            self.assertIn(prompt, alle_prompts,
                f"FC-Preset '{name}' nicht in KI_PRESET_KATEGORIEN eingebunden")


class TestNlGenerator(unittest.TestCase):
    """Tests für nl_generator.py – Konstanten und System-Prompts."""

    @classmethod
    def setUpClass(cls):
        projektpfad = os.path.join(
            os.path.dirname(__file__), "..", "data"
        )
        if projektpfad not in sys.path:
            sys.path.insert(0, projektpfad)
        import nl_generator as nlg
        cls.nlg = nlg

    def test_preset_schluessel_existieren(self):
        """Alle drei Preset-Schlüssel müssen definiert und nicht leer sein."""
        self.assertIsInstance(self.nlg.NL_PRESET_SCHLUESSEL, str)
        self.assertIsInstance(self.nlg.NL_PRESET_SCHLUESSEL_PD, str)
        self.assertIsInstance(self.nlg.NL_PRESET_SCHLUESSEL_SW, str)
        self.assertTrue(self.nlg.NL_PRESET_SCHLUESSEL)
        self.assertTrue(self.nlg.NL_PRESET_SCHLUESSEL_PD)
        self.assertTrue(self.nlg.NL_PRESET_SCHLUESSEL_SW)

    def test_preset_schluessel_enthalten_fc_nummer(self):
        """Jeder Preset-Schlüssel muss seine FC-Nummer tragen."""
        self.assertIn("FC11", self.nlg.NL_PRESET_SCHLUESSEL)
        self.assertIn("FC12", self.nlg.NL_PRESET_SCHLUESSEL_PD)
        self.assertIn("FC13", self.nlg.NL_PRESET_SCHLUESSEL_SW)

    def test_temperature_im_gueltigen_bereich(self):
        """NL_TEMPERATURE muss zwischen 0.0 und 1.0 liegen."""
        self.assertGreaterEqual(self.nlg.NL_TEMPERATURE, 0.0)
        self.assertLessEqual(self.nlg.NL_TEMPERATURE, 1.0)

    def test_schwache_modelle_liste_nicht_leer(self):
        """NL_PD_SCHWACHE_MODELLE muss bekannte Modelle enthalten."""
        self.assertIn("llama3",  self.nlg.NL_PD_SCHWACHE_MODELLE)
        self.assertIn("mistral", self.nlg.NL_PD_SCHWACHE_MODELLE)

    def test_fc11_prompt_enthaelt_pflichtinhalte(self):
        """FC11-Systemprompt muss kritische FreeCAD-Regeln enthalten."""
        prompt = self.nlg.NL_SYSTEM_PROMPT
        self.assertIn("App.Vector", prompt)
        self.assertIn("Part::Cut",  prompt)
        self.assertIn("Part::Fuse", prompt)
        self.assertIn("doc.addObject", prompt)

    def test_fc12_prompt_enthaelt_partdesign_reihenfolge(self):
        """FC12-Systemprompt muss PartDesign-Pflichtstruktur enthalten."""
        prompt = self.nlg.NL_SYSTEM_PROMPT_PARTDESIGN
        self.assertIn("PartDesign::Body",  prompt)
        self.assertIn("Sketcher::SketchObject", prompt)
        self.assertIn("PartDesign::Pad",   prompt)

    def test_fc13_prompt_enthaelt_verbote(self):
        """FC13-Systemprompt muss explizite Verbote (keine Doppelimporte) nennen."""
        prompt = self.nlg.NL_SYSTEM_PROMPT_SCHRITTWEISE
        self.assertIn("import FreeCAD", prompt)
        self.assertIn("KEIN", prompt)

    def test_alle_prompts_enden_mit_python_only_hinweis(self):
        """Alle Prompts müssen auf 'Nur Python-Code' hinweisen."""
        for prompt in (
            self.nlg.NL_SYSTEM_PROMPT,
            self.nlg.NL_SYSTEM_PROMPT_PARTDESIGN,
            self.nlg.NL_SYSTEM_PROMPT_SCHRITTWEISE,
        ):
            self.assertIn("Python", prompt)


# ══════════════════════════════════════════════════════════════════════════════
# 🐛  FEHLER-ZONE 7: Absichtlich falsch – für den Editor-Fehler-Tab
#     Syntax-Checker-Test einschalten → Klasse einkommentieren.
# ══════════════════════════════════════════════════════════════════════════════
# class KaputteTestKlasse:
#     def __init__(self)
#         self.wert = 42        # SyntaxError: fehlt ':'
#
#     def methode_ohne_return
#         print("ups")         # SyntaxError: fehlt ':'
#
#     def falscher_typ(self):
#         return self.wert + "string"  # Läuft durch aber → TypeError


# ══════════════════════════════════════════════════════════════════════════════
# ✅  REPORT-FUNKTION
# ══════════════════════════════════════════════════════════════════════════════

def zeige_fehler_demo():
    """Demonstriert alle Fehlertypen nacheinander."""
    print("\n" + "═" * 60)
    print("  🐛  FEHLER-DEMO  –  alle Typen einmal provozieren")
    print("═" * 60)

    tests = [
        ("NameError",          lambda: eval("nicht_def")),
        ("TypeError",          lambda: 1 + "x"),
        ("ZeroDivisionError",  lambda: 1 / 0),
        ("IndexError",         lambda: [][0]),
        ("KeyError",           lambda: {}["fehlt"]),
        ("AttributeError",     lambda: None.irgendwas()),
        ("FileNotFoundError",  lambda: open("/tmp/__xyz_nicht__.txt")),
        ("ValueError",         lambda: int("kein_int")),
    ]

    for name, fn in tests:
        try:
            fn()
            print(f"  ❌ {name:<25} → KEIN Fehler (unerwartet!)")
        except Exception as e:
            print(f"  ✅ {name:<25} → {type(e).__name__}: {e}")

    print("═" * 60)
    print("  Alle Fehler korrekt provoziert.")
    print("═" * 60 + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# ✅  EINSTIEGSPUNKT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    zeige_fehler_demo()

    print("🔬  Starte Unit-Tests für freecad-ai-editor ...\n")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    for klasse in [
        TestBackupErstellen,
        TestBackupWiederherstellen,
        TestNeuLaden,
        TestDbHoch,
        TestLesezeichenNavigation,
        TestLayoutPersistenz,
        TestPanelPlatzierung,
        TestPresets,
        TestNlGenerator,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(klasse))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "═" * 60)
    if result.wasSuccessful():
        print(f"  ✅  ALLE {result.testsRun} TESTS BESTANDEN")
    else:
        print(f"  ❌  {len(result.failures)} Fehler / "
              f"{len(result.errors)} Exceptions bei {result.testsRun} Tests")
    print("═" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)
