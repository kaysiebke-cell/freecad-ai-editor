[← Zurück: Erststart](erststart.md) | [Zur README](../README.md) | Weiter: [Panels im Detail →](panels.md)

# Die Benutzeroberfläche

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ❓Hilfe │ ⚙ │ 🤖 │ 🎛 │ 📦 │ 💡 │ 📂 │ 🛠 │ 📚 │ 🔧 │ ⚠ │ ♿ │ 🔧 │ 🤝          │
├──────────────┬───────────────────────────────────────────────────────────────────────┤
│              │                                                                       │
│  Dock-Panel  │         Code-Editor (Multi-Tab)                                       │
│  (links oder │                                                                       │
│   rechts     │                                                                       │
│   andockbar) │                                                                       │
│              ├───────────────────────────────────────────────────────────────────────┤
│              │  ⚠ Fehler-Panel (unten, einklappbar)                                  │
└──────────────┴───────────────────────────────────────────────────────────────────────┘
```

**Toolbar-Buttons** schalten die 13 Panels ein und aus. Die Buttons zeigen standardmäßig nur das Emoji (32 px). Im `♿ Zugang`-Panel kann die Beschriftung mit „Icons mit Text" eingeblendet werden, z. B. `⚙ Einst.`.

Alle Panels können:
- **Frei verschoben** werden (Titelleiste ziehen)
- **Zu Tabs zusammengefasst** werden (Panel auf Panel ablegen)
- **Als schwebendes Fenster** losgelöst werden (Doppelklick auf Titelleiste)
- Per **Toolbar-Button** ein- und ausgeblendet werden

## Intelligente Panel-Steuerung

Der Editor erkennt automatisch ob ein Panel-Platz bereits belegt ist:

| Situation | Verhalten |
|-----------|-----------|
| Ziel-Seite frei | Panel erscheint auf der bevorzugten Seite (links oder rechts) |
| Ziel-Seite belegt | Panel wechselt automatisch auf die Gegenseite |
| Beide Seiten belegt | Panel wird als Tab an ein vorhandenes Panel angehängt |

**⚠ Fehler-Panel** ist die einzige Konstante — es erscheint immer unten und wechselt nie die Position.

**Panel-Layout wird gespeichert:** Breiten und Positionen aller Panels werden beim Schließen automatisch gesichert und beim nächsten Start wiederhergestellt.

---

[← Zurück: Erststart](erststart.md) | [Zur README](../README.md) | Weiter: [Panels im Detail →](panels.md)
