# -*- coding: utf-8 -*-
"""
ki_streaming.py
───────────────
KIStreaming – HTTP-Streaming aller KI-Anbieter + Worker-Threads.

Hält eine Referenz auf den Controller (MakroEditor-Instanz) und nutzt
dessen Signale und Session-Objekt.
"""

import json

from core.params import lade_api_key, api_key_resolved, lade_system_prompt_extra
from editor.ki.provider_daten import lade_anbieter_url


class KIStreaming:
    """Kapselt alle HTTP-Streaming-Aufrufe und Worker-Thread-Funktionen."""

    def __init__(self, controller):
        self._c = controller

    def _params(self) -> dict:
        """Liest Modell-Parameter aus den Einstellungs-Widgets."""
        c = self._c
        return {
            "max_tokens": getattr(c, "_max_tokens_box", None) and c._max_tokens_box.value() or 4096,
            "top_p":      getattr(c, "_top_p_box",      None) and c._top_p_box.value()      or 0.9,
            "top_k":      getattr(c, "_top_k_box",      None) and c._top_k_box.value()      or 40,
            "num_ctx":    getattr(c, "_ctx_box",         None) and c._ctx_box.value()        or 8192,
        }

    @staticmethod
    def _system_mit_extra(basis: str) -> str:
        """Hängt den nutzerdefinierten System-Prompt-Zusatz an."""
        extra = lade_system_prompt_extra().strip()
        if extra:
            return f"{basis}\n\n{extra}"
        return basis

    # ── Zentrale Anbieter-Weiche ──────────────────────────────────────────

    def stream_fuer_anbieter(self, source, model, prompt, temperature):
        """Leitet Streaming-Aufruf an den passenden Anbieter weiter."""
        if source.startswith("Ollama"):
            self.stream_ollama(model, prompt, temperature)
        elif source.startswith("Anthropic"):
            self.stream_anthropic(
                api_key_resolved("anthropic"), model, prompt, temperature)
        else:
            base, kid = lade_anbieter_url(source)
            self.stream_openai_compat(base, api_key_resolved(kid), model, prompt, temperature)

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
        from editor.ki.ki_modi import MODUS_DEFAULT, MODUS_ANFAENGER
        from editor.ki.nl_generator import (NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_PD,
                                            NL_PRESET_SCHLUESSEL_SW, NL_PRESET_SCHLUESSEL_TC)
        if ki_modus is None:
            ki_modus = MODUS_DEFAULT
        ist_nl = preset_name in (
            NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_PD, NL_PRESET_SCHLUESSEL_SW)
        if ist_nl and ki_modus == MODUS_ANFAENGER:
            system_prompt = system_prompt.replace(
                "Reply ONLY with Python code, no text before or after.",
                "After the code: Exactly 3 short German sentences as # comments:\n"
                "# 1. What was created\n"
                "# 2. Which default values were chosen\n"
                "# 3. Which constant the user should adjust"
            )
        from editor.ki.nl_generator import NL_PRESET_SCHLUESSEL, NL_PRESET_SCHLUESSEL_SW
        if preset_name == NL_PRESET_SCHLUESSEL:
            user_prompt = f"FreeCAD Part Workbench:\n{user_prompt}"
        elif preset_name == NL_PRESET_SCHLUESSEL_SW:
            user_prompt = f"FreeCAD Part Workbench (Erweiterung):\n{user_prompt}"
        elif preset_name == NL_PRESET_SCHLUESSEL_TC:
            user_prompt = f"Task:\n{user_prompt}"
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
        from editor.ki.ki_verlauf import _COMPACT_SCHWELLE
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
                    api_key_resolved("anthropic"), model, verlauf, temperature)
            else:
                base, kid = lade_anbieter_url(source)
                self.stream_openai_verlauf(
                    base, api_key_resolved(kid), model, verlauf, temperature)
            if self._c._alive:
                self._c._ki_stream_done.emit()
        except Exception as e:
            if self._c._alive:
                self._c._ki_error.emit(f"# ❌ Fehler:\n{e}")

    # ── FC14: Ollama Tool-Calling (/api/chat + tools) ─────────────────────

    def worker_ollama_tools(self, model, user_prompt, temperature):
        """FC14-Worker: Ollama /api/chat mit echtem Tool-Calling."""
        try:
            if self._c._alive:
                self._c._ki_chunk.emit("# ⏳ Warte auf Ollama Tool-Calling ...\n")
            python_code = self._stream_ollama_tools(model, user_prompt, temperature)
            if self._c._alive:
                self._c._ki_chunk.emit(python_code)
                self._c._ki_stream_done.emit()
        except Exception as e:
            if self._c._alive:
                self._c._ki_error.emit(f"# ❌ Fehler:\n{e}")

    def _stream_ollama_tools(self, model, user_prompt, temperature) -> str:
        """POST /api/chat mit tools-Array — gibt FreeCAD-Python-Code zurück."""
        import os as _os
        from editor.ki.fc14_tool_calling import FC14_TOOLS, tool_calls_zu_code, parse_content_json_calls

        _SYSTEM = (
            "You are a FreeCAD assistant. Output ONLY tool calls as JSON objects — no text, no explanation, no numbering. "
            "Rules: "
            "1) Create every object BEFORE referencing it in fuse() or cut(). "
            "2) Use x, y, z parameters for positioning — never use translate. "
            "3) For holes: cylinder() first (with correct x,y,z), then cut(). "
            "4) For L/T/U profiles: box() for each leg (with correct z offset), then fuse()."
        )

        r = self._c._session.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user",   "content": user_prompt},
                ],
                "tools":  FC14_TOOLS,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx":    self._params()["num_ctx"],
                    "top_p":      self._params()["top_p"],
                    "top_k":      self._params()["top_k"],
                    "num_thread": _os.cpu_count() or 4,
                },
            },
            timeout=120,
        )
        r.raise_for_status()
        data       = r.json()
        tool_calls = data.get("message", {}).get("tool_calls", [])
        content    = data.get("message", {}).get("content", "")

        # qwen2.5-coder gibt tool_calls als JSON-Objekte im content-Feld zurück
        if not tool_calls and content.strip():
            tool_calls = parse_content_json_calls(content)

        if not tool_calls:
            return (
                "# ⚠ Modell hat keine Tool-Calls zurückgegeben.\n"
                "# Tipp: Verwende qwen2.5-coder:7b (ollama pull qwen2.5-coder:7b)\n"
                "# oder beschreibe das Objekt einfacher (z.B. 'Create a box 50x30x10').\n"
                f"# Modell-Antwort: {content[:200]}\n"
            )

        python_code = tool_calls_zu_code(tool_calls)
        return python_code or "# ❌ Tool-Calls konnten nicht konvertiert werden"

    # ── Streaming: Ollama ─────────────────────────────────────────────────

    def stream_ollama(self, model, prompt, temperature):
        import os as _os
        _p = self._params()
        r = self._c._session.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": True,
                  "options": {
                      "temperature": temperature,
                      "num_ctx":     _p["num_ctx"],
                      "num_predict": _p["max_tokens"],
                      "top_p":       _p["top_p"],
                      "top_k":       _p["top_k"],
                      "num_thread":  _os.cpu_count() or 4,
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
            json={"model": model, "max_tokens": self._params()["max_tokens"],
                  "temperature": temperature, "stream": True,
                  "top_p": self._params()["top_p"],
                  "system": self._system_mit_extra(
                      "You are a Python expert. Reply only with Python code. Explanations always in German."),
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
            json={"model": model, "max_tokens": self._params()["max_tokens"],
                  "temperature": temperature, "stream": True,
                  "top_p": self._params()["top_p"],
                  "system": self._system_mit_extra(
                      "You are a Python expert for FreeCAD macros. "
                      "Reply only with Python code, no Markdown fences. Explanations always in German."),
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
                  "max_tokens": self._params()["max_tokens"],
                  "top_p":      self._params()["top_p"],
                  "messages": [
                      {"role": "system",
                       "content": self._system_mit_extra(
                           "You are a Python expert. Reply only with Python code. Explanations always in German.")},
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
             "content": self._system_mit_extra(
                 "You are a Python expert for FreeCAD macros. "
                 "Reply only with Python code, no Markdown fences. Explanations always in German.")},
            *verlauf
        ]
        r = self._c._session.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": model, "temperature": temperature, "stream": True,
                  "max_tokens": self._params()["max_tokens"],
                  "top_p":      self._params()["top_p"],
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
            key = api_key_resolved("anthropic")
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
            key = api_key_resolved(kid)
            headers["Authorization"] = f"Bearer {key}"
            body = json.dumps({
                "model": model, "temperature": temperature, "stream": False,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. Always reply in German."},
                    {"role": "user", "content": prompt}
                ]
            }).encode()
            req = _urllib.Request(f"{base}/chat/completions", data=body, headers=headers)
            with _urllib.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
