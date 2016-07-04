"""Replace default list-style menu for transform orientations with a pie."""

bl_info = {
    "name": "Hotkey: 'Alt + Spacebar'",
#    "author": "Italic_",
#    "version": (1, 1, 0),
    "blender": (2, 77, 0),
    "description": "Set Transform Orientations",
    "location": "3D View",
    "category": "Orientation Pie"}


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
    bl_idname = "pie.orient"

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

    if wm.keyconfigs.addon:
        # Manipulators
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'SPACE', 'PRESS', alt=True)
        kmi.properties.name = "pie.orient"
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
                if kmi.properties.name == "pie.orient":
                    km.keymap_items.remove(kmi)


if __name__ == "__main__":
    register()
