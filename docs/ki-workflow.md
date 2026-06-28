[← Back: Panels in Detail](panels.md) | [Back to README](../README.md) | Next: [Macro from Description →](makro-generator.md)

# AI Workflow & Presets

## Standard Workflow (edit / improve code)
```
1. Select a block in the editor
2. 📥 Load  →  block appears in the AI input field
3. Choose a preset  (e.g. "Find & explain errors")
4. 🤖 Ask  →  AI response appears live
5. 🔍 Mark  →  block is highlighted in the editor
6. ✅ Replace  →  backup is created, code is replaced
```

## Quick Analysis (without selection)
```
🔎 Auto-Analyze  →  entire code is explained immediately
```

## Insert code after a block
```
Select block → 📥 Load → 🤖 Ask → ➕ Insert
→  AI response is appended AFTER the block (no overwriting)
```

## Auto-Insert (automatic after AI response)
```
⚙ Settings → AUTO-INSERT ✓ enable
→ After every stream end, the AI response is inserted automatically
→  (no manual click on ➕ Insert needed)
```
Disable this if you want to review the response before it is inserted.

## Plan Mode (review code before inserting)
```
🔍 Plan  activate (button in the Actions panel)
→ 🤖 Ask
→ ✅ Replace  →  a dialog opens showing the new code for review
   → ✅ Run     →  code is replaced
   → ❌ Cancel  →  nothing changes, no backup created
```
Ideal for critical sections — no accidental overwriting of important code.

## Save & restore session
```
💾  →  file dialog  →  save as .json
        (chat history + AI response + provider + model)

📂  →  open .json  →  everything is restored
```
On the next FreeCAD start, simply load the `.json` file and continue seamlessly.

## Using the chat history
The chat history is kept between questions. Follow-up questions build on previous answers.
After 5,000 characters the oldest part is automatically compressed (summarised).

## System prompt templates
```
⚙ Settings → SYSTEM PROMPT ADDITION → click 📋 button
→ Select a template → text appears in the field
→ Optional: edit directly in the field
→ Saved automatically
```

| Template | Use case |
|----------|----------|
| 🧱 FreeCAD Part-Script | Forces `Part.makeBox + .cut()`, prevents error-prone `Part::Cut` feature approach |
| 🤖 FreeCAD AI FC14 JSON | For JSON tool-calling with the FC14 preset |
| 🐍 Python Expert | Standard prompt for general coding tasks |
| 🔍 Code Analysis | Structured error analysis with line numbers |
| 📐 Parametric Model | All dimensions as constants, complete FreeCAD script |
| 🛡 Security Review | Critical/Medium/Low classification of security issues |

**Tip:** If your own text starts with "You are …" → it replaces the base prompt entirely. Otherwise it is appended as an addition.

---

# AI Presets

Over 40 predefined task templates in 7 categories:

## ★ Quick
- What does this code do?
- Find & explain errors
- Improve code
- Summary
- Explain simply

## 🔧 Code
- Refactoring · Add comments · Performance optimisation · Bug hunt
- SOLID refactoring · Security review · Threading · Production-ready

## ⚡ FreeCAD: Performance
- Performance analysis · Check transactions · Optimise loops

## 🧱 FreeCAD: Create
- Create macro · Parametric model · PartDesign script
- **FC11** – Macro from description (Natural language → Part code)
- **FC12** – PartDesign from description (Natural language → Body/Sketch/Pad)
- **FC13** – Build step by step (extend a model incrementally)
- Add GUI dialog

→ Details on FC11/FC12/FC13: [Macro from Description](makro-generator.md)  
→ Ollama experiences & model comparison: [Ollama Field Report](OLLAMA_ERFAHRUNGEN.md)

**Tip for Ollama + FC11:** First open the 🤝 Assistant panel and activate **🔤 Technical language mode**,
translate the natural description into structured FreeCAD terminology,
then paste that terminology into FC11. Ollama produces significantly more reliable code
from structured input than from free-form text.

## 🔍 FreeCAD: Analyse
- Error hunting · Selection macro · Mesh processing

## 📦 FreeCAD: Extend
- Workbench class · STEP/IGES export · Batch processing · Backup extension

## ✍ Documentation
- Generate docstrings · Inline comments · README section

---

[← Back: Panels in Detail](panels.md) | [Back to README](../README.md) | Next: [Macro from Description →](makro-generator.md)
