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
# Contributed to by
# meta-androcto, pkhg, zmj100, Stanislav Blinov, Piotr Komisarczyk, #
# Yi Danyang, Giuseppe De Marco, Andy Davies, Gert De Roost, liero, #
# Hidesato Ikeya, luxuy_BlenderCN, Andrew Hale, Oscurart #

bl_info = {
    "name": "Edit Tools",
    "author": "various",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "View3D > Toolshelf > Tools & Specials (W-key)",
    "description": "Add extra mesh edit tools",
    "warning": "",
    "wiki_url": "https://github.com/meta-androcto/blenderpython/wiki/AF_Edit_Tools",
    "tracker_url": "https://developer.blender.org/maniphest/project/3/type/Bug/",
    "category": "Mesh"}



if "bpy" in locals():
    import importlib
    importlib.reload(face_inset_fillet)
    importlib.reload(mesh_filletplus)
    importlib.reload(mesh_vertex_chamfer)
    importlib.reload(mesh_mextrude_plus)
    importlib.reload(mesh_offset_edges)
    importlib.reload(pkhg_faces)
    importlib.reload(mesh_edge_roundifier)
    importlib.reload(mesh_cut_faces)
    importlib.reload(split_solidify)
    importlib.reload(mesh_to_wall)
    importlib.reload(mesh_edges_length)
    importlib.reload(random_vertices)
    importlib.reload(mesh_fastloop)

else:
    from . import face_inset_fillet
    from . import mesh_filletplus
    from . import mesh_vertex_chamfer
    from . import mesh_mextrude_plus
    from . import mesh_offset_edges
    from . import pkhg_faces
    from . import mesh_edge_roundifier
    from . import mesh_cut_faces
    from . import split_solidify
    from . import mesh_to_wall
    from . import mesh_edges_length
    from . import random_vertices
    from . import mesh_fastloop

import bpy 
from bpy.props import BoolProperty
### ------ MENUS ====== ###

class VIEW3D_MT_edit_mesh_extras(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "VIEW3D_MT_edit_mesh_extras"
    bl_label = "Edit Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        mode = context.tool_settings.mesh_select_mode
        if mode[0]: 	
            split = layout.split()		
            col = split.column()
            col.label(text="Vert")
            col.operator("mesh.vertex_chamfer",
                text="Vertex Chamfer")
            col.operator("mesh.random_vertices",
                text="Random Vertices")

            row = split.row(align=True)		
            col = split.column()
            col.label(text="Utilities")
            col.operator("object_ot.fastloop",
                text="Fast loop")
            col.operator('mesh.flip_normals', text = 'Normals Flip')
            col.operator('mesh.remove_doubles', text = 'Remove Doubles')
            col.operator('mesh.subdivide', text = 'Subdivide')
            col.operator('mesh.dissolve_limited', text = 'Dissolve Limited')

        elif mode[1]: 	
            split = layout.split()		
            col = split.column()
            col.label(text="Edge")
            col.operator("fillet.op0_id",
                text="Edge Fillet Plus")
            col.operator("mesh.offset_edges",
                text="Offset Edges")
            col.operator("mesh.edge_roundifier",
                text="Edge Roundify")
            col.operator("object.mesh_edge_length_set",
                text="Set Edge Length")
            col.operator("bpt.mesh_to_wall",
                text="Edge(s) to Wall")
				
            row = split.row(align=True)		
            col = split.column()
            col.label(text="Utilities")
            col.operator("object_ot.fastloop",
                text="Fast loop")
            col.operator('mesh.flip_normals', text = 'Normals Flip')
            col.operator('mesh.remove_doubles', text = 'Remove Doubles')
            col.operator('mesh.remove_doubles', text = 'Remove Doubles')
            col.operator('mesh.subdivide', text = 'Subdivide')
            col.operator('mesh.dissolve_limited', text = 'Dissolve Limited')

        elif mode[2]: 			
            split = layout.split()		
            col = split.column()
            col.label(text="Face")
            col.operator("object.mextrude",
                text="Multi Extrude")
            col.operator("faceinfillet.op0_id",
                text="Face Inset Fillet")
            col.operator("mesh.add_faces_to_object",
                text="PKHG Faces")
            col.operator("mesh.ext_cut_faces",
                text="Cut Faces")
            col.operator("sp_sol.op0_id",
                text="Split Solidify")

            row = split.row(align=True)		
            col = split.column()
            col.label(text="Utilities")
            col.operator("object_ot.fastloop",
                text="Fast loop")
            col.operator('mesh.flip_normals', text = 'Normals Flip')
            col.operator('mesh.remove_doubles', text = 'Remove Doubles')
            col.operator('mesh.subdivide', text = 'Subdivide')
            col.operator('mesh.dissolve_limited', text = 'Dissolve Limited')


class EditToolsSettings(bpy.types.PropertyGroup):


    vert_settings = BoolProperty(
        name="Vert",
        default=False)

    edge_settings = BoolProperty(
        name="Edge",
        default=False)

    face_settings = BoolProperty(
        name="Face",
        default=False)

    utils_settings = BoolProperty(
        name="Utils",
        default=False)


class EditToolsPanel(bpy.types.Panel):
    bl_label = 'Mesh Edit Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'mesh_edit'
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        layout = self.layout
        wm = bpy.context.window_manager

        # Vert options
        box = layout.box()
        col = box.column(align=False)
        if wm.edit_tools_settings.vert_settings:
            file_icon = 'TRIA_DOWN'
        else:
            file_icon = 'TRIA_RIGHT'
        col.prop(wm.edit_tools_settings, "vert_settings",
                 icon=file_icon, toggle=True)
        if wm.edit_tools_settings.vert_settings:
            layout = self.layout
            row = layout.row()
            row.label(text="Vert Tools:", icon="VERTEXSEL")
            row = layout.split(0.70)
            row.operator('mesh.vertex_chamfer', text = 'Chamfer')
            row.operator('help.vertexchamfer', text = '?')
            row = layout.split(0.70)
            row.operator('mesh.random_vertices', text = 'Random Vertices')
            row.operator('help.random_vert', text = '?')
            row = layout.row()

        # Edge options
        box = layout.box()
        col = box.column(align=True)
        if wm.edit_tools_settings.edge_settings:
            modifier_icon = 'TRIA_DOWN'
        else:
            modifier_icon = 'TRIA_RIGHT'
        col.prop(wm.edit_tools_settings, "edge_settings",
                 icon=modifier_icon, toggle=True)
        if wm.edit_tools_settings.edge_settings:
            layout = self.layout
            row = layout.row()
            row.label(text="Edge Tools:", icon="EDGESEL")
            row = layout.split(0.70)
            row.operator('fillet.op0_id', text = 'Fillet plus')
            row.operator('help.edge_fillet', text = '?')
            row = layout.split(0.70)
            row.operator('mesh.offset_edges', text = 'Offset Edges')
            row.operator('help.offset_edges', text = '?')
            row = layout.split(0.70)
            row.operator('mesh.edge_roundifier', text = 'Roundify')
            row.operator('help.roundify', text = '?')
            row = layout.split(0.70)
            row.operator('object.mesh_edge_length_set', text = 'Set Edge Length')
            row.operator('help.roundify', text = '?')
            row = layout.split(0.70)
            row.operator('bpt.mesh_to_wall', text = 'Mesh to wall')
            row.operator('help.wall', text = '?')
            row = layout.row()

        # Face options
        box = layout.box()
        col = box.column(align=True)
        if wm.edit_tools_settings.face_settings:
            object_icon = 'TRIA_DOWN'
        else:
            object_icon = 'TRIA_RIGHT'
        col.prop(wm.edit_tools_settings, "face_settings",
                 icon=object_icon, toggle=True)
        if wm.edit_tools_settings.face_settings:
            layout = self.layout
            row = layout.row()
            row.label(text="Face Tools:", icon="FACESEL")
            row = layout.split(0.70)
            row.operator('object.mextrude', text = 'Multi Extrude')
            row.operator('help.mextrude', text = '?')
            row = layout.split(0.70)
            row.operator('faceinfillet.op0_id', text = 'Inset Fillet')
            row.operator('help.face_inset', text = '?')
            row = layout.split(0.70)
            row.operator('mesh.add_faces_to_object', text = 'Face Extrude')
            row.operator('help.pkhg', text = '?')
            row = layout.split(0.70)
            row.operator('mesh.ext_cut_faces', text = 'Cut Faces')
            row.operator('help.cut_faces', text = '?')
            row = layout.split(0.70)
            row.operator('sp_sol.op0_id', text = 'Split Solidify')
            row.operator('help.solidify', text = '?')
            row = layout.row()

        # Utils options
        box = layout.box()
        col = box.column(align=True)
        if wm.edit_tools_settings.utils_settings:
            rename_icon = 'TRIA_DOWN'
        else:
            rename_icon = 'TRIA_RIGHT'
        col.prop(wm.edit_tools_settings, "utils_settings",
                 icon=rename_icon, toggle=True)
        if wm.edit_tools_settings.utils_settings:
            layout = self.layout
            row = layout.row()
            row.label(text="Utilities:")
            row = layout.row()
            row = layout.split(0.70)
            row.operator('object_ot.fastloop', text = 'Fast Loop')
            row.operator('help.random_vert', text = '?')
            row = layout.row()
            row.operator('mesh.flip_normals', text = 'Normals Flip')
            row = layout.row()
            row.operator('mesh.remove_doubles', text = 'Remove Doubles')
            row = layout.row()
            row.operator('mesh.subdivide', text = 'Subdivide')
            row = layout.row()
            row.operator('mesh.dissolve_limited', text = 'Dissolve Limited')
# Addons Preferences
class AddonPreferences(bpy.types.AddonPreferences):
	bl_idname = __name__
	
	def draw(self, context):
		layout = self.layout
		layout.label(text="----Mesh Edit Tools----")
		layout.label(text="Collection of extra Mesh Edit Functions")
		layout.label(text="Edit Mode toolshelf or W key specials")

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu('VIEW3D_MT_edit_mesh_extras', icon='PLUGIN')

def register():

    bpy.utils.register_module(__name__)
    wm = bpy.context.window_manager
    bpy.types.WindowManager.edit_tools_settings = bpy.props.PointerProperty(type=EditToolsSettings)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)


def unregister():

    wm = bpy.context.window_manager
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

    del bpy.types.WindowManager.edit_tools_settings

if __name__ == "__main__":
    register()
