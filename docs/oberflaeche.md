[← Back: First Start](erststart.md) | [Back to README](../README.md) | Next: [Panels in Detail →](panels.md)

# The User Interface

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ │ ⚙ │ 🤖 │ 🎛 │ 📦 │ 💡 │ 📂 │ 🛠 │ 📚 │ 🔧 │ ⚠ │ ♿ │                          │
├──────────────┬───────────────────────────────────────────────────────────────────────┤
│              │                                                                       │
│  Dock Panel  │         Code Editor (Multi-Tab)                                       │
│  (dockable   │                                                                       │
│   left or    │                                                                       │
│   right)     │                                                                       │
│              ├───────────────────────────────────────────────────────────────────────┤
│              │  ⚠ Error Panel (bottom, collapsible)                                  │
└──────────────┴───────────────────────────────────────────────────────────────────────┘
```

**Toolbar buttons** toggle the 11 panels on and off. By default buttons show only the emoji (32 px). In the `♿ Help+Access` dock → `♿ Access` tab, labels can be enabled, e.g. `⚙ Settings`.

All panels can be:
- **Freely moved** (drag the title bar)
- **Merged into tabs** (drop one panel onto another)
- **Detached as floating windows** (double-click title bar)
- **Shown/hidden** via toolbar button

## Smart Panel Placement

The editor automatically detects whether a panel's preferred side is already occupied:

| Situation | Behavior |
|-----------|----------|
| Target side free | Panel appears on the preferred side (left or right) |
| Target side occupied | Panel automatically switches to the opposite side |
| Both sides occupied | Panel is added as a tab to an existing panel |

**⚠ Error Panel** is the only fixed element — it always appears at the bottom and never changes position.

**Panel layout is saved:** widths and positions of all panels are automatically saved on close and restored on the next start.

---

[← Back: First Start](erststart.md) | [Back to README](../README.md) | Next: [Panels in Detail →](panels.md)
