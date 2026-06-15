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

    _STY_BODY = (
        "QPlainTextEdit{"
        " "
        f"font-family:'Courier New', monospace; font-size:{schrift.pt(schrift.STUFE_BASE)}pt;"
        "text-align:left;"
        "border-radius:0 0 4px 4px;"
        "border:1px solid ; border-top:none;}"
    )

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
        self.setStyleSheet(
            "#HilfeTab QLabel, #HilfeTab QPushButton,"
            "#HilfeTab QLineEdit, #HilfeTab QScrollArea {"
            "  font-family: 'Ubuntu'; text-align: left; }"
            "#HilfeTab QPlainTextEdit {"
            "  font-family: 'Courier New', monospace; text-align: left; }"
        )
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
        icon.setStyleSheet(f"font-size:{schrift.pt(schrift.STUFE_XL)}pt; font-family:'Ubuntu','Noto Color Emoji';")
        such_zeile.addWidget(icon)
        self._suche = QtWidgets.QLineEdit()
        self._suche.setFont(self._ui_font)
        self._suche.setPlaceholderText("Hilfe durchsuchen …")
        self._suche.setClearButtonEnabled(True)
        self._suche.setStyleSheet(
            "QLineEdit{"
            "border:1px solid ;border-radius:3px;padding:3px;}")
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

        ver = QtWidgets.QLabel("KI-Makro-Editor  •  v1.1")
        ver.setFont(self._ui_font)
        ver.setAlignment(QtCore.Qt.AlignCenter)
        ver.setStyleSheet(f"font-size:{schrift.pt(schrift.STUFE_SM)}pt;padding-top:4px;")
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
        btn.setStyleSheet(
            f"QPushButton{{text-align:left; padding:5px 8px;"
            f"font-family:'Ubuntu','Noto Color Emoji';"
            f"font-size:{schrift.pt(schrift.STUFE_LG)}pt; font-weight:bold;"
            f"border:none; border-radius:4px;"
            f"QPushButton:hover{{}}"
            f"QPushButton:pressed{{}}")

        lbl = QtWidgets.QPlainTextEdit()
        lbl.setFont(self._mono_font)
        lbl.setReadOnly(True)

        _txt_opt = lbl.document().defaultTextOption()
        _txt_opt.setAlignment(QtCore.Qt.AlignLeft)
        _txt_opt.setWrapMode(QtGui.QTextOption.WordWrap)
        lbl.document().setDefaultTextOption(_txt_opt)
        lbl.setPlainText(inhalt)

        _bfmt = QtGui.QTextBlockFormat()
        _bfmt.setAlignment(QtCore.Qt.AlignLeft)
        _cur = lbl.textCursor()
        _cur.select(QtGui.QTextCursor.Document)
        _cur.mergeBlockFormat(_bfmt)
        _cur.clearSelection()
        lbl.setTextCursor(_cur)

        lbl.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        lbl.setFrameShape(QtWidgets.QFrame.NoFrame)
        lbl.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        lbl.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        lbl.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        fm = QtGui.QFontMetrics(self._mono_font)
        n_zeilen  = inhalt.count('\n') + 1
        _DOC_MARGIN = 8
        lbl.setFixedHeight(fm.lineSpacing() * n_zeilen + _DOC_MARGIN * 2 + 4)
        lbl.setStyleSheet(self._STY_BODY)
        lbl.document().setDocumentMargin(_DOC_MARGIN)
        lbl.setVisible(False)
        lbl.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
            | QtCore.Qt.TextSelectableByKeyboard)

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
