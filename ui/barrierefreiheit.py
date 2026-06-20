# -*- coding: utf-8 -*-
"""
barrierefreiheit.py – Barrierefreiheits-Einstellungen für den KI-Makro-Editor.

Bereiche:
  1. Sehschwäche      – Schriftgröße, Kontrast, Icon-Beschriftung
  2. Motorik          – Button-Größe, Tastaturmodus, einfache Ansicht
  3. Einfache Sprache – KI antwortet einfach, Fachbegriffe erklären
  4. Allgemein        – Animationen, Tooltips immer sichtbar
"""

from core.qt_compat import QtWidgets, QtCore
from core import theme
from core import schrift

# ── Einstellungs-Schlüssel (werden in FreeCAD-Parametern gespeichert) ─────────
try:
    import FreeCAD as App
    def _get_bool(key, default=False):
        return App.ParamGet("User parameter:BaseApp/Preferences/Macros").GetBool(key, default)
    def _set_bool(key, val):
        App.ParamGet("User parameter:BaseApp/Preferences/Macros").SetBool(key, val)
    def _get_int(key, default=0):
        return App.ParamGet("User parameter:BaseApp/Preferences/Macros").GetInt(key, default)
    def _set_int(key, val):
        App.ParamGet("User parameter:BaseApp/Preferences/Macros").SetInt(key, val)
except Exception:
    # Außerhalb FreeCAD: in-memory Fallback
    _store: dict = {}
    def _get_bool(key, default=False): return _store.get(key, default)
    def _set_bool(key, val): _store[key] = val
    def _get_int(key, default=0): return _store.get(key, default)
    def _set_int(key, val): _store[key] = val


# ── Hilfsfunktion: Abschnitts-Label ───────────────────────────────────────────
def _abschnitt(text: str) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet(theme.STY_ABSCHNITT_LABEL_LG(schrift.pt(schrift.STUFE_LG)))
    return lbl


# ── Haupt-Widget ───────────────────────────────────────────────────────────────
class BarrierefreiheitPanel(QtWidgets.QWidget):

    # Signal – andere Teile der App können auf Änderungen reagieren
    geaendert = QtCore.Signal(str, object)  # (schluessel, wert)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # ── 1. SEHSCHWÄCHE ────────────────────────────────────────────────────
        layout.addWidget(_abschnitt("👁  Sehschwäche"))

        # Schriftgröße UI
        _r_schrift = QtWidgets.QHBoxLayout()
        _r_schrift.addWidget(QtWidgets.QLabel("UI-Schriftgröße:"))
        self._schrift_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._schrift_slider.setRange(8, 24)
        self._schrift_slider.setValue(_get_int("BF_SchriftGroesse", schrift.pt()))
        self._schrift_slider.setTickInterval(2)
        self._schrift_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self._schrift_lbl = QtWidgets.QLabel(f"{self._schrift_slider.value()} pt")
        self._schrift_lbl.setFixedWidth(36)
        _r_schrift.addWidget(self._schrift_slider, stretch=1)
        _r_schrift.addWidget(self._schrift_lbl)
        layout.addLayout(_r_schrift)
        self._schrift_slider.valueChanged.connect(self._on_schrift)

        # Editor-Schriftgröße
        _r_editor = QtWidgets.QHBoxLayout()
        _r_editor.addWidget(QtWidgets.QLabel("Editor-Schriftgröße:"))
        self._editor_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._editor_slider.setRange(8, 24)
        self._editor_slider.setValue(_get_int("BF_EditorSchrift", 10))
        self._editor_slider.setTickInterval(2)
        self._editor_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self._editor_lbl = QtWidgets.QLabel(f"{self._editor_slider.value()} pt")
        self._editor_lbl.setFixedWidth(36)
        _r_editor.addWidget(self._editor_slider, stretch=1)
        _r_editor.addWidget(self._editor_lbl)
        layout.addLayout(_r_editor)
        self._editor_slider.valueChanged.connect(self._on_editor_schrift)

        # Hoher Kontrast
        self._kontrast_cb = QtWidgets.QCheckBox("Hoher Kontrast (stärkere Farben)")
        self._kontrast_cb.setToolTip(
            "Erhöht den Kontrast aller UI-Elemente deutlich.\n"
            "Nützlich bei Sehschwäche oder schwachem Bildschirm.")
        self._kontrast_cb.setChecked(_get_bool("BF_HoherKontrast", False))
        self._kontrast_cb.toggled.connect(
            lambda v: (self._speichere("BF_HoherKontrast", v),
                       self.geaendert.emit("kontrast", v)))
        layout.addWidget(self._kontrast_cb)

        # Icons mit Text
        self._icon_text_cb = QtWidgets.QCheckBox("Icons immer mit Text beschriften")
        self._icon_text_cb.setToolTip(
            "Zeigt neben jedem Symbol auch den Funktionsnamen an.\n"
            "Hilfreich wenn Symbole schwer erkennbar sind.")
        self._icon_text_cb.setChecked(_get_bool("BF_IconText", False))
        self._icon_text_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_IconText", v),
                       self.geaendert.emit("icon_text", v)))
        layout.addWidget(self._icon_text_cb)

        # ── 2. MOTORIK ────────────────────────────────────────────────────────
        layout.addWidget(_abschnitt("🖐  Motorische Einschränkungen"))

        # Button-Größe
        _r_btn = QtWidgets.QHBoxLayout()
        _r_btn.addWidget(QtWidgets.QLabel("Button-Größe:"))
        self._btn_gruppe = QtWidgets.QButtonGroup(self)
        for i, (label, key) in enumerate([("Normal", 0), ("Groß", 1), ("Sehr groß", 2)]):
            rb = QtWidgets.QRadioButton(label)
            rb.setToolTip(["Standard-Buttons", "Buttons 30% größer", "Buttons 60% größer"][i])
            rb.setChecked(_get_int("BF_ButtonGroesse", 0) == key)
            rb.toggled.connect(lambda v, k=key: v and self._on_button_groesse(k))
            self._btn_gruppe.addButton(rb, key)
            _r_btn.addWidget(rb)
        _r_btn.addStretch()
        layout.addLayout(_r_btn)

        # Tastaturmodus
        self._tastatur_cb = QtWidgets.QCheckBox("Tastaturmodus – alle Funktionen ohne Maus")
        self._tastatur_cb.setToolTip(
            "Aktiviert Tastaturkürzel für alle Hauptfunktionen.\n"
            "Eine Übersicht der Kürzel erscheint im Panel.")
        self._tastatur_cb.setChecked(_get_bool("BF_Tastaturmodus", False))
        self._tastatur_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_Tastaturmodus", v),
                       self.geaendert.emit("tastaturmodus", v)))
        layout.addWidget(self._tastatur_cb)

        # Einfache Ansicht
        self._einfach_cb = QtWidgets.QCheckBox("Einfache Ansicht – nur wichtigste Buttons")
        self._einfach_cb.setToolTip(
            "Blendet selten genutzte Funktionen aus.\n"
            "Reduziert die Anzahl sichtbarer Optionen.")
        self._einfach_cb.setChecked(_get_bool("BF_EinfacheAnsicht", False))
        self._einfach_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_EinfacheAnsicht", v),
                       self.geaendert.emit("einfache_ansicht", v)))
        layout.addWidget(self._einfach_cb)

        # ── 3. EINFACHE SPRACHE ───────────────────────────────────────────────
        layout.addWidget(_abschnitt("💬  Einfache Sprache"))

        self._einfach_sprache_cb = QtWidgets.QCheckBox(
            "KI antwortet in einfacher Sprache")
        self._einfach_sprache_cb.setToolTip(
            "Die KI verwendet kurze Sätze und einfache Wörter.\n"
            "Fachbegriffe werden vermieden oder erklärt.")
        self._einfach_sprache_cb.setChecked(_get_bool("BF_EinfacheSprache", False))
        self._einfach_sprache_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_EinfacheSprache", v),
                       self.geaendert.emit("einfache_sprache", v)))
        layout.addWidget(self._einfach_sprache_cb)

        self._fachbegriffe_cb = QtWidgets.QCheckBox(
            "Fachbegriffe automatisch erklären")
        self._fachbegriffe_cb.setToolTip(
            "Wenn die KI einen Fachbegriff verwendet,\n"
            "erklärt sie ihn direkt danach in einfachen Worten.")
        self._fachbegriffe_cb.setChecked(_get_bool("BF_FachbegriffeErklaeren", False))
        self._fachbegriffe_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_FachbegriffeErklaeren", v),
                       self.geaendert.emit("fachbegriffe", v)))
        layout.addWidget(self._fachbegriffe_cb)

        self._antwort_kurz_cb = QtWidgets.QCheckBox(
            "KI-Antworten kürzer und klarer halten")
        self._antwort_kurz_cb.setToolTip(
            "Die KI gibt kompakte Antworten ohne lange Erklärungen.\n"
            "Gut bei Konzentrationsschwierigkeiten.")
        self._antwort_kurz_cb.setChecked(_get_bool("BF_AntwortKurz", False))
        self._antwort_kurz_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_AntwortKurz", v),
                       self.geaendert.emit("antwort_kurz", v)))
        layout.addWidget(self._antwort_kurz_cb)

        # ── 4. ALLGEMEIN ──────────────────────────────────────────────────────
        layout.addWidget(_abschnitt("⚙  Allgemein"))

        self._tooltips_cb = QtWidgets.QCheckBox(
            "Tooltips immer sichtbar (nicht nur bei Hover)")
        self._tooltips_cb.setToolTip(
            "Erklärungs-Texte werden dauerhaft angezeigt\n"
            "und müssen nicht erst mit der Maus angesteuert werden.")
        self._tooltips_cb.setChecked(_get_bool("BF_TooltipsImmer", False))
        self._tooltips_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_TooltipsImmer", v),
                       self.geaendert.emit("tooltips_immer", v)))
        layout.addWidget(self._tooltips_cb)

        self._animation_cb = QtWidgets.QCheckBox("Animationen reduzieren")
        self._animation_cb.setToolTip(
            "Deaktiviert Übergangs-Animationen in der Oberfläche.\n"
            "Nützlich bei Empfindlichkeit gegenüber Bewegungen.")
        self._animation_cb.setChecked(_get_bool("BF_AnimationReduzieren", False))
        self._animation_cb.toggled.connect(
            lambda v: (self._speichere_bool("BF_AnimationReduzieren", v),
                       self.geaendert.emit("animation", v)))
        layout.addWidget(self._animation_cb)

        # ── Hinweis ───────────────────────────────────────────────────────────
        layout.addSpacing(8)
        hinweis = QtWidgets.QLabel(
            "ℹ  Einige Änderungen werden erst nach\n"
            "   einem Neustart vollständig wirksam.")
        hinweis.setStyleSheet(
            theme.STY_BF_HINWEIS(schrift.pt(schrift.STUFE_SM)))
        layout.addWidget(hinweis)
        layout.addStretch()

    # ── Speichern ──────────────────────────────────────────────────────────────
    def _speichere_bool(self, key, val):
        _set_bool(key, val)

    def _speichere(self, key, val):
        _set_bool(key, val)

    def _on_schrift(self, val):
        self._schrift_lbl.setText(f"{val} pt")
        _set_int("BF_SchriftGroesse", val)
        self.geaendert.emit("schrift_groesse", val)

    def _on_editor_schrift(self, val):
        self._editor_lbl.setText(f"{val} pt")
        _set_int("BF_EditorSchrift", val)
        self.geaendert.emit("editor_schrift", val)

    def _on_button_groesse(self, key):
        _set_int("BF_ButtonGroesse", key)
        self.geaendert.emit("button_groesse", key)

    # ── Öffentliche Lese-Funktionen ────────────────────────────────────────────
    @staticmethod
    def einfache_sprache() -> bool:
        return _get_bool("BF_EinfacheSprache", False)

    @staticmethod
    def fachbegriffe_erklaeren() -> bool:
        return _get_bool("BF_FachbegriffeErklaeren", False)

    @staticmethod
    def antwort_kurz() -> bool:
        return _get_bool("BF_AntwortKurz", False)

    @staticmethod
    def editor_schrift_pt() -> int:
        return _get_int("BF_EditorSchrift", 10)

    @staticmethod
    def ui_schrift_pt() -> int:
        return _get_int("BF_SchriftGroesse", 10)

    @staticmethod
    def button_groesse() -> int:
        return _get_int("BF_ButtonGroesse", 0)

    @staticmethod
    def hoher_kontrast() -> bool:
        return _get_bool("BF_HoherKontrast", False)

    @staticmethod
    def einfache_ansicht() -> bool:
        return _get_bool("BF_EinfacheAnsicht", False)

    @staticmethod
    def tastaturmodus() -> bool:
        return _get_bool("BF_Tastaturmodus", False)
