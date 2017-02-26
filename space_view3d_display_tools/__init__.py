# space_view_3d_display_tools.py Copyright (C) 2014, Jordi Vall-llovera
#
# Multiple display tools for fast navigate/interact with the viewport
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****
## Contributed to by Jasperge, Pixaal, Meta-androcto

bl_info = {
    "name": "Display Tools",
    "author": "Jordi Vall-llovera Medina, Jhon Wallace",
    "version": (1, 6, 0),
    "blender": (2, 7, 0),
    "location": "Toolshelf",
    "description": "Display tools for fast navigate/interact with the viewport",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/"
                "3D_interaction/Display_Tools",
    "tracker_url": "",
    "category": "3D View"}

# Import From Files
if "bpy" in locals():
    import importlib
    importlib.reload(display)
    importlib.reload(fast_navigate)
    importlib.reload(modifier_tools)

    importlib.reload(shading_menu)
    importlib.reload(select_tools)
    importlib.reload(useless_tools)
    importlib.reload(selection_restrictor)

else:
    from . import display
    from . import fast_navigate
    from . import modifier_tools

    from . import shading_menu
    from . import select_tools
    from . import useless_tools
    from . import selection_restrictor

import bpy
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        AddonPreferences,
        PointerProperty,
        )
from bpy.props import (
        IntProperty,
        BoolProperty,
        EnumProperty,
        StringProperty,
        )

from bpy_extras import view3d_utils

# define base dummy class for inheritance
class BasePollCheck:
    @classmethod
    def poll(cls, context):
        return True


class DisplayToolsPanel(bpy.types.Panel):
    bl_label = 'Display Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Display'
    bl_options = {'DEFAULT_CLOSED'}

    draw_type_icons = {'BOUNDS':'BBOX',
                       'WIRE':'WIRE',
                       'SOLID':'SOLID', 
                       'TEXTURED':'POTATO'}
    
    bounds_icons = {'BOX':'MESH_CUBE',
                    'SPHERE':'MATSPHERE',
                    'CYLINDER':'MESH_CYLINDER',
                    'CONE':'MESH_CONE'}

    def draw(self, context):
        scene = context.scene
        DISPLAYDROP = scene.UTDisplayDrop
        SHADINGDROP = scene.UTShadingDrop
        SCENEDROP = scene.UTSceneDrop
        MODIFIERDROP = scene.UTModifierDrop
        SELECT2DROP = scene.UTSelect2Drop
        SUBSURF1DROP = scene.UTSubSurf1Drop
        WIREDROP = scene.UTWireDrop
        VIEWPORTDROP = scene.UTViewPortDrop
        MISCDROP = scene.UTMiscDrop
        FASTNAVDROP = scene.UTFastnavDrop
        view = context.space_data
        toolsettings = context.tool_settings
        layout = self.layout
        ob = context.object

        # Display Scene options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        scene = context.scene
#        row.alignment = 'CENTER'
        row.prop(scene, "UTSceneDrop", icon="TRIA_DOWN")
        if not SCENEDROP:
            row.prop(ob, "show_texture_space", text="", icon='FACESEL_HLT')
            row.prop(ob, "show_name", text="", icon='SORTALPHA')
            row.prop(ob, "show_axis", text="", icon='AXIS_TOP')
        if SCENEDROP:
            col = box1.column(align=True)
            col.alignment = 'EXPAND'
            row = col.row()
            scene = context.scene
            render = scene.render
            space = context.space_data
            row.prop(space, "show_manipulator")

            view = context.space_data
            scene = context.scene

            col = box1.column(align=True)
            col.alignment = 'EXPAND'
            row = col.row()
            row.prop(view, "show_only_render")
            row = col.row()
            row.prop(view, "show_world")
            row = col.row()
            row.prop(space, "show_outline_selected")
            row = col.row()
            row.prop(space, "show_all_objects_origin")
            row = col.row()
            row.prop(space, "show_backface_culling")
            row = col.row()
            scene = context.scene
            ob = context.object
            ob_type = ob.type
            row.prop(ob, "show_x_ray", text="X-Ray")
            if ob_type == 'MESH' or is_empty_image:
                row = col.row()
                row.prop(ob, "show_transparent", text="Transparency")
            row = col.row()
            row.prop(render, "use_simplify", "Simplify")

            if scene.render.use_simplify is True:
                row.label("Settings :")
                row = layout.row()
                box = row.box()
                box.prop(render, "simplify_subdivision", "Subdivision")
                box.prop(render, "simplify_shadow_samples", "Shadow Samples")
                box.prop(render, "simplify_child_particles", "Child Particles")
                box.prop(render, "simplify_ao_sss", "AO and SSS")
                layout.operator("view3d.display_simplify")

        # Draw Type options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "UTDisplayDrop", icon="TRIA_DOWN")
        if not DISPLAYDROP:
            row.operator("ut.wirehideall", icon="MATSPHERE", text="").show = False
            row.operator("ut.wirehideall", icon="MESH_UVSPHERE", text="").show = True
            row.operator("ut.all_edges", icon="MESH_GRID", text="").on = True
        if DISPLAYDROP:
            col = box1.column(align=True)
            col.alignment = 'EXPAND'
            row = col.row()
            row.label(text="Maximum:")
            row.prop(ob, "draw_type", text="", icon=self.draw_type_icons[ob.draw_type])

            col = box1.column(align=True)
            col.alignment = 'EXPAND'
            col.label(text="Selected Object(s):")
            row = col.row()
            row.operator("view3d.display_draw_change", text="Wire",
                         icon='WIRE').drawing = 'WIRE'
            row.operator("view3d.display_draw_change", text="Solid",
                        icon='SOLID').drawing = 'SOLID'
            row = col.row()

            row1 = col.row(align=True)
            row.operator("view3d.display_draw_change", text="Textured",
                         icon='TEXTURE_SHADED').drawing = 'TEXTURED'
            row.operator("view3d.display_draw_change", text="Bounds",
                         icon='BBOX').drawing = 'BOUNDS'

            col = box1.column(align=True)
            col.alignment = 'CENTER'
            col.label(text="Wire Overlay:")

            if context.scene.WT_handler_enable:
                row = col.row()
                row.operator('object.wt_selection_handler_toggle', icon='X')
            else:
                row = col.row()
                row.operator('object.wt_selection_handler_toggle', icon='MOD_WIREFRAME')

            col = box1.column(align=True)
            col.alignment = 'CENTER'
            row = col.row(align=True)
            row.operator("object.wt_hide_all_wire", icon="SOLID", text="Hide All")
            row.operator("af_ops.wire_all", text="Toggle", icon='WIRE')
            row = col.row()

            row1 = col.row(align=True)
            row1.operator("ut.wirehidesel", icon="MATSPHERE", text="Hide").show = False
            row1.operator("ut.wirehidesel", icon="MESH_UVSPHERE", text="Show").show = True
            col = box1.column(align=True)
            col.alignment = 'CENTER'
            row = col.row()
            row3 = col.row(align=True)
            row3.alignment = 'CENTER'
            row3.label(text="All Edges:")
            row3.operator("ut.all_edges", icon="MESH_PLANE", text="Off").on = False
            row3.operator("ut.all_edges", icon="MESH_GRID", text="On").on = True
            col = box1.column(align=True)
            col.alignment = 'EXPAND'
            row = col.row()
            scene = context.scene.display_tools
            row.prop(scene, "BoundingMode")
            row = col.row()
            row.operator("view3d.display_bounds_switch", "Bounds On",
                        icon='BBOX').bounds = True
            row.operator("view3d.display_bounds_switch", "Bounds Off",
                        icon='BBOX').bounds = False


        # Shading options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        scene = context.scene
        row.prop(scene, "UTShadingDrop", icon="TRIA_DOWN")

        if not SHADINGDROP:
            row.operator("object.shade_smooth", icon="SMOOTH", text="" )
            row.operator("object.shade_flat", icon="MESH_ICOSPHERE", text="" )
            row.menu("VIEW3D_MT_Shade_menu", icon='SOLID', text="" )
        if SHADINGDROP:
            scene = context.scene
            layout = self.layout

            col = box1.column(align=True)
            col.alignment = 'EXPAND'

            view = context.space_data
            scene = context.scene
            gs = scene.game_settings
            obj = context.object

            col = layout.column()

            if not scene.render.use_shading_nodes:
                col.prop(gs, "material_mode", text="")

            if view.viewport_shade == 'SOLID':
                col.prop(view, "show_textured_solid")
                col.prop(view, "use_matcap")
                if view.use_matcap:
                    col.template_icon_view(view, "matcap_icon")
            if view.viewport_shade == 'TEXTURED' or context.mode == 'PAINT_TEXTURE':
                if scene.render.use_shading_nodes or gs.material_mode != 'GLSL':
                    col.prop(view, "show_textured_shadeless")

            col.prop(view, "show_backface_culling")

            if view.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'}:
                if obj and obj.mode == 'EDIT':
                    col.prop(view, "show_occlude_wire")
                if obj and obj.type == 'MESH' and obj.mode in {'EDIT'}:
                    col = layout.column(align=True)
                    col.label(text="Faces:")
                    row = col.row(align=True)
                    row.operator("mesh.faces_shade_smooth", text="Smooth")
                    row.operator("mesh.faces_shade_flat", text="Flat")
                    col.label(text="Edges:")
                    row = col.row(align=True)
                    row.operator("mesh.mark_sharp", text="Smooth").clear = True
                    row.operator("mesh.mark_sharp", text="Sharp")
                    col.label(text="Vertices:")
                    row = col.row(align=True)
                    props = row.operator("mesh.mark_sharp", text="Smooth")
                    props.use_verts = True
                    props.clear = True
                    row.operator("mesh.mark_sharp", text="Sharp").use_verts = True

                    col = layout.column(align=True)
                    col.label(text="Normals:")
                    col.operator("mesh.normals_make_consistent", text="Recalculate")
                    col.operator("mesh.flip_normals", text="Flip Direction")
                    col.operator("mesh.set_normals_from_faces", text="Set From Faces")

            fx_settings = view.fx_settings

            if view.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'}:
                sub = col.column()
                sub.active = view.region_3d.view_perspective == 'CAMERA'
                sub.prop(fx_settings, "use_dof")
                col.prop(fx_settings, "use_ssao", text="Ambient Occlusion")
                if fx_settings.use_ssao:
                    ssao_settings = fx_settings.ssao
                    subcol = col.column(align=True)
                    subcol.prop(ssao_settings, "factor")
                    subcol.prop(ssao_settings, "distance_max")
                    subcol.prop(ssao_settings, "attenuation")
                    subcol.prop(ssao_settings, "samples")
                    subcol.prop(ssao_settings, "color")

        # Modifier options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
#        row.alignment = 'CENTER'
        scene = context.scene
        row.prop(scene, "UTModifierDrop", icon="TRIA_DOWN")
        if not MODIFIERDROP:
            row.operator("ut.subsurfhideall", icon="MOD_SOLIDIFY", text="").show = False
            row.operator("ut.subsurfhideall", icon="MOD_SUBSURF", text="").show = True
            row.operator("ut.optimaldisplayall", icon="MESH_PLANE", text="").on = True
        if MODIFIERDROP:
            layout = self.layout
            col = box1.column(align=True)
            col.alignment = 'EXPAND'

            row = col.row(align=True)
            row.label('Viewport Visibility')
            row = col.row(align=True)
            row.operator("object.toggle_apply_modifiers_view",
                         icon='RESTRICT_VIEW_OFF',
                         text="Viewport Vis")
            row = col.row()
            row.label('Render Visibility')
            row = col.row()
            row.operator("view3d.display_modifiers_render_switch", text="On",
                          icon='RENDER_STILL').mod_render = True
            row.operator("view3d.display_modifiers_render_switch",
                          text="Off").mod_render = False
            row = col.row()
            row.label('Subsurf Visibility')
            row1 = col.row()
            row1.operator("ut.subsurfhidesel", icon="MOD_SOLIDIFY", text="Hide").show = False
            row1.operator("ut.subsurfhidesel", icon="MOD_SUBSURF", text="Show").show = True
            row2 = col.row()
            row2.operator("ut.subsurfhideall", icon="MOD_SOLIDIFY", text="Hide All").show = False
            row2.operator("ut.subsurfhideall", icon="MOD_SUBSURF", text="Show All").show = True
            col = box1.column()
            row = col.row()
            row.label('Edit Mode')
            row = col.row()
            row.operator("view3d.display_modifiers_edit_switch", text="On",
                        icon='EDITMODE_HLT').mod_edit = True
            row.operator("view3d.display_modifiers_edit_switch",
                        text="Off").mod_edit = False
            row = col.row()
            row.label('Modifier Cage')
            row = col.row()
            row.operator("view3d.display_modifiers_cage_set", text="On",
                         icon='EDITMODE_HLT').set_cage = True
            row.operator("view3d.display_modifiers_cage_set",
                         text="Off").set_cage = False
            row = col.row(align=True)

            row.label("Subdivision Level", icon='MOD_SUBSURF')

            row = col.row(align=True)
            row.operator("view3d.modifiers_subsurf_level_set", text="0").level = 0
            row.operator("view3d.modifiers_subsurf_level_set", text="1").level = 1
            row.operator("view3d.modifiers_subsurf_level_set", text="2").level = 2
            row.operator("view3d.modifiers_subsurf_level_set", text="3").level = 3
            row.operator("view3d.modifiers_subsurf_level_set", text="4").level = 4
            row.operator("view3d.modifiers_subsurf_level_set", text="5").level = 5
            row.operator("view3d.modifiers_subsurf_level_set", text="6").level = 6



# Selection options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
#        row.alignment = 'CENTER'
        row.prop(scene, "UTSelect2Drop", icon="TRIA_DOWN")

        if SELECT2DROP:
            if context.object != None:
                if context.object.mode == 'OBJECT':
                    layout.operator('opr.show_hide_object', text='Show/Hide', icon='GHOST_ENABLED')

            layout.operator('opr.show_all_objects', text='Show All', icon='RESTRICT_VIEW_OFF')
            layout.operator('opr.hide_all_objects', text='Hide All', icon='RESTRICT_VIEW_ON')
            row = layout.row(align=True)
            row.operator("op.render_show_all_selected", icon='RESTRICT_VIEW_OFF')
            row.operator("op.render_hide_all_selected", icon='RESTRICT_VIEW_ON')
            row = layout.row(align=True)
            if context.object != None:
                if context.object.mode == 'OBJECT':
                    layout.operator_menu_enum("object.select_by_type", "type", text="Select All by Type...")
                    layout.operator('opr.select_all', icon='MOD_MESHDEFORM')
                    layout.operator('opr.inverse_selection', icon='MOD_REMESH')
                    row = layout.row(align=True)
                    row.operator('view3d.select_border', icon='MESH_PLANE')
                    row.operator('view3d.select_circle', icon='MESH_CIRCLE')

                if context.object.type == 'MESH':
                    if context.object.mode == 'EDIT':
                        layout.operator('opr.select_all', icon='MOD_MESHDEFORM')
                        layout.operator('opr.inverse_selection', icon='MOD_REMESH')
                        layout.operator('view3d.select_border', icon='MESH_PLANE')
                        layout.operator('view3d.select_circle', icon='MESH_CIRCLE')
                        layout.operator('mesh.select_linked', icon='ROTATECOLLECTION')
                        layout.operator('opr.loop_multi_select', icon='OUTLINER_DATA_MESH')

            else:

                layout.operator('opr.select_all', icon='MOD_MESHDEFORM')
                layout.operator('opr.inverse_selection', icon='MOD_REMESH')
                layout.operator('view3d.select_border', icon='MESH_PLANE')
                layout.operator('view3d.select_circle', icon='MESH_CIRCLE')

        # fast nav options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
#        row.alignment = 'CENTER'
        row.prop(scene, "UTFastnavDrop", icon="TRIA_DOWN")

        if FASTNAVDROP:
            layout = self.layout
            scene = context.scene.display_tools
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.operator("view3d.fast_navigate_operator")
            row.operator("view3d.fast_navigate_stop")
            row.label("Settings :")
            row = layout.row()
            box = row.box()
            box.prop(scene, "OriginalMode")
            box.prop(scene, "FastMode")
            box.prop(scene, "EditActive", "Edit mode")
            box.prop(scene, "Delay")
            box.prop(scene, "DelayTimeGlobal", "Delay time")
            box.alignment = 'LEFT'
            box.prop(scene, "ShowParticles")
            box.prop(scene, "ParticlesPercentageDisplay")
# define scene props
class display_tools_scene_props(PropertyGroup):
    # Init delay variables
    Delay = BoolProperty(
            default=False,
            description="Activate delay return to normal viewport mode"
            )
    DelayTime = IntProperty(
            default=30,
            min=1,
            max=500,
            soft_min=10,
            soft_max=250,
            description="Delay time to return to normal viewport"
                        "mode after move your mouse cursor"
            )
    DelayTimeGlobal = IntProperty(
            default=30,
            min=1,
            max=500,
            soft_min=10,
            soft_max=250,
            description="Delay time to return to normal viewport"
                        "mode after move your mouse cursor"
            )
    # Init variable for fast navigate
    EditActive = BoolProperty(
            default=True,
            description="Activate for fast navigate in edit mode too"
            )

    # Init properties for scene
    FastNavigateStop = BoolProperty(
            name="Fast Navigate Stop",
            description="Stop fast navigate mode",
            default=False
            )
    OriginalMode = EnumProperty(
            items=[('TEXTURED', 'Texture', 'Texture display mode'),
                   ('SOLID', 'Solid', 'Solid display mode')],
            name="Normal",
            default='SOLID'
            )
    BoundingMode = EnumProperty(
            items=[('BOX', 'Box', 'Box shape'),
                   ('SPHERE', 'Sphere', 'Sphere shape'),
                   ('CYLINDER', 'Cylinder', 'Cylinder shape'),
                   ('CONE', 'Cone', 'Cone shape')],
            name="BB Mode"
            )
    FastMode = EnumProperty(
            items=[('WIREFRAME', 'Wireframe', 'Wireframe display'),
                   ('BOUNDBOX', 'Bounding Box', 'Bounding Box display')],
            name="Fast"
            )
    ShowParticles = BoolProperty(
            name="Show Particles",
            description="Show or hide particles on fast navigate mode",
            default=True
            )
    ParticlesPercentageDisplay = IntProperty(
            name="Display",
            description="Display only a percentage of particles",
            default=25,
            min=0,
            max=100,
            soft_min=0,
            soft_max=100,
            subtype='FACTOR'
            )
    InitialParticles = IntProperty(
            name="Count for initial particle setting before enter fast navigate",
            description="Display a percentage value of particles",
            default=100,
            min=0,
            max=100,
            soft_min=0,
            soft_max=100
            )
    Symplify = IntProperty(
            name="Integer",
            description="Enter an integer"
            )

    bpy.types.Scene.UTDisplayDrop = bpy.props.BoolProperty(
        name="Draw Type",
        default=False,
        description="Disply Draw Types")
    bpy.types.Scene.UTShadingDrop = bpy.props.BoolProperty(
        name="Shading",
        default=False,
        description="Shading Display")
    bpy.types.Scene.UTSceneDrop = bpy.props.BoolProperty(
        name="Display",
        default=False,
        description="Scene Display Settings")
    bpy.types.Scene.UTModifierDrop = bpy.props.BoolProperty(
        name="Modifiers",
        default=False,
        description="Modifier Display")
    bpy.types.Scene.UTFastnavDrop = bpy.props.BoolProperty(
        name="Fast Nav",
        default=False,
        description="Fast Nav")
    bpy.types.Scene.UTSelect2Drop = bpy.props.BoolProperty(
        name="Selection",
        default=False,
        description="Selection")
    bpy.types.Scene.UTSubSurf1Drop = bpy.props.BoolProperty(
        name="Subsurf",
        default=False,
        description="Quick batch subsurf control")
    bpy.types.Scene.UTWireDrop = bpy.props.BoolProperty(
        name="Wire",
        default=False,
        description="Wire display and overlay controls")
    bpy.types.Scene.UTViewPortDrop = bpy.props.BoolProperty(
        name="View",
        default=False,
        description="Viewport display and performance tweaks")
    bpy.types.Scene.UTMiscDrop = bpy.props.BoolProperty(
        name="Misc",
        default=False,
        description="I love your robot hand!")
    bpy.types.Scene.WT_handler_enable = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.WT_handler_previous_object = bpy.props.StringProperty(default='')
    bpy.types.Scene.WT_only_selection = bpy.props.BoolProperty(name="Only Selection", default=False)
    bpy.types.Scene.WT_invert = bpy.props.BoolProperty(name="Invert", default=False)
    bpy.types.Scene.WT_display_tools = bpy.props.BoolProperty(name="Display WireTools paramaters", default=False)

# Addons Preferences Update Panel
panels = [
        DisplayToolsPanel
        ]

def update_panel(self, context):
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)
    except:
        print("Display Tools: Updating panel locations has failed")
        pass

    for panel in panels:
        try:
            panel.bl_category = context.user_preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)
        except:
            print("Display Tools: Updating panel locations has failed")
            pass


class DisplayToolsPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category = StringProperty(
            name="Tab Category",
            description="Choose a name for the category of the panel",
            default="Display",
            update=update_panel)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")


# register the classes and props
def register():
    bpy.utils.register_module(__name__)
    # Register Scene Properties

    bpy.types.Scene.display_tools = bpy.props.PointerProperty(
                                            type=display_tools_scene_props
                                            )
    update_panel(None, bpy.context)
    selection_restrictor.register()

def unregister():
    del bpy.types.Scene.display_tools
    selection_restrictor.unregister()
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
