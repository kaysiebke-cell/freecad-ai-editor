# -*- coding: utf-8 -*-
"""
test_editor_live.py
═══════════════════
Startet den echten CodeEditor + WerkzeugLeiste und testet sie live.
Kein FreeCAD nötig — läuft direkt mit PySide6.

Ausführen:
    cd tests
    python3 test_editor_live.py
"""

import os
import sys
import unittest

# Muss mit FreeCADs eigenem Python laufen:
#   flatpak run --command=python3 org.freecad.FreeCAD \
#       /pfad/zu/tests/test_editor_live.py

# ── Pfade zum Projekt einrichten ─────────────────────────────────────────────
_BASIS = os.path.join(os.path.dirname(__file__), "..")
for _sub in ("", "core", "editor/widgets", "editor/controller", "editor"):
    _p = os.path.normpath(os.path.join(_BASIS, _sub))
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── FreeCAD mocken bevor irgendwas importiert wird ───────────────────────────
import types

_fc = types.ModuleType("FreeCAD")
_fc.getUserAppDataDir = lambda: "/tmp/"
_fcg = types.ModuleType("FreeCADGui")
sys.modules.setdefault("FreeCAD",    _fc)
sys.modules.setdefault("FreeCADGui", _fcg)

# ── Qt + Editor importieren ───────────────────────────────────────────────────
from qt_compat import QtWidgets, QtCore
try:
    from PySide6 import QtTest
except ImportError:
    from PySide2 import QtTest
from editor_widgets import FehlerMinimap, JediEditor
from werkzeuge import WerkzeugLeiste

# ── QApplication (einmalig) ───────────────────────────────────────────────────
_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)


# ══════════════════════════════════════════════════════════════════════════════
# ✅  TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestCodeEditorWidget(unittest.TestCase):
    """Testet den CodeEditor direkt als Qt-Widget."""

    def setUp(self):
        self.editor = JediEditor()
        self.editor.show()
        _app.processEvents()

    def tearDown(self):
        self.editor.close()
        _app.processEvents()

    def test_editor_startet(self):
        """Editor muss sichtbar und leer starten."""
        self.assertTrue(self.editor.isVisible())
        self.assertEqual(self.editor.toPlainText(), "")

    def test_text_eingabe(self):
        """Eingetippter Text muss im Editor erscheinen."""
        QtTest.QTest.keyClicks(self.editor, "x = 42")
        _app.processEvents()
        self.assertIn("x = 42", self.editor.toPlainText())

    def test_einrueckung_nach_doppelpunkt(self):
        """Nach 'def f():' + Enter muss automatisch eingerückt werden."""
        QtTest.QTest.keyClicks(self.editor, "def f():")
        QtTest.QTest.keyClick(self.editor, QtCore.Qt.Key_Return)
        _app.processEvents()
        text = self.editor.toPlainText()
        zeilen = text.split("\n")
        self.assertTrue(len(zeilen) >= 2)
        self.assertTrue(zeilen[1].startswith("    "),
                        f"Keine Einrückung nach def: {repr(zeilen[1])}")

    def test_tab_fuegt_leerzeichen_ein(self):
        """Tab-Taste muss 4 Leerzeichen einfügen."""
        QtTest.QTest.keyClick(self.editor, QtCore.Qt.Key_Tab)
        _app.processEvents()
        self.assertEqual(self.editor.toPlainText(), "    ")

    def test_set_text_setzt_inhalt(self):
        """setPlainText muss den Inhalt vollständig ersetzen."""
        self.editor.setPlainText("# hallo")
        _app.processEvents()
        self.assertEqual(self.editor.toPlainText(), "# hallo")


class TestFehlerMinimap(unittest.TestCase):
    """Testet die Fehler-Minimap direkt."""

    def setUp(self):
        self.editor = JediEditor()
        self.editor.resize(400, 300)
        self.editor.show()
        _app.processEvents()

    def tearDown(self):
        self.editor.close()
        _app.processEvents()

    def test_minimap_existiert(self):
        """Editor muss eine FehlerMinimap besitzen."""
        self.assertIsInstance(self.editor._fehler_minimap, FehlerMinimap)

    def test_minimap_startet_leer(self):
        """Minimap muss ohne Fehlerzeilen starten."""
        self.assertEqual(self.editor._fehler_minimap._zeilen, [])

    def test_setze_fehler_zeilen(self):
        """setze_fehler_zeilen muss die Zeilen in der Minimap speichern."""
        self.editor.setze_fehler_zeilen([5, 12, 30])
        _app.processEvents()
        self.assertEqual(self.editor._fehler_minimap._zeilen, [5, 12, 30])

    def test_fehler_zeilen_leeren(self):
        """Leere Liste muss die Minimap zurücksetzen."""
        self.editor.setze_fehler_zeilen([10, 20])
        self.editor.setze_fehler_zeilen([])
        _app.processEvents()
        self.assertEqual(self.editor._fehler_minimap._zeilen, [])

    def test_minimap_ist_sichtbar(self):
        """Minimap muss nach dem Anzeigen sichtbar sein."""
        self.assertTrue(self.editor._fehler_minimap.isVisible())

    def test_minimap_breite(self):
        """Minimap muss die definierte Breite haben."""
        from editor_widgets import _MINIMAP_BREITE
        self.assertEqual(self.editor._fehler_minimap.width(), _MINIMAP_BREITE)


class TestWerkzeugsSyntaxCheck(unittest.TestCase):
    """Testet den Syntax-Checker der WerkzeugLeiste mit echtem Editor."""

    def setUp(self):
        self.editor = JediEditor()
        self.wl     = WerkzeugLeiste(self.editor)
        self.editor.show()
        self.wl.show()
        _app.processEvents()

    def tearDown(self):
        self.wl.close()
        self.editor.close()
        _app.processEvents()

    def test_syntax_ok_leert_minimap(self):
        """Korrekter Code → Minimap muss nach Syntax-Check leer sein."""
        self.editor.setPlainText("x = 1\ny = 2\n")
        self.wl._syntax()
        _app.processEvents()
        self.assertEqual(self.editor._fehler_minimap._zeilen, [])

    def test_syntax_fehler_setzt_minimap(self):
        """Fehlerhafter Code → Minimap muss Fehlerzeile enthalten."""
        fehlerhafter_code = "def kaputt(\n    x, y\n    return x\n"
        self.editor.setPlainText(fehlerhafter_code)
        self.wl._syntax()
        _app.processEvents()
        self.assertGreater(len(self.editor._fehler_minimap._zeilen), 0,
                           "Minimap sollte Fehlerzeile enthalten")

    def test_syntax_fehler_zeile_ist_korrekt(self):
        """Die Fehlerzeile in der Minimap muss plausibel sein (0-basiert)."""
        # Fehler auf Zeile 3 (1-basiert) → Index 2 (0-basiert)
        code = "x = 1\ny = 2\ndef kaputt(\n    return 1\n"
        self.editor.setPlainText(code)
        self.wl._syntax()
        _app.processEvents()
        if self.editor._fehler_minimap._zeilen:
            zeile = self.editor._fehler_minimap._zeilen[0]
            self.assertGreaterEqual(zeile, 0)
            self.assertLess(zeile, self.editor.document().blockCount())

    def test_syntax_label_zeigt_ok(self):
        """Nach korrektem Code muss das Label '✅' zeigen."""
        self.editor.setPlainText("a = 1\n")
        self.wl._syntax()
        _app.processEvents()
        self.assertIn("✅", self.wl._check_lbl.text())

    def test_syntax_label_zeigt_fehler(self):
        """Nach fehlerhaftem Code muss das Label '❌' zeigen."""
        self.editor.setPlainText("def kaputt(\n    x\n    return x\n")
        self.wl._syntax()
        _app.processEvents()
        self.assertIn("❌", self.wl._check_lbl.text())


# ══════════════════════════════════════════════════════════════════════════════
# ✅  EINSTIEGSPUNKT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀  Starte Live-Editor-Tests ...\n")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    for klasse in [
        TestCodeEditorWidget,
        TestFehlerMinimap,
        TestWerkzeugsSyntaxCheck,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(klasse))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "═" * 60)
    if result.wasSuccessful():
        print(f"  ✅  ALLE {result.testsRun} LIVE-TESTS BESTANDEN")
    else:
        print(f"  ❌  {len(result.failures)} Fehler / "
              f"{len(result.errors)} Exceptions bei {result.testsRun} Tests")
    print("═" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)
