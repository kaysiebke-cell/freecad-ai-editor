# -*- coding: utf-8 -*-
"""
ki_widget_builder.py
────────────────────
Baut die KI-Einstellungs-Widgets (Anbieter-Box, Modell-Box, Preset-Menü,
API-Key-Feld, Modus-Buttons) des MakroEditors auf.
Aufgerufen einmalig aus MakroEditor.__init__.
"""

import os

from qt_compat import QtWidgets, QtCore, QtGui

import theme
import schrift
from params import (KI_PRESETS, KI_PRESET_KATEGORIEN,
                    lade_api_key, speichere_api_key, speichere_quelle, lade_quelle)


# ── Interne Event-Handler (nur hier verbunden) ────────────────────────────

def _on_modus_geaendert(editor):
    from ki_modi import MODUS_EXPERTE, MODUS_ANFAENGER, MODUS_LABELS
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
    speichere_api_key(editor._prev_anbieter_id, editor._key_feld.text().strip())
    editor._prev_anbieter_id = editor._key_anbieter_id()
    editor._key_feld.setText(lade_api_key(editor._prev_anbieter_id))
    editor._key_feld.setPlaceholderText(_PLACEHOLDERS.get(editor._prev_anbieter_id, ""))


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
    from ki_modi import (MODUS_ANFAENGER, MODUS_EXPERTE,
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
    editor._temp_box.setFixedWidth(58)
    editor._temp_box.setToolTip(
        "Temperatur (0.0–2.0)\n"
        "0.0–0.3 = präzise (Code)\n"
        "0.5–0.8 = kreativ\n"
        "1.0+    = sehr kreativ")

    editor._btn_modus_anfaenger = QtWidgets.QRadioButton(MODUS_LABELS[MODUS_ANFAENGER])
    editor._btn_modus_anfaenger.setToolTip(MODUS_TOOLTIPS[MODUS_ANFAENGER])
    editor._btn_modus_anfaenger.setChecked(MODUS_DEFAULT == MODUS_ANFAENGER)
    editor._btn_modus_experte = QtWidgets.QRadioButton(MODUS_LABELS[MODUS_EXPERTE])
    editor._btn_modus_experte.setToolTip(MODUS_TOOLTIPS[MODUS_EXPERTE])
    editor._btn_modus_experte.setChecked(MODUS_DEFAULT == MODUS_EXPERTE)
    editor._btn_modus_anfaenger.toggled.connect(lambda: _on_modus_geaendert(editor))
    editor._btn_modus_experte.toggled.connect(lambda: _on_modus_geaendert(editor))

    editor._key_anbieter = QtWidgets.QComboBox()
    editor._key_anbieter.addItems([k for _, k, _, _ in editor._ANBIETER if k is not None])
    editor._key_anbieter.setSizePolicy(
        QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    editor._key_anbieter.setToolTip("KI-Anbieter wählen")
    editor._key_feld = QtWidgets.QLineEdit()
    editor._key_feld.setEchoMode(QtWidgets.QLineEdit.Password)
    editor._key_feld.setMinimumHeight(26)
    editor._key_feld.setPlaceholderText("sk-ant-…")
    editor._prev_anbieter_id = "anthropic"
    editor._key_feld.editingFinished.connect(
        lambda: speichere_api_key(editor._key_anbieter_id(), editor._key_feld.text().strip()))
    editor._key_anbieter.currentIndexChanged.connect(
        lambda _: _on_anbieter_gewechselt(editor))
    _on_anbieter_gewechselt(editor)


# ── Hilfsfunktionen (extern aufrufbar via editor-Methoden-Wrapper) ────────

def get_preset_prompt(editor) -> str:
    return KI_PRESETS.get(editor._preset_btn.text(), "")


def baue_preset_menu(editor):
    _baue_preset_menu(editor)
