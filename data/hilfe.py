# -*- coding: utf-8 -*-
"""
hilfe.py
────────
HilfeTab – aufklappbare Hilfe-Dokumentation als QWidget.

Texte werden aus hilfe_texte.py importiert.

Verwendung:
    from hilfe import HilfeTab
    left_tabs.addTab(HilfeTab(), "❓ Hilfe")
"""

from qt_compat import QtWidgets, QtCore, QtGui
import theme
import schrift
from hilfe_texte import HILFE_ABSCHNITTE


class HilfeTab(QtWidgets.QWidget):
    """Aufklappbare Hilfe-Dokumentation als eigenständiges QWidget."""

    _FARBEN: list[tuple[str, str, str]] = [
        ("⚠",          "", ""),
        ("📦 Install",  "", ""),
        ("🔧",          "", ""),
        ("✂️",          "", ""),
        ("🎨",          "", ""),
    ]
    _FARBE_DEFAULT = ("", "")

    _STY_BODY = theme.STY_HILFE_BODY

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui_font = QtGui.QFont("Ubuntu", 10)
        try:
            from main import emoji_font
            self._ui_font = emoji_font(self._ui_font)
        except Exception:
            pass
        self.setFont(self._ui_font)
        self.setObjectName("HilfeTab")
        self.setStyleSheet(theme.STY_HILFE_TAB)
        self._mono_font = QtGui.QFont("Courier New", 10)
        try:
            from main import emoji_font
            self._mono_font = emoji_font(self._mono_font)
        except Exception:
            pass
        self._alle_widgets: list = []
        self._baue_ui()

    def _baue_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        such_zeile = QtWidgets.QHBoxLayout()
        icon = QtWidgets.QLabel("🔍")
        icon.setFont(self._ui_font)
        icon.setStyleSheet(theme.STY_ICON_BTN_BORDERLESS(schrift.pt(schrift.STUFE_XL)))
        such_zeile.addWidget(icon)
        self._suche = QtWidgets.QLineEdit()
        self._suche.setFont(self._ui_font)
        self._suche.setPlaceholderText("Hilfe durchsuchen …")
        self._suche.setClearButtonEnabled(True)
        self._suche.setStyleSheet(theme.STY_HILFE_SUCHE)
        such_zeile.addWidget(self._suche)
        layout.addLayout(such_zeile)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(container)
        vbox.setContentsMargins(2, 2, 2, 8)
        vbox.setSpacing(3)

        for titel, inhalt in HILFE_ABSCHNITTE:
            akzent, bg = self._akzent(titel)
            vbox.addWidget(self._baue_abschnitt(titel, inhalt, akzent, bg))

        vbox.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        ver = QtWidgets.QLabel("FreeCAD MultiAI Panel  •  v1.0.0")
        ver.setFont(self._ui_font)
        ver.setAlignment(QtCore.Qt.AlignCenter)
        ver.setStyleSheet(theme.STY_VORSCHAU_STATUS(schrift.pt(schrift.STUFE_SM)))
        layout.addWidget(ver)

        self._suche.textChanged.connect(self._filtern)

    def _baue_abschnitt(self, titel: str, inhalt: str,
                        akzent: str, bg: str) -> QtWidgets.QWidget:
        abschnitt = QtWidgets.QWidget()
        av = QtWidgets.QVBoxLayout(abschnitt)
        av.setContentsMargins(0, 0, 0, 0)
        av.setSpacing(0)

        btn = QtWidgets.QPushButton(f"▶  {titel.replace('&', '&&')}")
        btn.setCheckable(True)
        btn.setFont(self._ui_font)
        btn.setStyleSheet(theme.STY_SECTION_HEAD_BTN(schrift.pt(schrift.STUFE_LG)))

        # QLabel statt QPlainTextEdit: heightForWidth() regelt Höhe automatisch,
        # kein manueller setFixedHeight-Hack nötig.
        lbl = QtWidgets.QLabel()
        lbl.setFont(self._mono_font)
        lbl.setWordWrap(True)
        lbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        lbl.setText(inhalt)
        lbl.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        lbl.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
            | QtCore.Qt.TextSelectableByKeyboard)
        lbl.setStyleSheet(self._STY_BODY)
        lbl.setVisible(False)

        def _toggle(checked, b=btn, l=lbl):
            l.setVisible(checked)
            b.setText(("▼" if checked else "▶") + b.text()[1:])

        btn.toggled.connect(_toggle)
        av.addWidget(btn)
        av.addWidget(lbl)
        self._alle_widgets.append(
            (abschnitt, btn, lbl, titel.lower(), inhalt.lower()))
        return abschnitt

    def _akzent(self, titel: str) -> tuple[str, str]:
        for prefix, farbe, bg in self._FARBEN:
            if titel.startswith(prefix):
                return farbe, bg
        return self._FARBE_DEFAULT

    def _filtern(self, text: str):
        begriffe = text.lower().split()
        for abschnitt, btn, lbl, titel_l, inhalt_l in self._alle_widgets:
            if not begriffe:
                abschnitt.setVisible(True)
                btn.setChecked(False)
            else:
                treffer = all(b in titel_l or b in inhalt_l for b in begriffe)
                abschnitt.setVisible(treffer)
                if treffer:
                    btn.setChecked(True)
