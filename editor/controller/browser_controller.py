# -*- coding: utf-8 -*-
"""
browser_controller.py
─────────────────────
Browser – Datei-Browser-Tab:
  - _baue_dateibrowser_tab()  – kompletter Datei-Browser aufbauen
  - Navigation, Filter, Lesezeichen
  - Datei öffnen / Pfad kopieren / Makro-Pfad setzen
"""

import os
import json

from qt_compat import QtWidgets, QtCore
import theme
import schrift

from editor_widgets import _DateiFilterProxy


class Browser:
    """Datei-Browser-Controller.

    Greift über self._e nur auf eine Stelle des Hosts zurück:
      _tab_oeffnen(pfad)   – Datei als Editor-Tab öffnen
    """

    def __init__(self, editor):
        self._e = editor

    # ══ Tab-Builder ════════════════════════════════════════════════════════
    def _baue_dateibrowser_tab(self) -> QtWidgets.QWidget:
        """
        Datei-Browser: Ordnerstruktur des PCs als Tree-View.
        Doppelklick auf .py / .FCMacro → im Editor öffnen.
        Doppelklick auf andere Dateien  → Pfad ins Suchfeld kopieren.
        """
        w = QtWidgets.QWidget()
        w.setMinimumWidth(0)
        w.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding)
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(2, 4, 2, 2)
        layout.setSpacing(3)

        # ── Zeile 1: Schnell-Navigation ──────────────────────────────
        nav1 = QtWidgets.QHBoxLayout()
        nav1.setSpacing(3)

        self._db_zurueck = QtWidgets.QPushButton("^")
        self._db_zurueck.setFixedSize(26, 22)
        self._db_zurueck.setToolTip("Übergeordneter Ordner (eine Ebene hoch)")
        nav1.addWidget(self._db_zurueck)

        self._db_home = QtWidgets.QPushButton("Hom")
        self._db_home.setFixedSize(36, 22)
        self._db_home.setToolTip("Home-Verzeichnis öffnen")
        nav1.addWidget(self._db_home)

        self._db_makro = QtWidgets.QPushButton("Makr")
        self._db_makro.setFixedSize(38, 22)
        self._db_makro.setToolTip("Makro-Ordner öffnen")
        nav1.addWidget(self._db_makro)

        self._db_pfad_feld = QtWidgets.QLineEdit()
        self._db_pfad_feld.setPlaceholderText("Pfad …")
        self._db_pfad_feld.setMinimumWidth(0)
        self._db_pfad_feld.setStyleSheet(
            theme.STY_DB_PFAD_FELD(schrift.pt(schrift.STUFE_SM)))
        self._db_pfad_feld.returnPressed.connect(self._db_gehe_zu_pfad)
        nav1.addWidget(self._db_pfad_feld, stretch=1)

        btn_go = QtWidgets.QPushButton("GO")
        btn_go.setFixedSize(28, 22)
        btn_go.setToolTip("Zu diesem Pfad navigieren")
        btn_go.clicked.connect(self._db_gehe_zu_pfad)
        nav1.addWidget(btn_go)

        layout.addLayout(nav1)

        # ── Zeile 2: Filter ──────────────────────────────────────────
        filter_row = QtWidgets.QHBoxLayout()
        filter_row.setSpacing(3)

        self._db_filter = QtWidgets.QLineEdit()
        self._db_filter.setPlaceholderText("Dateiname filtern …")
        self._db_filter.setClearButtonEnabled(True)
        self._db_filter.setMinimumWidth(0)
        self._db_filter.setStyleSheet(
            theme.STY_DB_FILTER_FELD(schrift.pt(schrift.STUFE_BASE)))
        self._db_filter.textChanged.connect(self._db_filter_anwenden)
        filter_row.addWidget(self._db_filter, stretch=1)

        self._db_nur_code = QtWidgets.QCheckBox(".py")
        self._db_nur_code.setChecked(True)
        self._db_nur_code.setToolTip("Nur .py und .FCMacro anzeigen")
        self._db_nur_code.setStyleSheet(
            theme.STY_DB_CHECKBOX(schrift.pt(schrift.STUFE_SM)))
        self._db_nur_code.stateChanged.connect(self._db_filter_anwenden)
        filter_row.addWidget(self._db_nur_code)

        layout.addLayout(filter_row)

        # ── Neue Datei anlegen ───────────────────────────────────────
        btn_neu = QtWidgets.QPushButton("＋  Neue Datei anlegen")
        btn_neu.setToolTip("Neue .py-Datei im aktuellen Ordner anlegen")
        btn_neu.setMinimumHeight(26)
        btn_neu.setStyleSheet(theme.STY_DB_NEU_BTN(schrift.pt(schrift.STUFE_BASE)))
        btn_neu.clicked.connect(self._db_neue_datei)
        layout.addWidget(btn_neu)

        # ── Lesezeichen ──────────────────────────────────────────────
        self._db_lz_widget = QtWidgets.QWidget()
        lz_layout = QtWidgets.QHBoxLayout(self._db_lz_widget)
        lz_layout.setContentsMargins(0, 0, 0, 0)
        lz_layout.setSpacing(2)

        self._db_lz_combo = QtWidgets.QComboBox()
        self._db_lz_combo.setStyleSheet(
            theme.STY_DB_LZ_COMBO(schrift.pt(schrift.STUFE_SM)))
        self._db_lz_combo.setToolTip("Lesezeichen")
        self._db_lz_combo.activated.connect(self._db_lz_springen)
        lz_layout.addWidget(self._db_lz_combo, stretch=1)

        btn_lz_add = QtWidgets.QPushButton("★")
        btn_lz_add.setFixedSize(22, 22)
        btn_lz_add.setToolTip("Aktuellen Ordner als Lesezeichen speichern")
        btn_lz_add.setStyleSheet(theme.STY_DB_LZ_BTN(schrift.pt(schrift.STUFE_LG)))
        btn_lz_add.clicked.connect(self._db_lz_hinzufuegen)
        lz_layout.addWidget(btn_lz_add)

        btn_lz_del = QtWidgets.QPushButton("✕")
        btn_lz_del.setFixedSize(22, 22)
        btn_lz_del.setToolTip("Ausgewähltes Lesezeichen entfernen")
        btn_lz_del.setStyleSheet(theme.STY_DB_LZ_BTN(schrift.pt(schrift.STUFE_BASE)))
        btn_lz_del.clicked.connect(self._db_lz_entfernen)
        lz_layout.addWidget(btn_lz_del)

        layout.addWidget(self._db_lz_widget)

        # ── Datei-Tree ───────────────────────────────────────────────
        self._db_modell = QtWidgets.QFileSystemModel()
        self._db_modell.setRootPath("")

        self._db_proxy = _DateiFilterProxy(self._e)
        self._db_proxy.setSourceModel(self._db_modell)

        self._db_tree = QtWidgets.QTreeView()
        self._db_tree.setModel(self._db_proxy)
        self._db_tree.setAnimated(True)
        self._db_tree.setSortingEnabled(True)
        self._db_tree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self._db_tree.setHeaderHidden(True)
        self._db_tree.setColumnWidth(0, 160)
        self._db_tree.setMinimumWidth(0)
        self._db_tree.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored,
            QtWidgets.QSizePolicy.Expanding)
        self._db_tree.hideColumn(1)   # Größe
        self._db_tree.hideColumn(2)   # Typ
        self._db_tree.hideColumn(3)   # Datum
        self._db_tree.setHeaderHidden(True)  # kein Header nötig bei einer Spalte
        self._db_tree.setStyleSheet(theme.STY_DB_TREE(schrift.pt(schrift.STUFE_BASE)))
        self._db_tree.doubleClicked.connect(self._db_doppelklick)
        self._db_tree.clicked.connect(self._db_einzelklick)
        self._db_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._db_tree.customContextMenuRequested.connect(self._db_kontext_menu)

        layout.addWidget(self._db_tree, stretch=1)

        # ── Status & Aktions-Zeile ───────────────────────────────────
        self._db_status = QtWidgets.QLabel("")
        self._db_status.setStyleSheet(theme.STY_DB_STATUS(schrift.pt(schrift.STUFE_SM)))
        layout.addWidget(self._db_status)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(3)
        btn_oeffnen = QtWidgets.QPushButton("Öffnen")
        btn_oeffnen.setToolTip("Ausgewählte Datei im Editor öffnen")
        btn_oeffnen.clicked.connect(self._db_ausgewaehlte_oeffnen)
        btn_row.addWidget(btn_oeffnen)

        btn_pfad = QtWidgets.QPushButton("Pfad")
        btn_pfad.setToolTip("Pfad in Zwischenablage kopieren")
        btn_pfad.clicked.connect(self._db_pfad_kopieren)
        btn_row.addWidget(btn_pfad)

        btn_explorer = QtWidgets.QPushButton("Manager")
        btn_explorer.setToolTip("Ordner im Makro-Manager setzen")
        btn_explorer.clicked.connect(self._db_als_makro_pfad)
        btn_row.addWidget(btn_explorer)

        layout.addLayout(btn_row)

        # ── Initialisieren ───────────────────────────────────────────
        self._db_lesezeichen: list = []   # [(name, pfad)]
        self._db_wurzel = os.path.expanduser("~")
        self._db_set_wurzel(self._db_wurzel)
        self._db_lz_laden()

        # Navigation verdrahten
        self._db_zurueck.clicked.connect(self._db_hoch)
        self._db_home.clicked.connect(
            lambda: self._db_set_wurzel(os.path.expanduser("~")))
        self._db_makro.clicked.connect(
            lambda: self._db_set_wurzel(self._makro_pfad_holen()))

        return w

    # ── Navigation ────────────────────────────────────────────────────────
    def _makro_pfad_holen(self) -> str:
        """Makro-Pfad aus params holen (ohne direkten Import von manager)."""
        try:
            from params import lade_pfad
            return lade_pfad()
        except Exception:
            return os.path.expanduser("~")

    def _db_set_wurzel(self, pfad: str):
        """Setzt den sichtbaren Wurzelordner des Trees."""
        if not os.path.isdir(pfad):
            return
        self._db_wurzel = pfad
        src_idx   = self._db_modell.setRootPath(pfad)
        proxy_idx = self._db_proxy.mapFromSource(src_idx)
        self._db_tree.setRootIndex(proxy_idx)
        self._db_pfad_feld.setText(pfad)
        self._db_status.setText(f"📂 {os.path.basename(pfad) or pfad}")

    def _db_hoch(self):
        """Ein Verzeichnis nach oben."""
        eltern = os.path.dirname(self._db_wurzel)
        if eltern and eltern != self._db_wurzel:
            self._db_set_wurzel(eltern)

    def _db_gehe_zu_pfad(self):
        pfad = self._db_pfad_feld.text().strip()
        if os.path.isdir(pfad):
            self._db_set_wurzel(pfad)
        elif os.path.isfile(pfad):
            self._db_set_wurzel(os.path.dirname(pfad))
        else:
            self._db_status.setText("⚠ Pfad nicht gefunden")

    def _db_filter_anwenden(self):
        text = self._db_filter.text().strip()
        nur_code = self._db_nur_code.isChecked()
        self._db_proxy.setze_filter(text, nur_code)

    def _db_aktueller_pfad(self) -> str:
        """Gibt den Pfad des aktuell ausgewählten Elements zurück."""
        idx = self._db_tree.currentIndex()
        if not idx.isValid():
            return ""
        src_idx = self._db_proxy.mapToSource(idx)
        return self._db_modell.filePath(src_idx)

    def _db_einzelklick(self, idx):
        pfad = self._db_aktueller_pfad()
        if pfad:
            self._db_status.setText(pfad)

    def _db_doppelklick(self, idx):
        pfad = self._db_aktueller_pfad()
        if not pfad:
            return
        if os.path.isdir(pfad):
            self._db_set_wurzel(pfad)
        elif os.path.isfile(pfad):
            self._db_datei_oeffnen(pfad)

    # ── Datei öffnen ──────────────────────────────────────────────────────
    def _db_datei_oeffnen(self, pfad: str):
        """Öffnet eine Datei als Tab im Editor (oder wechselt zu bestehendem Tab)."""
        ext = os.path.splitext(pfad)[1].lower()
        if ext in (".py", ".fcmacro", ".txt", ".md", ".cfg", ".ini", ".json"):
            self._e._tab_oeffnen(pfad)
        else:
            QtWidgets.QApplication.clipboard().setText(pfad)
            self._db_status.setText(f"📋 Pfad kopiert: {os.path.basename(pfad)}")

    def _db_ausgewaehlte_oeffnen(self):
        pfad = self._db_aktueller_pfad()
        if pfad and os.path.isfile(pfad):
            self._db_datei_oeffnen(pfad)
        else:
            self._db_status.setText("⚠ Keine Datei ausgewählt")

    def _db_pfad_kopieren(self):
        pfad = self._db_aktueller_pfad()
        if pfad:
            QtWidgets.QApplication.clipboard().setText(pfad)
            self._db_status.setText(f"📋 Kopiert: {pfad}")

    def _db_als_makro_pfad(self):
        """Setzt den aktuellen Ordner als Makro-Pfad im Manager."""
        pfad   = self._db_aktueller_pfad()
        ordner = pfad if os.path.isdir(pfad) else os.path.dirname(pfad)
        if not ordner:
            return
        try:
            from params import speichere_pfad
            speichere_pfad(ordner)
            self._db_status.setText(f"✔ Makro-Pfad gesetzt: {ordner}")
        except Exception as e:
            self._db_status.setText(f"⚠ {e}")

    def _db_kontext_menu(self, pos):
        pfad = self._db_aktueller_pfad()
        if not pfad:
            return
        menu = QtWidgets.QMenu(self._e)
        if os.path.isfile(pfad):
            menu.addAction("📂  Im Editor öffnen").triggered.connect(
                lambda: self._db_datei_oeffnen(pfad))
        if os.path.isdir(pfad):
            menu.addAction("📁  Hier navigieren").triggered.connect(
                lambda: self._db_set_wurzel(pfad))
            menu.addAction("🗂  Als Makro-Pfad setzen").triggered.connect(
                self._db_als_makro_pfad)
            menu.addAction("📄  Neue Datei hier anlegen").triggered.connect(
                lambda: self._db_neue_datei(ordner=pfad))
        menu.addSeparator()
        menu.addAction("📋  Pfad kopieren").triggered.connect(
            self._db_pfad_kopieren)
        menu.addAction("★  Als Lesezeichen").triggered.connect(
            self._db_lz_hinzufuegen)
        menu.exec(self._db_tree.viewport().mapToGlobal(pos))

    # ── Lesezeichen ───────────────────────────────────────────────────────
    def _db_lz_schluessel(self) -> str:
        return "DateiBrowserLesezeichen"

    def _db_lz_laden(self):
        try:
            from params import PREF_KEY
            import FreeCAD as App
            raw = App.ParamGet(PREF_KEY).GetString(
                self._db_lz_schluessel(), "")
            self._db_lesezeichen = json.loads(raw) if raw else []
        except Exception:
            self._db_lesezeichen = []
        if not self._db_lesezeichen:
            self._db_lesezeichen = [
                ("🏠 Home",  os.path.expanduser("~")),
                ("📜 Makros", self._makro_pfad_holen()),
            ]
        self._db_lz_combo_aktualisieren()

    def _db_lz_speichern(self):
        try:
            from params import PREF_KEY
            import FreeCAD as App
            App.ParamGet(PREF_KEY).SetString(
                self._db_lz_schluessel(),
                json.dumps(self._db_lesezeichen))
        except Exception:
            pass

    def _db_lz_combo_aktualisieren(self):
        self._db_lz_combo.clear()
        for name, _ in self._db_lesezeichen:
            self._db_lz_combo.addItem(name)

    def _db_lz_hinzufuegen(self):
        pfad   = self._db_aktueller_pfad()
        ordner = pfad if os.path.isdir(pfad) else os.path.dirname(pfad)
        if not ordner:
            ordner = self._db_wurzel
        name, ok = QtWidgets.QInputDialog.getText(
            self._e, "Lesezeichen", "Name:",
            text=os.path.basename(ordner) or ordner)
        if ok and name.strip():
            self._db_lesezeichen.append((name.strip(), ordner))
            self._db_lz_combo_aktualisieren()
            self._db_lz_speichern()
            self._db_status.setText(f"★ Lesezeichen '{name.strip()}' gespeichert")

    def _db_lz_entfernen(self):
        idx = self._db_lz_combo.currentIndex()
        if 0 <= idx < len(self._db_lesezeichen):
            name = self._db_lesezeichen[idx][0]
            del self._db_lesezeichen[idx]
            self._db_lz_combo_aktualisieren()
            self._db_lz_speichern()
            self._db_status.setText(f"✕ '{name}' entfernt")

    def _db_lz_springen(self, idx):
        if 0 <= idx < len(self._db_lesezeichen):
            self._db_set_wurzel(self._db_lesezeichen[idx][1])

    def _db_neue_datei(self, ordner: str = ""):
        """Neue .py-Datei im angezeigten Ordner anlegen und sofort im Editor öffnen."""
        if not ordner:
            ordner = self._db_wurzel
        if not os.path.isdir(ordner):
            self._db_status.setText("⚠ Kein gültiger Ordner")
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self._e, "Neue Datei anlegen", "Dateiname (ohne Endung):")
        if not (ok and name.strip()):
            return
        name = name.strip()
        if not name.lower().endswith((".py", ".fcmacro")):
            name += ".py"
        pfad = os.path.join(ordner, name)
        if os.path.exists(pfad):
            QtWidgets.QMessageBox.warning(
                self._e, "Neue Datei", f"'{name}' existiert bereits.")
            return
        try:
            with open(pfad, "w", encoding="utf-8") as f:
                f.write(f"# -*- coding: utf-8 -*-\n# {name}\n\n")
            self._db_status.setText(f"✔  '{name}' angelegt")
            self._e._tab_oeffnen(pfad)
        except Exception as e:
            self._db_status.setText(f"⚠ {e}")
