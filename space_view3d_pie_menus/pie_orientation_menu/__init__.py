"""Replace default list-style menu for transform orientations with a pie."""

bl_info = {
    "name": "Orientation Pie",
    "author": "Italic_",
    "version": (1, 1, 0),
    "blender": (2, 77, 0),
    "description": "",
    "location": "Hotkey: ALT + Spacebar",
    "category": "Pie Menu"}


import bpy
from bpy.types import Menu, Operator


class OrientPoll(Operator):
    bl_idname = "pie.orientation"
    bl_label = "Orientation Poll"
    bl_options = {'INTERNAL'}
    space = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return bpy.context.space_data.type == "VIEW_3D"

    def execute(self, context):
        bpy.context.space_data.transform_orientation = self.space
        return {'FINISHED'}


class OrientPie(Menu):
    bl_label = "Transform Orientation"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        view = context.space_data

        pie.operator("pie.orientation", text="Global").space = 'GLOBAL'
        pie.operator("pie.orientation", text="Local").space = 'LOCAL'
        pie.operator("pie.orientation", text="Gimbal").space = 'GIMBAL'

        # XXX: Display only custom orientations
        pie = pie.box()
        pie.prop(view, "transform_orientation", text="")
        pie = layout.menu_pie()

        pie.operator("pie.orientation", text="Normal").space = 'NORMAL'
        pie.operator("pie.orientation", text="View").space = 'VIEW'


addon_keymaps = []

classes = [
    OrientPie,
    OrientPoll
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager

    km = wm.keyconfigs.addon.keymaps['3D View']
    kmi = km.keymap_items.new('wm.call_menu_pie', 'SPACE', 'PRESS', alt=True)
    kmi.properties.name = "OrientPie"
    addon_keymaps.append(km)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        for km in addon_keymaps:
            for kmi in km.keymap_items:
                km.keymap_items.remove(kmi)

            # wm.keyconfigs.addon.keymaps.remove(km)

    addon_keymaps.clear()


if __name__ == "__main__":
    register()
