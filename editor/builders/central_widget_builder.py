# -*- coding: utf-8 -*-
"""
central_widget_builder.py
─────────────────────────
Baut das zentrale Widget (Tab-Leiste + Schnellsuche-Leiste) des MakroEditors auf.
Aufgerufen einmalig aus MakroEditor.__init__.
"""

from core.qt_compat import QtWidgets, QtGui
from core import theme
from core import schrift


def init_central_widget(editor) -> None:
    """Erstellt zentrales Widget, Suche-Leiste und Statusbar und setzt sie am editor."""

    def mkbtn(label, tip, slot, w=None, h=28):
        b = QtWidgets.QPushButton(label)
        b.setToolTip(tip)
        b.setMinimumHeight(h)
        if w:
            b.setFixedWidth(w)
        b.clicked.connect(slot)
        return b

    editor._suche_widget = QtWidgets.QWidget()
    sl = QtWidgets.QHBoxLayout(editor._suche_widget)
    sl.setContentsMargins(4, 2, 4, 2)
    sl.setSpacing(6)
    sl.addWidget(QtWidgets.QLabel("Suche:"))
    editor._suche_feld = QtWidgets.QLineEdit()
    editor._suche_feld.setPlaceholderText("Suchen (Enter = weiter) …")
    editor._suche_feld.returnPressed.connect(editor._suche_weiter)
    sl.addWidget(editor._suche_feld)
    sl.addWidget(QtWidgets.QLabel("Ersetzen:"))
    editor._ersatz_feld = QtWidgets.QLineEdit()
    editor._ersatz_feld.setPlaceholderText("Ersatztext …")
    sl.addWidget(editor._ersatz_feld)
    for lbl, tip, slot in [("→", "Weiter", editor._suche_weiter),
                            ("✍", "Ersetzen", editor._ersetzen_text),
                            ("Alle", "Alle ersetzen", editor._alles_ersetzen)]:
        sl.addWidget(mkbtn(lbl, tip, slot, h=26))
    _bx = QtWidgets.QPushButton("✕")
    _bx.setFixedWidth(26)
    _bx.setToolTip("Suche schließen (Esc)")
    _bx.clicked.connect(lambda: editor._suche_widget.setVisible(False))
    sl.addWidget(_bx)
    editor._suche_widget.setVisible(False)

    _sc_suche = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F"), editor)
    _sc_suche.activated.connect(editor._toggle_suche)

    editor._tabs = []
    editor._editor = None
    editor._editor_tab_widget = QtWidgets.QTabWidget()
    editor._editor_tab_widget.setTabsClosable(True)
    editor._editor_tab_widget.setMovable(True)
    editor._editor_tab_widget.setDocumentMode(True)
    editor._editor_tab_widget.setStyleSheet(
        theme.STY_EDITOR_TABS(schrift.pt(schrift.STUFE_BASE)))
    editor._editor_tab_widget.tabCloseRequested.connect(editor._tab_schliessen)
    editor._editor_tab_widget.currentChanged.connect(editor._tab_gewechselt)

    central = QtWidgets.QWidget()
    _cl = QtWidgets.QVBoxLayout(central)
    _cl.setContentsMargins(0, 0, 0, 0)
    _cl.setSpacing(0)
    _cl.addWidget(editor._editor_tab_widget, stretch=1)
    _cl.addWidget(editor._suche_widget)
    editor.setCentralWidget(central)

    editor._status = QtWidgets.QLabel("Bereit.")
    editor._status.setStyleSheet(
        theme.STY_STATUS_LABEL(schrift.pt(schrift.STUFE_BASE)))
    editor.statusBar().addWidget(editor._status, stretch=1)
    editor.statusBar().setSizeGripEnabled(True)
