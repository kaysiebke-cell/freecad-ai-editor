# -*- coding: utf-8 -*-
"""
RechteSidebar
─────────────
Einzige rechte Leiste: schmale Icon-Rail + Flyout-Accordion nach links.

Icons:
  🤖  ki      – KI-Aktionen (Laden, Markieren, Fragen, Ersetzen …)
  📂  datei   – Datei & Editor (Speichern, Formatieren …)
  📍  nav     – Navigation (Zeile springen, Code-Baum, Lesezeichen)
  ✂   edit    – Bearbeitung (Einrücken, Kommentar, Transformation …)
  🧹  clean   – Bereinigung + Statistiken + Syntax
  🔑  api     – API-Schlüssel

Öffentliche API (kompatibel zu bisherigem WerkzeugLeiste + AktionenSidebar):
  bind(editor)                      – Editor-Instanz verbinden
  aktualisiere_code_baum(code_text) – Nav-Baum aktualisieren
  sammle_kontext_aus_baum() -> str  – Baum-Struktur als Text
"""

import ast
import re
import py_compile
import tempfile
import os

from qt_compat import QtWidgets, QtCore, QtGui
import theme
import schrift

_PANEL_W = 200
_ANIM_MS = 180
_ICON_SZ = 46
_RAIL_W  = _ICON_SZ + 6


# ── Lesezeichen-Modell ────────────────────────────────────────────────────────

class _LZModell(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._items: list[tuple[int, str]] = []

    def rowCount(self, p=QtCore.QModelIndex()): return len(self._items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid(): return None
        z, t = self._items[index.row()]
        if role == QtCore.Qt.DisplayRole: return f"Z {z+1:>4}  {t[:28]}"
        if role == QtCore.Qt.UserRole:    return z
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

    def hat(self, zeile): return any(z == zeile for z, _ in self._items)
    def alle(self):       return [z for z, _ in self._items]
    def loeschen(self):
        self.beginResetModel(); self._items.clear(); self.endResetModel()


# ── Hilfsklassen ──────────────────────────────────────────────────────────────

class _Section(QtWidgets.QWidget):
    """Aufklappbarer Abschnitt."""

    def __init__(self, title: str, open_=True, parent=None):
        super().__init__(parent)
        self._open = open_
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 2)
        root.setSpacing(0)

        self._hd = QtWidgets.QPushButton()
        self._hd.setCheckable(True)
        self._hd.setChecked(open_)
        self._hd.setCursor(QtCore.Qt.PointingHandCursor)
        self._hd.setStyleSheet(
            theme.STY_SECTION_HEAD_BTN(schrift.pt(schrift.STUFE_LG)))
        self._hd.clicked.connect(self._toggle)
        root.addWidget(self._hd)

        self._body = QtWidgets.QWidget()
        self._bl = QtWidgets.QVBoxLayout(self._body)
        self._bl.setContentsMargins(2, 0, 2, 2)
        self._bl.setSpacing(1)
        root.addWidget(self._body)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet(theme.STY_SEPARATOR)
        root.addWidget(sep)
        self._set_title(title)
        self._body.setVisible(open_)

    def _set_title(self, t):
        self._title = t
        arrow = "▾" if self._open else "▸"
        self._hd.setText(f"{arrow}  {t}")

    def _toggle(self):
        self._open = not self._open
        self._body.setVisible(self._open)
        self._set_title(self._title)

    def btn(self, label, tip="", slot=None, enabled=True) -> QtWidgets.QPushButton:
        b = QtWidgets.QPushButton(label)
        b.setToolTip(tip or label)
        b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        b.setMinimumHeight(24)
        b.setEnabled(enabled)
        b.setStyleSheet(theme.STY_SECTION_BTN(schrift.pt(schrift.STUFE_LG)))
        if slot: b.clicked.connect(slot)
        self._bl.addWidget(b)
        return b

    def btn2(self, items):
        """Zwei Buttons nebeneinander. items = [(label,tip,slot), ...]"""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(2)
        btns = []
        for label, tip, slot in items:
            b = self.btn(label, tip, slot)
            self._bl.removeWidget(b)
            row.addWidget(b)
            btns.append(b)
        self._bl.addLayout(row)
        return btns

    def grid2(self, items):
        """Buttons in 2-Spalten-Grid. items = [(label, tip, slot), ...]"""
        btns = []
        row_layout = None
        for i, (label, tip, slot) in enumerate(items):
            b = QtWidgets.QPushButton(label)
            b.setToolTip(tip or label)
            b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            b.setMinimumHeight(26)
            b.setMaximumHeight(26)
            b.setStyleSheet(theme.STY_GRID_BTN(schrift.pt(schrift.STUFE_LG)))
            if slot:
                b.clicked.connect(slot)
            if i % 2 == 0:
                row_layout = QtWidgets.QHBoxLayout()
                row_layout.setSpacing(2)
                row_layout.setContentsMargins(0, 0, 0, 0)
                self._bl.addLayout(row_layout)
            row_layout.addWidget(b)
            btns.append(b)
        return btns

    def add(self, w: QtWidgets.QWidget):
        self._bl.addWidget(w)

    def add_layout(self, l):
        self._bl.addLayout(l)


def _scroll_wrap(w):
    sc = QtWidgets.QScrollArea()
    sc.setWidget(w)
    sc.setWidgetResizable(True)
    sc.setFrameShape(QtWidgets.QFrame.NoFrame)
    sc.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    return sc


# ── Flyout-Panel ──────────────────────────────────────────────────────────────

class _Flyout(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        outer.addWidget(self._scroll)

        self._anim = QtCore.QPropertyAnimation(self, b"maximumWidth")
        self._anim.setDuration(_ANIM_MS)
        self._anim.setEasingCurve(QtCore.QEasingCurve.InOutQuart)

    def set_content(self, w: QtWidgets.QWidget):
        self._scroll.setWidget(w)

    def open(self):
        self._anim.stop()
        self._anim.setStartValue(self.maximumWidth())
        self._anim.setEndValue(_PANEL_W)
        self._anim.start()

    def close(self):
        self._anim.stop()
        self._anim.setStartValue(self.maximumWidth())
        self._anim.setEndValue(0)
        self._anim.start()


# ── Icon-Rail ─────────────────────────────────────────────────────────────────

class _Rail(QtWidgets.QWidget):
    toggled = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(_RAIL_W)
        self._root = QtWidgets.QVBoxLayout(self)
        self._root.setContentsMargins(3, 6, 3, 6)
        self._root.setSpacing(2)
        self._btns: dict[str, QtWidgets.QPushButton] = {}

    def add(self, key, label, tooltip, sep=False):
        if sep:
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setStyleSheet(theme.STY_SEPARATOR)
            self._root.addWidget(line)
        b = QtWidgets.QPushButton(label)
        b.setToolTip(tooltip)
        b.setFixedSize(_ICON_SZ, _ICON_SZ)
        b.setCheckable(True)
        b.setCursor(QtCore.Qt.PointingHandCursor)
        b.setStyleSheet(theme.STY_RAIL_BTN(schrift.pt(schrift.STUFE_LG)))
        b.clicked.connect(lambda _checked, k=key: self.toggled.emit(k))
        self._root.addWidget(b)
        self._btns[key] = b

    def stretch(self): self._root.addStretch()

    def set_active(self, key):
        for k, b in self._btns.items():
            b.setChecked(k == key)


# ── Haupt-Widget ──────────────────────────────────────────────────────────────

class RechteSidebar(QtWidgets.QWidget):
    """
    Ersetzt QTabWidget auf der rechten Seite komplett.
    Kompatible öffentliche API:
      bind(editor)
      aktualisiere_code_baum(code_text)
      sammle_kontext_aus_baum() -> str
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ed   = None
        self._cur  = None
        self._lzm  = _LZModell()
        self._gespeicherte_selektion = None

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._flyout = _Flyout()
        root.addWidget(self._flyout)

        SP = QtWidgets.QStyle.StandardPixmap
        self._rail = _Rail()
        self._rail.add("ki",    "KI",    "KI-Aktionen")
        self._rail.add("datei", "Datei", "Datei & Editor")
        self._rail.add("nav",   "Nav",   "Navigation",     sep=True)
        self._rail.add("edit",  "Edit",  "Bearbeitung")
        self._rail.add("clean", "Clean", "Bereinigung & Syntax")
        self._rail.add("api",   "API",   "API-Schlüssel",  sep=True)
        self._rail.stretch()
        self._rail.toggled.connect(self._on_icon)
        root.addWidget(self._rail)

        # Status-Label (unten) – wird per _ok/_err gesetzt
        self._status_lbl = QtWidgets.QLabel("")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setStyleSheet(
            theme.STY_SIDEBAR_STATUS(schrift.pt(schrift.STUFE_LG)))
        self._status_lbl.hide()

        # Leere Widgets vorhalten damit aktualisiere_code_baum nicht crasht
        self._nav_baum   = QtWidgets.QTreeWidget()
        self._zeile_edit = QtWidgets.QLineEdit()
        self._info_lbl   = QtWidgets.QLabel("—")
        self._check_lbl  = QtWidgets.QLabel("")

        # Nav-Panel sofort öffnen (kein Animate – Widget noch nicht sichtbar)
        self._cur = "nav"
        self._rail.set_active("nav")
        self._flyout.set_content(self._build("nav"))
        self._flyout.setMaximumWidth(_PANEL_W)

    # ── öffentlich ───────────────────────────────────────────────────────────

    def bind(self, editor):
        self._ed = editor
        ew = editor._editor   # QPlainTextEdit
        ew.cursorPositionChanged.connect(self._cursor_sync)
        ew.cursorPositionChanged.connect(self._lz_highlight)
        ew.cursorPositionChanged.connect(self._selektion_sichern)

    @property
    def _ew(self):
        """Das QPlainTextEdit des aktuell verbundenen Editors (kann None sein)."""
        if self._ed is None:
            return None
        return getattr(self._ed, "_editor", None)

    def aktualisiere_code_baum(self, code_text: str):
        self._nav_baum.clear()
        if not code_text.strip(): return
        try:
            root = ast.parse(code_text)
        except SyntaxError:
            w = QtWidgets.QTreeWidgetItem(self._nav_baum)
            w.setText(0, "⚠  Syntax unvollständig …")
            return
        fb = QtGui.QFont(); fb.setBold(True)
        for node in root.body:
            if isinstance(node, ast.ClassDef):
                kl = QtWidgets.QTreeWidgetItem(self._nav_baum)
                kl.setText(0, f"📦 {node.name}")
                kl.setFont(0, fb)
                kl.setData(0, QtCore.Qt.UserRole, node.lineno - 1)
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [a.arg for a in sub.args.args if a.arg != "self"]
                        me = QtWidgets.QTreeWidgetItem(kl)
                        me.setText(0, f"  ⚙ {sub.name}({', '.join(args)})")
                        me.setData(0, QtCore.Qt.UserRole, sub.lineno - 1)
                kl.setExpanded(True)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                fn = QtWidgets.QTreeWidgetItem(self._nav_baum)
                fn.setText(0, f"🚀 {node.name}({', '.join(args)})")
                fn.setData(0, QtCore.Qt.UserRole, node.lineno - 1)

    def sammle_kontext_aus_baum(self) -> str:
        struktur = []
        root = self._nav_baum.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            struktur.append(item.text(0).strip())
            for j in range(item.childCount()):
                struktur.append(f"  {item.child(j).text(0).strip()}")
        return "\n".join(struktur)

    # ── Icon-Klick ────────────────────────────────────────────────────────────

    def _on_icon(self, key: str):
        if self._cur == key:
            self._rail.set_active(None)
            self._flyout.close()
            self._cur = None
            return
        self._cur = key
        self._rail.set_active(key)
        self._flyout.set_content(self._build(key))
        self._flyout.open()

    # ── Panel-Aufbau ──────────────────────────────────────────────────────────

    def _build(self, key: str) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(4, 6, 4, 4)
        v.setSpacing(0)

        if key == "ki":     self._build_ki(v)
        elif key == "datei":self._build_datei(v)
        elif key == "nav":  self._build_nav(v)
        elif key == "edit": self._build_edit(v)
        elif key == "clean":self._build_clean(v)
        elif key == "api":  self._build_api(v)

        v.addStretch()
        return _scroll_wrap(w)

    def _build_ki(self, v):
        e = self._ed
        s1 = _Section("Suchfeld / KI-Input")
        s1.grid2([
            ("Laden",     "Markierten Text ins Suchfeld laden",   e._copy_from_editor if e else None),
            ("Markieren", "Suchfeld-Inhalt im Editor markieren",  e._find_and_highlight if e else None),
            ("Leeren",    "Suchfeld leeren", (lambda: e.find_area.clear()) if e else None),
        ])
        v.addWidget(s1)

        s2 = _Section("KI-Aktionen")
        btns = s2.grid2([
            ("Analyse",  "Code automatisch analysieren",         e._auto_analyse if e else None),
            ("Fragen",   "KI befragen",                          e._ki_fragen if e else None),
            ("Ersetzen", "Block durch KI-Antwort ersetzen",      e._ersetzen_und_speichern if e else None),
            ("Einfügen", "KI-Antwort nach Block einfügen",       e._einfuegen_nach_fundstelle if e else None),
            ("Vorschau", "FreeCAD-Viewport anzeigen",            e.vorschau_starten if e else None),
        ])
        self._btn_ki        = btns[1]
        self._btn_ersetzen  = btns[2]; self._btn_ersetzen.setEnabled(False)
        self._btn_einfuegen = btns[3]; self._btn_einfuegen.setEnabled(False)
        v.addWidget(s2)

        if e:
            e._btn_ki        = self._btn_ki
            e._btn_ersetzen  = self._btn_ersetzen
            e._btn_einfuegen = self._btn_einfuegen

    def _build_datei(self, v):
        e = self._ed
        s1 = _Section("Datei")
        s1.grid2([
            ("Speichern",              "Datei speichern",                  e.speichern if e else None),
            ("Speichern & schließen",  "Speichern und Fenster schließen",  e.speichern_und_schliessen if e else None),
            ("Neu laden",              "Letzten Speicherstand laden",      e.neu_laden if e else None),
            ("Backup wiederherstellen","Neuestes .bak laden",              e._backup_wiederherstellen if e else None),
        ])
        v.addWidget(s1)

        s2 = _Section("Editor")
        try:
            from params import _HAS_AUTOPEP8
            fmt_lbl = "autopep8 formatieren" if _HAS_AUTOPEP8 else "Einrückung formatieren"
        except Exception:
            fmt_lbl = "Formatieren"
        s2.grid2([
            ("Alles auswählen", "Gesamten Text markieren",    e.alles_auswaehlen if e else None),
            ("Löschen",         "Auswahl oder alles löschen", e.loeschen_auswahl if e else None),
            (fmt_lbl,           "Code formatieren",           e._formatieren if e else None),
        ])
        v.addWidget(s2)

    def _build_nav(self, v):
        s1 = _Section("Zeile anspringen")
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(3)
        self._zeile_edit = QtWidgets.QLineEdit()
        self._zeile_edit.setPlaceholderText("Nr.")
        self._zeile_edit.setFixedWidth(50)
        self._zeile_edit.setValidator(QtGui.QIntValidator(1, 99999))
        self._zeile_edit.returnPressed.connect(self._goto_zeile)
        b_go = QtWidgets.QPushButton("→ Gehe zu")
        b_go.setMinimumHeight(24)
        b_go.clicked.connect(self._goto_zeile)
        row.addWidget(self._zeile_edit)
        row.addWidget(b_go)
        row.addStretch()
        s1.add_layout(row)
        v.addWidget(s1)

        s2 = _Section("Code-Struktur")
        self._nav_baum = QtWidgets.QTreeWidget()
        self._nav_baum.setHeaderHidden(True)
        self._nav_baum.setMinimumHeight(140)
        self._nav_baum.setStyleSheet(
            theme.STY_NAV_BAUM_SIDEBAR(schrift.pt(schrift.STUFE_LG)))
        self._nav_baum.itemDoubleClicked.connect(self._nav_sprung_baum)
        s2.add(self._nav_baum)
        v.addWidget(s2)

        if self._ed:
            self.aktualisiere_code_baum(self._ew.toPlainText())

        s3 = _Section("Lesezeichen")
        lz_view = QtWidgets.QListView()
        lz_view.setModel(self._lzm)
        lz_view.setMinimumHeight(50)
        lz_view.setMaximumHeight(100)
        lz_view.doubleClicked.connect(self._lz_sprung)
        s3.add(lz_view)
        gr = QtWidgets.QGridLayout()
        gr.setSpacing(2)
        for i, (lbl, tip, fn) in enumerate([
            ("＋ Setzen",      "Lesezeichen setzen/entfernen", self._lz_toggle),
            ("↑ Vorige",       "Zum vorigen Lesezeichen",       self._lz_vor),
            ("↓ Nächste",      "Zum nächsten Lesezeichen",      self._lz_nach),
            ("🗑 Alle löschen", "Alle entfernen",               self._lzm.loeschen),
        ]):
            b = QtWidgets.QPushButton(lbl)
            b.setMinimumHeight(24)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            gr.addWidget(b, i // 2, i % 2)
        s3.add_layout(gr)
        v.addWidget(s3)

    def _build_edit(self, v):
        s1 = _Section("Einrücken")
        s1.grid2([
            ("→ Einrücken", "4 Leerzeichen hinzufügen", self._einruecken),
            ("← Ausrücken", "4 Leerzeichen entfernen",  self._ausruecken),
        ])
        v.addWidget(s1)

        s2 = _Section("Kommentar & Zeilen")
        s2.grid2([
            ("# Ein/Auskomm.", "# hinzufügen oder entfernen", self._auskommentieren),
            ("⧉ Duplizieren",  "Zeile kopieren",              self._duplizieren),
            ("✂ Löschen",      "Aktuelle Zeile löschen",       self._zeile_loeschen),
            ("⬆ Hoch",         "Zeile nach oben",             self._zeile_hoch),
            ("⬇ Runter",       "Zeile nach unten",            self._zeile_runter),
        ])
        v.addWidget(s2)

        s3 = _Section("Text-Transformation")
        s3.grid2([
            ("ABC → GROSS",  "Auswahl → GROSS",  self._gross),
            ("abc → klein",  "Auswahl → klein",  self._klein),
            ("Abc → Titel",  "Auswahl → Titel",  self._titel),
            ("⇥ Tab→Spaces", "Tabs durch Spaces", self._tabs_spaces),
        ])
        v.addWidget(s3)

    def _build_clean(self, v):
        s1 = _Section("Bereinigung")
        s1.grid2([
            ("␣ Trailing WS", "Leerzeichen am Zeilenende entfernen", self._trailing_ws),
            ("⬜ Max. 2 LZ",  "Mehr als 2 Leerzeilen → 2",           self._leerzeilen),
            ("¶ Schluss-LZ",  "Leerzeilen am Dateiende entfernen",   self._schluss_lz),
            ("BOM entfernen", "\ufeff am Anfang entfernen",           self._bom),
        ])
        v.addWidget(s1)

        s2 = _Section("Code-Statistiken")
        self._info_lbl = QtWidgets.QLabel("—")
        self._info_lbl.setWordWrap(True)
        self._info_lbl.setStyleSheet(
            theme.STY_STATISTIKEN_LBL_SIDEBAR(schrift.pt(schrift.STUFE_LG)))
        s2.add(self._info_lbl)
        s2.grid2([
            ("↺ Statistiken",  "Code analysieren",     self._code_info),
            ("▶ Syntax prüfen","Syntaxfehler prüfen",  self._syntax),
        ])
        self._check_lbl = QtWidgets.QLabel("")
        self._check_lbl.setWordWrap(True)
        self._check_lbl.setStyleSheet(theme.STY_CHECK_LBL_SIDEBAR(schrift.pt(schrift.STUFE_LG)))
        s2.add(self._check_lbl)
        v.addWidget(s2)

    def _build_api(self, v):
        e = self._ed
        s = _Section("API-Schlüssel")
        if e and hasattr(e, "_key_anbieter"):
            s.add(e._key_anbieter)
            s.add(e._key_feld)
        v.addWidget(s)

    # ── Hilfsmethoden (Status) ────────────────────────────────────────────────

    def _ok(self, text):
        if self._ed and hasattr(self._ed, "_status"):
            self._ed._status.setText(text)
            QtCore.QTimer.singleShot(3500, lambda: (
                self._ed._status.setText("") if self._ed else None))

    def _err(self, text):
        if self._ed and hasattr(self._ed, "_status"):
            self._ed._status.setText(text)
            QtCore.QTimer.singleShot(5000, lambda: (
                self._ed._status.setText("") if self._ed else None))

    # ── Cursor / Lesezeichen ──────────────────────────────────────────────────

    def _selektion_sichern(self):
        if not self._ed: return
        cur = self._ew.textCursor()
        if cur.hasSelection():
            self._gespeicherte_selektion = QtGui.QTextCursor(cur)

    def _cursor_sync(self):
        if not self._ed: return
        z = self._ew.textCursor().blockNumber() + 1
        self._zeile_edit.setText(str(z))

    def _lz_highlight(self):
        if not self._ed: return
        extra = []
        for z in self._lzm.alle():
            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            cur = QtGui.QTextCursor(self._ew.document().findBlockByNumber(z))
            cur.clearSelection()
            sel.cursor = cur
            extra.append(sel)
        self._ew.setExtraSelections(extra)

    def _bloecke(self):
        cur = self._ew.textCursor()
        if not cur.hasSelection() and self._gespeicherte_selektion:
            cur = self._gespeicherte_selektion
        if not cur.hasSelection():
            return cur, cur.block(), cur.block()
        s = self._ew.document().findBlock(cur.selectionStart())
        e = self._ew.document().findBlock(cur.selectionEnd())
        if cur.selectionEnd() == e.position() and s != e:
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
            if b == e: break
            b = b.next()
        cur.endEditBlock()

    def _ganz(self, fn):
        if not self._ed: return
        text = self._ew.toPlainText()
        neu  = fn(text)
        if neu == text: return
        pos = self._ew.textCursor().position()
        cur = self._ew.textCursor()
        cur.select(QtGui.QTextCursor.SelectionType.Document)
        cur.insertText(neu)
        nc = self._ew.textCursor()
        nc.setPosition(min(pos, len(neu)))
        self._ew.setTextCursor(nc)

    def _auswahl(self, fn):
        if not self._ed: return
        cur = self._ew.textCursor()
        if cur.hasSelection():
            cur.insertText(fn(cur.selectedText()))
        else:
            b = cur.block()
            bc = QtGui.QTextCursor(b)
            bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                            QtGui.QTextCursor.MoveMode.KeepAnchor)
            bc.insertText(fn(bc.selectedText()))

    # ── Nav-Logik ─────────────────────────────────────────────────────────────

    def _goto_zeile(self):
        if not self._ed: return
        try: nr = int(self._zeile_edit.text()) - 1
        except ValueError: return
        doc = self._ew.document()
        b   = doc.findBlockByNumber(max(0, min(nr, doc.blockCount() - 1)))
        cur = QtGui.QTextCursor(b)
        self._ew.setTextCursor(cur)
        self._ew.centerCursor()
        self._ew.setFocus()

    def _nav_sprung_baum(self, item, _col=0):
        nr = item.data(0, QtCore.Qt.UserRole)
        if nr is not None:
            self._zeile_edit.setText(str(nr + 1))
            self._goto_zeile()

    def _lz_toggle(self):
        if not self._ed: return
        cur = self._ew.textCursor()
        nr  = cur.blockNumber()
        self._lzm.toggle(nr, cur.block().text())
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
        if not alle: return
        ak   = self._ew.textCursor().blockNumber()
        ziel = next((z for z in alle if z > ak), alle[0])
        self._zeile_edit.setText(str(ziel + 1)); self._goto_zeile()

    def _lz_vor(self):
        alle = self._lzm.alle()
        if not alle: return
        ak   = self._ew.textCursor().blockNumber()
        ziel = next((z for z in reversed(alle) if z < ak), alle[-1])
        self._zeile_edit.setText(str(ziel + 1)); self._goto_zeile()

    # ── Edit-Logik ────────────────────────────────────────────────────────────

    def _einruecken(self):
        self._ersetze_bloecke(lambda z: "    " + z); self._ok("→ Eingerückt")

    def _ausruecken(self):
        def aus(z):
            if z.startswith("    "): return z[4:]
            if z.startswith("\t"):   return z[1:]
            return z
        self._ersetze_bloecke(aus); self._ok("← Ausgerückt")

    def _auskommentieren(self):
        cur, s, e = self._bloecke()
        bl = []
        b  = s
        while True:
            bl.append(b)
            if b == e: break
            b = b.next()
        alle_k = all(b2.text().lstrip().startswith("#") or not b2.text().strip() for b2 in bl)
        def tog(z):
            stripped = z.lstrip(); einz = len(z) - len(stripped)
            if alle_k:
                if stripped.startswith("# "): return z[:einz] + stripped[2:]
                if stripped.startswith("#"):  return z[:einz] + stripped[1:]
                return z
            return z[:einz] + "# " + stripped if stripped else z
        self._ersetze_bloecke(tog)
        self._ok("# " + ("entfernt" if alle_k else "hinzugefügt"))

    def _duplizieren(self):
        if not self._ed: return
        cur = self._ew.textCursor()
        cur.beginEditBlock()
        cur.movePosition(QtGui.QTextCursor.EndOfBlock)
        cur.insertText("\n" + cur.block().text())
        cur.endEditBlock()
        self._ew.setTextCursor(cur)
        self._ok("⧉ Zeile dupliziert")

    def _zeile_loeschen(self):
        if not self._ed: return
        cur = self._ew.textCursor()
        cur.beginEditBlock()
        cur.select(QtGui.QTextCursor.SelectionType.BlockUnderCursor)
        cur.removeSelectedText(); cur.deleteChar()
        cur.endEditBlock()
        self._ok("✂ Zeile gelöscht")

    def _zeile_hoch(self):
        if not self._ed: return
        cur = self._ew.textCursor(); b = cur.block()
        if b.blockNumber() == 0: return
        z = b.text()
        cur.beginEditBlock()
        bc = QtGui.QTextCursor(b)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                        QtGui.QTextCursor.MoveMode.KeepAnchor)
        bc.removeSelectedText(); bc.deletePreviousChar()
        bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
        bc.insertText(z + "\n")
        neu = self._ew.document().findBlockByNumber(b.blockNumber() - 1)
        cur.endEditBlock()
        self._ew.setTextCursor(QtGui.QTextCursor(neu))
        self._ok("⬆ Zeile nach oben")

    def _zeile_runter(self):
        if not self._ed: return
        cur = self._ew.textCursor(); b = cur.block()
        if not b.next().isValid(): return
        z = b.text()
        cur.beginEditBlock()
        bc = QtGui.QTextCursor(b)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
        bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                        QtGui.QTextCursor.MoveMode.KeepAnchor)
        bc.removeSelectedText(); bc.deleteChar()
        bc.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock)
        bc.insertText("\n" + z)
        neu = self._ew.document().findBlockByNumber(b.blockNumber() + 1)
        cur.endEditBlock()
        self._ew.setTextCursor(QtGui.QTextCursor(neu))
        self._ok("⬇ Zeile nach unten")

    def _gross(self):  self._auswahl(str.upper); self._ok("ABC Großbuchstaben")
    def _klein(self):  self._auswahl(str.lower); self._ok("abc Kleinbuchstaben")
    def _titel(self):  self._auswahl(str.title); self._ok("Abc Erster groß")
    def _tabs_spaces(self):
        self._ersetze_bloecke(lambda z: z.replace("\t", "    ")); self._ok("⇥ Tabs ersetzt")

    # ── Clean-Logik ───────────────────────────────────────────────────────────

    def _trailing_ws(self):
        self._ganz(lambda t: "\n".join(z.rstrip() for z in t.split("\n")))
        self._ok("␣ Trailing Whitespace entfernt")

    def _leerzeilen(self):
        self._ganz(lambda t: re.sub(r"\n{3,}", "\n\n", t))
        self._ok("⬜ Max. 2 Leerzeilen")

    def _schluss_lz(self):
        self._ganz(lambda t: t.rstrip("\n") + "\n"); self._ok("¶ Schluss-Leerzeilen entfernt")

    def _bom(self):
        self._ganz(lambda t: t.lstrip("\ufeff")); self._ok("BOM entfernt")

    def _code_info(self):
        if not self._ed: return
        lines = self._ew.toPlainText().splitlines()
        n  = len(lines)
        le = sum(1 for z in lines if not z.strip())
        ko = sum(1 for z in lines if z.strip().startswith("#"))
        fn = sum(1 for z in lines if re.match(r"\s*(async\s+)?def\s+", z))
        cl = sum(1 for z in lines if re.match(r"\s*class\s+", z))
        im = sum(1 for z in lines if re.match(r"\s*(import|from)\s+", z))
        self._info_lbl.setText(
            f"<table cellspacing='2' cellpadding='2'>"
            f"<tr><td>📄 Zeilen:</td><td><b>{n}</b></td>"
            f"    <td>&nbsp;⬜ Leer:</td><td><b>{le}</b></td></tr>"
            f"<tr><td># Komm.:</td><td><b>{ko}</b></td>"
            f"    <td>&nbsp;⚙ def:</td><td><b>{fn}</b></td></tr>"
            f"<tr><td>◆ class:</td><td><b>{cl}</b></td>"
            f"    <td>&nbsp;📦 import:</td><td><b>{im}</b></td></tr>"
            f"<tr><td>🔤 Zeichen:</td><td colspan='3'><b>{len(self._ew.toPlainText()):,}</b></td></tr>"
            f"</table>")
        self._ok("📊 Statistiken aktualisiert")

    def _syntax(self):
        if not self._ed: return
        text = self._ew.toPlainText()
        tmp  = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", encoding="utf-8", delete=False) as f:
                f.write(text); tmp = f.name
            py_compile.compile(tmp, doraise=True)
            os.unlink(tmp)
            if hasattr(self._ew, "setze_fehler_zeilen"):
                self._ew.setze_fehler_zeilen([])
            self._check_lbl.setText("✅  Kein Syntaxfehler")
            self._ok("✅ Syntax OK")
        except py_compile.PyCompileError as ex:
            try: os.unlink(tmp)
            except Exception: pass
            meldung = str(ex)
            m  = re.search(r"line (\d+)", meldung)
            nr = int(m.group(1)) if m else None
            kurz = re.sub(r"\(.*?\)", "", meldung).strip()
            txt = "❌  Syntaxfehler"
            if nr: txt += f"  →  Zeile {nr}"
            txt += f"\n{kurz[:120]}"
            if hasattr(self._ew, "setze_fehler_zeilen") and nr:
                self._ew.setze_fehler_zeilen([nr - 1])
            self._check_lbl.setText(txt)
            if nr:
                self._zeile_edit.setText(str(nr))
                self._goto_zeile()
            self._err(f"❌ Syntaxfehler Z {nr}")
        except Exception as ex:
            try: os.unlink(tmp)
            except Exception: pass
            self._check_lbl.setText(f"⚠ {ex}")


# Rückwärts-kompatibler Alias
AktionenSidebar = RechteSidebar
