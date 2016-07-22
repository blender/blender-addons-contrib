
bl_info = {
    "name": "Hotkey: 'Z'",
    "description": "Viewport Shading Menus",
#    "author": "pitiwazou, meta-androcto",
#    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View",
    "warning": "",
    "wiki_url": "",
    "category": "Shading Pie"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

# Pie Shading - Z
class PieShadingView(Menu):
    bl_idname = "pie.shadingview"
    bl_label = "Pie Shading"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.prop(context.space_data, "viewport_shade", expand=True)

        if context.active_object:
            if(context.mode == 'EDIT_MESH'):
                pie.operator("MESH_OT_faces_shade_smooth")
                pie.operator("MESH_OT_faces_shade_flat")
            else:
                pie.operator("OBJECT_OT_shade_smooth")
                pie.operator("OBJECT_OT_shade_flat")



classes = [
    PieShadingView,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Shading
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'Z', 'PRESS')
        kmi.properties.name = "pie.shadingview"
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
                if kmi.properties.name == "pie.shadingview":
                    km.keymap_items.remove(kmi)


if __name__ == "__main__":
    register()
