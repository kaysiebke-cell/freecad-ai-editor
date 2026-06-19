# -*- coding: utf-8 -*-
"""Schrift-Konfiguration und Widget-Stabilisierungs-Funktionen."""

from qt_compat import QtWidgets, QtCore, QtGui
import schrift

_FONT_UI_FAMILY   = schrift.FAMILIE_UI
_FONT_MONO_FAMILY = schrift.FAMILIE_MONO
_FONT_UI_SIZE     = schrift.pt(schrift.STUFE_BASE)
_FONT_MONO_SIZE   = schrift.pt(schrift.STUFE_BASE)


def _wrap_emoji(f: QtGui.QFont) -> QtGui.QFont:
    try:
        from main import emoji_font
        return emoji_font(f)
    except Exception:
        return f


def ui_font() -> QtGui.QFont:
    """Gibt die Standard-UI-Schrift zurück, fluid-skaliert, Emoji-sicher."""
    return _wrap_emoji(schrift.ui_font())


def mono_font() -> QtGui.QFont:
    """Gibt die Monospace-Schrift zurück, fluid-skaliert, Emoji-sicher."""
    return _wrap_emoji(schrift.mono_font())


def apply_global_font(widget: QtWidgets.QWidget) -> None:
    """Setzt die UI-Schrift auf das Widget. Im Konstruktor als erstes aufrufen."""
    widget.setFont(ui_font())


def stabilize_label(label: QtWidgets.QLabel) -> None:
    """Verhindert Blocksatz und vertikales Auseinanderreißen bei QLabel."""
    label.setFont(ui_font())
    label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    label.setWordWrap(True)
    label.setSizePolicy(
        QtWidgets.QSizePolicy.Preferred,
        QtWidgets.QSizePolicy.Preferred,
    )


def stabilize_text_editor(editor: QtWidgets.QPlainTextEdit) -> None:
    """
    Macht einen QPlainTextEdit bombensicher gegen Qt-Blocksatz.
    Aufrufen NACHDEM setPlainText() gesetzt wurde.
    """
    editor.setFont(mono_font())

    _txt_opt = editor.document().defaultTextOption()
    _txt_opt.setAlignment(QtCore.Qt.AlignLeft)
    _txt_opt.setWrapMode(QtGui.QTextOption.WordWrap)
    editor.document().setDefaultTextOption(_txt_opt)

    _bfmt = QtGui.QTextBlockFormat()
    _bfmt.setAlignment(QtCore.Qt.AlignLeft)
    _cur = editor.textCursor()
    _cur.select(QtGui.QTextCursor.Document)
    _cur.mergeBlockFormat(_bfmt)
    _cur.clearSelection()
    editor.setTextCursor(_cur)

    editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
    editor.setFrameShape(QtWidgets.QFrame.NoFrame)
    editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    editor.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
    editor.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding,
        QtWidgets.QSizePolicy.Fixed,
    )


def calc_plain_text_height(
    font: QtGui.QFont,
    text: str,
    doc_margin: int = 8,
) -> int:
    """Pixelgenaue Fixed-Höhe für einen QPlainTextEdit (Zeilenanzahl × lineSpacing + Ränder)."""
    fm = QtGui.QFontMetrics(font)
    n_zeilen = text.count("\n") + 1
    return fm.lineSpacing() * n_zeilen + doc_margin * 2 + 4
