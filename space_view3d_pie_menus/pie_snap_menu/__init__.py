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

# <pep8 compliant>

bl_info = {
    "name": "Hotkey: 'Ctrl Shift Tab'",
    "description": "Snap Element Menu",
    #    "author": "pitiwazou, meta-androcto",
    #    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3d View",
    "warning": "",
    "wiki_url": "",
    "category": "Snap Element Pie"
    }

import bpy
from bpy.types import Menu

# Pie Snap - Shift + Tab


class PieSnaping(Menu):
    bl_idname = "pie.snapping"
    bl_label = "Pie Snapping"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("snap.vertex", text="Vertex", icon='SNAP_VERTEX')
        # 6 - RIGHT
        pie.operator("snap.face", text="Face", icon='SNAP_FACE')
        # 2 - BOTTOM
        pie.operator("snap.edge", text="Edge", icon='SNAP_EDGE')
        # 8 - TOP
        pie.prop(context.tool_settings, "use_snap", text="Snap On/Off")
        # 7 - TOP - LEFT
        pie.operator("snap.volume", text="Volume", icon='SNAP_VOLUME')
        # 9 - TOP - RIGHT
        pie.operator("snap.increment", text="Increment", icon='SNAP_INCREMENT')
        # 1 - BOTTOM - LEFT
        pie.operator("snap.alignrotation", text="Align rotation", icon='SNAP_NORMAL')
        # 3 - BOTTOM - RIGHT
        pie.operator("wm.call_menu_pie", text="Snap Target", icon='SNAP_SURFACE').name = "snap.targetmenu"


class SnapActive(bpy.types.Operator):
    bl_idname = "snap.active"
    bl_label = "Snap Active"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout

        if bpy.context.scene.tool_settings.use_snap == (True):
            bpy.context.scene.tool_settings.use_snap = False

        elif bpy.context.scene.tool_settings.use_snap == (False):
            bpy.context.scene.tool_settings.use_snap = True

        return {'FINISHED'}


class SnapVolume(bpy.types.Operator):
    bl_idname = "snap.volume"
    bl_label = "Snap Volume"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_snap == (False):
            bpy.context.scene.tool_settings.use_snap = True
            bpy.context.scene.tool_settings.snap_element = 'VOLUME'

        if bpy.context.scene.tool_settings.snap_element != 'VOLUME':
            bpy.context.scene.tool_settings.snap_element = 'VOLUME'
        return {'FINISHED'}


class SnapFace(bpy.types.Operator):
    bl_idname = "snap.face"
    bl_label = "Snap Face"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_snap == (False):
            bpy.context.scene.tool_settings.use_snap = True
            bpy.context.scene.tool_settings.snap_element = 'FACE'

        if bpy.context.scene.tool_settings.snap_element != 'FACE':
            bpy.context.scene.tool_settings.snap_element = 'FACE'
        return {'FINISHED'}


class SnapEdge(bpy.types.Operator):
    bl_idname = "snap.edge"
    bl_label = "Snap Edge"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_snap == (False):
            bpy.context.scene.tool_settings.use_snap = True
            bpy.context.scene.tool_settings.snap_element = 'EDGE'

        if bpy.context.scene.tool_settings.snap_element != 'EDGE':
            bpy.context.scene.tool_settings.snap_element = 'EDGE'
        return {'FINISHED'}


class SnapVertex(bpy.types.Operator):
    bl_idname = "snap.vertex"
    bl_label = "Snap Vertex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_snap == (False):
            bpy.context.scene.tool_settings.use_snap = True
            bpy.context.scene.tool_settings.snap_element = 'VERTEX'

        if bpy.context.scene.tool_settings.snap_element != 'VERTEX':
            bpy.context.scene.tool_settings.snap_element = 'VERTEX'
        return {'FINISHED'}


class SnapIncrement(bpy.types.Operator):
    bl_idname = "snap.increment"
    bl_label = "Snap Increment"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_snap == (False):
            bpy.context.scene.tool_settings.use_snap = True
            bpy.context.scene.tool_settings.snap_element = 'INCREMENT'

        if bpy.context.scene.tool_settings.snap_element != 'INCREMENT':
            bpy.context.scene.tool_settings.snap_element = 'INCREMENT'
        return {'FINISHED'}


class SnapAlignRotation(bpy.types.Operator):
    bl_idname = "snap.alignrotation"
    bl_label = "Snap Align rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_snap_align_rotation == (True):
            bpy.context.scene.tool_settings.use_snap_align_rotation = False

        elif bpy.context.scene.tool_settings.use_snap_align_rotation == (False):
            bpy.context.scene.tool_settings.use_snap_align_rotation = True

        return {'FINISHED'}


class SnapTargetVariable(bpy.types.Operator):
    bl_idname = "object.snaptargetvariable"
    bl_label = "Snap Target Variable"
    bl_options = {'REGISTER', 'UNDO'}
    variable = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.context.scene.tool_settings.snap_target = self.variable
        return {'FINISHED'}

# Menu Snap Target - Shift + Tab


class SnapTargetMenu(Menu):
    bl_idname = "snap.targetmenu"
    bl_label = "Snap Target Menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("object.snaptargetvariable", text="Active").variable = 'ACTIVE'
        # 6 - RIGHT
        pie.operator("object.snaptargetvariable", text="Median").variable = 'MEDIAN'
        # 2 - BOTTOM
        pie.operator("object.snaptargetvariable", text="Center").variable = 'CENTER'
        # 8 - TOP
        pie.operator("object.snaptargetvariable", text="Closest").variable = 'CLOSEST'
        # 7 - TOP - LEFT
        # 9 - TOP - RIGHT
        # 1 - BOTTOM - LEFT
        # 3 - BOTTOM - RIGHT
# Pie Snapping - Shift + Tab

classes = (
    PieSnaping,
    SnapTargetMenu,
    SnapActive,
    SnapVolume,
    SnapFace,
    SnapEdge,
    SnapVertex,
    SnapIncrement,
    SnapAlignRotation,
    SnapTargetVariable
    )

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Snapping
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'TAB', 'PRESS', ctrl=True, shift=True)
        kmi.properties.name = "pie.snapping"
#        kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View Generic']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.snapping":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
