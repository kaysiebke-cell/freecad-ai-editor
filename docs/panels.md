[← Back: The User Interface](oberflaeche.md) | [Back to README](../README.md) | Next: [AI Workflow & Presets →](ki-workflow.md)

# Panels in Detail

## ⚙ Settings Panel

The panel is scrollable — all sections are accessible even in a small dock window.

### AI SOURCE
- **AI source** select (dropdown with all 19 providers)
- **🔄 Reload models** – fetch a fresh model list from the provider
- **🔌 Connection test** – checks without an AI request whether Ollama is reachable or an API key is stored; result appears as a label below the model box

### MODEL PARAMETERS
- **Temperature** 0.0–2.0 (recommended: 0.0–0.3 for code, 0.5–0.8 for documentation)
- **Top-P · Top-K · Max Tokens · Context** — all values are saved **per model** and loaded automatically on switch

### MODE
- 🟢 **Beginner** – detailed explanations in plain language
- 🔵 **Expert** – concise, technical responses
- Selection is **automatically restored** on the next start

### COLOUR SCHEME
- 🌙 Dark / ☀ Light – switches all colours immediately, selection is saved

### API KEYS
- Enter & auto-save API key per provider
- Alternative: enter `file:/path/to/key-file` → key is read from the file at runtime

### SYSTEM PROMPT ADDITION
- Free text field for custom instructions to the AI
- **📋 button** opens a template menu with predefined prompts:
  - 🧱 FreeCAD Part-Script (forces `Part.makeBox + .cut()`, no `Part::Cut`)
  - 🤖 FreeCAD AI FC14 JSON Tools (for JSON tool-calling with FC14)
  - 🐍 Python Expert (standard)
  - 🔍 Code Analysis
  - 📐 Parametric Model
  - 🛡 Security Review
- The template can be edited directly in the field after loading
- If the text starts with **"You are"** → it replaces the base prompt entirely
- Otherwise → it is appended to the base prompt

### RETENTION
- **Max. sessions** – maximum number of stored chat sessions

### AUTO-INSERT
- When active: AI response is **automatically** inserted at the found position after stream end (equivalent to manually clicking ➕ Insert)

### THINKING (ANTHROPIC)
- **Off** (default) – normal mode
- **On** – Extended Thinking with 8,000 budget tokens; `temperature` and `top_p` are automatically omitted (API requirement)
- Only effective with Anthropic models

## 🤖 AI Panel
- **AI input field** (green background) – a single field, subdivided internally by a label:
  - **Top:** enter a question or task freely (overrides the selected preset)
  - **Code block:** below – paste code to analyse or edit
  - Both areas are sent to the AI together on `🤖 Ask`
  - Type `/snippetname` → snippet autocomplete opens
- **AI response** (blue background) – response appears live-streamed
- **Project context** – sent with every AI call as background information
- **Search/Replace** (Ctrl+F) – directly in the panel
- **💾 Save session** – save chat history + AI response + provider as `.json`
- **📂 Load session** – restore a saved session
- **🧹 Reset history** – clears the entire chat history and display
- Chat history with automatic compacting

## 🎛 Actions Panel
All action buttons at a glance:

**AI Actions**

| Button | Function |
|--------|----------|
| 📥 Load | Load selected code from editor into AI input field |
| 🔍 Mark | Search & highlight AI input field content in editor |
| 🤖 Ask | Query the AI (with current preset) |
| 🔍 Plan | **Plan mode** – display and confirm AI response before inserting |
| ✅ Replace | Replace highlighted block with AI response |
| ➕ Insert | Append AI response after the highlighted block |
| 🔎 Auto-Analyze | Explain entire code immediately |

**File Actions**

| Button | Function |
|--------|----------|
| 💾 Save | Save current file |
| 💾✕ Save & close | Save and close tab |
| ↺ Reload | Reload file (discards unsaved changes) |
| ↩ Backup | Load newest .bak backup into editor |
| 📋 Select all | Select all code |
| 🗑 Clear | Empty editor content |
| ✨ autopep8 / 🪄 Indent | Auto-format code |

**Navigation**

| Function | Description |
|----------|-------------|
| Jump to line | Enter line number → Enter |
| Code tree | All `def` and `class` shown as a live tree — double-click jumps to definition |
| Bookmarks | ＋ set · ↑↓ navigate · 🗑 delete |

**Edit & Check**

| Button | Function |
|--------|----------|
| → Indent | Indent selection by 4 spaces |
| ← Unindent | Unindent selection |
| # Toggle | Add or remove comment character |
| ⧉ Duplicate | Duplicate selection/line |
| ✂ Delete | Delete selection/line |
| ⬆ / ⬇ Move | Move line(s) up/down |
| ABC / abc / Abc | Transform case |
| ↺ Statistics | Lines, comments, def, class, import, characters |
| ▶ Syntax check | Check Python syntax → error location with line number |

**Cleanup**

| Button | Function |
|--------|----------|
| ␣ Trailing spaces | Remove whitespace at end of lines |
| ⬜ Max 2 blank lines | Trim more than 2 consecutive blank lines |
| ¶ Trailing blank lines | Remove blank lines at end of file |
| Remove BOM | Remove UTF-8 byte-order mark from file |

## 📦 Snippets Panel

**Local (Offline)**
- Categories: Document · Part · Sketcher · Mesh · Draft · PartDesign
- Click snippet → preview appears
- **↪ Into editor** or **double-click** → insert at cursor position
- **📋 Copy** → to clipboard

**Custom Snippets**
- Select code in editor → **💾 Save selected code as snippet**
- Enter a name → appears under ⭐ My Snippets
- Saved permanently in FreeCAD settings

**Online (GitHub)**
- Loads real FreeCAD macros directly from the official FreeCAD GitHub repo
- Preview loaded asynchronously (no UI freeze)
- Preview cache (max. 50 entries) for fast re-display

**Quick access in AI input field**
- Type `/` → popup opens automatically
- Continue typing to filter the list live
- Enter or click → snippet is loaded into the input field

## 💡 API Hints Panel
Offline quick reference for all important FreeCAD Python commands:
- **App** · Part · Sketcher · Mesh · Draft · Placement · Selection · GUI/View
- Search field: multiple words at once (e.g. `part shape`, `mesh vector`)
- Click a command → description appears below
- **📋 Copy signature** → paste directly into editor or AI input field

## 📂 File Browser
- Freely resizable (drag the panel edge)
- **Navigation:** `^` folder up · `Hom` home directory · `Macr` macro folder · path field + `GO`
- **Filter:** `.py` only / `.FCMacro` only / all files
- **Double-click:** `.py`/`.FCMacro` → open in editor · other files → copy path
- **Bookmarks:** ☆ button → remember folder

## 🛠 Tools Panel

Contains three sections as collapsible areas:

**📄 FreeCAD Document Context**
Current document state (objects, types, placement) is automatically appended to every AI prompt.
→ The AI "sees" what is currently open in FreeCAD.

**🛠 Direct Tools**
Predefined, safe FreeCAD operations — no coding required:

| Tool | Parameters |
|------|------------|
| **Create primitive** | Type (Box/Cylinder/Sphere/Cone/Torus), dimensions, position |
| **Boolean operation** | Type (Cut/Fuse/Common), base object, tool object |
| **Set placement** | Object name, X/Y/Z, rotation axis, rotation angle |
| **List objects** | — (shows all objects + TypeId) |
| **Run macro** | Free Python code as fallback |

Every operation runs inside a FreeCAD undo transaction → fully reversible.
Result buttons: **▶ Run** · **📥 Into editor** · **➕ Append**

**📋 Log**
All executions with timestamp, ✅/❌ status and output. 🗑 Clear button.

## 📚 Library Panel

See [Macro Library](makro-bibliothek.md) for details.

## 🔧 Tools Panel
- **Code tree:** all `def`/`class` listed automatically → double-click jumps to definition
- **Navigation:** jump to line · set/navigate/delete bookmarks
- **Edit & Check:** indent, unindent, comment, move, syntax check
- **Cleanup:** trailing spaces, blank lines, BOM

## 🔧 Helper Panel (Accessibility & Vision)

A standalone chat panel with two functions:

### Dyslexia Assistant
Convert freely written text (spelling errors OK) into a clean FreeCAD description:
```
i need a box with hole to screw on the wall
→ AI corrects → "A rectangular bracket with mounting hole for wall attachment"
```
- Real-time spell checking while typing (using `pyspellchecker`)
- Diff view of corrections (red = removed, green = added)
- Result can be transferred directly into the editor

### Send Text + Image to AI (Vision)
- **📎 Attach image** – file dialog with provider-specific formats
- **📋 From clipboard** – Ctrl+V or button
- **Drag & Drop** – drag image file directly into the input field
- Thumbnail preview with image size display and ✕ button
- Warning when the selected model does not support vision
- Allowed formats are loaded automatically per provider (no hardcoding)

| Provider | Vision models | Formats |
|----------|--------------|---------|
| Ollama (Local) | llava, bakllava, moondream, minicpm-v | JPEG, PNG, WebP, GIF, BMP |
| Anthropic (Claude) | claude-3+ | JPEG, PNG, GIF, WebP |
| OpenAI (ChatGPT) | gpt-4o, gpt-4-turbo | JPEG, PNG, GIF, WebP |
| Gemini (Google) | gemini-1.5+ | JPEG, PNG, GIF, WebP, HEIC + more |
| OpenRouter (Cloud) | model-dependent | JPEG, PNG, GIF, WebP |

## ⚠ Error Panel

See [Error Translator & Backup System](fehler-und-backup.md) for details.

---

## 🤝 Assistant Panel

An interactive step-by-step assistant with two modes:

### Normal Help Mode

Answers questions about the editor and highlights the relevant buttons and panels directly.

**Usage:**
1. Click `🤝 Assist.` in the toolbar
2. Type a question in the input field, e.g.:
   - *"how do I translate an error?"*
   - *"how do I set up Ollama?"*
   - *"how do I use plan mode?"*
3. Press **❓ Ask** or Enter
4. The AI responds in numbered steps
5. The mentioned panels/buttons light up automatically in sequence (2.2 s interval)
   – closed panels open automatically

**Notes:**
- Works with the currently selected AI provider (⚙ Settings)
- For Ollama (local) a compact system prompt is used — for cloud providers the more detailed one
- **🗑 Clear history** empties the chat display

### 🔤 Technical Language Mode (Natural Language → FreeCAD Terminology)

Toggle at the top of the Assistant panel → the assistant translates
free-form descriptions into structured FreeCAD terminology.

**Why this is useful:**
Ollama produces significantly more reliable code when given structured
terminology as input instead of free-form text. Technical language mode
is the first step in the two-stage workflow:

```
[Technical language mode ON]
Input:   "Sphere 30mm radius. Cylinder 10mm radius 60mm height through the centre"
Output:
  Part::Sphere Radius=30 mm, centre at origin.
  Part::Cylinder Radius=10 mm, Height=60 mm, Placement.Base=App.Vector(0, 0, -30).
  Part::Cut: Base=sphere, Tool=cylinder.

[Technical language mode OFF]
Paste this terminology into the FC11 input field → generate code
```

The terminology can be reviewed and corrected before being passed on.

---

## ♿ Accessibility Panel

Adjustments for visual impairment, motor difficulties, and personal preferences. All settings are
saved and automatically restored on the next start.

### 👁 Visual

| Setting | Function |
|---------|----------|
| **UI font size** (slider 8–24 pt) | Adjust font size of all labels live |
| **Editor font size** (slider 8–24 pt) | Adjust font size in the code editor |
| **High contrast** | All UI elements: white on black (overrides the theme) |
| **Icons with text** | Toolbar buttons show emoji + short name, e.g. `⚙ Settings` instead of just `⚙` |

### 🖐 Motor

| Setting | Function |
|---------|----------|
| **Button size** Normal / Large / Extra large | Height of all buttons: 26 / 34 / 42 px |
| **Keyboard mode** | Alt+1 to Alt+0 open the panels; shortcut shown in tooltip |
| **Simple view** | Hides rarely used panels from the toolbar |

### 💬 Plain Language

| Setting | Function |
|---------|----------|
| **AI responds in plain language** | AI uses short sentences, avoids jargon |
| **Explain technical terms automatically** | AI explains terms it uses immediately after |
| **Keep AI responses shorter** | Compact answers without long explanations |

### ⚙ General

| Setting | Function |
|---------|----------|
| **Tooltips always visible** | Tooltip appears immediately on hover (no delay) |
| **Reduce animations** | Button highlight lasts 300 ms instead of 1,800 ms |

---

[← Back: The User Interface](oberflaeche.md) | [Back to README](../README.md) | Next: [AI Workflow & Presets →](ki-workflow.md)
