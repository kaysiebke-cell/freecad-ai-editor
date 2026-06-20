# -*- coding: utf-8 -*-
"""
editor_widgets.py
─────────────────
Wiederverwendbare UI-Widgets für den Makro-Editor:

Exports:
  STY_GLOBAL           – globaler Stylesheet-String (leer, Theme wird von FreeCAD geerbt)
  fix_text_opt(w)      – AlignLeft im Dokument verankern (VOR setPlainText)
  fix_block_fmt(w)     – AlignLeft auf alle Blöcke erzwingen (NACH setPlainText)
  set_text(w, text)    – setPlainText + sofort fix_block_fmt
  LinksTextEdit        – QPlainTextEdit mit garantiert linksbündigem Placeholder
  CodeEditor           – QPlainTextEdit mit VS-Code-Einrückungs-Guides
  JediEditor           – CodeEditor + Jedi-Autovervollständigung + FreeCAD-Schutz
  _DateiFilterProxy    – Proxy-Modell für den Datei-Browser
"""

import os
import threading

from core.qt_compat import QtWidgets, QtCore, QtGui
from core import theme
from core import schrift

try:
    import jedi
    _HAS_JEDI = True
except ImportError:
    _HAS_JEDI = False


# ══════════════════════════════════════════════════════════════════════════════
# Globales Stylesheet – leer, FreeCAD-Theme wird geerbt
# ══════════════════════════════════════════════════════════════════════════════
STY_GLOBAL = ""


# ══════════════════════════════════════════════════════════════════════════════
# TEXT-RENDERING-HILFSFUNKTIONEN
# ══════════════════════════════════════════════════════════════════════════════
def fix_text_opt(widget, word_wrap: bool = True):
    opt = widget.document().defaultTextOption()
    opt.setAlignment(QtCore.Qt.AlignLeft)
    opt.setWrapMode(
        QtGui.QTextOption.WordWrap if word_wrap else QtGui.QTextOption.NoWrap)
    widget.document().setDefaultTextOption(opt)


def fix_block_fmt(widget):
    fmt = QtGui.QTextBlockFormat()
    fmt.setAlignment(QtCore.Qt.AlignLeft)
    cur = widget.textCursor()
    cur.select(QtGui.QTextCursor.Document)
    cur.mergeBlockFormat(fmt)
    cur.clearSelection()
    widget.setTextCursor(cur)


def set_text(widget, text: str):
    widget.setPlainText(text)
    fix_block_fmt(widget)


# ══════════════════════════════════════════════════════════════════════════════
# LinksTextEdit
# ══════════════════════════════════════════════════════════════════════════════
class LinksTextEdit(QtWidgets.QPlainTextEdit):
    def paintEvent(self, event):
        super().paintEvent(event)
        ph = self.placeholderText()
        if ph and not self.toPlainText():
            vp   = self.viewport()
            p    = QtGui.QPainter(vp)
            col  = self.palette().color(QtGui.QPalette.PlaceholderText)
            p.setPen(QtGui.QPen(col))
            rect = vp.rect().adjusted(6, 4, -6, -4)
            p.drawText(rect,
                       QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
                       | QtCore.Qt.TextWordWrap,
                       ph)
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
# LineNumberArea – Zeilennummern-Leiste für CodeEditor
# ══════════════════════════════════════════════════════════════════════════════
class LineNumberArea(QtWidgets.QWidget):
    """Schmale Leiste links vom Editor, die Zeilennummern anzeigt."""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QtCore.QSize(self._editor._zeilennummer_breite(), 0)

    def paintEvent(self, event):
        self._editor._zeichne_zeilennummern(event)


# ══════════════════════════════════════════════════════════════════════════════
# FehlerMinimap – Fehlerzeilen-Anzeige rechts vom Editor
# ══════════════════════════════════════════════════════════════════════════════
_MINIMAP_BREITE = 14


class FehlerMinimap(QtWidgets.QWidget):
    """Schmale Leiste rechts, zeigt Fehlerzeilen als farbige Balken."""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor  = editor
        self._zeilen: list[int] = []
        self.setFixedWidth(_MINIMAP_BREITE)
        self.setToolTip("Fehlerzeilen")

    def setze_fehler(self, zeilen: list[int]):
        self._zeilen = list(zeilen)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        pal     = self.palette()

        # Hintergrund – gleiche Farbe wie Zeilennummernleiste
        bg = pal.color(QtGui.QPalette.Window)
        painter.fillRect(event.rect(), bg)

        # Linke Trennlinie
        rand_farbe = pal.color(QtGui.QPalette.Mid)
        painter.setPen(QtGui.QPen(rand_farbe, 1))
        painter.drawLine(0, 0, 0, self.height())

        if not self._zeilen:
            painter.end()
            return

        gesamt = max(self._editor.document().blockCount(), 1)
        h      = self.height()
        w      = self.width()

        # Fehlerfarbe: roter Akzent aus Palette (kein hartkodiertes Rot)
        fehler_farbe = QtGui.QColor(pal.color(QtGui.QPalette.Highlight))
        fehler_farbe.setHsv(0,
                            min(255, fehler_farbe.saturation() + 150),
                            min(255, fehler_farbe.value() + 60))

        for zeile in self._zeilen:
            y = int((zeile / gesamt) * h)
            painter.fillRect(2, max(0, y - 2), w - 3, 5, fehler_farbe)

        painter.end()


# ══════════════════════════════════════════════════════════════════════════════
# CodeEditor – Einrückungs-Guides + Zeilennummern
# ══════════════════════════════════════════════════════════════════════════════
class CodeEditor(QtWidgets.QPlainTextEdit):
    """QPlainTextEdit mit VS-Code-ähnlichen Einrückungs-Guides und Zeilennummern."""
    INDENT_SPACES = 4

    @property
    def INDENT_FARBE(self):
        return self.palette().color(QtGui.QPalette.Mid)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self._fehler_minimap   = FehlerMinimap(self)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._line_number_area.update)

        self._update_line_number_area_width(0)

    def setze_fehler_zeilen(self, zeilen: list[int]):
        """Übergibt Fehlerzeilen an die Minimap (0-basiert)."""
        self._fehler_minimap.setze_fehler(zeilen)

    # ── Breite der Zeilennummerleiste ────────────────────────────────────────
    def _zeilennummer_breite(self) -> int:
        stellen = max(1, len(str(self.blockCount())))
        return 6 + self.fontMetrics().horizontalAdvance("9") * (stellen + 1)

    def _update_line_number_area_width(self, _new_block_count):
        self.setViewportMargins(self._zeilennummer_breite(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QtCore.QRect(cr.left(), cr.top(),
                         self._zeilennummer_breite(), cr.height()))
        sb_breite = self.verticalScrollBar().width() if self.verticalScrollBar().isVisible() else 0
        self._fehler_minimap.setGeometry(
            QtCore.QRect(cr.right() - sb_breite - _MINIMAP_BREITE, cr.top(),
                         _MINIMAP_BREITE, cr.height()))

    # ── Zeilennummern zeichnen ───────────────────────────────────────────────
    def _zeichne_zeilennummern(self, event):
        painter = QtGui.QPainter(self._line_number_area)

        # Hintergrund der Leiste
        bg_farbe = self.palette().color(QtGui.QPalette.Window)
        painter.fillRect(event.rect(), bg_farbe)

        breite = self._line_number_area.width()
        aktuelle_nr = self.textCursor().blockNumber()

        block    = self.firstVisibleBlock()
        nr       = block.blockNumber()
        offy     = self.contentOffset().y()
        rect_bot = event.rect().bottom()

        while block.isValid():
            geo = self.blockBoundingGeometry(block)
            top = int(geo.top() + offy)
            if top > rect_bot:
                break
            if block.isVisible():
                hoehe = int(geo.height())
                if nr == aktuelle_nr:
                    hl_farbe = self.palette().color(QtGui.QPalette.Highlight)
                    hl_farbe.setAlpha(40)
                    painter.fillRect(0, top, breite - 1, hoehe, hl_farbe)
                    text_farbe = self.palette().color(QtGui.QPalette.Text)
                else:
                    text_farbe = self.palette().color(
                        QtGui.QPalette.PlaceholderText)

                painter.setPen(text_farbe)
                painter.setFont(self.font())
                painter.drawText(
                    QtCore.QRect(0, top, breite - 4, hoehe),
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                    str(nr + 1))
            block = block.next()
            nr   += 1
        painter.end()

    # ── Einrückungs-Guides ───────────────────────────────────────────────────
    def paintEvent(self, event):
        super().paintEvent(event)
        painter  = QtGui.QPainter(self.viewport())
        painter.setPen(QtGui.QPen(self.INDENT_FARBE, 1))
        fm       = self.fontMetrics()
        tab_px   = fm.horizontalAdvance(" " * self.INDENT_SPACES)
        margin   = int(self.document().documentMargin())
        offy     = self.contentOffset().y()
        rect_bot = event.rect().bottom()
        block    = self.firstVisibleBlock()
        while block.isValid():
            geo = self.blockBoundingGeometry(block)
            top = geo.top() + offy
            if top > rect_bot:
                break
            if block.isVisible():
                text   = block.text()
                indent = len(text) - len(text.lstrip())
                ebenen = indent // self.INDENT_SPACES
                bot    = geo.bottom() + offy
                for i in range(1, ebenen + 1):
                    x = margin + i * tab_px
                    painter.drawLine(x, int(top), x, int(bot))
            block = block.next()
        painter.end()


# ══════════════════════════════════════════════════════════════════════════════
# FreeCAD Autocomplete-Schutz
# ══════════════════════════════════════════════════════════════════════════════
FREECAD_AUTOCOMPLETE_AUSNAHMEN = [
    "App.ActiveDocument",
    "Gui.ActiveDocument",
    "FreeCADGui.",
    "Gui.",
    "doc.getObject",
    "FreeCAD.Vector",
    "FreeCAD.Rotation",
    "sel[",
]


def _jedi_ausnahme(zeilentext: str) -> bool:
    text_clear = zeilentext.strip()
    if "setExpression" in text_clear or "Expression" in text_clear:
        return True
    if "ActiveDocument" in text_clear or "getDocument" in text_clear:
        if text_clear.count(".") > 2:
            return True
    if (text_clear.startswith("#")
            or text_clear.count('"') % 2 != 0
            or text_clear.count("'") % 2 != 0):
        return True
    return any(exc in text_clear for exc in FREECAD_AUTOCOMPLETE_AUSNAHMEN)


# ══════════════════════════════════════════════════════════════════════════════
# JediEditor – Code-Editor + Autovervollständigung + FreeCAD-Schutz
# ══════════════════════════════════════════════════════════════════════════════
class JediEditor(CodeEditor):
    """CodeEditor (Indent-Guides) + Jedi-basierter Python-Autovervollständigung."""
    _completions_ready = QtCore.Signal(list, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.completer = QtWidgets.QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setMaxVisibleItems(12)
        self.completer.activated.connect(self._insert_completion)
        self.completer.popup().setStyleSheet(
            theme.STY_JEDI_POPUP(schrift.pt(schrift.STUFE_BASE)))
        self._jedi_timer = QtCore.QTimer(self)
        self._jedi_timer.setSingleShot(True)
        self._jedi_timer.setInterval(300)
        self._jedi_timer.timeout.connect(self._start_jedi_thread)
        self._completions_ready.connect(self._show_completions)

    def _text_under_cursor(self) -> str:
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        return cursor.selectedText()

    def _start_jedi_thread(self):
        if not _HAS_JEDI:
            return
        aktuelle_zeile = self.textCursor().block().text()
        if _jedi_ausnahme(aktuelle_zeile):
            self.completer.popup().hide()
            return
        code   = self.toPlainText()
        line   = self.textCursor().blockNumber() + 1
        col    = self.textCursor().columnNumber()
        prefix = self._text_under_cursor()
        threading.Thread(
            target=self._fetch_completions,
            args=(code, line, col, prefix),
            daemon=True
        ).start()

    def _fetch_completions(self, code: str, line: int, col: int, prefix: str):
        try:
            matches = jedi.Script(code=code).complete(line=line, column=col)
            names   = [m.name for m in matches]
            if names:
                self._completions_ready.emit(names, prefix)
        except Exception:
            pass

    @QtCore.Slot(list, str)
    def _show_completions(self, names: list, prefix: str):
        current = self._text_under_cursor()
        if not current or not current.endswith(prefix[-1] if prefix else ""):
            return
        popup = self.completer.popup()
        self.completer.setModel(QtCore.QStringListModel(names, self.completer))
        self.completer.setCompletionPrefix(current)
        cr = self.cursorRect()
        cr.setWidth(
            popup.sizeHintForColumn(0)
            + popup.verticalScrollBar().sizeHint().width()
        )
        self.completer.complete(cr)

    def _insert_completion(self, completion: str):
        if self.completer.widget() is not self:
            return
        cursor = self.textCursor()
        prefix = self.completer.completionPrefix()
        if prefix:
            cursor.movePosition(
                QtGui.QTextCursor.Left,
                QtGui.QTextCursor.KeepAnchor,
                len(prefix),
            )
            cursor.removeSelectedText()
        cursor.insertText(completion)
        self.setTextCursor(cursor)

    _AUSRUECK_KW = frozenset({
        "pass", "return", "break", "continue", "raise", "yield",
    })

    _BLOCK_FORT_KW = frozenset({
        "except", "else", "elif", "finally", "case",
    })

    _INDENT_W = 4

    def _berechne_einrueckung(self) -> str:
        cursor     = self.textCursor()
        block_text = cursor.block().text()
        col        = cursor.columnNumber()
        links      = block_text[:col]
        stripped   = block_text.lstrip()
        basis      = block_text[: len(block_text) - len(stripped)]

        if links.rstrip().endswith(":"):
            return basis + " " * self._INDENT_W

        erstes = stripped.split()[0].rstrip(":") if stripped.split() else ""
        if erstes in self._AUSRUECK_KW:
            return basis[self._INDENT_W:] if len(basis) >= self._INDENT_W else ""

        return basis

    def _korrigiere_block_fort(self):
        cursor     = self.textCursor()
        block_text = cursor.block().text()
        stripped   = block_text.lstrip()
        basis      = block_text[: len(block_text) - len(stripped)]

        if not basis:
            return

        teile  = stripped.split()
        if not teile:
            return
        erstes = teile[0].rstrip(":")

        if erstes not in self._BLOCK_FORT_KW:
            return

        neue_basis = basis[self._INDENT_W:] if len(basis) >= self._INDENT_W else ""
        neuer_text = neue_basis + stripped

        if neuer_text == block_text:
            return

        col = cursor.columnNumber()
        c   = self.textCursor()
        c.movePosition(QtGui.QTextCursor.StartOfBlock)
        c.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
        c.beginEditBlock()
        c.removeSelectedText()
        c.insertText(neuer_text)
        c.endEditBlock()

        entfernt = len(basis) - len(neue_basis)
        neue_col = max(len(neue_basis), col - entfernt)
        c2 = self.textCursor()
        c2.movePosition(QtGui.QTextCursor.StartOfBlock)
        c2.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.MoveAnchor, neue_col)
        self.setTextCursor(c2)

    def _enter_mit_einrueckung(self):
        geplant = self._berechne_einrueckung()
        cursor  = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        cursor.insertBlock()
        if geplant:
            cursor.insertText(geplant)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self._jedi_timer.stop()
        self.completer.popup().hide()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        popup = self.completer.popup()

        if popup.isVisible():
            if event.key() == QtCore.Qt.Key_Escape:
                event.ignore()
                return
            if event.key() == QtCore.Qt.Key_Tab:
                event.ignore()
                return
            if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                popup.hide()
                self._jedi_timer.stop()
                if not (event.modifiers() & (
                        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
                    self._enter_mit_einrueckung()
                    return
                super().keyPressEvent(event)
                return

        if event.key() == QtCore.Qt.Key_Tab and not popup.isVisible():
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                self._ausruecken()
            else:
                self._einruecken()
            return

        if event.key() == QtCore.Qt.Key_Backtab:
            self._ausruecken()
            return

        if (event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
                and not popup.isVisible()
                and not (event.modifiers() & (
                    QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier))):
            self._enter_mit_einrueckung()
            return

        if (event.key() == QtCore.Qt.Key_Backspace
                and not popup.isVisible()
                and not (event.modifiers() & (
                    QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier))):
            if self._smart_bs():
                return

        super().keyPressEvent(event)

        if event.text() and event.text().isalpha():
            self._korrigiere_block_fort()

        # Autovervollständigung nach jedem Buchstaben / Punkt / Unterstrich starten
        if _HAS_JEDI and event.text() and event.text() in (
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ._"):
            self._jedi_timer.start()
        elif event.key() == QtCore.Qt.Key_Backspace:
            self._jedi_timer.start()

    def insertFromMimeData(self, source):
        """
        Beim Einfügen (Strg+V) wird der eingefügte Block automatisch
        auf die Einrückungstiefe der aktuellen Cursor-Position angepasst.
        Die interne Einrückungsstruktur des eingefügten Codes bleibt erhalten –
        nur die Basis-Einrückung wird an die Einfügestelle angeglichen.
        """
        if not source.hasText():
            super().insertFromMimeData(source)
            return

        text = source.text()

        # Nur bei mehrzeiligem Inhalt anpassen
        zeilen = text.split("\n")
        if len(zeilen) <= 1:
            super().insertFromMimeData(source)
            return

        # Aktuelle Einrückungstiefe der Einfügezeile ermitteln
        cursor     = self.textCursor()
        zeile_text = cursor.block().text()
        ziel_indent = len(zeile_text) - len(zeile_text.lstrip())

        # Minimale Einrückung im eingefügten Block ermitteln (ohne Leerzeilen)
        min_indent = float("inf")
        for z in zeilen:
            if z.strip():
                min_indent = min(min_indent, len(z) - len(z.lstrip()))
        if min_indent == float("inf"):
            min_indent = 0

        # Basis-Einrückung anpassen: Differenz auf jede nicht-leere Zeile anwenden
        delta   = ziel_indent - min_indent
        neu     = []
        for i, z in enumerate(zeilen):
            if i == 0:
                # Erste Zeile: Cursor steht bereits auf der richtigen Einrückung
                neu.append(z.lstrip() if delta >= 0 else z)
            elif z.strip():
                aktuelle = len(z) - len(z.lstrip())
                neue_ind = max(0, aktuelle + delta)
                neu.append(" " * neue_ind + z.lstrip())
            else:
                neu.append("")

        new_source = QtCore.QMimeData()
        new_source.setText("\n".join(neu))
        super().insertFromMimeData(new_source)

    def _einruecken(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            self._block_delta(+self._INDENT_W)
        else:
            col    = cursor.columnNumber()
            spaces = self._INDENT_W - (col % self._INDENT_W)
            cursor.insertText(" " * spaces)
            self.setTextCursor(cursor)

    def _ausruecken(self):
        self._block_delta(-self._INDENT_W)

    def _block_delta(self, delta: int):
        cursor = self.textCursor()

        if not cursor.hasSelection():
            text     = cursor.block().text()
            fuehrend = len(text) - len(text.lstrip(" "))
            remove   = min(abs(delta), fuehrend)
            if remove and delta < 0:
                pos = cursor.block().position()
                cursor.setPosition(pos)
                cursor.movePosition(
                    QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, remove)
                cursor.removeSelectedText()
                self.setTextCursor(cursor)
            return

        start_pos = cursor.selectionStart()
        end_pos   = cursor.selectionEnd()

        start_cur = QtGui.QTextCursor(self.document())
        start_cur.setPosition(start_pos)
        start_block = start_cur.blockNumber()

        end_cur = QtGui.QTextCursor(self.document())
        end_cur.setPosition(end_pos)
        if end_cur.columnNumber() == 0 and end_pos > start_pos:
            end_cur.movePosition(QtGui.QTextCursor.PreviousBlock)
        end_block = end_cur.blockNumber()

        cursor.beginEditBlock()
        work = QtGui.QTextCursor(self.document())
        for block_num in range(start_block, end_block + 1):
            blk = self.document().findBlockByNumber(block_num)
            if not blk.isValid():
                continue
            work.setPosition(blk.position())
            if delta > 0:
                work.insertText(" " * delta)
            else:
                text     = blk.text()
                fuehrend = len(text) - len(text.lstrip(" "))
                remove   = min(abs(delta), fuehrend)
                if remove:
                    work.movePosition(
                        QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, remove)
                    work.removeSelectedText()
        cursor.endEditBlock()

        start_blk = self.document().findBlockByNumber(start_block)
        end_blk   = self.document().findBlockByNumber(end_block)
        new_cur   = self.textCursor()
        new_cur.setPosition(start_blk.position())
        new_cur.setPosition(
            end_blk.position() + end_blk.length() - 1,
            QtGui.QTextCursor.KeepAnchor)
        self.setTextCursor(new_cur)

    def _smart_bs(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        text = cursor.block().text()
        col  = cursor.columnNumber()
        if col == 0 or text[:col].strip():
            return False
        remove = col % self._INDENT_W or self._INDENT_W
        cursor.movePosition(
            QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor, remove)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        return True

    def focusOutEvent(self, event):
        self._jedi_timer.stop()
        self.completer.popup().hide()
        super().focusOutEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
# _DateiFilterProxy
# ══════════════════════════════════════════════════════════════════════════════
class _DateiFilterProxy(QtCore.QSortFilterProxyModel):
    _CODE_ENDUNGEN = {".py", ".fcmacro", ".FCMacro"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text     = ""
        self._nur_code = True
        self.setDynamicSortFilter(True)

    def setze_filter(self, text: str, nur_code: bool):
        self._text     = text.lower()
        self._nur_code = nur_code
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent):
        modell = self.sourceModel()
        idx    = modell.index(source_row, 0, source_parent)
        pfad   = modell.filePath(idx)

        if modell.isDir(idx):
            return True

        name = os.path.basename(pfad)
        ext  = os.path.splitext(name)[1].lower()

        if self._nur_code and ext not in self._CODE_ENDUNGEN:
            return False

        if self._text and self._text not in name.lower():
            return False

        return True
