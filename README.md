# Blender Bezier to Path3D

Draw Bezier curves in Blender, export your scene as glTF or GLB, and get ready-to-use `Path3D` nodes in Godot, with the same points and handles.

glTF has no curve type, so Blender normally leaves curves out of the file. This repository contains both halves of the fix:

| Folder | What it is |
|---|---|
| `addons/blender_path3d_import` | Godot editor plugin. Rebuilds each curve as a `Path3D` with a `Curve3D` during import. |
| `blender/godot_path3d_export` | Blender extension. Adds the exact Bezier data of each curve to the standard glTF 2.0 export. |

You need both. Files exported with the Blender extension still import normally without the Godot plugin, only without the `Path3D` nodes.

## Install

**Blender (4.2 or later).** Download `godot_path3d_export-<version>.zip` from the [Releases](../../releases) page, then open Preferences > Get Extensions > Install from Disk.

**Godot.** Copy `addons/blender_path3d_import` into your project's `addons` folder, then enable "Blender Bezier → Path3D Import" in Project > Project Settings > Plugins.

## Use

1. In Blender, export with File > Export > glTF 2.0. Curves included in the export carry their Bezier data automatically.
2. Put the `.glb` or `.gltf` file in your Godot project. If it was there before you enabled the plugin, select it and click Reimport.
3. Each curve appears as a `Path3D` with the name and transform of the Blender object. To reach it inside the imported scene, right-click the instance and enable Editable Children.

The `examples` folder has a test scene (`CurveTest_withCurves.blend`) and its export (`curves_test.glb`), with open, closed, multi-spline, bevelled, Poly, NURBS and parented curves.

## What is converted

| In Blender | In Godot |
|---|---|
| Bezier spline | `Path3D` with identical points and handles |
| Cyclic spline | Closed curve |
| Poly spline | Curve with straight segments |
| Object with several splines | `Node3D` with one `Path3D` child per spline |
| Curve with bevel or extrude | Mesh kept, `Path3D` added as a child |

Not supported: tilt, radius, NURBS splines (skipped with a warning), curve modifiers and shape keys. The plugin works at editor import time, not when loading glTF at runtime.

## How it works

The Blender extension writes a custom, optional glTF node extension named `BEZIER_path3d`. Each point is nine numbers: position, in-handle and out-handle, in Y-up coordinates, with handles relative to the point (the `Curve3D` convention). The Godot plugin registers a `GLTFDocumentExtension` that reads it during import.

## Build the Blender extension

```
blender --command extension build --source-dir blender/godot_path3d_export --output-dir dist
```

## Compatibility

Tested with Godot 4.7.2 and Blender 5.3.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
