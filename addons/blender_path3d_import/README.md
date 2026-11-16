# Blender Bezier → Path3D Import

Godot editor plugin that imports Bezier curves from Blender as `Path3D` nodes.

It reads the `BEZIER_path3d` data written into glTF/GLB files by the companion Blender extension, "glTF: Bezier Curves to Godot Path3D", and rebuilds each curve as a `Path3D` with a `Curve3D` that has the same points and handles.

## Install

1. Copy the `blender_path3d_import` folder into your project's `addons` folder.
2. Open Project > Project Settings > Plugins and enable "Blender Bezier → Path3D Import".
3. Export from Blender with File > Export > glTF 2.0 and put the file in your project. If it was already there, select it and click Reimport.

Each curve appears as a `Path3D` with the name and transform of the Blender object. Curves with several splines become a `Node3D` with one `Path3D` child per spline, and curves with bevel or extrude geometry keep their mesh and gain a `Path3D` child.

## Limits

Tilt and radius are not transferred, NURBS splines are skipped by the Blender extension, and the plugin works at editor import time, not when loading glTF at runtime.

Tested with Godot 4.7.2.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
