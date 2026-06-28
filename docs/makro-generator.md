[← Back: AI Workflow & Presets](ki-workflow.md) | [Back to README](../README.md) | Next: [Snippets, API Hints & Tools →](snippets-und-werkzeuge.md)

# FC11, FC12 & FC13 – Macro from Description

Convert natural language directly into FreeCAD Python code.

## FC11 – Macro from Description (Part Workbench)
```
Select preset "FC11"
→ Type in the AI input field: "A bracket for a 20mm pipe"
→ 🤖 Ask
→ A complete FreeCAD Part macro is generated
   (Box, Cylinder, Boolean operations, Placement)
→ Review code → ✅ Replace
```
✅ Works with **all backends** including Ollama.

## FC12 – PartDesign from Description
```
Select preset "FC12"
→ Enter description
→ Generates a parametric PartDesign macro:
   Body → Sketch → Constraints → Pad/Pocket
```
⚠️ Recommended: **Claude (Anthropic)** or **GPT-4o** — too complex for local models.
⚠️ Disabled for Ollama.

## FC13 – Build Step by Step
```
Select preset "FC13"
→ Open existing code in the editor
→ Type in the AI input field: "Add a hole with 5mm radius at the top"
→ 🤖 Ask
→ Only the new code block is generated (existing code is not overwritten)
→ ➕ Insert  →  code is appended at the end
```
⚠️ **Cloud models only** — disabled for Ollama.  
Recommended: Claude (Anthropic) · GPT-4o · Groq (llama-3.3-70b) · Llama API

**Why Ollama does not work here:**
- Local 7B–8B models cannot reliably track the existing code as context
- They redefine variables instead of reusing them (`doc = App.newDocument(...)` instead of `App.ActiveDocument`)
- The context window of llama3 (8,192 tokens) is too small for longer macros
- For simple Part models with Ollama: use **FC11**

---

## Tip: Technical Language Mode for better Ollama results

Ollama produces more reliable code when given **structured FreeCAD terminology** as
input instead of free-form text. The **Assistant Tab** has a toggle for this:

```
Open 🤝 Assist. panel
→ Enable "🔤 Technical language mode"
→ Enter a natural description:
  "Sphere 30mm radius, cylinder 10mm radius 60mm height cut through the centre"
→ Assistant outputs structured terminology:
  Part::Sphere Radius=30 mm, centre at origin.
  Part::Cylinder Radius=10 mm, Height=60 mm, Placement.Base=App.Vector(0, 0, -30).
  Part::Cut: Base=sphere, Tool=cylinder.
→ Paste this terminology into FC11 → generate code
```

The result is significantly more precise than the direct NL→Code path, because Ollama
only has to handle one clearly defined task per step.

[← Back: AI Workflow & Presets](ki-workflow.md) | [Back to README](../README.md) | Next: [Snippets, API Hints & Tools →](snippets-und-werkzeuge.md)
