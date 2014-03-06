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
    "author": "Pablo Vazquez, Bassam Kurdali, Sergey Sharybin",
    "version": (0, 8, 1),
    "blender": (2, 70),
    "location": "Everywhere!",
    "description": "A collection of tools and settings to improve productivity",
    "warning": "",
    "wiki_url": "http://pablovazquez.org/amaranth",
    "tracker_url": "",
    "category": "Scene"}


import bpy
import bmesh
from bpy.types import Operator, AddonPreferences, Panel, Menu
from bpy.props import BoolProperty
from mathutils import Vector
from bpy.app.handlers import persistent
from bl_operators.presets import AddPresetBase

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
        sub.label(text="") # General
        sub.label(
            text="Quickly save and reload the current file (no warning!). "
                 "File menu or Ctrl+Shift+W")
        sub.label(
            text="SMPTE Timecode and frames left/ahead on Timeline's header")
        sub.label(
            text="Display extra statistics for Scenes, Cameras, and Meshlights (Cycles)")

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

    test_items = [
        ("ALL", "All Types", "", 0),
        ("BLUR", "Blur", "", 1),
        ("BOKEHBLUR", "Bokeh Blur", "", 2),
        ("VECBLUR", "Vector Blur", "", 3),
        ("DEFOCUS", "Defocus", "", 4),
        ("R_LAYERS", "Render Layer", "", 5)
        ]

    nodes_compo.types = bpy.props.EnumProperty(
        items=test_items, name = "Types")

    nodes_compo.toggle_mute = BoolProperty(default=False)
    node.status = BoolProperty(default=False)

    # Scene Debug
    # Cycles Node Types
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
        ]

    scene.amaranth_cycles_node_types = bpy.props.EnumProperty(
        items=cycles_shader_node_types, name = "Shader")

    scene.amaranth_debug_scene_list_lamps = BoolProperty(
        default=False,
        name="Lamps List",
        description="Display a list of all the lamps")

    scene.amaranth_debug_scene_list_missing_images = BoolProperty(
        default=False,
        name="List Missing Images",
        description="Display a list of all the missing images")

    global materials


def clear_properties():
    props = (
        "use_unsimplify_render",
        "simplify_status",
        "use_matching_indices",
        "use_simplify_nodes_vector",
        "status"
    )
    
    wm = bpy.context.window_manager
    for p in props:
        if p in wm:
            del wm[p]

# FEATURE: Refresh Scene!
class SCENE_OT_refresh(Operator):
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
            SCENE_OT_refresh.bl_idname,
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

class WM_OT_save_reload(Operator):
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
            WM_OT_save_reload.bl_idname,
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
class FILE_OT_directory_current_blend(Operator):
    """Go to the directory of the currently open blend file"""
    bl_idname = "file.directory_current_blend"
    bl_label = "Current Blend's Folder"

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir='//')
        return {'FINISHED'}

def button_directory_current_blend(self, context):

    if bpy.data.filepath:
        self.layout.operator(
            FILE_OT_directory_current_blend.bl_idname,
            text="Current Blend's Folder",
            icon='APPEND_BLEND')
# // FEATURE: Directory Current Blend

# FEATURE: Libraries panel on file browser
class FILE_PT_libraries(Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'CHANNELS'
    bl_label = "Libraries"

    def draw(self, context):
        layout = self.layout

        libs = bpy.data.libraries
        libslist = []

        # Build the list of folders from libraries
        import os

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
            for filepath in libslist:
                if filepath != '//':
                    row = box.row()
                    row.alignment = 'LEFT'
                    props = row.operator(
                        FILE_OT_directory_go_to.bl_idname,
                        text=filepath, icon="BOOKMARKS",
                        emboss=False)
                    props.filepath = filepath
        else:
            box.label(text='No libraries loaded')

class FILE_OT_directory_go_to(Operator):
    """Go to this library's directory"""
    bl_idname = "file.directory_go_to"
    bl_label = "Go To"
    
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):

        bpy.ops.file.select_bookmark(dir=self.filepath)
        return {'FINISHED'}
    
# FEATURE: Node Templates
class NODE_OT_AddTemplateVignette(Operator):
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

        if tree.nodes.active:
            blur.location = tree.nodes.active.location
            blur.location += Vector((330.0, -250.0))
        else:
            blur.location += Vector((space.cursor_location[0], space.cursor_location[1]))

        ellipse.location = blur.location
        ellipse.location += Vector((-300.0, 0))

        ramp.location = blur.location
        ramp.location += Vector((175.0, 0))

        overlay.location = ramp.location
        overlay.location += Vector((240.0, 275.0))

        for node in {ellipse, blur, ramp, overlay}:
            node.select = True
            node.show_preview = False

        bpy.ops.node.join()

        frame = ellipse.parent
        frame.label = 'Vignette'
        frame.use_custom_color = True
        frame.color = (0.783538, 0.0241576, 0.0802198)
        
        overlay.parent = None
        overlay.label = 'Vignette Overlay'

    def execute(self, context):
        self._setupNodes(context)

        return {'FINISHED'}

# Node Templates Menu
class NODE_MT_amaranth_templates(Menu):
    bl_idname = 'NODE_MT_amaranth_templates'
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Templates"
    bl_description = "List of Amaranth Templates"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            NODE_OT_AddTemplateVignette.bl_idname,
            text="Vignette",
            icon='COLOR')

def node_templates_pulldown(self, context):

    if context.space_data.tree_type == 'CompositorNodeTree':
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        row.menu("NODE_MT_amaranth_templates",
            icon="RADIO")
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
class NODE_PT_simplify(Panel):
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
            layout.operator(NODE_OT_toggle_mute.bl_idname,
                text="Turn On" if node_tree.toggle_mute else "Turn Off",
                icon='RESTRICT_VIEW_OFF' if node_tree.toggle_mute else 'RESTRICT_VIEW_ON')
        
            if node_tree.types == 'VECBLUR':
                layout.label(text="This will also toggle the Vector pass {}".format(
                                    "on" if node_tree.toggle_mute else "off"), icon="INFO")

class NODE_OT_toggle_mute(Operator):
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
class NODE_PT_indices(Panel):
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
            if ob.material_slots:
                for ma in ob.material_slots:
                    if ma.material:
                        if ma.material.node_tree:
                            for no in ma.material.node_tree.nodes:
                                if no.type == 'EMISSION':
                                    for ou in no.outputs:
                                        if ou.links:
                                            meshlights = meshlights + 1
                                            if ob in context.visible_objects:
                                                meshlights_visible = meshlights_visible + 1
                                            break
            if ob in context.selected_objects:
                if ob.type == 'CAMERA':
                    cameras_selected = cameras_selected + 1
    
        meshlights_string = '| Meshlights:{}/{}'.format(meshlights_visible, meshlights)
    
        row = self.layout.row(align=True)
        row.label(text="Scenes:{} | Cameras:{}/{} {}".format(
                   scenes_count, cameras_selected, cameras_count,
                   meshlights_string if context.scene.render.engine == 'CYCLES' else ''))

# //FEATURE: Extra Info Stats

# FEATURE: Camera Bounds as Render Border
class VIEW3D_OT_render_border_camera(Operator):
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
        layout.operator(VIEW3D_OT_render_border_camera.bl_idname,
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
class VIEW3D_OT_show_only_render(Operator):
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
               "ShaderNodeTexImage",
               "ShaderNodeTexEnvironment"}

class NODE_OT_show_active_node_image(Operator):
    """Show active image node image in the image editor"""
    bl_idname = "node.show_active_node_image"
    bl_label = "Show Active Node Node"
    bl_options = {'UNDO'}

    def execute(self, context):
        preferences = context.user_preferences.addons[__name__].preferences
        if preferences.use_image_node_display:
            if context.active_node:
                active_node = context.active_node
                if active_node.bl_idname in image_nodes and active_node.image:
                    for area in context.screen.areas:
                        if area.type == "IMAGE_EDITOR":
                            for space in area.spaces:
                                if space.type == "IMAGE_EDITOR":
                                    space.image = active_node.image
                            break
    
        return {'FINISHED'}
# // FEATURE: Display Active Image Node on Image Editor

# FEATURE: Select Meshlights
class OBJECT_OT_select_meshlights(Operator):
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
            if ob.material_slots:
                for ma in ob.material_slots:
                    if ma.material:
                        if ma.material.node_tree:
                            for no in ma.material.node_tree.nodes:
                                if no.type == 'EMISSION':
                                    ob.select = True
                                    context.scene.objects.active = ob

        if not context.selected_objects and not context.scene.objects.active:
            self.report({'INFO'}, "No meshlights to select")

        return {'FINISHED'}

def button_select_meshlights(self, context):
    
    if context.scene.render.engine == 'CYCLES':
        self.layout.operator('object.select_meshlights', icon="LAMP_SUN")
# // FEATURE: Select Meshlights

# FEATURE: Mesh Symmetry Tools by Sergey Sharybin
class MESH_OT_find_asymmetric(Operator):
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

class MESH_OT_make_symmetric(Operator):
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

# FEATURE: Cycles Render Samples per Scene
def render_cycles_scene_samples(self, context):

    layout = self.layout

    scenes = bpy.data.scenes
    scene = context.scene
    cscene = scene.cycles

    if (len(bpy.data.scenes) > 1):
        layout.separator()

        layout.label(text="Samples Per Scene:")

        if cscene.progressive == 'PATH':
            for s in bpy.data.scenes:
                if s != scene:
                    if s.render.engine == 'CYCLES':
                        cscene = s.cycles
        
                        split = layout.split()
                        col = split.column()
                        sub = col.column(align=True)
        
                        sub.label(text="%s" % s.name)
        
                        col = split.column()
                        sub = col.column(align=True)
                        sub.prop(cscene, "samples", text="Samples")
                    else:
                        layout.label(text="Scene: '%s' is not using Cycles" % s.name)
        else:
            for s in bpy.data.scenes:
                if s != scene:
                    if s.render.engine == 'CYCLES':
                        cscene = s.cycles
        
                        split = layout.split()
                        col = split.column()
                        sub = col.column(align=True)
        
                        sub.label(text="%s" % s.name)
        
                        col = split.column()
                        sub = col.column(align=True)
                        sub.prop(cscene, "aa_samples", text="AA Samples")
                    else:
                        layout.label(text="Scene: '%s' is not using Cycles" % s.name)
# // FEATURE: Cycles Render Samples per Scene

# FEATURE: Motion Paths Extras
class POSE_OT_paths_clear_all(Operator):
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

class POSE_OT_paths_frame_match(Operator):
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
    col.operator(POSE_OT_paths_frame_match.bl_idname,
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
    layout.operator(POSE_OT_paths_clear_all.bl_idname, icon="X")
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
class SCENE_OT_cycles_shader_list_nodes(Operator):
    """List Cycles materials containing a specific shader"""
    bl_idname = "scene.cycles_list_nodes"
    bl_label = "List Materials"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'CYCLES'

    def execute(self, context):
        node_type = context.scene.amaranth_cycles_node_types
        count_ma = 0
        roughness = False
        materials = []
        global materials

        print("\n=== Cycles Shader Type: %s === \n" % node_type)

        for ma in bpy.data.materials:
            if ma.node_tree:
                nodes = ma.node_tree.nodes
                for no in nodes:
                    if no.type == node_type:
                        for ou in no.outputs:
                            if ou.links:
                                if no.type in ['BSDF_GLOSSY','BSDF_DIFFUSE','BSDF_GLASS']:
                                    roughness = 'R: %.4f' % no.inputs['Roughness'].default_value
                                else:
                                    roughness = False
                            else:
                                print('Note: \nOutput from "%s" node' % node_type,
                                      'in material "%s"' % ma.name,
                                      'not connected',
                                      '\n')

                            materials = list(set(materials))

                            count_ma = len(materials)

                            if ma.name not in materials:
                                materials.append('%s%s [%s] %s%s' % (
                                    '[L] ' if ma.library else '',
                                    ma.name, ma.users,
                                    '[F]' if ma.use_fake_user else '',
                                    ' - [%s]' % roughness if roughness else ''))

        if count_ma == 0:
            print("* No materials with nodes type %s found" % node_type)

        else:
            print("* A total of %s materials using %s was found \n" % (
                    count_ma + 1, node_type))

            count = 0

            for mat in materials:
                print('%02d. %s' % (count + 1, materials[count]))
                count = count + 1
            print("\n")

        materials = list(set(materials))

        return {'FINISHED'}

class SCENE_OT_cycles_shader_list_nodes_clear(Operator):
    """Clear the list below"""
    bl_idname = "scene.cycles_list_nodes_clear"
    bl_label = "Clear Materials List"
    
    def execute(self, context):
        materials[:] = []
        return {'FINISHED'}

class SCENE_OT_amaranth_debug_lamp_select(Operator):
    '''Select Lamp'''
    bl_idname = "scene.amaranth_debug_lamp_select"
    bl_label = "Select Lamp"
    lamp = bpy.props.StringProperty()
 
    def execute(self, context):
        if self.lamp:
            lamp = bpy.data.objects[self.lamp]

            bpy.ops.object.select_all(action='DESELECT')
            lamp.select = True
            context.scene.objects.active = lamp

        return{'FINISHED'}    


class SCENE_PT_scene_debug(Panel):
    '''Scene Debug'''
    bl_label = 'Scene Debug'
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        objects =  bpy.data.objects
        ob_act = context.active_object
        images = bpy.data.images
        lamps = bpy.data.lamps
        images_missing = []
        list_lamps = scene.amaranth_debug_scene_list_lamps
        list_missing_images = scene.amaranth_debug_scene_list_missing_images
        engine = scene.render.engine

        if engine == 'CYCLES':

            layout.label(text="List Cycles Materials:")

            split = layout.split(percentage=0.5)
            split.prop(scene, 'amaranth_cycles_node_types')

            row = split.row(align=True)
            row.operator(SCENE_OT_cycles_shader_list_nodes.bl_idname,
                            icon="SORTALPHA")
            row.operator(SCENE_OT_cycles_shader_list_nodes_clear.bl_idname,
                            icon="X", text="")

            try:
                materials
            except NameError:
                layout.label(text="No materials to show", icon="INFO")
            else:
                count = 0
                layout.label(text="%s %s found" % (len(materials),
                    'material' if len(materials) < 2 else 'materials'), icon="INFO")
                for mat in materials:
                    count = count + 1
                    layout.label(text='%s' % (materials[count-1]), icon="MATERIAL")

        # List Lamps
        box = layout.box()
        row = box.row(align=True)
        split = row.split()
        col = split.column()
        
        if lamps:
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.prop(scene, 'amaranth_debug_scene_list_lamps',
                        icon="%s" % 'TRIA_DOWN' if list_lamps else 'TRIA_RIGHT',
                        emboss=False)

            if objects and list_lamps:
                row = box.row(align=True)
                split = row.split(percentage=0.42)
                col = split.column()
                col.label(text="Name")

                split = split.split(percentage=0.1)
                col = split.column()
                col.label(text="", icon="BLANK1")
                if engine in ['CYCLES', 'BLENDER_RENDER']:
                    if engine == 'BLENDER_RENDER':
                        split = split.split(percentage=0.7)
                    else:
                        split = split.split(percentage=0.35)
                    col = split.column()
                    col.label(text="Samples")

                if engine == 'CYCLES':
                    split = split.split(percentage=0.35)
                    col = split.column()
                    col.label(text="Size")

                split = split.split(percentage=0.8)
                col = split.column()
                col.label(text="Visibility")

                for ob in objects:
                    if ob and ob.type == 'LAMP':
                        lamp = ob.data
                        clamp = ob.data.cycles

                        row = box.row(align=True)
                        split = row.split(percentage=0.5)
                        col = split.column()
                        row = col.row()
                        row.alignment = 'LEFT'
                        row.active = ob.name in context.scene.objects
                        row.operator("scene.amaranth_debug_lamp_select",
                                    text='%s %s%s' % (
                                        " [L] " if ob.library else "",
                                        ob.name,
                                        "" if ob.name in context.scene.objects else " [Not in Scene]"),
                                    icon="LAMP_%s" % ob.data.type,
                                    emboss=False).lamp = ob.name

                        if engine == 'CYCLES':
                            split = split.split(percentage=0.35)
                            col = split.column()
                            if scene.cycles.progressive == 'BRANCHED_PATH':
                                col.prop(clamp, "samples", text="")
                            if scene.cycles.progressive == 'PATH':
                               col.label(text="N/A")
                           
                        if engine == 'BLENDER_RENDER':
                            split = split.split(percentage=0.7)
                            col = split.column()
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

                        if engine == 'CYCLES':
                            split = split.split(percentage=0.4)
                            col = split.column()    
                            if lamp.type in ['POINT','SUN', 'SPOT']:
                                col.label(text="%.2f" % lamp.shadow_soft_size)
                            elif lamp.type == 'HEMI':
                                col.label(text="N/A")
                            else:
                                col.label(text="%.2f" % lamp.size)

                        split = split.split(percentage=0.8)
                        col = split.column()
                        row = col.row(align=True)
                        row.prop(ob, "hide", text="", emboss=False)
                        row.prop(ob, "hide_render", text="", emboss=False)

                        split = split.split(percentage=0.3)
                        col = split.column()
                        col.label(text="", icon="%s" % "TRIA_LEFT" if ob == ob_act else "BLANK1")

        else:
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="Lamps List", icon="RIGHTARROW_THIN")

            split = split.split()
            col = split.column()

            col.label(text="No Lamps", icon="LAMP_DATA")

        # List Missing Images
        if images:
            import os.path

            for im in images:
                if im.type not in ['UV_TEST', 'RENDER_RESULT', 'COMPOSITING']: 
                    if not os.path.exists(bpy.path.abspath(im.filepath, library=im.library)):
                        images_missing.append(["%s%s [%s]%s" % (
                            '[L] ' if im.library else '',
                            im.name, im.users,
                            ' [F]' if im.use_fake_user else ''),
                            im.filepath if im.filepath else 'No Filepath'])

            box = layout.box()
            row = box.row(align=True)
            split = row.split()
            col = split.column()

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
                        col.label(text=mis[1], icon="BLANK1")
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

# // FEATURE: Scene Debug

# FEATURE: Color Management Presets
class SCENE_MT_color_management_presets(Menu):
    """List of Color Management presets"""
    bl_label = "Color Management Presets"
    preset_subdir = "color"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class AddPresetColorManagement(AddPresetBase, Operator):
    """Add or remove a Color Management preset"""
    bl_idname = "scene.color_management_preset_add"
    bl_label = "Add Color Management Preset"
    preset_menu = "SCENE_MT_color_management_presets"

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
    row.menu("SCENE_MT_color_management_presets", text=bpy.types.SCENE_MT_color_management_presets.bl_label)
    row.operator("scene.color_management_preset_add", text="", icon="ZOOMIN")
    row.operator("scene.color_management_preset_add", text="", icon="ZOOMOUT").remove_active = True
    layout.separator()
# // FEATURE: Color Management Presets


classes = (SCENE_MT_color_management_presets,
           AddPresetColorManagement,
           SCENE_PT_scene_debug,
           SCENE_OT_refresh,
           SCENE_OT_cycles_shader_list_nodes,
           SCENE_OT_cycles_shader_list_nodes_clear,
           SCENE_OT_amaranth_debug_lamp_select,
           WM_OT_save_reload,
           MESH_OT_find_asymmetric,
           MESH_OT_make_symmetric,
           NODE_OT_AddTemplateVignette,
           NODE_MT_amaranth_templates,
           FILE_OT_directory_current_blend,
           FILE_OT_directory_go_to,
           NODE_PT_indices,
           NODE_PT_simplify,
           NODE_OT_toggle_mute,
           NODE_OT_show_active_node_image,
           VIEW3D_OT_render_border_camera,
           VIEW3D_OT_show_only_render,
           OBJECT_OT_select_meshlights,
           POSE_OT_paths_clear_all,
           POSE_OT_paths_frame_match,
           FILE_PT_libraries)

addon_keymaps = []

kmi_defs = (
    ('wm.call_menu', 'W', False, False, False, (('name', NODE_MT_amaranth_templates.bl_idname),)),
)

def register():

    bpy.utils.register_class(AmaranthToolsetPreferences)

    # UI: Register the panel
    init_properties()
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_object_specials.append(button_refresh)
    bpy.types.VIEW3D_MT_object_specials.append(button_render_border_camera)
    bpy.types.VIEW3D_MT_object_specials.append(button_camera_passepartout)

    bpy.types.INFO_MT_file.append(button_save_reload)
    bpy.types.INFO_HT_header.append(stats_scene)

    bpy.types.VIEW3D_MT_object_specials.append(button_frame_current) # Current Frame
    bpy.types.VIEW3D_MT_pose_specials.append(button_frame_current)
    bpy.types.VIEW3D_MT_select_object.append(button_select_meshlights)

    bpy.types.TIME_HT_header.append(label_timeline_extra_info) # Timeline Extra Info

    bpy.types.NODE_HT_header.append(node_templates_pulldown)
    bpy.types.NODE_HT_header.append(node_stats)
    bpy.types.NODE_HT_header.append(node_shader_extra)

    bpy.types.CyclesRender_PT_sampling.append(render_cycles_scene_samples)

    bpy.types.FILEBROWSER_HT_header.append(button_directory_current_blend)

    bpy.types.SCENE_PT_simplify.append(unsimplify_ui)
    bpy.types.CyclesScene_PT_simplify.append(unsimplify_ui)

    bpy.types.DATA_PT_display.append(pose_motion_paths_ui)

    bpy.types.RENDER_PT_dimensions.append(render_final_resolution_ui)

    bpy.types.SCENE_PT_color_management.prepend(ui_color_management_presets)

    bpy.app.handlers.render_pre.append(unsimplify_render_pre)
    bpy.app.handlers.render_post.append(unsimplify_render_post)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window')
        kmi = km.keymap_items.new('scene.refresh', 'F5', 'PRESS', shift=False, ctrl=False)
        kmi = km.keymap_items.new('wm.save_reload', 'W', 'PRESS', shift=True, ctrl=True)

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

        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        km.keymap_items.new("node.show_active_node_image", 'ACTIONMOUSE', 'RELEASE')
        km.keymap_items.new("node.show_active_node_image", 'SELECTMOUSE', 'RELEASE')

        addon_keymaps.append((km, kmi))

        # copypasted from the awesome node efficiency tools, future hotkeys proof!
        km = kc.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
        for (identifier, key, CTRL, SHIFT, ALT, props) in kmi_defs:
            kmi = km.keymap_items.new(identifier, key, 'PRESS', ctrl=CTRL, shift=SHIFT, alt=ALT)
            if props:
                for prop, value in props:
                    setattr(kmi.properties, prop, value)
            addon_keymaps.append((km, kmi))

def unregister():

    bpy.utils.unregister_class(AmaranthToolsetPreferences)

    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_object_specials.remove(button_refresh)
    bpy.types.VIEW3D_MT_object_specials.remove(button_render_border_camera)
    bpy.types.VIEW3D_MT_object_specials.remove(button_camera_passepartout)

    bpy.types.INFO_MT_file.remove(button_save_reload)
    bpy.types.INFO_HT_header.remove(stats_scene)

    bpy.types.VIEW3D_MT_object_specials.remove(button_frame_current)
    bpy.types.VIEW3D_MT_pose_specials.remove(button_frame_current)
    bpy.types.VIEW3D_MT_select_object.remove(button_select_meshlights)

    bpy.types.TIME_HT_header.remove(label_timeline_extra_info)

    bpy.types.NODE_HT_header.remove(node_templates_pulldown)
    bpy.types.NODE_HT_header.remove(node_stats)
    bpy.types.NODE_HT_header.remove(node_shader_extra)

    bpy.types.CyclesRender_PT_sampling.remove(render_cycles_scene_samples)

    bpy.types.FILEBROWSER_HT_header.remove(button_directory_current_blend)

    bpy.types.SCENE_PT_simplify.remove(unsimplify_ui)
    bpy.types.CyclesScene_PT_simplify.remove(unsimplify_ui)

    bpy.types.DATA_PT_display.remove(pose_motion_paths_ui)

    bpy.types.RENDER_PT_dimensions.remove(render_final_resolution_ui)

    bpy.types.SCENE_PT_color_management.remove(ui_color_management_presets)

    bpy.app.handlers.render_pre.remove(unsimplify_render_pre)
    bpy.app.handlers.render_post.remove(unsimplify_render_post)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    clear_properties()

if __name__ == "__main__":
    register()
