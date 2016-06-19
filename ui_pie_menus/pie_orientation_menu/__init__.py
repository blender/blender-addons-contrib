
bl_info = {
    "name": "Orientation Menu: Key: 'Alt Space' ",
    "description": "Orientation Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "Alt Space",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty

class OrientationVariable(bpy.types.Operator):
    bl_idname = "object.orientationvariable"
    bl_label = "Orientation Variable"
    bl_options = {'REGISTER', 'UNDO'}
    variable = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.context.space_data.transform_orientation = self.variable
        return {'FINISHED'}

# Pie Orientation - Alt + Space
class PieOrientation(Menu):
    bl_idname = "pie.orientation"
    bl_label = "Pie Orientation"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("object.orientationvariable", text="View").variable = 'VIEW'
        # 6 - RIGHT
        pie.operator("object.orientationvariable", text="Local").variable = 'LOCAL'
        # 2 - BOTTOM
        pie.operator("object.orientationvariable", text="Normal").variable = 'NORMAL'
        # 8 - TOP
        pie.operator("object.orientationvariable", text="Global").variable = 'GLOBAL'
        # 7 - TOP - LEFT
        pie.operator("object.orientationvariable", text="Gimbal").variable = 'GIMBAL'
        # 9 - TOP - RIGHT
        # 1 - BOTTOM - LEFT

classes = [
    OrientationVariable,
    PieOrientation,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Orientation
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'SPACE', 'PRESS', alt=True)
        kmi.properties.name = "pie.orientation"
        kmi.active = True
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
                if kmi.properties.name == "pie.orientation":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
