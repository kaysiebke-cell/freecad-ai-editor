# -*- coding: utf-8 -*-
"""
editor_barrierefreiheit.py
──────────────────────────
Farbschema-Umschaltung, Barrierefreiheits-Handler und Widget-Blinken.
"""

import re

from qt_compat import QtWidgets, QtCore, QtGui

import theme
import params


class BarriereLogik:
    """Reagiert auf Farbschema- und Barrierefreiheits-Änderungen."""

    __slots__ = ("_e",)

    def __init__(self, editor):
        self._e = editor

    def on_farbschema(self, dunkel: bool) -> None:
        e = self._e
        params.set_farbschema_dunkel(dunkel)
        theme.set_farbschema(dunkel)
        for tab in getattr(e, "_tabs", []):
            editor = tab.get("editor")
            if editor:
                editor.setStyleSheet(theme.STY_CODE_EDITOR())
            hl = tab.get("highlighter")
            if hl:
                hl.aktualisiere_theme()
        if hasattr(e, "_hl_find"):  e._hl_find.aktualisiere_theme()
        if hasattr(e, "_hl_ki"):    e._hl_ki.aktualisiere_theme()
        if hasattr(e, "find_area"): theme.apply_input_bg_suche(e.find_area)
        if hasattr(e, "_ki_area"):  theme.apply_input_bg_ki(e._ki_area)
        if hasattr(e, "_kontext"):  theme.apply_input_bg_kontext(e._kontext)

    def on_barrierefreiheit(self, schluessel, wert):
        e = self._e
        if schluessel == "schrift_groesse":
            font = e.font()
            font.setPointSize(int(wert))
            e.setFont(font)
            QtWidgets.QApplication.instance().setFont(font)
        elif schluessel == "editor_schrift":
            f = QtGui.QFont("Courier New", int(wert))
            for tab in getattr(e, "_tabs", []):
                editor = tab.get("editor")
                if editor:
                    editor.setFont(f)
            if hasattr(e, "find_area"): e.find_area.setFont(f)
            if hasattr(e, "_ki_area"):  e._ki_area.setFont(f)
        elif schluessel == "button_groesse":
            groessen = {0: 26, 1: 34, 2: 42}
            hoehe = groessen.get(int(wert), 26)
            for btn in e.findChildren(QtWidgets.QPushButton):
                if btn.height() in (26, 34, 42):
                    btn.setFixedHeight(hoehe)
        elif schluessel == "icon_text":
            for btn, ico, lbl in getattr(e, "_panel_btns", []):
                if wert:
                    btn.setText(f"{ico}  {lbl}")
                    btn.setMinimumWidth(44)
                    btn.setMaximumWidth(16777215)
                else:
                    btn.setText(ico)
                    btn.setFixedWidth(32)
        elif schluessel == "einfache_ansicht":
            for btn in getattr(e, "_panel_btns_optional", []):
                btn.setVisible(not wert)
        elif schluessel == "animation":
            e._animationen_reduziert = bool(wert)
        elif schluessel == "tooltips_immer":
            if wert:
                if not hasattr(e, "_tooltip_filter"):
                    class _TooltipFilter(QtCore.QObject):
                        def eventFilter(self_, obj, event):
                            if (event.type() == QtCore.QEvent.Type.Enter
                                    and isinstance(obj, QtWidgets.QWidget)
                                    and obj.toolTip()):
                                QtWidgets.QToolTip.showText(
                                    obj.mapToGlobal(QtCore.QPoint(0, obj.height())),
                                    obj.toolTip(), obj)
                            return False
                    e._tooltip_filter = _TooltipFilter(e)
                QtWidgets.QApplication.instance().installEventFilter(e._tooltip_filter)
            else:
                if hasattr(e, "_tooltip_filter"):
                    QtWidgets.QApplication.instance().removeEventFilter(e._tooltip_filter)
                QtWidgets.QToolTip.hideText()
        elif schluessel == "tastaturmodus":
            for sc in getattr(e, "_tastatur_shortcuts", []):
                sc.setEnabled(False)
            e._tastatur_shortcuts.clear()
            for btn, ico, lbl in getattr(e, "_panel_btns", []):
                btn.setToolTip(lbl)
            if wert:
                _tasten = ["Alt+1","Alt+2","Alt+3","Alt+4","Alt+5",
                           "Alt+6","Alt+7","Alt+8","Alt+9","Alt+0","Alt+-","Alt+="]
                sichtbare = [(btn, ico, lbl)
                             for btn, ico, lbl in getattr(e, "_panel_btns", [])
                             if btn.isVisible()]
                for i, (btn, ico, lbl) in enumerate(sichtbare):
                    if i >= len(_tasten):
                        break
                    taste = _tasten[i]
                    sc = QtWidgets.QShortcut(QtGui.QKeySequence(taste), e)
                    sc.activated.connect(btn.click)
                    sc.setEnabled(True)
                    e._tastatur_shortcuts.append(sc)
                    btn.setToolTip(f"{lbl}  [{taste}]")
        elif schluessel == "kontrast":
            e.setStyleSheet(theme.STY_HOCHKONTRAST if wert else "")

    def zeige_hilfe(self):
        e = self._e
        if hasattr(e, "_bf_stack"):
            e._bf_stack.setCurrentIndex(3)
        if hasattr(e, "_btn_bf_gruppe"):
            e._btn_bf_gruppe.setChecked(True)

    def widget_blinken(self, name: str):
        e = self._e
        _re = re

        def _kern(s):
            return _re.sub(r'[^\w]', '', s, flags=_re.UNICODE).replace('_', '').lower()

        ziel = _kern(name)
        if not ziel:
            return
        pal   = e.palette()
        farbe = pal.color(QtGui.QPalette.ColorRole.Highlight).name()
        treffer: list = []
        for dock in e.findChildren(QtWidgets.QDockWidget):
            titel = _kern(dock.windowTitle())
            if titel and (ziel in titel or titel in ziel):
                treffer.append(dock)
                if not dock.isVisible():
                    dock.show()
                    dock.raise_()
        for tb in e.findChildren(QtWidgets.QToolBar):
            for btn in tb.findChildren(QtWidgets.QPushButton):
                tip = _kern(btn.toolTip())
                if tip and (ziel in tip or tip in ziel):
                    treffer.append(btn)
        if not treffer:
            return
        ms = 300 if getattr(e, "_animationen_reduziert", False) else 1800
        for widget in treffer:
            orig = widget.styleSheet()
            if isinstance(widget, QtWidgets.QDockWidget):
                widget.setStyleSheet(
                    f"QDockWidget::title {{ background-color: {farbe}; }}")
                QtCore.QTimer.singleShot(ms, lambda w=widget, s=orig: w.setStyleSheet(s))
            else:
                widget.setStyleSheet(
                    orig + f"\nQPushButton {{ background-color: {farbe};"
                           f" border: 2px solid {farbe}; }}")
                QtCore.QTimer.singleShot(ms, lambda w=widget, s=orig: w.setStyleSheet(s))
