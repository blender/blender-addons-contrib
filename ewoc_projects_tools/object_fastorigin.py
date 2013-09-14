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
	"version": (0, 3, 0),
	"blender": (2, 6, 8),
	"location": "View3D > Tools",
	"description": "Set object origin with snapping.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Object"}



import bpy
import bpy_extras
import bmesh
from bgl import glColor3f, glBegin, GL_POLYGON, glVertex2f, glEnd
from mathutils import * 



class FastOrigin(bpy.types.Operator):
	bl_idname = "object.fastorigin"
	bl_label = "Fast Origin"
	bl_description = "Set object origin with snapping"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH')

	def invoke(self, context, event):
		
		bpy.types.Scene.PreSelOff = bpy.props.BoolProperty(
				name = "PreSelOff", 
				description = "Switch off PreSel during Straighten operation",
				default = True)
		
		self.init_fastorigin(context)
		
		context.window_manager.modal_handler_add(self)

		self._handle = bpy.types.SpaceView3D.draw_handler_add(self.redraw, (), 'WINDOW', 'POST_PIXEL')
		
		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE', 'G', 'X', 'Y', 'Z', 'MOUSEMOVE'}:
			return {'PASS_THROUGH'}
			
		elif event.type in {'RET', 'NUMPAD_ENTER'}:
			self.area.header_text_set()
			del bpy.types.Scene.PreSelOff
			# Consolidate changes.
			for v in self.vsellist:
				v.select = 1
			for e in self.esellist:
				e.select = 1
			for f in self.fsellist:
				f.select = 1
			self.bm.verts.remove(self.originvert)
			self.mesh.update()
			self.bm.free()
			self.snapelem = context.tool_settings.snap_element
			self.snapstate = context.tool_settings.use_snap
			context.tool_settings.snap_element = self.snapelsave
			context.tool_settings.use_snap = self.snapstsave
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			self.space3d.cursor_location = self.cursorsave			
			if self.mode == 'EDIT':
				bpy.ops.object.editmode_toggle()
			bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
			return {'FINISHED'}
		
		return {'RUNNING_MODAL'}


	def getmatrix(self):
		
		# Rotating / panning / zooming 3D view is handled here.
		# Calculate matrix.
		if self.selobj.rotation_mode == 'AXIS_ANGLE':
			# object rotationmode axisangle
			ang, x, y, z =  self.selobj.rotation_axis_angle
			self.matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
		elif self.selobj.rotation_mode == 'QUATERNION':
			# object rotationmode quaternion
			w, x, y, z = self.selobj.rotation_quaternion
			x = -x
			y = -y
			z = -z
			quat = Quaternion([w, x, y, z])
			self.matrix = quat.to_matrix()
			self.matrix.resize_4x4()
		else:
			# object rotationmode euler
			ax, ay, az = self.selobj.rotation_euler
			mat_rotX = Matrix.Rotation(-ax, 4, 'X')
			mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
			mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
		if self.selobj.rotation_mode == 'XYZ':
			self.matrix = mat_rotX * mat_rotY * mat_rotZ
		elif self.selobj.rotation_mode == 'XZY':
			self.matrix = mat_rotX * mat_rotZ * mat_rotY
		elif self.selobj.rotation_mode == 'YXZ':
			self.matrix = mat_rotY * mat_rotX * mat_rotZ
		elif self.selobj.rotation_mode == 'YZX':
			self.matrix = mat_rotY * mat_rotZ * mat_rotX
		elif self.selobj.rotation_mode == 'ZXY':
			self.matrix = mat_rotZ * mat_rotX * mat_rotY
		elif self.selobj.rotation_mode == 'ZYX':
			self.matrix = mat_rotZ * mat_rotY * mat_rotX
	
		# handle object scaling
		sx, sy, sz = self.selobj.scale
		mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
		mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
		mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
		self.matrix = mat_scX * mat_scY * mat_scZ * self.matrix
	
	
	
	def init_fastorigin(self, context):
	
		for space in context.area.spaces:
			if space.type == 'VIEW_3D':
				self.space3d = space
		self.selobj = context.active_object
		self.mesh = self.selobj.data
		self.area = context.area
		
		self.rv3ds = {}
		for a in bpy.context.screen.areas:
			if not(a.type == "VIEW_3D"):
				continue
			for sp in a.spaces:
				if sp.type == "VIEW_3D":
					for r in a.regions:
						if not(r.type == "WINDOW"):
							continue
						self.rv3ds[r] = sp.region_3d
						
		self.getmatrix()
		
		self.mode = self.selobj.mode
		if self.mode == 'OBJECT':
			bpy.ops.object.editmode_toggle()
		self.bm = bmesh.from_edit_mesh(self.mesh)
		
		self.vsellist = []
		self.esellist = []
		self.fsellist = []
		for v in self.bm.verts:
			if v.select:
				self.vsellist.append(v)
		for e in self.bm.edges:
			if e.select:
				self.esellist.append(e)
		for f in self.bm.faces:
			if f.select:
				self.fsellist.append(f)
			
		self.snapelem = 'VERTEX'
		self.snapstate = 1
		
		self.snapelsave = context.tool_settings.snap_element
		self.snapstsave = context.tool_settings.use_snap
		context.tool_settings.snap_element = self.snapelem
		context.tool_settings.use_snap = self.snapstate
		self.cursorsave = self.space3d.cursor_location.copy()
		for v in self.bm.verts:
			v.select = 0
		context.tool_settings.mesh_select_mode = [True, False, False]
		self.originvert = self.bm.verts.new((0, 0, 0))
		self.originvert.select = 1
		bmesh.update_edit_mesh(self.mesh, destructive=True)
		self.mesh.update()
		self.space3d.cursor_location = self.originvert.co
		
				
	def getscreencoords(self, vector, reg, rv3d):
	
		# calculate screencoords of given Vector
		vector = vector * self.matrix
		vector = vector + self.selobj.location
		return bpy_extras.view3d_utils.location_3d_to_region_2d(reg, rv3d, vector)


	
	def redraw(self):
	
		drawregion = bpy.context.region
		
		rv3d = self.rv3ds[drawregion]
		
		self.area.header_text_set(text = "FastOrigin active :  Enter to exit")
		
		self.space3d.cursor_location = self.originvert.co * self.matrix + self.selobj.location

		glColor3f(1.0,1.0,0)
		glBegin(GL_POLYGON)
		x, y = self.getscreencoords(self.originvert.co, drawregion, rv3d)
		glVertex2f(x-2, y-2)
		glVertex2f(x-2, y+2)
		glVertex2f(x+2, y+2)
		glVertex2f(x+2, y-2)
		glEnd()



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


	
