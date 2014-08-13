# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Amaranth Toolset",
    "author": "Pablo Vazquez, Bassam Kurdali, Sergey Sharybin, Lukas Tönne",
    "version": (0, 9, 5),
    "blender": (2, 71),
    "location": "Everywhere!",
    "description": "A collection of tools and settings to improve productivity",
    "warning": "",
    "wiki_url": "http://pablovazquez.org/amaranth",
    "tracker_url": "",
    "category": "Scene"}


import bpy
import bmesh
from bpy.types import Operator, AddonPreferences, Panel, Menu
from bpy.props import (BoolProperty, EnumProperty,
                       FloatProperty, FloatVectorProperty,
                       IntProperty, StringProperty)
from mathutils import Vector
from bpy.app.handlers import persistent
from bl_operators.presets import AddPresetBase

# Addon wide, we need to know if cycles is available
cycles_exists = False


def check_cycles_exists():
    global cycles_exists
    cycles_exists = ('cycles' in dir(bpy.types.Scene))
    return cycles_exists


check_cycles_exists()


# Preferences
class AmaranthToolsetPreferences(AddonPreferences):
    bl_idname = __name__
    use_frame_current = BoolProperty(
            name="Current Frame Slider",
            description="Set the current frame from the Specials menu in the 3D View",
            default=True,
            )
    use_file_save_reload = BoolProperty(
            name="Save & Reload File",
            description="File menu > Save & Reload, or Ctrl + Shift + W",
            default=True,
            )

    use_scene_refresh = BoolProperty(
            name="Refresh Scene",
            description="Specials Menu [W], or hit F5",
            default=True,
            )
    use_timeline_extra_info = BoolProperty(
            name="Timeline Extra Info",
            description="Timeline Header",
            default=True,
            )
    use_image_node_display = BoolProperty(
            name="Active Image Node in Editor",
            description="Display active node image in image editor",
            default=True,
            )
    use_scene_stats = BoolProperty(
            name="Extra Scene Statistics",
            description="Display extra scene statistics in Info editor's header",
            default=True,
            )

    frames_jump = IntProperty(
                name="Frames",
                description="Number of frames to jump forward/backward",
                default=10,
                min=1)

    use_framerate = BoolProperty(
        name="Framerate Jump",
        description="Jump the amount of frames forward/backward that you have set as your framerate",
        default=False,
    )

    use_layers_for_render = BoolProperty(
            name="Current Layers for Render",
            description="Save the layers that should be enabled for render",
            default=True,
            )


    def draw(self, context):
        layout = self.layout

        layout.label(
            text="Here you can enable or disable specific tools, "
                 "in case they interfere with others or are just plain annoying")

        split = layout.split(percentage=0.25)

        col = split.column()
        sub = col.column(align=True)
        sub.label(text="3D View", icon="VIEW3D")
        sub.prop(self, "use_frame_current")
        sub.prop(self, "use_scene_refresh")

        sub.separator()

        sub.label(text="General", icon="SCENE_DATA")
        sub.prop(self, "use_file_save_reload")
        sub.prop(self, "use_timeline_extra_info")
        sub.prop(self, "use_scene_stats")
        sub.prop(self, "use_layers_for_render")
        sub.prop(self, "use_framerate")

        sub.separator()

        sub.label(text="Nodes Editor", icon="NODETREE")
        sub.prop(self, "use_image_node_display")

        col = split.column()
        sub = col.column(align=True)
        sub.label(text="")
        sub.label(
            text="Set the current frame from the Specials menu in the 3D View [W]")
        sub.label(
            text="Refresh the current Scene. Hotkey: F5 or in Specials menu [W]")

        sub.separator()
        sub.label(text="") # General icon
        sub.label(
            text="Quickly save and reload the current file (no warning!). "
                 "File menu or Ctrl+Shift+W")
        sub.label(
            text="SMPTE Timecode and frames left/ahead on Timeline's header")
        sub.label(
            text="Display extra statistics for Scenes, Cameras, and Meshlights (Cycles)")
        sub.label(text="Save the set of layers that should be activated for a final render")
        sub.label(text="Jump the amount of frames forward/backward that you've set as your framerate")
        
        sub.separator()
        sub.label(text="") # Nodes
        sub.label(
            text="When selecting an Image node, display it on the Image editor "
                 "(if any)")

# Properties
def init_properties():

    scene = bpy.types.Scene
    node = bpy.types.Node
    nodes_compo = bpy.types.CompositorNodeTree

    scene.use_unsimplify_render = BoolProperty(
        default=False,
        name="Unsimplify Render",
        description="Disable Simplify during render")
    scene.simplify_status = BoolProperty(default=False)

    node.use_matching_indices = BoolProperty(
        default=True,
        description="If disabled, display all available indices")

    nodes_compo_types = [
        ("ALL", "All Types", "", 0),
        ("BLUR", "Blur", "", 1),
        ("BOKEHBLUR", "Bokeh Blur", "", 2),
        ("VECBLUR", "Vector Blur", "", 3),
        ("DEFOCUS", "Defocus", "", 4),
        ("R_LAYERS", "Render Layer", "", 5)
        ]

    nodes_compo.types = EnumProperty(
        items=nodes_compo_types, name = "Types")

    nodes_compo.toggle_mute = BoolProperty(default=False)
    node.status = BoolProperty(default=False)

    # Scene Debug
    # Cycles Node Types
    if check_cycles_exists():
        cycles_shader_node_types = [
            ("BSDF_DIFFUSE", "Diffuse BSDF", "", 0),
            ("BSDF_GLOSSY", "Glossy BSDF", "", 1),
            ("BSDF_TRANSPARENT", "Transparent BSDF", "", 2),
            ("BSDF_REFRACTION", "Refraction BSDF", "", 3),
            ("BSDF_GLASS", "Glass BSDF", "", 4),
            ("BSDF_TRANSLUCENT", "Translucent BSDF", "", 5),
            ("BSDF_ANISOTROPIC", "Anisotropic BSDF", "", 6),
            ("BSDF_VELVET", "Velvet BSDF", "", 7),
            ("BSDF_TOON", "Toon BSDF", "", 8),
            ("SUBSURFACE_SCATTERING", "Subsurface Scattering", "", 9),
            ("EMISSION", "Emission", "", 10),
            ("BSDF_HAIR", "Hair BSDF", "", 11),
            ("BACKGROUND", "Background", "", 12),
            ("AMBIENT_OCCLUSION", "Ambient Occlusion", "", 13),
            ("HOLDOUT", "Holdout", "", 14),
            ("VOLUME_ABSORPTION", "Volume Absorption", "", 15),
            ("VOLUME_SCATTER", "Volume Scatter", "", 16)
            ]

        scene.amaranth_cycles_node_types = EnumProperty(
            items=cycles_shader_node_types, name = "Shader")

        scene.amaranth_cycles_list_sampling = BoolProperty(
            default=False,
            name="Samples Per:")

        bpy.types.CyclesRenderSettings.use_samples_final = BoolProperty(
            name="Use Final Render Samples",
            description="Use current shader samples as final render samples",
            default=False)

    scene.amaranth_lighterscorner_list_meshlights = BoolProperty(
        default=False,
        name="List Meshlights",
        description="Include light emitting meshes on the list")

    scene.amaranth_debug_scene_list_missing_images = BoolProperty(
        default=False,
        name="List Missing Images",
        description="Display a list of all the missing images")

    bpy.types.ShaderNodeNormal.normal_vector = prop_normal_vector
    bpy.types.CompositorNodeNormal.normal_vector = prop_normal_vector

    bpy.types.Object.is_keyframe = is_keyframe

    scene.amth_wire_toggle_scene_all = BoolProperty(
        default=False,
        name="All Scenes",
        description="Toggle wire on objects in all scenes")
    scene.amth_wire_toggle_is_selected = BoolProperty(
        default=False,
        name="Only Selected",
        description="Only toggle wire on selected objects")
    scene.amth_wire_toggle_edges_all = BoolProperty(
        default=True,
        name="All Edges",
        description="Draw all edges")
    scene.amth_wire_toggle_optimal = BoolProperty(
        default=False,
        name="Optimal Display",
        description="Skip drawing/rendering of interior subdivided edges "
                    "on meshes with Subdivision Surface modifier")

def clear_properties():
    props = (
        "use_unsimplify_render",
        "simplify_status",
        "use_matching_indices",
        "use_simplify_nodes_vector",
        "status",
        "types",
        "toggle_mute",
        "amaranth_cycles_node_types",
        "amaranth_lighterscorner_list_meshlights",
        "amaranth_debug_scene_list_missing_images",
        "amarath_cycles_list_sampling",
        "normal_vector",
        "use_samples_final",
        'amth_wire_toggle_is_selected',
        'amth_wire_toggle_scene_all',
        "amth_wire_toggle_edges_all",
        "amth_wire_toggle_optimal"
    )
    
    wm = bpy.context.window_manager
    for p in props:
        if p in wm:
            del wm[p]

# Some settings are bound to be saved on a startup py file
def amaranth_text_startup(context):

    amth_text_name = "AmaranthStartup.py"
    amth_text_exists = False

    global amth_text

    try:
        if bpy.data.texts:
            for tx in bpy.data.texts:
                if tx.name == amth_text_name:
                    amth_text_exists = True
                    amth_text = bpy.data.texts[amth_text_name]
                    break
                else:
                    amth_text_exists = False

        if not amth_text_exists:
            bpy.ops.text.new()
            amth_text = bpy.data.texts[-1]
            amth_text.name = amth_text_name
            amth_text.write("# Amaranth Startup Script\nimport bpy\n\n")
            amth_text.use_module = True

        return amth_text_exists
    except AttributeError:
        return None

# FUNCTION: Check if material has Emission (for select and stats)
def cycles_is_emission(context, ob):

    is_emission = False

    if ob.material_slots:
        for ma in ob.material_slots:
            if ma.material:
                if ma.material.node_tree and ma.material.node_tree.nodes:
                    for no in ma.material.node_tree.nodes:
                        if no.type in {'EMISSION', 'GROUP'}:
                            for ou in no.outputs:
                                if ou.links:
                                    if no.type == 'GROUP' and no.node_tree and no.node_tree.nodes:
                                        for gno in no.node_tree.nodes:
                                            if gno.type == 'EMISSION':
                                                for gou in gno.outputs:
                                                    if ou.links and gou.links:
                                                        is_emission = True

                                    elif no.type == 'EMISSION':
                                        if ou.links:
                                            is_emission = True
    return is_emission

# FUNCTION: Check if object has keyframes for a specific frame
def is_keyframe(ob, frame):
    if ob is not None and ob.animation_data is not None and ob.animation_data.action is not None:
        for fcu in ob.animation_data.action.fcurves:
            if frame in (p.co.x for p in fcu.keyframe_points):
                return True
    return False

# FEATURE: Refresh Scene!
class AMTH_SCENE_OT_refresh(Operator):
    """Refresh the current scene"""
    bl_idname = "scene.refresh"
    bl_label = "Refresh!"
    
    def execute(self, context):
        preferences = context.user_preferences.addons[__name__].preferences
        scene = context.scene

        if preferences.use_scene_refresh:    
            # Changing the frame is usually the best way to go
            scene.frame_current = scene.frame_current
            self.report({"INFO"}, "Scene Refreshed!")
            
        return {'FINISHED'}

def button_refresh(self, context):

    preferences = context.user_preferences.addons[__name__].preferences

    if preferences.use_scene_refresh:
        self.layout.separator()
        self.layout.operator(
            AMTH_SCENE_OT_refresh.bl_idname,
            text="Refresh!",
            icon='FILE_REFRESH')
# // FEATURE: Refresh Scene!

# FEATURE: Save & Reload
def save_reload(self, context, path):

    if path:
        bpy.ops.wm.save_mainfile()
        self.report({'INFO'}, "Saved & Reloaded")
        bpy.ops.wm.open_mainfile("EXEC_DEFAULT", filepath=path)
    else:
        bpy.ops.wm.save_as_mainfile("INVOKE_AREA")

class AMTH_WM_OT_save_reload(Operator):
    """Save and Reload the current blend file"""
    bl_idname = "wm.save_reload"
    bl_label = "Save & Reload"

    def execute(self, context):

        path = bpy.data.filepath
        save_reload(self, context, path)
        return {'FINISHED'}

def button_save_reload(self, context):

    preferences = context.user_preferences.addons[__name__].preferences

    if preferences.use_file_save_reload:
        self.layout.separator()
        self.layout.operator(
            AMTH_WM_OT_save_reload.bl_idname,
            text="Save & Reload",
            icon='FILE_REFRESH')
# // FEATURE: Save & Reload

# FEATURE: Current Frame
def button_frame_current(self, context):

    preferences = context.user_preferences.addons[__name__].preferences
    scene = context.scene

    if preferences.use_frame_current:
        self.layout.separator()
        self.layout.prop(
            scene, "frame_current",
            text="Set Current Frame")
# // FEATURE: Current Frame

# FEATURE: Timeline Time + Frames Left
def label_timeline_extra_info(self, context):

    preferences = context.user_preferences.addons[__name__].preferences
    layout = self.layout
    scene = context.scene

    if preferences.use_timeline_extra_info:
        row = layout.row(align=True)

        row.operator(AMTH_SCREEN_OT_keyframe_jump_inbetween.bl_idname, icon="PREV_KEYFRAME", text="").backwards = True
        row.operator(AMTH_SCREEN_OT_keyframe_jump_inbetween.bl_idname, icon="NEXT_KEYFRAME", text="").backwards = False

        # Check for preview range
        frame_start = scene.frame_preview_start if scene.use_preview_range else scene.frame_start
        frame_end = scene.frame_preview_end if scene.use_preview_range else scene.frame_end
        
        row.label(text="%s / %s" % (bpy.utils.smpte_from_frame(scene.frame_current - frame_start),
                        bpy.utils.smpte_from_frame(frame_end - frame_start)))

        if (scene.frame_current > frame_end):
            row.label(text="%s Frames Ahead" % ((frame_end - scene.frame_current) * -1))
        elif (scene.frame_current == frame_start):
            row.label(text="Start Frame (%s left)" % (frame_end - scene.frame_current))
        elif (scene.frame_current == frame_end):
            row.label(text="%s End Frame" % scene.frame_current)
        else:
            row.label(text="%s Frames Left" % (frame_end - scene.frame_current))

# // FEATURE: Timeline Time + Frames Left

# FEATURE: Directory Current Blend
class AMTH_FILE_OT_directory_current_blend(Operator):
    """Go to the directory of the currently open blend file"""
    bl_idname = "file.directory_current_blend"
    bl_label = "Current Blend's Folder"

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir='//')
        return {'FINISHED'}

def button_directory_current_blend(self, context):

    if bpy.data.filepath:
        self.layout.operator(
            AMTH_FILE_OT_directory_current_blend.bl_idname,
            text="Current Blend's Folder",
            icon='APPEND_BLEND')
# // FEATURE: Directory Current Blend

# FEATURE: Libraries panel on file browser
class AMTH_FILE_PT_libraries(Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'CHANNELS'
    bl_label = "Libraries"

    def draw(self, context):
        layout = self.layout

        libs = bpy.data.libraries
        libslist = []

        # Build the list of folders from libraries
        import os.path

        for lib in libs:
            directory_name = os.path.dirname(lib.filepath)
            libslist.append(directory_name)

        # Remove duplicates and sort by name
        libslist = set(libslist)
        libslist = sorted(libslist)

        # Draw the box with libs

        row = layout.row()
        box = row.box()

        if libslist:
            col = box.column()
            for filepath in libslist:
                if filepath != '//':
                    row = col.row()
                    row.alignment = 'LEFT'
                    props = row.operator(
                        AMTH_FILE_OT_directory_go_to.bl_idname,
                        text=filepath, icon="BOOKMARKS",
                        emboss=False)
                    props.filepath = filepath
        else:
            box.label(text='No libraries loaded')

class AMTH_FILE_OT_directory_go_to(Operator):
    """Go to this library's directory"""
    bl_idname = "file.directory_go_to"
    bl_label = "Go To"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir=self.filepath)
        return {'FINISHED'}

# FEATURE: Node Templates
class AMTH_NODE_OT_AddTemplateVignette(Operator):
    bl_idname = "node.template_add_vignette"
    bl_label = "Add Vignette"
    bl_description = "Add a vignette effect"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' \
                and space.node_tree is not None \
                and space.tree_type == 'CompositorNodeTree'

    # used as reference the setup scene script from master nazgul
    def _setupNodes(self, context):
        scene = context.scene
        space = context.space_data
        tree = scene.node_tree
        has_act = True if tree.nodes.active else False

        bpy.ops.node.select_all(action='DESELECT')

        ellipse = tree.nodes.new(type='CompositorNodeEllipseMask')
        ellipse.width = 0.8
        ellipse.height = 0.4
        blur = tree.nodes.new(type='CompositorNodeBlur')
        blur.use_relative = True
        blur.factor_x = 30
        blur.factor_y = 50
        ramp = tree.nodes.new(type='CompositorNodeValToRGB')
        ramp.color_ramp.interpolation = 'B_SPLINE'
        ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1)

        overlay = tree.nodes.new(type='CompositorNodeMixRGB')
        overlay.blend_type = 'OVERLAY'
        overlay.inputs[0].default_value = 0.8
        overlay.inputs[1].default_value = (0.5, 0.5, 0.5, 1)

        tree.links.new(ellipse.outputs["Mask"],blur.inputs["Image"])
        tree.links.new(blur.outputs["Image"],ramp.inputs[0])
        tree.links.new(ramp.outputs["Image"],overlay.inputs[2])
        if has_act:
            tree.links.new(tree.nodes.active.outputs[0],overlay.inputs[1])

        if has_act:
            overlay.location = tree.nodes.active.location
            overlay.location += Vector((350.0, 0.0))
        else:
            overlay.location += Vector((space.cursor_location[0], space.cursor_location[1]))

        ellipse.location = overlay.location
        ellipse.location += Vector((-715.0, -400))
        ellipse.inputs[0].hide = True
        ellipse.inputs[1].hide = True

        blur.location = ellipse.location
        blur.location += Vector((300.0, 0.0))
        blur.inputs['Size'].hide = True

        ramp.location = blur.location
        ramp.location += Vector((175.0, 0))
        ramp.outputs['Alpha'].hide = True

        for node in {ellipse, blur, ramp, overlay}:
            node.select = True
            node.show_preview = False

        bpy.ops.node.join()

        frame = ellipse.parent
        frame.label = 'Vignette'
        frame.use_custom_color = True
        frame.color = (0.1, 0.1, 0.1)
        
        overlay.parent = None
        overlay.label = 'Vignette Overlay'

    def execute(self, context):
        self._setupNodes(context)

        return {'FINISHED'}

class AMTH_NODE_OT_AddTemplateVectorBlur(Operator):
    bl_idname = "node.template_add_vectorblur"
    bl_label = "Add Vector Blur"
    bl_description = "Add a vector blur filter"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        tree = context.scene.node_tree
        return space.type == 'NODE_EDITOR' \
                and space.node_tree is not None \
                and space.tree_type == 'CompositorNodeTree' \
                and tree \
                and tree.nodes.active \
                and tree.nodes.active.type == 'R_LAYERS'

    def _setupNodes(self, context):
        scene = context.scene
        space = context.space_data
        tree = scene.node_tree

        bpy.ops.node.select_all(action='DESELECT')

        act_node = tree.nodes.active
        rlayer = act_node.scene.render.layers[act_node.layer]

        if not rlayer.use_pass_vector:
            rlayer.use_pass_vector = True

        vblur = tree.nodes.new(type='CompositorNodeVecBlur')
        vblur.use_curved = True
        vblur.factor = 0.5

        tree.links.new(act_node.outputs["Image"],vblur.inputs["Image"])
        tree.links.new(act_node.outputs["Z"],vblur.inputs["Z"])
        tree.links.new(act_node.outputs["Speed"],vblur.inputs["Speed"])

        if tree.nodes.active:
            vblur.location = tree.nodes.active.location
            vblur.location += Vector((250.0, 0.0))
        else:
            vblur.location += Vector((space.cursor_location[0], space.cursor_location[1]))

        vblur.select = True

    def execute(self, context):
        self._setupNodes(context)

        return {'FINISHED'}

# Node Templates Menu
class AMTH_NODE_MT_amaranth_templates(Menu):
    bl_idname = 'AMTH_NODE_MT_amaranth_templates'
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Templates"
    bl_description = "List of Amaranth Templates"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            AMTH_NODE_OT_AddTemplateVectorBlur.bl_idname,
            text="Vector Blur",
            icon='FORCE_HARMONIC')
        layout.operator(
            AMTH_NODE_OT_AddTemplateVignette.bl_idname,
            text="Vignette",
            icon='COLOR')

def node_templates_pulldown(self, context):
    if context.space_data.tree_type == 'CompositorNodeTree':
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        row.menu("AMTH_NODE_MT_amaranth_templates",
            icon="NODETREE")
# // FEATURE: Node Templates

def node_stats(self,context):
    if context.scene.node_tree:
        tree_type = context.space_data.tree_type
        nodes = context.scene.node_tree.nodes
        nodes_total = len(nodes.keys())
        nodes_selected = 0
        for n in nodes:
            if n.select:
                nodes_selected = nodes_selected + 1

        if tree_type == 'CompositorNodeTree':
            layout = self.layout
            row = layout.row(align=True)
            row.label(text="Nodes: %s/%s" % (nodes_selected, str(nodes_total)))

# FEATURE: Simplify Compo Nodes
class AMTH_NODE_PT_simplify(Panel):
    '''Simplify Compositor Panel'''
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = 'Simplify'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' \
                and space.node_tree is not None \
                and space.tree_type == 'CompositorNodeTree'

    def draw(self, context):
        layout = self.layout
        node_tree = context.scene.node_tree

        if node_tree is not None:
            layout.prop(node_tree, 'types')
            layout.operator(AMTH_NODE_OT_toggle_mute.bl_idname,
                text="Turn On" if node_tree.toggle_mute else "Turn Off",
                icon='RESTRICT_VIEW_OFF' if node_tree.toggle_mute else 'RESTRICT_VIEW_ON')
        
            if node_tree.types == 'VECBLUR':
                layout.label(text="This will also toggle the Vector pass {}".format(
                                    "on" if node_tree.toggle_mute else "off"), icon="INFO")

class AMTH_NODE_OT_toggle_mute(Operator):
    """"""
    bl_idname = "node.toggle_mute"
    bl_label = "Toggle Mute"

    def execute(self, context):
        scene = context.scene
        node_tree = scene.node_tree
        node_type = node_tree.types
        rlayers = scene.render
        
        if not 'amaranth_pass_vector' in scene.keys():
            scene['amaranth_pass_vector'] = []
        
        #can't extend() the list, so make a dummy one
        pass_vector = scene['amaranth_pass_vector']

        if not pass_vector:
            pass_vector = []

        if node_tree.toggle_mute:
            for node in node_tree.nodes:
                if node_type == 'ALL':
                    node.mute = node.status
                if node.type == node_type:
                    node.mute = node.status
                if node_type == 'VECBLUR':
                    for layer in rlayers.layers:
                        if layer.name in pass_vector:
                            layer.use_pass_vector = True
                            pass_vector.remove(layer.name)

                node_tree.toggle_mute = False

        else:
            for node in node_tree.nodes:
                if node_type == 'ALL':
                    node.mute = True
                if node.type == node_type:
                    node.status = node.mute
                    node.mute = True
                if node_type == 'VECBLUR':
                    for layer in rlayers.layers:
                        if layer.use_pass_vector:
                            pass_vector.append(layer.name)
                            layer.use_pass_vector = False
                            pass

                node_tree.toggle_mute = True

        # Write back to the custom prop
        pass_vector = sorted(set(pass_vector))
        scene['amaranth_pass_vector'] = pass_vector

        return {'FINISHED'}
        

# FEATURE: OB/MA ID panel in Node Editor
class AMTH_NODE_PT_indices(Panel):
    '''Object / Material Indices Panel'''
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = 'Object / Material Indices'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node and node.type == 'ID_MASK'

    def draw(self, context):
        layout = self.layout

        objects = bpy.data.objects
        materials = bpy.data.materials
        node = context.active_node

        show_ob_id = False
        show_ma_id = False
        matching_ids = False

        if context.active_object:
            ob_act = context.active_object
        else:
            ob_act = False

        for ob in objects:
            if ob and ob.pass_index > 0:
                show_ob_id = True
        for ma in materials:
            if ma and ma.pass_index > 0:
                show_ma_id = True
        row = layout.row(align=True)  
        row.prop(node, 'index', text="Mask Index")
        row.prop(node, 'use_matching_indices', text="Only Matching IDs")
        
        layout.separator()

        if not show_ob_id and not show_ma_id:
            layout.label(text="No objects or materials indices so far.", icon="INFO")

        if show_ob_id:
            split = layout.split()
            col = split.column()
            col.label(text="Object Name")
            split.label(text="ID Number")
            row = layout.row()
            for ob in objects:
                icon = "OUTLINER_DATA_" + ob.type
                if ob.library:
                    icon = "LIBRARY_DATA_DIRECT"
                elif ob.is_library_indirect:
                    icon = "LIBRARY_DATA_INDIRECT"

                if ob and node.use_matching_indices \
                      and ob.pass_index == node.index \
                      and ob.pass_index != 0:
                    matching_ids = True
                    row.label(
                      text="[{}]".format(ob.name)
                          if ob_act and ob.name == ob_act.name else ob.name,
                      icon=icon)
                    row.label(text="%s" % ob.pass_index)
                    row = layout.row()

                elif ob and not node.use_matching_indices \
                        and ob.pass_index > 0:

                    matching_ids = True
                    row.label(
                      text="[{}]".format(ob.name)
                          if ob_act and ob.name == ob_act.name else ob.name,
                      icon=icon)
                    row.label(text="%s" % ob.pass_index)
                    row = layout.row()

            if node.use_matching_indices and not matching_ids:
                row.label(text="No objects with ID %s" % node.index, icon="INFO")

            layout.separator()

        if show_ma_id:
            split = layout.split()
            col = split.column()
            col.label(text="Material Name")
            split.label(text="ID Number")
            row = layout.row()

            for ma in materials:
                icon = "BLANK1"
                if ma.use_nodes:
                    icon = "NODETREE"
                elif ma.library:
                    icon = "LIBRARY_DATA_DIRECT"
                    if ma.is_library_indirect:
                        icon = "LIBRARY_DATA_INDIRECT"

                if ma and node.use_matching_indices \
                      and ma.pass_index == node.index \
                      and ma.pass_index != 0:
                    matching_ids = True
                    row.label(text="%s" % ma.name, icon=icon)
                    row.label(text="%s" % ma.pass_index)
                    row = layout.row()

                elif ma and not node.use_matching_indices \
                        and ma.pass_index > 0:

                    matching_ids = True
                    row.label(text="%s" % ma.name, icon=icon)
                    row.label(text="%s" % ma.pass_index)
                    row = layout.row()

            if node.use_matching_indices and not matching_ids:
                row.label(text="No materials with ID %s" % node.index, icon="INFO")


# // FEATURE: OB/MA ID panel in Node Editor

# FEATURE: Unsimplify on render
@persistent
def unsimplify_render_pre(scene):
    render = scene.render
    scene.simplify_status = render.use_simplify

    if scene.use_unsimplify_render:
        render.use_simplify = False

@persistent
def unsimplify_render_post(scene):
    render = scene.render
    render.use_simplify = scene.simplify_status

def unsimplify_ui(self,context):
    scene = bpy.context.scene
    self.layout.prop(scene, 'use_unsimplify_render')
# //FEATURE: Unsimplify on render

# FEATURE: Extra Info Stats
def stats_scene(self, context):

    preferences = context.user_preferences.addons[__name__].preferences

    if preferences.use_scene_stats:
        scenes_count = str(len(bpy.data.scenes))
        cameras_count = str(len(bpy.data.cameras))
        cameras_selected = 0
        meshlights = 0
        meshlights_visible = 0

        for ob in context.scene.objects:
            if cycles_is_emission(context, ob):
                meshlights += 1
                if ob in context.visible_objects:
                    meshlights_visible += 1

            if ob in context.selected_objects:
                if ob.type == 'CAMERA':
                    cameras_selected += 1
    
        meshlights_string = '| Meshlights:{}/{}'.format(meshlights_visible, meshlights)
    
        row = self.layout.row(align=True)
        row.label(text="Scenes:{} | Cameras:{}/{} {}".format(
                   scenes_count, cameras_selected, cameras_count,
                   meshlights_string if context.scene.render.engine == 'CYCLES' else ''))

# //FEATURE: Extra Info Stats

# FEATURE: Camera Bounds as Render Border
class AMTH_VIEW3D_OT_render_border_camera(Operator):
    """Set camera bounds as render border"""
    bl_idname = "view3d.render_border_camera"
    bl_label = "Camera as Render Border"

    @classmethod
    def poll(cls, context):
        return context.space_data.region_3d.view_perspective == 'CAMERA'

    def execute(self, context):
        render = context.scene.render
        render.use_border = True
        render.border_min_x = 0
        render.border_min_y = 0
        render.border_max_x = 1
        render.border_max_y = 1

        return {'FINISHED'}

def button_render_border_camera(self, context):

    view3d = context.space_data.region_3d
    
    if view3d.view_perspective == 'CAMERA':
        layout = self.layout
        layout.separator()
        layout.operator(AMTH_VIEW3D_OT_render_border_camera.bl_idname,
                        text="Camera as Render Border", icon="FULLSCREEN_ENTER")

# //FEATURE: Camera Bounds as Render Border

# FEATURE: Passepartout options on W menu
def button_camera_passepartout(self, context):

    view3d = context.space_data.region_3d
    cam = context.scene.camera.data
    
    if view3d.view_perspective == 'CAMERA':
        layout = self.layout
        if cam.show_passepartout:
            layout.prop(cam, "passepartout_alpha", text="Passepartout")
        else:
            layout.prop(cam, "show_passepartout")

# FEATURE: Show Only Render with Alt+Shift+Z
class AMTH_VIEW3D_OT_show_only_render(Operator):
    bl_idname = "view3d.show_only_render"
    bl_label = "Show Only Render"

    def execute(self, context):
        space = bpy.context.space_data
        
        if space.show_only_render:
            space.show_only_render = False
        else:
            space.show_only_render = True
        return {'FINISHED'}


# FEATURE: Display Active Image Node on Image Editor
# Made by Sergey Sharybin, tweaks from Bassam Kurdali
image_nodes = {"CompositorNodeImage",
               "CompositorNodeViewer",
               "CompositorNodeComposite",
               "ShaderNodeTexImage",
               "ShaderNodeTexEnvironment"}

class AMTH_NODE_OT_show_active_node_image(Operator):
    """Show active image node image in the image editor"""
    bl_idname = "node.show_active_node_image"
    bl_label = "Show Active Node Node"
    bl_options = {'UNDO'}

    def execute(self, context):
        preferences = context.user_preferences.addons[__name__].preferences
        if preferences.use_image_node_display:
            if context.active_node:
                active_node = context.active_node

                if active_node.bl_idname in image_nodes:
                    for area in context.screen.areas:
                        if area.type == "IMAGE_EDITOR":
                            for space in area.spaces:
                                if space.type == "IMAGE_EDITOR":
                                    if active_node.bl_idname == 'CompositorNodeViewer':
                                        space.image = bpy.data.images['Viewer Node']
                                    elif active_node.bl_idname == 'CompositorNodeComposite':
                                        space.image = bpy.data.images['Render Result']
                                    elif active_node.image:
                                        space.image = active_node.image
                            break

        return {'FINISHED'}
# // FEATURE: Display Active Image Node on Image Editor

# FEATURE: Select Meshlights
class AMTH_OBJECT_OT_select_meshlights(Operator):
    """Select light emitting meshes"""
    bl_idname = "object.select_meshlights"
    bl_label = "Select Meshlights"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'CYCLES'

    def execute(self, context):
        # Deselect everything first
        bpy.ops.object.select_all(action='DESELECT')

        for ob in context.scene.objects:
            if cycles_is_emission(context, ob):
                ob.select = True
                context.scene.objects.active = ob

        if not context.selected_objects and not context.scene.objects.active:
            self.report({'INFO'}, "No meshlights to select")

        return {'FINISHED'}

def button_select_meshlights(self, context):
    if cycles_exists and context.scene.render.engine == 'CYCLES':
        self.layout.operator('object.select_meshlights', icon="LAMP_SUN")
# // FEATURE: Select Meshlights

# FEATURE: Mesh Symmetry Tools by Sergey Sharybin
class AMTH_MESH_OT_find_asymmetric(Operator):
    """
    Find asymmetric vertices
    """

    bl_idname = "mesh.find_asymmetric"
    bl_label = "Find Asymmetric"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        object = context.object
        if object:
            return object.mode == 'EDIT' and object.type == 'MESH'
        return False

    def execute(self, context):
        threshold = 1e-6

        object = context.object
        bm = bmesh.from_edit_mesh(object.data)

        # Deselect all the vertices
        for v in bm.verts:
            v.select = False

        for v1 in bm.verts:
            if abs(v1.co[0]) < threshold:
                continue

            mirror_found = False
            for v2 in bm.verts:
                if v1 == v2:
                    continue
                if v1.co[0] * v2.co[0] > 0.0:
                    continue

                mirror_coord = Vector(v2.co)
                mirror_coord[0] *= -1
                if (mirror_coord - v1.co).length_squared < threshold:
                    mirror_found = True
                    break
            if not mirror_found:
                v1.select = True

        bm.select_flush_mode()

        bmesh.update_edit_mesh(object.data)

        return {'FINISHED'}

class AMTH_MESH_OT_make_symmetric(Operator):
    """
    Make symmetric
    """

    bl_idname = "mesh.make_symmetric"
    bl_label = "Make Symmetric"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        object = context.object
        if object:
            return object.mode == 'EDIT' and object.type == 'MESH'
        return False

    def execute(self, context):
        threshold = 1e-6

        object = context.object
        bm = bmesh.from_edit_mesh(object.data)

        for v1 in bm.verts:
            if v1.co[0] < threshold:
                continue
            if not v1.select:
                continue

            closest_vert = None
            closest_distance = -1
            for v2 in bm.verts:
                if v1 == v2:
                    continue
                if v2.co[0] > threshold:
                    continue
                if not v2.select:
                    continue

                mirror_coord = Vector(v2.co)
                mirror_coord[0] *= -1
                distance = (mirror_coord - v1.co).length_squared
                if closest_vert is None or distance < closest_distance:
                    closest_distance = distance
                    closest_vert = v2

            if closest_vert:
                closest_vert.select = False
                closest_vert.co = Vector(v1.co)
                closest_vert.co[0] *= -1
            v1.select = False

        for v1 in bm.verts:
            if v1.select:
                closest_vert = None
                closest_distance = -1
                for v2 in bm.verts:
                    if v1 != v2:
                        mirror_coord = Vector(v2.co)
                        mirror_coord[0] *= -1
                        distance = (mirror_coord - v1.co).length_squared
                        if closest_vert is None or distance < closest_distance:
                            closest_distance = distance
                            closest_vert = v2
                if closest_vert:
                    v1.select = False
                    v1.co = Vector(closest_vert.co)
                    v1.co[0] *= -1

        bm.select_flush_mode()
        bmesh.update_edit_mesh(object.data)

        return {'FINISHED'}
# // FEATURE: Mesh Symmetry Tools by Sergey Sharybin

# FEATURE: Cycles Render Sampling Extra
def render_cycles_scene_samples(self, context):

    layout = self.layout
    scenes = bpy.data.scenes
    scene = context.scene
    render = scene.render
    if cycles_exists:
        cscene = scene.cycles
        list_sampling = scene.amaranth_cycles_list_sampling

    # Set Render Samples
    if cycles_exists and cscene.progressive == 'BRANCHED_PATH':
        layout.separator()
        split = layout.split()
        col = split.column()

        col.operator(
            AMTH_RENDER_OT_cycles_samples_percentage_set.bl_idname,
            text="%s" % 'Set as Render Samples' if cscene.use_samples_final else 'Set New Render Samples',
            icon="%s" % 'PINNED' if cscene.use_samples_final else 'UNPINNED')

        col = split.column()
        row = col.row(align=True)
        row.enabled = True if scene.get('amth_cycles_samples_final') else False

        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="100%").percent=100
        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="75%").percent=75
        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="50%").percent=50
        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="25%").percent=25

    # List Samples
    if (len(scene.render.layers) > 1) or \
        (len(bpy.data.scenes) > 1):

        box = layout.box()
        row = box.row(align=True)
        col = row.column(align=True)

        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.prop(scene, 'amaranth_cycles_list_sampling',
                    icon="%s" % 'TRIA_DOWN' if list_sampling else 'TRIA_RIGHT',
                    emboss=False)

    if list_sampling:
        if len(scene.render.layers) == 1 and \
            render.layers[0].samples == 0:
            pass
        else:
            col.separator()
            col.label(text="RenderLayers:", icon='RENDERLAYERS')

            for rl in scene.render.layers:
                row = col.row(align=True)
                row.label(rl.name, icon='BLANK1')
                row.prop(rl, "samples", text="%s" %
                    "Samples" if rl.samples > 0 else "Automatic (%s)" % (
                        cscene.aa_samples if cscene.progressive == 'BRANCHED_PATH' else cscene.samples))

        if (len(bpy.data.scenes) > 1):
            col.separator()

            col.label(text="Scenes:", icon='SCENE_DATA')

            if cycles_exists and cscene.progressive == 'PATH':
                for s in bpy.data.scenes:
                    if s != scene:
                        row = col.row(align=True)
                        if s.render.engine == 'CYCLES':
                            cscene = s.cycles

                            row.label(s.name)
                            row.prop(cscene, "samples", icon='BLANK1')
                        else:
                            row.label(text="Scene: '%s' is not using Cycles" % s.name)
            else:
                for s in bpy.data.scenes:
                    if s != scene:
                        row = col.row(align=True)
                        if s.render.engine == 'CYCLES':
                            cscene = s.cycles

                            row.label(s.name, icon='BLANK1')
                            row.prop(cscene, "aa_samples",
                                text="AA Samples")
                        else:
                            row.label(text="Scene: '%s' is not using Cycles" % s.name)

# // FEATURE: Cycles Render Sampling Extra

# FEATURE: Motion Paths Extras
class AMTH_POSE_OT_paths_clear_all(Operator):
    """Clear motion paths from all bones"""
    bl_idname = "pose.paths_clear_all"
    bl_label = "Clear All Motion Paths"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE'

    def execute(self, context):
        #silly but works
        for b in context.object.data.bones:
            b.select = True
            bpy.ops.pose.paths_clear()
            b.select = False
        return {'FINISHED'}

class AMTH_POSE_OT_paths_frame_match(Operator):
    """Match Start/End frame of scene to motion path range"""
    bl_idname = "pose.paths_frame_match"
    bl_label = "Match Frame Range"
    bl_options = {'UNDO'}

    def execute(self, context):
        avs = context.object.pose.animation_visualization
        scene = context.scene

        if avs.motion_path.type == 'RANGE':
            if scene.use_preview_range:
                avs.motion_path.frame_start = scene.frame_preview_start
                avs.motion_path.frame_end = scene.frame_preview_end
            else:
                avs.motion_path.frame_start = scene.frame_start
                avs.motion_path.frame_end = scene.frame_end

        else:
            if scene.use_preview_range:
                avs.motion_path.frame_before = scene.frame_preview_start
                avs.motion_path.frame_after = scene.frame_preview_end
            else:
                avs.motion_path.frame_before = scene.frame_start
                avs.motion_path.frame_after = scene.frame_end

        return {'FINISHED'}

def pose_motion_paths_ui(self, context):

    layout = self.layout
    scene = context.scene
    avs = context.object.pose.animation_visualization
    if context.active_pose_bone:
        mpath = context.active_pose_bone.motion_path
    layout.separator()    
    layout.label(text="Motion Paths Extras:")

    split = layout.split()

    col = split.column(align=True)

    if context.selected_pose_bones:
        if mpath:
            sub = col.row(align=True)
            sub.operator("pose.paths_update", text="Update Path", icon='BONE_DATA')
            sub.operator("pose.paths_clear", text="", icon='X')
        else:
            col.operator("pose.paths_calculate", text="Calculate Path", icon='BONE_DATA')
    else:
        col.label(text="Select Bones First", icon="ERROR")

    col = split.column(align=True)
    col.operator(AMTH_POSE_OT_paths_frame_match.bl_idname,
        text="{}".format( "Set Preview Frame Range"
                if scene.use_preview_range else "Set Frame Range"),
        icon="{}".format("PREVIEW_RANGE"
                if scene.use_preview_range else "TIME"))

    col = layout.column()
    row = col.row(align=True)

    if avs.motion_path.type == 'RANGE':
        row.prop(avs.motion_path, "frame_start", text="Start")
        row.prop(avs.motion_path, "frame_end", text="End")
    else:
        row.prop(avs.motion_path, "frame_before", text="Before")
        row.prop(avs.motion_path, "frame_after", text="After")

    layout.separator()
    layout.operator(AMTH_POSE_OT_paths_clear_all.bl_idname, icon="X")
# // FEATURE: Motion Paths Extras

# FEATURE: Final Render Resolution Display
def render_final_resolution_ui(self, context):

    rd = context.scene.render
    layout = self.layout

    final_res_x = (rd.resolution_x * rd.resolution_percentage) / 100
    final_res_y = (rd.resolution_y * rd.resolution_percentage) / 100

    if rd.use_border:
       final_res_x_border = round((final_res_x * (rd.border_max_x - rd.border_min_x)))
       final_res_y_border = round((final_res_y * (rd.border_max_y - rd.border_min_y)))
       layout.label(text="Final Resolution: {} x {} [Border: {} x {}]".format(
             str(final_res_x)[:-2], str(final_res_y)[:-2],
             str(final_res_x_border), str(final_res_y_border)))
    else:
        layout.label(text="Final Resolution: {} x {}".format(
             str(final_res_x)[:-2], str(final_res_y)[:-2]))
# // FEATURE: Final Render Resolution Display

# FEATURE: Shader Nodes Extra Info
def node_shader_extra(self, context):

    if context.space_data.tree_type == 'ShaderNodeTree':
        ob = context.active_object
        snode = context.space_data
        layout = self.layout

        if ob and snode.shader_type != 'WORLD':
            if ob.type == 'LAMP':
                layout.label(text="%s" % ob.name,
                             icon="LAMP_%s" % ob.data.type)        
            else:
                layout.label(text="%s" % ob.name,
                             icon="OUTLINER_DATA_%s" % ob.type)
             

# // FEATURE: Shader Nodes Extra Info

# FEATURE: Scene Debug
class AMTH_SCENE_OT_cycles_shader_list_nodes(Operator):
    """List Cycles materials containing a specific shader"""
    bl_idname = "scene.cycles_list_nodes"
    bl_label = "List Materials"
    materials = []

    @classmethod
    def poll(cls, context):
        return cycles_exists and context.scene.render.engine == 'CYCLES'

    def execute(self, context):
        node_type = context.scene.amaranth_cycles_node_types
        roughness = False
        self.__class__.materials = []
        shaders_roughness = ['BSDF_GLOSSY','BSDF_DIFFUSE','BSDF_GLASS']

        print("\n=== Cycles Shader Type: %s === \n" % node_type)

        for ma in bpy.data.materials:
            if ma.node_tree:
                nodes = ma.node_tree.nodes
                
                print_unconnected = ('Note: \nOutput from "%s" node' % node_type,
                                        'in material "%s"' % ma.name, 'not connected\n')

                for no in nodes:
                    if no.type == node_type:
                        for ou in no.outputs:
                            if ou.links:
                                connected = True
                                if no.type in shaders_roughness:
                                    roughness = 'R: %.4f' % no.inputs['Roughness'].default_value
                                else:
                                    roughness = False
                            else:
                                connected = False
                                print(print_unconnected)

                            if ma.name not in self.__class__.materials:
                                self.__class__.materials.append('%s%s [%s] %s%s%s' % (
                                    '[L] ' if ma.library else '',
                                    ma.name, ma.users,
                                    '[F]' if ma.use_fake_user else '',
                                    ' - [%s]' % roughness if roughness else '',
                                    ' * Output not connected' if not connected else ''))

                    elif no.type == 'GROUP':
                        if no.node_tree:
                            for nog in no.node_tree.nodes:
                                if nog.type == node_type:
                                    for ou in nog.outputs:
                                        if ou.links:
                                            connected = True
                                            if nog.type in shaders_roughness:
                                                roughness = 'R: %.4f' % nog.inputs['Roughness'].default_value
                                            else:
                                                roughness = False
                                        else:
                                            connected = False
                                            print(print_unconnected)

                                        if ma.name not in self.__class__.materials:
                                            self.__class__.materials.append('%s%s%s [%s] %s%s%s' % (
                                                '[L] ' if ma.library else '',
                                                'Node Group:  %s%s  ->  ' % (
                                                    '[L] ' if no.node_tree.library else '',
                                                    no.node_tree.name),
                                                ma.name, ma.users,
                                                '[F]' if ma.use_fake_user else '',
                                                ' - [%s]' % roughness if roughness else '',
                                                ' * Output not connected' if not connected else ''))

                    self.__class__.materials = sorted(list(set(self.__class__.materials)))

        if len(self.__class__.materials) == 0:
            self.report({"INFO"}, "No materials with nodes type %s found" % node_type)
        else:
            print("* A total of %d %s using %s was found \n" % (
                    len(self.__class__.materials),
                    "material" if len(self.__class__.materials) == 1 else "materials",
                    node_type))

            count = 0

            for mat in self.__class__.materials:
                print('%02d. %s' % (count+1, self.__class__.materials[count]))
                count += 1
            print("\n")

        self.__class__.materials = sorted(list(set(self.__class__.materials)))

        return {'FINISHED'}

class AMTH_SCENE_OT_cycles_shader_list_nodes_clear(Operator):
    """Clear the list below"""
    bl_idname = "scene.cycles_list_nodes_clear"
    bl_label = "Clear Materials List"

    @classmethod
    def poll(cls, context):
        return cycles_exists

    def execute(self, context):
        AMTH_SCENE_OT_cycles_shader_list_nodes.materials[:] = []
        print("* Cleared Cycles Materials List")
        return {'FINISHED'}

class AMTH_SCENE_OT_amaranth_object_select(Operator):
    '''Select object'''
    bl_idname = "scene.amaranth_object_select"
    bl_label = "Select Object"
    object = bpy.props.StringProperty()
 
    def execute(self, context):
        if self.object:
            object = bpy.data.objects[self.object]

            bpy.ops.object.select_all(action='DESELECT')
            object.select = True
            context.scene.objects.active = object

        return{'FINISHED'}

class AMTH_SCENE_OT_list_missing_node_links(Operator):
    '''Print a list of missing node links'''
    bl_idname = "scene.list_missing_node_links"
    bl_label = "List Missing Node Links"

    count_groups = 0
    count_images = 0
    count_image_node_unlinked = 0

    def execute(self, context):
        missing_groups = []
        missing_images = []
        image_nodes_unlinked = []
        libraries = []
        self.__class__.count_groups = 0
        self.__class__.count_images = 0
        self.__class__.count_image_node_unlinked = 0

        for ma in bpy.data.materials:
            if ma.node_tree:
                for no in ma.node_tree.nodes:
                    if no.type == 'GROUP':
                        if not no.node_tree:
                            self.__class__.count_groups += 1

                            users_ngroup = []

                            for ob in bpy.data.objects:
                                if ob.material_slots and ma.name in ob.material_slots:
                                    users_ngroup.append("%s%s%s" % (
                                        "[L] " if ob.library else "",
                                        "[F] " if ob.use_fake_user else "",
                                        ob.name))

                            missing_groups.append("MA: %s%s%s [%s]%s%s%s\n" % (
                                "[L] " if ma.library else "",
                                "[F] " if ma.use_fake_user else "",
                                ma.name, ma.users,
                                " *** No users *** " if ma.users == 0 else "",
                                "\nLI: %s" % 
                                ma.library.filepath if ma.library else "",
                                "\nOB: %s" % ',  '.join(users_ngroup) if users_ngroup else ""))

                            if ma.library:
                                libraries.append(ma.library.filepath)
                    if no.type == 'TEX_IMAGE':

                        outputs_empty = not no.outputs['Color'].is_linked and not no.outputs['Alpha'].is_linked

                        if no.image:
                            import os.path
                            image_path_exists = os.path.exists(
                                                    bpy.path.abspath(
                                                        no.image.filepath, library=no.image.library))

                        if outputs_empty or not \
                           no.image or not \
                           image_path_exists:

                            users_images = []

                            for ob in bpy.data.objects:
                                if ob.material_slots and ma.name in ob.material_slots:
                                    users_images.append("%s%s%s" % (
                                        "[L] " if ob.library else "",
                                        "[F] " if ob.use_fake_user else "",
                                        ob.name))

                            if outputs_empty:
                                self.__class__.count_image_node_unlinked += 1

                                image_nodes_unlinked.append("%s%s%s%s%s [%s]%s%s%s%s%s\n" % (
                                    "NO: %s" % no.name,
                                    "\nMA: ",
                                    "[L] " if ma.library else "",
                                    "[F] " if ma.use_fake_user else "",
                                    ma.name, ma.users,
                                    " *** No users *** " if ma.users == 0 else "",
                                    "\nLI: %s" % 
                                    ma.library.filepath if ma.library else "",
                                    "\nIM: %s" % no.image.name if no.image else "",
                                    "\nLI: %s" % no.image.filepath if no.image and no.image.filepath else "",
                                    "\nOB: %s" % ',  '.join(users_images) if users_images else ""))
                            

                            if not no.image or not image_path_exists:
                                self.__class__.count_images += 1

                                missing_images.append("MA: %s%s%s [%s]%s%s%s%s%s\n" % (
                                    "[L] " if ma.library else "",
                                    "[F] " if ma.use_fake_user else "",
                                    ma.name, ma.users,
                                    " *** No users *** " if ma.users == 0 else "",
                                    "\nLI: %s" % 
                                    ma.library.filepath if ma.library else "",
                                    "\nIM: %s" % no.image.name if no.image else "",
                                    "\nLI: %s" % no.image.filepath if no.image and no.image.filepath else "",
                                    "\nOB: %s" % ',  '.join(users_images) if users_images else ""))

                                if ma.library:
                                    libraries.append(ma.library.filepath)

        # Remove duplicates and sort
        missing_groups = sorted(list(set(missing_groups)))
        missing_images = sorted(list(set(missing_images)))
        image_nodes_unlinked = sorted(list(set(image_nodes_unlinked)))
        libraries = sorted(list(set(libraries)))

        print("\n\n== %s missing image %s, %s missing node %s and %s image %s unlinked ==" %
            ("No" if self.__class__.count_images == 0 else str(self.__class__.count_images),
            "node" if self.__class__.count_images == 1 else "nodes",
            "no" if self.__class__.count_groups == 0 else str(self.__class__.count_groups),
            "group" if self.__class__.count_groups == 1 else "groups",
            "no" if self.__class__.count_image_node_unlinked == 0 else str(self.__class__.count_image_node_unlinked),
            "node" if self.__class__.count_groups == 1 else "nodes"))

        # List Missing Node Groups
        if missing_groups:
            print("\n* Missing Node Group Links\n")
            for mig in missing_groups:
                print(mig)

        # List Missing Image Nodes
        if missing_images:
            print("\n* Missing Image Nodes Link\n")

            for mii in missing_images:
                print(mii)

        # List Image Nodes with its outputs unlinked
        if image_nodes_unlinked:
            print("\n* Image Nodes Unlinked\n")

            for nou in image_nodes_unlinked:
                print(nou)

        if missing_groups or \
           missing_images or \
           image_nodes_unlinked:
            if libraries:
                print("\nThat's bad, run check on %s:" % (
                    "this library" if len(libraries) == 1 else "these libraries"))
                for li in libraries:
                    print(li)
        else:
            self.report({"INFO"}, "Yay! No missing node links")            

        print("\n")

        if missing_groups and missing_images:
            self.report({"WARNING"}, "%d missing image %s and %d missing node %s found" %
                (self.__class__.count_images, "node" if self.__class__.count_images == 1 else "nodes",
                self.__class__.count_groups, "group" if self.__class__.count_groups == 1 else "groups"))

        return{'FINISHED'}

class AMTH_SCENE_OT_list_missing_material_slots(Operator):
    '''List objects with empty material slots'''
    bl_idname = "scene.list_missing_material_slots"
    bl_label = "List Empty Material Slots"

    objects = []
    libraries = []

    def execute(self, context):
        self.__class__.objects = []
        self.__class__.libraries = []

        for ob in bpy.data.objects:
            for ma in ob.material_slots:
                if not ma.material:
                    self.__class__.objects.append('%s%s' % (
                        '[L] ' if ob.library else '',
                        ob.name))
                    if ob.library:
                        self.__class__.libraries.append(ob.library.filepath)

        self.__class__.objects = sorted(list(set(self.__class__.objects)))
        self.__class__.libraries = sorted(list(set(self.__class__.libraries)))

        if len(self.__class__.objects) == 0:
            self.report({"INFO"}, "No objects with empty material slots found")
        else:
            print("\n* A total of %d %s with empty material slots was found \n" % (
                    len(self.__class__.objects),
                    "object" if len(self.__class__.objects) == 1 else "objects"))

            count = 0
            count_lib = 0

            for obs in self.__class__.objects:
                print('%02d. %s' % (
                    count+1, self.__class__.objects[count]))
                count += 1

            if self.__class__.libraries:
                print("\n\n* Check %s:\n" % 
                    ("this library" if len(self.__class__.libraries) == 1
                        else "these libraries"))

                for libs in self.__class__.libraries:
                    print('%02d. %s' % (
                        count_lib+1, self.__class__.libraries[count_lib]))
                    count_lib += 1
            print("\n")

        return{'FINISHED'}

class AMTH_SCENE_OT_list_missing_material_slots_clear(Operator):
    """Clear the list below"""
    bl_idname = "scene.list_missing_material_slots_clear"
    bl_label = "Clear Empty Material Slots List"
    
    def execute(self, context):
        AMTH_SCENE_OT_list_missing_material_slots.objects[:] = []
        print("* Cleared Empty Material Slots List")
        return {'FINISHED'}

class AMTH_SCENE_OT_blender_instance_open(Operator):
    '''Open in a new Blender instance'''
    bl_idname = "scene.blender_instance_open"
    bl_label = "Open Blender Instance"
    filepath = bpy.props.StringProperty()

    def execute(self, context):
        if self.filepath:
            import os.path
            filepath = os.path.normpath(bpy.path.abspath(self.filepath))

            import subprocess
            try:
                subprocess.Popen([bpy.app.binary_path, filepath])
            except:
                print("Error on the new Blender instance")
                import traceback
                traceback.print_exc()

        return{'FINISHED'}

class AMTH_SCENE_PT_scene_debug(Panel):
    '''Scene Debug'''
    bl_label = 'Scene Debug'
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="RADIO")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        objects =  bpy.data.objects
        ob_act = context.active_object
        images = bpy.data.images
        lamps = bpy.data.lamps
        images_missing = []
        list_missing_images = scene.amaranth_debug_scene_list_missing_images
        materials = AMTH_SCENE_OT_cycles_shader_list_nodes.materials
        materials_count = len(AMTH_SCENE_OT_cycles_shader_list_nodes.materials)
        missing_material_slots_obs = AMTH_SCENE_OT_list_missing_material_slots.objects
        missing_material_slots_count = len(AMTH_SCENE_OT_list_missing_material_slots.objects)
        missing_material_slots_lib = AMTH_SCENE_OT_list_missing_material_slots.libraries
        engine = scene.render.engine

        # List Missing Images
        box = layout.box()
        row = box.row(align=True)
        split = row.split()
        col = split.column()

        if images:
            import os.path

            for im in images:
                if im.type not in ['UV_TEST', 'RENDER_RESULT', 'COMPOSITING']: 
                    if not os.path.exists(bpy.path.abspath(im.filepath, library=im.library)):
                        images_missing.append(["%s%s [%s]%s" % (
                            '[L] ' if im.library else '',
                            im.name, im.users,
                            ' [F]' if im.use_fake_user else ''),
                            im.filepath if im.filepath else 'No Filepath',
                            im.library.filepath if im.library else ''])

            if images_missing:
                row = col.row(align=True)
                row.alignment = 'LEFT'
                row.prop(scene, 'amaranth_debug_scene_list_missing_images',
                            icon="%s" % 'TRIA_DOWN' if list_missing_images else 'TRIA_RIGHT',
                            emboss=False)

                split = split.split()
                col = split.column()

                col.label(text="%s missing %s" % (
                             str(len(images_missing)),
                             'image' if len(images_missing) == 1 else 'images'),
                             icon="ERROR")

                if list_missing_images:
                    col = box.column(align=True)
                    for mis in images_missing:
                        col.label(text=mis[0],
                         icon="IMAGE_DATA")
                        col.label(text=mis[1], icon="LIBRARY_DATA_DIRECT")
                        if mis[2]:
                            row = col.row(align=True)
                            row.alignment = "LEFT"
                            row.operator(AMTH_SCENE_OT_blender_instance_open.bl_idname,
                                         text=mis[2],
                                         icon="LINK_BLEND",
                                         emboss=False).filepath=mis[2]
                        col.separator()
            else:
                row = col.row(align=True)
                row.alignment = 'LEFT'
                row.label(text="Great! No missing images", icon="RIGHTARROW_THIN")

                split = split.split()
                col = split.column()

                col.label(text="%s %s loading correctly" % (
                             str(len(images)),
                             'image' if len(images) == 1 else 'images'),
                             icon="IMAGE_DATA")
        else:
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="No images loaded yet", icon="RIGHTARROW_THIN")

        # List Cycles Materials by Shader
        if cycles_exists and engine == 'CYCLES':
            box = layout.box()
            split = box.split()
            col = split.column(align=True)
            col.prop(scene, 'amaranth_cycles_node_types',
                icon="MATERIAL")

            row = split.row(align=True)
            row.operator(AMTH_SCENE_OT_cycles_shader_list_nodes.bl_idname,
                            icon="SORTSIZE",
                            text="List Materials Using Shader")
            if materials_count != 0: 
                row.operator(AMTH_SCENE_OT_cycles_shader_list_nodes_clear.bl_idname,
                                icon="X", text="")
            col.separator()

            try:
                materials
            except NameError:
                pass
            else:
                if materials_count != 0: 
                    col = box.column(align=True)
                    count = 0
                    col.label(text="%s %s found" % (materials_count,
                        'material' if materials_count == 1 else 'materials'), icon="INFO")
                    for mat in materials:
                        count += 1
                        col.label(text='%s' % (materials[count-1]), icon="MATERIAL")

        # List Missing Node Trees
        box = layout.box()
        row = box.row(align=True)
        split = row.split()
        col = split.column(align=True)

        split = col.split()
        split.label(text="Node Links")
        split.operator(AMTH_SCENE_OT_list_missing_node_links.bl_idname,
                        icon="NODETREE")

        if AMTH_SCENE_OT_list_missing_node_links.count_groups != 0 or \
            AMTH_SCENE_OT_list_missing_node_links.count_images != 0 or \
            AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked != 0:
            col.label(text="Warning! Check Console", icon="ERROR")

        if AMTH_SCENE_OT_list_missing_node_links.count_groups != 0:
            col.label(text="%s" % ("%s node %s missing link" % (
                     str(AMTH_SCENE_OT_list_missing_node_links.count_groups),
                     "group" if AMTH_SCENE_OT_list_missing_node_links.count_groups == 1 else "groups")),
                     icon="NODETREE")
        if AMTH_SCENE_OT_list_missing_node_links.count_images != 0:
            col.label(text="%s" % ("%s image %s missing link" % (
                     str(AMTH_SCENE_OT_list_missing_node_links.count_images),
                     "node" if AMTH_SCENE_OT_list_missing_node_links.count_images == 1 else "nodes")),
                     icon="IMAGE_DATA")

        if AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked != 0:
            col.label(text="%s" % ("%s image %s with no output conected" % (
                     str(AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked),
                     "node" if AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked == 1 else "nodes")),
                     icon="NODE")

        # List Empty Materials Slots
        box = layout.box()
        split = box.split()
        col = split.column(align=True)
        col.label(text="Material Slots")

        row = split.row(align=True)
        row.operator(AMTH_SCENE_OT_list_missing_material_slots.bl_idname,
                        icon="MATERIAL",
                        text="List Empty Materials Slots")
        if missing_material_slots_count != 0: 
            row.operator(AMTH_SCENE_OT_list_missing_material_slots_clear.bl_idname,
                            icon="X", text="")
        col.separator()

        try:
            missing_material_slots_obs
        except NameError:
            pass
        else:
            if missing_material_slots_count != 0: 
                col = box.column(align=True)
                count = 0
                count_lib = 0
                col.label(text="%s %s with empty material slots found" % (
                    missing_material_slots_count,
                    'object' if missing_material_slots_count == 1 else 'objects'),
                    icon="INFO")

                for obs in missing_material_slots_obs:
                    count += 1

                    row = col.row()
                    row.alignment = 'LEFT'
                    row.label(text='%s' % missing_material_slots_obs[count-1],
                                icon="OBJECT_DATA")

                if missing_material_slots_lib:
                    col.separator()
                    col.label("Check %s:" % (
                        "this library" if
                            len(missing_material_slots_lib) == 1
                                else "these libraries"))
                    
                    for libs in missing_material_slots_lib:
                        count_lib += 1
                        row = col.row(align=True)
                        row.alignment = "LEFT"
                        row.operator(AMTH_SCENE_OT_blender_instance_open.bl_idname,
                                     text=missing_material_slots_lib[count_lib-1],
                                     icon="LINK_BLEND",
                                     emboss=False).filepath=missing_material_slots_lib[count_lib-1]

# // FEATURE: Scene Debug
# FEATURE: Dupli  Group Path
def ui_dupli_group_library_path(self, context):

    ob = context.object

    row = self.layout.row()
    row.alignment = 'LEFT'

    if ob and ob.dupli_group and ob.dupli_group.library:
        lib = ob.dupli_group.library.filepath

        row.operator(AMTH_SCENE_OT_blender_instance_open.bl_idname,
            text="Library: %s" % lib,
            emboss=False,
            icon="LINK_BLEND").filepath=lib

# // FEATURE: Dupli  Group Path
# FEATURE: Color Management Presets
class AMTH_SCENE_MT_color_management_presets(Menu):
    """List of Color Management presets"""
    bl_label = "Color Management Presets"
    preset_subdir = "color"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class AMTH_AddPresetColorManagement(AddPresetBase, Operator):
    """Add or remove a Color Management preset"""
    bl_idname = "scene.color_management_preset_add"
    bl_label = "Add Color Management Preset"
    preset_menu = "AMTH_SCENE_MT_color_management_presets"

    preset_defines = [
        "scene = bpy.context.scene"
    ]

    preset_values = [
        "scene.view_settings.view_transform",
        "scene.display_settings.display_device",
        "scene.view_settings.exposure",
        "scene.view_settings.gamma",
        "scene.view_settings.look",
        "scene.view_settings.use_curve_mapping",
        "scene.sequencer_colorspace_settings.name",
    ]

    preset_subdir = "color"

def ui_color_management_presets(self, context):
    
    layout = self.layout

    row = layout.row(align=True)
    row.menu("AMTH_SCENE_MT_color_management_presets", text=bpy.types.AMTH_SCENE_MT_color_management_presets.bl_label)
    row.operator("scene.color_management_preset_add", text="", icon="ZOOMIN")
    row.operator("scene.color_management_preset_add", text="", icon="ZOOMOUT").remove_active = True
    layout.separator()
# // FEATURE: Color Management Presets

# FEATURE: Sequencer Extra Info
def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return None

def ui_sequencer_extra_info(self, context):

    layout = self.layout
    strip = act_strip(context)

    if strip:
        seq_type = strip.type

        if seq_type and seq_type == 'IMAGE':
            elem = strip.strip_elem_from_frame(context.scene.frame_current)
            if elem:
                layout.label(text="%s %s" % (
                    elem.filename,
                    "[%s]" % (context.scene.frame_current - strip.frame_start)))
# // FEATURE: Sequencer Extra Info

# FEATURE: Normal Node Values, by Lukas Tönne
def normal_vector_get(self):
    return self.outputs['Normal'].default_value

def normal_vector_set(self, values):
    # default_value allows un-normalized values,
    # do this here to prevent awkward results
    values = Vector(values).normalized()
    self.outputs['Normal'].default_value = values

prop_normal_vector = bpy.props.FloatVectorProperty(
                        name="Normal", size=3, subtype='XYZ',
                        min=-1.0, max=1.0, soft_min=-1.0, soft_max=1.0,
                        get=normal_vector_get, set=normal_vector_set
                        )

def act_node(context):
    try:
        return context.active_node
    except AttributeError:
        return None

def ui_node_normal_values(self, context):

    node = act_node(context)

    if act_node:
        if node and node.type == 'NORMAL':
            self.layout.prop(node, "normal_vector", text="")

# // FEATURE: Normal Node Values, by Lukas Tönne

# FEATURE: Object ID for objects inside DupliGroups
class AMTH_OBJECT_OT_id_dupligroup(Operator):
    '''Set the Object ID for objects in the dupli group'''
    bl_idname = "object.amaranth_object_id_duplis"
    bl_label = "Apply Object ID to Duplis"

    clear = False

    @classmethod
    def poll(cls, context):
        return context.active_object.dupli_group

    def execute(self, context):
        self.__class__.clear = False
        ob = context.active_object
        amth_text_exists = amaranth_text_startup(context)
        script_exists = False
        script_intro = "# OB ID: %s" % ob.name
        obdata = "bpy.data.objects['%s']" % ob.name
        script = "%s" % (
            "\nif %(obdata)s and %(obdata)s.dupli_group and %(obdata)s.pass_index != 0: %(obname)s \n"
            "    for dob in %(obdata)s.dupli_group.objects: %(obname)s \n"
            "        dob.pass_index = %(obdata)s.pass_index %(obname)s \n" %
                {'obdata' : obdata, 'obname' : script_intro})

        for txt in bpy.data.texts:
            if txt.name == amth_text.name:
                for li in txt.lines:
                    if script_intro == li.body:
                        script_exists = True
                        continue

        if not script_exists:
            amth_text.write("\n")
            amth_text.write(script_intro)
            amth_text.write(script)

        if ob and ob.dupli_group:
            if ob.pass_index != 0:
                for dob in ob.dupli_group.objects:
                    dob.pass_index = ob.pass_index

        self.report({'INFO'},
            "%s ID: %s to all objects in this Dupli Group" % (
                "Applied" if not script_exists else "Updated",
                ob.pass_index))

        return{'FINISHED'}

class AMTH_OBJECT_OT_id_dupligroup_clear(Operator):
    '''Clear the Object ID from objects in dupli group'''
    bl_idname = "object.amaranth_object_id_duplis_clear"
    bl_label = "Clear Object ID from Duplis"

    @classmethod
    def poll(cls, context):
        return context.active_object.dupli_group

    def execute(self, context):
        context.active_object.pass_index = 0
        AMTH_OBJECT_OT_id_dupligroup.clear = True
        amth_text_exists = amaranth_text_startup(context)
        match_first = "# OB ID: %s" % context.active_object.name

        if amth_text_exists:
            for txt in bpy.data.texts:
                if txt.name == amth_text.name:
                    for li in txt.lines:
                        if match_first in li.body:
                            li.body = ''
                            continue

        self.report({'INFO'}, "Object IDs back to normal")
        return{'FINISHED'}

def ui_object_id_duplis(self, context):

    if context.active_object.dupli_group:
        split = self.layout.split()
        row = split.row(align=True)
        row.enabled = context.active_object.pass_index != 0
        row.operator(
            AMTH_OBJECT_OT_id_dupligroup.bl_idname)
        row.operator(
            AMTH_OBJECT_OT_id_dupligroup_clear.bl_idname,
            icon="X", text="")
        split.separator()

        if AMTH_OBJECT_OT_id_dupligroup.clear:
            self.layout.label(text="Next time you save/reload this file, "
                                        "object IDs will be back to normal",
                              icon="INFO")

# // FEATURE: Object ID for objects inside DupliGroups
# UI: Warning about Z not connected when using EXR
def ui_render_output_z(self, context):

    scene = bpy.context.scene
    image = scene.render.image_settings
    if scene.render.use_compositing and \
        image.file_format == 'OPEN_EXR' and \
        image.use_zbuffer:
        if scene.node_tree and scene.node_tree.nodes:
            for no in scene.node_tree.nodes:
                if no.type == 'COMPOSITE':
                    if not no.inputs['Z'].is_linked:
                        self.layout.label(
                            text="The Z output in node \"%s\" is not connected" % 
                                no.name, icon="ERROR")

# // UI: Warning about Z not connected

# FEATURE: Delete Materials not assigned to any verts
class AMTH_OBJECT_OT_material_remove_unassigned(Operator):
    '''Remove materials not assigned to any vertex'''
    bl_idname = "object.amaranth_object_material_remove_unassigned"
    bl_label = "Remove Unassigned Materials"

    @classmethod
    def poll(cls, context):
        return context.active_object.material_slots

    def execute(self, context):

        scene = context.scene
        act_ob = context.active_object
        count = len(act_ob.material_slots)
        materials_removed = []
        act_ob.active_material_index = 0
        is_visible = True

        if act_ob not in context.visible_objects:
            is_visible = False
            n = -1
            for lay in act_ob.layers:
                n += 1
                if lay:
                    break

            scene.layers[n] = True

        for slot in act_ob.material_slots:
            count -= 1

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            act_ob.active_material_index = count
            bpy.ops.object.material_slot_select()
            
            if act_ob.data.total_vert_sel == 0 or \
                (len(act_ob.material_slots) == 1 and not \
                    act_ob.material_slots[0].material):
                materials_removed.append(
                    "%s" % act_ob.active_material.name if act_ob.active_material else "Empty")
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.material_slot_remove()
            else:
                pass

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        if materials_removed:
            print("\n* Removed %s Unassigned Materials \n" % len(materials_removed))

            count_mr = 0

            for mr in materials_removed:
                count_mr += 1
                print("%0.2d. %s" % (count_mr, materials_removed[count_mr - 1]))

            print("\n")
            self.report({'INFO'}, "Removed %s Unassigned Materials" %
                len(materials_removed))

        if not is_visible:
            scene.layers[n] = False

        return{'FINISHED'}

def ui_material_remove_unassigned(self, context):

    self.layout.operator(
        AMTH_OBJECT_OT_material_remove_unassigned.bl_idname,
        icon="X")

# // FEATURE: Delete Materials not assigned to any verts
# FEATURE: Cycles Samples Percentage
class AMTH_RENDER_OT_cycles_samples_percentage_set(Operator):
    '''Save the current number of samples per shader as final (gets saved in .blend)'''
    bl_idname = "scene.amaranth_cycles_samples_percentage_set"
    bl_label = "Set as Render Samples"

    def execute(self, context):
        cycles = context.scene.cycles
        cycles.use_samples_final = True

        context.scene['amth_cycles_samples_final'] = [
            cycles.diffuse_samples,
            cycles.glossy_samples,
            cycles.transmission_samples,
            cycles.ao_samples,
            cycles.mesh_light_samples,
            cycles.subsurface_samples,
            cycles.volume_samples]

        self.report({'INFO'}, "Render Samples Saved")

        return{'FINISHED'}


class AMTH_RENDER_OT_cycles_samples_percentage(Operator):
    '''Set a percentage of the final render samples'''
    bl_idname = "scene.amaranth_cycles_samples_percentage"
    bl_label = "Set Render Samples Percentage"

    percent = IntProperty(
                name="Percentage",
                description="Percentage to divide render samples by",
                subtype='PERCENTAGE',
                default=0)

    def execute(self, context):
        percent = self.percent
        cycles = context.scene.cycles
        cycles_samples_final = context.scene['amth_cycles_samples_final']

        cycles.use_samples_final = False

        if percent == 100:
            cycles.use_samples_final = True

        cycles.diffuse_samples = int((cycles_samples_final[0] / 100) * percent)
        cycles.glossy_samples = int((cycles_samples_final[1] / 100) * percent)
        cycles.transmission_samples = int((cycles_samples_final[2] / 100) * percent)
        cycles.ao_samples = int((cycles_samples_final[3] / 100) * percent)
        cycles.mesh_light_samples = int((cycles_samples_final[4] / 100) * percent)
        cycles.subsurface_samples = int((cycles_samples_final[5] / 100) * percent)
        cycles.volume_samples = int((cycles_samples_final[6] / 100) * percent)

        return{'FINISHED'}

# //FEATURE: Cycles Samples Percentage
# FEATURE: Jump forward/backward every N frames
class AMTH_SCREEN_OT_frame_jump(Operator):
    '''Jump a number of frames forward/backwards'''
    bl_idname = "screen.amaranth_frame_jump"
    bl_label = "Jump Frames"

    forward = BoolProperty(default=True)

    def execute(self, context):
        scene = context.scene
        preferences = context.user_preferences.addons[__name__].preferences

        if preferences.use_framerate:
            framedelta = scene.render.fps
        else:
            framedelta = preferences.frames_jump
        if self.forward:
            scene.frame_current = scene.frame_current + framedelta
        else:
            scene.frame_current = scene.frame_current - framedelta

        return{'FINISHED'}

def ui_userpreferences_edit(self, context):
    preferences = context.user_preferences.addons[__name__].preferences

    col = self.layout.column()
    split = col.split(percentage=0.21)
    split.prop(preferences, "frames_jump",
               text="Frames to Jump")

# // FEATURE: Jump forward/backward every N frames
# FEATURE: Set Layers to Render
class AMTH_SCENE_OT_layers_render_save(Operator):
    '''Save the current scene layers as those that should be enabled for final renders'''
    bl_idname = "scene.amaranth_layers_render_save"
    bl_label = "Save as Layers for Render"

    def execute(self, context):
        which = []
        n = -1

        for l in context.scene.layers:
            n += 1
            if l:
                which.append(n)

        context.scene['amth_layers_for_render'] = which
        self.report({'INFO'}, "Layers for Render Saved")

        return{'FINISHED'}

class AMTH_SCENE_OT_layers_render_view(Operator):
    '''Enable the scene layers that should be active for final renders'''
    bl_idname = "scene.amaranth_layers_render_view"
    bl_label = "View Layers for Render"

    def execute(self, context):
        scene = context.scene
        layers_render = scene['amth_layers_for_render']

        for window in bpy.context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    override = {'window': window, 'screen': screen, 'scene': scene, 
                                'area': area, 'region': area.regions[4],
                                'blend_data': context.blend_data}

                    if layers_render:
                        bpy.ops.view3d.layers(override, nr=layers_render[0]+1, extend=False, toggle=False)

                        for n in layers_render:
                            context.scene.layers[n] = True
                    else:
                        bpy.ops.view3d.layers(override, nr=1, extend=False, toggle=False)
                        self.report({'INFO'}, "No layers set for render")

                    break

        return{'FINISHED'}

class AMTH_SCENE_OT_layers_render_set_individual(Operator):
    '''Whether this layer should be enabled or not for final renders'''
    bl_idname = "scene.amaranth_layers_render_set_individual"
    bl_label = "Set This Layer for Render"

    toggle = BoolProperty()
    number = IntProperty()

    def execute(self, context):
        toggle = self.toggle
        number = self.number

        new_layers = []

        for la in context.scene['amth_layers_for_render']:
            new_layers.append(la)

        if len(context.scene['amth_layers_for_render']) and number in new_layers:
            new_layers.remove(number)
        else:
            new_layers.append(number)

        # Remove Duplicates
        new_layers = list(set(new_layers))
        context.scene['amth_layers_for_render'] = new_layers

        bpy.ops.scene.amaranth_layers_render_view()

        return{'FINISHED'}

class AMTH_SCENE_OT_layers_render_clear(Operator):
    '''Clear layers for render'''
    bl_idname = "scene.amaranth_layers_render_clear"
    bl_label = "Clear Layers for Render"

    def execute(self, context):

        if context.scene.get('amth_layers_for_render'):
            context.scene['amth_layers_for_render'] = []

        return{'FINISHED'}

def ui_layers_for_render(self, context):

    preferences = context.user_preferences.addons[__name__].preferences

    if preferences.use_layers_for_render:
        lfr_available = context.scene.get('amth_layers_for_render')
        if lfr_available:
            lfr = context.scene['amth_layers_for_render']

        layout = self.layout
        layout.label("Layers for Rendering:")
        split = layout.split()
        col = split.column(align=True)
        row = col.row(align=True)
        row.operator(
            AMTH_SCENE_OT_layers_render_save.bl_idname,
            text="Replace Layers" if lfr_available else "Save Current Layers for Render",
            icon="FILE_REFRESH" if lfr_available else 'LAYER_USED')

        if lfr_available:
            row.operator(
                AMTH_SCENE_OT_layers_render_clear.bl_idname,
                icon='X', text="")
            col = col.column(align=True)
            col.enabled = True if lfr_available else False
            col.operator(
                AMTH_SCENE_OT_layers_render_view.bl_idname,
                icon="RESTRICT_VIEW_OFF")

            split = split.split()
            col = split.column(align=True)
            row = col.row(align=True)

            for n in range(0,5):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname, text="",
                    icon='LAYER_ACTIVE' if n in lfr else 'BLANK1').number = n
            row = col.row(align=True)
            for n in range(10,15):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname, text="",
                    icon='LAYER_ACTIVE' if n in lfr else 'BLANK1').number = n

            split = split.split()
            col = split.column(align=True)
            row = col.row(align=True)

            for n in range(5,10):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname, text="",
                    icon='LAYER_ACTIVE' if n in lfr else 'BLANK1').number = n
            row = col.row(align=True)
            for n in range(15,20):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname, text="",
                    icon='LAYER_ACTIVE' if n in lfr else 'BLANK1').number = n

def ui_layers_for_render_header(self, context):

    preferences = context.user_preferences.addons[__name__].preferences

    if preferences.use_layers_for_render:
        if context.scene.get('amth_layers_for_render'):
            self.layout.operator(
                AMTH_SCENE_OT_layers_render_view.bl_idname,
                text="", icon="IMGDISPLAY")

# // FEATURE: Set Layers to Render
# FEATURE: Lighters Corner
class AMTH_LightersCorner(bpy.types.Panel):
    """The Lighters Panel"""
    bl_label = "Lighter's Corner"
    bl_idname = "AMTH_SCENE_PT_lighters_corner"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        any_lamps = False
        for ob in bpy.data.objects:
            if ob.type == 'LAMP' or cycles_is_emission(context, ob):
                any_lamps = True
            else:
                pass
        return any_lamps

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="LAMP_SUN")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        objects =  bpy.data.objects
        ob_act = context.active_object
        lamps = bpy.data.lamps
        list_meshlights = scene.amaranth_lighterscorner_list_meshlights
        engine = scene.render.engine

        if cycles_exists:
            layout.prop(scene, "amaranth_lighterscorner_list_meshlights")

        box = layout.box()
        if lamps:
            if objects:
                row = box.row(align=True)
                split = row.split(percentage=0.45)
                col = split.column()

                col.label(text="Name")

                if engine in ['CYCLES', 'BLENDER_RENDER']:
                    if engine == 'BLENDER_RENDER':
                        split = split.split(percentage=0.7)
                    else:
                        split = split.split(percentage=0.27)
                    col = split.column()
                    col.label(text="Samples")

                if cycles_exists and engine == 'CYCLES':
                    split = split.split(percentage=0.2)
                    col = split.column()
                    col.label(text="Size")

                split = split.split(percentage=1.0)
                col = split.column()
                col.label(text="%sRender Visibility" % 
                    'Rays /' if cycles_exists else '')

                for ob in objects:
                    is_lamp = ob.type == 'LAMP'
                    is_emission = True if cycles_is_emission(context, ob) and list_meshlights else False

                    if ob and is_lamp or is_emission:
                        lamp = ob.data
                        if cycles_exists:
                            clamp = ob.data.cycles
                            visibility = ob.cycles_visibility

                        row = box.row(align=True)
                        split = row.split(percentage=1.0)
                        col = split.column()
                        row = col.row(align=True)
                        col.active = ob == ob_act
                        row.label(icon="%s" % ('LAMP_%s' % ob.data.type if is_lamp else 'MESH_GRID'))
                        split = row.split(percentage=.45)
                        col = split.column()
                        row = col.row(align=True)
                        row.alignment = 'LEFT'
                        row.active = True
                        row.operator(AMTH_SCENE_OT_amaranth_object_select.bl_idname,
                                    text='%s %s%s' % (
                                        " [L] " if ob.library else "",
                                        ob.name,
                                        "" if ob.name in context.scene.objects else " [Not in Scene]"),
                                    emboss=False).object = ob.name
                        if ob.library:
                            row = col.row(align=True)
                            row.alignment = "LEFT"
                            row.operator(AMTH_SCENE_OT_blender_instance_open.bl_idname,
                                         text=ob.library.filepath,
                                         icon="LINK_BLEND",
                                         emboss=False).filepath=ob.library.filepath

                        if cycles_exists and engine == 'CYCLES':
                            split = split.split(percentage=0.25)
                            col = split.column()
                            if is_lamp:
                                if scene.cycles.progressive == 'BRANCHED_PATH':
                                    col.prop(clamp, "samples", text="")
                                if scene.cycles.progressive == 'PATH':
                                   col.label(text="N/A")
                            else:
                              col.label(text="N/A")

                        if engine == 'BLENDER_RENDER':
                            split = split.split(percentage=0.7)
                            col = split.column()
                            if is_lamp:
                                if lamp.type == 'HEMI':
                                    col.label(text="Not Available")
                                elif lamp.type == 'AREA' and lamp.shadow_method == 'RAY_SHADOW':
                                    row = col.row(align=True)
                                    row.prop(lamp, "shadow_ray_samples_x", text="X")
                                    if lamp.shape == 'RECTANGLE':
                                        row.prop(lamp, "shadow_ray_samples_y", text="Y")
                                elif lamp.shadow_method == 'RAY_SHADOW':
                                    col.prop(lamp, "shadow_ray_samples", text="Ray Samples")
                                elif lamp.shadow_method == 'BUFFER_SHADOW':
                                    col.prop(lamp, "shadow_buffer_samples", text="Buffer Samples")
                                else:
                                    col.label(text="No Shadow")
                            else:
                              col.label(text="N/A")

                        if cycles_exists and engine == 'CYCLES':
                            split = split.split(percentage=0.2)
                            col = split.column()
                            if is_lamp:
                                if lamp.type in ['POINT','SUN', 'SPOT']:
                                    col.label(text="%.2f" % lamp.shadow_soft_size)
                                elif lamp.type == 'HEMI':
                                    col.label(text="N/A")
                                elif lamp.type == 'AREA' and lamp.shape == 'RECTANGLE':
                                    col.label(text="%.2fx%.2f" % (lamp.size, lamp.size_y))
                                else:
                                    col.label(text="%.2f" % lamp.size)
                            else:
                              col.label(text="N/A")

                        split = split.split(percentage=1.0)
                        col = split.column()
                        row = col.row(align=True)
                        if cycles_exists:
                            row.prop(visibility, "camera", text="")
                            row.prop(visibility, "diffuse", text="")
                            row.prop(visibility, "glossy", text="")
                            row.prop(visibility, "shadow", text="")
                            row.separator()
                        row.prop(ob, "hide", text="", emboss=False)
                        row.prop(ob, "hide_render", text="", emboss=False)
        else:
            box.label(text="No Lamps", icon="LAMP_DATA")

# FEATURE: Jump to frame in-between next and previous keyframe
class AMTH_SCREEN_OT_keyframe_jump_inbetween(Operator):
    '''Jump to half in-between keyframes'''
    bl_idname = "screen.amth_keyframe_jump_inbetween"
    bl_label = "Jump to Keyframe In-between"

    backwards = BoolProperty()

    def execute(self, context):
        back = self.backwards

        scene = context.scene
        ob = bpy.context.object
        frame_start = scene.frame_start
        frame_end = scene.frame_end

        if not context.scene.get('amth_keyframes_jump'):
            context.scene['amth_keyframes_jump'] = []

        keyframes_list = context.scene['amth_keyframes_jump']

        for f in range(frame_start, frame_end):
            if ob.is_keyframe(f):
                 keyframes_list = list(keyframes_list)
                 keyframes_list.append(f)

        if keyframes_list:
            i = 0
            keyframes_list_half = []

            for item in keyframes_list:
                try:
                    keyframes_list_half.append(int((keyframes_list[i] + keyframes_list[i+1]) / 2))
                    i += 1
                except:
                    pass

            if len(keyframes_list_half) > 1:
                if back:
                    if scene.frame_current == keyframes_list_half[::-1][-1] or \
                        scene.frame_current < keyframes_list_half[::-1][-1]:
                        self.report({'INFO'}, "No keyframes behind")
                    else:
                        for i in keyframes_list_half[::-1]:
                            if scene.frame_current > i:
                                scene.frame_current = i
                                break
                else:
                    if scene.frame_current == keyframes_list_half[-1] or \
                        scene.frame_current > keyframes_list_half[-1]:
                        self.report({'INFO'}, "No keyframes ahead")
                    else:
                        for i in keyframes_list_half:
                            if scene.frame_current < i:
                                scene.frame_current = i
                                break
            else:
                self.report({'INFO'}, "Object has only 1 keyframe")
        else:
            self.report({'INFO'}, "Object has no keyframes")

        return{'FINISHED'}
# // FEATURE: Jump to frame in-between next and previous keyframe
# FEATURE: Toggle Wire Display
class AMTH_OBJECT_OT_wire_toggle(Operator):
    '''Turn on/off wire display on mesh objects'''
    bl_idname = "object.amth_wire_toggle"
    bl_label = "Display Wireframe"
    bl_options = {'REGISTER', 'UNDO'}

    clear = BoolProperty(
        default=False, name="Clear Wireframe",
        description="Clear Wireframe Display")

    def execute(self, context):

        scene = context.scene
        is_all_scenes = scene.amth_wire_toggle_scene_all
        is_selected = scene.amth_wire_toggle_is_selected
        is_all_edges = scene.amth_wire_toggle_edges_all
        is_optimal = scene.amth_wire_toggle_optimal
        clear = self.clear

        if is_all_scenes:
            which = bpy.data.objects
        elif is_selected:
            if not context.selected_objects:
                self.report({'INFO'}, "No selected objects")
            which = context.selected_objects
        else:
            which = scene.objects

        if which:
            for ob in which:
                if ob and ob.type in {
                    'MESH', 'EMPTY', 'CURVE',
                    'META','SURFACE','FONT'}:

                    ob.show_wire = False if clear else True
                    ob.show_all_edges = is_all_edges

                    for mo in ob.modifiers:
                        if mo and mo.type == 'SUBSURF':
                            mo.show_only_control_edges = is_optimal

        return{'FINISHED'}

def ui_object_wire_toggle(self, context):

    scene = context.scene

    self.layout.separator()
    col = self.layout.column(align=True)
    row = col.row(align=True)
    row.operator(AMTH_OBJECT_OT_wire_toggle.bl_idname,
        icon='MOD_WIREFRAME').clear = False
    row.operator(AMTH_OBJECT_OT_wire_toggle.bl_idname,
        icon='X', text="").clear = True
    col.separator()
    row = col.row(align=True)
    row.prop(scene, "amth_wire_toggle_edges_all")
    row.prop(scene, "amth_wire_toggle_optimal")
    row = col.row(align=True)
    sub = row.row(align=True)
    sub.active = not scene.amth_wire_toggle_scene_all
    sub.prop(scene, "amth_wire_toggle_is_selected")
    sub = row.row(align=True)
    sub.active = not scene.amth_wire_toggle_is_selected
    sub.prop(scene, "amth_wire_toggle_scene_all")

# //FEATURE: Toggle Wire Display
# FEATURE: Add Meshlight
class AMTH_OBJECT_OT_meshlight_add(bpy.types.Operator):
    """Add a light emitting mesh"""
    bl_idname = "object.meshlight_add"
    bl_label = "Add Meshlight"
    bl_options = {'REGISTER', 'UNDO'}

    single_sided = BoolProperty(
            name="Single Sided",
            default=True,
            description="Only emit light on one side",
            )

    visible = BoolProperty(
            name="Visible on Camera",
            default=False,
            description="Show the meshlight on Cycles preview",
            )

    size = FloatProperty(
            name="Size",
            description="Meshlight size",
            min=0.01, max=100.0,
            default=1.0,
            )

    strength = FloatProperty(
            name="Strength",
            min=0.01, max=100000.0,
            default=1.5,
            step=0.25,
            )

    temperature = FloatProperty(
            name="Temperature",
            min=800, max=12000.0,
            default=5500.0,
            step=800.0,
            )

    rotation = FloatVectorProperty(
            name="Rotation",
            subtype='EULER',
            )

    def execute(self, context):
        scene = context.scene
        exists = False
        number = 1

        for obs in bpy.data.objects:
            if obs.name.startswith("light_meshlight"):
                number +=1

        meshlight_name = 'light_meshlight_%.2d' % number

        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=4, y_subdivisions=4,
            rotation=self.rotation, radius=self.size)

        bpy.context.object.name = meshlight_name
        meshlight = scene.objects[meshlight_name]
        meshlight.show_wire = True
        meshlight.show_all_edges = True

        material = bpy.data.materials.get(meshlight_name)

        if not material:
            material = bpy.data.materials.new(meshlight_name)

        bpy.ops.object.material_slot_add()
        meshlight.active_material = material

        material.use_nodes = True
        material.diffuse_color = (1, 0.5, 0)
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # clear default nodes to start nice fresh
        for no in nodes:
            nodes.remove(no)

        if self.single_sided:
            geometry = nodes.new(type="ShaderNodeNewGeometry")

            transparency = nodes.new(type="ShaderNodeBsdfTransparent")
            transparency.inputs[0].default_value = (1,1,1,1)
            transparency.location = geometry.location
            transparency.location += Vector((0.0, -55.0))

            emission = nodes.new(type="ShaderNodeEmission")
            emission.inputs['Strength'].default_value = self.strength
            emission.location = transparency.location
            emission.location += Vector((0.0, -80.0))
            emission.inputs[0].show_expanded = True # so it shows slider on properties editor

            blackbody = nodes.new(type="ShaderNodeBlackbody")
            blackbody.inputs['Temperature'].default_value = self.temperature
            blackbody.location = emission.location
            blackbody.location += Vector((-180.0, 0.0))

            mix = nodes.new(type="ShaderNodeMixShader")
            mix.location = geometry.location
            mix.location += Vector((180.0, 0.0))
            mix.inputs[2].show_expanded = True

            output = nodes.new(type="ShaderNodeOutputMaterial")
            output.inputs[1].hide = True
            output.inputs[2].hide = True
            output.location = mix.location
            output.location += Vector((180.0, 0.0))

            # Make links
            links.new(geometry.outputs['Backfacing'], mix.inputs['Fac'])
            links.new(transparency.outputs['BSDF'], mix.inputs[1])
            links.new(emission.outputs['Emission'], mix.inputs[2])
            links.new(blackbody.outputs['Color'], emission.inputs['Color'])
            links.new(mix.outputs['Shader'], output.inputs['Surface'])

            for sockets in geometry.outputs:
                sockets.hide = True
        else:
            emission = nodes.new(type="ShaderNodeEmission")
            emission.inputs['Strength'].default_value = self.strength
            emission.inputs[0].show_expanded = True

            blackbody = nodes.new(type="ShaderNodeBlackbody")
            blackbody.inputs['Temperature'].default_value = self.temperature
            blackbody.location = emission.location
            blackbody.location += Vector((-180.0, 0.0))

            output = nodes.new(type="ShaderNodeOutputMaterial")
            output.inputs[1].hide = True
            output.inputs[2].hide = True
            output.location = emission.location
            output.location += Vector((180.0, 0.0))

            links.new(blackbody.outputs['Color'], emission.inputs['Color'])
            links.new(emission.outputs['Emission'], output.inputs['Surface'])

        material.cycles.sample_as_light = True
        meshlight.cycles_visibility.shadow = False
        meshlight.cycles_visibility.camera = self.visible

        return {'FINISHED'}

def ui_menu_lamps_add(self, context):
    if cycles_exists and context.scene.render.engine == 'CYCLES':
        self.layout.separator()
        self.layout.operator(
            AMTH_OBJECT_OT_meshlight_add.bl_idname,
            icon="LAMP_AREA", text="Meshlight")

# //FEATURE: Add Meshlight: Single Sided

classes = (AMTH_SCENE_MT_color_management_presets,
           AMTH_AddPresetColorManagement,
           AMTH_LightersCorner,
           AMTH_SCENE_PT_scene_debug,
           AMTH_SCENE_OT_refresh,
           AMTH_SCENE_OT_cycles_shader_list_nodes,
           AMTH_SCENE_OT_cycles_shader_list_nodes_clear,
           AMTH_SCENE_OT_amaranth_object_select,
           AMTH_SCENE_OT_list_missing_node_links,
           AMTH_SCENE_OT_list_missing_material_slots,
           AMTH_SCENE_OT_list_missing_material_slots_clear,
           AMTH_SCENE_OT_blender_instance_open,
           AMTH_SCENE_OT_layers_render_save,
           AMTH_SCENE_OT_layers_render_view,
           AMTH_SCENE_OT_layers_render_set_individual,
           AMTH_SCENE_OT_layers_render_clear,
           AMTH_WM_OT_save_reload,
           AMTH_MESH_OT_find_asymmetric,
           AMTH_MESH_OT_make_symmetric,
           AMTH_NODE_OT_AddTemplateVignette,
           AMTH_NODE_OT_AddTemplateVectorBlur,
           AMTH_NODE_MT_amaranth_templates,
           AMTH_FILE_OT_directory_current_blend,
           AMTH_FILE_OT_directory_go_to,
           AMTH_NODE_PT_indices,
           AMTH_NODE_PT_simplify,
           AMTH_NODE_OT_toggle_mute,
           AMTH_NODE_OT_show_active_node_image,
           AMTH_VIEW3D_OT_render_border_camera,
           AMTH_VIEW3D_OT_show_only_render,
           AMTH_OBJECT_OT_select_meshlights,
           AMTH_OBJECT_OT_id_dupligroup,
           AMTH_OBJECT_OT_id_dupligroup_clear,
           AMTH_OBJECT_OT_material_remove_unassigned,
           AMTH_OBJECT_OT_wire_toggle,
           AMTH_OBJECT_OT_meshlight_add,
           AMTH_POSE_OT_paths_clear_all,
           AMTH_POSE_OT_paths_frame_match,
           AMTH_RENDER_OT_cycles_samples_percentage,
           AMTH_RENDER_OT_cycles_samples_percentage_set,
           AMTH_FILE_PT_libraries,
           AMTH_SCREEN_OT_frame_jump,
           AMTH_SCREEN_OT_keyframe_jump_inbetween)

addon_keymaps = []

def register():

    bpy.utils.register_class(AmaranthToolsetPreferences)

    # UI: Register the panel
    init_properties()
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_object_specials.append(button_refresh)
    bpy.types.VIEW3D_MT_object_specials.append(button_render_border_camera)
    bpy.types.VIEW3D_MT_object_specials.append(button_camera_passepartout)
    bpy.types.VIEW3D_MT_object_specials.append(button_frame_current)
    bpy.types.VIEW3D_MT_pose_specials.append(button_frame_current)
    bpy.types.VIEW3D_MT_select_object.append(button_select_meshlights)
    bpy.types.VIEW3D_HT_header.append(ui_layers_for_render_header)

    bpy.types.INFO_MT_file.append(button_save_reload)
    bpy.types.INFO_HT_header.append(stats_scene)

    bpy.types.TIME_HT_header.append(label_timeline_extra_info)

    bpy.types.NODE_HT_header.append(node_templates_pulldown)
    bpy.types.NODE_HT_header.append(node_stats)
    bpy.types.NODE_HT_header.append(node_shader_extra)
    bpy.types.NODE_PT_active_node_properties.append(ui_node_normal_values)

    if check_cycles_exists():
        bpy.types.CyclesRender_PT_sampling.append(render_cycles_scene_samples)
        bpy.types.CyclesScene_PT_simplify.append(unsimplify_ui)

    bpy.types.FILEBROWSER_HT_header.append(button_directory_current_blend)

    bpy.types.SCENE_PT_simplify.append(unsimplify_ui)

    bpy.types.DATA_PT_display.append(pose_motion_paths_ui)

    bpy.types.RENDER_PT_dimensions.append(render_final_resolution_ui)
    bpy.types.RENDER_PT_output.append(ui_render_output_z)

    bpy.types.SCENE_PT_color_management.prepend(ui_color_management_presets)

    bpy.types.SEQUENCER_HT_header.append(ui_sequencer_extra_info)

    bpy.types.OBJECT_PT_duplication.append(ui_dupli_group_library_path)

    bpy.types.OBJECT_PT_relations.append(ui_object_id_duplis)

    bpy.types.MATERIAL_MT_specials.append(ui_material_remove_unassigned)

    bpy.types.USERPREF_PT_edit.append(ui_userpreferences_edit)

    bpy.types.RENDERLAYER_PT_layers.append(ui_layers_for_render)

    bpy.types.VIEW3D_PT_view3d_display.append(ui_object_wire_toggle)

    bpy.types.INFO_MT_mesh_add.append(ui_menu_lamps_add)

    bpy.app.handlers.render_pre.append(unsimplify_render_pre)
    bpy.app.handlers.render_post.append(unsimplify_render_post)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        km.keymap_items.new("node.show_active_node_image", 'ACTIONMOUSE', 'DOUBLE_CLICK')

        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu', 'W', 'PRESS')
        kmi.properties.name = "AMTH_NODE_MT_amaranth_templates"

        km = kc.keymaps.new(name='Window')
        kmi = km.keymap_items.new('scene.refresh', 'F5', 'PRESS', shift=False, ctrl=False)
        kmi = km.keymap_items.new('wm.save_reload', 'W', 'PRESS', shift=True, ctrl=True)

        km = kc.keymaps.new(name='Frames')
        kmi = km.keymap_items.new('screen.amaranth_frame_jump', 'UP_ARROW', 'PRESS', shift=True)
        kmi.properties.forward = True
        kmi = km.keymap_items.new('screen.amaranth_frame_jump', 'DOWN_ARROW', 'PRESS', shift=True)
        kmi.properties.forward = False

        km = kc.keymaps.new(name='Frames')
        kmi = km.keymap_items.new('screen.amth_keyframe_jump_inbetween', 'UP_ARROW', 'PRESS', shift=True, ctrl=True)
        kmi.properties.backwards = False
        kmi = km.keymap_items.new('screen.amth_keyframe_jump_inbetween', 'DOWN_ARROW', 'PRESS', shift=True, ctrl=True)
        kmi.properties.backwards = True

        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('view3d.show_only_render', 'Z', 'PRESS', shift=True, alt=True)

        km = kc.keymaps.new(name='Graph Editor', space_type='GRAPH_EDITOR')
        kmi = km.keymap_items.new('wm.context_set_enum', 'TAB', 'PRESS', ctrl=True)
        kmi.properties.data_path = 'area.type'
        kmi.properties.value = 'DOPESHEET_EDITOR'

        km = kc.keymaps.new(name='Dopesheet', space_type='DOPESHEET_EDITOR')
        kmi = km.keymap_items.new('wm.context_set_enum', 'TAB', 'PRESS', ctrl=True)
        kmi.properties.data_path = 'area.type'
        kmi.properties.value = 'GRAPH_EDITOR'

        km = kc.keymaps.new(name='Dopesheet', space_type='DOPESHEET_EDITOR')
        kmi = km.keymap_items.new('wm.context_toggle_enum', 'TAB', 'PRESS', shift=True)
        kmi.properties.data_path = 'space_data.mode'
        kmi.properties.value_1 = 'ACTION'
        kmi.properties.value_2 = 'DOPESHEET'

        addon_keymaps.append((km, kmi))

def unregister():

    bpy.utils.unregister_class(AmaranthToolsetPreferences)

    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_object_specials.remove(button_refresh)
    bpy.types.VIEW3D_MT_object_specials.remove(button_render_border_camera)
    bpy.types.VIEW3D_MT_object_specials.remove(button_camera_passepartout)
    bpy.types.VIEW3D_MT_object_specials.remove(button_frame_current)
    bpy.types.VIEW3D_MT_pose_specials.remove(button_frame_current)
    bpy.types.VIEW3D_MT_select_object.remove(button_select_meshlights)
    bpy.types.VIEW3D_HT_header.remove(ui_layers_for_render_header)

    bpy.types.INFO_MT_file.remove(button_save_reload)
    bpy.types.INFO_HT_header.remove(stats_scene)

    bpy.types.TIME_HT_header.remove(label_timeline_extra_info)

    bpy.types.NODE_HT_header.remove(node_templates_pulldown)
    bpy.types.NODE_HT_header.remove(node_stats)
    bpy.types.NODE_HT_header.remove(node_shader_extra)
    bpy.types.NODE_PT_active_node_properties.remove(ui_node_normal_values)

    if check_cycles_exists():
        bpy.types.CyclesRender_PT_sampling.remove(render_cycles_scene_samples)
        bpy.types.CyclesScene_PT_simplify.remove(unsimplify_ui)

    bpy.types.FILEBROWSER_HT_header.remove(button_directory_current_blend)

    bpy.types.SCENE_PT_simplify.remove(unsimplify_ui)

    bpy.types.DATA_PT_display.remove(pose_motion_paths_ui)

    bpy.types.RENDER_PT_dimensions.remove(render_final_resolution_ui)
    bpy.types.RENDER_PT_output.remove(ui_render_output_z)

    bpy.types.SCENE_PT_color_management.remove(ui_color_management_presets)

    bpy.types.SEQUENCER_HT_header.remove(ui_sequencer_extra_info)

    bpy.types.OBJECT_PT_duplication.remove(ui_dupli_group_library_path)

    bpy.types.OBJECT_PT_relations.remove(ui_object_id_duplis)

    bpy.types.MATERIAL_MT_specials.remove(ui_material_remove_unassigned)

    bpy.types.USERPREF_PT_edit.remove(ui_userpreferences_edit)

    bpy.types.RENDERLAYER_PT_layers.remove(ui_layers_for_render)

    bpy.types.VIEW3D_PT_view3d_display.remove(ui_object_wire_toggle)

    bpy.types.INFO_MT_mesh_add.remove(ui_menu_lamps_add)

    bpy.app.handlers.render_pre.remove(unsimplify_render_pre)
    bpy.app.handlers.render_post.remove(unsimplify_render_post)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    clear_properties()

if __name__ == "__main__":
    register()

