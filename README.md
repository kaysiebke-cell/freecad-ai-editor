# FreeCAD MultiAI Panel

A modern, AI-assisted Python editor as a FreeCAD plugin with freely arrangeable panels,
syntax highlighting, 19 supported AI providers, and extensive tools for
FreeCAD automation.

---

## Preview

![FreeCAD MultiAI Panel Demo](assets/ki-makro-editor-demo.gif)

> *Recording tool: [Peek](https://github.com/phw/peek) on Linux*

---

## Quick Start

1. **Install required package:** `pip install requests`
2. **Clone/download the repo** and place it in the FreeCAD `Mod` folder (folder name: `FreeCAD_MultiAI_Panel`, no spaces)
3. **Restart FreeCAD** and select the workbench **"FreeCAD MultiAI Panel"**
4. **Set up an AI provider** in the welcome dialog (e.g. locally with Ollama or with your own API key) — done!

> For OS-specific installation paths (Linux/Flatpak/Windows/macOS) see [Requirements & Installation](#requirements--installation).

---

## Table of Contents

- [Feature Overview](#feature-overview)
- [Requirements & Installation](#requirements--installation)
- [Setting Up AI Providers](#setting-up-ai-providers)
- [First Start & Welcome Dialog](docs/erststart.md)
- [The User Interface](docs/oberflaeche.md)
- [Panels in Detail](docs/panels.md)
- [AI Workflow & Presets](docs/ki-workflow.md)
- [FC11, FC12 & FC13 – Macro from Description](docs/makro-generator.md)
- [Snippets, API Hints & Tools Panel](docs/snippets-und-werkzeuge.md)
- [Macro Library](docs/makro-bibliothek.md)
- [Error Translator & Backup System](docs/fehler-und-backup.md)
- [Ollama – Field Report](docs/OLLAMA_ERFAHRUNGEN.md)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Feature Overview

### Editor
- Multiple files open simultaneously as tabs with drag & drop
- Python syntax highlighting (automatically adapts to light/dark theme)
- Line numbers, indent guides, cursor position
- Jedi-based autocomplete (optional)
- Search & replace with Ctrl+F
- Unlimited undo/redo transactions
- Automatic backups before every AI replacement (max. 3 per file)
- autopep8 formatting (optional)

### AI Integration
- **19 AI providers** supported (Ollama, Claude, ChatGPT, Gemini, DeepSeek, Groq …)
- **40+ presets** for all common coding tasks
- Streaming responses in real time (50 ms chunk batching)
- Chat history with auto-compacting after 5,000 characters
- Two modes: 🟢 Beginner (detailed, plain language) / 🔵 Expert (concise, technical) — **selection is saved**
- Generate macros from natural-language descriptions (FC11 / FC12 / FC13)
- AI tool-calling for structured FreeCAD operations (FC14 JSON)
- Ask the AI without any code in the editor (pure Q&A mode)
- **FreeCAD document state** automatically included in the prompt — compact for Ollama, full for cloud models
- **AGENTS.md support** — project-specific instructions next to the open file or in the home directory are loaded automatically
- **Preview errors → AI sandbox** — runtime errors from the preview can be resolved directly with "⚠ Explain error" or "🔧 AI fix"
- **🔌 Connection test** — checks Ollama reachability or API key status without an AI request
- **Auto-insert** — AI response is automatically inserted into the editor after stream end (optional)
- **Thinking mode** (Anthropic) — Extended Thinking with 8,000 budget tokens
- **System prompt templates** — 📋 menu with predefined prompts (FreeCAD Part-Script, FC14 JSON, Code Analysis etc.), directly editable; a prompt starting with "You are" replaces the base prompt entirely
- **Per-model parameters** — temperature, top-P, top-K, max tokens and context are saved per model and loaded automatically on switch
- **API key from file** — enter `file:/path/to/key-file` as the API key → key is read at runtime

### User Interface
- 11 freely arrangeable dock panels (move, detach, merge into tabs)
- **Light and dark mode** switchable via 🌙/☀ button in settings, selection is saved
- Every panel individually toggleable via toolbar
- Welcome dialog on first start (set up AI provider immediately)
- **🤝 Interactive assistant** — ask questions, AI responds with step-by-step instructions and highlights buttons
- **♿ Accessibility** — font size, contrast, keyboard mode (Alt+1–0), simplified view, tooltip delay, animations

---

## Requirements & Installation

### Requirements
- **FreeCAD 0.21** or newer
- **Python 3.10+**

### Required package
```bash
pip install requests
```
*Needed for all AI connections. Without `requests` the editor starts but all AI features are disabled.*

### Optional packages
```bash
pip install jedi            # Python autocomplete in the editor
pip install autopep8        # automatic PEP-8 formatting (button changes to "✨ autopep8")
pip install pyspellchecker  # spell checking in the helper panel (pure Python, Flatpak-compatible)
```

All at once:
```bash
pip install requests jedi autopep8 pyspellchecker
```

> **Flatpak users:** packages must be installed via the embedded Python:
> ```bash
> flatpak run --command=python3 org.freecad.FreeCAD -m pip install pyspellchecker
> ```

> **FreeCAD AppImage / Flatpak:** restart FreeCAD after `pip install`.
> For AppImages, `pip` may need to target the embedded Python:
> `/path/to/FreeCAD.AppImage --appimage-extract` → use the Python from the extracted directory.

### Installing the plugin

1. Clone this repository or download and extract the ZIP
2. Rename the folder to `FreeCAD_MultiAI_Panel` (no spaces — important!)

#### Linux – AppImage

```bash
mkdir -p ~/.local/share/FreeCAD/v1-1/Mod
ln -s /path/to/FreeCAD_MultiAI_Panel ~/.local/share/FreeCAD/v1-1/Mod/FreeCAD_MultiAI_Panel
```

#### Linux – Flatpak

```bash
mkdir -p ~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod
ln -s /path/to/FreeCAD_MultiAI_Panel ~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod/FreeCAD_MultiAI_Panel
```

> **Tip:** Using a symlink (`ln -s`) keeps the folder at its original location — code changes take effect immediately without copying again.

> **Flatpak file access:** If the workbench does not load in Flatpak, grant FreeCAD access to the home folder:
> ```bash
> flatpak override --user --filesystem=home org.freecad.FreeCAD
> ```

#### Windows

```
%APPDATA%\FreeCAD\Mod\FreeCAD_MultiAI_Panel\
```

#### macOS

```
~/Library/Preferences/FreeCAD/Mod/FreeCAD_MultiAI_Panel/
```

> **Note for Linux:** FreeCAD 1.x stores user data under `v1-1/` — older guides without this subfolder will not work.

3. Restart FreeCAD → the workbench **"FreeCAD MultiAI Panel"** appears in the workbench menu

---

## Setting Up AI Providers

### Supported providers (19)

| Provider | Models (selection) | API key format |
|----------|--------------------|----------------|
| **Ollama** (local) | codellama, llama3, mistral, … | — (no key) |
| **Anthropic (Claude)** | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5 | `sk-ant-…` |
| **OpenAI (ChatGPT)** | gpt-4o, gpt-4o-mini, gpt-4-turbo | `sk-…` |
| **GitHub Copilot** | gpt-4o, gpt-4o-mini, o1-mini | `ghp_…` |
| **DeepSeek** | deepseek-coder, deepseek-chat, deepseek-reasoner | API key |
| **Gemini (Google)** | gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash | API key |
| **Groq** | llama-3.3-70b, mixtral-8x7b, gemma2-9b | API key |
| **Mistral** | mistral-large-latest, codestral-latest | API key |
| **Together AI** | llama-3.3-70B, mixtral-8x7B, CodeLlama-34b | API key |
| **HuggingFace** | Llama 3.2, Qwen2.5-Coder, Mistral | API key |
| **xAI (Grok)** | grok-3, grok-3-mini, grok-2 | API key |
| **Fireworks AI** | llama-v3p3-70b, deepseek-coder-v2 | API key |
| **Moonshot** | moonshot-v1-8k, v1-32k, v1-128k | API key |
| **Qwen (Alibaba)** | qwen-coder-plus, qwen-plus, qwen-max, qwen2.5-coder-32b | API key |
| **Cohere** | command-a-03-2025, command-r-plus, command-r | API key |
| **SambaNova** | DeepSeek-R1, Meta-Llama-3.3-70B, Qwen2.5-Coder | API key |
| **MiniMax** | MiniMax-Text-01, abab6.5s-chat | API key |
| **Llama API** | Llama-4-Scout-17B, Llama-4-Maverick-17B, Llama-3.3-70B | API key |
| **OpenRouter** | (all supported models) | `sk-or-…` |

### Ollama (local, free)
```bash
# 1. Install Ollama: https://ollama.ai
# 2. Download recommended model for FreeCAD code
ollama pull qwen2.5-coder:7b   # ← recommended for FC11 macros

# Alternative general models
ollama pull codellama
ollama pull llama3

# 3. Start the Ollama service (runs on http://localhost:11434)
ollama serve
```
In the editor: **⚙ Settings** → Source: `Ollama (Local)` → no API key needed → **🔄 Reload models**

> 💡 **Tip:** The editor automatically detects whether a code model is installed and shows a hint if `qwen2.5-coder` is missing.

### Anthropic / OpenAI / other cloud providers
In the editor: **⚙ Settings** → select provider → enter API key → **press Tab** (saved automatically in FreeCAD settings)

### OpenRouter
```bash
# Set environment variable before starting FreeCAD
export OPENROUTER_API_KEY=sk-or-...
```

> ⚠️ **Security note:** API keys are stored unencrypted in FreeCAD settings. Do not use production keys.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+S** | Save |
| **Ctrl+A** | Select all |
| **Ctrl+Z** | Undo |
| **Ctrl+Y** | Redo |
| **Ctrl+F** | Toggle search/replace |
| **Tab** | Accept autocomplete suggestion |
| **Escape** | Close autocomplete |
| **Ctrl+Enter** | Error translator: translate immediately |

---

## Project Structure

```
FreeCAD_MultiAI_Panel/
│
├── main.py              # Entry point (FreeCAD macro / sidebar)
├── InitGui.py           # FreeCAD GUI integration (toolbar button)
├── Icon.svg             # Plugin icon
├── package.xml          # FreeCAD addon metadata
├── README.md
│
├── core/
│   ├── params.py        # Settings persistence (FreeCAD params + API keys)
│   ├── qt_compat.py     # PySide6/PySide2 compatibility layer + requests export
│   ├── theme.py         # Stylesheets & design functions (light/dark adaptive)
│   ├── farben.py        # Colour definitions for light and dark mode
│   ├── highlighter.py   # Python syntax highlighter
│   └── schrift.py       # Font size constants
│
├── editor/
│   ├── editor.py        # Coordinator (QMainWindow, delegates to intern/)
│   ├── freecad_helfer_panel.py
│   │
│   ├── intern/          # Editor build and logic modules
│   │   ├── central_widget_builder.py  # Central widget + status bar
│   │   ├── dock_builder.py            # All 13 dock panels
│   │   ├── toolbar_builder.py         # Toolbar
│   │   ├── ki_widget_builder.py       # AI panel (provider, model, presets, temp.)
│   │   ├── editor_datei.py            # File logic (save, backup, reload)
│   │   ├── editor_suche.py            # Search & replace
│   │   ├── editor_code.py             # Formatting, indentation, selection
│   │   ├── editor_plan.py             # Plan mode, insert after match
│   │   ├── editor_tabs.py             # Tab management
│   │   └── editor_barrierefreiheit.py # Colour scheme, font, keyboard mode
│   │
│   ├── widgets/
│   │   └── editor_widgets.py   # CodeEditor, LinksTextEdit, LineNumberArea
│   │
│   ├── controller/
│   │   ├── assistent.py          # Interactive assistant (button highlighting)
│   │   ├── bibliothek_tab.py     # Macro library tab
│   │   ├── browser_controller.py # File browser
│   │   ├── ki_tools_tab.py       # AI tools tab (direct operations)
│   │   ├── snippet_controller.py # Snippets tab controller (local + online)
│   │   ├── snippet_widgets.py    # Helper widgets: SnipCommandEdit, Worker, Banner
│   │   ├── vorschau_controller.py
│   │   └── werkzeuge.py          # Tools panel (code tree, navigation, edit)
│   │
│   ├── fehler/
│   │   └── fehler_panel.py       # Error panel + AI self-correction + sandbox
│   │
│   └── ki/
│       ├── ki_controller.py      # AI coordinator (delegates to composition objects)
│       ├── ki_werkzeuge.py       # AI tool-calling
│       ├── assistent_prompt.py   # Assistant system prompt
│       ├── dokument_kontext.py   # Document context preparation
│       │
│       └── intern/               # AI implementation modules
│           ├── provider_daten.py      # Provider URLs + model lists (19 providers)
│           ├── ki_streaming.py        # HTTP streaming for all providers + worker threads
│           ├── ki_anfrage.py          # Prompt building + AI requests
│           ├── ki_verlauf.py          # Chat history + context compacting
│           ├── ki_chunk.py            # Chunk buffer + stream-done processing
│           ├── ki_sitzung.py          # Save/load sessions (JSON)
│           ├── ki_fehler.py           # Error panel integration + self-correction
│           ├── kod_analyse.py         # AST analysis (pure functions)
│           └── kod_korrektor.py       # FreeCAD code correction + NL filter
│
├── ui/
│   ├── manager.py       # FreeCAD macro manager (sidebar)
│   ├── begruessung.py   # Welcome dialog (first start)
│   ├── barrierefreiheit.py  # Accessibility panel
│   └── fehler.py        # Error translator (EN→DE) + error display
│
├── data/
│   ├── freecad_data.py       # Snippets (6 categories) + API hints
│   ├── nl_generator.py       # System prompts for FC11/FC12/FC13
│   ├── ki_modi.py            # AI modes (beginner / expert)
│   ├── bibliothek.py         # Macro library data
│   ├── anbieter_formate.py   # Provider formats
│   ├── hilfe_texte.py        # Built-in help texts
│   └── hilfe.py              # Help panel
│
├── assets/
│   └── icons/           # SVG icons for AI providers, demo GIF
│
├── docs/                # Detailed documentation
│   ├── erststart.md
│   ├── oberflaeche.md
│   ├── panels.md
│   ├── ki-workflow.md
│   ├── makro-generator.md
│   ├── snippets-und-werkzeuge.md
│   ├── makro-bibliothek.md
│   ├── fehler-und-backup.md
│   └── OLLAMA_ERFAHRUNGEN.md
│
└── tests/
    ├── test_back_funktionen.py
    └── test_editor_live.py
```

---

## Known Limitations

| Problem | Cause | Solution |
|---------|-------|----------|
| **Emojis displayed as outlines** in Flatpak | Flatpak sandbox blocks system emoji fonts | Use native package or AppImage |
| **FC12/FC13 disabled for Ollama** | Too complex for local models | Use Claude (Anthropic) or GPT-4o |
| **API keys stored unencrypted** | FreeCAD settings have no encryption | Do not use production keys |
| **Large files (>2,000 lines)** | AI context window is limited | Load only relevant sections into the input field |
| **Ollama not found** | Service is not running | Run `ollama serve` in the terminal |
| **Ollama produces poor FreeCAD code** | General model without code focus | Install `ollama pull qwen2.5-coder:7b` |

---
