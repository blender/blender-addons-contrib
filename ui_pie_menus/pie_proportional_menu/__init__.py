
bl_info = {
    "name": "Proportional Edit: Key: 'O'",
    "description": "Sculpt Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "O key",
    "warning": "",
    "wiki_url": "",
    "category": "Pie"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

#####################################
#      Proportional Edit Object     #
#####################################


class ProportionalEditObj(bpy.types.Operator):
    bl_idname = "proportional_obj.active"
    bl_label = "Proportional Edit Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout

        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (True):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = False

        elif bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True

        return {'FINISHED'}


class ProportionalSmoothObj(bpy.types.Operator):
    bl_idname = "proportional_obj.smooth"
    bl_label = "Proportional Smooth Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'SMOOTH':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'
        return {'FINISHED'}


class ProportionalSphereObj(bpy.types.Operator):
    bl_idname = "proportional_obj.sphere"
    bl_label = "Proportional Sphere Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SPHERE'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'SPHERE':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SPHERE'
        return {'FINISHED'}


class ProportionalRootObj(bpy.types.Operator):
    bl_idname = "proportional_obj.root"
    bl_label = "Proportional Root Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'ROOT'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'ROOT':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'ROOT'
        return {'FINISHED'}


class ProportionalSharpObj(bpy.types.Operator):
    bl_idname = "proportional_obj.sharp"
    bl_label = "Proportional Sharp Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SHARP'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'SHARP':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SHARP'
        return {'FINISHED'}


class ProportionalLinearObj(bpy.types.Operator):
    bl_idname = "proportional_obj.linear"
    bl_label = "Proportional Linear Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'LINEAR'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'LINEAR':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'LINEAR'
        return {'FINISHED'}


class ProportionalConstantObj(bpy.types.Operator):
    bl_idname = "proportional_obj.constant"
    bl_label = "Proportional Constant Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'CONSTANT'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'CONSTANT':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'CONSTANT'
        return {'FINISHED'}


class ProportionalRandomObj(bpy.types.Operator):
    bl_idname = "proportional_obj.random"
    bl_label = "Proportional Random Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.use_proportional_edit_objects == (False):
            bpy.context.scene.tool_settings.use_proportional_edit_objects = True
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'RANDOM'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'RANDOM':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'RANDOM'
        return {'FINISHED'}

#######################################
#     Proportional Edit Edit Mode     #
#######################################


class ProportionalEditEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.active"
    bl_label = "Proportional Edit EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout

        if bpy.context.scene.tool_settings.proportional_edit != ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'DISABLED'
        elif bpy.context.scene.tool_settings.proportional_edit != ('ENABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
        return {'FINISHED'}


class ProportionalConnectedEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.connected"
    bl_label = "Proportional Connected EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout

        if bpy.context.scene.tool_settings.proportional_edit != ('CONNECTED'):
            bpy.context.scene.tool_settings.proportional_edit = 'CONNECTED'
        return {'FINISHED'}


class ProportionalProjectedEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.projected"
    bl_label = "Proportional projected EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout

        if bpy.context.scene.tool_settings.proportional_edit != ('PROJECTED'):
            bpy.context.scene.tool_settings.proportional_edit = 'PROJECTED'
        return {'FINISHED'}


class ProportionalSmoothEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.smooth"
    bl_label = "Proportional Smooth EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.proportional_edit == ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'SMOOTH':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'
        return {'FINISHED'}


class ProportionalSphereEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.sphere"
    bl_label = "Proportional Sphere EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.proportional_edit == ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SPHERE'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'SPHERE':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SPHERE'
        return {'FINISHED'}


class ProportionalRootEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.root"
    bl_label = "Proportional Root EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.proportional_edit == ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'ROOT'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'ROOT':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'ROOT'
        return {'FINISHED'}


class ProportionalSharpEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.sharp"
    bl_label = "Proportional Sharp EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.proportional_edit == ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SHARP'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'SHARP':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'SHARP'
        return {'FINISHED'}


class ProportionalLinearEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.linear"
    bl_label = "Proportional Linear EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.proportional_edit == ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'LINEAR'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'LINEAR':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'LINEAR'
        return {'FINISHED'}


class ProportionalConstantEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.constant"
    bl_label = "Proportional Constant EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.proportional_edit == ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'CONSTANT'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'CONSTANT':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'CONSTANT'
        return {'FINISHED'}


class ProportionalRandomEdt(bpy.types.Operator):
    bl_idname = "proportional_edt.random"
    bl_label = "Proportional Random EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layout = self.layout
        if bpy.context.scene.tool_settings.proportional_edit == ('DISABLED'):
            bpy.context.scene.tool_settings.proportional_edit = 'ENABLED'
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'RANDOM'

        if bpy.context.scene.tool_settings.proportional_edit_falloff != 'RANDOM':
            bpy.context.scene.tool_settings.proportional_edit_falloff = 'RANDOM'
        return {'FINISHED'}

# Pie ProportionalEditObj - O
class PieProportionalObj(Menu):
    bl_idname = "pie.proportional_obj"
    bl_label = "Pie Proportional Edit Obj"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("proportional_obj.sphere", text="Sphere", icon='SPHERECURVE')
        # 6 - RIGHT
        pie.operator("proportional_obj.root", text="Root", icon='ROOTCURVE')
        # 2 - BOTTOM
        pie.operator("proportional_obj.smooth", text="Smooth", icon='SMOOTHCURVE')
        # 8 - TOP
        pie.prop(context.tool_settings, "use_proportional_edit_objects", text="Proportional On/Off")
        # 7 - TOP - LEFT
        pie.operator("proportional_obj.linear", text="Linear", icon='LINCURVE')
        # 9 - TOP - RIGHT
        pie.operator("proportional_obj.sharp", text="Sharp", icon='SHARPCURVE')
        # 1 - BOTTOM - LEFT
        pie.operator("proportional_obj.constant", text="Constant", icon='NOCURVE')
        # 3 - BOTTOM - RIGHT
        pie.operator("proportional_obj.random", text="Random", icon='RNDCURVE')

# Pie ProportionalEditEdt - O
class PieProportionalEdt(Menu):
    bl_idname = "pie.proportional_edt"
    bl_label = "Pie Proportional Edit"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("proportional_edt.connected", text="Connected", icon='PROP_CON')
        # 6 - RIGHT
        pie.operator("proportional_edt.projected", text="Projected", icon='PROP_ON')
        # 2 - BOTTOM
        pie.operator("proportional_edt.smooth", text="Smooth", icon='SMOOTHCURVE')
        # 8 - TOP
        pie.operator("proportional_edt.active", text="Proportional On/Off", icon='PROP_ON')
        # 7 - TOP - LEFT
        pie.operator("proportional_edt.sphere", text="Sphere", icon='SPHERECURVE')
        # 9 - TOP - RIGHT
        pie.operator("proportional_edt.root", text="Root", icon='ROOTCURVE')
        # 1 - BOTTOM - LEFT
        pie.operator("proportional_edt.constant", text="Constant", icon='NOCURVE')
        # 3 - BOTTOM - RIGHT
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("proportional_edt.linear", text="Linear", icon='LINCURVE')
        box.operator("proportional_edt.sharp", text="Sharp", icon='SHARPCURVE')
        box.operator("proportional_edt.random", text="Random", icon='RNDCURVE')

classes = [
    ProportionalEditObj,
    ProportionalSmoothObj,
    ProportionalSphereObj,
    ProportionalRootObj,
    ProportionalSharpObj,
    ProportionalLinearObj,
    ProportionalConstantObj,
    ProportionalRandomObj,
    ProportionalEditEdt,
    ProportionalConnectedEdt,
    ProportionalProjectedEdt,
    ProportionalSmoothEdt,
    ProportionalSphereEdt,
    ProportionalRootEdt,
    ProportionalSharpEdt,
    ProportionalLinearEdt,
    ProportionalConstantEdt,
    ProportionalRandomEdt,
    PieProportionalObj,
    PieProportionalEdt,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # ProportionalEditObj
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'O', 'PRESS')
        kmi.properties.name = "pie.proportional_obj"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

        # ProportionalEditEdt
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'O', 'PRESS')
        kmi.properties.name = "pie.proportional_edt"
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
                if kmi.properties.name == "pie.proportional_obj":
                    km.keymap_items.remove(kmi)

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Mesh']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.proportional_edt":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
