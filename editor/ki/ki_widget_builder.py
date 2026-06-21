# -*- coding: utf-8 -*-
"""
ki_widget_builder.py
────────────────────
Baut die KI-Einstellungs-Widgets (Anbieter-Box, Modell-Box, Preset-Menü,
API-Key-Feld, Modus-Buttons) des MakroEditors auf.
Aufgerufen einmalig aus MakroEditor.__init__.
"""

import os

from core.qt_compat import QtWidgets, QtCore, QtGui

from core.params import (KI_PRESETS, KI_PRESET_KATEGORIEN,
                         lade_api_key, speichere_api_key, speichere_quelle, lade_quelle,
                         speichere_modell, lade_modell_params, speichere_modell_params)
from core.theme_styles import PARAM_SPINBOX_BREITE_SCHMAL, PARAM_SPINBOX_BREITE_BREIT


# ── Interne Event-Handler (nur hier verbunden) ────────────────────────────

def _aktueller_params_dict(editor) -> dict:
    """Liest aktuelle Spinbox-Werte als params-Dict."""
    return {
        "temp":       editor._temp_box.value(),
        "top_p":      editor._top_p_box.value(),
        "top_k":      editor._top_k_box.value(),
        "max_tokens": editor._max_tokens_box.value(),
        "num_ctx":    editor._ctx_box.value(),
    }


def _lade_params_in_widgets(editor, modell: str) -> None:
    """Lädt gespeicherte Params für modell in die Spinboxen."""
    p = lade_modell_params(modell)
    for box, key in [
        (editor._temp_box,       "temp"),
        (editor._top_p_box,      "top_p"),
        (editor._top_k_box,      "top_k"),
        (editor._max_tokens_box, "max_tokens"),
        (editor._ctx_box,        "num_ctx"),
    ]:
        box.blockSignals(True)
        box.setValue(p[key])
        box.blockSignals(False)


def _on_modell_gewechselt(editor, neuer_name: str) -> None:
    """Speichert Params des alten Modells und lädt die des neuen."""
    alter = getattr(editor, "_prev_modell", "")
    if alter and alter != neuer_name:
        speichere_modell_params(alter, _aktueller_params_dict(editor))
    if neuer_name:
        _lade_params_in_widgets(editor, neuer_name)
    editor._prev_modell = neuer_name


def _on_modus_geaendert(editor):
    from editor.ki.ki_modi import MODUS_EXPERTE, MODUS_ANFAENGER, MODUS_LABELS
    editor._ki_modus = (MODUS_EXPERTE
                        if editor._btn_modus_experte.isChecked()
                        else MODUS_ANFAENGER)
    editor._set_status(f"Modus → {MODUS_LABELS[editor._ki_modus]}")


def _on_anbieter_gewechselt(editor):
    _PLACEHOLDERS = {
        "anthropic":"sk-ant-…", "openai":"sk-…",    "github":"ghp_…",
        "openrouter":"sk-or-…", "deepseek":"sk-…",  "gemini":"AIza…",
        "groq":"gsk_…",         "mistral":"…",       "together":"…",
        "huggingface":"hf_…",   "xai":"xai-…",       "fireworks":"fw_…",
        "moonshot":"sk-…",      "qwen":"sk-…",        "cohere":"…",
        "sambanova":"…",        "minimax":"…",        "llama":"…",
    }
    if editor._prev_anbieter_id:
        speichere_api_key(editor._prev_anbieter_id, editor._key_feld.text().strip())
    neuer_id = editor._key_anbieter_id()
    editor._prev_anbieter_id = neuer_id
    if neuer_id:
        editor._key_feld.setText(lade_api_key(neuer_id))
        editor._key_feld.setPlaceholderText(_PLACEHOLDERS.get(neuer_id, ""))
        editor._key_feld.setEnabled(True)
    else:
        editor._key_feld.clear()
        editor._key_feld.setPlaceholderText("(kein API-Key benötigt)")
        editor._key_feld.setEnabled(False)


def _baue_preset_menu(editor):
    editor._preset_menu.clear()
    schnell = KI_PRESET_KATEGORIEN.get("★ Schnell", {})
    for name, prompt in schnell.items():
        action = editor._preset_menu.addAction(f"★ {name}")
        action.triggered.connect(
            lambda checked, n=name, p=prompt: _preset_gewaehlt(editor, n, p))
    if schnell:
        editor._preset_menu.addSeparator()
    for kat, eintraege in KI_PRESET_KATEGORIEN.items():
        if kat == "★ Schnell" or not eintraege:
            continue
        sub = editor._preset_menu.addMenu(kat)
        for name, prompt in eintraege.items():
            action = sub.addAction(name)
            action.triggered.connect(
                lambda checked, n=name, p=prompt, k=kat: _preset_gewaehlt(
                    editor, f"{k}: {n}", p))


def _preset_gewaehlt(editor, name: str, prompt: str):
    editor._preset_btn.setText(name)
    idx = editor._preset_box.findText(name)
    if idx >= 0:
        editor._preset_box.setCurrentIndex(idx)
    else:
        editor._preset_box.addItem(name)
        editor._preset_box.setCurrentText(name)


# ── Builder ───────────────────────────────────────────────────────────────

def init_ki_widgets(editor, icons_dir: str) -> None:
    """Erstellt alle KI-Einstellungs-Widgets und setzt sie als Attribute am editor."""
    from editor.ki.ki_modi import (MODUS_ANFAENGER, MODUS_EXPERTE,
                         MODUS_LABELS, MODUS_TOOLTIPS, MODUS_DEFAULT)
    editor._ki_modus = MODUS_DEFAULT

    editor._src_box = QtWidgets.QComboBox()
    editor._src_box.setIconSize(QtCore.QSize(16, 16))
    for src_name, _, _, icon_datei in editor._ANBIETER:
        if icon_datei:
            icon_pfad = os.path.join(icons_dir, icon_datei)
            editor._src_box.addItem(QtGui.QIcon(icon_pfad), src_name)
        else:
            editor._src_box.addItem(src_name)
    editor._src_box.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    _gespeicherte_quelle = lade_quelle()
    if _gespeicherte_quelle in [
            editor._src_box.itemText(i) for i in range(editor._src_box.count())]:
        editor._src_box.blockSignals(True)
        editor._src_box.setCurrentText(_gespeicherte_quelle)
        editor._src_box.blockSignals(False)

    editor._model_box = QtWidgets.QComboBox()
    editor._model_box.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    # Signal erst verbinden nachdem _model_box existiert
    editor._src_box.currentIndexChanged.connect(editor._refresh_models)
    editor._src_box.currentTextChanged.connect(speichere_quelle)
    editor._src_box.currentIndexChanged.connect(lambda _: _on_anbieter_gewechselt(editor))
    editor._model_box.currentTextChanged.connect(speichere_modell)
    editor._prev_modell = ""
    editor._model_box.currentTextChanged.connect(lambda name: _on_modell_gewechselt(editor, name))

    editor._preset_btn = QtWidgets.QToolButton()
    editor._preset_btn.setText("── Preset wählen ──")
    editor._preset_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
    editor._preset_btn.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    editor._preset_menu = QtWidgets.QMenu(editor._preset_btn)
    editor._preset_btn.setMenu(editor._preset_menu)
    _baue_preset_menu(editor)

    editor._preset_box = QtWidgets.QComboBox()
    editor._preset_box.addItems(KI_PRESETS.keys())
    editor._preset_box.hide()

    editor._temp_box = QtWidgets.QDoubleSpinBox()
    editor._temp_box.setRange(0.0, 2.0)
    editor._temp_box.setSingleStep(0.1)
    editor._temp_box.setValue(0.2)
    editor._temp_box.setFixedWidth(PARAM_SPINBOX_BREITE_SCHMAL)
    editor._temp_box.setToolTip(
        "Temperatur (0.0–2.0)\n"
        "0.0–0.3 = präzise (Code)\n"
        "0.5–0.8 = kreativ\n"
        "1.0+    = sehr kreativ")

    editor._max_tokens_box = QtWidgets.QSpinBox()
    editor._max_tokens_box.setRange(256, 65536)
    editor._max_tokens_box.setSingleStep(256)
    editor._max_tokens_box.setValue(4096)
    editor._max_tokens_box.setFixedWidth(PARAM_SPINBOX_BREITE_BREIT)
    editor._max_tokens_box.setToolTip(
        "Max. Output-Tokens\n"
        "Wie viel Text/Code das Modell maximal zurückgeben darf.\n"
        "Ollama: num_predict  |  Cloud: max_tokens")

    editor._ctx_box = QtWidgets.QSpinBox()
    editor._ctx_box.setRange(512, 131072)
    editor._ctx_box.setSingleStep(1024)
    editor._ctx_box.setValue(8192)
    editor._ctx_box.setFixedWidth(PARAM_SPINBOX_BREITE_BREIT)
    editor._ctx_box.setToolTip(
        "Kontext-Fenster (num_ctx)\n"
        "Wie viele Token das Modell gleichzeitig 'sehen' kann.\n"
        "Nur wirksam bei Ollama. Größer = mehr RAM.")

    editor._top_p_box = QtWidgets.QDoubleSpinBox()
    editor._top_p_box.setRange(0.0, 1.0)
    editor._top_p_box.setSingleStep(0.05)
    editor._top_p_box.setValue(0.9)
    editor._top_p_box.setDecimals(2)
    editor._top_p_box.setFixedWidth(PARAM_SPINBOX_BREITE_SCHMAL)
    editor._top_p_box.setToolTip(
        "Top-P (Nucleus Sampling)\n"
        "Wählt aus den wahrscheinlichsten Tokens die zusammen P % ausmachen.\n"
        "0.9 = Standard  |  1.0 = deaktiviert")

    editor._top_k_box = QtWidgets.QSpinBox()
    editor._top_k_box.setRange(0, 200)
    editor._top_k_box.setSingleStep(5)
    editor._top_k_box.setValue(40)
    editor._top_k_box.setFixedWidth(PARAM_SPINBOX_BREITE_SCHMAL)
    editor._top_k_box.setToolTip(
        "Top-K\n"
        "Wählt nur aus den K wahrscheinlichsten nächsten Tokens.\n"
        "0 = deaktiviert  |  40 = Standard (Ollama)")

    editor._btn_modus_anfaenger = QtWidgets.QRadioButton(MODUS_LABELS[MODUS_ANFAENGER])
    editor._btn_modus_anfaenger.setToolTip(MODUS_TOOLTIPS[MODUS_ANFAENGER])
    editor._btn_modus_anfaenger.setChecked(MODUS_DEFAULT == MODUS_ANFAENGER)
    editor._btn_modus_experte = QtWidgets.QRadioButton(MODUS_LABELS[MODUS_EXPERTE])
    editor._btn_modus_experte.setToolTip(MODUS_TOOLTIPS[MODUS_EXPERTE])
    editor._btn_modus_experte.setChecked(MODUS_DEFAULT == MODUS_EXPERTE)
    editor._btn_modus_anfaenger.toggled.connect(lambda: _on_modus_geaendert(editor))
    editor._btn_modus_experte.toggled.connect(lambda: _on_modus_geaendert(editor))

    editor._key_feld = QtWidgets.QLineEdit()
    editor._key_feld.setEchoMode(QtWidgets.QLineEdit.Password)
    editor._key_feld.setMinimumHeight(26)
    editor._key_feld.setPlaceholderText("sk-ant-…")
    editor._prev_anbieter_id = editor._key_anbieter_id()
    editor._key_feld.editingFinished.connect(
        lambda: speichere_api_key(editor._key_anbieter_id(), editor._key_feld.text().strip()))
    _on_anbieter_gewechselt(editor)

    # Params-Spinboxen: beim Ändern immer für das aktuelle Modell speichern
    def _param_geaendert():
        modell = editor._model_box.currentText()
        if modell:
            speichere_modell_params(modell, _aktueller_params_dict(editor))

    for _box in (editor._temp_box, editor._top_p_box, editor._top_k_box,
                 editor._max_tokens_box, editor._ctx_box):
        _box.valueChanged.connect(lambda *_: _param_geaendert())


# ── Hilfsfunktionen (extern aufrufbar via editor-Methoden-Wrapper) ────────

def get_preset_prompt(editor) -> str:
    return KI_PRESETS.get(editor._preset_btn.text(), "")


def baue_preset_menu(editor):
    _baue_preset_menu(editor)
