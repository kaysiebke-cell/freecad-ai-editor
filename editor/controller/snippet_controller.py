# -*- coding: utf-8 -*-
"""
snippet_controller.py
─────────────────────
Snippets – linke Tab-Inhalte:
  - _baue_snippet_tab()   – Snippet-Browser (Lokal + Online GitHub)
  - _baue_hints_tab()     – FreeCAD API-Kurzreferenz
  - _baue_fehler_tab()    – Fehler-Übersetzer-Tab (linke Leiste)
  - _baue_fehler_panel()  – Fehler-Übersetzer-Panel (unterer Rand)

Änderungen gegenüber Vorgänger:
  [NEU] Lokal/Online-Umschalter im Snippet-Tab
  [NEU] OnlineMakroWorker  – asynchrone GitHub-Liste
  [NEU] OnlinePreviewWorker – blockierungsfreie Vorschau für Online-Makros
  [NEU] Benutzerdefinierte Snippets mit JSON-Persistenz
  [NEU] 'Markierung als Snippet speichern'-Button
  [FIX] self._snip_filter statt self._hint_suche (war doppelt vergeben)
"""

import os

from core.qt_compat import QtWidgets, QtCore, QtGui
from core import theme
from core import schrift

from data.freecad_data import SNIPPETS, FC_API_HINTS
from editor.controller.snippet_widgets import SnipCommandEdit, OnlineMakroWorker, OnlinePreviewWorker, _BlauBanner



class Snippets:
    """Snippet/Hints/Fehler-Tab-Controller.

    Greift über self._e auf den Host zurück für:
      _editor        (aktueller CodeEditor)
      _set_status()
      _ki_fehler_erklaeren(), _on_self_correction_needed()  (vom KI-Controller)
    """

    def __init__(self, editor):
        self._e = editor

    # ── Wiederverwendbarer Info-Banner ────────────────────────────────────
    @staticmethod
    def _baue_info_banner(titel: str, html_text: str,
                          verstecke_widgets: list = None) -> QtWidgets.QWidget:
        """
        Aufklappbarer Info-Banner.
        Wenn aufgeklappt → verstecke_widgets werden ausgeblendet (Fenster bleibt gleich groß).
        Wenn zugeklappt  → verstecke_widgets werden wieder eingeblendet.
        verstecke_widgets wird NACH dem Erstellen befüllt (Liste per Referenz).
        """
        container = _BlauBanner()
        container.setObjectName("infoBanner")
        vbox = QtWidgets.QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        btn = QtWidgets.QPushButton(f"▶  {titel}")
        btn.setCheckable(True)
        btn.setMinimumHeight(28)
        btn.setObjectName("_bannerBtn")
        btn.setStyleSheet(theme.STY_BANNER_BTN(schrift.pt(schrift.STUFE_LG)))
        vbox.addWidget(btn)

        body = QtWidgets.QTextBrowser()
        body.setHtml(html_text)
        body.setReadOnly(True)
        body.setFrameShape(QtWidgets.QFrame.NoFrame)
        body.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        body.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        body.setObjectName("_bannerBody")
        body.setStyleSheet(theme.STY_BANNER_BODY)
        body.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        body.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)
        body.hide()
        vbox.addWidget(body)

        def _toggle(checked):
            body.setVisible(checked)
            btn.setText(
                f"▼  {titel}  –  Zuklappen" if checked
                else f"▶  {titel}")
            targets = verstecke_widgets or []
            for w in targets:
                w.setVisible(not checked)

        btn.toggled.connect(_toggle)
        return container

    # ══ Snippet-Tab ════════════════════════════════════════════════════════
    def _baue_snippet_tab(self) -> QtWidgets.QWidget:
        """Snippet-Browser mit Lokal- und Online-Modus."""
        w      = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Interne Zustandsdaten
        self._online_makro_links  = {}
        self._user_snippets       = {}
        self._snip_worker         = None
        self._preview_worker      = None
        # Preview-Cache: verhindert wiederholte GitHub-Downloads (max. 50 Einträge)
        self._online_preview_cache: dict = {}
        self._ONLINE_CACHE_MAX = 50

        # ── Info-Banner ───────────────────────────────────────────────────
        # verstecke_widgets wird nach dem Erstellen der Inhalts-Widgets befüllt
        _snip_verstecke = []
        snip_banner = self._baue_info_banner(
            "📦 Snippets – Fertige Code-Bausteine",
            "<b>Snippets</b> sind vorgefertigte Python-Codeblöcke für FreeCAD.<br>"
            "Häufig benötigte Aufgaben – Dokument anlegen, Objekte erstellen,<br>"
            "Placement setzen usw. – sind bereits fertig und einsatzbereit.<br><br>"
            "<b>Lokale Snippets verwenden:</b><br>"
            "① &nbsp;Modus oben auf  <b>📁 Lokal</b>  lassen<br>"
            "② &nbsp;Kategorie wählen  (Dokument · Part · Sketcher · Mesh …)<br>"
            "③ &nbsp;Snippet in der Liste anklicken → Vorschau erscheint<br>"
            "④ &nbsp;<b>↪ In Editor</b>  oder  <b>Doppelklick</b>  → an Cursor-Position einfügen<br>"
            "⑤ &nbsp;<b>📋 Kopieren</b>  → nur in Zwischenablage<br><br>"
            "<b>Online-Makros von GitHub:</b><br>"
            "Modus auf  <b>🌐 Online (GitHub)</b>  schalten<br>"
            "→ lädt echte FreeCAD-Makros direkt aus dem offiziellen Repo<br><br>"
            "<b>Eigene Snippets anlegen:</b><br>"
            "Code im Editor markieren → <b>💾 Markierten Code als Snippet speichern</b><br>"
            "Name vergeben → erscheint danach unter  <b>⭐ Eigene</b><br><br>"
            "<b>Schnellzugriff im KI-Eingabefeld:</b><br>"
            "<b>/</b>  tippen → Popup öffnet sich automatisch<br>"
            "Weitertippen filtert die Liste · Enter fügt den Snippet ein",
            _snip_verstecke,
        )
        layout.addWidget(snip_banner)

        # Modus-Umschalter
        modus_combo = QtWidgets.QComboBox()
        modus_combo.addItems(["📁 Lokal (Offline)", "🌐 Online (GitHub)"])
        layout.addWidget(modus_combo)
        self._snip_modus_combo = modus_combo

        # Kategorie-Auswahl (nur Lokal sichtbar)
        self._kat_widget = QtWidgets.QWidget()
        kat_row = QtWidgets.QHBoxLayout(self._kat_widget)
        kat_row.setContentsMargins(0, 0, 0, 0)
        kat_lbl = QtWidgets.QLabel("Kat:")
        kat_lbl.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_LG)))
        self._snippet_kat = QtWidgets.QComboBox()
        self._snippet_kat.addItems(list(SNIPPETS.keys()) + ["⭐ Eigene"])
        self._snippet_kat.currentIndexChanged.connect(self._lade_snippets_neu)
        kat_row.addWidget(kat_lbl)
        kat_row.addWidget(self._snippet_kat, stretch=1)
        layout.addWidget(self._kat_widget)

        # Suchfilter — self._snip_filter, NICHT self._hint_suche!
        # _hint_suche ist im Hints-Tab bereits vergeben.
        self._snip_filter = QtWidgets.QLineEdit()
        self._snip_filter.setPlaceholderText("🔍  filtern …")
        self._snip_filter.setClearButtonEnabled(True)
        self._snip_filter.textChanged.connect(self._filter_snippets)
        layout.addWidget(self._snip_filter)

        # Snippet-Liste
        self._snippet_liste = QtWidgets.QListWidget()
        self._snippet_liste.setAlternatingRowColors(True)
        self._snippet_liste.setStyleSheet(
            theme.STY_SNIPPET_LISTE(schrift.pt(schrift.STUFE_LG)))
        self._snippet_liste.currentItemChanged.connect(self._snippet_vorschau_aktualisieren)
        self._snippet_liste.itemDoubleClicked.connect(lambda _: self._snippet_in_editor())
        layout.addWidget(self._snippet_liste, stretch=1)

        # Vorschau
        vw_lbl = QtWidgets.QLabel("Vorschau:")
        vw_lbl.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_LG)))
        layout.addWidget(vw_lbl)
        self._snippet_vorschau = QtWidgets.QTextEdit()
        self._snippet_vorschau.setReadOnly(True)
        self._snippet_vorschau.setMaximumHeight(90)
        self._snippet_vorschau.setFont(QtGui.QFont("Courier New", 9))
        self._snippet_vorschau.setStyleSheet(theme.STY_SNIPPET_VORSCHAU)
        layout.addWidget(self._snippet_vorschau)

        # Aktions-Buttons
        btn_row_w = QtWidgets.QWidget()
        btn_row = QtWidgets.QHBoxLayout(btn_row_w)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_einfuegen = QtWidgets.QPushButton("↪ In Editor")
        btn_einfuegen.setToolTip(
            "Snippet an der aktuellen Cursor-Position in den Editor einfügen.\n"
            "Tipp: Doppelklick auf einen Snippet-Namen macht dasselbe.")
        btn_einfuegen.clicked.connect(self._snippet_in_editor)
        btn_kopieren = QtWidgets.QPushButton("📋 Kopieren")
        btn_kopieren.setToolTip("Snippet-Code in die Zwischenablage kopieren.")
        btn_kopieren.clicked.connect(self._snippet_kopieren)
        btn_row.addWidget(btn_einfuegen)
        btn_row.addWidget(btn_kopieren)
        layout.addWidget(btn_row_w)

        # Auswahl-Speicher-Button
        btn_speichern = QtWidgets.QPushButton("💾 Markierten Code als Snippet speichern")
        btn_speichern.setToolTip(
            "Eigenes Snippet anlegen:\n"
            "1. Code im Editor mit der Maus markieren\n"
            "2. Diesen Button klicken\n"
            "3. Namen eingeben\n"
            "→ Snippet erscheint danach unter ⭐ Eigene\n"
            "→ Auch im KI-Suchfeld mit / abrufbar")
        btn_speichern.clicked.connect(self._markierung_als_snippet_speichern)
        layout.addWidget(btn_speichern)

        # ── Banner-Referenzen: alle Inhalts-Widgets eintragen ─────────────
        _snip_verstecke.extend([
            modus_combo, self._kat_widget, self._snip_filter,
            self._snippet_liste, vw_lbl, self._snippet_vorschau,
            btn_row_w, btn_speichern,
        ])

        # Initialisieren
        modus_combo.currentIndexChanged.connect(self._snip_modus_geaendert)
        self._lade_user_snippets()
        self._lade_snippets_neu()

        return w

    # ── Persistenz ────────────────────────────────────────────────────────

    def _get_user_snippet_pfad(self) -> str:
        try:
            import FreeCAD as App
            basis = App.getUserAppDataDir()
        except ImportError:
            basis = os.path.expanduser("~")
        return os.path.join(basis, "makro_editor_snippets.json")

    def _lade_user_snippets(self):
        pfad = self._get_user_snippet_pfad()
        self._user_snippets = {}
        if os.path.exists(pfad):
            try:
                with open(pfad, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._user_snippets = data
            except Exception as e:
                print(f"[SnippetTab] Laden fehlgeschlagen: {e}")

    def _speichere_user_snippet(self, name: str, code: str) -> bool:
        self._user_snippets[name] = code
        pfad = self._get_user_snippet_pfad()
        try:
            with open(pfad, "w", encoding="utf-8") as f:
                json.dump(self._user_snippets, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self._e, "Speicherfehler", f"Fehler beim Sichern:\n{e}")
            return False

    # ── Modus-Steuerung ───────────────────────────────────────────────────

    def _snip_modus_geaendert(self, index: int):
        self._snip_filter.clear()   # korrekt: _snip_filter
        ist_lokal = (index == 0)
        self._kat_widget.setVisible(ist_lokal)
        if ist_lokal:
            self._lade_snippets_neu()
        else:
            self._lade_online_makros()

    def _lade_snippets_neu(self):
        self._snippet_liste.clear()
        self._snippet_vorschau.clear()
        kat = self._snippet_kat.currentText()
        namen = (sorted(self._user_snippets.keys()) if kat == "⭐ Eigene"
                 else sorted(SNIPPETS.get(kat, {}).keys()))
        self._snippet_liste.addItems(namen)

    def _filter_snippets(self, text: str):
        for i in range(self._snippet_liste.count()):
            item = self._snippet_liste.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    # ── Vorschau + Code-Zugriff ───────────────────────────────────────────

    def _snippet_vorschau_aktualisieren(self, item, _prev=None):
        if item is None:
            self._snippet_vorschau.clear()
            return

        name = item.text()

        if self._snip_modus_combo.currentIndex() == 1:
            # Online: erst Cache prüfen, dann asynchronen Worker starten
            url = self._online_makro_links.get(name, "")
            if not url:
                return
            # ── Cache-Treffer: sofort anzeigen, kein Download ────────────
            if url in self._online_preview_cache:
                self._snippet_vorschau.setPlainText(
                    self._online_preview_cache[url])
                return
            # ── Cache-Miss: Worker starten ────────────────────────────────
            self._snippet_vorschau.setPlainText("# Lade Code-Vorschau von GitHub …")
            if self._preview_worker and self._preview_worker.isRunning():
                self._preview_worker.quit()
                self._preview_worker.wait(300)
            self._preview_worker = OnlinePreviewWorker(url)
            # Lambda speichert url als Default-Argument (Closure-Schutz)
            self._preview_worker.code_geladen.connect(
                lambda code, u=url: self._on_preview_geladen(u, code))
            self._preview_worker.start()
        else:
            # Lokal
            kat  = self._snippet_kat.currentText()
            code = (self._user_snippets.get(name, "") if kat == "⭐ Eigene"
                    else SNIPPETS.get(kat, {}).get(name, ""))
            self._snippet_vorschau.setPlainText(code)

    @QtCore.Slot(str, str)
    def _on_preview_geladen(self, url: str, code: str):
        """Speichert den heruntergeladenen Code im Cache und zeigt ihn an."""
        # Cache-Größe begrenzen: ältesten Eintrag entfernen wenn voll
        if len(self._online_preview_cache) >= self._ONLINE_CACHE_MAX:
            try:
                self._online_preview_cache.pop(next(iter(self._online_preview_cache)))
            except StopIteration:
                pass
        self._online_preview_cache[url] = code
        self._snippet_vorschau.setPlainText(code)

    def _snippet_in_editor(self):
        """Fügt den Code aus der Vorschau an der Cursor-Position ein."""
        item = self._snippet_liste.currentItem()
        if item is None:
            return
        # Code direkt aus der Vorschau lesen – kein Doppel-Download
        code = self._snippet_vorschau.toPlainText()
        if not code or code.startswith("# Lade Code"):
            self._e._set_status("⚠  Vorschau noch nicht geladen")
            return
        c = self._e._editor.textCursor()
        if c.columnNumber() > 0 and not c.hasSelection():
            c.movePosition(QtGui.QTextCursor.EndOfBlock)
            c.insertText("\n")
        c.insertText(code)
        self._e._editor.setTextCursor(c)
        self._e._editor.setFocus()
        self._e._set_status(
            f"📦 '{item.text()}' eingefügt ({len(code.splitlines())} Zeilen)")

    def _snippet_kopieren(self):
        code = self._snippet_vorschau.toPlainText()
        if code:
            QtWidgets.QApplication.clipboard().setText(code)
            item = self._snippet_liste.currentItem()
            name = item.text() if item else "Snippet"
            self._e._set_status(f"📋 '{name}' kopiert")

    def _markierung_als_snippet_speichern(self):
        if not self._e._editor:
            return
        # Qt codiert Zeilenumbrüche in selectedText() als U+2029
        text = self._e._editor.textCursor().selectedText().replace("\u2029", "\n")
        if not text.strip():
            QtWidgets.QMessageBox.information(
                self._e, "Achtung", "Bitte markiere zuerst Code im Editor.")
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self._e, "Snippet benennen", "Name für das neue Snippet:",
            QtWidgets.QLineEdit.Normal, "⭐ Mein: ")
        if ok and name.strip():
            name = name.strip()
            if self._speichere_user_snippet(name, text):
                idx = self._snippet_kat.findText("⭐ Eigene")
                if idx >= 0:
                    self._snippet_kat.setCurrentIndex(idx)
                self._lade_snippets_neu()
                treffer = self._snippet_liste.findItems(name, QtCore.Qt.MatchExactly)
                if treffer:
                    self._snippet_liste.setCurrentItem(treffer[0])
                self._e._set_status(f"💾 Snippet '{name}' gespeichert")

    # ── Online-Makros ─────────────────────────────────────────────────────

    def _lade_online_makros(self):
        self._snippet_liste.clear()
        self._snippet_vorschau.clear()
        self._snippet_liste.addItem("⏳ Verbinde mit GitHub …")
        self._snip_worker = OnlineMakroWorker(self)
        self._snip_worker.liste_geladen.connect(self._on_online_liste_geladen)
        self._snip_worker.fehler.connect(self._on_online_fehler)
        self._snip_worker.start()

    @QtCore.Slot(dict)
    def _on_online_liste_geladen(self, makros: dict):
        self._online_makro_links = makros
        self._snippet_liste.clear()
        if makros:
            self._snippet_liste.addItems(sorted(makros.keys()))
            self._e._set_status(f"🌐 {len(makros)} Makros von GitHub geladen")
        else:
            self._snippet_liste.addItem("Keine Makros gefunden.")

    @QtCore.Slot(str)
    def _on_online_fehler(self, fehler: str):
        self._snippet_liste.clear()
        self._snippet_liste.addItem(f"❌ {fehler}")
        self._snippet_liste.addItem("Bitte Internetverbindung prüfen.")
        self._e._set_status("⚠  GitHub-Abruf fehlgeschlagen")

    # ══ API-Hints-Tab ══════════════════════════════════════════════════════
    def _baue_hints_tab(self) -> QtWidgets.QWidget:
        """Durchsuchbare FreeCAD-API-Kurzreferenz."""
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Info-Banner ───────────────────────────────────────────────────
        _hints_verstecke = []
        layout.addWidget(self._baue_info_banner(
            "💡 FreeCAD API-Kurzreferenz",
            "<b>API-Hints</b> sind Kurzbeschreibungen der wichtigsten FreeCAD-Befehle<br>"
            "und Python-Funktionen – offline, sofort verfügbar, ohne Internetverbindung.<br><br>"
            "<b>Enthalten sind Befehle aus:</b><br>"
            "&nbsp;&nbsp;App · Part · Sketcher · Mesh · Draft · Placement · Selection · GUI<br><br>"
            "<b>So benutzt du die Referenz:</b><br>"
            "① &nbsp;Suchbegriff eintippen  (z.B. <b>mesh</b>, <b>vector</b>, <b>placement</b>)<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Mehrere Wörter gleichzeitig möglich: z.B. <b>part shape</b><br>"
            "② &nbsp;Befehl in der Liste anklicken<br>"
            "③ &nbsp;Kurzbeschreibung erscheint direkt darunter<br>"
            "④ &nbsp;<b>📋 Signatur kopieren</b>  → in Zwischenablage<br><br>"
            "<b>Mit KI kombinieren:</b><br>"
            "Signatur ins KI-Eingabefeld (🤖 KI-Panel) einfügen → <b>🤖 Fragen</b><br>"
            "→ KI erklärt Parameter, gibt Beispielcode und häufige Fehler",
            _hints_verstecke,
        ))

        # self._hint_suche gehört ausschließlich in diesen Tab
        self._hint_suche = QtWidgets.QLineEdit()
        self._hint_suche.setPlaceholderText("🔍  filtern … z.B. 'Mesh', 'Vector'")
        self._hint_suche.setClearButtonEnabled(True)
        self._hint_suche.textChanged.connect(self._filter_hints)
        layout.addWidget(self._hint_suche)

        self._hint_liste = QtWidgets.QListWidget()
        self._hint_liste.setAlternatingRowColors(True)
        self._hint_liste.setFont(QtGui.QFont("Courier New", 9))
        self._hint_liste.setStyleSheet(theme.STY_HINTS_LISTE)
        self._hint_liste.currentItemChanged.connect(self._hint_desc_aktualisieren)
        layout.addWidget(self._hint_liste, stretch=1)

        self._hint_desc = QtWidgets.QLabel("")
        self._hint_desc.setWordWrap(True)
        self._hint_desc.setStyleSheet(
            theme.STY_HINTS_DESC(schrift.pt(schrift.STUFE_BASE)))
        layout.addWidget(self._hint_desc)

        btn = QtWidgets.QPushButton("📋  Signatur kopieren")
        btn.setMinimumHeight(28)
        btn.setStyleSheet(theme.STY_BTN_BORDER(schrift.pt(schrift.STUFE_BASE)))
        btn.clicked.connect(self._hint_kopieren)
        layout.addWidget(btn)

        # ── Banner-Referenzen ─────────────────────────────────────────────
        _hints_verstecke.extend([
            self._hint_suche, self._hint_liste, self._hint_desc, btn])

        self._alle_hints = FC_API_HINTS
        self._befuelle_hints(self._alle_hints)
        return w

    def _befuelle_hints(self, hints: list):
        self._hint_liste.clear()
        self._hint_desc.setText("")
        for sig, desc in hints:
            item = QtWidgets.QListWidgetItem(sig)
            item.setData(QtCore.Qt.UserRole, desc)
            item.setToolTip(desc)
            self._hint_liste.addItem(item)
        if self._hint_liste.count():
            self._hint_liste.setCurrentRow(0)

    def _filter_hints(self, text: str):
        begriffe = text.lower().split()
        if not begriffe:
            self._befuelle_hints(self._alle_hints)
            return
        gefunden = [
            (s, d) for s, d in self._alle_hints
            if all(b in s.lower() or b in d.lower() for b in begriffe)
        ]
        self._befuelle_hints(gefunden)

    def _hint_desc_aktualisieren(self, item, _prev=None):
        self._hint_desc.setText(
            item.data(QtCore.Qt.UserRole) if item else "")

    def _hint_kopieren(self):
        item = self._hint_liste.currentItem()
        if item:
            QtWidgets.QApplication.clipboard().setText(item.text())
            self._e._set_status(f"📋 Kopiert: {item.text()[:50]}")

    # ══ Fehler-Tab (linke Leiste) ══════════════════════════════════════════
    def _baue_fehler_tab(self) -> QtWidgets.QWidget:
        """Fehler-Übersetzer als eigenständiger Tab in der linken Leiste."""
        from ui.fehler import uebersetze_text as _ue
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── Info-Banner ───────────────────────────────────────────────────
        _fehler_verstecke = []
        layout.addWidget(self._baue_info_banner(
            "⚠ Fehler-Übersetzer – Fehlermeldungen verstehen",
            "FreeCAD gibt Fehlermeldungen und Tracebacks auf <b>Englisch</b> aus.<br>"
            "Dieser Tab übersetzt sie ins Deutsche und erklärt die genaue Ursache<br>"
            "sowie konkrete Lösungshinweise.<br><br>"
            "<b>So benutzt du ihn:</b><br>"
            "① &nbsp;Fehlermeldung oder Traceback aus FreeCAD kopieren<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;(möglichst den vollständigen Text inkl. Zeilennummer)<br>"
            "② &nbsp;In das obere Eingabefeld einfügen<br>"
            "③ &nbsp;<b>🔍 Übersetzen</b> klicken  oder  <b>Strg+Enter</b><br>"
            "④ &nbsp;Deutsche Erklärung + Lösungsvorschlag erscheint darunter<br><br>"
            "<b>Häufige Fehlertypen die erkannt werden:</b><br>"
            "&nbsp;&nbsp;AttributeError · TypeError · NameError · ImportError<br>"
            "&nbsp;&nbsp;No active document · Shape-Fehler · Constraint-Fehler<br><br>"
            "<b>KI hinzuziehen:</b><br>"
            "Im ⚠ Fehler-Panel unten  →  <b>🔧 KI korrigieren</b><br>"
            "→ KI analysiert den Fehler zusammen mit dem aktuellen Code<br>"
            "→ Korrigierter Code wird direkt in die Sandbox geladen",
            _fehler_verstecke,
        ))

        lbl_ein = QtWidgets.QLabel("Fehlermeldung (Englisch):")
        lbl_ein.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_BASE)))
        layout.addWidget(lbl_ein)

        self._ftab_eingabe = QtWidgets.QPlainTextEdit()
        self._ftab_eingabe.setFont(QtGui.QFont("Courier New", 9))
        self._ftab_eingabe.setPlaceholderText(
            "'NoneType' object has no attribute 'Shape'\n"
            "name 'doc' is not defined\n"
            "No active document")
        self._ftab_eingabe.setMaximumHeight(120)
        self._ftab_eingabe.setStyleSheet(theme.STY_FEHLER_TAB_FELD)
        _opt = self._ftab_eingabe.document().defaultTextOption()
        _opt.setAlignment(QtCore.Qt.AlignLeft)
        self._ftab_eingabe.document().setDefaultTextOption(_opt)
        layout.addWidget(self._ftab_eingabe)

        btn = QtWidgets.QPushButton("🔍  Übersetzen  (Strg+Return)")
        btn.setMinimumHeight(32)
        btn.setStyleSheet(theme.STY_BTN_BORDER_BOLD(schrift.pt(schrift.STUFE_LG)))
        layout.addWidget(btn)

        lbl_aus = QtWidgets.QLabel("Erklärung (Deutsch):")
        lbl_aus.setStyleSheet(theme.STY_ABSCHNITT_LABEL(schrift.pt(schrift.STUFE_BASE)))
        layout.addWidget(lbl_aus)

        self._ftab_ausgabe = QtWidgets.QPlainTextEdit()
        self._ftab_ausgabe.setReadOnly(True)
        self._ftab_ausgabe.setFont(QtGui.QFont("Courier New", 9))
        self._ftab_ausgabe.setPlaceholderText("Deutsche Erklärung erscheint hier …")
        self._ftab_ausgabe.setStyleSheet(theme.STY_FEHLER_TAB_FELD)
        _opt = self._ftab_ausgabe.document().defaultTextOption()
        _opt.setAlignment(QtCore.Qt.AlignLeft)
        self._ftab_ausgabe.document().setDefaultTextOption(_opt)
        layout.addWidget(self._ftab_ausgabe, stretch=1)

        # ── Banner-Referenzen ─────────────────────────────────────────────
        _fehler_verstecke.extend([
            lbl_ein, self._ftab_eingabe, btn, lbl_aus, self._ftab_ausgabe])

        def _uebersetzen():
            text = self._ftab_eingabe.toPlainText().strip()
            if not text:
                return
            ergebnis = _ue(text)
            self._ftab_ausgabe.setPlainText(ergebnis)
            # ins untere Panel spiegeln wenn vorhanden
            if hasattr(self._e, "_fehler_eingabe"):
                self._e._fehler_eingabe.setPlainText(text)
            if hasattr(self._e, "_fehler_ausgabe"):
                self._e._fehler_ausgabe.setPlainText(ergebnis)

        btn.clicked.connect(_uebersetzen)
        _QShortcut = getattr(QtGui, "QShortcut", None) or getattr(QtWidgets, "QShortcut", None)
        if _QShortcut:
            _QShortcut(QtGui.QKeySequence("Ctrl+Return"), self._ftab_eingabe, _uebersetzen)

        return w

    # ══ Fehler-Panel (unterer einklappbarer Bereich) ═══════════════════════
    def _baue_fehler_panel(self) -> QtWidgets.QWidget:
        """
        Erstellt das FehlerPanel-Widget und verdrahtet die internen Referenzen.
        Das eigentliche Widget lebt in fehler_panel.py.
        """
        from ui.fehler import uebersetze_text as _ue
        from editor.fehler.fehler_panel import FehlerPanel

        panel = FehlerPanel(
            uebersetze_fn = _ue,
            ki_callback   = self._e._ki_fehler_erklaeren,
            max_hoehe     = 150,
        )

        # Rückwärts-Kompatibilität: Attribute die ki_fehler.py direkt auf dem
        # echten Editor liest (self._e statt self, da diese Klasse jetzt
        # komponiert statt gemixt ist).
        self._e._fehler_eingabe = panel._ein
        self._e._fehler_ausgabe = panel._aus

        # KI-Korrektur-Callback verdrahten
        panel.setze_ki_korrektur_cb(self._e._on_self_correction_needed)
        self._e._fehler_panel = panel

        return panel

