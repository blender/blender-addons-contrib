
bl_info = {
    "name": "Hotkey: 'Alt A'",
    "description": "Pie menu for Timeline controls",
    #    "author": "pitiwazou, meta-androcto",
    #    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View",
    "warning": "",
    "wiki_url": "",
    "category": "Animation Pie"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

# Pie Animation


class PieAnimation(Menu):
    bl_idname = "pie.animation"
    bl_label = "Pie Animation"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("screen.frame_jump", text="Jump REW", icon='REW').end = False
        # 6 - RIGHT
        pie.operator("screen.frame_jump", text="Jump FF", icon='FF').end = True
        # 2 - BOTTOM
        pie.operator("screen.animation_play", text="Reverse", icon='PLAY_REVERSE').reverse = True
        # 8 - TOP
        if not context.screen.is_animation_playing:  # Play / Pause
            pie.operator("screen.animation_play", text="Play", icon='PLAY')
        else:
            pie.operator("screen.animation_play", text="Stop", icon='PAUSE')
        # 7 - TOP - LEFT
        pie.operator("screen.keyframe_jump", text="Previous FR", icon='PREV_KEYFRAME').next = False
        # 9 - TOP - RIGHT
        pie.operator("screen.keyframe_jump", text="Next FR", icon='NEXT_KEYFRAME').next = True
        # 1 - BOTTOM - LEFT
        pie.operator("insert.autokeyframe", text="Auto Keyframe ", icon='REC')
        # 3 - BOTTOM - RIGHT
        pie.menu("VIEW3D_MT_object_animation", icon="CLIP")


# Insert Auto Keyframe
class InsertAutoKeyframe(bpy.types.Operator):
    bl_idname = "insert.autokeyframe"
    bl_label = "Insert Auto Keyframe"
    bl_description = "Toggle Insert Auto Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        if bpy.context.scene.tool_settings.use_keyframe_insert_auto == True:
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

        else:
            if bpy.context.scene.tool_settings.use_keyframe_insert_auto == False:
                bpy.context.scene.tool_settings.use_keyframe_insert_auto = True

        for area in bpy.context.screen.areas:
            if area.type in ('TIMELINE'):
                area.tag_redraw()

        return {'FINISHED'}

classes = [
    PieAnimation,
    InsertAutoKeyframe
    ]

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Animation
        km = wm.keyconfigs.addon.keymaps.new(name='Object Non-modal')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'A', 'PRESS', alt=True)
        kmi.properties.name = "pie.animation"
 #       kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Object Non-modal']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.animation":
                    km.keymap_items.remove(kmi)


if __name__ == "__main__":
    register()
