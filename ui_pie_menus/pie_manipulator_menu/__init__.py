
bl_info = {
    "name": "Manipulator: Key: 'Ctrl Space' ",
    "description": "Manipulator Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "Ctrl Space",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

class ManipTranslate(bpy.types.Operator):
    bl_idname = "manip.translate"
    bl_label = "Manip Translate"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show Translate"

    def execute(self, context):
        layout = self.layout
        if bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True
            bpy.context.space_data.transform_manipulators = {'TRANSLATE'}
        if bpy.context.space_data.transform_manipulators != {'TRANSLATE'}:
            bpy.context.space_data.transform_manipulators = {'TRANSLATE'}
        return {'FINISHED'}


class ManipRotate(bpy.types.Operator):
    bl_idname = "manip.rotate"
    bl_label = "Manip Rotate"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show Rotate"

    def execute(self, context):
        layout = self.layout
        if bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True
            bpy.context.space_data.transform_manipulators = {'ROTATE'}
        if bpy.context.space_data.transform_manipulators != {'ROTATE'}:
            bpy.context.space_data.transform_manipulators = {'ROTATE'}
        return {'FINISHED'}


class ManipScale(bpy.types.Operator):
    bl_idname = "manip.scale"
    bl_label = "Manip Scale"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show Scale"

    def execute(self, context):
        layout = self.layout
        if bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True
            bpy.context.space_data.transform_manipulators = {'SCALE'}
        if bpy.context.space_data.transform_manipulators != {'SCALE'}:
            bpy.context.space_data.transform_manipulators = {'SCALE'}
        return {'FINISHED'}


class TranslateRotate(bpy.types.Operator):
    bl_idname = "translate.rotate"
    bl_label = "Translate Rotate"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show Translate/Rotate"

    def execute(self, context):
        layout = self.layout
        if bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True
            bpy.context.space_data.transform_manipulators = {'TRANSLATE', 'ROTATE'}
        if bpy.context.space_data.transform_manipulators != {'TRANSLATE', 'ROTATE'}:
            bpy.context.space_data.transform_manipulators = {'TRANSLATE', 'ROTATE'}
        return {'FINISHED'}


class TranslateScale(bpy.types.Operator):
    bl_idname = "translate.scale"
    bl_label = "Translate Scale"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show Translate/Scale"

    def execute(self, context):
        layout = self.layout
        if bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True
            bpy.context.space_data.transform_manipulators = {'TRANSLATE', 'SCALE'}
        if bpy.context.space_data.transform_manipulators != {'TRANSLATE', 'SCALE'}:
            bpy.context.space_data.transform_manipulators = {'TRANSLATE', 'SCALE'}
        return {'FINISHED'}


class RotateScale(bpy.types.Operator):
    bl_idname = "rotate.scale"
    bl_label = "Rotate Scale"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show Rotate/Scale"

    def execute(self, context):
        layout = self.layout
        if bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True
            bpy.context.space_data.transform_manipulators = {'ROTATE', 'SCALE'}
        if bpy.context.space_data.transform_manipulators != {'ROTATE', 'SCALE'}:
            bpy.context.space_data.transform_manipulators = {'ROTATE', 'SCALE'}
        return {'FINISHED'}


class TranslateRotateScale(bpy.types.Operator):
    bl_idname = "translate.rotatescale"
    bl_label = "Translate Rotate Scale"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Show All"

    def execute(self, context):
        layout = self.layout
        if bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True
            bpy.context.space_data.transform_manipulators = {'TRANSLATE', 'ROTATE', 'SCALE'}
        if bpy.context.space_data.transform_manipulators != {'TRANSLATE', 'ROTATE', 'SCALE'}:
            bpy.context.space_data.transform_manipulators = {'TRANSLATE', 'ROTATE', 'SCALE'}
        return {'FINISHED'}


class WManupulators(bpy.types.Operator):
    bl_idname = "w.manupulators"
    bl_label = "W Manupulators"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show/Hide Manipulator"


    def execute(self, context):
        layout = self.layout

        if bpy.context.space_data.show_manipulator == (True):
            bpy.context.space_data.show_manipulator = False

        elif bpy.context.space_data.show_manipulator == (False):
            bpy.context.space_data.show_manipulator = True

        return {'FINISHED'}

# Pie Manipulators - Ctrl + Space
class PieManipulator(Menu):
    bl_idname = "pie.manipulator"
    bl_label = "Pie Manipulator"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("translate.scale", text="Translate/Scale")
        # 6 - RIGHT
        pie.operator("manip.rotate", text="Rotate", icon='MAN_ROT')
        # 2 - BOTTOM
        pie.operator("translate.rotatescale", text="Translate/Rotate/Scale")
        # 8 - TOP
        pie.operator("w.manupulators", text="Manipulator", icon='MANIPUL')
        # 7 - TOP - LEFT
        pie.operator("translate.rotate", text="Translate/Rotate")
        # 9 - TOP - RIGHT
        pie.operator("manip.translate", text="Translate", icon='MAN_TRANS')
        # 1 - BOTTOM - LEFT
        pie.operator("rotate.scale", text="Rotate/Scale")
        # 3 - BOTTOM - RIGHT
        pie.operator("manip.scale", text="scale", icon='MAN_SCALE')

# Pie Snapping - Shift + Tab

classes = [
    PieManipulator,
    ManipTranslate,
    ManipRotate,
    ManipScale,
    TranslateRotate,
    TranslateScale,
    RotateScale,
    TranslateRotateScale,
    WManupulators,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Manipulators
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'SPACE', 'PRESS', ctrl=True)
        kmi.properties.name = "pie.manipulator"
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
                if kmi.properties.name == "pie.manipulator":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
