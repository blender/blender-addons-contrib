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
# meta-androcto #

bl_info = {
    "name": "Multi Extrude Plus",
    "author": "liero, macouno",
    "version": (0, 1),
    "blender": (2, 6, 3),
    "location": "View3D > Toolbar and View3D > Specials (W-key)",
    "description": "Add extra curve object types",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Modeling/Multi_Extrude",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=28570",
    "category": "Mesh"}


if "bpy" in locals():
    import imp

else:
    from . import mesh_bump
    from . import mesh_mextrude_plus

import bpy


class VIEW3D_MT_edit_mesh_bump(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "VIEW3D_MT_edit_mesh_bump"
    bl_label = "Bump"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.bump",
            text="Bump")

class ExtrudePanel(bpy.types.Panel):
    bl_label = 'Multi Extrude Plus'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        prop = layout.operator("wm.context_set_value", text="Face Select",
            icon='FACESEL')
        prop.value = "(False, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.operator('object.mextrude')
        layout.operator('mesh.bump')
        layout.operator('object.mesh2bones')

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_bump", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
