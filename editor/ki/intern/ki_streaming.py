# -*- coding: utf-8 -*-
"""
ki_streaming.py
───────────────
KIStreaming – HTTP-Streaming aller KI-Anbieter + Worker-Threads.

Hält eine Referenz auf den Controller (MakroEditor-Instanz) und nutzt
dessen Signale und Session-Objekt.
"""

import json

from params import lade_api_key
from provider_daten import lade_anbieter_url


class KIStreaming:
    """Kapselt alle HTTP-Streaming-Aufrufe und Worker-Thread-Funktionen."""

    def __init__(self, controller):
        self._c = controller

    # ── Zentrale Anbieter-Weiche ──────────────────────────────────────────

    def stream_fuer_anbieter(self, source, model, prompt, temperature):
        """Leitet Streaming-Aufruf an den passenden Anbieter weiter."""
        if source.startswith("Ollama"):
            self.stream_ollama(model, prompt, temperature)
        elif source.startswith("Anthropic"):
            self.stream_anthropic(
                lade_api_key("anthropic"), model, prompt, temperature)
        else:
            base, kid = lade_anbieter_url(source)
            self.stream_openai_compat(base, lade_api_key(kid), model, prompt, temperature)

    # ── Worker-Threads ────────────────────────────────────────────────────

    def worker(self, source, model, prompt, temperature=0.2):
        """Einfacher Worker-Thread ohne Verlauf."""
        try:
            self.stream_fuer_anbieter(source, model, prompt, temperature)
            if self._c._alive:
                self._c._ki_stream_done.emit()
        except Exception as e:
            if self._c._alive:
                self._c._ki_error.emit(f"# ❌ Fehler:\n{e}")

    def worker_mit_system(self, source, model, system_prompt, user_prompt,
                           temperature=0.2, preset_name="", ki_modus=None):
        """Worker für Aufrufe mit separatem System-Prompt.

        preset_name und ki_modus im Hauptthread gesichert übergeben —
        niemals aus dem Worker-Thread von Qt-Widgets lesen.
        """
        from ki_modi import MODUS_DEFAULT, MODUS_ANFAENGER
        from nl_generator import (NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_PD,
                                   NL_PRESET_SCHLUESSEL_SW)
        if ki_modus is None:
            ki_modus = MODUS_DEFAULT
        ist_nl = preset_name in (
            NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_PD, NL_PRESET_SCHLUESSEL_SW)
        if ist_nl and ki_modus == MODUS_ANFAENGER:
            system_prompt = system_prompt.replace(
                "Nur reinen Python-Code ausgeben. Kein Erklärungstext nach dem Code.",
                "Nach dem Code: Genau 3 kurze deutsche Saetze als #-Kommentare:\n"
                "# 1. Was wurde erstellt\n"
                "# 2. Welche Standardwerte gewaehlt wurden\n"
                "# 3. Welche Konstante der Nutzer anpassen muss"
            )
        from nl_generator import NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_SW
        if preset_name == NL_PRESET_SCHLUESSEL:
            user_prompt = f"FreeCAD Part Workbench:\n{user_prompt}"
        elif preset_name == NL_PRESET_SCHLUESSEL_SW:
            user_prompt = f"FreeCAD Part Workbench (Erweiterung):\n{user_prompt}"
        full = f"{system_prompt}\n\nFrage des Users:\n{user_prompt}"
        try:
            if self._c._alive:
                self._c._ki_chunk.emit("# ⏳ Anfrage an KI gesendet ...\n\n")
            self.stream_fuer_anbieter(source, model, full, temperature)
            if self._c._alive:
                self._c._ki_stream_done.emit()
        except Exception as e:
            if self._c._alive:
                self._c._ki_error.emit(f"# ❌ Fehler:\n{e}")

    def worker_mit_verlauf(self, source, model, verlauf, temperature=0.2):
        """Worker mit Gesprächsverlauf + automatischem Context Compacting."""
        from ki_verlauf import _COMPACT_SCHWELLE
        gesamt_zeichen = sum(len(m["content"]) for m in verlauf)
        if gesamt_zeichen > _COMPACT_SCHWELLE:
            self._c._verlauf.komprimieren(source, model, temperature)
            verlauf = list(self._c._chat_verlauf)

        try:
            if source.startswith("Ollama"):
                kompakt = "\n\n".join(
                    f"[{m['role'].upper()}]:\n{m['content']}" for m in verlauf)
                self.stream_ollama(model, kompakt, temperature)
            elif source.startswith("Anthropic"):
                self.stream_anthropic_verlauf(
                    lade_api_key("anthropic"), model, verlauf, temperature)
            else:
                base, kid = lade_anbieter_url(source)
                self.stream_openai_verlauf(
                    base, lade_api_key(kid), model, verlauf, temperature)
            if self._c._alive:
                self._c._ki_stream_done.emit()
        except Exception as e:
            if self._c._alive:
                self._c._ki_error.emit(f"# ❌ Fehler:\n{e}")

    # ── Streaming: Ollama ─────────────────────────────────────────────────

    def stream_ollama(self, model, prompt, temperature):
        import os as _os
        _cpu_kerne = _os.cpu_count() or 4
        r = self._c._session.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": True,
                  "options": {
                      "temperature": temperature,
                      "num_ctx":     2048,
                      "num_predict": 1024,
                      "num_thread":  _cpu_kerne,
                  }},
            stream=True, timeout=None)
        r.raise_for_status()
        for line in r.iter_lines():
            if not self._c._alive:
                break
            if line:
                data  = json.loads(line)
                chunk = data.get("response", "")
                if chunk:
                    self._c._ki_chunk.emit(chunk)

    # ── Streaming: Anthropic ──────────────────────────────────────────────

    def stream_anthropic(self, key, model, prompt, temperature):
        if not key:
            raise RuntimeError(
                "Kein Anthropic API-Schlüssel hinterlegt.\n"
                "Bitte unten rechts 'Anthropic (Claude)' wählen und sk-ant-… eintragen.")
        r = self._c._session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": model, "max_tokens": 4096, "temperature": temperature,
                  "stream": True,
                  "system": "Du bist ein Python-Experte. Antworte nur mit Python-Code.",
                  "messages": [{"role": "user", "content": prompt}]},
            stream=True, timeout=120)
        r.raise_for_status()
        for line in r.iter_lines():
            if not self._c._alive:
                break
            if line and line.startswith(b"data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta":
                        chunk = data.get("delta", {}).get("text", "")
                        if chunk:
                            self._c._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError):
                    pass

    def stream_anthropic_verlauf(self, key, model, verlauf, temperature):
        """Anthropic-Streaming mit vollständigem Nachrichtenverlauf."""
        if not key:
            raise RuntimeError(
                "Kein Anthropic API-Schlüssel hinterlegt.\n"
                "Bitte unten rechts 'Anthropic (Claude)' wählen und sk-ant-… eintragen.")
        r = self._c._session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": model, "max_tokens": 4096, "temperature": temperature,
                  "stream": True,
                  "system": "Du bist ein Python-Experte für FreeCAD-Makros. "
                             "Antworte nur mit Python-Code ohne Markdown-Fences.",
                  "messages": verlauf},
            stream=True, timeout=120)
        r.raise_for_status()
        antwort_teile = []
        for line in r.iter_lines():
            if not self._c._alive:
                break
            if line and line.startswith(b"data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta":
                        chunk = data.get("delta", {}).get("text", "")
                        if chunk:
                            antwort_teile.append(chunk)
                            self._c._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError):
                    pass
        if antwort_teile:
            self._c._chat_verlauf.append(
                {"role": "assistant", "content": "".join(antwort_teile)})

    # ── Streaming: OpenAI-kompatibel ──────────────────────────────────────

    def stream_openai_compat(self, base_url, key, model, prompt, temperature):
        if not key:
            raise RuntimeError(
                f"Kein API-Schlüssel für {base_url} hinterlegt.\n"
                "Bitte unten rechts den passenden Anbieter wählen und den Key eintragen.")
        r = self._c._session.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": model, "temperature": temperature, "stream": True,
                  "messages": [
                      {"role": "system",
                       "content": "Du bist ein Python-Experte. Antworte nur mit Python-Code."},
                      {"role": "user", "content": prompt}]},
            stream=True, timeout=120)
        r.raise_for_status()
        for line in r.iter_lines():
            if not self._c._alive:
                break
            if line and line.startswith(b"data: "):
                raw = line[6:]
                if raw == b"[DONE]":
                    break
                try:
                    chunk = json.loads(raw)["choices"][0]["delta"].get("content", "")
                    if chunk:
                        self._c._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

    def stream_openai_verlauf(self, base_url, key, model, verlauf, temperature):
        """OpenAI-kompatibles Streaming mit vollständigem Nachrichtenverlauf."""
        if not key:
            raise RuntimeError(f"Kein API-Schlüssel für {base_url} hinterlegt.")
        nachrichten = [
            {"role": "system",
             "content": "Du bist ein Python-Experte für FreeCAD-Makros. "
                        "Antworte nur mit Python-Code ohne Markdown-Fences."},
            *verlauf
        ]
        r = self._c._session.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": model, "temperature": temperature, "stream": True,
                  "messages": nachrichten},
            stream=True, timeout=120)
        r.raise_for_status()
        antwort_teile = []
        for line in r.iter_lines():
            if not self._c._alive:
                break
            if line and line.startswith(b"data: "):
                raw = line[6:]
                if raw == b"[DONE]":
                    break
                try:
                    chunk = json.loads(raw)["choices"][0]["delta"].get("content", "")
                    if chunk:
                        antwort_teile.append(chunk)
                        self._c._ki_chunk.emit(chunk)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        if antwort_teile:
            self._c._chat_verlauf.append(
                {"role": "assistant", "content": "".join(antwort_teile)})

    # ── Blockierender Einmal-Aufruf ───────────────────────────────────────

    def einmaliger_aufruf(self, source, model, prompt, temperature) -> str:
        """Blockierender (nicht-streamender) API-Aufruf für interne Zwecke."""
        import urllib.request as _urllib
        headers = {"Content-Type": "application/json"}
        if source.startswith("Anthropic"):
            key = lade_api_key("anthropic")
            url = "https://api.anthropic.com/v1/messages"
            headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
            body = json.dumps({
                "model": model, "max_tokens": 512, "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()
            req = _urllib.Request(url, data=body, headers=headers)
            with _urllib.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["content"][0]["text"].strip()
        elif source.startswith("Ollama"):
            url = "http://localhost:11434/api/generate"
            body = json.dumps({
                "model": model, "prompt": prompt,
                "stream": False, "options": {
                    "temperature": temperature,
                    "num_ctx": 2048, "num_predict": 512,
                    "num_thread": __import__("os").cpu_count() or 4,
                }
            }).encode()
            req = _urllib.Request(url, data=body, headers=headers)
            with _urllib.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read()).get("response", "").strip()
        else:
            base, kid = lade_anbieter_url(source)
            key = lade_api_key(kid)
            headers["Authorization"] = f"Bearer {key}"
            body = json.dumps({
                "model": model, "temperature": temperature, "stream": False,
                "messages": [
                    {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                    {"role": "user", "content": prompt}
                ]
            }).encode()
            req = _urllib.Request(f"{base}/chat/completions", data=body, headers=headers)
            with _urllib.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
