# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__bpydoc__ = """\
The FastOrigin addon enables one to interactively set the active objects origin, either by 3D
manipulator or Gkey with full support for snapping and realtime preview of this.


Documentation

First go to User Preferences->Addons and enable the FastOrigin addon in the Object category.
Select an object.  Invoke addon (button in Tools panel).  When in Object mode, addon will switch into
EditMode and create a single selected vertex which can be translated by standard means with snapping
on for vertices (this can be changed in the standard way to other targets or no snap , the snap target 
mode will be retained when using the addon a second time).  The 3D cursor will move along with the vert
to make the chosen position a bit clearer.  The old origin will remain visible during moving, this is
perfectly normal.
You can transform the view during operation.
Press ENTER to consolidate changes. 3D cursor and Editmode/Object mode
will be reset to before addon state.

REMARK - works only for mesh objects

If you wish to hotkey FastOrigin:
In the Input section of User Preferences at the bottom of the 3D View > Object Mode section click 'Add New' button.
In the Operator Identifier box put 'object.fastorigin'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "FastOrigin",
	"author": "Gert De Roost",
	"version": (0, 2, 3),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Set object origin with snapping.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Object"}

if "bpy" in locals():
    import imp


import bpy
import bmesh
from mathutils import * 

snapelem = "VERTEX"
snapstate = 1


class FastOrigin(bpy.types.Operator):
	bl_idname = "object.fastorigin"
	bl_label = "Fast Origin"
	bl_description = "Set object origin with snapping"
	bl_options = {"REGISTER", "UNDO"}
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH')

	def invoke(self, context, event):
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		do_fastorigin()
		
		context.window_manager.modal_handler_add(self)
		if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
			self._handle = bpy.types.SpaceView3D.draw_handler_add(redraw, (), 'WINDOW', 'POST_PIXEL')
		else:
			self._handle = context.region.callback_add(redraw, (), 'POST_PIXEL')
		
		return {'RUNNING_MODAL'}

	def modal(self, context, event):

		global mesh
		global snapelem, snapstate
		
		if event.type in ["LEFTMOUSE", "MIDDLEMOUSE", "RIGHTMOUSE", "WHEELDOWNMOUSE", "WHEELUPMOUSE", "G", "X", "Y", "Z", "MOUSEMOVE"]:
			return {"PASS_THROUGH"}
		elif event.type == "RET":
			# Consolidate changes.
			for v in vsellist:
				v.select = 1
			for e in esellist:
				e.select = 1
			for f in fsellist:
				f.select = 1
			bm.verts.remove(originvert)
			mesh.update()
			bm.free()
			snapelem = bpy.context.tool_settings.snap_element
			snapstate = bpy.context.tool_settings.use_snap
			bpy.context.tool_settings.snap_element = snapelsave
			bpy.context.tool_settings.use_snap = snapstsave
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
			space3d.cursor_location = cursorsave			
			if mode == "EDIT":
				bpy.ops.object.editmode_toggle()
			if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
				bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
			else:
				context.region.callback_remove(self._handle)
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			return {'FINISHED'}
		
		return {'RUNNING_MODAL'}


def panel_func(self, context):
	self.layout.label(text="FastOrigin:")
	self.layout.operator("object.fastorigin", text="Choose Origin")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)
	bpy.types.VIEW3D_PT_tools_objectmode.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)
	bpy.types.VIEW3D_PT_tools_objectmode.remove(panel_func)

if __name__ == "__main__":
	register()


def adapt():
	
	global matrix
	
	# Rotating / panning / zooming 3D view is handled here.
	# Calculate matrix.
	if selobj.rotation_mode == "AXIS_ANGLE":
		# object rotationmode axisangle
		ang, x, y, z =  selobj.rotation_axis_angle
		matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
	elif selobj.rotation_mode == "QUATERNION":
		# object rotationmode quaternion
		w, x, y, z = selobj.rotation_quaternion
		x = -x
		y = -y
		z = -z
		quat = Quaternion([w, x, y, z])
		matrix = quat.to_matrix()
		matrix.resize_4x4()
	else:
		# object rotationmode euler
		ax, ay, az = selobj.rotation_euler
		mat_rotX = Matrix.Rotation(-ax, 4, 'X')
		mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
		mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
	if selobj.rotation_mode == "XYZ":
		matrix = mat_rotX * mat_rotY * mat_rotZ
	elif selobj.rotation_mode == "XZY":
		matrix = mat_rotX * mat_rotZ * mat_rotY
	elif selobj.rotation_mode == "YXZ":
		matrix = mat_rotY * mat_rotX * mat_rotZ
	elif selobj.rotation_mode == "YZX":
		matrix = mat_rotY * mat_rotZ * mat_rotX
	elif selobj.rotation_mode == "ZXY":
		matrix = mat_rotZ * mat_rotX * mat_rotY
	elif selobj.rotation_mode == "ZYX":
		matrix = mat_rotZ * mat_rotY * mat_rotX

	# handle object scaling
	sx, sy, sz = selobj.scale
	mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
	mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
	mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
	matrix = mat_scX * mat_scY * mat_scZ * matrix




def do_fastorigin():

	global bm, mesh, mode, space3d, selobj
	global vsellist, esellist, fsellist
	global originvert, cursorsave, snapelsave, snapstsave

	context = bpy.context
	area = context.area
	for space in area.spaces:
		if space.type == "VIEW_3D":
			space3d = space
	region = context.region  
	selobj = bpy.context.active_object
	mesh = selobj.data
	
	mode = selobj.mode
	if mode == "OBJECT":
		bpy.ops.object.editmode_toggle()
	bm = bmesh.from_edit_mesh(mesh)
		
	vsellist = []
	esellist = []
	fsellist = []
	for v in bm.verts:
		if v.select:
			vsellist.append(v)
	for e in bm.edges:
		if e.select:
			esellist.append(e)
	for f in bm.faces:
		if f.select:
			fsellist.append(f)
		
	snapelsave = bpy.context.tool_settings.snap_element
	snapstsave = bpy.context.tool_settings.use_snap
	bpy.context.tool_settings.snap_element = snapelem
	bpy.context.tool_settings.use_snap = snapstate
	cursorsave = space3d.cursor_location.copy()
	for v in bm.verts:
		v.select = 0
	bpy.context.tool_settings.mesh_select_mode = [True, False, False]
	originvert = bm.verts.new((0, 0, 0))
	originvert.select = 1
	if eval(str(bpy.app.build_revision)[2:7]) > 53189:
		bmesh.update_edit_mesh(mesh, destructive=True)
	mesh.update()
	space3d.cursor_location = originvert.co
	
	
	
	
def redraw():
	
	adapt()
	space3d.cursor_location = originvert.co	* matrix + selobj.location
	
