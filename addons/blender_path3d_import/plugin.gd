# SPDX-FileCopyrightText: 2026 Antoine Flynn
#
# SPDX-License-Identifier: GPL-3.0-or-later

@tool
extends EditorPlugin

const BezierPathExtension := preload("bezier_path_gltf_extension.gd")

var _extension: GLTFDocumentExtension


func _enter_tree() -> void:
	_extension = BezierPathExtension.new()
	GLTFDocument.register_gltf_document_extension(_extension)


func _exit_tree() -> void:
	if _extension != null:
		GLTFDocument.unregister_gltf_document_extension(_extension)
		_extension = null
