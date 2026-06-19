# -*- coding: utf-8 -*-
"""
WerkzeugLeiste – Rechter Sidebar-Tab für selbständiges Arbeiten.

Einbinden in editor.py:
    from werkzeuge import WerkzeugLeiste
    self._werkzeug_leiste = WerkzeugLeiste(self._editor)
    rechte_tabs.addTab(self._werkzeug_leiste, "🔧 Werkzeuge")
"""

from qt_compat import QtWidgets, QtCore, QtGui
import theme
import schrift

from _nav_mixin  import _NavMixin
from _edit_mixin import _EditMixin

# ── PySide6 / PySide2 Enum-Kompatibilität ─────────────────────────────────────
_cur = QtGui.QTextCursor
_sel = getattr(_cur, "SelectionType", None)
if _sel is not None:
    _TC_BLOCK_UNDER_CUR = _sel.BlockUnderCursor
    _TC_DOCUMENT        = _sel.Document
else:
    _TC_BLOCK_UNDER_CUR = _cur.BlockUnderCursor
    _TC_DOCUMENT        = _cur.Document


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


# ── Hilfs-Funktionen ──────────────────────────────────────────────────────────

def _btn(text, tooltip="", small=False):
    b = QtWidgets.QPushButton(text)
    b.setToolTip(tooltip or text)
    b.setMinimumHeight(24 if small else 27)
    b.setMinimumWidth(0)
    b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    return b


def _section(text):
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet(theme.STY_WERKZEUG_SEKTION(schrift.pt(schrift.STUFE_LG)))
    return lbl


def _scroll_wrap(widget):
    scroll = QtWidgets.QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    return scroll


# ── Haupt-Widget ──────────────────────────────────────────────────────────────

class WerkzeugLeiste(_NavMixin, _EditMixin, QtWidgets.QWidget):
    """
    Kompaktes Werkzeug-Panel mit 2 Tabs (Nav | Edit & Check).

    Tab 1  📍 Nav   – Zeile springen · Funktionsübersicht · Lesezeichen
    Tab 2  ✏ Edit  – Einrücken · Kommentar · Verschieben · Bereinigung · Syntax
    """

    def __init__(self, editor: QtWidgets.QPlainTextEdit, parent=None):
        super().__init__(parent)
        _f = QtGui.QFont("Ubuntu", 10)
        try:
            from main import emoji_font
            _f = emoji_font(_f)
        except Exception:
            pass
        self.setFont(_f)
        self.setObjectName("WerkzeugLeiste")
        self.setStyleSheet(theme.STY_WERKZEUG_LEISTE)
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
        sep.setStyleSheet(theme.STY_SEPARATOR_TIGHT)
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

        self._status = QtWidgets.QLabel("")
        self._status.setStyleSheet(
            theme.STY_WERKZEUG_STATUS(schrift.pt(schrift.STUFE_LG)))
        self._status.setWordWrap(True)
        root.addWidget(self._status)

    # ── Tab 1: Nav-UI ────────────────────────────────────────────────────────

    def _tab_nav(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(3)

        v.addWidget(_section("Zeile anspringen"))
        row = QtWidgets.QHBoxLayout()
        self._zeile_edit = QtWidgets.QLineEdit()
        self._zeile_edit.setPlaceholderText("Nr.")
        self._zeile_edit.setFixedWidth(52)
        self._zeile_edit.setStyleSheet(
            theme.STY_ZEILE_EDIT(schrift.pt(schrift.STUFE_XL)))
        self._zeile_edit.setValidator(QtGui.QIntValidator(1, 99999))
        self._zeile_edit.returnPressed.connect(self._goto_zeile)
        b_goto = _btn("→ Gehe zu", "Zeile anspringen (Enter)", small=True)
        b_goto.clicked.connect(self._goto_zeile)
        row.addWidget(self._zeile_edit)
        row.addWidget(b_goto)
        row.addStretch()
        v.addLayout(row)

        v.addWidget(_section("Code-Struktur  (live)"))
        self._nav_baum = QtWidgets.QTreeWidget()
        self._nav_baum.setHeaderHidden(True)
        self._nav_baum.setStyleSheet(
            theme.STY_CODE_BAUM(schrift.pt(schrift.STUFE_LG)))
        self._nav_baum.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)
        self._nav_baum.itemDoubleClicked.connect(self._nav_sprung_baum)
        v.addWidget(self._nav_baum, stretch=3)

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
            ("＋ Setzen",      "Lesezeichen setzen / entfernen", self._lz_toggle),
            ("↑ Vorige",       "Zum vorigen Lesezeichen",         self._lz_vor),
            ("↓ Nächste",      "Zum nächsten Lesezeichen",        self._lz_nach),
            ("🗑 Alle löschen", "Alle Lesezeichen entfernen",     self._lzm.loeschen),
        ]
        for i, (txt, tip, fn) in enumerate(lz_daten):
            b = _btn(txt, tip, small=True)
            b.setFixedHeight(24)
            b.clicked.connect(fn)
            gr.addWidget(b, i // 2, i % 2)
        v.addLayout(gr)
        v.addStretch()
        return _scroll_wrap(w)

    # ── Tab 2: Edit/Clean-UI ─────────────────────────────────────────────────

    def _tab_edit_clean(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(3)

        v.addWidget(_section("Einrücken"))
        gr1 = QtWidgets.QGridLayout()
        gr1.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("→ Einrücken", "4 Leerzeichen vorne hinzufügen", self._einruecken),
            ("← Ausrücken", "4 Leerzeichen vorne entfernen",  self._ausruecken),
        ]):
            b = _btn(txt, tip, small=True)
            b.clicked.connect(fn)
            gr1.addWidget(b, 0, i)
        v.addLayout(gr1)

        v.addWidget(_section("Kommentar"))
        b_kom = _btn("# Ein/Auskomm.", "# vorne hinzufügen oder entfernen")
        b_kom.clicked.connect(self._auskommentieren)
        v.addWidget(b_kom)

        v.addWidget(_section("Zeilen"))
        gr2 = QtWidgets.QGridLayout()
        gr2.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("⧉ Duplizieren", "Zeile darunter kopieren",     self._duplizieren),
            ("✂ Löschen",     "Aktuelle Zeile löschen",       self._zeile_loeschen),
            ("⬆ Hoch",        "Zeile nach oben verschieben",  self._zeile_hoch),
            ("⬇ Runter",      "Zeile nach unten verschieben", self._zeile_runter),
        ]):
            b = _btn(txt, tip, small=True)
            b.clicked.connect(fn)
            gr2.addWidget(b, i // 2, i % 2)
        v.addLayout(gr2)

        v.addWidget(_section("Text-Transformation"))
        gr3 = QtWidgets.QGridLayout()
        gr3.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("ABC → GROSS",  "Auswahl → GROSS",   self._gross),
            ("abc → klein",  "Auswahl → klein",   self._klein),
            ("Abc → Titel",  "Auswahl → Titel",   self._titel),
            ("⇥ Tab→Spaces", "Tabs durch Spaces",  self._tabs_spaces),
        ]):
            b = _btn(txt, tip, small=True)
            b.clicked.connect(fn)
            gr3.addWidget(b, i // 2, i % 2)
        v.addLayout(gr3)

        v.addWidget(_section("Bereinigung"))
        gr4 = QtWidgets.QGridLayout()
        gr4.setSpacing(2)
        for i, (txt, tip, fn) in enumerate([
            ("␣ Trailing WS", "Leerzeichen am Zeilenende entfernen", self._trailing_ws),
            ("⬜ Max. 2 LZ",  "Mehr als 2 Leerzeilen → 2",          self._leerzeilen),
            ("¶ Schluss-LZ",  "Leerzeilen am Dateiende entfernen",   self._schluss_lz),
            ("BOM entfernen", "\\ufeff am Anfang entfernen",          self._bom),
        ]):
            b = _btn(txt, tip, small=True)
            b.clicked.connect(fn)
            gr4.addWidget(b, i // 2, i % 2)
        v.addLayout(gr4)

        v.addWidget(_section("Code-Statistiken"))
        self._info = QtWidgets.QLabel("—")
        self._info.setWordWrap(True)
        self._info.setStyleSheet(
            theme.STY_CODE_STATISTIKEN_LBL(schrift.pt(schrift.STUFE_LG)))
        v.addWidget(self._info)

        gr5 = QtWidgets.QGridLayout()
        gr5.setSpacing(2)
        b_info = _btn("↺ Statistiken",  "Code analysieren",                  small=True)
        b_syn  = _btn("▶ Syntax prüfen","Datei auf Syntaxfehler prüfen",      small=True)
        b_info.clicked.connect(self._code_info)
        b_syn.clicked.connect(self._syntax)
        gr5.addWidget(b_info, 0, 0)
        gr5.addWidget(b_syn,  0, 1)
        v.addLayout(gr5)

        self._check_lbl = QtWidgets.QLabel("")
        self._check_lbl.setWordWrap(True)
        self._check_lbl.setStyleSheet(
            theme.STY_SYNTAX_CHECK_LBL(schrift.pt(schrift.STUFE_LG)))
        v.addWidget(self._check_lbl)

        v.addStretch()
        return _scroll_wrap(w)

    # ── Gemeinsame Hilfsmethoden ──────────────────────────────────────────────

    def _selektion_sichern(self):
        cur = self._ed.textCursor()
        if cur.hasSelection():
            self._gespeicherte_selektion = QtGui.QTextCursor(cur)

    def _ok(self, text):
        self._status.setStyleSheet(
            theme.STY_WERKZEUG_STATUS(schrift.pt(schrift.STUFE_LG)))
        self._status.setText(text)
        QtCore.QTimer.singleShot(3500, lambda: self._status.setText(""))

    def _err(self, text):
        self._status.setStyleSheet(
            theme.STY_WERKZEUG_STATUS(schrift.pt(schrift.STUFE_LG)))
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
            b  = cur.block()
            bc = QtGui.QTextCursor(b)
            bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                            QtGui.QTextCursor.MoveMode.KeepAnchor)
            bc.insertText(fn(bc.selectedText()))
