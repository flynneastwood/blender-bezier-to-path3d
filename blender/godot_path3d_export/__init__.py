# SPDX-FileCopyrightText: 2026 Antoine Flynn
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""glTF: Bezier Curves to Godot Path3D.

Hooks into Blender's built-in glTF 2.0 exporter. Every curve object that is
part of a normal File > Export > glTF 2.0 export gets its exact Bezier data
(control points + handles) written on its glTF node, under the
"BEZIER_path3d" extension. The companion Godot add-on reads that extension
at import time and builds Path3D / Curve3D nodes from it.

glTF has no curve primitive, so without this the curve is exported as an
empty node (or a tessellated mesh) and the Bezier data is lost.
"""

import bpy

EXTENSION_NAME = "BEZIER_path3d"
FORMAT_VERSION = 1
PANEL_KEY = "godot_path3d_export"
PRECISION = 6


class GodotPath3DExportProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Godot Path3D",
        description=(
            "Embed the Bezier data of exported curve objects in the glTF file, "
            "so the Godot add-on can import them as Path3D nodes"
        ),
        default=True,
    )


# ---------------------------------------------------------------------------
# Curve conversion
# ---------------------------------------------------------------------------

def _convert(vec, y_up):
    """Blender (Z up) -> glTF (Y up), same swizzle the glTF exporter uses."""
    if y_up:
        return (vec[0], vec[2], -vec[1])
    return (vec[0], vec[1], vec[2])


def _row(co, handle_in, handle_out, y_up):
    """One control point: position, then in/out handles RELATIVE to it."""
    values = (
        _convert(co, y_up)
        + _convert(handle_in, y_up)
        + _convert(handle_out, y_up)
    )
    # "+ 0.0" turns -0.0 into 0.0 so the JSON stays clean.
    return [round(v, PRECISION) + 0.0 for v in values]


def collect_splines(curve, y_up=True):
    """Return (splines, skipped) for a bpy.types.Curve.

    splines: list of {"closed": bool, "points": [[x,y,z, ix,iy,iz, ox,oy,oz]]}
    skipped: number of splines that cannot be represented (NURBS, < 2 points)
    """
    zero = (0.0, 0.0, 0.0)
    splines = []
    skipped = 0

    for spline in curve.splines:
        points = []

        if spline.type == 'BEZIER':
            for p in spline.bezier_points:
                points.append(_row(
                    p.co,
                    p.handle_left - p.co,
                    p.handle_right - p.co,
                    y_up,
                ))
        elif spline.type == 'POLY':
            # Straight segments: representable exactly with zero-length handles.
            for p in spline.points:
                points.append(_row(p.co.to_3d(), zero, zero, y_up))
        else:
            skipped += 1
            continue

        if len(points) < 2:
            skipped += 1
            continue

        splines.append({
            "closed": bool(spline.use_cyclic_u),
            "points": points,
        })

    return splines, skipped


# ---------------------------------------------------------------------------
# glTF exporter hook (discovered by io_scene_gltf2 through this class name)
# ---------------------------------------------------------------------------

class glTF2ExportUserExtension:

    def __init__(self):
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        scene = bpy.context.scene
        props = getattr(scene, "godot_path3d_export", None)
        self.enabled = props.enabled if props is not None else True

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        if not self.enabled:
            return
        if blender_object is None or blender_object.type != 'CURVE':
            return

        y_up = bool(export_settings.get('gltf_yup', True))
        splines, skipped = collect_splines(blender_object.data, y_up)

        if skipped:
            export_settings['log'].warning(
                "Godot Path3D: %d spline(s) of '%s' skipped "
                "(only Bezier and Poly splines with 2+ points are supported)"
                % (skipped, blender_object.name)
            )
        if not splines:
            return

        if gltf2_object.extensions is None:
            gltf2_object.extensions = {}
        gltf2_object.extensions[EXTENSION_NAME] = self.Extension(
            name=EXTENSION_NAME,
            extension={"version": FORMAT_VERSION, "splines": splines},
            required=False,
        )


# ---------------------------------------------------------------------------
# UI: one checkbox in the glTF export dialog
# ---------------------------------------------------------------------------

def draw_export(context, layout):
    props = context.scene.godot_path3d_export
    header, body = layout.panel("GLTF_addon_godot_path3d", default_closed=True)
    header.use_property_split = False
    header.prop(props, "enabled")
    if body:
        col = body.column(align=True)
        col.active = props.enabled
        col.label(text="Bezier curves are imported as Path3D", icon='CURVE_BEZCURVE')
        col.label(text="by the Godot add-on (exact handles).")


def _register_export_panel():
    try:
        from io_scene_gltf2 import exporter_extension_layout_draw
        exporter_extension_layout_draw[PANEL_KEY] = draw_export
    except Exception:
        # glTF add-on disabled or API changed: the export hook still works,
        # only the checkbox in the export dialog is missing.
        pass


def _unregister_export_panel():
    try:
        from io_scene_gltf2 import exporter_extension_layout_draw
        exporter_extension_layout_draw.pop(PANEL_KEY, None)
    except Exception:
        pass


def register():
    bpy.utils.register_class(GodotPath3DExportProperties)
    bpy.types.Scene.godot_path3d_export = bpy.props.PointerProperty(
        type=GodotPath3DExportProperties
    )
    _register_export_panel()


def unregister():
    _unregister_export_panel()
    del bpy.types.Scene.godot_path3d_export
    bpy.utils.unregister_class(GodotPath3DExportProperties)
