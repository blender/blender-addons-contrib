
bl_info = {
    "name": "Hotkey: 'A'",
    "description": "Object/Edit mode Selection Menu",
    #    "author": "pitiwazou, meta-androcto",
    #    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View",
    "warning": "",
    "wiki_url": "",
    "category": "Select Pie"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

# Pie Selection Object Mode - A


class PieSelectionsMore(Menu):
    bl_idname = "pie.selectionsmore"
    bl_label = "Pie Selections Object Mode"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("object.select_by_type", text="Select By Type", icon='SNAP_VOLUME')
        box.operator("object.select_grouped", text="Select Grouped", icon='ROTATE')
        box.operator("object.select_linked", text="Select Linked", icon='CONSTRAINT_BONE')
        box.menu("VIEW3D_MT_select_object_more_less", text="More/Less")

# Pie Selection Object Mode - A


class PieSelectionsOM(Menu):
    bl_idname = "pie.selectionsom"
    bl_label = "Pie Selections Object Mode"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("object.select_by_layer", text="Select By Layer", icon='GROUP_VERTEX')
        # 6 - RIGHT
        pie.operator("object.select_random", text="Select Random", icon='GROUP_VERTEX')
        # 2 - BOTTOM
        pie.operator("object.select_all", text="Invert Selection", icon='ZOOM_PREVIOUS').action = 'INVERT'
        # 8 - TOP
        pie.operator("object.select_all", text="Select All", icon='RENDER_REGION').action = 'TOGGLE'
        # 7 - TOP - LEFT
        pie.operator("view3d.select_circle", text="Circle Select", icon='BORDER_LASSO')
        # 9 - TOP - RIGHT
        pie.operator("view3d.select_border", text="Border Select", icon='BORDER_RECT')
        # 1 - BOTTOM - LEFT
        pie.operator("object.select_camera", text="Select Camera", icon='CAMERA_DATA')
        # 3 - BOTTOM - RIGHT
        pie.menu("pie.selectionsmore", text="Select More", icon='GROUP_VERTEX')

# Pie Selection Edit Mode


class PieSelectionsEM(Menu):
    bl_idname = "pie.selectionsem"
    bl_label = "Pie Selections Edit Mode"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("view3d.select_circle", text="Circle Select", icon='BORDER_LASSO')
        # 6 - RIGHT
        pie.operator("view3d.select_border", text="Border Select", icon='BORDER_RECT')
        # 2 - BOTTOM
        pie.operator("mesh.select_all", text="Invert Selection", icon='ZOOM_PREVIOUS').action = 'INVERT'
        # 8 - TOP
        pie.operator("mesh.select_all", text="De/Select All", icon='RENDER_REGION').action = 'TOGGLE'
        # 7 - TOP - LEFT
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("mesh.select_nth", text="Checker Select", icon='PARTICLE_POINT')
        box.operator("mesh.loop_to_region", text="Select Loop Inner Region", icon='FACESEL')
        box.operator("mesh.select_similar", text="Select Similar", icon='GHOST')
        # 9 - TOP - RIGHT
        pie.operator("object.selectallbyselection", text="Complete Select", icon='RENDER_REGION')
        # 1 - BOTTOM - LEFT
        pie.operator("mesh.loop_multi_select", text="Select Ring", icon='ZOOM_PREVIOUS').ring = True
        # 3 - BOTTOM - RIGHT
        pie.operator("mesh.loop_multi_select", text="Select Loop", icon='ZOOM_PREVIOUS').ring = False

# Select All By Selection


class SelectAllBySelection(bpy.types.Operator):
    bl_idname = "object.selectallbyselection"
    bl_label = "Verts Edges Faces"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout

        bpy.ops.mesh.select_all(action='TOGGLE')
        bpy.ops.mesh.select_all(action='TOGGLE')
        return {'FINISHED'}

classes = [
    PieSelectionsOM,
    PieSelectionsEM,
    SelectAllBySelection,
    PieSelectionsMore,
    ]

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Selection Object Mode
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'A', 'PRESS')
        kmi.properties.name = "pie.selectionsom"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

        # Selection Edit Mode
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'A', 'PRESS')
        kmi.properties.name = "pie.selectionsem"
#        kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Object Mode']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.selectionsom":
                    km.keymap_items.remove(kmi)

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Mesh']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.selectionsem":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
