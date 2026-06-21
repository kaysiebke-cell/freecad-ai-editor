# -*- coding: utf-8 -*-
"""
toolbar_builder.py
──────────────────
Baut die Panel-Toolbar (Toggle-Buttons für alle Dock-Panels) des MakroEditors auf.
Aufgerufen einmalig aus MakroEditor.__init__.
"""

from core.qt_compat import QtWidgets, QtCore

from core import theme
from core import schrift


def init_toolbar(editor) -> None:
    """Erstellt die Panel-Toolbar und verbindet alle Toggle-Buttons mit ihren Docks."""
    _L = QtCore.Qt.LeftDockWidgetArea
    _R = QtCore.Qt.RightDockWidgetArea
    _B = QtCore.Qt.BottomDockWidgetArea

    editor._dock_werkzeuge = editor._make_dock(
        "🔧  Werkzeuge", "dock_werkzeuge", _R, editor._werkzeug_leiste)
    editor.tabifyDockWidget(editor._dock_akt, editor._dock_werkzeuge)

    for _d in (editor._dock_cfg, editor._dock_ki, editor._dock_snip,
               editor._dock_hints, editor._dock_files, editor._dock_kitools,
               editor._dock_akt, editor._dock_bib, editor._dock_werkzeuge,
               editor._dock_fehler):
        _d.hide()

    _tb = QtWidgets.QToolBar("Panels", editor)
    _tb.setObjectName("toolbar_panels")
    _tb.setMovable(False)
    _tb.setFloatable(False)
    _tb.setStyleSheet(theme.STY_TOOLBAR)
    editor.addToolBar(QtCore.Qt.TopToolBarArea, _tb)

    _fs = schrift.pt(schrift.STUFE_BASE)
    editor._panel_btns           = []
    editor._panel_btns_optional  = []
    editor._animationen_reduziert = False
    editor._tastatur_shortcuts   = []

    def _panel_btn(dock, icon_text, label, standard_area=_L, optional=False):
        btn = QtWidgets.QPushButton(icon_text)
        btn.setToolTip(label)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setFixedHeight(theme.TOOLBAR_PANEL_BTN_HOEHE)
        btn.setFixedWidth(theme.TOOLBAR_PANEL_BTN_BREITE)
        editor._panel_btns.append((btn, icon_text, label))
        if optional:
            editor._panel_btns_optional.append(btn)
        btn.setStyleSheet(theme.STY_PANEL_BTN(_fs))

        def _on_click(checked, d=dock, a=standard_area):
            if checked:
                editor._zeige_panel(d, a)
            else:
                d.hide()

        btn.toggled.connect(_on_click)
        def _sync_btn(vis, b=btn):
            b.blockSignals(True)
            b.setChecked(vis)
            b.blockSignals(False)
        dock.visibilityChanged.connect(_sync_btn)
        _tb.addWidget(btn)
        return btn

    _tb.addSeparator()
    _panel_btn(editor._dock_cfg,       "⚙",  "Einst.",       _L)
    _panel_btn(editor._dock_ki,        "🤖", "KI",            _L)
    _panel_btn(editor._dock_akt,       "🎛", "Akt.",          _R)
    _panel_btn(editor._dock_snip,      "📦", "Snip",          _L, optional=True)
    _panel_btn(editor._dock_hints,     "💡", "API",           _L, optional=True)
    _panel_btn(editor._dock_files,     "📂", "Dat.",          _L, optional=True)
    _panel_btn(editor._dock_kitools,   "🛠", "Tools",         _R, optional=True)
    _panel_btn(editor._dock_bib,       "📚", "Bib.",          _R, optional=True)
    _panel_btn(editor._dock_werkzeuge, "🔧", "Werkz.",        _R, optional=True)
    _panel_btn(editor._dock_fehler,    "⚠",  "Fehler",        _B)
    editor._btn_bf_gruppe = _panel_btn(editor._dock_bf_gruppe, "♿", "Hilfe+Zugang", _R)

    from ui.barrierefreiheit import _get_bool as _bf_bool
    if _bf_bool("BF_IconText", False):
        for _pb, _ico, _lbl in editor._panel_btns:
            _pb.setText(f"{_ico}  {_lbl}")
            _pb.setMinimumWidth(44)
            _pb.setMaximumWidth(16777215)
    if _bf_bool("BF_EinfacheAnsicht", False):
        for _pb in editor._panel_btns_optional:
            _pb.setVisible(False)
    if _bf_bool("BF_AnimationReduzieren", False):
        editor._animationen_reduziert = True
    if _bf_bool("BF_TooltipsImmer", False):
        QtCore.QTimer.singleShot(
            500, lambda: editor._on_barrierefreiheit("tooltips_immer", True))
    if _bf_bool("BF_Tastaturmodus", False):
        QtCore.QTimer.singleShot(
            500, lambda: editor._on_barrierefreiheit("tastaturmodus", True))
