[← Back: Macro Library](makro-bibliothek.md) | [Back to README](../README.md) | Next: [Ollama – Field Report →](OLLAMA_ERFAHRUNGEN.md)

# Error Translator

Explain FreeCAD error messages in plain language:

```
Copy an error message (e.g. from the FreeCAD console):

  AttributeError: 'NoneType' object has no attribute 'Shape'

→ Paste it into the input field
→ 🔍 Translate  (or Ctrl+Enter)
→ Explanation:
   "The object does not exist or has not been fully built yet …"
→ Suggested fix:
   "Check whether doc.getObject('...') returns None …"
```

For more complex errors: **🔧 AI Fix** sends the error + current code directly to the AI.

Split into two areas: **Error Tab** (in the dock) + **Error Panel** (bottom edge, always visible).

**Error Tab in the dock:**
1. Paste an English error message / traceback
2. **🔍 Translate** or **Ctrl+Enter**
3. Plain-language explanation + suggested fix appears

Recognised error types: `AttributeError` · `TypeError` · `NameError` · `ImportError` · `No active document` · Shape errors · Constraint errors

**🔧 AI Fix:**
Error + current code are sent directly to the AI → corrected code appears in the sandbox (max. 3 attempts).

---

# Backup System

- Before every **✅ Replace**, a `.bak` file is created automatically
- Backups are stored in a dedicated **`__backups__/`** subfolder next to the original file
- Maximum **3 backups** per file (oldest are deleted automatically)
- **↩ Backup** in the Actions panel loads the newest backup into the editor
- On close with unsaved changes: Save / Discard / Cancel

```
Macro folder/
├── my_script.py
└── __backups__/
    ├── my_script.py.20260615_201500.bak
    ├── my_script.py.20260615_202100.bak
    └── my_script.py.20260615_203000.bak
```

---

[← Back: Macro Library](makro-bibliothek.md) | [Back to README](../README.md) | Next: [Ollama – Field Report →](OLLAMA_ERFAHRUNGEN.md)
