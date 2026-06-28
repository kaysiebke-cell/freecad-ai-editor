[← Back: Macro from Description](makro-generator.md) | [Back to README](../README.md) | Next: [Macro Library →](makro-bibliothek.md)

# Snippets & API Hints

## Snippet Categories
- 📄 **Document** – create/load/save documents, query objects
- 🔷 **Part** – Box, Cylinder, Boolean, Placement, Shape operations
- 📐 **Sketcher** – create sketches, constraints, geometry
- 🕸 **Mesh** – import/export, convert meshes
- 📏 **Draft** – lines, circles, dimensions
- 🧩 **PartDesign** – Body, feature chain, Pad, Pocket

## API Hints Areas
- `App.*` – document, objects, settings
- `Part.*` – shapes, operations, geometry
- `Sketcher.*` – constraints, geometry
- `Mesh.*` – import/export, processing
- `Draft.*` – 2D operations
- `Placement`, `Vector`, `Rotation`
- `Gui.*`, `FreeCADGui.*` – view, selection

---

# Tools Panel

## Direct Operations (no coding required)

**Create primitive**
```
Type:     Box / Cylinder / Sphere / Cone / Torus
Dims:     Length / Width / Height / Radius
Pos.:     X / Y / Z
→ Object appears directly in FreeCAD
```

**Boolean operation**
```
Type:     Cut / Fuse / Common
Base:     name of the base object
Tool:     name of the tool object
→ Result object is created
```

**Set placement**
```
Object:   name of the object
Position: X / Y / Z
Rotation: axis (X/Y/Z), angle
→ Object is repositioned
```

All operations run inside a **FreeCAD undo transaction** — fully reversible.

---

[← Back: Macro from Description](makro-generator.md) | [Back to README](../README.md) | Next: [Macro Library →](makro-bibliothek.md)
