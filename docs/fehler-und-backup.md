[← Zurück: Makro-Bibliothek](makro-bibliothek.md) | [Zur README](../README.md) | Weiter: [Ollama – Erfahrungsbericht →](OLLAMA_ERFAHRUNGEN.md)

# Fehler-Übersetzer

FreeCAD-Fehlermeldungen auf Deutsch erklären:

```
Fehlermeldung kopieren (z.B. aus der FreeCAD-Konsole):

  AttributeError: 'NoneType' object has no attribute 'Shape'

→ In das Eingabefeld einfügen
→ 🔍 Übersetzen  (oder Strg+Enter)
→ Deutsche Erklärung:
   "Das Objekt existiert nicht oder ist noch nicht vollständig aufgebaut …"
→ Lösungsvorschlag:
   "Prüfe ob doc.getObject('...') nicht None zurückgibt …"
```

Für komplexere Fehler: **🔧 KI korrigieren** sendet Fehler + Code direkt an die KI.

Zweigeteilt: **Fehler-Tab** (im Dock) + **Fehler-Panel** (unterer Rand, immer sichtbar).

**Fehler-Tab im Dock:**
1. Englische Fehlermeldung / Traceback einfügen
2. **🔍 Übersetzen** oder **Strg+Enter**
3. Deutsche Erklärung + Lösungsvorschlag erscheint

Erkannte Fehlertypen: `AttributeError` · `TypeError` · `NameError` · `ImportError` · `No active document` · Shape-Fehler · Constraint-Fehler

**🔧 KI korrigieren:**
Fehler + aktueller Code werden direkt an die KI gesendet → Korrigierter Code erscheint in der Sandbox (max. 3 Versuche).

---

# Backup-System

- Vor jedem **✅ Ersetzen** wird automatisch eine `.bak`-Datei erstellt
- Maximal **3 Backups** je Datei (älteste werden automatisch gelöscht)
- **↩ Backup** im Aktionen-Panel lädt das neueste Backup in den Editor
- Beim Schließen mit ungespeicherten Änderungen: Speichern / Verwerfen / Abbrechen

---

[← Zurück: Makro-Bibliothek](makro-bibliothek.md) | [Zur README](../README.md) | Weiter: [Ollama – Erfahrungsbericht →](OLLAMA_ERFAHRUNGEN.md)
