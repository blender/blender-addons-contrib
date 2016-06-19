
bl_info = {
    "name": "Text Editor: Key: 'A'",
    "description": "Text Editor",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "A key",
    "warning": "",
    "wiki_url": "",
    "category": "Text Editor"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

# Pie Text Editor 
class PieTextEditor(Menu):
    bl_idname = "pie.texteditor"
    bl_label = "Pie Text Editor"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        if bpy.context.area.type == 'TEXT_EDITOR':
            # 4 - LEFT
            pie.operator("text.comment", text="Comment", icon='FONT_DATA')
            # 6 - RIGHT
            pie.operator("text.uncomment", text="Uncomment", icon='NLA')
            # 2 - BOTTOM
            pie.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')
            # 8 - TOP
            pie.operator("text.start_find", text="Search", icon='VIEWZOOM')
            # 7 - TOP - LEFT
            pie.operator("text.indent", text="Tab (indent)", icon='FORWARD')
            # 9 - TOP - RIGHT
            pie.operator("text.unindent", text="UnTab (unindent)", icon='BACK')
            # 1 - BOTTOM - LEFT
            pie.operator("text.save", text="Save Script", icon='SAVE_COPY')
            # 3 - BOTTOM - RIGHT}

            # Search Menu


def SearchMenu(self, context):
    layout = self.layout

    layout.operator("wm.search_menu", text="", icon='VIEWZOOM')

classes = [
    PieTextEditor,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Text Editor
        km = wm.keyconfigs.addon.keymaps.new(name='Text', space_type='TEXT_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'RIGHTMOUSE', 'PRESS', ctrl=True, alt=True)
        kmi.properties.name = "pie.texteditor"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Text']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.texteditor":
                    km.keymap_items.remove(kmi)


if __name__ == "__main__":
    register()
