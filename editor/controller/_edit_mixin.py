# -*- coding: utf-8 -*-
"""Edit/Clean/Syntax-Tab-Logik für WerkzeugLeiste (pure Python-Mixin, kein QObject)."""

import os
import py_compile
import re
import tempfile

from qt_compat import QtWidgets, QtGui
import schrift
import theme

# PySide6/PySide2 Enum-Kompatibilität (wird auch in werkzeuge.py gebraucht)
_cur = QtGui.QTextCursor
_TC_BLOCK_UNDER_CUR = getattr(
    getattr(_cur, "SelectionType", None),
    "BlockUnderCursor",
    getattr(_cur, "BlockUnderCursor", None),
)
_TC_DOCUMENT = getattr(
    getattr(_cur, "SelectionType", None),
    "Document",
    getattr(_cur, "Document", None),
)


class _EditMixin:
    """
    Mixin mit der Logik von Edit, Bereinigung, Statistiken und Syntax-Check.
    Erwartet in der konkreten Klasse: self._ed, self._info, self._check_lbl,
    self._zeile_edit, self._ok(), self._err(),
    self._ersetze_bloecke(), self._ganz(), self._auswahl(), self._bloecke().
    """

    # ── Einrücken / Kommentar ─────────────────────────────────────────────────

    def _einruecken(self):
        self._ersetze_bloecke(lambda z: "    " + z)
        self._ok("→ Eingerückt")

    def _ausruecken(self):
        def aus(z):
            if z.startswith("    "):
                return z[4:]
            if z.startswith("\t"):
                return z[1:]
            return z
        self._ersetze_bloecke(aus)
        self._ok("← Ausgerückt")

    def _auskommentieren(self):
        cur, s, e = self._bloecke()
        bl = []
        b  = s
        while True:
            bl.append(b)
            if b == e:
                break
            b = b.next()
        alle_k = all(bl2.text().lstrip().startswith("#") or
                     not bl2.text().strip() for bl2 in bl)

        def tog(z):
            stripped = z.lstrip()
            einz = len(z) - len(stripped)
            if alle_k:
                if stripped.startswith("# "):
                    return z[:einz] + stripped[2:]
                if stripped.startswith("#"):
                    return z[:einz] + stripped[1:]
                return z
            return z[:einz] + "# " + stripped if stripped else z

        self._ersetze_bloecke(tog)
        self._ok("# " + ("entfernt" if alle_k else "hinzugefügt"))

    # ── Zeilen-Operationen ────────────────────────────────────────────────────

    def _duplizieren(self):
        cur = self._ed.textCursor()
        cur.beginEditBlock()
        cur.movePosition(QtGui.QTextCursor.EndOfBlock)
        cur.insertText("\n" + cur.block().text())
        cur.endEditBlock()
        self._ed.setTextCursor(cur)
        self._ok("⧉ Zeile dupliziert")

    def _zeile_loeschen(self):
        cur = self._ed.textCursor()
        cur.beginEditBlock()
        cur.select(_TC_BLOCK_UNDER_CUR)
        cur.removeSelectedText()
        cur.deleteChar()
        cur.endEditBlock()
        self._ok("✂ Zeile gelöscht")

    def _zeile_hoch(self):
        cur = self._ed.textCursor()
        b   = cur.block()
        if b.blockNumber() == 0:
            return
        z = b.text()
        cur.beginEditBlock()
        bc = QtGui.QTextCursor(b)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                        QtGui.QTextCursor.MoveMode.KeepAnchor)
        bc.removeSelectedText()
        bc.deletePreviousChar()
        bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
        bc.insertText(z + "\n")
        neu = self._ed.document().findBlockByNumber(b.blockNumber() - 1)
        cur.endEditBlock()
        self._ed.setTextCursor(QtGui.QTextCursor(neu))
        self._ok("⬆ Zeile nach oben")

    def _zeile_runter(self):
        cur = self._ed.textCursor()
        b   = cur.block()
        if not b.next().isValid():
            return
        z = b.text()
        cur.beginEditBlock()
        bc = QtGui.QTextCursor(b)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                        QtGui.QTextCursor.MoveMode.KeepAnchor)
        bc.removeSelectedText()
        bc.deleteChar()
        bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock)
        bc.insertText("\n" + z)
        neu = self._ed.document().findBlockByNumber(b.blockNumber() + 1)
        cur.endEditBlock()
        self._ed.setTextCursor(QtGui.QTextCursor(neu))
        self._ok("⬇ Zeile nach unten")

    # ── Text-Transformation ───────────────────────────────────────────────────

    def _gross(self):
        self._auswahl(str.upper);  self._ok("ABC Großbuchstaben")

    def _klein(self):
        self._auswahl(str.lower);  self._ok("abc Kleinbuchstaben")

    def _titel(self):
        self._auswahl(str.title);  self._ok("Abc Erster groß")

    def _tabs_spaces(self):
        self._ersetze_bloecke(lambda z: z.replace("\t", "    "))
        self._ok("⇥ Tabs ersetzt")

    # ── Bereinigung ───────────────────────────────────────────────────────────

    def _trailing_ws(self):
        self._ganz(lambda t: "\n".join(z.rstrip() for z in t.split("\n")))
        self._ok("␣ Trailing Whitespace entfernt")

    def _leerzeilen(self):
        self._ganz(lambda t: re.sub(r"\n{3,}", "\n\n", t))
        self._ok("⬜ Max. 2 Leerzeilen")

    def _schluss_lz(self):
        self._ganz(lambda t: t.rstrip("\n") + "\n")
        self._ok("¶ Schluss-Leerzeilen entfernt")

    def _bom(self):
        self._ganz(lambda t: t.lstrip("﻿"))
        self._ok("BOM entfernt")

    # ── Statistiken ───────────────────────────────────────────────────────────

    def _code_info(self):
        lines = self._ed.toPlainText().splitlines()
        n  = len(lines)
        le = sum(1 for z in lines if not z.strip())
        ko = sum(1 for z in lines if z.strip().startswith("#"))
        fn = sum(1 for z in lines if re.match(r"\s*(async\s+)?def\s+", z))
        cl = sum(1 for z in lines if re.match(r"\s*class\s+", z))
        im = sum(1 for z in lines if re.match(r"\s*(import|from)\s+", z))
        self._info.setText(
            f"<table cellspacing='2' cellpadding='3'>"
            f"<tr><td>📄 Zeilen:</td><td><b>{n}</b></td>"
            f"    <td>&nbsp;&nbsp;⬜ Leer:</td><td><b>{le}</b></td></tr>"
            f"<tr><td># Komm.:</td><td><b>{ko}</b></td>"
            f"    <td>&nbsp;&nbsp;⚙ def:</td><td><b>{fn}</b></td></tr>"
            f"<tr><td>◆ class:</td><td><b>{cl}</b></td>"
            f"    <td>&nbsp;&nbsp;📦 import:</td><td><b>{im}</b></td></tr>"
            f"<tr><td>🔤 Zeichen:</td><td colspan='3'><b>{len(self._ed.toPlainText()):,}</b></td></tr>"
            f"</table>"
        )
        self._ok("📊 Statistiken aktualisiert")

    # ── Syntax-Prüfung ────────────────────────────────────────────────────────

    def _syntax(self):
        text = self._ed.toPlainText()
        tmp  = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", encoding="utf-8",
                    delete=False) as f:
                f.write(text)
                tmp = f.name
            py_compile.compile(tmp, doraise=True)
            os.unlink(tmp)
            if hasattr(self._ed, "setze_fehler_zeilen"):
                self._ed.setze_fehler_zeilen([])
            self._check_lbl.setStyleSheet(
                theme.STY_SYNTAX_CHECK_LBL(schrift.pt(schrift.STUFE_LG)))
            self._check_lbl.setText("✅  Kein Syntaxfehler")
            self._ok("✅ Syntax OK")
        except py_compile.PyCompileError as e:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            meldung = str(e)
            m  = re.search(r"line (\d+)", meldung)
            nr = int(m.group(1)) if m else None
            kurz = re.sub(r"\(.*?\)", "", meldung).strip()
            txt = "❌  Syntaxfehler"
            if nr:
                txt += f"  →  Zeile {nr}"
            txt += f"\n{kurz[:120]}"
            if hasattr(self._ed, "setze_fehler_zeilen") and nr:
                self._ed.setze_fehler_zeilen([nr - 1])
            self._check_lbl.setStyleSheet(
                theme.STY_SYNTAX_CHECK_LBL(schrift.pt(schrift.STUFE_LG)))
            self._check_lbl.setText(txt)
            if nr:
                self._zeile_edit.setText(str(nr))
                self._goto_zeile()
            self._err(f"❌ Syntaxfehler Z {nr}")
        except Exception as ex:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            self._check_lbl.setText(f"⚠ {ex}")
