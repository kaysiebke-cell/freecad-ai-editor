# -*- coding: utf-8 -*-
import os
import shutil
import re

from qt_compat import QtWidgets, QtCore, QtGui
import theme

import FreeCADGui as Gui

from editor import MakroEditor
from params import lade_pfad, speichere_pfad, fenster_schwebend, set_fenster_schwebend


class SuchFeld(QtWidgets.QLineEdit):
    """
    Suchfeld der Makroliste mit automatischer Zwischenablage-Übernahme.
    Einzelwortsuche: mehrere Wörter werden AND-verknüpft.
    """
    def focusInEvent(self, event):
        super().focusInEvent(event)
        clip = QtWidgets.QApplication.clipboard().text().strip()
        if clip and "\n" not in clip and len(clip) < 60:
            self.setText(clip)
            self.selectAll()


class MakroLeiste(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ubuntu-Schrift + Emoji einmalig für das gesamte Widget setzen
        _f = QtGui.QFont("Ubuntu", 10)
        try:
            from main import emoji_font
            _f = emoji_font(_f)
        except Exception:
            pass
        self.setFont(_f)
        self.setStyleSheet(theme.STY_MAKRO_LEISTE_FONT)
        self._makro_pfad = lade_pfad()
        self._offene_editoren: dict = {}
        self._makro_buttons: list = []          # Cache für Buttons: (Button-Objekt, datei_name_lowered, relativer_ordner_pfad)
        self._ordner_labels: dict = {}          # Cache für Ordner-Überschriften: {rel_pfad: QLabel}

        # Debounce-Timer – verhindert Doppel-Refresh bei Speichern
        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._lade_makros)

        self._watcher = QtCore.QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._debounce_refresh)
        self._watcher.fileChanged.connect(self._debounce_refresh)
        self._baue_ui()
        self._lade_makros()

    def _baue_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        row = QtWidgets.QHBoxLayout()
        btn_mgr = QtWidgets.QPushButton("⚙  Macro-Manager öffnen")
        btn_mgr.setToolTip("FreeCAD Makro-Manager aufrufen")
        btn_mgr.setMinimumHeight(34)
        btn_mgr.clicked.connect(self._oeffne_macro_manager)
        row.addWidget(btn_mgr, stretch=1)
        btn_r = QtWidgets.QPushButton("↺")
        btn_r.setToolTip("Makroliste neu laden")
        btn_r.setMinimumHeight(34)
        btn_r.setFixedWidth(36)
        btn_r.setStyleSheet(theme.STY_REFRESH_BTN())
        btn_r.clicked.connect(self._manueller_refresh)
        row.addWidget(btn_r)
        root.addLayout(row)

        self.chk_auto = QtWidgets.QCheckBox("Auto-Refresh bei Dateiänderung")
        self.chk_auto.setChecked(True)
        self.chk_auto.setStyleSheet(theme.STY_MAKRO_CHECKBOX())
        self.chk_auto.stateChanged.connect(self._toggle_auto_refresh)
        root.addWidget(self.chk_auto)

        self.suche = SuchFeld()
        self.suche.setPlaceholderText("🔍  Makro oder Ordner suchen …")
        self.suche.setClearButtonEnabled(True)
        self.suche.setMinimumHeight(28)
        self.suche.setStyleSheet(theme.STY_MAKRO_SUCHE)
        self.suche.textChanged.connect(self._filter_makros)
        root.addWidget(self.suche)

        self.chk_inhalt = QtWidgets.QCheckBox("📄  Im Dateiinhalt suchen")
        self.chk_inhalt.setChecked(False)
        self.chk_inhalt.setToolTip(
            "Durchsucht den Inhalt aller Makro-Dateien nach dem Suchbegriff.\n"
            "Treffer: Klick öffnet die Datei direkt im Editor.")
        self.chk_inhalt.setStyleSheet(theme.STY_MAKRO_CHECKBOX())
        self.chk_inhalt.stateChanged.connect(lambda: self._filter_makros(self.suche.text()))
        root.addWidget(self.chk_inhalt)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._btn_container = QtWidgets.QWidget()
        self._btn_layout = QtWidgets.QVBoxLayout(self._btn_container)
        self._btn_layout.setContentsMargins(0, 4, 0, 0)
        self._btn_layout.setSpacing(6)
        self._btn_layout.setAlignment(QtCore.Qt.AlignTop)
        scroll.setWidget(self._btn_container)
        root.addWidget(scroll, stretch=1)

        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet(theme.STY_MAKRO_STATUS())
        root.addWidget(self.status)

        linie = QtWidgets.QFrame()
        linie.setFrameShape(QtWidgets.QFrame.HLine)
        linie.setFrameShadow(QtWidgets.QFrame.Sunken)
        root.addWidget(linie)

        root.addWidget(QtWidgets.QLabel("Speicherort der Benutzermakros:"))
        prow = QtWidgets.QHBoxLayout()
        self.pfad_feld = QtWidgets.QLineEdit(self._makro_pfad)
        self.pfad_feld.setPlaceholderText("Pfad eingeben und Enter drücken …")
        self.pfad_feld.returnPressed.connect(self._pfad_aus_feld_laden)
        prow.addWidget(self.pfad_feld)
        btn_o = QtWidgets.QPushButton("Ordner öffnen")
        btn_o.clicked.connect(self._waehle_ordner)
        prow.addWidget(btn_o)
        root.addLayout(prow)

    def _registriere_watcher(self):
        alte = self._watcher.directories() + self._watcher.files()
        if alte:
            self._watcher.removePaths(alte)
        if not self.chk_auto.isChecked():
            return
        if os.path.isdir(self._makro_pfad):
            self._watcher.addPath(self._makro_pfad)
        for pfad in self._offene_editoren:
            if os.path.isfile(pfad):
                self._watcher.addPath(pfad)

    def _toggle_auto_refresh(self):
        self._registriere_watcher()
        self.status.setText(
            "Auto-Refresh " + ("aktiv" if self.chk_auto.isChecked() else "deaktiviert"))

    def _debounce_refresh(self, _=""):
        self._refresh_timer.start()

    def _manueller_refresh(self):
        self._lade_makros()
        self.status.setText("↺ Makroliste aktualisiert")

    def _trenne_namen(self, text):
        """Trennt CamelCase, Unterstriche und Bindestriche mit Leerzeichen."""
        t = re.sub(r'[-_]+', ' ', text)
        t = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', t)
        return ' '.join(t.split())

    def _lade_makros(self):
        while self._btn_layout.count():
            c = self._btn_layout.takeAt(0)
            if c.widget():
                c.widget().deleteLater()
        
        self._makro_buttons.clear()
        self._ordner_labels.clear()

        if not os.path.isdir(self._makro_pfad):
            self.status.setText("⚠ Pfad nicht gefunden")
            return

        zaehler = 0
        for rd, dirs, files in os.walk(self._makro_pfad):
            dirs.sort()
            files.sort()
            makros = [f for f in files if f.lower().endswith((".py", ".fcmacro"))]
            if not makros:
                continue
            
            rel = os.path.relpath(rd, self._makro_pfad)
            
            # --- OPTIMIERTES ORDNER-LAYOUT ---
            if rel != ".":
                tiefe = len(rel.split(os.sep)) - 1
                indent_lbl = 6 + (tiefe * 12)
                
                ordner_name = os.path.basename(rd)
                ordner_anzeige = self._trenne_namen(ordner_name)
                
                lbl = QtWidgets.QLabel(f"📂  {ordner_anzeige}")
                lbl.setStyleSheet(theme.STY_MAKRO_ORDNER_LBL(indent_lbl))
                self._btn_layout.addWidget(lbl)
                self._ordner_labels[rel] = lbl
            
            # --- MAKRO BUTTONS ---
            for datei in makros:
                pfad  = os.path.join(rd, datei)
                name  = os.path.splitext(datei)[0]
                
                name_anzeige = self._trenne_namen(name)
                
                tiefe = 0 if rel == "." else len(rel.split(os.sep))
                indent_btn = 6 + (tiefe * 14)
                
                b = QtWidgets.QPushButton(name_anzeige)
                b.setToolTip(pfad)
                b.setMinimumHeight(26)
                b.setStyleSheet(theme.STY_MAKRO_BTN(indent_btn))
                b.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
                b.clicked.connect(lambda c=False, p=pfad, n=name: self._button_klick(p, n))
                b.customContextMenuRequested.connect(
                    lambda pos, btn=b, p=pfad, n=name: self._zeige_kontext_menu(btn, p, n))

                self._btn_layout.addWidget(b)
                self._makro_buttons.append((b, name.lower(), rel.lower(), pfad))
                zaehler += 1

        self.status.setText(f"{zaehler} Makro(s) geladen")
        if self.pfad_feld.text() != self._makro_pfad:
            self.pfad_feld.setText(self._makro_pfad)
        self._registriere_watcher()
        if self.suche.text():
            self._filter_makros(self.suche.text())

    def _button_klick(self, pfad: str, name: str):
        """Öffnet Datei im Editor (Inhalts-Modus) oder führt sie aus (Normal-Modus)."""
        if self.chk_inhalt.isChecked():
            self._hole_editor(pfad)
        else:
            self._fuehre_aus(pfad, name)

    def _filter_makros(self, text):
        """
        Filtert nach Dateinamen UND Ordnernamen.
        Mit Checkbox 'Im Dateiinhalt suchen' zusätzlich nach Dateiinhalt.
        """
        woerter = text.lower().split()
        inhalt_modus = self.chk_inhalt.isChecked() and len(text.strip()) >= 2

        if not woerter:
            for btn, _, _, pfad in self._makro_buttons:
                btn.setVisible(True)
                btn.setToolTip(pfad)
            for lbl in self._ordner_labels.values():
                lbl.setVisible(True)
            return

        sichtbare_ordner = set()
        for btn, name_low, rel_low, pfad in self._makro_buttons:
            datei_match  = all(w in name_low for w in woerter)
            ordner_match = all(w in rel_low  for w in woerter)

            inhalt_match   = False
            treffer_zeile  = ""
            if inhalt_modus and not datei_match:
                try:
                    with open(pfad, "r", encoding="utf-8", errors="ignore") as f:
                        for nr, zeile in enumerate(f, 1):
                            if all(w in zeile.lower() for w in woerter):
                                inhalt_match  = True
                                treffer_zeile = f"Zeile {nr}: {zeile.strip()[:80]}"
                                break
                except Exception:
                    pass

            ist_sichtbar = datei_match or ordner_match or inhalt_match
            btn.setVisible(ist_sichtbar)

            if inhalt_match and treffer_zeile:
                btn.setToolTip(f"{pfad}\n\n📄 Treffer:\n  {treffer_zeile}")
            else:
                btn.setToolTip(pfad)

            if ist_sichtbar and rel_low != ".":
                sichtbare_ordner.add(rel_low)

        anzahl = sum(1 for btn, *_ in self._makro_buttons if btn.isVisible())
        if inhalt_modus:
            self.status.setText(
                f"{anzahl} Treffer  –  Klick öffnet Datei im Editor")

        for rel_pfad, lbl in self._ordner_labels.items():
            rel_low = rel_pfad.lower()
            ordner_selbst_match = all(w in rel_low for w in woerter)
            lbl.setVisible(ordner_selbst_match or rel_low in sichtbare_ordner)

    def _zeige_kontext_menu(self, btn, pfad, name):
        menu = QtWidgets.QMenu(self)
        a_ed     = menu.addAction("✎  Im Makro-Editor öffnen")
        menu.addSeparator()
        a_unter  = menu.addAction("📄  Speichern unter …")
        a_rename = menu.addAction("✏  Datei umbenennen")
        a_reload = menu.addAction("↺  Inhalt neu laden (Reload)")
        menu.addSeparator()
        a_del_f  = menu.addAction("🗑  Datei löschen …")
        ordner   = os.path.dirname(pfad)
        a_del_d  = None
        if os.path.normpath(ordner) != os.path.normpath(self._makro_pfad):
            a_del_d = menu.addAction("📁🗑  Ordner löschen …")
        aktion = menu.exec(btn.mapToGlobal(QtCore.QPoint(btn.width(), 0)))
        if aktion is None:
            return
        if   aktion == a_ed:     self._hole_editor(pfad)
        elif aktion == a_unter:  self._speichere_unter(pfad, name)
        elif aktion == a_rename: self._umbenennen(pfad, name)
        elif aktion == a_reload:
            if pfad in self._offene_editoren:
                self._offene_editoren[pfad].neu_laden()
            self._lade_makros()
            self.status.setText(f"↺  '{name}' neu geladen")
        elif aktion == a_del_f:  self._loesche_datei(pfad, name)
        elif a_del_d and aktion == a_del_d:
            self._loesche_ordner(ordner)

    def _hole_editor(self, pfad) -> MakroEditor:
        if pfad in self._offene_editoren and not self._offene_editoren[pfad].isHidden():
            ed = self._offene_editoren[pfad]
            ed.raise_()
            ed.activateWindow()
            return ed
        ed = MakroEditor(pfad, Gui.getMainWindow())
        ed.destroyed.connect(lambda obj=None, p=pfad: self._editor_geschlossen(p))
        ed.such_in_dateien.connect(lambda text, e=ed: self._dateisuche_aus_editor(text, e))
        self._offene_editoren[pfad] = ed
        if self.chk_auto.isChecked() and os.path.isfile(pfad):
            self._watcher.addPath(pfad)
        if fenster_schwebend():
            self._zeige_als_fenster(ed)
        else:
            self._zeige_als_dock(ed, pfad)
        return ed

    @staticmethod
    def _freecad_inhalte(verstecken: bool):
        """Blendet FreeCAD-Zentralbereich, Toolbars und Dock-Panels aus/ein."""
        mw = Gui.getMainWindow()
        # Zentrales MDI-Widget (3D-Ansicht)
        cw = mw.centralWidget()
        if cw:
            cw.setVisible(not verstecken)
        # Werkzeugleisten – Workbench-Leiste bleibt immer sichtbar
        for tb in mw.findChildren(QtWidgets.QToolBar):
            # Workbench-Leiste erkennen: enthält eine ComboBox (Workbench-Auswahl)
            # oder heißt "Workbench"
            ist_wb_leiste = (
                tb.objectName() == "Workbench"
                or bool(tb.findChildren(QtWidgets.QComboBox))
            )
            if not ist_wb_leiste:
                tb.setVisible(not verstecken)
        # Alle Dock-Panels außer dem Editor selbst ausblenden
        for dock in mw.findChildren(QtWidgets.QDockWidget):
            if not dock.objectName().startswith("EditorDock_"):
                dock.setVisible(not verstecken)

    def _zeige_als_fenster(self, ed: MakroEditor):
        """Eigenständiges Fenster – kein Andocken möglich."""
        # FreeCAD-Inhalte wieder einblenden
        self._freecad_inhalte(verstecken=False)
        if hasattr(ed, "_freecad_dock") and ed._freecad_dock:
            ed._freecad_dock.setWidget(None)
            ed._freecad_dock.deleteLater()
            ed._freecad_dock = None
        ed.setParent(None)
        ed.setWindowFlags(QtCore.Qt.Window)
        ed.show()
        ed.raise_()
        ed.activateWindow()

    def _zeige_als_dock(self, ed: MakroEditor, pfad: str):
        """Editor als Dock in FreeCAD – FreeCAD-Inhalte werden ausgeblendet."""
        mw = Gui.getMainWindow()
        titel = os.path.basename(pfad)
        ed.setWindowFlags(QtCore.Qt.Widget)
        dock = QtWidgets.QDockWidget(titel, mw)
        dock.setObjectName(f"EditorDock_{pfad}")
        dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea  |
            QtCore.Qt.RightDockWidgetArea |
            QtCore.Qt.TopDockWidgetArea   |
            QtCore.Qt.BottomDockWidgetArea)
        dock.setWidget(ed)
        mw.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        ed._freecad_dock = dock
        # FreeCAD-Inhalte ausblenden → Editor bekommt den vollen Platz
        self._freecad_inhalte(verstecken=True)
        ed.show()
        dock.show()
        dock.raise_()

        # Beim Schließen des Docks FreeCAD-Inhalte wiederherstellen
        dock.visibilityChanged.connect(
            lambda vis: self._freecad_inhalte(verstecken=False) if not vis else None)

    def wechsle_editor_modus(self, ed: MakroEditor, andockbar: bool):
        """Geöffneten Editor live zwischen den Modi umschalten."""
        set_fenster_schwebend(not andockbar)
        pfad = getattr(ed, "_pfad", "") or ""
        if andockbar:
            self._zeige_als_dock(ed, pfad)
        else:
            self._zeige_als_fenster(ed)

    def _dateisuche_aus_editor(self, suchtext: str, quell_editor=None):
        """Fallback-Suche vom Editor: durchsucht alle Dateien im Makro-Pfad direkt."""
        suchtext = suchtext.strip()
        if not suchtext:
            return
        if not os.path.isdir(self._makro_pfad):
            self.status.setText("⚠ Makro-Pfad nicht gefunden")
            return

        mehrzeilig = "\n" in suchtext
        nadel = suchtext.lower()
        treffer = []

        for rd, dirs, files in os.walk(self._makro_pfad):
            dirs.sort()
            for datei in sorted(files):
                if not datei.lower().endswith((".py", ".fcmacro")):
                    continue
                pfad = os.path.join(rd, datei)
                try:
                    with open(pfad, "r", encoding="utf-8", errors="ignore") as f:
                        inhalt = f.read()
                    inhalt_low = inhalt.lower()

                    if mehrzeilig:
                        # Ganzen Block als Substring im Dateiinhalt suchen
                        pos = inhalt_low.find(nadel)
                        if pos >= 0:
                            nr = inhalt[:pos].count("\n") + 1
                            treffer.append((pfad, nr, suchtext.splitlines()[0].strip()))
                    else:
                        # Einzeilig: erste Zeile mit dem Treffer finden
                        for nr, zeile in enumerate(inhalt.splitlines(), 1):
                            if nadel in zeile.lower():
                                treffer.append((pfad, nr, zeile.strip()))
                                break
                except Exception:
                    pass

        if not treffer:
            self.status.setText("❌ Kein Treffer in allen Makros")
            return

        if len(treffer) == 1:
            pfad, nr, _ = treffer[0]
            name = os.path.basename(pfad)

            # Datei als Tab im selben Editor öffnen — kein neues Fenster
            if quell_editor is not None and hasattr(quell_editor, "_tab_oeffnen"):
                ziel_ed = quell_editor
                ziel_ed._tab_oeffnen(pfad)
                ziel_ed.raise_()
                ziel_ed.activateWindow()
            else:
                ziel_ed = self._hole_editor(pfad)

            def _markiere(ed=ziel_ed, suchtext=suchtext, nr=nr, name=name):
                if hasattr(ed, "such_und_markiere") and ed.such_und_markiere(suchtext):
                    self.status.setText(f"📍 Gefunden: {name} – Zeile {nr}")
                elif hasattr(ed, "gehe_zu_zeile"):
                    ed.gehe_zu_zeile(nr)
                    self.status.setText(f"📍 Zeile {nr} in {name}")
            QtCore.QTimer.singleShot(80, _markiere)
        else:
            self.suche.setText(suchtext.splitlines()[0][:60])
            self.chk_inhalt.setChecked(True)
            self.status.setText(f"🔍 {len(treffer)} Treffer – Datei anklicken zum Öffnen")

    def _editor_geschlossen(self, pfad: str):
        self._offene_editoren.pop(pfad, None)
        self._watcher.removePath(pfad)

    def closeEvent(self, event):
        """Watcher + Timer sauber freigeben wenn Dock geschlossen wird."""
        self._refresh_timer.stop()
        alte = self._watcher.directories() + self._watcher.files()
        if alte:
            self._watcher.removePaths(alte)
        # Offene Editoren nicht schließen – nur Referenzen vergessen
        self._offene_editoren.clear()
        super().closeEvent(event)

    def _speichere_unter(self, pfad, name):
        ziel, _ = QtWidgets.QFileDialog.getSaveFileName(
            Gui.getMainWindow(), "Speichern unter", pfad,
            "Python-Dateien (*.py);;FreeCAD-Makros (*.FCMacro);;Alle (*)")
        if not ziel:
            return
        try:
            shutil.copy2(pfad, ziel)
            self.status.setText(f"✔  Gespeichert als: {os.path.basename(ziel)}")
            self._lade_makros()
        except Exception as e:
            from fehler import uebersetze_fehler
            QtWidgets.QMessageBox.critical(self, "Fehler", uebersetze_fehler(e))

    def _umbenennen(self, pfad, name):
        ext = os.path.splitext(pfad)[1]
        neu, ok = QtWidgets.QInputDialog.getText(
            self, "Umbenennen", "Neuer Name:", text=name)
        if not (ok and neu.strip()):
            return
        neu = neu.strip()
        if not neu.lower().endswith(ext.lower()):
            neu += ext
        ziel = os.path.join(os.path.dirname(pfad), neu)
        if os.path.exists(ziel):
            QtWidgets.QMessageBox.warning(
                self, "Umbenennen", f"'{neu}' existiert bereits.")
            return
        try:
            if pfad in self._offene_editoren:
                self._offene_editoren[pfad].close()
            os.rename(pfad, ziel)
            self.status.setText(f"✔  Umbenannt → {neu}")
            self._lade_makros()
        except Exception as e:
            from fehler import uebersetze_fehler
            QtWidgets.QMessageBox.critical(self, "Fehler", uebersetze_fehler(e))

    def _loesche_datei(self, pfad, name):
        antwort = QtWidgets.QMessageBox.warning(
            self, "Datei löschen",
            f"'{name}' wirklich unwiderruflich löschen?\n\n{pfad}",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if antwort != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            if pfad in self._offene_editoren:
                self._offene_editoren[pfad].close()
            os.remove(pfad)
            self.status.setText(f"🗑  '{name}' gelöscht")
            self._lade_makros()
        except Exception as e:
            from fehler import uebersetze_fehler
            QtWidgets.QMessageBox.critical(self, "Fehler beim Löschen", uebersetze_fehler(e))

    def _loesche_ordner(self, ordner):
        rel = os.path.relpath(ordner, self._makro_pfad)
        if os.path.normpath(ordner) == os.path.normpath(self._makro_pfad):
            QtWidgets.QMessageBox.warning(
                self, "Löschen abgebrochen",
                "Das Makro-Wurzelverzeichnis kann nicht gelöscht werden.")
            return
        inhalt = []
        for rd, dirs, files in os.walk(ordner):
            inhalt.extend(files)
        anzahl = len(inhalt)
        antwort = QtWidgets.QMessageBox.warning(
            self, "Ordner löschen",
            f"Ordner '{rel}' wirklich unwiderruflich löschen?\n"
            f"Enthält {anzahl} Datei(en).\n\n{ordner}",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if antwort != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            for pfad in list(self._offene_editoren):
                if pfad.startswith(ordner + os.sep) or pfad.startswith(ordner + "/"):
                    self._offene_editoren[pfad].close()
            shutil.rmtree(ordner)
            self.status.setText(f"🗑  Ordner '{rel}' gelöscht")
            self._lade_makros()
        except Exception as e:
            from fehler import uebersetze_fehler
            QtWidgets.QMessageBox.critical(self, "Fehler beim Löschen", uebersetze_fehler(e))

    def _fuehre_aus(self, pfad, name):
        try:
            try:
                with open(pfad, "r", encoding="utf-8") as f:
                    code = f.read()
            except UnicodeDecodeError:
                with open(pfad, "r", encoding="latin-1") as f:
                    code = f.read()
            namespace = {
                "__file__": pfad,
                "__name__": "__main__",
                "__builtins__": __builtins__
            }
            exec(compile(code, pfad, "exec"), namespace)
            self.status.setText(f"✔ {name} ausgeführt")
        except Exception as e:
            import traceback as _tb
            from fehler import uebersetze_fehler
            fehlertext = _tb.format_exc()
            # Fehler-Panel im zugehörigen Editor befüllen (falls geöffnet)
            ed = self._offene_editoren.get(pfad)
            if ed is not None and hasattr(ed, "fehler_anzeigen"):
                ed.fehler_anzeigen(fehlertext)
            else:
                QtWidgets.QMessageBox.critical(self, "Fehler", uebersetze_fehler(e))

    def _oeffne_macro_manager(self):
        Gui.runCommand("Std_DlgMacroExecute", 0)

    def _waehle_ordner(self):
        mw = Gui.getMainWindow()
        ordner = QtWidgets.QFileDialog.getExistingDirectory(
            mw, "Makro-Ordner wählen", self._makro_pfad,
            QtWidgets.QFileDialog.ShowDirsOnly)
        if ordner:
            ordner = os.path.normpath(ordner)
            self._makro_pfad = ordner
            speichere_pfad(ordner)
            self.pfad_feld.setText(ordner)
            self._lade_makros()
            self.status.setText(f"✔ Neuer Pfad: {ordner}")
        else:
            self.status.setText("⚠ Kein Ordner gewählt")

    def _pfad_aus_feld_laden(self):
        pfad = os.path.normpath(self.pfad_feld.text().strip())
        if os.path.isdir(pfad):
            self._makro_pfad = pfad
            speichere_pfad(pfad)
            self._lade_makros()
            self.status.setText(f"✔ Pfad gesetzt: {pfad}")
        else:
            self.status.setText("⚠ Ungültiger Pfad")
            _err_col = self.pfad_feld.palette().color(
                QtGui.QPalette.Active, QtGui.QPalette.BrightText
            ).name()
            self.pfad_feld.setStyleSheet(
                f"border:1px solid {_err_col};"
            )
            QtCore.QTimer.singleShot(
                2000, lambda: self.pfad_feld.setStyleSheet(""))
