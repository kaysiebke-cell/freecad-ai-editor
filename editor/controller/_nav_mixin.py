# -*- coding: utf-8 -*-
"""Nav-Tab-Logik für WerkzeugLeiste (pure Python-Mixin, kein QObject)."""

import ast

from qt_compat import QtWidgets, QtCore, QtGui


class _NavMixin:
    """
    Mixin mit der gesamten Logik des Nav-Tabs.
    Erwartet in der konkreten Klasse: self._ed, self._lzm,
    self._nav_baum, self._zeile_edit, self._lz_view, self._ok().
    """

    def _goto_zeile(self):
        try:
            nr = int(self._zeile_edit.text()) - 1
        except ValueError:
            return
        doc = self._ed.document()
        b   = doc.findBlockByNumber(max(0, min(nr, doc.blockCount() - 1)))
        cur = QtGui.QTextCursor(b)
        self._ed.setTextCursor(cur)
        self._ed.centerCursor()
        self._ed.setFocus()

    def aktualisiere_code_baum(self, code_text: str):
        """
        Parst den Code per AST und baut den QTreeWidget-Baum live auf.
        Wird von editor.py über einen 500ms-Debounce-Timer aufgerufen.
        """
        self._nav_baum.clear()

        if not code_text.strip():
            return

        try:
            root = ast.parse(code_text)
        except SyntaxError:
            warn = QtWidgets.QTreeWidgetItem(self._nav_baum)
            warn.setText(0, "⚠  Syntax unvollständig …")
            return

        font_bold = QtGui.QFont()
        font_bold.setBold(True)

        for node in root.body:
            if isinstance(node, ast.ClassDef):
                kl = QtWidgets.QTreeWidgetItem(self._nav_baum)
                kl.setText(0, f"📦 {node.name}")
                kl.setFont(0, font_bold)
                kl.setData(0, QtCore.Qt.UserRole, node.lineno - 1)
                kl.setToolTip(0, f"Klasse  –  Zeile {node.lineno}")

                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [a.arg for a in sub.args.args if a.arg != "self"]
                        me = QtWidgets.QTreeWidgetItem(kl)
                        me.setText(0, f"  ⚙ {sub.name}({', '.join(args)})")
                        me.setData(0, QtCore.Qt.UserRole, sub.lineno - 1)
                        me.setToolTip(0, f"Methode  –  Zeile {sub.lineno}")

                kl.setExpanded(True)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                fn = QtWidgets.QTreeWidgetItem(self._nav_baum)
                fn.setText(0, f"🚀 {node.name}({', '.join(args)})")
                fn.setData(0, QtCore.Qt.UserRole, node.lineno - 1)
                fn.setToolTip(0, f"Funktion  –  Zeile {node.lineno}")

        n = self._nav_baum.topLevelItemCount()
        self._ok(f"🗂 {n} Einträge")

    def sammle_kontext_aus_baum(self) -> str:
        """Liest die Baumstruktur aus QTreeWidget als kompakten String."""
        struktur = []
        root = self._nav_baum.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            struktur.append(item.text(0).strip())
            for j in range(item.childCount()):
                struktur.append(f"  {item.child(j).text(0).strip()}")
        return "\n".join(struktur)

    def _nav_sprung_baum(self, item, _col=0):
        nr = item.data(0, QtCore.Qt.UserRole)
        if nr is not None:
            self._zeile_edit.setText(str(nr + 1))
            self._goto_zeile()

    def _lz_toggle(self):
        cur  = self._ed.textCursor()
        nr   = cur.blockNumber()
        txt  = cur.block().text()
        self._lzm.toggle(nr, txt)
        self._lz_highlight()
        st = "gesetzt" if self._lzm.hat(nr) else "entfernt"
        self._ok(f"🔖 Lesezeichen Z {nr+1} {st}")

    def _lz_sprung(self, idx):
        nr = self._lzm.data(idx, QtCore.Qt.UserRole)
        if nr is not None:
            self._zeile_edit.setText(str(nr + 1))
            self._goto_zeile()

    def _lz_nach(self):
        alle = self._lzm.alle()
        if not alle:
            return
        ak   = self._ed.textCursor().blockNumber()
        ziel = next((z for z in alle if z > ak), alle[0])
        self._zeile_edit.setText(str(ziel + 1))
        self._goto_zeile()

    def _lz_vor(self):
        alle = self._lzm.alle()
        if not alle:
            return
        ak   = self._ed.textCursor().blockNumber()
        ziel = next((z for z in reversed(alle) if z < ak), alle[-1])
        self._zeile_edit.setText(str(ziel + 1))
        self._goto_zeile()
