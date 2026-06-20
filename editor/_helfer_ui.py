# -*- coding: utf-8 -*-
"""UI-Komponenten für den FreeCAD-Helfer: Diff-Blase, Chat-Blase, Bild-Vorschau."""

import difflib
import html

from core.qt_compat import QtCore, QtWidgets, QtGui
from core import theme


# ── Diff-Berechnung ───────────────────────────────────────────────────────────

def berechne_diff_html(original: str, korrigiert: str, widget: QtWidgets.QWidget) -> str:
    pal    = widget.palette()
    dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
    rot    = QtGui.QColor.fromHsl(4,  210, 80 if dunkel else 45).name()
    gruen  = QtGui.QColor.fromHsl(130, 180, 80 if dunkel else 40).name()

    w_orig = original.split()
    w_korr = korrigiert.split()
    matcher = difflib.SequenceMatcher(None, w_orig, w_korr, autojunk=False)
    teile   = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            teile.append(html.escape(" ".join(w_orig[i1:i2])))
        elif tag == "replace":
            for w in w_orig[i1:i2]:
                teile.append(
                    f'<span style="color:{rot};text-decoration:line-through;">'
                    f'{html.escape(w)}</span>')
            for w in w_korr[j1:j2]:
                teile.append(
                    f'<span style="color:{gruen};font-weight:bold;">'
                    f'{html.escape(w)}</span>')
        elif tag == "delete":
            for w in w_orig[i1:i2]:
                teile.append(
                    f'<span style="color:{rot};text-decoration:line-through;">'
                    f'{html.escape(w)}</span>')
        elif tag == "insert":
            for w in w_korr[j1:j2]:
                teile.append(
                    f'<span style="color:{gruen};font-weight:bold;">'
                    f'{html.escape(w)}</span>')
    return " ".join(teile)


# ── Diff-Blase ────────────────────────────────────────────────────────────────

class DiffBlase(QtWidgets.QFrame):
    def __init__(self, original: str, korrigiert: str, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        kopf = QtWidgets.QLabel("✏️ Deine Korrekturen:")
        kopf.setStyleSheet(theme.STY_HELFER_BLASE_KOPF())
        layout.addWidget(kopf)

        self._lbl = QtWidgets.QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setTextFormat(QtCore.Qt.RichText)
        self._lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(self._lbl)

        self._original   = original
        self._korrigiert = korrigiert
        QtCore.QTimer.singleShot(50, self._render)

    def _render(self):
        diff = berechne_diff_html(self._original, self._korrigiert, self)
        self._lbl.setText(diff)
        pal    = self.palette()
        dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
        bg     = QtGui.QColor.fromHsl(50, 60, 40 if dunkel else 220)
        fg     = pal.color(QtGui.QPalette.WindowText)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg.name()}; border-radius: 8px; }}")
        self._lbl.setStyleSheet(theme.STY_HELFER_DIFF_TEXT(fg.name()))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.PaletteChange:
            self._render()
        super().changeEvent(event)


# ── Chat-Blase ────────────────────────────────────────────────────────────────

class ChatBubble(QtWidgets.QFrame):
    def __init__(self, text: str, rolle: str, parent=None):
        super().__init__(parent)
        self._rolle = rolle
        self._text  = text

        outer = QtWidgets.QHBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(8)

        avatar = QtWidgets.QLabel("🤖" if rolle == "ki" else "🧑")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(QtCore.Qt.AlignCenter)
        outer.addWidget(avatar) if rolle == "ki" else outer.addSpacing(40)

        bubble = QtWidgets.QFrame()
        blay   = QtWidgets.QVBoxLayout(bubble)
        blay.setContentsMargins(12, 8, 12, 8)
        blay.setSpacing(4)

        self._lbl = QtWidgets.QLabel(text)
        self._lbl.setWordWrap(True)
        self._lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        blay.addWidget(self._lbl)

        if rolle == "ki":
            self._copy_btn = QtWidgets.QPushButton("📋  Kopieren")
            self._copy_btn.setVisible(bool(text))
            self._copy_btn.clicked.connect(self._kopieren)
            blay.addWidget(self._copy_btn)
        else:
            self._copy_btn = None

        outer.addWidget(bubble, 1)
        outer.addWidget(avatar) if rolle == "nutzer" else outer.addSpacing(40)

        self._bubble = bubble
        self._aktualisiere_farben()

    def _aktualisiere_farben(self):
        pal    = self.palette()
        base   = pal.color(QtGui.QPalette.Base)
        dunkel = base.lightness() < 128
        if self._rolle == "ki":
            hue, sat, lit_d, lit_h = 220, 80, 45, 210
        else:
            hue, sat, lit_d, lit_h = 260, 60, 50, 205
        lit = lit_d if dunkel else lit_h
        bg  = QtGui.QColor.fromHsl(hue, sat, lit)
        fg  = pal.color(QtGui.QPalette.WindowText)
        self._bubble.setStyleSheet(
            f"QFrame {{ background-color: {bg.name()}; border-radius: 10px; }}")
        self._lbl.setStyleSheet(theme.STY_HELFER_BUBBLE_TEXT(fg.name()))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.PaletteChange:
            self._aktualisiere_farben()
        super().changeEvent(event)

    def append(self, chunk: str):
        self._text += chunk
        self._lbl.setText(self._text)

    def finalize(self):
        if self._copy_btn:
            self._copy_btn.setVisible(True)

    def _kopieren(self):
        QtWidgets.QApplication.clipboard().setText(self._text)
        self._copy_btn.setText("✅  Kopiert!")
        QtCore.QTimer.singleShot(
            2500, lambda: self._copy_btn.setText("📋  Kopieren"))


# ── Bild-Vorschau ─────────────────────────────────────────────────────────────

class BildVorschau(QtWidgets.QFrame):
    """Zeigt das angehängte Bild als Thumbnail mit Entfernen-Button."""

    entfernt = QtCore.Signal()

    def __init__(self, pixmap: QtGui.QPixmap, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        thumb = QtWidgets.QLabel()
        thumb.setFixedSize(72, 72)
        thumb.setAlignment(QtCore.Qt.AlignCenter)
        thumb.setPixmap(pixmap.scaled(
            72, 72,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation))
        layout.addWidget(thumb)

        rechts = QtWidgets.QVBoxLayout()
        rechts.setSpacing(4)

        info = QtWidgets.QLabel(f"📎  {pixmap.width()} × {pixmap.height()} px")
        info.setStyleSheet(theme.STY_HELFER_BLASE_KOPF())
        rechts.addWidget(info)

        entf = QtWidgets.QPushButton("✕  Bild entfernen")
        entf.setFixedHeight(26)
        entf.setToolTip("Angehängtes Bild entfernen")
        entf.clicked.connect(self.entfernt)
        rechts.addWidget(entf)
        rechts.addStretch()

        layout.addLayout(rechts)
        layout.addStretch()

        self._aktualisiere_rahmen()

    def _aktualisiere_rahmen(self):
        pal    = self.palette()
        dunkel = pal.color(QtGui.QPalette.Base).lightness() < 128
        bg     = QtGui.QColor.fromHsl(200, 60, 38 if dunkel else 230)
        rand   = pal.color(QtGui.QPalette.Mid)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg.name()}; "
            f"border: 1px solid {rand.name()}; border-radius: 8px; }}")

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.PaletteChange:
            self._aktualisiere_rahmen()
        super().changeEvent(event)
