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
# by meta-androcto, saidenka #

bl_info = {
    "name": "Modifier Tools",
    "author": "Meta Androcto, saidenka",
    "version": (0, 2, 0),
    "blender": (2, 77, 0),
    "location": "Properties > Modifiers",
    "description": "Modifiers Specials Show/Hide/Apply Selected",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6"
    "/Py/Scripts",
    "tracker_url": "https://developer.blender.org/maniphest/project/3/type/Bug/",
    "category": "3D View"}

import bpy
from mathutils import Vector, Matrix, Quaternion, Euler, Color

class ApplyAllModifiers(bpy.types.Operator):
    bl_idname = "object.apply_all_modifiers"
    bl_label = "Apply All"
    bl_description = "Apply All modifiers of the selected object(s)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            for mod in obj.modifiers[:]:
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
        return {'FINISHED'}


class DeleteAllModifiers(bpy.types.Operator):
    bl_idname = "object.delete_all_modifiers"
    bl_label = "Remove All"
    bl_description = "Remove All modifiers of the selected object(s)"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        for obj in context.selected_objects:
            modifiers = obj.modifiers[:]
            for modi in modifiers:
                obj.modifiers.remove(modi)
        return {'FINISHED'}


class ToggleApplyModifiersView(bpy.types.Operator):
    bl_idname = "object.toggle_apply_modifiers_view"
    bl_label = "Hide Viewport"
    bl_description = "Shows/Hide modifier of the selected object(s) in 3d View"
    bl_options = {'REGISTER'}

    def execute(self, context):
        is_apply = True
        for mod in context.active_object.modifiers:
            if (mod.show_viewport):
                is_apply = False
                break
        for obj in context.selected_objects:
            for mod in obj.modifiers:
                mod.show_viewport = is_apply
        if is_apply:
            self.report(type={"INFO"}, message="Applying modifiers to view")
        else:
            self.report(type={"INFO"}, message="Unregistered modifiers apply to the view")
        return {'FINISHED'}


class ToggleAllShowExpanded(bpy.types.Operator):
    bl_idname = "wm.toggle_all_show_expanded"
    bl_label = "Expand/Collapse All"
    bl_description = "Expand/Collapse Modifier Stack"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.active_object
        if (len(obj.modifiers)):
            vs = 0
            for mod in obj.modifiers:
                if (mod.show_expanded):
                    vs += 1
                else:
                    vs -= 1
            is_close = False
            if (0 < vs):
                is_close = True
            for mod in obj.modifiers:
                mod.show_expanded = not is_close
        else:
            self.report(type={'WARNING'}, message="Not a single modifier")
            return {'CANCELLED'}
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}

# menu
def menu(self, context):

    if (context.active_object):
        if (len(context.active_object.modifiers)):
            col = self.layout.column(align=True)
            row = col.row(align=True)
            row.operator(ApplyAllModifiers.bl_idname, icon='IMPORT', text="Apply All")
            row.operator(DeleteAllModifiers.bl_idname, icon='X', text="Delete All")
            row = col.row(align=True)
            row.operator(ToggleApplyModifiersView.bl_idname, icon='RESTRICT_VIEW_OFF', text="Viewport Vis")
            row.operator(ToggleAllShowExpanded.bl_idname, icon='FULLSCREEN_ENTER', text="Toggle Stack")


def register():
    bpy.utils.register_module(__name__)
    # Add "Specials" menu to the "Modifiers" menu
    bpy.types.DATA_PT_modifiers.prepend(menu)


def unregister():
    bpy.types.DATA_PT_modifiers.remove(menu)

    # Remove "Specials" menu from the "Modifiers" menu.
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
