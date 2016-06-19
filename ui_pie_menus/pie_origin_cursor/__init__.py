
bl_info = {
    "name": "Origin/Cursor: Key: 'Shift S' ",
    "description": "Origin/Pivot Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "Shift S",
    "warning": "",
    "wiki_url": "",
    "category": "Object"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

# Pivot to selection
class PivotToSelection(bpy.types.Operator):
    bl_idname = "object.pivot2selection"
    bl_label = "Pivot To Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        saved_location = bpy.context.scene.cursor_location.copy()
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.cursor_location = saved_location
        return {'FINISHED'}

# Pivot to Bottom
class PivotBottom(bpy.types.Operator):
    bl_idname = "object.pivotobottom"
    bl_label = "Pivot To Bottom"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        o = bpy.context.active_object
        init = 0
        for x in o.data.vertices:
            if init == 0:
                a = x.co.z
                init = 1
            elif x.co.z < a:
                a = x.co.z

        for x in o.data.vertices:
            x.co.z -= a

        o.location.z += a
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

# Pie Origin/Pivot - Shift + S
class PieOriginPivot(Menu):
    bl_idname = "pie.originpivot"
    bl_label = "Pie Origin/Cursor"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        pie = layout.menu_pie()
        if obj and obj.type == 'MESH':
            # 4 - LEFT
            pie.operator("object.pivotobottom", text="Origin to Bottom", icon='TRIA_DOWN')
            # 6 - RIGHT
            pie.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='ROTACTIVE')
            # 2 - BOTTOM
            pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon='CLIPUV_HLT').use_offset = False
            # 8 - TOP
            pie.operator("object.origin_set", text="Origin To 3D Cursor", icon='CURSOR').type = 'ORIGIN_CURSOR'
            # 7 - TOP - LEFT
            pie.operator("object.pivot2selection", text="Origin To Selection", icon='SNAP_INCREMENT')
            # 9 - TOP - RIGHT
            pie.operator("object.origin_set", text="Origin To Geometry", icon='ROTATE').type = 'ORIGIN_GEOMETRY'
            # 1 - BOTTOM - LEFT
            pie.operator("object.origin_set", text="Geometry To Origin", icon='BBOX').type = 'GEOMETRY_ORIGIN'
            # 3 - BOTTOM - RIGHT
            pie.operator("wm.call_menu_pie", text="Others", icon='CURSOR').name = "origin.pivotmenu"
        else:
            # 4 - LEFT
#            pie.operator("object.pivotobottom", text="Origin to Bottom", icon='TRIA_DOWN')
            # 6 - RIGHT
            pie.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='ROTACTIVE')
            # 2 - BOTTOM
            pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon='CLIPUV_HLT').use_offset = False
            # 8 - TOP
            pie.operator("object.origin_set", text="Origin To 3D Cursor", icon='CURSOR').type = 'ORIGIN_CURSOR'
            # 7 - TOP - LEFT
            pie.operator("object.pivot2selection", text="Origin To Selection", icon='SNAP_INCREMENT')
            # 9 - TOP - RIGHT
            pie.operator("object.origin_set", text="Origin To Geometry", icon='ROTATE').type = 'ORIGIN_GEOMETRY'
            # 1 - BOTTOM - LEFT
            pie.operator("object.origin_set", text="Geometry To Origin", icon='BBOX').type = 'GEOMETRY_ORIGIN'
            # 3 - BOTTOM - RIGHT
            pie.operator("wm.call_menu_pie", text="Others", icon='CURSOR').name = "origin.pivotmenu"

# Origin/Pivot menu1  - Shift + S
class OriginPivotMenu(Menu):
    bl_idname = "origin.pivotmenu"
    bl_label = "Origin Pivot Menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Offset)", icon='CURSOR').use_offset = True
        # 6 - RIGHT
        pie.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon='GRID')
        # 2 - BOTTOM
        pie.operator("object.origin_set", text="Origin to Center of Mass", icon='BBOX').type = 'ORIGIN_CENTER_OF_MASS'
        # 8 - TOP
        pie.operator("view3d.snap_cursor_to_center", text="Cursor to Center", icon='CLIPUV_DEHLT')
        # 7 - TOP - LEFT
        pie.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon='GRID')
        # 9 - TOP - RIGHT
        pie.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon='BBOX')
        # 1 - BOTTOM - LEFT
        # 3 - BOTTOM - RIGHT

classes = [
    OriginPivotMenu,
    PieOriginPivot,
    PivotToSelection,
    PivotBottom,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Origin/Pivot
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'S', 'PRESS', shift=True)
        kmi.properties.name = "pie.originpivot"
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
                if kmi.properties.name == "pie.originpivot":
                    km.keymap_items.remove(kmi)


if __name__ == "__main__":
    register()
