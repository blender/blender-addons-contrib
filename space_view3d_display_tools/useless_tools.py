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

bl_info = {
    "name": "Useless Tools",
    "description": "Just a little collection of scripts and tools I use daily",
    "author": "Greg Zaal",
    "version": (1, 2),
    "blender": (2, 75, 0),
    "location": "Mostly 3D view toolshelf",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Tools"}


import bpy
import os

global obtypes
obtypes = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY', 'CAMERA', 'LAMP']


class UTSetSelectable(bpy.types.Operator):

    'Sets selectability for the selected objects'
    bl_idname = 'ut.set_selectable'
    bl_label = 'set selectable'
    selectable = bpy.props.BoolProperty()

    def execute(self, context,):
        for obj in bpy.context.selected_objects:
            if self.selectable == True:
                obj.hide_select = False
            else:
                obj.hide_select = True
        return {'FINISHED'}


class UTSetRenderable(bpy.types.Operator):

    'Sets renderability for the selected objects'
    bl_idname = 'ut.set_renderable'
    bl_label = 'set renderable'
    renderable = bpy.props.BoolProperty()

    def execute(self, context,):
        for obj in bpy.context.selected_objects:
            if self.renderable == True:
                obj.hide_render = False
            else:
                obj.hide_render = True
        return {'FINISHED'}


class UTAllSelectable(bpy.types.Operator):

    'Allows all objects to be selected'
    bl_idname = 'ut.all_selectable'
    bl_label = 'all selectable'

    def execute(self, context,):
        for obj in bpy.data.objects:
            obj.hide_select = False
        return {'FINISHED'}


class UTAllRenderable(bpy.types.Operator):

    'Allows all objects to be rendered'
    bl_idname = 'ut.all_renderable'
    bl_label = 'all renderable'

    def execute(self, context,):
        for obj in bpy.data.objects:
            obj.hide_render = False
        return {'FINISHED'}


class UTSelNGon(bpy.types.Operator):

    'Selects faces with more than 4 vertices'
    bl_idname = 'ut.select_ngons'
    bl_label = 'Select NGons'

    @classmethod
    def poll(cls, context):
        if not context.active_object or context.mode != 'EDIT_MESH':
            return False
        else:
            return True

    def execute(self, context):
        context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER', extend=True)
        return {'FINISHED'}


class UTWireHideSel(bpy.types.Operator):

    'Hides the wire overlay of all objects in the selection'
    bl_idname = 'ut.wirehidesel'
    bl_label = 'Hide Wire'
    show = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.context.selected_objects:
            try:
                e.show_wire = self.show
            except KeyError:
                print("Error on " + e.name)
        return {'FINISHED'}


class UTWireHideAll(bpy.types.Operator):

    'Hides the wire overlay of all objects'
    bl_idname = 'ut.wirehideall'
    bl_label = 'Hide Wire (All)'
    show = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.data.objects:
            try:
                e.show_wire = self.show
            except KeyError:
                print("Error on " + e.name)
        return {'FINISHED'}


class UTSubsurfHideSel(bpy.types.Operator):

    'Sets the Subsurf modifier of all objects in selection to be invisible in the viewport'
    bl_idname = 'ut.subsurfhidesel'
    bl_label = 'Subsurf Hide'
    show = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.context.selected_objects:
            try:
                e.modifiers['Subsurf'].show_viewport = self.show
            except KeyError:
                print("No subsurf on " + e.name + " or it is not named Subsurf")
        return {'FINISHED'}


class UTSubsurfHideAll(bpy.types.Operator):

    'Sets the Subsurf modifier of all objects to be invisible in the viewport'
    bl_idname = 'ut.subsurfhideall'
    bl_label = 'Subsurf Hide (All)'
    show = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.data.objects:
            try:
                e.modifiers['Subsurf'].show_viewport = self.show
            except KeyError:
                print("No subsurf on " + e.name + " or it is not named Subsurf")
        return {'FINISHED'}


class UTOptimalDisplaySel(bpy.types.Operator):

    'Disables Optimal Display for all Subsurf modifiers on selected objects'
    bl_idname = 'ut.optimaldisplaysel'
    bl_label = 'Optimal Display'
    on = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.context.selected_objects:
            try:
                e.modifiers['Subsurf'].show_only_control_edges = self.on
            except KeyError:
                print("No subsurf on " + e.name + " or it is not named Subsurf")
        return {'FINISHED'}


class UTOptimalDisplayAll(bpy.types.Operator):

    'Disables Optimal Display for all Subsurf modifiers'
    bl_idname = 'ut.optimaldisplayall'
    bl_label = 'Optimal Display Off (All)'
    on = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.data.objects:
            try:
                e.modifiers['Subsurf'].show_only_control_edges = self.on
            except KeyError:
                print("No subsurf on " + e.name + " or it is not named Subsurf")
        return {'FINISHED'}


class UTAllEdges(bpy.types.Operator):

    'Enables All Edges for all objects'
    bl_idname = 'ut.all_edges'
    bl_label = 'All Edges'
    on = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.data.objects:
            e.show_all_edges = self.on
        return {'FINISHED'}


class UTDoubleSided(bpy.types.Operator):

    'Disables Double Sided Normals for all objects'
    bl_idname = 'ut.double_sided'
    bl_label = 'Double Sided Normals'
    on = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for e in bpy.data.meshes:
            try:
                e.show_double_sided = self.on
            except KeyError:
                print("Error setting double sided on " + e.name)
        return {'FINISHED'}



class UTDrawTypeOp(bpy.types.Operator):

    'Sets draw type for the selected objects'
    bl_idname = 'ut.set_draw_type'
    bl_label = 'Draw Type'
    prop = bpy.props.StringProperty()

    def execute(self, context,):
        for obj in bpy.context.selected_objects:
            obj.draw_type = self.prop
        return {'FINISHED'}


class UTDrawTypeMenu(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_DrawTypeMenu'
    bl_label = "Draw Type"

    def draw(self, context):
        layout = self.layout
        layout.operator("ut.set_draw_type", text="Textured").prop = "TEXTURED"
        layout.operator("ut.set_draw_type", text="Solid").prop = "SOLID"
        layout.operator("ut.set_draw_type", text="Wire").prop = "WIRE"
        layout.operator("ut.set_draw_type", text="Bounds").prop = "BOUNDS"

