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
The FanConnect addon connects multiple selected verts to one single other vert. 


Documentation

First go to User Preferences->Addons and enable the ParEdge addon in the Mesh category.
Go to EditMode, select all verts (including the vert to connect to) and invoke 
the addon (button in the Mesh Tool panel).
Now leftclick (this will work with pre-selection highlighting) the single vert to connect to et voila...
"""


bl_info = {
	"name": "FanConnect",
	"author": "Gert De Roost",
	"version": (0, 1, 2),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Connects multiple selected verts to one single other vert.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}

if "bpy" in locals():
    import imp


import bpy
from bpy_extras import *
from bgl import *
import bmesh
from mathutils import *



class FanConnect(bpy.types.Operator):
	bl_idname = "mesh.fanconnect"
	bl_label = "Fan Connect"
	bl_description = "Connects multiple selected verts to one single other vert"
	bl_options = {"REGISTER", "UNDO"}
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		do_fanconnect(self)
		
		context.window_manager.modal_handler_add(self)
		if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
			self._handle = bpy.types.SpaceView3D.draw_handler_add(redraw, (), 'WINDOW', 'POST_PIXEL')
		else:
			self._handle = context.region.callback_add(redraw, (), 'POST_PIXEL')
		
		return {'RUNNING_MODAL'}

	def modal(self, context, event):

		global bm, mesh
		global viewchange
		global vertlist, hoververt
		
		if event.type == "LEFTMOUSE":
			# do connection
			if hoververt != None:	
				vertlist.pop(vertlist.index(hoververt))
				for v in vertlist:
					for f in hoververt.link_faces:
						if v in f.verts:
							# when already face: split it
							bmesh.utils.face_split(f, v, hoververt)
				for v in vertlist:
					v2 = None
					for e in v.link_edges:
						vertl = e.verts[:]
						vertl.pop(vertl.index(v))
						if vertl[0] in vertlist:
							v2 = vertl[0]
					if v2 != None:
						already = 0
						for f in hoververt.link_faces:
							if v in f.verts and v2 in f.verts:
								already = 1
								break
						# if no face already between to first and selected vert: make it
						if already == 0:
							bm.faces.new([v, hoververt, v2])
			bm.free()
			if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
				bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
			else:
				context.region.callback_remove(self._handle)
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			return {'FINISHED'}
		elif event.type in ["MIDDLEMOUSE"]:
			# user transforms view
			viewchange = 1
			return {"PASS_THROUGH"}
		elif event.type in ["WHEELDOWNMOUSE", "WHEELUPMOUSE"]:
			# user transforms view
			viewchange = 1		
			return {"PASS_THROUGH"}
		elif event.type == "MOUSEMOVE":
			mx = event.mouse_region_x
			my = event.mouse_region_y
			# check for vert mouse hovers over
			hoververt = None
			for v in vertlist:
				x, y, dummy = getscreencoords(v.co)
				# max distance 5 pixels
				if abs(mx - x) < 5 and abs(my - y) < 5:
					hoververt = v
					break
			region.tag_redraw()
			return {'RUNNING_MODAL'}

		
		return {'RUNNING_MODAL'}


def panel_func(self, context):
	self.layout.label(text="FanConnect:")
	self.layout.operator("mesh.fanconnect", text="Connect mult")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()







def adapt():
	
	global matrix, selobj
	
	# Rotating / panning / zooming 3D view is handled here.
	# Creates a matrix.
	if selobj.rotation_mode == "AXIS_ANGLE":
		# object rotationmode axisangle
		ang, x, y, z =  selobj.rotation_axis_angle
		matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
	elif selobj.rotation_mode == "QUATERNION":
		# object rotationmode euler
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


	





def getscreencoords(vector):
	# calculate screencoords of given Vector
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d	
	pvector = vector * matrix
	pvector = pvector + selobj.location
	
	svector = view3d_utils.location_3d_to_region_2d(region, rv3d, pvector)
	if svector == None:
		return [0, 0 ,0]
	else:
		return [svector[0], svector[1], pvector[2]]






def do_fanconnect(self):

	global bm, mesh, selobj, region
	global vertlist, viewchange

	# main operation
	context = bpy.context
	region = context.region  
	selobj = bpy.context.active_object
	mesh = selobj.data
	bm = bmesh.from_edit_mesh(mesh)
	area = bpy.context.area
	
	vertlist = []
	for v in bm.verts:
		if v.select:
			vertlist.append(v)
			
	adapt()
	
	viewchange = 0





def redraw():	

	global viewchange

	if viewchange:
		adapt()
		viewchange = 0

	# Draw mouseover highlighting.
	# Draw single verts as boxes.
	glColor3f(1.0,1.0,0)
	if hoververt != None:
		glBegin(GL_POLYGON)
		x, y, dummy = getscreencoords(hoververt.co)
		glVertex2f(x-4, y-4)
		glVertex2f(x-4, y+4)
		glVertex2f(x+4, y+4)
		glVertex2f(x+4, y-4)
		glEnd()

