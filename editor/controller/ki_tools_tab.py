# -*- coding: utf-8 -*-
"""
ki_tools_tab.py  —  🛠 Tools-Tab für den MakroEditor.
"""

import sys, os

_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in [
    os.path.join(_DIR, "..", "ki"),
    os.path.join(_DIR, "..", "..", "data"),
    os.path.join(_DIR, "..", "..", "core"),
]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from qt_compat import QtWidgets, QtCore, QtGui
import schrift
import theme


# ── Aufklappbarer Abschnitt ───────────────────────────────────────────────────

class KlappSektion(QtWidgets.QWidget):
    """Aufklappbarer Abschnitt – Titel-Button ohne jegliches eigenes Stylesheet."""

    def __init__(self, titel: str, offen: bool = False, parent=None):
        super().__init__(parent)
        self._offen = offen
        self._titel = titel

        vl = QtWidgets.QVBoxLayout(self)
        vl.setContentsMargins(0, 2, 0, 2)
        vl.setSpacing(0)

        self._btn = QtWidgets.QPushButton(self._titel_text())
        self._btn.setMinimumHeight(28)
        self._btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._btn.setStyleSheet(theme.STY_TAB_BTN())
        self._btn.clicked.connect(self._toggle)
        vl.addWidget(self._btn)

        # Inhalt
        self._inhalt = QtWidgets.QWidget()
        self._inhalt.setVisible(offen)
        il = QtWidgets.QVBoxLayout(self._inhalt)
        il.setContentsMargins(8, 2, 4, 6)
        il.setSpacing(4)
        self._inhalt_layout = il
        vl.addWidget(self._inhalt)

    def _titel_text(self):
        return f"{'▼' if self._offen else '▶'}  {self._titel}"

    def _toggle(self):
        self._offen = not self._offen
        self._inhalt.setVisible(self._offen)
        self._btn.setText(self._titel_text())

    def addWidget(self, w):
        self._inhalt_layout.addWidget(w)

    def addLayout(self, lay):
        self._inhalt_layout.addLayout(lay)


# ── Haupt-Mixin ───────────────────────────────────────────────────────────────

class KiToolsTabMixin:

    def _baue_ki_tools_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        aussen = QtWidgets.QVBoxLayout(w)
        aussen.setContentsMargins(0, 0, 0, 0)
        aussen.setSpacing(0)

        # Info-Banner
        _verstecke = []
        from snippet_controller import SnippetController as _TM
        aussen.addWidget(_TM._baue_info_banner(
            "🛠 Was kann der Tools-Tab?",
            "Dokumentkontext: KI sieht dein FreeCAD-Dokument.<br>"
            "Werkzeuge: FreeCAD-Ops per Formular ohne Code.<br>"
            "① Aufklappen  ② Werte eingeben  ③ Ausführen",
            _verstecke,
        ))

        # ScrollArea für den Rest
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        inhalt = QtWidgets.QWidget()
        vl = QtWidgets.QVBoxLayout(inhalt)
        vl.setContentsMargins(4, 4, 4, 4)
        vl.setSpacing(4)

        # ── Sektion 1: Dokumentkontext (aufgeklappt) ──────────────────────
        sek1 = KlappSektion("📄 FreeCAD-Dokumentkontext", offen=True)

        info1 = QtWidgets.QLabel(
            "Wird automatisch an jeden KI-Prompt angehängt.")
        info1.setStyleSheet(
            f"font-size:{schrift.pt(schrift.STUFE_SM)}pt; font-style:italic;")
        info1.setWordWrap(True)
        sek1.addWidget(info1)

        self._kontext_anzeige = QtWidgets.QPlainTextEdit()
        self._kontext_anzeige.setReadOnly(True)
        self._kontext_anzeige.setFont(QtGui.QFont("Courier New", 9))
        self._kontext_anzeige.setFixedHeight(100)
        self._kontext_anzeige.setPlaceholderText("(Kein FreeCAD-Dokument)")
        sek1.addWidget(self._kontext_anzeige)

        btn_refresh = QtWidgets.QPushButton("🔄 Aktualisieren")
        btn_refresh.setFixedHeight(26)
        btn_refresh.clicked.connect(self._kontext_aktualisieren)
        sek1.addWidget(btn_refresh)
        vl.addWidget(sek1)

        # ── Sektion 2: Werkzeuge (zugeklappt) ────────────────────────────
        sek2 = KlappSektion("🛠 Werkzeuge (Direkt-Ausführung)", offen=False)

        info2 = QtWidgets.QLabel(
            "FreeCAD-Operationen ohne Code — sicher & rückgängig machbar.")
        info2.setStyleSheet(
            f"font-size:{schrift.pt(schrift.STUFE_SM)}pt; font-style:italic;")
        info2.setWordWrap(True)
        sek2.addWidget(info2)

        try:
            from ki_werkzeuge import WERKZEUG_REGISTER
            for name, defn in WERKZEUG_REGISTER.items():
                btn_start = QtWidgets.QPushButton(f"▶  {name}")
                btn_start.setFixedHeight(26)
                btn_start.setToolTip(defn.beschreibung)
                btn_start.setStyleSheet(
                    f"QPushButton{{text-align:left; padding:2px 6px;"
                    f"font-size:{schrift.pt(schrift.STUFE_BASE)}pt;}}")
                sek2.addWidget(btn_start)

                # Logik verdrahten: Klick öffnet den Werkzeug-Dialog
                btn_start.clicked.connect(
                    lambda checked, n=name, d=defn:
                        self._werkzeug_dialog(n, d))

        except ImportError:
            sek2.addWidget(QtWidgets.QLabel("⚠ ki_werkzeuge.py nicht gefunden"))

        vl.addWidget(sek2)

        # ── Sektion 3: Protokoll (zugeklappt) ────────────────────────────
        sek3 = KlappSektion("📋 Protokoll", offen=False)

        self._protokoll_area = QtWidgets.QPlainTextEdit()
        self._protokoll_area.setReadOnly(True)
        self._protokoll_area.setFont(QtGui.QFont("Courier New", 9))
        self._protokoll_area.setFixedHeight(100)
        self._protokoll_area.setPlaceholderText("Ergebnisse erscheinen hier …")
        sek3.addWidget(self._protokoll_area)

        btn_clear = QtWidgets.QPushButton("🗑 Leeren")
        btn_clear.setFixedHeight(26)
        btn_clear.clicked.connect(lambda: self._protokoll_area.clear())
        sek3.addWidget(btn_clear)
        vl.addWidget(sek3)

        vl.addStretch()
        scroll.setWidget(inhalt)
        aussen.addWidget(scroll)

        QtCore.QTimer.singleShot(300, self._kontext_aktualisieren)
        return w

    # ── Kontext ───────────────────────────────────────────────────────────

    def _kontext_aktualisieren(self):
        try:
            from dokument_kontext import get_dokument_kontext
            text = get_dokument_kontext()
            self._kontext_anzeige.setPlainText(
                text if text else "(Kein Dokument geöffnet)")
        except ImportError:
            self._kontext_anzeige.setPlainText("⚠ dokument_kontext.py nicht gefunden")
        except Exception as e:
            self._kontext_anzeige.setPlainText(f"Fehler: {e}")

    # ── Werkzeug-Dialog ───────────────────────────────────────────────────

    def _werkzeug_dialog(self, name: str, defn):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(f"🛠 {name}")
        dlg.setMinimumWidth(420)
        dlg.setMinimumHeight(300)

        haupt = QtWidgets.QVBoxLayout(dlg)
        haupt.setContentsMargins(10, 10, 10, 10)
        haupt.setSpacing(8)

        beschr = QtWidgets.QLabel(
            f"<b>{name}</b><br>"
            f"<small style='color:{theme.farbe_gedaempft(dlg)}'>"
            f"{defn.beschreibung}</small>")
        beschr.setWordWrap(True)
        haupt.addWidget(beschr)

        linie = QtWidgets.QFrame()
        linie.setFrameShape(QtWidgets.QFrame.HLine)
        linie.setFrameShadow(QtWidgets.QFrame.Sunken)
        haupt.addWidget(linie)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        felder_widget = QtWidgets.QWidget()
        grid = QtWidgets.QFormLayout(felder_widget)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setSpacing(8)
        grid.setLabelAlignment(QtCore.Qt.AlignRight)

        eingaben: dict = {}
        for param in defn.parameter:
            lbl = QtWidgets.QLabel(f"{param.name}:")
            lbl.setToolTip(param.beschreibung)
            if param.typ == "number":
                feld = QtWidgets.QDoubleSpinBox()
                feld.setRange(-99999, 99999)
                feld.setDecimals(2)
                feld.setValue(float(param.standard or 0))
                feld.setMinimumWidth(120)
                if param.name in ("x","y","z","laenge","breite","hoehe","radius","radius2"):
                    feld.setSuffix(" mm")
                elif param.name == "drehwinkel":
                    feld.setSuffix(" °")
            elif param.enum:
                feld = QtWidgets.QComboBox()
                feld.addItems(param.enum)
                feld.setMinimumWidth(120)
                if param.standard and param.standard in param.enum:
                    feld.setCurrentText(param.standard)
            elif param.typ == "string" and param.name == "code":
                feld = QtWidgets.QPlainTextEdit()
                feld.setFont(QtGui.QFont("Courier New", 9))
                feld.setMinimumHeight(120)
                feld.setPlaceholderText("Python-Code hier eingeben …")
            else:
                feld = QtWidgets.QLineEdit()
                feld.setPlaceholderText("optional" if not param.pflicht else param.beschreibung)
                if param.standard:
                    feld.setText(str(param.standard))
                feld.setMinimumWidth(120)
            lbl.setToolTip(param.beschreibung)
            grid.addRow(lbl, feld)
            eingaben[param.name] = feld

        scroll.setWidget(felder_widget)
        haupt.addWidget(scroll, stretch=1)

        ergebnis_lbl = QtWidgets.QLabel("")
        ergebnis_lbl.setWordWrap(True)
        ergebnis_lbl.setMinimumHeight(24)
        ergebnis_lbl.setStyleSheet(theme.sty_status(dlg))
        haupt.addWidget(ergebnis_lbl)

        linie2 = QtWidgets.QFrame()
        linie2.setFrameShape(QtWidgets.QFrame.HLine)
        linie2.setFrameShadow(QtWidgets.QFrame.Sunken)
        haupt.addWidget(linie2)

        btn_zeile = QtWidgets.QHBoxLayout()

        btn_ausfuehren = QtWidgets.QPushButton("▶  Ausführen")
        btn_ausfuehren.setMinimumHeight(32)
        btn_ausfuehren.setStyleSheet("QPushButton{font-weight:bold; padding:4px 16px;}")
        btn_zeile.addWidget(btn_ausfuehren)

        btn_in_editor = QtWidgets.QPushButton("📥  In Editor")
        btn_in_editor.setMinimumHeight(32)
        btn_in_editor.setToolTip("Generierten Code in den aktiven Editor-Tab einfügen")
        btn_in_editor.setEnabled(False)
        btn_zeile.addWidget(btn_in_editor)

        btn_anhaengen = QtWidgets.QPushButton("➕  Anhängen")
        btn_anhaengen.setMinimumHeight(32)
        btn_anhaengen.setToolTip("Code ans Ende des aktiven Editor-Tabs anhängen")
        btn_anhaengen.setEnabled(False)
        btn_zeile.addWidget(btn_anhaengen)

        btn_abbrechen = QtWidgets.QPushButton("✕")
        btn_abbrechen.setMinimumHeight(32)
        btn_abbrechen.setFixedWidth(36)
        btn_zeile.addWidget(btn_abbrechen)
        haupt.addLayout(btn_zeile)

        # Merkt sich den letzten generierten Code
        _letzter_code = {"wert": ""}

        def _get_aktiver_editor():
            """Gibt das aktive QPlainTextEdit zurück."""
            try:
                idx = self._editor_tab_widget.currentIndex()
                if 0 <= idx < len(self._tabs):
                    return self._tabs[idx]["editor"]
            except Exception:
                pass
            return None

        def _code_fuer_werkzeug(kwargs: dict) -> str:
            """Baut einen lesbaren Python-Code-Kommentar für den Editor."""
            zeilen = [f"# Werkzeug: {name}"]
            for k, v in kwargs.items():
                zeilen.append(f"# {k} = {v!r}")
            return "\n".join(zeilen)

        def ausfuehren():
            kwargs = {}
            for pname, widget in eingaben.items():
                if isinstance(widget, QtWidgets.QDoubleSpinBox):
                    kwargs[pname] = widget.value()
                elif isinstance(widget, QtWidgets.QComboBox):
                    kwargs[pname] = widget.currentText()
                elif isinstance(widget, QtWidgets.QPlainTextEdit):
                    kwargs[pname] = widget.toPlainText()
                else:
                    kwargs[pname] = widget.text()

            ergebnis_lbl.setStyleSheet(theme.sty_status(dlg))
            ergebnis_lbl.setText("⏳ Wird ausgeführt …")
            QtWidgets.QApplication.processEvents()

            try:
                from ki_werkzeuge import werkzeug_ausfuehren
                ergebnis = werkzeug_ausfuehren(name, kwargs)
                if ergebnis.erfolg:
                    ergebnis_lbl.setStyleSheet(theme.sty_status(dlg, "ok"))
                    ergebnis_lbl.setText(f"✅ {ergebnis.ausgabe}")
                    self._protokoll_hinzufuegen(name, ergebnis.ausgabe, True)
                    self._kontext_aktualisieren()
                    # Code für Editor vorbereiten
                    _letzter_code["wert"] = _code_fuer_werkzeug(kwargs)
                    btn_in_editor.setEnabled(True)
                    btn_anhaengen.setEnabled(True)
                else:
                    ergebnis_lbl.setStyleSheet(theme.sty_status(dlg, "fehler"))
                    ergebnis_lbl.setText(f"❌ {ergebnis.fehler}")
                    self._protokoll_hinzufuegen(name, ergebnis.fehler, False)
            except Exception as e:
                ergebnis_lbl.setStyleSheet(theme.sty_status(dlg, "fehler"))
                ergebnis_lbl.setText(f"❌ Fehler: {e}")

        def in_editor_laden():
            editor = _get_aktiver_editor()
            if editor is None:
                ergebnis_lbl.setText("⚠ Kein Editor-Tab geöffnet")
                return
            editor.setPlainText(_letzter_code["wert"])
            ergebnis_lbl.setStyleSheet(theme.sty_status(dlg, "ok"))
            ergebnis_lbl.setText("✅ In Editor geladen")

        def anhaengen():
            editor = _get_aktiver_editor()
            if editor is None:
                ergebnis_lbl.setText("⚠ Kein Editor-Tab geöffnet")
                return
            aktuell = editor.toPlainText()
            trenner = "\n\n" if aktuell.strip() else ""
            editor.setPlainText(aktuell + trenner + _letzter_code["wert"])
            # Cursor ans Ende
            cursor = editor.textCursor()
            cursor.movePosition(cursor.End)
            editor.setTextCursor(cursor)
            ergebnis_lbl.setStyleSheet(theme.sty_status(dlg, "ok"))
            ergebnis_lbl.setText("✅ An Editor angehängt")

        btn_ausfuehren.clicked.connect(ausfuehren)
        btn_in_editor.clicked.connect(in_editor_laden)
        btn_anhaengen.clicked.connect(anhaengen)
        btn_abbrechen.clicked.connect(dlg.reject)
        dlg.exec_()

    # ── Protokoll ─────────────────────────────────────────────────────────

    def _protokoll_hinzufuegen(self, name: str, text: str, erfolg: bool):
        symbol = "✅" if erfolg else "❌"
        self._protokoll_area.appendPlainText(f"{symbol} [{name}] {text}")
