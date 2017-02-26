from bpy.props import *
from .Utils.core import *


class BrushOptionsMenu(bpy.types.Menu):
    bl_label = "Brush Options"
    bl_idname = "view3d.brush_options"

    @classmethod
    def poll(self, context):
        if get_mode() in [sculpt, vertex_paint, weight_paint, texture_paint, particle_edit]:
            return True
        else:
            return False

    def draw(self, context):
        menu = Menu(self)

        if get_mode() == sculpt:
            self.sculpt(menu, context)

        elif get_mode() in [vertex_paint, weight_paint]:
            self.vw_paint(menu, context)

        elif get_mode() == texture_paint:
            self.texpaint(menu, context)

        else:
            self.particle(menu, context)

    def sculpt(self, menu, context):
        menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon='BRUSH_SCULPT_DRAW')
        menu.add_item().menu(BrushRadiusMenu.bl_idname)
        menu.add_item().menu(BrushStrengthMenu.bl_idname)
        menu.add_item().menu(BrushAutosmoothMenu.bl_idname)
        menu.add_item().menu(BrushModeMenu.bl_idname)
        menu.add_item().menu("view3d.texture_menu")
        menu.add_item().menu("view3d.stroke_options")
        menu.add_item().menu("view3d.brush_curve_menu")
        menu.add_item().menu("view3d.dyntopo")
        menu.add_item().menu("view3d.symmetry_menu")

    def vw_paint(self, menu, context):
        if get_mode() == vertex_paint:
            menu.add_item().operator(ColorPickerPopup.bl_idname, icon="COLOR")
            menu.add_item().separator()
            menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon='BRUSH_VERTEXDRAW')
            menu.add_item().menu(BrushRadiusMenu.bl_idname)
            menu.add_item().menu(BrushStrengthMenu.bl_idname)
            menu.add_item().menu(BrushModeMenu.bl_idname)
            menu.add_item().menu("view3d.texture_menu")
            menu.add_item().menu("view3d.stroke_options")
            menu.add_item().menu("view3d.brush_curve_menu")
        if get_mode() == weight_paint:
            menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon='BRUSH_TEXMASK')
            menu.add_item().menu(BrushWeightMenu.bl_idname)
            menu.add_item().menu(BrushRadiusMenu.bl_idname)
            menu.add_item().menu(BrushStrengthMenu.bl_idname)
            menu.add_item().menu(BrushModeMenu.bl_idname)
            menu.add_item().menu("view3d.stroke_options")
            menu.add_item().menu("view3d.brush_curve_menu")

    def texpaint(self, menu, context):
        menu.add_item().operator(ColorPickerPopup.bl_idname, icon="COLOR")
        menu.add_item().separator()
        menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon='SCULPTMODE_HLT')
        menu.add_item().menu(BrushRadiusMenu.bl_idname)
        menu.add_item().menu(BrushStrengthMenu.bl_idname)
        menu.add_item().menu(BrushModeMenu.bl_idname)
        menu.add_item().menu("view3d.texture_menu")
        menu.add_item().menu("view3d.stroke_options")
        menu.add_item().menu("view3d.brush_curve_menu")
        menu.add_item().menu("view3d.symmetry_menu")


    def particle(self, menu, context):
        if context.tool_settings.particle_edit.tool == 'NONE':
            menu.add_item().label("No Brush Selected")
            menu.add_item().menu("view3d.brushes_menu", text="Select Brush")
        else:
            menu.add_item().menu("view3d.brushes_menu")
            menu.add_item().menu(BrushRadiusMenu.bl_idname)
            if context.tool_settings.particle_edit.tool != 'ADD':
                menu.add_item().menu(BrushStrengthMenu.bl_idname)

            else:
                menu.add_item().menu(ParticleCountMenu.bl_idname)
                menu.add_item().separator()
                menu.add_item().prop(context.tool_settings.particle_edit,
                                     "use_default_interpolate", toggle=True)

                menu.add_item().prop(context.tool_settings.particle_edit.brush,
                                     "steps", slider=True)
                menu.add_item().prop(context.tool_settings.particle_edit,
                                     "default_key_count", slider=True)

            if context.tool_settings.particle_edit.tool == 'LENGTH':
                menu.add_item().separator()
                menu.add_item().prop(context.tool_settings.particle_edit.brush,
                                     "length_mode", text="")

            if context.tool_settings.particle_edit.tool == 'PUFF':
                menu.add_item().separator()
                menu.add_item().prop(context.tool_settings.particle_edit.brush,
                                     "puff_mode", text="")
                menu.add_item().prop(context.tool_settings.particle_edit.brush,
                                     "use_puff_volume", toggle=True)


class BrushRadiusMenu(bpy.types.Menu):
    bl_label = "Radius"
    bl_idname = "view3d.brush_radius_menu"

    def init(self, context):
        if get_mode() == particle_edit:
            settings = [["100", 100], ["70", 70], ["50", 50],
                        ["30", 30], ["20", 20], ["10", 10]]
            datapath = "tool_settings.particle_edit.brush.size"
            proppath = context.tool_settings.particle_edit.brush

        else:
            settings = [["200", 200], ["150", 150], ["100", 100],
                        ["50", 50], ["35", 35], ["10", 10]]
            datapath = "tool_settings.unified_paint_settings.size"
            proppath = context.tool_settings.unified_paint_settings

        return settings, datapath, proppath

    def draw(self, context):
        settings, datapath, proppath = self.init(context)
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(proppath, "size", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     datapath, icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class BrushStrengthMenu(bpy.types.Menu):
    bl_label = "Strength"
    bl_idname = "view3d.brush_strength_menu"

    def init(self, context):
        settings = [["1.0", 1.0], ["0.7", 0.7], ["0.5", 0.5],
                    ["0.3", 0.3], ["0.2", 0.2], ["0.1", 0.1]]

        if get_mode() == sculpt:
            datapath = "tool_settings.sculpt.brush.strength"
            proppath = context.tool_settings.sculpt.brush

        elif get_mode() == vertex_paint:
            datapath = "tool_settings.vertex_paint.brush.strength"
            proppath = context.tool_settings.vertex_paint.brush

        elif get_mode() == weight_paint:
            datapath = "tool_settings.weight_paint.brush.strength"
            proppath = context.tool_settings.weight_paint.brush

        elif get_mode() == texture_paint:
            datapath = "tool_settings.image_paint.brush.strength"
            proppath = context.tool_settings.image_paint.brush

        else:
            datapath = "tool_settings.particle_edit.brush.strength"
            proppath = context.tool_settings.particle_edit.brush

        return settings, datapath, proppath

    def draw(self, context):
        settings, datapath, proppath = self.init(context)
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(proppath, "strength", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     datapath, icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class BrushModeMenu(bpy.types.Menu):
    bl_label = "Brush Mode"
    bl_idname = "view3d.brush_mode_menu"

    def init(self):
        if get_mode() == sculpt:
            path = "tool_settings.sculpt.brush.sculpt_plane"
            brushmodes = [["Area Plane", 'AREA'],
                          ["View Plane", 'VIEW'],
                          ["X Plane", 'X'],
                          ["Y Plane", 'Y'],
                          ["Z Plane", 'Z']]

        elif get_mode() == texture_paint:
            path = "tool_settings.image_paint.brush.blend"
            brushmodes = [["Mix", 'MIX'],
                          ["Add", 'ADD'],
                          ["Subtract", 'SUB'],
                          ["Multiply", 'MUL'],
                          ["Lighten", 'LIGHTEN'],
                          ["Darken", 'DARKEN'],
                          ["Erase Alpha", 'ERASE_ALPHA'],
                          ["Add Alpha", 'ADD_ALPHA'],
                          ["Overlay", 'OVERLAY'],
                          ["Hard Light", 'HARDLIGHT'],
                          ["Color Burn", 'COLORBURN'],
                          ["Linear Burn", 'LINEARBURN'],
                          ["Color Dodge", 'COLORDODGE'],
                          ["Screen", 'SCREEN'],
                          ["Soft Light", 'SOFTLIGHT'],
                          ["Pin Light", 'PINLIGHT'],
                          ["Vivid Light", 'VIVIDLIGHT'],
                          ["Linear Light", 'LINEARLIGHT'],
                          ["Difference", 'DIFFERENCE'],
                          ["Exclusion", 'EXCLUSION'],
                          ["Hue", 'HUE'],
                          ["Saturation", 'SATURATION'],
                          ["Luminosity", 'LUMINOSITY'],
                          ["Color", 'COLOR'],
                          ]

        else:
            path = "tool_settings.vertex_paint.brush.vertex_tool"
            brushmodes = [["Mix", 'MIX'],
                          ["Add", 'ADD'],
                          ["Subtract", 'SUB'],
                          ["Multiply", 'MUL'],
                          ["Blur", 'BLUR'],
                          ["Lighten", 'LIGHTEN'],
                          ["Darken", 'DARKEN']]

        return path, brushmodes

    def draw(self, context):
        path, brushmodes = self.init()
        menu = Menu(self)

        menu.add_item().label(text="Brush Mode")
        menu.add_item().separator()

        if get_mode() == texture_paint:
            column_flow = menu.add_item("column_flow", columns=2)

            # add all the brush modes to the menu
            for brush in brushmodes:
                menuprop(menu.add_item(parent=column_flow), brush[0],
                         brush[1], path, icon='RADIOBUT_OFF',
                         disable=True, disable_icon='RADIOBUT_ON')

        else:
            # add all the brush modes to the menu
            for brush in brushmodes:
                menuprop(menu.add_item(), brush[0],
                         brush[1], path, icon='RADIOBUT_OFF',
                         disable=True, disable_icon='RADIOBUT_ON')


class BrushAutosmoothMenu(bpy.types.Menu):
    bl_label = "Autosmooth"
    bl_idname = "view3d.brush_autosmooth_menu"

    def init(self):
        settings = [["1.0", 1.0], ["0.7", 0.7], ["0.5", 0.5], ["0.3", 0.3], ["0.2", 0.2],
                    ["0.1", 0.1]]

        return settings

    def draw(self, context):
        settings = self.init()
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(context.tool_settings.sculpt.brush,
                             "auto_smooth_factor", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     "tool_settings.sculpt.brush.auto_smooth_factor",
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class BrushWeightMenu(bpy.types.Menu):
    bl_label = "Weight"
    bl_idname = "view3d.brush_weight_menu"

    def draw(self, context):
        menu = Menu(self)
        settings = [["1.0", 1.0], ["0.7", 0.7],
                    ["0.5", 0.5], ["0.3", 0.3],
                    ["0.2", 0.2], ["0.1", 0.1]]

        # add the top slider
        menu.add_item().prop(context.tool_settings.unified_paint_settings,
                             "weight", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     "tool_settings.unified_paint_settings.weight",
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class ParticleCountMenu(bpy.types.Menu):
    bl_label = "Count"
    bl_idname = "view3d.particle_count_menu"

    def init(self):
        settings = [["50", 50], ["25", 25], ["10", 10], ["5", 5], ["3", 3],
                    ["1", 1]]

        return settings

    def draw(self, context):
        settings = self.init()
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(context.tool_settings.particle_edit.brush,
                             "count", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     "tool_settings.particle_edit.brush.count",
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class ParticleLengthMenu(bpy.types.Menu):
    bl_label = "Length Mode"
    bl_idname = "view3d.particle_length_menu"

    def draw(self, context):
        menu = Menu(self)
        datapath = "tool_settings.particle_edit.brush.length_mode"

        # add the menu items
        menuprop(menu.add_item(), "Grow", "GROW",
                 datapath, icon='RADIOBUT_OFF',
                 disable=True, disable_icon='RADIOBUT_ON')

        menuprop(menu.add_item(), "Shrink", "SHRINK",
                 datapath, icon='RADIOBUT_OFF',
                 disable=True, disable_icon='RADIOBUT_ON')


class ParticlePuffMenu(bpy.types.Menu):
    bl_label = "Puff Mode"
    bl_idname = "view3d.particle_puff_menu"

    def draw(self, context):
        menu = Menu(self)
        datapath = "tool_settings.particle_edit.brush.puff_mode"

        # add the menu items
        menuprop(menu.add_item(), "Add", "ADD",
                 datapath, icon='RADIOBUT_OFF',
                 disable=True, disable_icon='RADIOBUT_ON')

        menuprop(menu.add_item(), "Sub", "SUB",
                 datapath, icon='RADIOBUT_OFF',
                 disable=True, disable_icon='RADIOBUT_ON')


class ColorPickerPopup(bpy.types.Operator):
    bl_label = "Color Picker"
    bl_idname = "view3d.color_picker_popup"
    bl_options = {'REGISTER'}

    def draw(self, context):
        menu = Menu(self)

        if get_mode() == texture_paint:
            brush = context.tool_settings.image_paint.brush

        else:
            brush = context.tool_settings.vertex_paint.brush

        menu.add_item().template_color_picker(brush, "color", value_slider=True)
        menu.add_item().prop(brush, "color", text="")

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=180)

### ------------ New hotkeys and registration ------------ ###

addon_keymaps = []


def register():
    wm = bpy.context.window_manager
    modes = ['Sculpt', 'Vertex Paint', 'Weight Paint', 'Image Paint', 'Particle']

    for mode in modes:
        km = wm.keyconfigs.active.keymaps[mode]
        kmi = km.keymap_items.new('wm.call_menu', 'V', 'PRESS', alt=True)
        kmi.properties.name = "view3d.brush_options"
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
