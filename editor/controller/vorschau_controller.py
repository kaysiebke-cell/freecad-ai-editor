# -*- coding: utf-8 -*-
"""
editor_vorschau_mixin.py
────────────────────────
VorschauMixin – Interaktiver FreeCAD-3D-Viewport direkt im Editor-Tab.

Strategie: Widget-Embedding via setParent()
  FreeCAD läuft im selben Prozess. Der aktive View3DInventor (QWidget) wird
  temporär per setParent() in den Vorschau-Tab eingebettet.
  Der User kann das 3D-Modell drehen, zoomen und schwenken — genau wie im
  normalen FreeCAD-Viewport. Beim Schließen des Tabs wird der View wieder
  in sein ursprüngliches MdiSubWindow zurückgesetzt.

Ablauf:
  1. ▶ Ausführen  → exec() im FreeCAD-Namespace, recompute(), fitAll()
  2. View3DInventor-Widget per setParent() in Tab-Container einbetten
  3. Volle Maus-Interaktion: drehen / zoomen / schwenken
  4. 🔄 Aktualisieren → Code erneut ausführen, Widget bleibt eingebettet
  5. ✕ Schließen → Widget per setParent() zurück ins MdiSubWindow

Öffentliche API:
  vorschau_starten()    – Sidebar-Button "👁 Vorschau"
  vorschau_schliessen() – Tab-✕ oder Schließen-Button
  _vorschau_init()      – am Ende von MakroEditor.__init__()
"""

import ast
import traceback as _tb

from qt_compat import QtWidgets, QtCore, QtGui
import theme
import schrift


class VorschauController:
    """
    Mixin: Interaktiver FreeCAD-3D-Viewport eingebettet in den Editor-Tab.

    Erwartet auf self:
      _editor_tab_widget   QTabWidget (Datei-Tab-Leiste)
      _editor              aktueller JediEditor
      _set_status()
    """

    # ── Init ──────────────────────────────────────────────────────────────
    def _vorschau_init(self):
        self._vorschau_tab_index:    int                      = -1
        self._vorschau_widget:       QtWidgets.QWidget | None = None
        self._vorschau_container:    QtWidgets.QWidget | None = None
        self._vorschau_status_lbl:   QtWidgets.QLabel  | None = None
        self._vorschau_log_box:      QtWidgets.QPlainTextEdit | None = None
        self._vorschau_view_widget:  QtWidgets.QWidget | None = None  # der eingebettete View
        self._vorschau_orig_parent:  QtWidgets.QWidget | None = None  # MdiSubWindow
        self._vorschau_orig_geom:    QtCore.QRect      | None = None
        self._vorschau_shot_timer:   QtCore.QTimer     | None = None
        self._vorschau_code_override: str | None = None

        self._editor_tab_widget.tabCloseRequested.connect(
            self._vorschau_tab_close_requested)

    # ── Öffentlich ────────────────────────────────────────────────────────
    def vorschau_starten(self, code: str = None):
        """Öffnet den Vorschau-Tab. Wenn code angegeben, wird er sofort ausgeführt."""
        if self._vorschau_tab_index >= 0:
            self._editor_tab_widget.setCurrentIndex(self._vorschau_tab_index)
        else:
            self._vorschau_widget = self._baue_vorschau_tab()
            idx = self._editor_tab_widget.addTab(self._vorschau_widget, "👁 Vorschau")
            self._vorschau_tab_index = idx
            self._editor_tab_widget.setCurrentIndex(idx)

        if code:
            self._vorschau_code_override = code
            self._set_status("👁 Vorschau-Tab — führe KI-Code aus …")
            self._vorschau_ausfuehren()
        else:
            self._set_status("👁 Vorschau-Tab geöffnet — ▶ Ausführen drücken")

    def vorschau_schliessen(self):
        self._view_zurueckgeben()
        if self._vorschau_shot_timer:
            self._vorschau_shot_timer.stop()
            self._vorschau_shot_timer = None
        if self._vorschau_tab_index >= 0:
            self._editor_tab_widget.removeTab(self._vorschau_tab_index)
            self._vorschau_tab_index = -1
        self._vorschau_widget   = None
        self._vorschau_container = None
        self._vorschau_status_lbl = None
        self._vorschau_log_box    = None
        self._set_status("👁 Vorschau geschlossen")

    # ── Tab-UI ────────────────────────────────────────────────────────────
    def _baue_vorschau_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(w)
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(4)

        # Titelzeile
        tz = QtWidgets.QHBoxLayout()
        tl = QtWidgets.QLabel("👁  Live-Vorschau  —  FreeCAD 3D-Viewport  (drehbar)")
        tl.setStyleSheet(theme.STY_VORSCHAU_TITEL(schrift.pt(schrift.STUFE_LG)))
        tz.addWidget(tl)
        tz.addStretch()
        bx = QtWidgets.QPushButton("✕  Schließen")
        bx.setFixedHeight(22)
        bx.setStyleSheet(theme.STY_VORSCHAU_CLOSE_BTN(schrift.pt(schrift.STUFE_BASE)))
        bx.clicked.connect(self.vorschau_schliessen)
        tz.addWidget(bx)
        root.addLayout(tz)

        # Status
        self._vorschau_status_lbl = QtWidgets.QLabel(
            "Bereit — '▶ Ausführen' drücken")
        self._vorschau_status_lbl.setStyleSheet(
            theme.STY_VORSCHAU_STATUS(schrift.pt(schrift.STUFE_BASE)))
        root.addWidget(self._vorschau_status_lbl)

        # Container für den eingebetteten View
        self._vorschau_container = QtWidgets.QWidget()
        self._vorschau_container.setObjectName("VorschauContainer")
        self._vorschau_container.setMinimumHeight(300)
        self._vorschau_container.setStyleSheet(theme.STY_VORSCHAU_CONTAINER)
        container_lay = QtWidgets.QVBoxLayout(self._vorschau_container)
        container_lay.setContentsMargins(0, 0, 0, 0)

        # Platzhalter-Label (wird ersetzt sobald der View eingebettet ist)
        self._vorschau_placeholder = QtWidgets.QLabel(
            f"<span style='font-size:{schrift.pt(schrift.STUFE_ICON)}pt;'>👁</span><br>"
            f"<span style='font-size:{schrift.pt(schrift.STUFE_LG)}pt;'>"
            "FreeCAD-Viewport erscheint hier<br>"
            "nach ▶ Ausführen</span>")
        self._vorschau_placeholder.setAlignment(QtCore.Qt.AlignCenter)
        self._vorschau_placeholder.setStyleSheet(theme.STY_VORSCHAU_PLACEHOLDER)
        container_lay.addWidget(self._vorschau_placeholder)
        root.addWidget(self._vorschau_container, stretch=1)

        # Log (klein)
        log_lbl = QtWidgets.QLabel("Ausgabe:")
        log_lbl.setStyleSheet(theme.STY_VORSCHAU_LOG_LABEL(schrift.pt(schrift.STUFE_SM)))
        root.addWidget(log_lbl)

        self._vorschau_log_box = QtWidgets.QPlainTextEdit()
        self._vorschau_log_box.setReadOnly(True)
        self._vorschau_log_box.setFont(QtGui.QFont("Courier New", 9))
        self._vorschau_log_box.setMaximumHeight(70)
        self._vorschau_log_box.setStyleSheet(theme.STY_VORSCHAU_LOG_BOX)
        root.addWidget(self._vorschau_log_box)

        # Buttons
        bz = QtWidgets.QHBoxLayout()
        bz.setSpacing(6)

        def _btn(label, slot, tip=""):
            b = QtWidgets.QPushButton(label)
            b.setMinimumHeight(30)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            bz.addWidget(b)
            return b

        self._btn_vp_aus  = _btn("▶  Ausführen",
                                  self._vorschau_ausfuehren,
                                  "Code ausführen und 3D-Viewport einbetten")
        self._btn_vp_akt  = _btn("🔄  Aktualisieren",
                                  self._vorschau_ausfuehren,
                                  "Code erneut ausführen (Viewport bleibt eingebettet)")
        self._btn_vp_fit  = _btn("⊡  Einpassen",
                                  self._vorschau_fit_all,
                                  "fitAll() — Modell ins Bild einpassen")
        root.addLayout(bz)

        warn = QtWidgets.QLabel(
            "⚠  Code wird direkt in FreeCAD ausgeführt — Änderungen am Dokument sind real.")
        warn.setStyleSheet(theme.STY_VORSCHAU_WARN(schrift.pt(schrift.STUFE_SM)))
        warn.setWordWrap(True)
        root.addWidget(warn)

        return w

    # ── Ausführen ────────────────────────────────────────────────────────
    def _vorschau_ausfuehren(self):
        # Priorität: override (KI-Code) → Editor
        code = getattr(self, "_vorschau_code_override", None) or self._editor.toPlainText().strip()
        self._vorschau_code_override = None  # einmalig verwenden
        if not code:
            self._vorschau_log("⚠  Editor ist leer.")
            return

        try:
            ast.parse(code)
        except SyntaxError as e:
            self._vorschau_log(f"❌  SyntaxError Zeile {e.lineno}: {e.msg}")
            self._vorschau_status(f"❌ SyntaxError Zeile {e.lineno}")
            if hasattr(self._editor, "setze_fehler_zeilen") and e.lineno:
                self._editor.setze_fehler_zeilen([e.lineno - 1])
            return

        if hasattr(self._editor, "setze_fehler_zeilen"):
            self._editor.setze_fehler_zeilen([])
        self._vorschau_log_box.clear()
        self._vorschau_log("▶ Führe Code aus …")
        self._vorschau_status("⏳ Code wird ausgeführt …")

        # Auto-Backup vor Ausführung (wie im Referenzprojekt freecad-ai)
        try:
            import FreeCAD as _App
            _doc = _App.ActiveDocument
            if _doc and _doc.FileName:
                import shutil as _sh
                backup = _doc.FileName + ".vorschau-backup"
                _sh.copy2(_doc.FileName, backup)
                self._vorschau_log(f"💾 Backup: {backup}")
        except Exception:
            pass

        fehler = self._vorschau_exec(code)
        if fehler:
            self._vorschau_status(f"❌ {fehler}")
            if hasattr(self, "fehler_anzeigen"):
                self.fehler_anzeigen(fehler)
            return

        self._vorschau_log("✅ Ausgeführt — bette Viewport ein …")

        # View einbetten nach kurzem Delay (FreeCAD braucht einen Frame)
        self._vorschau_shot_timer = QtCore.QTimer(self)
        self._vorschau_shot_timer.setSingleShot(True)
        self._vorschau_shot_timer.timeout.connect(self._view_einbetten)
        self._vorschau_shot_timer.start(200)

    def _vorschau_exec(self, code: str):
        """exec() im echten FreeCAD-Namespace. Gibt None oder Fehlermeldung zurück."""
        try:
            import FreeCAD as App
            import FreeCADGui as Gui
        except ImportError:
            return "FreeCAD nicht verfügbar"

        ns = {
            "__builtins__": __builtins__,
            "__name__":     "__vorschau__",
            "App": App, "Gui": Gui,
        }
        import importlib
        for mod in ("Part", "PartDesign", "Sketcher", "Draft", "Mesh"):
            try:
                ns[mod] = importlib.import_module(mod)
            except ImportError:
                pass
        # Part-Workbench explizit initialisieren damit Part::Cut/.Base/.Tool existieren
        try:
            import Part as _Part
            _Part.show  # triggert Workbench-Initialisierung
        except Exception:
            pass

        import re as _re
        code = _re.sub(r'\bPySide2\b', 'PySide6', code)

        # Bekannte halluzinierte FreeCAD-Typen vor exec() erkennen
        _FAKE_TYPEN = {
            "Part::UnionForTwoVolumes", "Part::Union", "Part::BooleanUnion",
            "Part::BooleanCut", "Part::Subtract", "Part::Difference",
            "Part::Merge", "Part::Intersection", "Part::BooleanIntersection",
            "Part::Profile2D", "Part::Extrude2D", "Part::Shell2D",
            "Part::Loft2D", "Part::Solid2D",
        }
        for fake in _FAKE_TYPEN:
            if fake in code:
                return (
                    f"❌ Unbekannter FreeCAD-Typ: '{fake}'\n"
                    f"   Dieser Typ existiert nicht in FreeCAD.\n"
                    f"   KI-Code wurde NICHT ausgeführt.\n"
                    f"   → Bitte KI erneut anfragen oder Beschreibung anpassen."
                )

        doc = App.ActiveDocument
        in_transaction = False
        try:
            if doc:
                doc.openTransaction("KI-Vorschau")
                in_transaction = True
            exec(compile(code, "<vorschau>", "exec"), ns)  # noqa: S102
        except Exception as e:
            if in_transaction:
                try:
                    doc.abortTransaction()
                except Exception:
                    pass
            zeilen = _tb.format_exc().strip().splitlines()
            self._vorschau_log("\n".join(zeilen[-8:]))
            return f"{type(e).__name__}: {e}"

        # recompute + fitAll
        try:
            if App.ActiveDocument:
                App.ActiveDocument.recompute()
        except Exception:
            pass

        if in_transaction:
            try:
                doc.commitTransaction()
            except Exception:
                pass

        try:
            v = Gui.ActiveDocument.ActiveView if Gui.ActiveDocument else None
            if v:
                v.fitAll()
        except Exception:
            pass

        return None

    # ── View einbetten / zurückgeben ──────────────────────────────────────
    def _view_einbetten(self):
        """Holt den aktiven View3DInventor und bettet ihn in den Container ein."""
        try:
            import FreeCADGui as Gui
        except ImportError:
            self._vorschau_log("❌ FreeCAD nicht verfügbar")
            return

        # Alten View ggf. zurückgeben bevor neuer geholt wird
        if self._vorschau_view_widget:
            self._view_zurueckgeben()

        # View-Widget aus FreeCAD holen
        view_widget = self._hole_view_widget(Gui)
        if view_widget is None:
            self._vorschau_log(
                "⚠  Kein aktiver 3D-View gefunden.\n"
                "   Öffne ein FreeCAD-Dokument und führe den Code erneut aus.")
            self._vorschau_status("⚠ Kein 3D-View gefunden")
            return

        # Original-Parent und Geometrie merken (für Rückgabe)
        self._vorschau_orig_parent = view_widget.parent()
        self._vorschau_orig_geom   = view_widget.geometry()

        # Dock-Zustände sichern — setParent() löst Qt-Relayout aus der Docks versteckt
        self._vorschau_dock_zustaende = [
            (d, d.isVisible())
            for d in self.findChildren(QtWidgets.QDockWidget)
        ]

        # Platzhalter ausblenden
        self._vorschau_placeholder.hide()

        # View in unseren Container einbetten
        lay = self._vorschau_container.layout()
        self._vorschau_view_widget = view_widget
        view_widget.setParent(self._vorschau_container)
        lay.addWidget(view_widget)
        view_widget.show()

        # Docks wiederherstellen die Qt beim setParent() versteckt hat
        for dock, war_sichtbar in self._vorschau_dock_zustaende:
            if war_sichtbar and not dock.isVisible():
                dock.show()

        self._vorschau_status("✅ 3D-Viewport eingebettet — drehen/zoomen mit Maus")
        self._vorschau_log("📐 Viewport eingebettet — Maus: Drehen=Rechtsklick, Zoom=Rad, Pan=Mitte")

    def _view_zurueckgeben(self):
        """Gibt den eingebetteten View zurück an FreeCAD."""
        if self._vorschau_view_widget is None:
            return
        try:
            vw = self._vorschau_view_widget
            lay = self._vorschau_container.layout()
            lay.removeWidget(vw)

            # Zurück zum Original-Parent (MdiSubWindow)
            if self._vorschau_orig_parent:
                orig_lay = self._vorschau_orig_parent.layout()
                vw.setParent(self._vorschau_orig_parent)
                if orig_lay:
                    orig_lay.addWidget(vw)
                if self._vorschau_orig_geom:
                    vw.setGeometry(self._vorschau_orig_geom)
                vw.show()
            else:
                # Kein Original-Parent bekannt → als eigenes Fenster zeigen
                vw.setParent(None)
                vw.show()
        except Exception as e:
            self._vorschau_log(f"Rückgabe View: {e}")
        finally:
            self._vorschau_view_widget = None
            self._vorschau_orig_parent = None
            self._vorschau_orig_geom   = None
            # Platzhalter wieder anzeigen
            if self._vorschau_placeholder:
                self._vorschau_placeholder.show()
            # Docks wiederherstellen die beim Einbetten versteckt wurden
            for dock, war_sichtbar in getattr(self, "_vorschau_dock_zustaende", []):
                if war_sichtbar and not dock.isVisible():
                    dock.show()
            self._vorschau_dock_zustaende = []

    @staticmethod
    def _hole_view_widget(Gui) -> QtWidgets.QWidget | None:
        """
        Gibt das QWidget des aktiven View3DInventors zurück.
        Versucht mehrere FreeCAD-API-Wege.
        """
        # Weg 1: activeView() direkt
        try:
            doc = Gui.ActiveDocument
            if doc:
                view = doc.ActiveView
                if view and hasattr(view, "graphicsView"):
                    return view.graphicsView()
        except Exception:
            pass

        # Weg 2: getMainWindow → MdiArea → aktives SubWindow → QWidget suchen
        try:
            mw = Gui.getMainWindow()
            mdi = mw.findChild(QtWidgets.QMdiArea)
            if mdi:
                sub = mdi.activeSubWindow()
                if sub:
                    # Das erste QWidget-Kind das kein QMdiSubWindow ist
                    for child in sub.findChildren(QtWidgets.QWidget):
                        cn = type(child).__name__
                        if "View3D" in cn or "Inventor" in cn or "Quarter" in cn:
                            return child
                    # Fallback: den Widget-Inhalt des SubWindows selbst
                    w = sub.widget()
                    if w:
                        return w
        except Exception:
            pass

        # Weg 3: centralWidget des MainWindows
        try:
            mw = Gui.getMainWindow()
            cw = mw.centralWidget()
            if cw:
                for child in cw.findChildren(QtWidgets.QWidget):
                    cn = type(child).__name__
                    if "View3D" in cn or "Inventor" in cn or "Quarter" in cn:
                        return child
        except Exception:
            pass

        return None

    def _vorschau_fit_all(self):
        """fitAll() auf dem aktuellen View."""
        try:
            import FreeCADGui as Gui
            v = Gui.ActiveDocument.ActiveView if Gui.ActiveDocument else None
            if v:
                v.fitAll()
                self._vorschau_status("⊡ fitAll ausgeführt")
        except Exception as e:
            self._vorschau_log(f"fitAll: {e}")

    # ── Tab-Close ────────────────────────────────────────────────────────
    def _vorschau_tab_close_requested(self, index: int):
        if index == self._vorschau_tab_index:
            self.vorschau_schliessen()

    # ── Hilfsmethoden ────────────────────────────────────────────────────
    def _vorschau_log(self, text: str):
        if self._vorschau_log_box:
            self._vorschau_log_box.appendPlainText(text)
            sb = self._vorschau_log_box.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _vorschau_status(self, text: str, farbe: str = ""):
        if self._vorschau_status_lbl:
            self._vorschau_status_lbl.setText(text)
            self._vorschau_status_lbl.setStyleSheet(
                theme.STY_VORSCHAU_STATUS(schrift.pt(schrift.STUFE_BASE)))
