
bl_info = {
    "name": "Sculpt Mode: Key: 'W' &  'Alt W'",
    "description": "Sculpt Mode Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "W key & Alt W key",
    "warning": "",
    "wiki_url": "",
    "category": "Sculpt Mode"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

# Sculpt Polish
class SculptPolish(bpy.types.Operator):
    bl_idname = "sculpt.polish"
    bl_label = "Sculpt Polish"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        bpy.context.tool_settings.sculpt.brush = bpy.data.brushes['Polish']
        return {'FINISHED'}

# Sculpt Polish
class SculptSculptDraw(bpy.types.Operator):
    bl_idname = "sculpt.sculptraw"
    bl_label = "Sculpt SculptDraw"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        bpy.context.tool_settings.sculpt.brush = bpy.data.brushes['SculptDraw']
        return {'FINISHED'}

# Pie Sculp Pie Menus - W
class PieSculptPie(Menu):
    bl_idname = "pie.sculpt"
    bl_label = "Pie Sculpt"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("paint.brush_select", text="Crease", icon='BRUSH_CREASE').sculpt_tool = 'CREASE'
        # 6 - RIGHT
        pie.operator("paint.brush_select", text="Clay", icon='BRUSH_CLAY').sculpt_tool = 'CLAY'
        # 2 - BOTTOM
        pie.operator("paint.brush_select", text='Flatten', icon='BRUSH_FLATTEN').sculpt_tool = 'FLATTEN'
        # 8 - TOP
        pie.operator("paint.brush_select", text='Brush', icon='BRUSH_SCULPT_DRAW').sculpt_tool = 'DRAW'
        # 7 - TOP - LEFT
        pie.operator("paint.brush_select", text='Inflate/Deflate', icon='BRUSH_INFLATE').sculpt_tool = 'INFLATE'
        # 9 - TOP - RIGHT
        pie.operator("paint.brush_select", text='Grab', icon='BRUSH_GRAB').sculpt_tool = 'GRAB'
        # 1 - BOTTOM - LEFT
        pie.operator("paint.brush_select", text='Simplify', icon='BRUSH_DATA').sculpt_tool = 'SIMPLIFY'
        # 3 - BOTTOM - RIGHT
        pie.operator("wm.call_menu_pie", text="Others Brushes", icon='LINE_DATA').name = "pie.sculpttwo"

# Pie Sculp Pie Menus 2 - W
class PieSculpttwo(Menu):
    bl_idname = "pie.sculpttwo"
    bl_label = "Pie Sculpt 2"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("paint.brush_select", text='Claystrips', icon='BRUSH_CREASE').sculpt_tool = 'CLAY_STRIPS'
        # 6 - RIGHT
        pie.operator("paint.brush_select", text='Blob', icon='BRUSH_BLOB').sculpt_tool = 'BLOB'
        # 2 - BOTTOM
        pie.operator("paint.brush_select", text='Snakehook', icon='BRUSH_SNAKE_HOOK').sculpt_tool = 'SNAKE_HOOK'
        # 8 - TOP
        pie.operator("paint.brush_select", text='Smooth', icon='BRUSH_SMOOTH').sculpt_tool = 'SMOOTH'
        # 7 - TOP - LEFT
        pie.operator("paint.brush_select", text='Pinch/Magnify', icon='BRUSH_PINCH').sculpt_tool = 'PINCH'
        # 9 - TOP - RIGHT
        pie.operator("sculpt.polish", text='Polish', icon='BRUSH_FLATTEN')
        # 1 - BOTTOM - LEFT
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("paint.brush_select", text='Twist', icon='BRUSH_ROTATE').sculpt_tool = 'ROTATE'
        box.operator("paint.brush_select", text='Scrape/Peaks', icon='BRUSH_SCRAPE').sculpt_tool = 'SCRAPE'
        box.operator("sculpt.sculptraw", text='SculptDraw', icon='BRUSH_SCULPT_DRAW')
        box.operator("paint.brush_select", text='Mask', icon='BRUSH_MASK').sculpt_tool = 'MASK'
        # 3 - BOTTOM - RIGHT
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("paint.brush_select", text='Layer', icon='BRUSH_LAYER').sculpt_tool = 'LAYER'
        box.operator("paint.brush_select", text='Nudge', icon='BRUSH_NUDGE').sculpt_tool = 'NUDGE'
        box.operator("paint.brush_select", text='Thumb', icon='BRUSH_THUMB').sculpt_tool = 'THUMB'
        box.operator("paint.brush_select", text='Fill/Deepen', icon='BRUSH_FILL').sculpt_tool = 'FILL'

classes = [
    PieSculptPie,
    PieSculpttwo,
    SculptPolish,
    SculptSculptDraw,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Sculpt Pie Menu
        km = wm.keyconfigs.addon.keymaps.new(name='Sculpt')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'W', 'PRESS')
        kmi.properties.name = "pie.sculpt"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

        # Sculpt Pie Menu 2
        km = wm.keyconfigs.addon.keymaps.new(name='Sculpt')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'W', 'PRESS', alt=True)
        kmi.properties.name = "pie.sculpttwo"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Sculpt']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.sculpt":
                    km.keymap_items.remove(kmi)

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Sculpt']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.sculpttwo":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
