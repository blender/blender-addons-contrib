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
The SelProject addon enables you to "project" an object onto another object, every vertex inside the 
projection's shape will be selected.


Documentation

First go to User Preferences->Addons and enable the SelProject addon in the Mesh category.
It will appear in the Tools panel.  First set From and To object from the dropdown list.  From object
is the object you project, To object the one you project on.  If switching to editmode first,
the "Use Selection" option appears.  When choosing this you will use a copy of the selected area
instead of a From object.
Press Start SelProject to start the projection.  When in Use Selection mode, the object selected from
will be temporarily hidden for the duration of the operation.  You can use manipulator and 
G, R and S (and XYZ) hotkeys as usual to transform both objects.  Also there is the direction Empty 
which is used in combination with the origin of the From object (which will be temporarily set to
object geometry median) to set the projection direction.
Press ENTER to finalize the selection projection operation.
"""


bl_info = {
	"name": "SelProject",
	"author": "Gert De Roost",
	"version": (0, 2, 8),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Use object projection as selection tool.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}

if "bpy" in locals():
    import imp


import bpy
from bpy_extras import *
import bmesh
from bgl import *
from mathutils import *
import math


activated = 0
redomenus = 1
started = 0
cont = 0
oldobjs = None
selverts = []
fromobj = None
oldfromobj = None



bpy.types.Scene.UseSel = bpy.props.BoolProperty(
		name = "Use Selection", 
		description = "Use selected area as From object",
		default = False)

itemlist = [("Empty", "Empty", "Empty")]
bpy.types.Scene.FromObject = bpy.props.EnumProperty(
		items = itemlist,
		name = "From", 
		description = "Object to project",
		default = "Empty")

bpy.types.Scene.ToObject = bpy.props.EnumProperty(
		items = itemlist,
		name = "To", 
		description = "Object to project onto")





class Activate(bpy.types.Operator):
	bl_idname = "selproject.activate"
	bl_label = "Activate"
	bl_description = "Activate addon"
	bl_options = {"REGISTER", "UNDO"}
	
	def invoke(self, context, event):
		
		global activated
		
		setparam()
		activated = 1
	
		return {'RUNNING_MODAL'}
		

class SelProject(bpy.types.Operator):
	bl_idname = "mesh.selproject"
	bl_label = "SelProject"
	bl_description = "Use object projection as selection tool"
	bl_options = {"REGISTER", "UNDO"}
	
	def invoke(self, context, event):
		
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		do_selproject()
		
		context.window_manager.modal_handler_add(self)
		if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
			self._handle = bpy.types.SpaceView3D.draw_handler_add(redraw, (), 'WINDOW', 'POST_PIXEL')
			self._handle3 = bpy.types.SpaceView3D.draw_handler_add(setparam, (), 'WINDOW', 'POST_PIXEL')
		else:
			self._handle = context.region.callback_add(redraw, (), 'POST_PIXEL')
			self._handle3 = context.region.callback_add(setparam, (), 'POST_PIXEL')
		
		
		return {'RUNNING_MODAL'}
		
	def modal(self, context, event):

		global obF, obT, bmF, bmT, meF, meT, matrixF, matrixT
		global oldlocF, oldrotF, oldscaF, oldlocT, oldrotT, oldscaT
		global started, bigxmin, bigymin
				
		if event.type == "RET":
			if obhide != None:
				bpy.ops.object.select_all(action="DESELECT")
				obF.select = 1
				bpy.context.scene.objects.active = obF
				bpy.ops.object.delete()
				obhide.hide = 0
			bpy.ops.object.select_all(action="DESELECT")
			empt.select = 1
			bpy.context.scene.objects.active = empt
			bpy.ops.object.delete()
			obT.select = 1
			bpy.context.scene.objects.active = obT				
			started = 0
			for v in vsellist:
				v.select = 1
			for e in esellist:
				e.select = 1
			for f in fsellist:
				f.select = 1
			obF.location = originobF
			obT.location = originobT
			bmT.select_flush(1)
			bmT.to_mesh(meT)
			meT.update()
			bmF.free()
			bmT.free()
			if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
				bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
				bpy.types.SpaceView3D.draw_handler_remove(self._handle3, "WINDOW")
			else:
				context.region.callback_remove(self._handle)
				context.region.callback_remove(self._handle3)
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			bpy.ops.object.editmode_toggle()
			return {'FINISHED'}
		elif event.type in ["LEFTMOUSE", "MIDDLEMOUSE", "RIGHTMOUSE", "WHEELDOWNMOUSE", "WHEELUPMOUSE", "G", "S", "R", "X", "Y", "Z", "MOUSEMOVE"]:
			context.region.tag_redraw()
			return {"PASS_THROUGH"}

		
		return {'RUNNING_MODAL'}


def panel_func(self, context):
	
	global shrink, started, oldfromobj, fromobj, redomenus
	
	scn = bpy.context.scene
	
	self.layout.label(text="SelProject:")
	if not(activated):
		self.layout.operator("selproject.activate", text="Activate SelProject")
	else:
		if not(started):
			self.layout.operator("mesh.selproject", text="Start SelProject")
			if context.mode == "EDIT_MESH":
				self.layout.prop(scn, "UseSel")
				if not(scn.UseSel):
					self.layout.prop(scn, "FromObject")
				else:
					fromobj = bpy.context.active_object.name
					redomenus = 1
					context.region.tag_redraw()
			else:
				self.layout.prop(scn, "FromObject")
			self.layout.prop(scn, "ToObject")
		else:
			self.layout.label(text="ENTER to confirm")
	
		if scn.FromObject != oldfromobj:
			oldfromobj = scn.FromObject
			redomenus = 1
			context.region.tag_redraw()
			
		redomenus = 1



def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)
	bpy.types.VIEW3D_PT_tools_objectmode.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)
	bpy.types.VIEW3D_PT_tools_objectmode.append(panel_func)


if __name__ == "__main__":
	register()







def adapt(selobj):
	
	# Rotating / panning / zooming 3D view is handled here.
	# Creates a matrix.
	if selobj.rotation_mode == "AXIS_ANGLE":
		# object rotation_quaternionmode axisangle
		ang, x, y, z =  selobj.rotation_axis_angle
		matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
	elif selobj.rotation_mode == "QUATERNION":
		# object rotation_quaternionmode euler
		w, x, y, z = selobj.rotation_quaternion
		x = -x
		y = -y
		z = -z
		quat = Quaternion([w, x, y, z])
		matrix = quat.to_matrix()
		matrix.resize_4x4()
	else:
		# object rotation_quaternionmode euler
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
	
	return matrix


def getscreencoords(vector):
	# calculate screencoords of given Vector
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d	
	pvector = vector * matrixT
	pvector = pvector + obT.location
	
	svector = view3d_utils.location_3d_to_region_2d(region, rv3d, pvector)
	if svector == None:
		return [0, 0]
	else:
		return [svector[0], svector[1]]






def checksel():
	
	global selverts, started, matrixT
		
	selverts = []
	matrixT = adapt(obT)
	matrixF = adapt(obF).inverted()
	direc =  (obF.location - empt.location) * matrixF
	for v in bmT.verts:
		vno = v.normal
		vno.length = 0.0001
		vco = v.co + vno
		hit = obT.ray_cast(vco, vco + direc)
		if hit[2] == -1:
			vco = ((v.co * matrixT + obT.location) - obF.location) * matrixF
			vco2 = vco.copy()
			vco2 += direc * 10000
			hit = obF.ray_cast(vco, vco2)
			if hit[2] != -1:
				v.select = 1
				selverts.append(v)	





def do_selproject():

	global obF, obT, bmF, bmT, meF, meT, matrixF, matrixT, empt
	global quat
	global started, obhide, originobF, originobT
	global oldlocF, oldrotF, oldscaF, oldlocT, oldrotT, oldscaT
	global vsellist, esellist, fsellist, selverts

	obhide = None
	# main operation
	context = bpy.context
#	context.region.callback_remove(_handle3)
	region = context.region  
	selobj = bpy.context.active_object
	mesh = selobj.data
	scn = bpy.context.scene
	
	if scn.UseSel and context.mode == "EDIT_MESH":
		obhide = context.active_object
		me = obhide.data
		bmundo = bmesh.new()
		bmundo.from_mesh(me)
		objlist = []
		for obj in scn.objects:
			objlist.append(obj)
		bpy.ops.mesh.separate(type='SELECTED')
		for obj in scn.objects:
			if not(obj in objlist):
				obF = obj
		bmundo.to_mesh(me)
		bmundo.free()
		obhide.hide = 1
	else:
		obF = bpy.data.objects.get(scn.FromObject)
	if context.mode == "EDIT_MESH":
		bpy.ops.object.editmode_toggle()
	obF.select = 1
	scn.objects.active = obF
	originobF = obF.location
	bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
	meF = obF.to_mesh(scn, 1, "PREVIEW")
	bmF = bmesh.new()
	bmF.from_mesh(meF)
	
	obT = bpy.data.objects.get(scn.ToObject)
	obT.select = 1
	scn.objects.active = obT
	originobT = obT.location
	bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
	meT = obT.data
	bmT = bmesh.new()
	bmT.from_mesh(meT)
		
	vsellist = []
	for v in bmT.verts:
		if v.select:
			vsellist.append(v)
	esellist = []
	for e in bmT.edges:
		if e.select:
			esellist.append(e)
	fsellist = []
	for f in bmT.faces:
		if f.select:
			fsellist.append(f)
			
	bpy.ops.object.add(type='EMPTY', location=(obF.location + obT.location) / 2)
	empt = context.active_object
	empt.name = "SelProject_dir_empty"

	started = 1
	selverts = []


def redraw():
	
	global matrixT
	
	if started:
		checksel()
		glColor3f(1.0,1.0,0)
		for v in selverts:
			glBegin(GL_POLYGON)
			x, y = getscreencoords(v.co)
			glVertex2f(x-2, y-2)
			glVertex2f(x-2, y+2)
			glVertex2f(x+2, y+2)
			glVertex2f(x+2, y-2)
			glEnd()



def setparam():
	
	global axoff, fromobj, redomenus

	if redomenus:
		redomenus = 0
		scn = bpy.context.scene
		
		if fromobj != None and fromobj != "":
			scn.FromObject = fromobj
			fromobj = None
		
		itemlist = []
		
		scn.update()
		objs = bpy.context.scene.objects
		for ob in objs:
			if ob.type == "MESH":
				itemlist.append((ob.name, ob.name, "Set From:"))
		bpy.types.Scene.FromObject = bpy.props.EnumProperty(
				items = itemlist,
				name = "From", 
				description = "Object to project")
		if itemlist != []:
			itemlist.pop(itemlist.index((scn.FromObject, scn.FromObject, "Set From:")))
		bpy.types.Scene.ToObject = bpy.props.EnumProperty(
				items = itemlist,
				name = "To", 
				description = "Object to project onto")
	


