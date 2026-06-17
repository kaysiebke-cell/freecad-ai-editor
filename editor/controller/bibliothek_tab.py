# -*- coding: utf-8 -*-
"""
bibliothek_tab.py
──────────────────
Bibliotheks-Tab für den MakroEditor.

Zwei Modi:
  OHNE KI — Nutzer sucht, wählt und führt getestete Makros direkt aus
  MIT KI  — KI kennt die Bibliothek und baut auf vorhandenen Makros auf

UI-Struktur:
  ┌─────────────────────────────────────────┐
  │  🔍 Suchfeld          [+ Neu] [💾 Aktuell speichern] │
  ├─────────────────────────────────────────┤
  │  Liste (Name · KI-Icon · Datum)         │
  ├─────────────────────────────────────────┤
  │  📋 Beschreibung + Tags + Code-Vorschau │
  ├─────────────────────────────────────────┤
  │  [▶ Ausführen]  [📥 In Editor laden]  [🗑 Löschen] │
  └─────────────────────────────────────────┘
"""

import os
import sys

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


class BibliothekTabMixin:
    """Mixin: fügt dem MakroEditor den '📚 Bibliothek'-Tab hinzu."""

    def _baue_bibliothek_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Info-Banner ───────────────────────────────────────────────────
        _bib_verstecke = []
        from snippet_controller import SnippetController as _TM
        layout.addWidget(_TM._baue_info_banner(
            "📚 Was ist die Bibliothek?",
            "Getestete FreeCAD-Makros speichern & direkt ausführen.<br>"
            "① Suchen  ② Auswählen  ③ Ausführen oder In Editor laden<br>"
            "Speichern: Editor-Code → 💾 In Bibliothek",
            _bib_verstecke,
        ))

        # ── Suchzeile + Buttons ───────────────────────────────────────────
        such_zeile = QtWidgets.QHBoxLayout()
        self._bib_suche = QtWidgets.QLineEdit()
        self._bib_suche.setPlaceholderText("🔍 Suchen … Name, Beschreibung, Tag")
        self._bib_suche.setClearButtonEnabled(True)
        self._bib_suche.textChanged.connect(self._bib_liste_aktualisieren)
        such_zeile.addWidget(self._bib_suche)

        btn_neu = QtWidgets.QPushButton("➕")
        btn_neu.setFixedWidth(30)
        btn_neu.setToolTip("Neuen leeren Eintrag anlegen")
        btn_neu.clicked.connect(self._bib_neu_dialog)
        such_zeile.addWidget(btn_neu)

        bib_widget = QtWidgets.QWidget()
        bib_widget.setLayout(such_zeile)
        _bib_verstecke.append(bib_widget)
        layout.addWidget(bib_widget)

        # ── Liste ─────────────────────────────────────────────────────────
        self._bib_liste = QtWidgets.QListWidget()
        self._bib_liste.setAlternatingRowColors(True)
        self._bib_liste.setMinimumHeight(120)
        self._bib_liste.setFont(QtGui.QFont("Courier New", 9))
        self._bib_liste.currentRowChanged.connect(self._bib_vorschau_aktualisieren)
        _bib_verstecke.append(self._bib_liste)
        layout.addWidget(self._bib_liste)

        # ── Vorschau ──────────────────────────────────────────────────────
        vorschau_widget = QtWidgets.QWidget()
        vl = QtWidgets.QVBoxLayout(vorschau_widget)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(2)

        self._bib_beschr_lbl = QtWidgets.QLabel("")
        self._bib_beschr_lbl.setWordWrap(True)
        self._bib_beschr_lbl.setStyleSheet(
            theme.STY_LABEL_SM(schrift.pt(schrift.STUFE_SM)))
        vl.addWidget(self._bib_beschr_lbl)

        self._bib_code_vorschau = QtWidgets.QPlainTextEdit()
        self._bib_code_vorschau.setReadOnly(True)
        self._bib_code_vorschau.setFont(QtGui.QFont("Courier New", 9))
        self._bib_code_vorschau.setMaximumHeight(130)
        self._bib_code_vorschau.setPlaceholderText("Code-Vorschau …")
        vl.addWidget(self._bib_code_vorschau)

        _bib_verstecke.append(vorschau_widget)
        layout.addWidget(vorschau_widget)

        # ── Aktions-Buttons ───────────────────────────────────────────────
        btn_zeile = QtWidgets.QHBoxLayout()

        self._bib_btn_ausfuehren = QtWidgets.QPushButton("▶ Ausführen")
        self._bib_btn_ausfuehren.setMinimumHeight(28)
        self._bib_btn_ausfuehren.setStyleSheet(theme.STY_BOLD_BTN)
        self._bib_btn_ausfuehren.setEnabled(False)
        self._bib_btn_ausfuehren.clicked.connect(self._bib_ausfuehren)
        btn_zeile.addWidget(self._bib_btn_ausfuehren)

        self._bib_btn_laden = QtWidgets.QPushButton("📥 In Editor")
        self._bib_btn_laden.setMinimumHeight(28)
        self._bib_btn_laden.setToolTip("Code in den Editor laden")
        self._bib_btn_laden.setEnabled(False)
        self._bib_btn_laden.clicked.connect(self._bib_in_editor_laden)
        btn_zeile.addWidget(self._bib_btn_laden)

        self._bib_btn_loeschen = QtWidgets.QPushButton("🗑")
        self._bib_btn_loeschen.setFixedWidth(34)
        self._bib_btn_loeschen.setMinimumHeight(28)
        self._bib_btn_loeschen.setToolTip("Eintrag löschen")
        self._bib_btn_loeschen.setEnabled(False)
        self._bib_btn_loeschen.clicked.connect(self._bib_loeschen)
        btn_zeile.addWidget(self._bib_btn_loeschen)

        btn_widget = QtWidgets.QWidget()
        btn_widget.setLayout(btn_zeile)
        _bib_verstecke.append(btn_widget)
        layout.addWidget(btn_widget)

        # ── Statuszeile ───────────────────────────────────────────────────
        self._bib_status = QtWidgets.QLabel("")
        self._bib_status.setStyleSheet(
            theme.STY_LABEL_SM(schrift.pt(schrift.STUFE_SM)))
        _bib_verstecke.append(self._bib_status)
        layout.addWidget(self._bib_status)

        layout.addStretch()

        # Beim Start laden
        QtCore.QTimer.singleShot(200, self._bib_liste_aktualisieren)
        return w

    # ── Daten-Zugriff ─────────────────────────────────────────────────────

    def _bib_laden(self) -> list[dict]:
        try:
            from bibliothek import laden
            return laden()
        except ImportError:
            return []

    def _bib_aktueller_eintrag(self) -> dict | None:
        row = self._bib_liste.currentRow()
        if row < 0:
            return None
        item = self._bib_liste.item(row)
        if item is None:
            return None
        return item.data(QtCore.Qt.UserRole)

    # ── Liste aktualisieren ───────────────────────────────────────────────

    def _bib_liste_aktualisieren(self):
        try:
            from bibliothek import suchen
            suchbegriff = self._bib_suche.text()
            eintraege   = suchen(suchbegriff)
        except ImportError:
            eintraege = []

        self._bib_liste.clear()
        for e in eintraege:
            ki_icon  = " 🤖" if e.get("ki_generiert") else ""
            datum    = e.get("datum", "")[:10]
            anzeige  = f"{e['name']}{ki_icon}  —  {datum}"
            item     = QtWidgets.QListWidgetItem(anzeige)
            item.setData(QtCore.Qt.UserRole, e)
            self._bib_liste.addItem(item)

        anzahl = len(eintraege)
        self._bib_status.setText(
            f"{anzahl} Eintrag/Einträge" if anzahl else "Bibliothek ist leer — speichere dein erstes Makro!")
        self._bib_btn_ausfuehren.setEnabled(False)
        self._bib_btn_laden.setEnabled(False)
        self._bib_btn_loeschen.setEnabled(False)
        self._bib_beschr_lbl.setText("")
        self._bib_code_vorschau.clear()

    # ── Vorschau ──────────────────────────────────────────────────────────

    def _bib_vorschau_aktualisieren(self, row: int):
        e = self._bib_aktueller_eintrag()
        if e is None:
            self._bib_btn_ausfuehren.setEnabled(False)
            self._bib_btn_laden.setEnabled(False)
            self._bib_btn_loeschen.setEnabled(False)
            return

        tags = ", ".join(e.get("tags", []))
        ki   = " · 🤖 KI-generiert" if e.get("ki_generiert") else ""
        ausg = e.get("ausfuehrungen", 0)
        info = (
            f"<b>{e['name']}</b>{ki}<br>"
            f"{e.get('beschreibung', '')}<br>"
            f"<small>Tags: {tags or '–'}  ·  "
            f"Ausgeführt: {ausg}x  ·  {e.get('datum', '')}</small>"
        )
        self._bib_beschr_lbl.setText(info)
        self._bib_code_vorschau.setPlainText(e.get("code", ""))
        self._bib_btn_ausfuehren.setEnabled(True)
        self._bib_btn_laden.setEnabled(True)
        self._bib_btn_loeschen.setEnabled(True)

    # ── Ausführen ─────────────────────────────────────────────────────────

    def _bib_ausfuehren(self):
        e = self._bib_aktueller_eintrag()
        if e is None:
            return
        code = e.get("code", "").strip()
        if not code:
            return

        self._bib_status.setText("⏳ Wird ausgeführt …")
        QtWidgets.QApplication.processEvents()

        try:
            # Sandbox-Mechanismus aus fehler_panel wiederverwenden
            from fehler_panel import FehlerPanel
            ergebnis = FehlerPanel._execute_in_sandbox(code)
            if ergebnis.get("success"):
                self._bib_status.setText(f"✅ '{e['name']}' erfolgreich ausgeführt")
                # Zähler erhöhen
                try:
                    from bibliothek import ausfuehrung_zaehlen
                    ausfuehrung_zaehlen(e["name"])
                    self._bib_liste_aktualisieren()
                except Exception:
                    pass
            else:
                fehler = ergebnis.get("error", "Unbekannter Fehler")
                self._bib_status.setText(f"❌ Fehler: {fehler[:80]}")
        except Exception as ex:
            # Direkter Fallback ohne Sandbox
            try:
                import FreeCAD  # noqa: F401
                exec(compile(code, "<bibliothek>", "exec"), {})  # noqa: S102
                self._bib_status.setText(f"✅ '{e['name']}' ausgeführt")
            except Exception as ex2:
                self._bib_status.setText(f"❌ {ex2}")

    # ── In Editor laden ───────────────────────────────────────────────────

    def _bib_in_editor_laden(self):
        e = self._bib_aktueller_eintrag()
        if e is None:
            return
        code = e.get("code", "")
        # In aktiven Editor-Tab laden
        try:
            editor = self._aktiver_editor()
            if editor:
                editor.setPlainText(code)
                self._bib_status.setText(
                    f"📥 '{e['name']}' in Editor geladen")
            else:
                # Neuen Tab öffnen
                self._neue_datei()
                editor = self._aktiver_editor()
                if editor:
                    editor.setPlainText(code)
        except Exception as ex:
            self._bib_status.setText(f"❌ Laden fehlgeschlagen: {ex}")

    # ── Löschen ───────────────────────────────────────────────────────────

    def _bib_loeschen(self):
        e = self._bib_aktueller_eintrag()
        if e is None:
            return
        antwort = QtWidgets.QMessageBox.question(
            self,
            "Eintrag löschen",
            f"'{e['name']}' aus der Bibliothek löschen?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if antwort != QtWidgets.QMessageBox.Yes:
            return
        try:
            from bibliothek import eintrag_loeschen
            if eintrag_loeschen(e["name"]):
                self._bib_status.setText(f"🗑 '{e['name']}' gelöscht")
                self._bib_liste_aktualisieren()
        except Exception as ex:
            self._bib_status.setText(f"❌ Fehler: {ex}")

    # ── Neu-Dialog ────────────────────────────────────────────────────────

    def _bib_neu_dialog(self):
        """Dialog zum manuellen Anlegen eines neuen Bibliotheks-Eintrags."""
        self._bib_speichern_dialog(
            code=self._get_editor_code(),
            ki_generiert=False,
        )

    def _bib_speichern_dialog(self, code: str = "", ki_generiert: bool = False):
        """Zeigt den Speichern-Dialog und legt den Eintrag an."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("💾 In Bibliothek speichern")
        dlg.setMinimumWidth(440)

        vl = QtWidgets.QVBoxLayout(dlg)
        vl.setSpacing(8)

        form = QtWidgets.QFormLayout()

        name_feld = QtWidgets.QLineEdit()
        name_feld.setPlaceholderText("z.B. 'Box mit Bohrung 50x30mm'")
        form.addRow("Name:", name_feld)

        beschr_feld = QtWidgets.QLineEdit()
        beschr_feld.setPlaceholderText("Kurze Beschreibung was das Makro macht")
        form.addRow("Beschreibung:", beschr_feld)

        tags_feld = QtWidgets.QLineEdit()
        tags_feld.setPlaceholderText("Box, Boolean, PartDesign  (kommagetrennt)")
        form.addRow("Tags:", tags_feld)

        ki_cb = QtWidgets.QCheckBox("Von KI generiert")
        ki_cb.setChecked(ki_generiert)
        form.addRow("", ki_cb)

        code_area = QtWidgets.QPlainTextEdit()
        code_area.setFont(QtGui.QFont("Courier New", 9))
        code_area.setMinimumHeight(150)
        code_area.setPlainText(code)
        form.addRow("Code:", code_area)

        vl.addLayout(form)

        status_lbl = QtWidgets.QLabel("")
        status_lbl.setStyleSheet(
            theme.STY_LABEL_SM_NP(schrift.pt(schrift.STUFE_SM)))
        vl.addWidget(status_lbl)

        btn_zeile = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("💾 Speichern")
        btn_ok.setMinimumHeight(30)
        btn_ok.setStyleSheet(theme.STY_BOLD_BTN)
        btn_ab = QtWidgets.QPushButton("Abbrechen")
        btn_zeile.addWidget(btn_ok)
        btn_zeile.addWidget(btn_ab)
        vl.addLayout(btn_zeile)

        def speichern():
            name = name_feld.text().strip()
            if not name:
                status_lbl.setStyleSheet(f"color:{theme.farbe_fehler(dlg)};")
                status_lbl.setText("⚠ Bitte einen Namen eingeben")
                return
            code_text = code_area.toPlainText().strip()
            if not code_text:
                status_lbl.setStyleSheet(f"color:{theme.farbe_fehler(dlg)};")
                status_lbl.setText("⚠ Code darf nicht leer sein")
                return
            tags = [t.strip() for t in tags_feld.text().split(",") if t.strip()]
            try:
                from bibliothek import eintrag_hinzufuegen
                eintrag_hinzufuegen(
                    name=name,
                    code=code_text,
                    beschreibung=beschr_feld.text().strip(),
                    tags=tags,
                    ki_generiert=ki_cb.isChecked(),
                )
                status_lbl.setStyleSheet(f"color:{theme.farbe_ok(dlg)};")
                status_lbl.setText(f"✅ '{name}' gespeichert!")
                self._bib_liste_aktualisieren()
                QtCore.QTimer.singleShot(800, dlg.accept)
            except Exception as ex:
                status_lbl.setStyleSheet(f"color:{theme.farbe_fehler(dlg)};")
                status_lbl.setText(f"❌ Fehler: {ex}")

        btn_ok.clicked.connect(speichern)
        btn_ab.clicked.connect(dlg.reject)
        # Enter-Taste im Name-Feld → direkt speichern
        name_feld.returnPressed.connect(speichern)
        dlg.exec_()

    # ── Hilfsmethoden ─────────────────────────────────────────────────────

    def _get_editor_code(self) -> str:
        """Gibt den aktuellen Editor-Inhalt zurück."""
        try:
            editor = self._aktiver_editor()
            if editor:
                return editor.toPlainText()
        except Exception:
            pass
        return ""

    def _aktiver_editor(self):
        """Gibt das aktive QPlainTextEdit zurück."""
        try:
            idx = self._editor_tab_widget.currentIndex()
            if 0 <= idx < len(self._tabs):
                return self._tabs[idx]["editor"]
        except Exception:
            pass
        return None

    # ── Öffentliche Methode: aus Editor heraus speichern ─────────────────

    def bibliothek_speichern(self, code: str = "", ki_generiert: bool = False):
        """Wird vom Editor-Toolbar-Button '💾 In Bibliothek' aufgerufen."""
        if not code:
            code = self._get_editor_code()
        self._bib_speichern_dialog(code=code, ki_generiert=ki_generiert)
