# SPDX-FileCopyrightText: 2026 Antoine Flynn
#
# SPDX-License-Identifier: GPL-3.0-or-later

@tool
extends GLTFDocumentExtension
## Turns glTF nodes carrying the "BEZIER_path3d" extension (written by the
## Blender add-on "glTF: Bezier Curves to Godot Path3D") into Path3D nodes.
##
## - Curve with a single spline and no mesh  -> the node itself is a Path3D.
## - Curve with several splines, or with a mesh (bevel/extrude geometry)
##   -> the node is kept as-is and one Path3D child is added per spline.

const EXTENSION_NAME := "BEZIER_path3d"
const SUPPORTED_VERSION := 1


func _get_supported_extensions() -> PackedStringArray:
	return PackedStringArray([EXTENSION_NAME])


func _parse_node_extensions(_state: GLTFState, gltf_node: GLTFNode, extensions: Dictionary) -> Error:
	if extensions.has(EXTENSION_NAME):
		gltf_node.set_additional_data(EXTENSION_NAME, extensions[EXTENSION_NAME])
	return OK


func _generate_scene_node(_state: GLTFState, gltf_node: GLTFNode, _scene_parent: Node) -> Node3D:
	var splines := _get_splines(gltf_node.get_additional_data(EXTENSION_NAME))
	# Only replace the node when it is a pure, single-spline curve. Otherwise
	# let Godot build the node normally; paths are added in _import_node().
	if splines.size() != 1 or gltf_node.mesh >= 0 or gltf_node.camera >= 0 or gltf_node.light >= 0:
		return null
	var curve := _build_curve(splines[0])
	if curve == null:
		return null
	var path := Path3D.new()
	path.curve = curve
	return path


func _import_node(_state: GLTFState, gltf_node: GLTFNode, _json: Dictionary, node: Node) -> Error:
	if node == null or node is Path3D:
		return OK
	var splines := _get_splines(gltf_node.get_additional_data(EXTENSION_NAME))
	if splines.is_empty():
		return OK

	var owner := node.owner if node.owner != null else node
	for i in splines.size():
		var curve := _build_curve(splines[i])
		if curve == null:
			continue
		var path := Path3D.new()
		path.curve = curve
		path.name = "%s_Path" % node.name if splines.size() == 1 else "%s_Path%d" % [node.name, i + 1]
		node.add_child(path)
		path.owner = owner
	return OK


func _get_splines(data: Variant) -> Array:
	if typeof(data) != TYPE_DICTIONARY:
		return []
	var version := int(data.get("version", 1))
	if version > SUPPORTED_VERSION:
		push_warning("%s: file uses format version %d, this add-on supports up to %d. Update the Godot add-on." % [EXTENSION_NAME, version, SUPPORTED_VERSION])
	var splines: Variant = data.get("splines", [])
	return splines if typeof(splines) == TYPE_ARRAY else []


func _build_curve(spline: Variant) -> Curve3D:
	if typeof(spline) != TYPE_DICTIONARY:
		return null
	var points: Variant = spline.get("points", [])
	if typeof(points) != TYPE_ARRAY or points.size() < 2:
		return null

	var curve := Curve3D.new()
	for p: Variant in points:
		if typeof(p) != TYPE_ARRAY or p.size() < 9:
			continue
		# [x, y, z,  in.x, in.y, in.z,  out.x, out.y, out.z] — handles are
		# relative to the point, exactly like Curve3D expects.
		curve.add_point(
			Vector3(p[0], p[1], p[2]),
			Vector3(p[3], p[4], p[5]),
			Vector3(p[6], p[7], p[8])
		)
	if curve.point_count < 2:
		return null
	curve.closed = bool(spline.get("closed", false))
	return curve
