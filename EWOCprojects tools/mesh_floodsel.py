# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__bpydoc__ = """\
This addon enables you to "flood-select" or deselect entire areas of selected/deselected elements. 


Documentation

First go to User Preferences->Addons and enable the FloodSel addon in the Mesh category.
Go to EditMode, select one or more areas of elements.  Invoke addon (button in Mesh Tools panel)
Click area with leftmouse to select/deselect and rightmouse to cancel.	Choose "Multiple" tickbox
if you want to do several operations in succession, and ENTER to keep changes.	Click tickbox
"Preselection" to preview selection/deselection when hovering mouse over areas.
View can be transformed during operation.

If you wish to hotkey FloodSel:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.floodsel'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "FloodSel",
	"author": "Gert De Roost",
	"version": (0, 1, 2),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Flood-(de)select areas.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}

if "bpy" in locals():
	import imp


import bpy
from bpy_extras import *
import bmesh
from mathutils import *


oldviewmat = None
started = 0


bpy.types.Scene.Multiple = bpy.props.BoolProperty(
		name = "Multiple", 
		description = "Several operations after each other",
		default = False)

bpy.types.Scene.Preselection = bpy.props.BoolProperty(
		name = "Preselection", 
		description = "Preview when hovering over areas",
		default = True)

bpy.types.Scene.Diagonal = bpy.props.BoolProperty(
		name = "Diagonal is border", 
		description = "Diagonal selections are treated as borders",
		default = True)



class FloodSel(bpy.types.Operator):
	bl_idname = "mesh.floodsel"
	bl_label = "FloodSel"
	bl_description = "Flood-(de)select areas"
	bl_options = {"REGISTER", "UNDO"}
	
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):
		
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		do_prepare()
		
		context.window_manager.modal_handler_add(self)
		if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
			self._handle = bpy.types.SpaceView3D.draw_handler_add(redraw, (), 'WINDOW', 'POST_PIXEL')
		else:
			self._handle = context.region.callback_add(redraw, (), 'POST_PIXEL')
		
		return {'RUNNING_MODAL'}

	def modal(self, context, event):
		
		global viewchange, state, doneset, selset, started
		
		scn = bpy.context.scene
		if event.type == "RIGHTMOUSE":
			started = 0
			# cancel operation, reset selection state
			bpy.ops.mesh.select_all(action="DESELECT")
			for elem in baseselset:
				elem.select = 1
			bm.free()
			if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
				bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
			else:
				context.region.callback_remove(self._handle)
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			return {'CANCELLED'}
		elif event.type in ["MIDDLEMOUSE"]:
			return {"PASS_THROUGH"}
		elif event.type in ["WHEELDOWNMOUSE", "WHEELUPMOUSE"]:
			return {"PASS_THROUGH"}
		elif event.type in ["LEFTMOUSE"]:
			if event.mouse_region_x < 0:
				# this for splitting up mouse func between panel and 3d view
				return {"PASS_THROUGH"}
			if not(scn.Preselection):
				for elem in doneset:
					elem.select = not(state)
			if not(scn.Multiple):
				bm.free()
				if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
					bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
				else:
					context.region.callback_remove(self._handle)
				bpy.ops.object.editmode_toggle()
				bpy.ops.object.editmode_toggle()
				bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
				return {'FINISHED'}
			else:
				if state == 0:
					selset = selset.union(doneset)
				else:
					selset = selset.difference(doneset)
			return {"RUNNING_MODAL"}
		elif event.type == "RET":
			started = 0
			# Consolidate changes if ENTER pressed.
			# Free the bmesh.
			bm.free()
			if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
				bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
			else:
				context.region.callback_remove(self._handle)
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			return {'FINISHED'}
		elif event.type in ["MOUSEMOVE"]:
			if event.mouse_region_x <= 0:
				# this for splitting up mouse func between panel and 3d view
				return {"PASS_THROUGH"}
				
			mx = event.mouse_region_x
			my = event.mouse_region_y
			
			hoverlist = []
			for [fidx, xmin, xmax, ymin, ymax] in boundlist:
				if xmin < mx < xmax and ymin < my < ymax:
					hoverlist.append(fidx)
				
			face = None	
			bpy.ops.mesh.select_all(action="DESELECT")
			for fidx in hoverlist:
				f = bm.faces[fidx]
				pointlist = []
				for v in f.verts:
					pointlist.append(getscreencoords(v.co))
				mpoint = (mx, my)
				if insidepoly(pointlist, len(f.verts), mpoint):
					face = f
					break
			
			doneset = set([])
			for elem in selset:
				elem.select = 1
			if face == None:
				return {"RUNNING_MODAL"}
			if "VERT" in bm.select_mode:
				state = 1
				for v in face.verts:
					if not(v.select):
						state = 0
						break
				scanlist = list(face.verts[:])
				doneset = set(face.verts[:])
				while len(scanlist) > 0:
					vert = scanlist.pop()
					cands = []
					if scn.Diagonal:
						for e in vert.link_edges:
							v = e.other_vert(vert)
							cands.append(v)
					else:
						for f in vert.link_faces:
							cands.extend(list(f.verts))
					for v in cands:
						if not(v in doneset) and v.select == state:
							doneset.add(v)
							scanlist.append(v)
			if "EDGE" in bm.select_mode:
				state = 1
				testset = set(face.edges[:])
				for e in face.edges:
					if not(e.select):
						state = 0
					else:
						testset.discard(e)
				if state == 1:
					testset = set(face.edges[:])
				scanlist = list(testset)
				doneset = testset
				while len(scanlist) > 0:
					edge = scanlist.pop()
					for l in edge.link_loops:
						if l.edge == edge:
							if state == 0:
								cands = [l.link_loop_prev.edge, l.link_loop_next.edge]
							else:
								cands = l.vert.link_edges
							for e in cands:
								if e!= edge and not(e in doneset) and e.select == state:
									doneset.add(e)
									scanlist.append(e)
			if "FACE" in bm.select_mode:
				if face.select:
					state = 1
				else:
					state = 0
				scanlist = [face]
				doneset = set([face])
				while len(scanlist) > 0:
					face = scanlist.pop()
					cands = []
					if scn.Diagonal:
						for e in face.edges:
							for f in e.link_faces:
								cands.append(f)
					else:
						for v in face.verts:
							for f in v.link_faces:
								cands.append(f)
					for f in cands:
						if f != face and not(f in doneset) and f.select == state:
							doneset.add(f)
							scanlist.append(f)
			if scn.Preselection:
				for elem in doneset:
					elem.select = not(state)
			
			return {"RUNNING_MODAL"}
			
		return {'RUNNING_MODAL'}


def panel_func(self, context):
	
	scn = bpy.context.scene
	self.layout.label(text="FloodSel:")
	self.layout.operator("mesh.floodsel", text="Flood SelArea")
	self.layout.prop(scn, "Multiple")
	self.layout.prop(scn, "Preselection")
	self.layout.prop(scn, "Diagonal")

def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)

if __name__ == "__main__":
	register()




def adapt():
	
	global matrix, boundlist
	
	# Rotating / panning / zooming 3D view is handled here.
	# Calculate matrix.
	if selobj.rotation_mode == "AXIS_ANGLE":
		# object rotationmode axisangle
		ang, x, y, z =	selobj.rotation_axis_angle
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

	boundlist = []
	for f in bm.faces:
		xli = []
		yli = []
		for v in f.verts:
			x, y = getscreencoords(v.co)
			xli.append(x)
			yli.append(y)
		xmin = min(xli)
		xmax = max(xli)
		ymin = min(yli)
		ymax = max(yli)
		boundlist.append([f.index, xmin, xmax, ymin, ymax])



def getscreencoords(vector):
	# calculate screencoords of given Vector
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d 
	vector = Vector([vector[0], vector[1], vector[2]])
	pvector = vector * matrix
	pvector = pvector + selobj.location
	
	svector = view3d_utils.location_3d_to_region_2d(region, rv3d, pvector)
	if svector == None:
		return [0, 0]
	else:
		return [svector[0], svector[1]]




def do_prepare():
	
	global bm, mesh, selobj, started
	global selset, baseselset, boundlist

	started = 1
	bpy.ops.object.editmode_toggle()
	bpy.ops.object.editmode_toggle()
	context = bpy.context
	region = context.region	 
	area = context.area
	selobj = bpy.context.active_object
	mesh = selobj.data
	bm = bmesh.from_edit_mesh(mesh)
	
	selset = set([])
	if "VERT" in bm.select_mode:
		for v in bm.verts:
			if v.select:
				selset.add(v)
	if "EDGE" in bm.select_mode:
		for e in bm.edges:
			if e.select:
				selset.add(e)
	if "FACE" in bm.select_mode:
		for f in bm.faces:
			if f.select:
				selset.add(f)
	baseselset = selset.copy()
	
	adapt()


def insidepoly(polygonlist, N, p):

	counter = 0
	p1 = polygonlist[0]
	for i in range(1, N+1, 1):
		p2 = polygonlist[i % N]
		if (p[1] > min(p1[1],p2[1])):
			if (p[1] <= max(p1[1],p2[1])):
				if (p[0] <= max(p1[0],p2[0])):
					if (p1[1] != p2[1]):
						xinters = (p[1]-p1[1])*(p2[0]-p1[0])/(p2[1]-p1[1])+p1[0]
						if (p1[0] == p2[0]) or (p[0] <= xinters):
							counter += 1
		p1 = p2

	if counter % 2 == 0:
		return False
	else:
		return True



def redraw():
	
	global oldviewmat
	
	# user changes view
	viewmat = bpy.context.space_data.region_3d.perspective_matrix
	if viewmat != oldviewmat:
		adapt()
		oldviewmat = viewmat.copy()
	

