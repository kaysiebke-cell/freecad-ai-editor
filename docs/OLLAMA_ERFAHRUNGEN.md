[← Back: Error Translator & Backup System](fehler-und-backup.md) | [Back to README](../README.md)

# Ollama + FreeCAD — An Honest Field Report

This document is not a tutorial. It is an honest account from a real development project —
including all the mistakes, detours, setbacks, and what actually worked in the end.

It emerged from a collaboration between the project developer and **Claude (Anthropic)** —
an AI assistant that helped write the code, debug issues, and draft this documentation.
The "we" in this document means exactly that: a human and an AI fighting together
against the quirks of local language models.

Target audience: developers who want to integrate Ollama into a FreeCAD toolchain
and are looking for a realistic assessment before they start.

---

## The Starting Point

The goal sounded simple: the user describes in plain language what they want to build
("Create a cube with a central hole"), and Ollama generates a working FreeCAD Python macro.

What sounds simple turned out to be considerably harder than expected.

---

## The Four Installed Models — A Comparison

Four Ollama models were used and compared in real operation.
All run locally on the same hardware.

| Model | Size | Context window | FreeCAD code | Instruction following | Recommendation |
|-------|------|---------------|--------------|----------------------|----------------|
| `llama3:latest` | 4.7 GB | **8,192 tokens** | satisfactory | weak | entry level |
| `llama3.1:8b` | 4.9 GB | **131,072 tokens** | good | medium | standard choice |
| `qwen2.5-coder:7b` | 4.7 GB | **32,768 tokens** | very good | good | best choice |
| `codellama:latest` | 3.8 GB | **16,384 tokens** | satisfactory | medium | code-focused |

### What the context window means in practice

The context window determines how much text (system prompt + user request +
existing code) the model can "see" at the same time.

- **8,192 tokens (llama3):** Sufficient for simple single requests. With
  FC13 (step-by-step) the existing code is sent as context —
  that fills the window quickly. After just a few steps the model
  "forgets" what came at the beginning.

- **16,384 tokens (codellama):** Good for pure coding tasks. The model
  is specialised on code but knows the FreeCAD-specific API
  barely better than llama3.

- **32,768 tokens (qwen2.5-coder):** The best local model in our tests.
  Knows FreeCAD-adjacent Python APIs, follows instructions better,
  and hallucinates fewer fake types. Clearly recommended
  when code quality matters more than speed.

- **131,072 tokens (llama3.1):** Enormous context window — good for
  conversational scenarios and long documents. For FreeCAD code generation
  not better than qwen2.5-coder, but ideal when the entire macro code
  should be sent as context.

### Why `num_ctx` must be set explicitly

Ollama uses only 2,048 tokens as the active context window by default —
even if the model technically supports 131,072. The value must be
set explicitly in the API request:

```python
"options": {"num_ctx": 8192}   # default in the panel
```

In the AI panel, `num_ctx` is adjustable via a slider.
The default is 8,192 — a compromise between memory usage and quality.
For FC13 (step-by-step) it should be set to at least 16,384 when using llama3.1.

---

## Why use Ollama at all?

Ollama runs entirely locally. No account, no cloud, no data sharing,
no ongoing costs. This fits the Linux and open-source philosophy
this project stands under. Anyone using FreeCAD as a Flatpak on Linux
who does not want to send their CAD data to the cloud has a
serious alternative with Ollama.

| Property | Ollama (local) | Claude / GPT-4o (cloud) |
|----------|---------------|------------------------|
| Cost | free | paid |
| Privacy | fully local | data leaves the machine |
| Offline use | yes | no |
| FreeCAD API knowledge | patchy to wrong | good |
| Code generation reliability | limited | significantly better |
| Instruction following | weak | good |

---

## Installation

### Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3        # 8B parameters, approx. 4.7 GB
```

### FreeCAD as Flatpak — a world of its own

FreeCAD is frequently installed as a Flatpak. The Flatpak runs in an
isolated sandbox with its own Python interpreter at:

```
~/.var/app/org.freecad.FreeCAD/data/python/lib/python3.13/site-packages/
```

Python packages must be installed explicitly via this Python:

```bash
flatpak run --command=python3 org.freecad.FreeCAD -m pip install packagename
```

**Key insight from the project:**
Packages that require C libraries do not work inside the Flatpak sandbox.
`pyenchant` (spell checking) failed because `libenchant` was missing.
Only switching to `pyspellchecker` (pure Python) worked:

```bash
flatpak run --command=python3 org.freecad.FreeCAD -m pip install pyspellchecker
```

Test command to verify the installation landed in the right Python:

```bash
flatpak run --command=python3 org.freecad.FreeCAD -c \
  "from spellchecker import SpellChecker; s=SpellChecker(language='de'); \
   print(s.unknown(['wandsterke', 'würfel']))"
# Output: {'wandsterke'}  → correctly identified as error
```

---

## What Ollama is genuinely good at

- Producing syntactically valid Python code
- Creating simple FreeCAD Part Workbench objects
  (`Part::Box`, `Part::Cylinder`, `Part::Sphere`)
- Basic positioning via `Placement.Base`
- Correctly implementing short, clear descriptions

---

## What Ollama cannot do — the complete list

### 1. Know the FreeCAD API

This is the core problem. Local 7B–14B models do not fully know the FreeCAD API
and **invent object types and methods that do not exist**.

#### Hallucinated object types

All of the following types were generated by `llama3:latest` in real operation
and do not exist in FreeCAD:

```python
# Hallucination                    Correct alternative
"Part::UnionForTwoVolumes"     →   "Part::Fuse"
"Part::Union"                  →   "Part::Fuse"
"Part::BooleanUnion"           →   "Part::Fuse"
"Part::Merge"                  →   "Part::Fuse"
"Part::BooleanCut"             →   "Part::Cut"
"Part::Subtract"               →   "Part::Cut"
"Part::Difference"             →   "Part::Cut"
"Part::Intersection"           →   "Part::Common"
"Part::BooleanIntersection"    →   "Part::Common"
"Part::Profile2D"              →   does not exist
"Part::Extrude2D"              →   does not exist
```

#### Hallucinated methods

```python
# WRONG — generated by Ollama:
fusion = doc.addObject("Part::Fuse", "Fusion")
fusion.Add(box)       # .Add() does not exist on Part::Fuse
fusion.Add(cylinder)

# CORRECT:
fusion.Base = box
fusion.Tool = cylinder
```

#### Wrong property names

```python
# WRONG — Part::Cylinder has no .Length:
cylinder.Length = 80

# CORRECT:
cylinder.Height = 80
```

#### Completely wrong API system

One tested model (C3D-v0) generated **CadQuery code** instead of FreeCAD code —
a completely different Python CAD framework. The code was syntactically correct
and semantically meaningful, but unusable in FreeCAD.

### 2. Consistently follow instructions

Despite an explicit prohibition in the system prompt, the model regularly
produces explanatory prose after the code:

```python
box = doc.addObject("Part::Box", "Box")
box.Length = 40

The box was created successfully with dimensions 40x40x40mm.
# ^ not Python — causes SyntaxError
```

This is not an occasional error — it happens constantly.

**What helped:**
The output instruction ("Python code only") must appear at the **end** of the system prompt,
not at the beginning. Local models tend to prioritise the last instruction they see.
An instruction placed early in the prompt is overridden by rules that follow later.

### 3. Process long prompts

Beyond about 50 lines of system prompt the model loses focus. Early attempts
with detailed rule sets (100+ lines) made results **worse** instead of better.
The model then produced more explanatory text than before, because the actual
output instruction was too far back in the context.

### 4. Complex FreeCAD modes

FreeCAD PartDesign with Sketcher constraints (sketches, extrusion, pockets)
is too complex for local models. Generated code regularly contained
incorrect constraint syntax and missing Body assignments. This mode
was disabled for Ollama in the project.

### 4b. FC13 — Step-by-step: not with Ollama

FC13 is a special mode: the existing macro code is sent as context,
and the model should only append the next block — without redefining
existing variables, without repeating `import`, without duplicating
`doc = App.ActiveDocument`.

This sounds simpler than writing a complete macro — but it is not.
The model has to understand what already exists and what is still missing.
It must reuse variable names from the existing code consistently.

**Typical errors from local models in FC13:**

- `import FreeCAD as App` is repeated → `SyntaxError` from
  duplicate imports (harmless), but doc is reset to None
  if no `App.ActiveDocument` exists
- `doc = App.newDocument(...)` instead of `doc = App.ActiveDocument` →
  opens a new empty document and loses the previous state
- Variables from previous steps are recreated with different
  names → `NameError` in Boolean operations that reference the old name
- Context window too small for long existing code → the model no longer
  sees the beginning and invents its own definitions

**Result:** FC13 is hard-disabled for local Ollama models (7B–8B).
An error message explains which backends work instead
(Claude, GPT-4o, Groq, Llama API with 70B models). For simple
Part models with Ollama, FC11 is the right choice.

### 5. Correctly assign Boolean operations

The model frequently confuses "Boolean subtraction" and "union".
Concrete descriptive terms ("drill hole", "hollow out", "cut out")
work more reliably than technical terminology.

---

## Mistakes WE made

This is the part most documentation leaves out. Not all problems
came from Ollama. Some came from our own code.

### The filter that destroyed code

To filter out explanatory text, a function was written that
classifies every line: is this Python code or prose?

The classification was based on a token list:
```python
_CODE_STARTS = ("import ", "from ", "def ", "doc", "box", "zyl", ...)
```

**The problem:** Lines like `cylinder = doc.addObject(...)` start with
`cylinder` — a variable name that was not in the list.
The filter classified this line as text and commented it out.

**The result:**

```python
# cylinder = doc.addObject("Part::Cylinder", "Zylinder")  ← commented out
# cylinder.Radius = 5                                       ← commented out

cut = doc.addObject("Part::Cut", "Schnitt")
cut.Tool = cylinder  # ← NameError: name 'cylinder' is not defined
```

The `NameError` looked like it came from Ollama. It came from our filter.
This was only discovered by raw-logging the unfiltered model response.

**Fix:** Detect Python assignments via regex:
```python
# Any line of the form "identifier = ..." or "identifier.attr ..."
re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*[\(\[=]", line)
```

### The filter applied to all responses

The explanatory-text filter was designed for FC11/FC12/FC13 (natural-language modes).
It was accidentally applied to **all** AI responses — including regular preset responses
that already returned pure Python code. There it damaged code that was previously correct.

**Fix:** Flag `_nl_antwort_aktiv` that is only set for FC11/FC12/FC13.

### The expert mode that did not work

There was an expert mode that was supposed to suppress explanatory text.
The mode did not work. Cause: the expert instruction was placed as a
**prefix** before the system prompt. The long system prompt that followed it overrode it.

```python
# WRONG:
full_prompt = f"{expert_prefix}\n{system_prompt}\n{user_prompt}"
# → system_prompt overrides expert_prefix

# CORRECT:
full_prompt = f"{system_prompt}\n{expert_suffix}\n{user_prompt}"
# → expert_suffix is at the end, read last
```

### Thread safety ignored

The `_worker_mit_system` function ran in a separate thread.
It still read Qt widgets from the main thread:

```python
# WRONG — Qt widget access from worker thread:
preset = getattr(self, "_preset_box", None)
preset_name = preset.currentText()  # race condition possible
```

This can cause inconsistent state if the user changes the preset
during an AI request. Values must be captured in the main thread before the thread starts.

### The viewport that hid dock panels

The embedded FreeCAD 3D viewport was taken out of FreeCAD via `setParent()`
and embedded in the editor. This Qt call internally triggers a complete
relayout of the main window — all dock panels (AI, Actions, etc.) were hidden.

The user saw an empty window without panels after opening the preview.

**Fix:** Save dock states before `setParent()` and restore them afterwards.

---

## What actually helped

### Two-track strategy

No single measure solves the problem. Only the combination makes
the system usable:

**Track 1 — Prompt optimisation:**
- Keep prompts under 50 lines
- Context prefix: `"FreeCAD Part Workbench:\n"` before every user request
- Output instruction at the beginning AND at the end of the prompt
- Concrete descriptive terms instead of technical jargon
- One good code example in the prompt is more effective than ten rules

**Track 2 — Automatic post-processing:**
- Automatically replace all known fake types
- `.Add(x)` → `.Base = x` / `.Tool = x`
- `cylinder.Length` → `cylinder.Height`
- Pre-execution check: code is not run if known phantom types are detected
- Raw-logging every unfiltered model response for diagnostics

### Raw logging as a diagnostic tool

The most important debugging tool: log the unfiltered response
before any filter touches it.

```python
with open(os.path.expanduser("~/ollama_raw.txt"), "w", encoding="utf-8") as f:
    f.write(full_ollama_response)
```

Only with this log was it clear whether an error came from the model or our own filter.
Without this log we would have been groping in the dark.

### Disabling Ollama for certain modes

Not every task is suitable for Ollama. It does not help to keep
confronting the model with complex tasks it cannot handle.
Set clear limits: FC12 (PartDesign) and complex step-by-step modes
are disabled for Ollama — with a clear error message for the user.

---

## New Insights: Natural Language vs. Technical Terminology

This is one of the most important insights from the further course of the project.

### Ollama understands technical terminology better than natural language

When Ollama is asked to generate FreeCAD Python code directly from a
natural-language description, systematic errors arise:

- Dimensions are halved, doubled or rounded
- Boolean operations are assigned incorrectly
  (`Part::Common` instead of `Part::Fuse` for "merge")
- Placements are ignored or calculated incorrectly
- The model "interprets" instead of translating

**When Ollama is given structured FreeCAD terminology as input instead,
the generated code is significantly more reliable.**

Technical terminology here means a compact intermediate format that precisely
names the objects, dimensions and operations — without natural-language ambiguity:

```
**Sphere**
Part::Sphere Radius=30 mm, centre at origin.

**Cylinder**
Part::Cylinder Radius=10 mm, Height=60 mm, Placement.Base=App.Vector(0, 0, -30).
Part::Cut: Base=sphere, Tool=cylinder.

**Staircase pyramid**
Part::Box Length=80 mm, Width=80 mm, Height=10 mm, Placement.Base=App.Vector(-40, -40, 0).
Part::Box Length=60 mm, Width=60 mm, Height=10 mm, Placement.Base=App.Vector(-30, -30, 10).
Part::Box Length=40 mm, Width=40 mm, Height=10 mm, Placement.Base=App.Vector(-20, -20, 20).
```

Ollama then only needs to mechanically produce Python code from this input —
no interpretation, no inference about dimensions or positions.
That is a task it handles significantly better.

### The two-step approach: NL → terminology → code

This yields an effective strategy:

**Step 1:** Natural language → FreeCAD terminology  
(Assistant tab with 🔤 Technical language mode enabled)

**Step 2:** Terminology → Python code  
(FC11 macro generator with the terminology as input)

The user can review and correct between steps.
This is slower than a direct NL→code path, but significantly
more reliable — because Ollama receives a clearly defined and
solvable sub-task at each step.

### Why the fully automated two-step path failed

An initial attempt chained both steps automatically:
FC11 first called the translator, waited for the terminology, and
then sent it to the code generator.

This revealed three problems:

1. **Double wait time.** Two sequential Ollama requests take
   200+ seconds combined. That is not viable for interactive work.

2. **Errors in the first step block the second.**
   If the translator got the dimensions wrong, the code generator
   received wrong values from the start — without the user being able to intervene.

3. **Invisible intermediate result.**
   The terminology was never shown. The user ended up seeing code
   with wrong values, not knowing why — because the
   translation ran hidden.

**Solution:** The terminology translator is now a deliberately toggleable
mode in the Assistant tab (🔤 Technical language mode). The user sees the
intermediate result, can correct it, and then pastes it into FC11 themselves.
This is more transparent, faster (because the user controls both steps)
and more robust.

### Typical errors when using natural language as input

These errors occur reproducibly when Ollama generates directly from NL:

```
Input:  "Create a sphere radius 30mm with a cylinder radius 10mm
         height 60mm through the centre (bottom to top)"

Ollama (direct):
  sphere.Radius = 15   # ← halved!
  cylinder.Height = 30  # ← halved!
  fusion = doc.addObject("Part::Common", "Fusion")  # ← wrong operation
  # (Part::Common = intersection, not a through-hole)

Ollama (from terminology):
  sphere = doc.addObject("Part::Sphere", "Sphere")
  sphere.Radius = 30   # ← correct
  zyl = doc.addObject("Part::Cylinder", "Cylinder")
  zyl.Radius = 10      # ← correct
  zyl.Height = 60      # ← correct
  zyl.Placement.Base = App.Vector(0, 0, -30)
  cut = doc.addObject("Part::Cut", "Cut")
  cut.Base = sphere
  cut.Tool = zyl       # ← correct operation
```

---

## The Three Safety-Net Files

The safety net for generated Ollama code consists of three
specialised files that work together:

### 1. `data/freecad_beispiele.py` — Preventive layer (few-shot RAG)

Before Ollama sees the request, the system searches this database
for matching task-code pairs and inserts them as examples into the
prompt. Ollama learns from concrete examples what correct
FreeCAD API calls look like — without having to explain it in the prompt.

Scoring: exact tag match = 5 pts, alias (DE↔EN) = 3 pts,
partial word = 1 pt. The best matching example is placed in the prompt.

**Effect:** Many hallucinations never happen because
the model has a correct counter-example in the context.

### 2. `editor/ki/kod_korrektor.py` — Corrective layer

After generation, the produced code runs through an automatic
correction pipeline:

- All known fake object types are replaced:
  `Part::Union` → `Part::Fuse`, `Part::Subtract` → `Part::Cut` etc.
- Wrong methods are corrected:
  `.Add(obj)` → `.Base = obj` / `.Tool = obj`
- Wrong property names:
  `cylinder.Length` → `cylinder.Height`
- CadQuery calls (`Part.makeBox(...)`) are rewritten to `doc.addObject(...)`
  where possible
- `Part::Feature` and `.Shape =` lines are removed
  (produce unnecessary copies)
- `Part::Compound` is converted to `Part::Fuse` by context
  or treated as a stacking scenario

### 3. `editor/ki/kod_analyse.py` — Protective layer (pre-execution)

Before the code is actually executed, this file checks whether
any known phantom types are still in the code that the corrector
could not replace. Code containing such types never reaches `exec()`.

A half-built FreeCAD document state is hard to undo.
This check is the last line of defence.

### How the three layers interact

```
User input (terminology or natural language)
         ↓
[freecad_beispiele.py] — insert matching examples into the prompt
         ↓
Ollama generates code
         ↓
[kod_korrektor.py] — automatically fix known errors
         ↓
[kod_analyse.py] — check residual risk, abort on phantom types
         ↓
exec() — only clean code reaches this point
```

No single step is error-free. Only all three together make
the system usable in everyday work.

---

## Concrete Recommendations

1. **Never rely on the prompt alone.**
   Local models do not consistently follow rules. A downstream
   correction and validation layer is essential.

2. **Keep system prompts under 50 lines.**
   One good code example in the prompt is more effective than ten prohibitions.

3. **Log the unfiltered model response.**
   Otherwise you never know whether the model or your own filter is the problem.

4. **Build fake-type detection before exec().**
   Code with known phantom types must never reach the exec() call.
   A half-built FreeCAD document state is hard to undo.

5. **Test filter code thoroughly.**
   Especially code-detection heuristics. A filter that comments out valid code
   is worse than no filter at all.

6. **Disable complex modes for Ollama.**
   Not every feature needs to work with Ollama.

7. **Think in two tracks.**
   Prompt optimisation and code post-processing together turn an
   unreliable model into a usable tool.

8. **Prefer structured terminology over natural language as input.**
   Ollama translates structured terminology (Part::Box, Part::Fuse etc.)
   more reliably into code than free descriptive text. Anyone wanting to generate
   complex objects is better off first formulating the terminology
   (or having the assistant do it) and then feeding it to the code generator.

9. **Avoid fully automated chaining.**
   Two sequential Ollama calls (NL → terminology → code) sound
   elegant but are too slow and error-prone for interactive use.
   Better: let the user see and correct the intermediate result
   before the second step runs.

---

## Conclusion

Ollama is a good choice when privacy, cost, and offline operation
are the priority. For FreeCAD-specific code generation, the limits of local
models are noticeable — and sometimes frustrating.

The work was worth it nonetheless: the entire infrastructure
(prompts, filters, fake-type detection, corrections) is model-independent.
With Claude or GPT-4o the same architecture works — and produces
far fewer errors there, because those models know the FreeCAD API
and follow instructions.

Anyone starting with Ollama should bring realistic expectations:
it will not be error-free. But with enough post-processing it becomes usable.
And you learn more about your own codebase than expected —
because you have to catch every model error yourself.

---

[← Back: Error Translator & Backup System](fehler-und-backup.md) | [Back to README](../README.md)
