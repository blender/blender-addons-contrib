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
This addon implements a smoothing algorithm for meshes based on Laplacian relaxation, but adapted
to have no shrinkage.


Documentation

First go to User Preferences->Addons and enable the LapRelax addon in the Mesh category.
Go to EditMode, select some vertices and invoke the addon (button in the Mesh Tool panel).
Set the amount of times you want the smoothing operation to be repeated.
The mesh will be smoothed.

If you wish to hotkey LapRelax:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.laprelax'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "LapRelax",
	"author": "Gert De Roost",
	"version": (0, 1, 2),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Smoothing mesh keeping volume",
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

bpy.types.Scene.Repeat = bpy.props.IntProperty(
		name = "Repeat", 
		description = "Repeat how many times",
		default = 1,
		min = 1,
		max = 100)



class LapRelax(bpy.types.Operator):
	bl_idname = "mesh.laprelax"
	bl_label = "LapRelax"
	bl_description = "Smoothing mesh keeping volume"
	bl_options = {"REGISTER", "UNDO"}
	

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):
		
		scn = bpy.context.scene
		
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		# smooth #Repeat times
		for i in range(scn.Repeat):
			do_laprelax(self)
		
		return {'FINISHED'}


def panel_func(self, context):
	
	scn = bpy.context.scene
	self.layout.label(text="LapRelax:")
	self.layout.operator("mesh.laprelax", text="Laplace Relax")
	self.layout.prop(scn, "Repeat")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()




def do_laprelax(self):

	context = bpy.context
	region = context.region  
	area = context.area
	selobj = bpy.context.active_object
	mesh = selobj.data
	bm = bmesh.from_edit_mesh(mesh)
	bmprev = bm.copy()

	for v in bmprev.verts:
		if v.select:
			tot = Vector((0, 0, 0))
			cnt = 0
			for e in v.link_edges:
				for f in e.link_faces:
					if not(f.select):
						cnt = 1
				if len(e.link_faces) == 1:
					cnt = 1
					break
			if cnt:
				# dont affect border edges: they cause shrinkage
				continue
				
			# find Laplacian mean
			for e in v.link_edges:
				tot += e.other_vert(v).co
			tot /= len(v.link_edges)
			
			# cancel movement in direction of vertex normal
			delta = (tot - v.co)
			if delta.length != 0:
				ang = delta.angle(v.normal)
				deltanor = math.cos(ang) * delta.length
				nor = v.normal
				nor.length = abs(deltanor)
				bm.verts[v.index].co = tot + nor
		
		
	mesh.update()
	bm.free()
	bmprev.free()
	bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
	bpy.ops.object.editmode_toggle()
	bpy.ops.object.editmode_toggle()
	
