# -*- coding: utf-8 -*-
"""
WerkzeugLeiste – Rechter Sidebar-Tab für selbständiges Arbeiten.

Einbinden in editor.py:
    from werkzeuge import WerkzeugLeiste
    self._werkzeug_leiste = WerkzeugLeiste(self._editor)
    rechte_tabs.addTab(self._werkzeug_leiste, "🔧 Werkzeuge")
"""

import ast
import re
import py_compile
import tempfile
import os

from qt_compat import QtWidgets, QtCore, QtGui
import theme
import schrift

# ── PySide6 / PySide2 Enum-Kompatibilität ─────────────────────────────────────
# PySide6: SelectionType hat kein BlockContents → BlockUnderCursor verwenden
# PySide2: BlockContents direkt verfügbar
_cur = QtGui.QTextCursor
_sel = getattr(_cur, "SelectionType", None)
if _sel is not None:
    # PySide6 — BlockContents existiert nicht, BlockUnderCursor als Ersatz
    _TC_BLOCK_CONTENTS   = _sel.BlockUnderCursor
    _TC_BLOCK_UNDER_CUR  = _sel.BlockUnderCursor
    _TC_DOCUMENT         = _sel.Document
    _TC_LINE             = _sel.LineUnderCursor
else:
    # PySide2
    _TC_BLOCK_CONTENTS   = _cur.BlockContents
    _TC_BLOCK_UNDER_CUR  = _cur.BlockUnderCursor
    _TC_DOCUMENT         = _cur.Document
    _TC_LINE             = _cur.LineUnderCursor


# ── Stil-Konstanten ────────────────────────────────────────────────────────────


def _btn(text, tooltip="", small=False):
    b = QtWidgets.QPushButton(text)
    b.setToolTip(tooltip or text)   # Tooltip zeigt immer den vollen Text
    b.setMinimumHeight(24 if small else 27)
    b.setMinimumWidth(0)
    # Ignored: sizeHint-Breite wird vom Layout ignoriert → Button zwingt
    # den Container nicht breiter, füllt aber den verfügbaren Platz aus.
    b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    return b


def _section(text):
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet(
        f" font-size:{schrift.pt(schrift.STUFE_LG)}pt; font-weight:bold;"
        "font-family:'Ubuntu','Noto Color Emoji';"
        "padding-top:6px; padding-bottom:4px;"
        "border-bottom:1px solid ;"
    )
    return lbl


def _scroll_wrap(widget):
    """Wickelt ein Widget in eine ScrollArea ein – verhindert überhohes Fenster.
    Ohne ScrollArea berechnet Qt die sizeHint als Summe aller Inhalte
    und drückt damit das gesamte Fenster in die Höhe."""
    scroll = QtWidgets.QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    return scroll


# ── Lesezeichen-Modell ────────────────────────────────────────────────────────

class _LZModell(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._items: list[tuple[int, str]] = []

    def rowCount(self, p=QtCore.QModelIndex()):
        return len(self._items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        z, t = self._items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return f"Z {z+1:>4}  {t[:32]}"
        if role == QtCore.Qt.UserRole:
            return z
        return None

    def toggle(self, zeile, text):
        for i, (z, _) in enumerate(self._items):
            if z == zeile:
                self.beginRemoveRows(QtCore.QModelIndex(), i, i)
                self._items.pop(i)
                self.endRemoveRows()
                return
        n = len(self._items)
        self.beginInsertRows(QtCore.QModelIndex(), n, n)
        self._items.append((zeile, text.strip()))
        self._items.sort(key=lambda x: x[0])
        self.endInsertRows()

    def hat(self, zeile):
        return any(z == zeile for z, _ in self._items)

    def alle(self):
        return [z for z, _ in self._items]

    def loeschen(self):
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()


# ── Haupt-Widget ──────────────────────────────────────────────────────────────

class WerkzeugLeiste(QtWidgets.QWidget):
    """
    Kompaktes Werkzeug-Panel mit 4 Tabs ohne Scrollbars.

    Tab 1  📍 Nav   – Zeile springen · Funktionsübersicht · Lesezeichen
    Tab 2  ✏ Edit  – Einrücken · Kommentar · Verschieben · Transformation
    Tab 3  🧹 Clean – Bereinigung · Code-Statistiken
    Tab 4  ✅ Check – Python-Syntax-Prüfung
    """

    def __init__(self, editor: QtWidgets.QPlainTextEdit, parent=None):
        super().__init__(parent)
        # ── Schrift: Ubuntu + Emoji-Fallback (Regel 1) ────────────────────
        _f = QtGui.QFont("Ubuntu", 10)
        try:
            from main import emoji_font
            _f = emoji_font(_f)
        except Exception:
            pass
        self.setFont(_f)
        self.setObjectName("WerkzeugLeiste")
        self.setStyleSheet(
            "#WerkzeugLeiste QLabel, #WerkzeugLeiste QPushButton,"
            "#WerkzeugLeiste QLineEdit, #WerkzeugLeiste QComboBox,"
            "#WerkzeugLeiste QCheckBox, #WerkzeugLeiste QDoubleSpinBox,"
            "#WerkzeugLeiste QSpinBox, #WerkzeugLeiste QTabBar::tab,"
            "#WerkzeugLeiste QGroupBox, #WerkzeugLeiste QRadioButton {"
            "  font-family: 'Ubuntu'; }"
            "#WerkzeugLeiste QPlainTextEdit, #WerkzeugLeiste QTextEdit {"
            "  font-family: 'Courier New', monospace; }")
        # ──────────────────────────────────────────────────────────────────
        self._ed  = editor
        self._lzm = _LZModell()
        self._gespeicherte_selektion = None
        self._baue_ui()
        self._ed.cursorPositionChanged.connect(self._cursor_sync)
        self._ed.cursorPositionChanged.connect(self._lz_highlight)
        self._ed.cursorPositionChanged.connect(self._selektion_sichern)

    # ── Aufbau ───────────────────────────────────────────────────────────────

    def _baue_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(2, 2, 2, 2)
        root.setSpacing(2)

        btn_nav  = QtWidgets.QPushButton("📍 Nav")
        btn_edit = QtWidgets.QPushButton("✏ Edit & Check")
        for _b in (btn_nav, btn_edit):
            _b.setCheckable(True)
            _b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            _b.setStyleSheet(theme.STY_TABBAR)
        btn_nav.setChecked(True)

        tab_grid = QtWidgets.QGridLayout()
        tab_grid.setSpacing(0)
        tab_grid.setContentsMargins(0, 0, 0, 0)
        tab_grid.addWidget(btn_nav,  0, 0)
        tab_grid.addWidget(btn_edit, 0, 1)
        root.addLayout(tab_grid)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("color:palette(mid);margin:0;")
        root.addWidget(sep)

        stack = QtWidgets.QStackedWidget()
        stack.addWidget(self._tab_nav())
        stack.addWidget(self._tab_edit_clean())
        stack.setCurrentIndex(0)
        root.addWidget(stack, stretch=1)

        def _switch(idx, b_on, b_off):
            stack.setCurrentIndex(idx)
            b_on.setChecked(True)
            b_off.setChecked(False)
        btn_nav.clicked.connect( lambda: _switch(0, btn_nav,  btn_edit))
        btn_edit.clicked.connect(lambda: _switch(1, btn_edit, btn_nav))

        # ── Statuszeile ganz unten ────────────────────────────────────────
        self._status = QtWidgets.QLabel("")
        self._status.setStyleSheet(
            f"font-size:{schrift.pt(schrift.STUFE_LG)}pt;  padding:2px 4px;"
            "border-top:1px solid ;"
        )
        self._status.setWordWrap(True)
        root.addWidget(self._status)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 · NAV
    # ─────────────────────────────────────────────────────────────────────────

    def _tab_nav(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(3)

        # Zeile springen ─ QLineEdit statt Spinner (kein Regler!)
        v.addWidget(_section("Zeile anspringen"))
        row = QtWidgets.QHBoxLayout()
        self._zeile_edit = QtWidgets.QLineEdit()
        self._zeile_edit.setPlaceholderText("Nr.")
        self._zeile_edit.setFixedWidth(52)
        self._zeile_edit.setStyleSheet(
            f"QLineEdit{{ font-size:{schrift.pt(schrift.STUFE_XL)}pt;"
            "border:1px solid ;padding:3px 5px;border-radius:2px;}"
        )
        self._zeile_edit.setValidator(QtGui.QIntValidator(1, 99999))
        self._zeile_edit.returnPressed.connect(self._goto_zeile)
        b_goto = _btn("→ Gehe zu", "Zeile anspringen (Enter)", small=True)
        b_goto.clicked.connect(self._goto_zeile)
        row.addWidget(self._zeile_edit)
        row.addWidget(b_goto)
        row.addStretch()
        v.addLayout(row)

        # Code-Struktur (live, QTreeWidget)
        v.addWidget(_section("Code-Struktur  (live)"))
        self._nav_baum = QtWidgets.QTreeWidget()
        self._nav_baum.setHeaderHidden(True)
        self._nav_baum.setStyleSheet(
            f"QTreeWidget{{font-size:{schrift.pt(schrift.STUFE_LG)}pt;"
            "border:1px solid ;border-radius:2px;"
            "font-family:'Ubuntu','Noto Color Emoji';}"
            "QTreeWidget::item{padding:2px 2px;}"
            "QTreeWidget::item:selected{}"
            "QTreeWidget::item:hover{}"
            "QTreeWidget::branch:has-children:!has-siblings:closed,"
            "QTreeWidget::branch:closed:has-children:has-siblings{"
            "  border-image:none; image:none;}"
        )
        self._nav_baum.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)
        self._nav_baum.itemDoubleClicked.connect(self._nav_sprung_baum)
        v.addWidget(self._nav_baum, stretch=3)

        # Lesezeichen
        v.addWidget(_section("Lesezeichen"))
        self._lz_view = QtWidgets.QListView()
        self._lz_view.setModel(self._lzm)
        self._lz_view.setMinimumHeight(55)
        self._lz_view.setMaximumHeight(110)
        self._lz_view.doubleClicked.connect(self._lz_sprung)
        v.addWidget(self._lz_view, stretch=1)

        gr = QtWidgets.QGridLayout()
        gr.setSpacing(2)
        lz_daten = [
            ("＋ Setzen",     "Lesezeichen setzen / entfernen", self._lz_toggle),
            ("↑ Vorige",      "Zum vorigen Lesezeichen",         self._lz_vor),
            ("↓ Nächste",     "Zum nächsten Lesezeichen",        self._lz_nach),
            ("🗑 Alle löschen","Alle Lesezeichen entfernen",     self._lzm.loeschen),
        ]
        for i, (txt, tip, fn) in enumerate(lz_daten):
            b = _btn(txt, tip, small=True)
            b.setFixedHeight(24)
            b.clicked.connect(fn)
            gr.addWidget(b, i // 2, i % 2)
        v.addLayout(gr)
        v.addStretch()
        return _scroll_wrap(w)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 · EDIT & CLEAN (zusammengelegt)
    # ─────────────────────────────────────────────────────────────────────────

    def _tab_edit_clean(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(3)

        # ── Einrücken ────────────────────────────────────────────────────
        v.addWidget(_section("Einrücken"))
        gr1 = QtWidgets.QGridLayout()
        gr1.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("→ Einrücken",  "4 Leerzeichen vorne hinzufügen", self._einruecken),
            ("← Ausrücken",  "4 Leerzeichen vorne entfernen",  self._ausruecken),
        ]):
            b = _btn(txt, tip, small=True)   # ← small=True: 11px statt 13px, passt in 2 Spalten
            b.clicked.connect(fn)
            gr1.addWidget(b, 0, i)
        v.addLayout(gr1)

        # ── Kommentar ────────────────────────────────────────────────────
        v.addWidget(_section("Kommentar"))
        b_kom = _btn("# Ein/Auskomm.",
                     "# vorne hinzufügen oder entfernen")
        b_kom.clicked.connect(self._auskommentieren)
        v.addWidget(b_kom)

        # ── Zeilen ───────────────────────────────────────────────────────
        v.addWidget(_section("Zeilen"))
        gr2 = QtWidgets.QGridLayout()
        gr2.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("⧉ Duplizieren",  "Zeile darunter kopieren",     self._duplizieren),
            ("✂ Löschen",      "Aktuelle Zeile löschen",       self._zeile_loeschen),
            ("⬆ Hoch",         "Zeile nach oben verschieben",  self._zeile_hoch),
            ("⬇ Runter",       "Zeile nach unten verschieben", self._zeile_runter),
        ]):
            b = _btn(txt, tip, small=True)
            b.clicked.connect(fn)
            gr2.addWidget(b, i // 2, i % 2)
        v.addLayout(gr2)

        # ── Text-Transformation ──────────────────────────────────────────
        v.addWidget(_section("Text-Transformation"))
        gr3 = QtWidgets.QGridLayout()
        gr3.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("ABC → GROSS",   "Auswahl → GROSS",   self._gross),
            ("abc → klein",   "Auswahl → klein",   self._klein),
            ("Abc → Titel",   "Auswahl → Titel",   self._titel),
            ("⇥ Tab→Spaces", "Tabs durch Spaces",  self._tabs_spaces),
        ]):
            b = _btn(txt, tip, small=True)
            b.clicked.connect(fn)
            gr3.addWidget(b, i // 2, i % 2)
        v.addLayout(gr3)

        # ── Bereinigung ──────────────────────────────────────────────────
        v.addWidget(_section("Bereinigung"))
        gr4 = QtWidgets.QGridLayout()
        gr4.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("␣ Trailing WS",  "Leerzeichen am Zeilenende entfernen", self._trailing_ws),
            ("⬜ Max. 2 LZ",   "Mehr als 2 Leerzeilen → 2",          self._leerzeilen),
            ("¶ Schluss-LZ",   "Leerzeilen am Dateiende entfernen",   self._schluss_lz),
            ("BOM entfernen",  "\\ufeff am Anfang entfernen",          self._bom),
        ]):
            b = _btn(txt, tip, small=True)
            b.clicked.connect(fn)
            gr4.addWidget(b, i // 2, i % 2)
        v.addLayout(gr4)

        # ── Code-Statistiken ─────────────────────────────────────────────
        v.addWidget(_section("Code-Statistiken"))
        self._info = QtWidgets.QLabel("—")
        self._info.setWordWrap(True)
        self._info.setStyleSheet(
            " border:1px solid ;"
            f"padding:6px; font-size:{schrift.pt(schrift.STUFE_LG)}pt; border-radius:2px;"
            "font-family:'Ubuntu','Noto Color Emoji';"
        )
        v.addWidget(self._info)

        # ── Aktionen: Statistiken + Syntax nebeneinander ─────────────────
        gr5 = QtWidgets.QGridLayout()
        gr5.setSpacing(2)
        b_info = _btn("↺ Statistiken", "Code analysieren", small=True)
        b_info.clicked.connect(self._code_info)
        b_syn = _btn("▶ Syntax prüfen", "Datei auf Syntaxfehler prüfen", small=True)
        b_syn.clicked.connect(self._syntax)
        gr5.addWidget(b_info, 0, 0)
        gr5.addWidget(b_syn,  0, 1)
        v.addLayout(gr5)

        self._check_lbl = QtWidgets.QLabel("")
        self._check_lbl.setWordWrap(True)
        self._check_lbl.setStyleSheet(
            f"padding:6px; border-radius:3px; font-size:{schrift.pt(schrift.STUFE_LG)}pt;"
            "font-family:'Ubuntu','Noto Color Emoji';")
        v.addWidget(self._check_lbl)

        v.addStretch()
        return _scroll_wrap(w)

    # ─────────────────────────────────────────────────────────────────────────
    # Hilfsmethoden
    # ─────────────────────────────────────────────────────────────────────────

    def _selektion_sichern(self):
        """Speichert die aktuelle Selektion bevor Fokus verloren gehen kann."""
        cur = self._ed.textCursor()
        if cur.hasSelection():
            self._gespeicherte_selektion = QtGui.QTextCursor(cur)

    def _ok(self, text):
        self._status.setStyleSheet(
            f"font-size:{schrift.pt(schrift.STUFE_LG)}pt;  padding:2px 4px;"
            "border-top:1px solid ;")
        self._status.setText(text)
        QtCore.QTimer.singleShot(3500, lambda: self._status.setText(""))

    def _err(self, text):
        self._status.setStyleSheet(
            f"font-size:{schrift.pt(schrift.STUFE_LG)}pt;  padding:2px 4px;"
            "border-top:1px solid ;")
        self._status.setText(text)
        QtCore.QTimer.singleShot(5000, lambda: self._status.setText(""))

    def _cursor_sync(self):
        z = self._ed.textCursor().blockNumber() + 1
        self._zeile_edit.setText(str(z))

    def _lz_highlight(self):
        extra = []
        for z in self._lzm.alle():
            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            cur = QtGui.QTextCursor(
                self._ed.document().findBlockByNumber(z))
            cur.clearSelection()
            sel.cursor = cur
            extra.append(sel)
        self._ed.setExtraSelections(extra)

    def _bloecke(self):
        cur = self._ed.textCursor()
        # ── Fokus-Sicherung: gespeicherte Selektion bevorzugen ────────────
        # Wenn der Button-Klick den Fokus vom Editor genommen hat,
        # ist die Selektion weg. _gespeicherte_selektion enthält sie noch.
        if not cur.hasSelection() and hasattr(self, "_gespeicherte_selektion"):
            cur = self._gespeicherte_selektion
        if not cur.hasSelection():
            return cur, cur.block(), cur.block()
        s = self._ed.document().findBlock(cur.selectionStart())
        e = self._ed.document().findBlock(cur.selectionEnd())
        if (cur.selectionEnd() == e.position()) and s != e:
            e = e.previous()
        return cur, s, e

    def _ersetze_bloecke(self, fn):
        cur, s, e = self._bloecke()
        cur.beginEditBlock()
        b = s
        while True:
            neu = fn(b.text())
            if neu != b.text():
                bc = QtGui.QTextCursor(b)
                # Manuell Start bis Ende des Blocks selektieren
                # (BlockContents in PySide6 nicht verfügbar)
                bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
                bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                                QtGui.QTextCursor.MoveMode.KeepAnchor)
                bc.insertText(neu)
            if b == e:
                break
            b = b.next()
        cur.endEditBlock()

    def _ganz(self, fn):
        text = self._ed.toPlainText()
        neu  = fn(text)
        if neu == text:
            return
        pos = self._ed.textCursor().position()
        cur = self._ed.textCursor()
        cur.select(_TC_DOCUMENT)
        cur.insertText(neu)
        nc = self._ed.textCursor()
        nc.setPosition(min(pos, len(neu)))
        self._ed.setTextCursor(nc)

    def _auswahl(self, fn):
        cur = self._ed.textCursor()
        if cur.hasSelection():
            cur.insertText(fn(cur.selectedText()))
        else:
            b = cur.block()
            bc = QtGui.QTextCursor(b)
            bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                            QtGui.QTextCursor.MoveMode.KeepAnchor)
            bc.insertText(fn(bc.selectedText()))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 · Logik
    # ─────────────────────────────────────────────────────────────────────────

    def _goto_zeile(self):
        try:
            nr = int(self._zeile_edit.text()) - 1
        except ValueError:
            return
        doc = self._ed.document()
        b   = doc.findBlockByNumber(max(0, min(nr, doc.blockCount() - 1)))
        cur = QtGui.QTextCursor(b)
        self._ed.setTextCursor(cur)
        self._ed.centerCursor()
        self._ed.setFocus()

    def aktualisiere_code_baum(self, code_text: str):
        """
        Parst den Code per AST und baut den QTreeWidget-Baum live auf.
        Wird von editor.py über einen 500ms-Debounce-Timer aufgerufen.

        Struktur:
          📦 class Foo          ← türkis, fett
            └─ ⚙ methode()     ← gelb
          🚀 def funktion()     ← blau
          ⚠️  Syntax unvollst.  ← rot (beim Tippen)
        """
        self._nav_baum.clear()

        if not code_text.strip():
            return

        try:
            root = ast.parse(code_text)
        except SyntaxError:
            warn = QtWidgets.QTreeWidgetItem(self._nav_baum)
            warn.setText(0, "⚠  Syntax unvollständig …")
            return

        font_bold = QtGui.QFont()
        font_bold.setBold(True)

        for node in root.body:
            if isinstance(node, ast.ClassDef):
                kl = QtWidgets.QTreeWidgetItem(self._nav_baum)
                kl.setText(0, f"📦 {node.name}")
                kl.setFont(0, font_bold)
                kl.setData(0, QtCore.Qt.UserRole, node.lineno - 1)
                kl.setToolTip(0, f"Klasse  –  Zeile {node.lineno}")

                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [a.arg for a in sub.args.args if a.arg != "self"]
                        me = QtWidgets.QTreeWidgetItem(kl)
                        me.setText(0, f"  ⚙ {sub.name}({', '.join(args)})")
                        me.setData(0, QtCore.Qt.UserRole, sub.lineno - 1)
                        me.setToolTip(0, f"Methode  –  Zeile {sub.lineno}")

                kl.setExpanded(True)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                fn = QtWidgets.QTreeWidgetItem(self._nav_baum)
                fn.setText(0, f"🚀 {node.name}({', '.join(args)})")
                fn.setData(0, QtCore.Qt.UserRole, node.lineno - 1)
                fn.setToolTip(0, f"Funktion  –  Zeile {node.lineno}")

        n = self._nav_baum.topLevelItemCount()
        self._ok(f"🗂 {n} Einträge")

    def sammle_kontext_aus_baum(self) -> str:
        """
        Liest die aktuelle Baumstruktur aus dem QTreeWidget und gibt sie
        als kompakten String zurück.

        Verwendung in editor_ki_mixin.py:
            kontext = self._werkzeug_leiste.sammle_kontext_aus_baum()
        """
        struktur = []
        root = self._nav_baum.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            struktur.append(item.text(0).strip())
            for j in range(item.childCount()):
                struktur.append(f"  {item.child(j).text(0).strip()}")
        return "\n".join(struktur)

    def _nav_sprung_baum(self, item, _col=0):
        """Springt zur Zeile des angeklickten Baum-Eintrags."""
        nr = item.data(0, QtCore.Qt.UserRole)
        if nr is not None:
            self._zeile_edit.setText(str(nr + 1))
            self._goto_zeile()

    def _lz_toggle(self):
        cur  = self._ed.textCursor()
        nr   = cur.blockNumber()
        txt  = cur.block().text()
        self._lzm.toggle(nr, txt)
        self._lz_highlight()
        st = "gesetzt" if self._lzm.hat(nr) else "entfernt"
        self._ok(f"🔖 Lesezeichen Z {nr+1} {st}")

    def _lz_sprung(self, idx):
        nr = self._lzm.data(idx, QtCore.Qt.UserRole)
        if nr is not None:
            self._zeile_edit.setText(str(nr + 1))
            self._goto_zeile()

    def _lz_nach(self):
        alle = self._lzm.alle()
        if not alle:
            return
        ak = self._ed.textCursor().blockNumber()
        ziel = next((z for z in alle if z > ak), alle[0])
        self._zeile_edit.setText(str(ziel + 1))
        self._goto_zeile()

    def _lz_vor(self):
        alle = self._lzm.alle()
        if not alle:
            return
        ak = self._ed.textCursor().blockNumber()
        ziel = next((z for z in reversed(alle) if z < ak), alle[-1])
        self._zeile_edit.setText(str(ziel + 1))
        self._goto_zeile()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 · Logik
    # ─────────────────────────────────────────────────────────────────────────

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

    def _gross(self):
        self._auswahl(str.upper);  self._ok("ABC Großbuchstaben")

    def _klein(self):
        self._auswahl(str.lower);  self._ok("abc Kleinbuchstaben")

    def _titel(self):
        self._auswahl(str.title);  self._ok("Abc Erster groß")

    def _tabs_spaces(self):
        self._ersetze_bloecke(lambda z: z.replace("\t", "    "))
        self._ok("⇥ Tabs ersetzt")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 · Logik
    # ─────────────────────────────────────────────────────────────────────────

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
        self._ganz(lambda t: t.lstrip("\ufeff"))
        self._ok("BOM entfernt")

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

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4 · Logik
    # ─────────────────────────────────────────────────────────────────────────

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
                f"padding:6px;border-radius:3px;font-size:{schrift.pt(schrift.STUFE_LG)}pt;"
                "font-family:'Ubuntu','Noto Color Emoji';"
                ""
                "")
            self._check_lbl.setText("✅  Kein Syntaxfehler")
            self._ok("✅ Syntax OK")
        except py_compile.PyCompileError as e:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            meldung = str(e)
            m = re.search(r"line (\d+)", meldung)
            nr = int(m.group(1)) if m else None
            kurz = re.sub(r"\(.*?\)", "", meldung).strip()
            txt = f"❌  Syntaxfehler"
            if nr:
                txt += f"  →  Zeile {nr}"
            txt += f"\n{kurz[:120]}"
            if hasattr(self._ed, "setze_fehler_zeilen") and nr:
                self._ed.setze_fehler_zeilen([nr - 1])
            self._check_lbl.setStyleSheet(
                f"padding:6px;border-radius:3px;font-size:{schrift.pt(schrift.STUFE_LG)}pt;"
                "font-family:'Ubuntu','Noto Color Emoji';"
                ""
                "")
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
