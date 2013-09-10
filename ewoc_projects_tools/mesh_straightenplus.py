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
This addon enables you to straighten out multiple connected-edge-snakes between their endpoints.


Documentation

First go to User Preferences->Addons and enable the StraightenPlus addon in the Mesh category.
Go to EditMode, select one or more connected-edges-snakes (you can straighten several at the same time).
The vertices will be straightened out between the endpoints.  Choose amount of straightening with slider.
Restrict axis toggle restricts straightening to the view plane.
ENTER or lefmouse to end operation and keep values, rightmouse or ESC to cancel.

If you wish to hotkey StraightenPlus:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.straightenplus'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "StraightenPlus",
	"author": "Gert De Roost",
	"version": (0, 2, 7),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Straighten connected edges",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}

if "bpy" in locals():
    import imp


import bpy
import bmesh
from mathutils import *
import math


oldperc = 0
started = 0


bpy.types.Scene.CancelAxis = bpy.props.BoolProperty(
		name = "Restrict axis", 
		description = "Dont straighten along the view axis",
		default = False)

bpy.types.Scene.Percentage = bpy.props.FloatProperty(
		name = "Amount", 
		description = "Amount of straightening",
        default = 1,
        min = 0,
        max = 1)


class StraightenPlus(bpy.types.Operator):
	bl_idname = "mesh.straightenplus"
	bl_label = "StraightenPlus"
	bl_description = "Straighten edgeslices"
	bl_options = {"REGISTER", "UNDO"}
	
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):
		
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		prepare_lists()
		do_straighten()
		
		context.window_manager.modal_handler_add(self)
		
		return {'RUNNING_MODAL'}

	def modal(self, context, event):
		
		global started
		
		if event.type in ["RIGHTMOUSE", "ESC"]:
			# cancel operation, reset mesh
			for vlist in vertlist:
				for (v, co) in vlist:
					v.co = co
			bm.free()
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			started = 0
			return {'CANCELLED'}
		elif event.type in ["MIDDLEMOUSE"]:
			return {"PASS_THROUGH"}
		elif event.type in ["WHEELDOWNMOUSE", "WHEELUPMOUSE"]:
			return {"PASS_THROUGH"}
		elif event.type in ["MOUSEMOVE", "LEFTMOUSE"]:
			if 0 < event.mouse_region_y < context.region.height and event.mouse_region_x < 0: 
				return {"PASS_THROUGH"}
		if event.type in ["RET", "NUMPAD_ENTER", "LEFTMOUSE"]:
			# Consolidate changes if ENTER pressed.
			# Free the bmesh.
			bm.free()
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			started = 0
			return {'FINISHED'}
		return {'RUNNING_MODAL'}


def panel_func(self, context):
	
	global oldperc
	
	scn = bpy.context.scene
	self.layout.label(text="StraightenPlus:")
	if not(started):
		self.layout.operator("mesh.straightenplus", text="Straighten")
	else:
		self.layout.label(text="ENTER or leftmouse to confirm")
		self.layout.label(text="RightMouse or ESC to cancel")
	self.layout.prop(scn, "Percentage")
	if started and scn.Percentage != oldperc:
		do_straighten()
		oldperc = scn.Percentage
	self.layout.prop(scn, "CancelAxis")

def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)

if __name__ == "__main__":
	register()





def addstart(vert):
	
	global selset, vertlist

	# recursive: adds to initial edgelist at start
	for e in vert.link_edges:
		if e in selset:
			selset.discard(e)
			v = e.other_vert(vert)
			vertlist[posn].insert(0, (v, Vector(v.co[:])))
			addstart(v)
			break

def addend(vert):
	
	global selset, vertlist

	# recursive: adds to initial edgelist at end
	for e in vert.link_edges:
		if e in selset:
			selset.discard(e)
			v = e.other_vert(vert)
			vertlist[posn].append((v, Vector(v.co[:])))
			addend(v)
			break


def prepare_lists():

	global selset, vertlist, posn, started
	global bm, mesh

	oldperc = 0

	bpy.ops.object.editmode_toggle()
	bpy.ops.object.editmode_toggle()
	context = bpy.context
	region = context.region  
	area = context.area
	selobj = bpy.context.active_object
	mesh = selobj.data
	bm = bmesh.from_edit_mesh(mesh)

	selset = set([])
	for edge in bm.edges:
		if edge.select:
			selset.add(edge)

	posn = 0
	vertlist = []
	while len(selset) > 0:
		# initialize next edgesnake		
		vertlist.append([])
		elem = selset.pop()
		vert = elem.verts[0]
		selset.add(elem)
		vertlist[posn].append((vert, Vector(vert.co[:])))
		# add to start and end of arbitrary start vert
		addstart(vert)
		addend(vert)
		posn += 1
		
	started = 1
	


def do_straighten():
	scn = bpy.context.scene
	for vlist in vertlist:
		vstart = vlist[0][0]
		vend = vlist[len(vlist) - 1][0]
		for (vert, vco) in vlist:
			savco = vco[:]
			# P' = A + {(AB dot AP) / || AB ||^2} AB
			ab = vend.co - vstart.co
			ap = vco - vstart.co
			perpco = vstart.co + ((ab.dot(ap) / (ab.length ** 2)) * ab)
			vert.co = vco + ((perpco - vco) * (scn.Percentage))
			
			if scn.CancelAxis:
				# cancel movement in direction perp view
				delta = (vert.co - vco)
				if delta.length != 0:
					rv3d = bpy.context.space_data.region_3d
					eyevec = Vector(rv3d.view_matrix[2][:3])
					ang = delta.angle(eyevec)
					deltanor = math.cos(ang) * delta.length
					nor = eyevec
					nor.length = abs(deltanor)
					print (deltanor)
					if deltanor >= 0:
						nor = -1*nor
					vert.co = vert.co + nor		

	mesh.update()
			
		
