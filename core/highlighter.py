# -*- coding: utf-8 -*-
from qt_compat import QtGui, QtCore
import theme


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """
    Syntax-Highlighter für Python.
    Farben werden bei jedem rehighlight() neu aus theme.syntax_farben() geladen
    – passt sich automatisch an Hell- und Dunkel-Modus an.
    """

    def __init__(self, dokument):
        super().__init__(dokument)
        self._regeln = []
        self._letztes_dunkel: bool | None = None
        self._aufbau()

    # ── Hilfsmethode: Format erzeugen ─────────────────────────────────────────
    @staticmethod
    def _fmt(farbe: QtGui.QColor, fett=False, kursiv=False) -> QtGui.QTextCharFormat:
        f = QtGui.QTextCharFormat()
        f.setForeground(farbe)
        if fett:   f.setFontWeight(QtGui.QFont.Bold)
        if kursiv: f.setFontItalic(True)
        return f

    def aktualisiere_theme(self):
        """Prüft ob sich das Theme geändert hat und baut Regeln neu auf."""
        from qt_compat import QtWidgets, QtGui as _QtGui
        app = QtWidgets.QApplication.instance()
        pal = app.palette() if app else _QtGui.QPalette()
        dunkel = theme.ist_dunkel()
        if dunkel != self._letztes_dunkel:
            self._letztes_dunkel = dunkel
            self._aufbau()
            self.rehighlight()

    # ── Regeln aufbauen ───────────────────────────────────────────────────────
    def _aufbau(self):
        farben, text_farbe = theme.syntax_farben()

        # Standard-Textfarbe als Format speichern – wird in highlightBlock()
        # zuerst auf die gesamte Zeile angewendet, bevor Syntax-Regeln greifen.
        # So überschreibt FreeCADs globales QSS die Textfarbe nicht mehr.
        self._default_fmt = self._fmt(text_farbe)

        self._regeln = []
        R = self._regeln
        F = self._fmt
        _FARBEN = farben

        # Keywords
        R.append((QtCore.QRegularExpression(
            r"\b(?:False|None|True|and|as|assert|async|await|break|class|"
            r"continue|def|del|elif|else|except|finally|for|from|global|if|"
            r"import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|"
            r"while|with|yield)\b"),
            F(_FARBEN["keyword"], fett=True)))

        # Builtins
        R.append((QtCore.QRegularExpression(
            r"\b(?:abs|all|any|bool|bytes|dict|enumerate|filter|float|"
            r"format|getattr|hasattr|int|isinstance|len|list|map|max|min|"
            r"next|object|open|print|range|repr|reversed|set|setattr|sorted|"
            r"str|sum|super|tuple|type|vars|zip|input|id|hex|bin|oct|"
            r"callable|chr|ord|hash|iter|pow|round|divmod|eval|exec|"
            r"compile|globals|locals|dir|vars|help|property|staticmethod|"
            r"classmethod)\b"),
            F(_FARBEN["builtin"])))

        # self / cls
        R.append((QtCore.QRegularExpression(r"\b(?:self|cls)\b"),
                  F(_FARBEN["self"], kursiv=True)))

        # Dekoratoren
        R.append((QtCore.QRegularExpression(r"@[\w.]+"),
                  F(_FARBEN["decorator"])))

        # Funktionsname nach def
        R.append((QtCore.QRegularExpression(r"(?<=\bdef\s)\w+"),
                  F(_FARBEN["def_name"])))

        # Klassenname nach class
        R.append((QtCore.QRegularExpression(r"(?<=\bclass\s)\w+"),
                  F(_FARBEN["class_name"], fett=True)))

        # Zahlen (hex, float, int)
        R.append((QtCore.QRegularExpression(
            r"\b(?:0x[0-9A-Fa-f]+|0b[01]+|0o[0-7]+"
            r"|[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?)\b"),
            F(_FARBEN["zahl"])))

        # Einfache Strings (einzeilig) – ' und "
        R.append((QtCore.QRegularExpression(
            r"""(?:f|b|r|rb|br|u)?'(?:[^'\\]|\\.)*'"""
            r"""|(?:f|b|r|rb|br|u)?"(?:[^"\\]|\\.)*\""""),
            F(_FARBEN["string"])))

        # Operatoren
        R.append((QtCore.QRegularExpression(
            r"[+\-*/%&|^~<>=!:,\.]+"),
            F(_FARBEN["operator"])))

        # Kommentare – werden zuletzt gesetzt (überschreiben alles)
        self._kommentar_re  = QtCore.QRegularExpression(r"#[^\n]*")
        self._kommentar_fmt = F(_FARBEN["kommentar"], kursiv=True)

        # Triple-String-Formate für Multiline
        self._triple_fmt = F(_FARBEN["triple"])
        self._triple_re_start = [
            QtCore.QRegularExpression(r'"""'),
            QtCore.QRegularExpression(r"'''"),
        ]

    # ── Einzeilige Regeln anwenden ────────────────────────────────────────────
    def highlightBlock(self, text: str):
        # 0) Prüfen ob sich Hell/Dunkel geändert hat – ggf. Farben neu aufbauen.
        #    Wird hier inline geprüft (nicht via aktualisiere_theme), damit kein
        #    rehighlight() mitten im laufenden Zyklus ausgelöst wird.
        dunkel = theme.ist_dunkel()
        if dunkel != self._letztes_dunkel:
            self._letztes_dunkel = dunkel
            self._aufbau()

        # 1) Gesamte Zeile mit der Modus-korrekten Standard-Textfarbe belegen,
        #    damit FreeCADs globales QSS die Textfarbe nicht überschreibt.
        if text:
            self.setFormat(0, len(text), self._default_fmt)

        # 2) Einzeilige Regeln
        for regex, fmt in self._regeln:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

        # 3) Kommentare (überschreiben vorherige Highlights)
        it = self._kommentar_re.globalMatch(text)
        while it.hasNext():
            m = it.next()
            self.setFormat(m.capturedStart(), m.capturedLength(),
                           self._kommentar_fmt)

        # 4) Triple-Strings (Multiline – State 1 = """, State 2 = ''')
        self._handle_triple(text, '"""', 1)
        self._handle_triple(text, "'''", 2)

    def _handle_triple(self, text: str, delim: str, state_id: int):
        re_delim = QtCore.QRegularExpression(QtCore.QRegularExpression.escape(delim))
        in_block = (self.previousBlockState() == state_id)
        idx = 0

        while True:
            m = re_delim.match(text, idx)
            if not m.hasMatch():
                if in_block:
                    self.setFormat(idx, len(text) - idx, self._triple_fmt)
                    self.setCurrentBlockState(state_id)
                break
            pos = m.capturedStart()
            if in_block:
                self.setFormat(idx, pos - idx + len(delim), self._triple_fmt)
                in_block = False
                idx = pos + len(delim)
            else:
                in_block = True
                idx = pos + len(delim)
