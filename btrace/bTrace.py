#BEGIN GPL LICENSE BLOCK

#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software Foundation,
#Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

#END GPL LICENCE BLOCK

bl_info = {
    'name': "Btrace",
    'author': "liero, crazycourier, Atom, Meta-Androcto, MacKracken",
    'version': (1, 1, ),
    'blender': (2, 62),
    'location': "View3D > Tools",
    'description': "Tools for converting/animating objects/particles into curves",
    'warning': "Still under development, bug reports appreciated",
    'wiki_url': "",
    'tracker_url': "http://projects.blender.org/tracker/?func=detail&atid=468&aid=29563&group_id=153",
    'category': "Add Curve"
    }

#### TO DO LIST ####
### [   ]  Add more options to curve radius/modulation plus cyclic/connect curve option

import bpy, selection_utils
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty, FloatVectorProperty


# Class to define properties
class TracerProperties(bpy.types.PropertyGroup):
    enabled = IntProperty(default=0)
    # Object Curve Settings
    curve_spline = EnumProperty(name="Spline", items=(("POLY", "Poly", "Use Poly spline type"),  ("NURBS", "Nurbs", "Use Nurbs spline type"), ("BEZIER", "Bezier", "Use Bezier spline type")), description="Choose which type of spline to use when curve is created", default="BEZIER")
    curve_handle = EnumProperty(name="Handle", items=(("ALIGNED", "Aligned", "Use Aligned Handle Type"), ("AUTOMATIC", "Automatic", "Use Auto Handle Type"), ("FREE_ALIGN", "Free Align", "Use Free Handle Type"), ("VECTOR", "Vector", "Use Vector Handle Type")), description="Choose which type of handle to use when curve is created",  default="VECTOR")
    curve_resolution = IntProperty(name="Bevel Resolution", min=1, max=32, default=4, description="Adjust the Bevel resolution")
    curve_depth = FloatProperty(name="Bevel Depth", min=0.0, max=100.0, default=0.1, description="Adjust the Bevel depth")
    curve_u = IntProperty(name="Resolution U", min=0, max=64, default=12, description="Adjust the Surface resolution")
    curve_join = BoolProperty(name="Join Curves", default=False, description="Join all the curves after they have been created")
    curve_smooth = BoolProperty(name="Smooth", default=True, description="Render curve smooth")
    # Option to Duplicate Mesh
    object_duplicate = BoolProperty(name="Apply to Copy", default=False, description="Apply curve to a copy of object")
    # Distort Mesh options
    distort_modscale = IntProperty(name="Modulation Scale", min=0, max=50, default=2, description="Add a scale to modulate the curve at random points, set to 0 to disable")
    distort_noise = FloatProperty(name="Mesh Noise", min=0.0, max=50.0, default=0.00, description="Adjust noise added to mesh before adding curve")
    # Particle Options
    particle_step = IntProperty(name="Step Size", min=1, max=50, default=5, description="Sample one every this number of frames")
    particle_auto = BoolProperty(name='Auto Frame Range', default=True, description='Calculate Frame Range from particles life')
    particle_f_start = IntProperty(name='Start Frame', min=1, max=5000, default=1, description='Start frame')
    particle_f_end = IntProperty(name='End Frame', min=1, max=5000, default=250, description='End frame')
    # F-Curve Modifier Properties
    fcnoise_rot = BoolProperty(name="Rotation", default=False, description="Affect Rotation")
    fcnoise_loc = BoolProperty(name="Location", default=True, description="Affect Location")
    fcnoise_scale = BoolProperty(name="Scale", default=False, description="Affect Scale")
    fcnoise_amp = IntProperty(name="Amp", min=1, max=500, default=5, description="Adjust the amplitude")
    fcnoise_timescale = FloatProperty(name="Time Scale", min=1, max=500, default=50, description="Adjust the time scale")
    fcnoise_key = BoolProperty(name="Add Keyframe", default=True, description="Keyframe is needed for tool, this adds a LocRotScale keyframe")
    # Toolbar Settings/Options Booleans
    curve_settings = BoolProperty(name="Curve Settings", default=False, description="Change the settings for the created curve")
    particle_settings = BoolProperty(name="Particle Settings", default=False, description="Show the settings for the created curve")
    animation_settings = BoolProperty(name="Animation Settings", default=False, description="Show the settings for the Animations")
    distort_curve = BoolProperty(name="Add Distortion", default=False, description="Set options to distort the final curve")
    connect_noise = BoolProperty(name="F-Curve Noise", default=False, description="Adds F-Curve Noise Modifier to selected objects")
    settings_objectTrace = BoolProperty(name="Object Trace Settings", default=False, description="Trace selected mesh object with a curve")
    settings_objectsConnect = BoolProperty(name="Objects Connect Settings", default=False, description="Connect objects with a curve controlled by hooks")
    settings_objectTrace = BoolProperty(name="Object Trace Settings", default=False, description="Trace selected mesh object with a curve")
    respect_order = BoolProperty(name="Order", default=False, description="Remember order objects were selected")
    settings_particleTrace = BoolProperty(name="Particle Trace Settings", default=False, description="Trace particle path with a  curve")
    settings_particleConnect = BoolProperty(name="Particle Connect Settings", default=False, description="Connect particles with a curves and animated over particle lifetime")
    settings_growCurve = BoolProperty(name="Grow Curve Settings", default=False, description="Animate curve bevel over time by keyframing points radius")
    settings_fcurve = BoolProperty(name="F-Curve Settings", default=False, description="F-Curve Settings")
    settings_meshfollow = BoolProperty(name="Mesh Follow Settings", default=False, description="Mesh Follow Settings")
    # Toolbar Tool show/hide booleans
    tool_objectTrace = BoolProperty(name="Object Trace", default=False, description="Trace selected mesh object with a curve")
    tool_objectsConnect = BoolProperty(name="Objects Connect", default=False, description="Connect objects with a curve controlled by hooks")
    tool_particleTrace = BoolProperty(name="Particle Trace", default=False, description="Trace particle path with a  curve")
    tool_meshFollow = BoolProperty(name="Mesh Follow", default=False, description="Follow selection items on animated mesh object")
    tool_particleConnect = BoolProperty(name="Particle Connect", default=False, description="Connect particles with a curves and animated over particle lifetime")
    tool_growCurve = BoolProperty(name="Grow Curve", default=False, description="Animate curve bevel over time by keyframing points radius")
    tool_handwrite = BoolProperty(name="Handwriting", default=False, description="Create and Animate curve using the grease pencil")
    tool_fcurve = BoolProperty(name="F-Curve Noise", default=False, description="Add F-Curve noise to selected objects")
    # Animation Options
    anim_auto = BoolProperty(name='Auto Frame Range', default=True, description='Automatically calculate Frame Range')
    anim_f_start = IntProperty(name='Start', min=1, max=2500, default=1, description='Start frame / Hidden object')
    anim_length = IntProperty(name='Duration', min=1, soft_max=1000, max=2500, default=100, description='Animation Length')
    anim_f_fade = IntProperty(name='Fade After', min=0, soft_max=250, max=2500, default=10, description='Fade after this frames / Zero means no fade')
    anim_delay = IntProperty(name='Grow', min=0, max=50, default=5, description='Frames it takes a point to grow')
    anim_tails = BoolProperty(name='Tails on endpoints', default=True, description='Set radius to zero for open splines endpoints')
    anim_keepr = BoolProperty(name='Keep Radius', default=True, description='Try to keep radius data from original curve')
    animate = BoolProperty(name="Animate Result", default=False, description='Animate the final curve objects')
    # Convert to Curve options
    convert_conti = BoolProperty(name='Continuous', default=True, description='Create a continuous curve using verts from mesh')
    convert_everyedge = BoolProperty(name='Every Edge', default=False, description='Create a curve from all verts in a mesh')
    convert_edgetype = EnumProperty(name="Edge Type for Curves",
        items=(("CONTI", "Continuous", "Create a continuous curve using verts from mesh"),  ("EDGEALL", "All Edges", "Create a curve from every edge in a mesh")),
        description="Choose which type of spline to use when curve is created", default="CONTI")
    convert_joinbefore = BoolProperty(name="Join objects before convert", default=False, description='Join all selected mesh to one object before converting to mesh')
    # Mesh Follow Options
    fol_edge_select = BoolProperty(name='Edge', default=False, description='Grow from edges')
    fol_vert_select = BoolProperty(name='Vertex', default=False, description='Grow from verts')
    fol_face_select = BoolProperty(name='Face', default=True, description='Grow from faces')
    fol_mesh_type = EnumProperty(name='Mesh type', default='VERTS', description='Mesh feature to draw cruves from', items=(
        ("VERTS", "Verts", "Draw from Verts"), ("EDGES", "Edges", "Draw from Edges"), ("FACES", "Faces", "Draw from Faces"), ("OBJECT", "Object", "Draw from Object origin")))
    fol_start_frame = IntProperty(name="Start Frame", min=1, max=2500, default=1, description="Start frame for range to trace")
    fol_end_frame = IntProperty(name="End Frame", min=1, max=2500, default=250, description="End frame for range to trace")
    fol_perc_verts = FloatProperty(name="Reduce selection by", min=0.001, max=1.000, default=0.5, description="percentage of total verts to trace")
    fol_sel_option = EnumProperty(name="Selection type", description="Choose which objects to follow", default="RANDOM", items=(
        ("RANDOM", "Random", "Follow Random items"),  ("CUSTOM", "Custom Select", "Follow selected items"), ("ALL", "All", "Follow all items")))
    trace_mat_color = FloatVectorProperty(name="Material Color", description="Choose material color", min=0, max=1, default=(0.0,0.3,0.6), subtype="COLOR")
    trace_mat_random = BoolProperty(name="Random Color", default=False, description='Make the material colors random')


############################
## Draw Brush panel in Toolbar
############################
class addTracerObjectPanel(bpy.types.Panel):
    bl_label = "bTrace: Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'

    def draw(self, context):
        layout = self.layout
        bTrace = bpy.context.window_manager.curve_tracer
        obj = bpy.context.object

        ############################
        ## Curve options
        ############################
        curve_settings = bTrace.curve_settings
        row = self.layout.row()
        row.label(text="Universal Curve Settings")
        box = self.layout.box()
        row = box.row()
        CurveSettingText = "Show: Curve Settings"
        if curve_settings:
            CurveSettingText = "Hide: Curve Settings"
        else:
            CurveSettingText = "Show: Curve Settings"
        row.prop(bTrace, 'curve_settings', icon='CURVE_BEZCURVE', text=CurveSettingText)
        if curve_settings:
            box.label(text="Curve Settings", icon="CURVE_BEZCURVE")
            row = box.row()
            row.label("Curve Material Color")
            row = box.row()
            row.prop(bTrace, "trace_mat_random")
            if not bTrace.trace_mat_random:
                row.prop(bTrace, "trace_mat_color", text="")
            if len(bpy.context.selected_objects) > 0:
                if obj.type == 'CURVE':
                    col = box.column(align=True)
                    col.label(text="Edit Curves for")
                    col.label(text="Selected Curve")
                    col.prop(obj.data, 'bevel_depth')
                    col.prop(obj.data, 'bevel_resolution')
                    col.prop(obj.data, 'resolution_u')
                else:
                    ############################
                    ## Object Curve Settings
                    ############################
                    curve_spline, curve_handle, curve_depth, curve_resolution, curve_u = bTrace.curve_spline, bTrace.curve_handle, bTrace.curve_depth, bTrace.curve_resolution, bTrace.curve_u
                    box.label(text="New Curve Settings")
                    box.prop(bTrace, "curve_spline")
                    box.prop(bTrace, "curve_handle")
                    col = box.column(align=True)
                    col.prop(bTrace, "curve_depth")
                    col.prop(bTrace, "curve_resolution")
                    col.prop(bTrace, "curve_u")

        ######################
        ## Start  Object Tools ###
        ######################
        row = self.layout.row()
        row.label(text="Object Tools")
        distort_curve = bTrace.distort_curve
        tool_objectTrace, settings_objectTrace, convert_joinbefore, convert_edgetype = bTrace.tool_objectTrace, bTrace.settings_objectTrace, bTrace.convert_joinbefore, bTrace.convert_edgetype
        animate = bTrace.animate
        anim_auto, curve_join = bTrace.anim_auto, bTrace.curve_join
        settings_particleTrace, settings_particleConnect = bTrace.settings_particleTrace, bTrace.settings_particleConnect
        sel = bpy.context.selected_objects
        ############################
        ### Object Trace
        ############################
        box = self.layout.box()
        row = box.row()
        ObjectText = "Show: Objects Trace"
        if tool_objectTrace:
            ObjectText = "Hide: Objects Trace"
        else:
            ObjectText = "Show: Objects Trace"
        row.prop(bTrace, "tool_objectTrace", text=ObjectText, icon="FORCE_MAGNETIC")
        if tool_objectTrace:
            row = box.row()
            row.label(text="Object Trace", icon="FORCE_MAGNETIC")
            row.operator("object.btobjecttrace", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(bTrace, "settings_objectTrace", icon='MODIFIER', text='Settings')
            row.label(text="")
            if settings_objectTrace:
                row = box.row()
                row.label(text='Edge Draw Method')
                row = box.row(align=True)
                row.prop(bTrace, 'convert_edgetype')
                box.prop(bTrace, "object_duplicate")
                if len(sel) > 1:
                    box.prop(bTrace, 'convert_joinbefore')
                else:
                    convert_joinbefore = False
                row = box.row()
                row.prop(bTrace, "distort_curve")
                if distort_curve:
                    col = box.column(align=True)
                    col.prop(bTrace, "distort_modscale")
                    col.prop(bTrace, "distort_noise")
                row = box.row()
                row.prop(bTrace, "animate", text="Add Grow Curve Animation", icon="META_BALL")
                row.label("")
                if animate:
                    # animation settings here
                    box.label(text='Frame Animation Settings:')
                    col = box.column(align=True)
                    col.prop(bTrace, 'anim_auto')
                    if not anim_auto:
                        row = col.row(align=True)
                        row.prop(bTrace, 'anim_f_start')
                        row.prop(bTrace, 'anim_length')
                    row = col.row(align=True)
                    row.prop(bTrace, 'anim_delay')
                    row.prop(bTrace, 'anim_f_fade')

                    box.label(text='Additional Settings')
                    row = box.row()
                    row.prop(bTrace, 'anim_tails')
                    row.prop(bTrace, 'anim_keepr')

        ############################
        ### Objects Connect
        ############################
        connect_noise = bTrace.connect_noise
        tool_objectsConnect, settings_objectsConnect, respect_order = bTrace.tool_objectsConnect, bTrace.settings_objectsConnect, bTrace.respect_order
        box = self.layout.box()
        row = box.row()
        ObjectConnText = "Show: Objects Connect"
        if tool_objectsConnect:
            ObjectConnText = "Hide: Objects Connect"
        else:
            ObjectConnText = "Show: Objects Connect"
        row.prop(bTrace, "tool_objectsConnect", text=ObjectConnText, icon="OUTLINER_OB_EMPTY")
        if tool_objectsConnect:
            row = box.row()
            row.label(text="Objects Connect", icon="OUTLINER_OB_EMPTY")
            row.operator("object.btobjectsconnect", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(bTrace, "settings_objectsConnect", icon='MODIFIER', text='Settings')
            row.prop(bTrace, "respect_order")
            if respect_order:
                box.operator("object.select_order")
            if settings_objectsConnect:
                box.prop(bTrace, "connect_noise")
                if connect_noise:
                    row = box.row()
                    row.label(text="F-Curve Noise")
                    row = box.row(align=True)
                    row.prop(bTrace, "fcnoise_rot")
                    row.prop(bTrace, "fcnoise_loc")
                    row.prop(bTrace, "fcnoise_scale")
                    col = box.column(align=True)
                    col.prop(bTrace, "fcnoise_amp")
                    col.prop(bTrace, "fcnoise_timescale")
                    box.prop(bTrace, "fcnoise_key")
                # Grow settings here
                row = box.row()
                row.prop(bTrace, "animate", text="Add Grow Curve Animation", icon="META_BALL")
                row.label("")
                if animate:
                    box.label(text='Frame Animation Settings:')
                    col = box.column(align=True)
                    col.prop(bTrace, 'anim_auto')
                    if not anim_auto:
                        row = col.row(align=True)
                        row.prop(bTrace, 'anim_f_start')
                        row.prop(bTrace, 'anim_length')
                    row = col.row(align=True)
                    row.prop(bTrace, 'anim_delay')
                    row.prop(bTrace, 'anim_f_fade')

                    box.label(text='Additional Settings')
                    row = box.row()
                    row.prop(bTrace, 'anim_tails')
                    row.prop(bTrace, 'anim_keepr')

        ############################
        ### Mesh Follow
        ############################
        tool_meshFollow, settings_meshfollow, fol_edge_select, fol_vert_select, fol_face_select, fol_sel_option, fol_perc_verts, fol_mesh_type = bTrace.tool_meshFollow, bTrace.settings_meshfollow, bTrace.fol_edge_select, bTrace.fol_vert_select, bTrace.fol_face_select, bTrace.fol_sel_option, bTrace.fol_perc_verts, bTrace.fol_mesh_type
        box = self.layout.box()
        row = box.row()
        ObjectConnText = "Show: Mesh Follow"
        if tool_meshFollow:
            ObjectConnText = "Hide: Mesh Follow"
        else:
            ObjectConnText = "Show: Mesh Follow"
        row.prop(bTrace, "tool_meshFollow", text=ObjectConnText, icon="DRIVER")
        if tool_meshFollow:
            row = box.row()
            row.label(text="Mesh Follow", icon="DRIVER")
            row.operator("object.btmeshfollow", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(bTrace, "settings_meshfollow", icon='MODIFIER', text='Settings')
            if fol_mesh_type == 'OBJECT':
                row.label(text="Trace Object", icon="SNAP_VOLUME")
            if fol_mesh_type == 'VERTS':
                row.label(text="Trace Verts", icon="SNAP_VERTEX")
            if fol_mesh_type == 'EDGES':
                row.label(text="Trace Edges", icon="SNAP_EDGE")
            if fol_mesh_type == 'FACES':
                row.label(text="Trace Faces", icon="SNAP_FACE")
            if settings_meshfollow:
                col = box.column(align=True)
                row = col.row(align=True)
                row.prop(bTrace, "fol_mesh_type", expand=True)
                row = col.row(align=True)
                if fol_mesh_type != 'OBJECT':
                    row.prop(bTrace, "fol_sel_option", expand=True)
                    row = box.row()
                    if fol_sel_option == 'RANDOM':
                        row.label("Random Select of Total")
                        row.prop(bTrace, "fol_perc_verts", text="%")
                    if fol_sel_option == 'CUSTOM':
                        row.label("Choose selection in Edit Mode")
                    if fol_sel_option == 'ALL':
                        row.label("Select All items")
                #row = box.row()
                sep = box.separator()
                col = box.column(align=True)
                col.label("Time Options", icon="TIME")
                col.prop(bTrace, "particle_step")
                row = col.row(align=True)
                row.prop(bTrace, "fol_start_frame")
                row.prop(bTrace, "fol_end_frame")
                # Grow settings here
                row = box.row()
                row.prop(bTrace, "animate", text="Add Grow Curve Animation", icon="META_BALL")
                row.label("")
                if animate:
                    box.label(text='Frame Animation Settings:')
                    col = box.column(align=True)
                    col.prop(bTrace, 'anim_auto')
                    if not anim_auto:
                        row = col.row(align=True)
                        row.prop(bTrace, 'anim_f_start')
                        row.prop(bTrace, 'anim_length')
                    row = col.row(align=True)
                    row.prop(bTrace, 'anim_delay')
                    row.prop(bTrace, 'anim_f_fade')

                    box.label(text='Additional Settings')
                    row = box.row()
                    row.prop(bTrace, 'anim_tails')
                    row.prop(bTrace, 'anim_keepr')

         ############################
        ### Handwriting Tools
        ############################
        tool_handwrite = bTrace.tool_handwrite
        box = self.layout.box()
        row = box.row()
        handText = "Show: Handwriting Tool"
        if tool_handwrite:
            handText = "Hide: Handwriting Tool"
        else:
            handText = "Show: Handwriting Tool"
        row.prop(bTrace, 'tool_handwrite', text=handText, icon='BRUSH_DATA')
        if tool_handwrite:
            row = box.row()
            row.label(text='Handwriting', icon='BRUSH_DATA')
            row.operator("curve.btwriting", text="Run!", icon='PLAY')
            row = box.row()
            row.prop(bTrace, "animate", text="Grow Curve Animation Settings", icon="META_BALL")
            if animate:
                # animation settings here
                row = box.row()
                row.label(text='Frame Animation Settings:')
                row.prop(bTrace, 'anim_auto')
                if not anim_auto:
                    row = box.row(align=True)
                    row.prop(bTrace, 'anim_f_start')
                    row.prop(bTrace, 'anim_length')
                row = box.row(align=True)
                row.prop(bTrace, 'anim_delay')
                row.prop(bTrace, 'anim_f_fade')

                box.label(text='Additional Settings')
                row = box.row()
                row.prop(bTrace, 'anim_tails')
                row.prop(bTrace, 'anim_keepr')
            row = box.row()
            row.label(text='Grease Pencil Writing Tools')
            col = box.column(align=True)
            row = col.row(align=True)
            row.operator("gpencil.draw", text="Draw", icon='BRUSH_DATA').mode = 'DRAW'
            row.operator("gpencil.draw", text="Poly", icon='VPAINT_HLT').mode = 'DRAW_POLY'
            row = col.row(align=True)
            row.operator("gpencil.draw", text="Line", icon='ZOOMOUT').mode = 'DRAW_STRAIGHT'
            row.operator("gpencil.draw", text="Erase", icon='TPAINT_HLT').mode = 'ERASER'
            row = box.row()
            row.operator("gpencil.data_unlink", text="Delete Grease Pencil Layer", icon="CANCEL")
            row = box.row()

        ############################
        ### Particle Trace
        ############################
        tool_particleTrace = bTrace.tool_particleTrace
        box = self.layout.box()
        row = box.row()
        ParticleText = "Show: Particle Trace"
        if tool_particleTrace:
            ParticleText = "Hide: Particle Trace"
        else:
            ParticleText = "Show: Particle Trace"
        row.prop(bTrace, "tool_particleTrace", icon="PARTICLES", text=ParticleText)
        if tool_particleTrace:
            row = box.row()
            row.label(text="Particle Trace", icon="PARTICLES")
            row.operator("particles.particletrace", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(bTrace, 'settings_particleTrace', icon='MODIFIER', text='Settings')
            row.label(text='')
            if settings_particleTrace:
                box.prop(bTrace, "particle_step")
                row = box.row()
                row.prop(bTrace, "curve_join")
                row.prop(bTrace, "animate", text="Add Grow Curve Animation", icon="META_BALL")
                if animate:
                    # animation settings here
                    box.label(text='Frame Animation Settings:')
                    col = box.column(align=True)
                    col.prop(bTrace, 'anim_auto')
                    if not anim_auto:
                        row = col.row(align=True)
                        row.prop(bTrace, 'anim_f_start')
                        row.prop(bTrace, 'anim_length')
                    row = col.row(align=True)
                    row.prop(bTrace, 'anim_delay')
                    row.prop(bTrace, 'anim_f_fade')

                    box.label(text='Additional Settings')
                    row = box.row()
                    row.prop(bTrace, 'anim_tails')
                    row.prop(bTrace, 'anim_keepr')

        ############################
        ### Connect Particles
        ############################
        particle_auto = bTrace.particle_auto
        tool_particleConnect = bTrace.tool_particleConnect
        box = self.layout.box()
        row = box.row()
        ParticleConnText = "Show: Particle Connect"
        if tool_particleConnect:
            ParticleConnText = "Hide: Particle Connect"
        else:
            ParticleConnText = "Show: Particle Connect"
        row.prop(bTrace, "tool_particleConnect", icon="MOD_PARTICLES", text=ParticleConnText)
        if tool_particleConnect:
            row = box.row()
            row.label(text='Particle Connect', icon='MOD_PARTICLES')
            row.operator("particles.connect", icon="PLAY", text='Run!')
            row = box.row()
            row.prop(bTrace, 'settings_particleConnect', icon='MODIFIER', text='Settings')
            row.label(text='')
            if settings_particleConnect:
                box.prop(bTrace, "particle_step")
                row = box.row()
                row.prop(bTrace, 'particle_auto')
                row.prop(bTrace, 'animate', text='Add Grow Curve Animation', icon="META_BALL")
                col = box.column(align=True)
                if not particle_auto:
                    row = box.row(align=True)
                    row.prop(bTrace, 'particle_f_start')
                    row.prop(bTrace, 'particle_f_end')
                if animate:
                    # animation settings here
                    box.label(text='Frame Animation Settings:')
                    col = box.column(align=True)
                    col.prop(bTrace, 'anim_auto')
                    if not anim_auto:
                        row = col.row(align=True)
                        row.prop(bTrace, 'anim_f_start')
                        row.prop(bTrace, 'anim_length')
                    row = col.row(align=True)
                    row.prop(bTrace, 'anim_delay')
                    row.prop(bTrace, 'anim_f_fade')

                    box.label(text='Additional Settings')
                    row = box.row()
                    row.prop(bTrace, 'anim_tails')
                    row.prop(bTrace, 'anim_keepr')

        #######################
        #### Animate Curve ####
        #######################
        row = self.layout.row()
        row.label(text="Curve Animation Tools")

        animation_settings = bTrace.animation_settings
        settings_growCurve = bTrace.settings_growCurve
        box = self.layout.box()
        row = box.row()
        GrowText = "Show: Grow Curve Animation"
        if animation_settings:
            GrowText = "Hide: Grow Curve Animation"
        else:
            GrowText = "Show: Grow Curve Animation"
        row.prop(bTrace, 'animation_settings', icon="META_BALL", text=GrowText)
        if animation_settings:
            row = box.row()
            row.label(text="Grow Curve", icon="META_BALL")
            row.operator('curve.btgrow', text='Run!', icon='PLAY')
            row = box.row()
            row.prop(bTrace, "settings_growCurve", icon='MODIFIER', text='Settings')
            row.operator('object.btreset',  icon='KEY_DEHLT')
            if settings_growCurve:
                box.label(text='Frame Animation Settings:')
                col = box.column(align=True)
                col.prop(bTrace, 'anim_auto')
                if not anim_auto:
                    row = col.row(align=True)
                    row.prop(bTrace, 'anim_f_start')
                    row.prop(bTrace, 'anim_length')
                row = col.row(align=True)
                row.prop(bTrace, 'anim_delay')
                row.prop(bTrace, 'anim_f_fade')

                box.label(text='Additional Settings')
                row = box.row()
                row.prop(bTrace, 'anim_tails')
                row.prop(bTrace, 'anim_keepr')

        #######################
        #### F-Curve Noise Curve ####
        #######################
        tool_fcurve = bTrace.tool_fcurve
        settings_fcurve = bTrace.settings_fcurve
        box = self.layout.box()
        row = box.row()
        fcurveText = "Show: F-Curve Noise"
        if tool_fcurve:
            fcurveText = "Hide: F-Curve Noise"
        else:
            fcurveText = "Show: F-Curve Noise"
        row.prop(bTrace, "tool_fcurve", text=fcurveText, icon='RNDCURVE')
        if tool_fcurve:
            row = box.row()
            row.label(text="F-Curve Noise", icon='RNDCURVE')
            row.operator("object.btfcnoise", icon='PLAY', text="Run!")
            row = box.row()
            row.prop(bTrace, "settings_fcurve", icon='MODIFIER', text='Settings')
            row.operator('object.btreset',  icon='KEY_DEHLT')
            if settings_fcurve:
                row = box.row(align=True)
                row.prop(bTrace, "fcnoise_rot")
                row.prop(bTrace, "fcnoise_loc")
                row.prop(bTrace, "fcnoise_scale")
                col = box.column(align=True)
                col.prop(bTrace, "fcnoise_amp")
                col.prop(bTrace, "fcnoise_timescale")
                box.prop(bTrace, "fcnoise_key")
###### END PANEL ##############
###############################


################## ################## ################## ############
## Object Trace
## creates a curve with a modulated radius connecting points of a mesh
################## ################## ################## ############

class OBJECT_OT_objecttrace(bpy.types.Operator):
    bl_idname = "object.btobjecttrace"
    bl_label = "bTrace: Object Trace"
    bl_description = "Trace selected mesh object with a curve with the option to animate"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type in {'MESH', 'FONT'})

    def invoke(self, context, event):
        import bpy

        # Run through each selected object and convert to to a curved object
        brushObj = bpy.context.selected_objects
        objectDupli = bpy.context.window_manager.curve_tracer.object_duplicate  # Get duplicate check setting
        convert_joinbefore = bpy.context.window_manager.curve_tracer.convert_joinbefore
        animate = bpy.context.window_manager.curve_tracer.animate
        # Duplicate Mesh
        if objectDupli:
            bpy.ops.object.duplicate_move()
            brushObj = bpy.context.selected_objects
        # Join Mesh
        if convert_joinbefore:
            if len(brushObj) > 1:  # Only run if multiple objects selected
                bpy.ops.object.join()
                brushObj = bpy.context.selected_objects

        for i in brushObj:
            bpy.context.scene.objects.active = i
            if i and i.type != 'CURVE':
                bpy.ops.object.btconvertcurve()
                addtracemat(bpy.context.object.data)
            if animate:
                bpy.ops.curve.btgrow()
        return{"FINISHED"}


################## ################## ################## ############
## Objects Connect
## connect selected objects with a curve + hooks to each node
## possible handle types: 'FREE' 'AUTO' 'VECTOR' 'ALIGNED'
################## ################## ################## ############


class OBJECT_OT_objectconnect(bpy.types.Operator):
    bl_idname = "object.btobjectsconnect"
    bl_label = "bTrace: Objects Connect"
    bl_description = "Connect selected objects with a curve and add hooks to each node"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(bpy.context.selected_objects) > 1

    def invoke(self, context, event):
        import bpy, selection_utils
        list = []
        bTrace = bpy.context.window_manager.curve_tracer
        objectHandle = bTrace.curve_handle  # Get Handle selection
        if objectHandle == 'AUTOMATIC':  # hackish because of naming conflict in api
            objectHandle = 'AUTO'
        objectrez = bTrace.curve_resolution  # Get Bevel resolution
        objectdepth = bTrace.curve_depth  # Get Bevel Depth
        animate = bTrace.animate  # add Grow Curve
        respect_order = bTrace.respect_order  # respect object selection order
        connect_noise = bTrace.connect_noise
        # Check if bTrace group exists, if not create
        bgroup = bpy.data.groups.keys()
        if 'bTrace' not in bgroup:
            bpy.ops.group.create(name="bTrace")
        #  check if noise
        if connect_noise:
            bpy.ops.object.btfcnoise()
        # check if respect order is checked, create list of objects
        if respect_order == True:
            selobnames = selection_utils.selected
            obnames = []
            for ob in selobnames:
                obnames.append(bpy.data.objects[ob])
        else:
            obnames = bpy.context.selected_objects  # No selection order

        for a in obnames:
            list.append(a)
            a.select = False

        # trace the origins
        tracer = bpy.data.curves.new('tracer', 'CURVE')
        tracer.dimensions = '3D'
        spline = tracer.splines.new('BEZIER')
        spline.bezier_points.add(len(list) - 1)
        curve = bpy.data.objects.new('curve', tracer)
        bpy.context.scene.objects.link(curve)

        # render ready curve
        tracer.resolution_u = 64
        tracer.bevel_resolution = objectrez  # Set bevel resolution from Panel options
        tracer.fill_mode = 'FULL'
        tracer.bevel_depth = objectdepth  # Set bevel depth from Panel options

        # move nodes to objects
        for i in range(len(list)):
            p = spline.bezier_points[i]
            p.co = list[i].location
            p.handle_right_type = objectHandle
            p.handle_left_type = objectHandle

        bpy.context.scene.objects.active = curve
        bpy.ops.object.mode_set(mode='OBJECT')

        # place hooks
        for i in range(len(list)):
            list[i].select = True
            curve.data.splines[0].bezier_points[i].select_control_point = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.hook_add_selob()
            bpy.ops.object.mode_set(mode='OBJECT')
            curve.data.splines[0].bezier_points[i].select_control_point = False
            list[i].select = False

        bpy.ops.object.select_all(action='DESELECT')
        curve.select = True # selected curve after it's created
        addtracemat(bpy.context.object.data) # Add material
        if animate: # Add Curve Grow it?
            bpy.ops.curve.btgrow()
        bpy.ops.object.group_link(group="bTrace") # add to bTrace group
        if bTrace.animate:
            bpy.ops.curve.btgrow() # Add grow curve
        return{"FINISHED"}


################## ################## ################## ############
## Particle Trace
## creates a curve from each particle of a system
################## ################## ################## ############
def  curvetracer(curvename, splinename):
    bTrace = bpy.context.window_manager.curve_tracer
    tracer = bpy.data.curves.new(splinename, 'CURVE')
    tracer.dimensions = '3D'
    curve = bpy.data.objects.new(curvename, tracer)
    bpy.context.scene.objects.link(curve)
    addtracemat(tracer)  # Add material
    # tracer.materials.append(bpy.data.materials.get('TraceMat'))
    try: tracer.fill_mode = 'FULL'
    except: tracer.use_fill_front = tracer.use_fill_back = False
    tracer.bevel_resolution = bTrace.curve_resolution
    tracer.bevel_depth = bTrace.curve_depth
    tracer.resolution_u = bTrace.curve_u
    return tracer, curve


class OBJECT_OT_particletrace(bpy.types.Operator):
    bl_idname = "particles.particletrace"
    bl_label = "bTrace: Particle Trace"
    bl_description = "Creates a curve from each particle of a system. Keeping particle amount under 250 will make this run faster"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (bpy.context.object and bpy.context.object.particle_systems)

    def execute(self, context):
        bTrace = bpy.context.window_manager.curve_tracer
        objectHandle = bTrace.curve_handle
        stepSize = bTrace.particle_step    # step size in frames
        curve_join = bTrace.curve_join # join curves after created
        obj = bpy.context.object
        ps = obj.particle_systems.active
        curvelist = []
        if objectHandle == 'AUTOMATIC': # hackish because of naming conflict in api
            objectHandle = 'AUTO'
        if objectHandle == 'FREE_ALIGN':
            objectHandle = 'FREE'
        
        # Check if bTrace group exists, if not create
        bgroup = bpy.data.groups.keys()
        if 'bTrace' not in bgroup:
            bpy.ops.group.create(name="bTrace") 

        if bTrace.curve_join:
            tracer = curvetracer('Tracer', 'Splines')
        for x in ps.particles:
            if not bTrace.curve_join:
                tracer = curvetracer('Tracer.000', 'Spline.000')
            spline = tracer[0].splines.new('BEZIER')
            spline.bezier_points.add((x.lifetime-1)//stepSize) #add point to spline based on step size
            for t in list(range(int(x.lifetime))):
                bpy.context.scene.frame_set(t+x.birth_time)
                if not t%stepSize:
                    p = spline.bezier_points[t//stepSize]
                    p.co = x.location
                    p.handle_right_type = objectHandle
                    p.handle_left_type = objectHandle
            particlecurve = tracer[1]
            curvelist.append(particlecurve)
        # add to group
        bpy.ops.object.select_all(action='DESELECT')
        for curvename in curvelist:
            curvename.select = True
            bpy.context.scene.objects.active = curvename
            bpy.ops.object.group_link(group="bTrace")
            
        if bTrace.animate:
            bpy.ops.curve.btgrow() # Add grow curve
        
        return{"FINISHED"}


###########################################################################
## Particle Connect
## connect all particles in active system with a continuous animated curve
###########################################################################

class OBJECT_OT_traceallparticles(bpy.types.Operator):
    bl_idname = 'particles.connect'
    bl_label = 'Connect Particles'
    bl_description = 'Create a continuous animated curve from particles in active system'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (bpy.context.object and bpy.context.object.particle_systems)

    def execute(self, context):
        
        obj = bpy.context.object
        ps = obj.particle_systems.active
        set = ps.settings

        # Grids distribution not supported
        if set.distribution == 'GRID':
            self.report('INFO',"Grid distribution mode for particles not supported.")
            return{'FINISHED'}
        
        bTrace = bpy.context.window_manager.curve_tracer
        particleHandle = bTrace.curve_handle # Get Handle selection
        particleSpline = bTrace.curve_spline # Get Spline selection  
        stepSize = bTrace.particle_step    # step size in frames
        particlerez = bTrace.curve_resolution # Get Bevel resolution 
        particledepth = bTrace.curve_depth # Get Bevel Depth
        particleauto = bTrace.particle_auto # Get Auto Time Range
        particle_f_start = bTrace.particle_f_start # Get frame start
        particle_f_end = bTrace.particle_f_end # Get frame end
        if particleHandle == 'AUTOMATIC': # hackish because of naming conflict in api
            particleHandle = 'AUTO'
        if particleHandle == 'FREE_ALIGN':
            particleHandle = 'FREE'        
        tracer = bpy.data.curves.new('Splines','CURVE') # define what kind of object to create
        curve = bpy.data.objects.new('Tracer',tracer) # Create new object with settings listed above
        bpy.context.scene.objects.link(curve) # Link newly created object to the scene
        spline = tracer.splines.new('BEZIER')  # add a new Bezier point in the new curve
        spline.bezier_points.add(set.count-1)
		
        tracer.dimensions = '3D'
        tracer.resolution_u = 32
        tracer.bevel_resolution = particlerez
        tracer.fill_mode = 'FULL'
        tracer.bevel_depth = particledepth

        addtracemat(tracer) #Add material

        if particleauto:
            f_start = int(set.frame_start)
            f_end = int(set.frame_end + set.lifetime)
        else:
            if particle_f_end <= particle_f_start:
                 particle_f_end = particle_f_start + 1
            f_start = particle_f_start
            f_end = particle_f_end
        print ('range: ', f_start, '/', f_end)

        for bFrames in range(f_start, f_end):
            bpy.context.scene.frame_set(bFrames)
            if not (bFrames-f_start) % stepSize:
                print ('done frame: ',bFrames)
                for bFrames in range(set.count):
                    if ps.particles[bFrames].alive_state != 'UNBORN': 
                        e = bFrames
                    bp = spline.bezier_points[bFrames]
                    pt = ps.particles[e]
                    bp.co = pt.location
                    #bp.handle_left = pt.location
                    #bp.handle_right = pt.location
                    bp.handle_right_type = particleHandle
                    bp.handle_left_type = particleHandle 
                    bp.keyframe_insert('co')
                    bp.keyframe_insert('handle_left')
                    bp.keyframe_insert('handle_right')
        # Select new curve
        bpy.ops.object.select_all(action='DESELECT')
        curve .select = True
        bpy.context.scene.objects.active = curve
        if bTrace.animate:
            bpy.ops.curve.btgrow()
        return{'FINISHED'}

################## ################## ################## ############
## Writing Tool
## Writes a curve by animating its point's radii
## 
################## ################## ################## ############
class OBJECT_OT_writing(bpy.types.Operator):
    bl_idname = 'curve.btwriting'
    bl_label = 'Write'
    bl_description = 'Use Grease Pencil to write and convert to curves'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod  ### Removed so panel still draws if nothing is selected
    def poll(cls, context):
        return (context.scene.grease_pencil != None)

    def execute(self, context):
        bTrace, obj = bpy.context.window_manager.curve_tracer, bpy.context.object
        animate = bTrace.animate
        gactive = bpy.context.active_object # set selected object before convert
        bpy.ops.gpencil.convert(type='CURVE')
        gactiveCurve = bpy.context.active_object # get curve after convert
        writeObj = bpy.context.selected_objects
        for i in writeObj:
            bpy.context.scene.objects.active = i
            bpy.ops.curve.btgrow()
            addtracemat(bpy.context.object.data) #Add material
        # Delete grease pencil strokes
        bpy.context.scene.objects.active = gactive
        bpy.ops.gpencil.data_unlink()
        bpy.context.scene.objects.active = gactiveCurve
        # Smooth object
        bpy.ops.object.shade_smooth()
        # Return to first frame
        bpy.context.scene.frame_set(bTrace.anim_f_start)
        
        return{'FINISHED'}

################## ################## ################## ############
## Create Curve
## Convert mesh to curve using either Continuous, All Edges, or Sharp Edges
## Option to create noise
################## ################## ################## ############

class OBJECT_OT_convertcurve(bpy.types.Operator):
    bl_idname = "object.btconvertcurve"
    bl_label = "bTrace: Create Curve"
    bl_description = "Convert mesh to curve using either Continuous, All Edges, or Sharp Edges"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        import bpy, random, mathutils
        from mathutils import Vector

        bTrace = bpy.context.window_manager.curve_tracer
        distort_modscale = bTrace.distort_modscale # add a scale to the modular random 
        distort_curve = bTrace.distort_curve    # modulate the resulting curve
        objectHandle = bTrace.curve_handle # Get Handle selection
        objectSpline = bTrace.curve_spline # Get Spline selection
        objectDupli = bTrace.object_duplicate # Get duplicate check setting
        objectrez = bTrace.curve_resolution # Get Bevel resolution 
        objectdepth = bTrace.curve_depth # Get Bevel Depth
        objectU = bTrace.curve_u # Get Bevel Depth
        objectnoise = bTrace.distort_noise # Get Bevel Depth
        convert_joinbefore = bTrace.convert_joinbefore 
        convert_edgetype = bTrace.convert_edgetype
        traceobjects = bpy.context.selected_objects # create a list with all the selected objects

        obj = bpy.context.object
        
        ### Convert Font
        if obj.type == 'FONT':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.convert(target='CURVE') # Convert edges to curve
            bpy.context.object.data.dimensions = '3D'
            
        # make a continuous edge through all vertices
        if obj.type == 'MESH':
            # Add noise to mesh
            if distort_curve:
                for v in obj.data.vertices:
                    for u in range(3):
                        v.co[u] += objectnoise*(random.uniform(-1,1))

            if convert_edgetype == 'CONTI':
                ## Start Continuous edge
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='EDGE_FACE')
                bpy.ops.mesh.select_all(action='DESELECT')
                verts = bpy.context.object.data.vertices
                bpy.ops.object.mode_set(mode='OBJECT')
                li = []
                p1 = random.randint(0,len(verts)-1) 
                
                for v in verts: 
                    li.append(v.index)
                li.remove(p1)
                for z in range(len(li)):
                    x = []
                    for px in li:
                        d = verts[p1].co - verts[px].co # find distance from first vert
                        x.append(d.length)
                    p2 = li[x.index(min(x))] # find the shortest distance list index
                    verts[p1].select = verts[p2].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.context.tool_settings.mesh_select_mode = [True, False, False]
                    bpy.ops.mesh.edge_face_add()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    # verts[p1].select = verts[p2].select = False #Doesn't work after Bmesh merge
                    li.remove(p2)  # remove item from list.
                    p1 = p2
                # Convert edges to curve
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.convert(target='CURVE') 
            
            if convert_edgetype == 'EDGEALL':
                ## Start All edges
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='ONLY_FACE')
                bpy.ops.object.mode_set()
                bpy.ops.object.convert(target='CURVE')
                for sp in obj.data.splines:
                    sp.type = objectSpline

        obj = bpy.context.object
        # Set spline type to custom property in panel
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.spline_type_set(type=objectSpline) 
        # Set handle type to custom property in panel
        bpy.ops.curve.handle_type_set(type=objectHandle) 
        bpy.ops.object.editmode_toggle()
        obj.data.fill_mode = 'FULL'
        # Set resolution to custom property in panel
        obj.data.bevel_resolution = objectrez 
        obj.data.resolution_u = objectU 
        # Set depth to custom property in panel
        obj.data.bevel_depth = objectdepth 
        # Smooth object
        bpy.ops.object.shade_smooth()
        # Modulate curve radius and add distortion
        if distort_curve: 
            scale = distort_modscale
            if scale == 0:
                return{"FINISHED"}
            for u in obj.data.splines:
                for v in u.bezier_points:
                    v.radius = scale*round(random.random(),3) 
        return{"FINISHED"}


################## ################## ################## ############
## Mesh Follow, trace vertex or faces
## Create curve at center of selection item, extruded along animation
## Needs to be animated mesh!!!
################## ################## ################## ############

class OBJECT_OT_meshfollow(bpy.types.Operator):
    bl_idname = "object.btmeshfollow"
    bl_label = "bTrace: Vertex Trace"
    bl_description = "Trace Vertex or Face on an animated mesh"
    bl_options = {'REGISTER', 'UNDO'}
        
    
    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type in {'MESH'})

    def execute(self, context):
        import bpy, random
        from mathutils import Vector

        bTrace = bpy.context.window_manager.curve_tracer
        distort_modscale = bTrace.distort_modscale  # add a scale to the modular random
        distort_curve = bTrace.distort_curve    # modulate the resulting curve
        objectHandle = bTrace.curve_handle  # Get Handle selection
        objectSpline = bTrace.curve_spline  # Get Spline selection
        objectrez = bTrace.curve_resolution  # Get Bevel resolution
        objectdepth = bTrace.curve_depth  # Get Bevel Depth
        objectU = bTrace.curve_u  # Get curve u
        convert_joinbefore = bTrace.convert_joinbefore 
        stepsize = bTrace.particle_step
        traceobjects = bpy.context.selected_objects  # create a list with all the selected objects

        obj = bpy.context.object
        scn = bpy.context.scene
        meshdata = obj.data
        cursor = bpy.context.scene.cursor_location.copy()  # Store the location to restore at end of script
        drawmethod = bTrace.fol_mesh_type  # Draw from Edges, Verts, or Faces
        if drawmethod == 'VERTS':
            meshobjs = obj.data.vertices
        if drawmethod == 'FACES':
            meshobjs = obj.data.polygons  # untested
        if drawmethod == 'EDGES':
            meshobjs = obj.data.edges  # untested

        # Frame properties
        start_frame, end_frame = bTrace.fol_start_frame, bTrace.fol_end_frame
        if start_frame > end_frame:  # Make sure the math works
            startframe = end_frame - 5  # if start past end, goto (end - 5)
        frames = int((end_frame - start_frame) / stepsize)

        def getsel_option():  # Get selection objects.
            sel = []
            seloption, fol_mesh_type = bTrace.fol_sel_option, bTrace.fol_mesh_type  # options = 'random', 'custom', 'all'
            if fol_mesh_type == 'OBJECT':
                pass
            else:
                if seloption == 'CUSTOM':
                    for i in meshobjs:
                        if i.select == True:
                            sel.append(i.index)
                if seloption == 'RANDOM':
                    for i in list(meshobjs):
                        sel.append(i.index)
                    finalsel = int(len(sel) * bTrace.fol_perc_verts)
                    remove = len(sel) - finalsel
                    for i in range(remove):
                        sel.pop(random.randint(0, len(sel) - 1))
                if seloption == 'ALL':
                    for i in list(meshobjs):
                        sel.append(i.index)

            return sel

        def get_coord(objindex):
            obj_co = []  # list of vector coordinates to use
            frame_x = start_frame
            for i in range(frames):  # create frame numbers list
                scn.frame_set(frame_x)
                if drawmethod != 'OBJECT':
                    followed_item = meshobjs[objindex]
                    if drawmethod == 'VERTS':
                        g_co = obj.matrix_local * followed_item.co  # find Vert vector

                    if drawmethod == 'FACES':
                        g_co = obj.matrix_local * followed_item.normal  # find Face vector

                    if drawmethod == 'EDGES':
                        v1 = followed_item.vertices[0]
                        v2 = followed_item.vertices[1]
                        co1 = bpy.context.object.data.vertices[v1]
                        co2 = bpy.context.object.data.vertices[v2]
                        localcenter = co1.co.lerp(co2.co, 0.5)
                        g_co = obj.matrix_world * localcenter

                if drawmethod == 'OBJECT':
                    g_co = objindex.location.copy()

                obj_co.append(g_co)
                frame_x = frame_x + stepsize

            scn.frame_set(start_frame)
            return obj_co

        def make_curve(co_list):
            tracer = bpy.data.curves.new('tracer','CURVE')
            tracer.dimensions = '3D'
            spline = tracer.splines.new('BEZIER')
            spline.bezier_points.add(len(co_list)-  1)
            curve = bpy.data.objects.new('curve',tracer)
            scn.objects.link(curve)
            curvelist.append(curve)
            # render ready curve
            tracer.resolution_u = 64
            tracer.bevel_resolution = objectrez  # Set bevel resolution from Panel options
            tracer.fill_mode = 'FULL'
            tracer.bevel_depth = objectdepth  # Set bevel depth from Panel options
            bTrace = bpy.context.window_manager.curve_tracer
            objectHandle = bTrace.curve_handle
            if objectHandle == 'AUTOMATIC': # hackish AUTOMATIC doesn't work here
                objectHandle = 'AUTO'

            # move bezier points to objects
            for i in range(len(co_list)):
                p = spline.bezier_points[i]
                p.co = co_list[i]
                p.handle_right_type = objectHandle
                p.handle_left_type = objectHandle
            curve.select = True

        # Run methods
        # Check if bTrace group exists, if not create
        bgroup = bpy.data.groups.keys()
        if 'bTrace' not in bgroup:
            bpy.ops.group.create(name="bTrace") 

        bTrace = bpy.context.window_manager.curve_tracer
        sel = getsel_option()  # Get selection
        curvelist = []  # list to use for grow curve
        
        if bTrace.fol_mesh_type == 'OBJECT':
            vector_list = get_coord(obj)
            make_curve(vector_list)
        else:
            for i in sel:
                vector_list = get_coord(i)
                make_curve(vector_list)

        # Select new curves and add to group
        #bpy.ops.object.select_all(action='DESELECT')
        for curveobject in bpy.context.selected_objects:
            curveobject.select = True
            bpy.context.scene.objects.active = curveobject
            bpy.ops.object.group_link(group="bTrace")
            addtracemat(curveobject.data)
            curveobject.select = False

        if bTrace.animate:  # Add grow curve
            bpy.ops.curve.btgrow()

        obj.select = False  # Deselect original object
        return {'FINISHED'}



###################################################################
#### Add Tracer Material
###################################################################        

def addtracemat(matobj):
    import random
    engine = bpy.context.scene.render.engine
    bTrace = bpy.context.window_manager.curve_tracer
    if bTrace.trace_mat_random:
        mat_color = (random.random(), random.random(), random.random())
    else:
       mat_color = bTrace.trace_mat_color
    #if engine == 'CYCLES':
        # Do cycles mat
    if engine == 'BLENDER_RENDER':
        TraceMat = bpy.data.materials.new('TraceMat')
        TraceMat.diffuse_color = mat_color
        TraceMat.specular_intensity = 0.5
        matobj.materials.append(bpy.data.materials.get('TraceMat'))
    return {'FINISHED'}
        
################## ################## ################## ############
## F-Curve Noise
## will add noise modifiers to each selected object f-curves
## change type to: 'rotation' | 'location' | 'scale' | '' to effect all
## first record a keyframe for this to work (to generate the f-curves)
################## ################## ################## ############

class OBJECT_OT_fcnoise(bpy.types.Operator):
    bl_idname = "object.btfcnoise"
    bl_label = "bTrace: F-curve Noise"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        import bpy, random
        
        bTrace = bpy.context.window_manager.curve_tracer
        amp = bTrace.fcnoise_amp
        timescale = bTrace.fcnoise_timescale
        addkeyframe = bTrace.fcnoise_key
        
        # This sets properties for Loc, Rot and Scale if they're checked in the Tools window
        noise_rot = 'rotation'
        noise_loc = 'location'
        noise_scale = 'scale'
        if not bTrace.fcnoise_rot:
            noise_rot = 'none'
        if not bTrace.fcnoise_loc:
            noise_loc = 'none'
        if not bTrace.fcnoise_scale:
            noise_scale = 'none'
            
        type = noise_loc, noise_rot, noise_scale # Add settings from panel for type of keyframes
        amplitude = amp
        time_scale = timescale
        
        for i in bpy.context.selected_objects:
            # Add keyframes, this is messy and should only add keyframes for what is checked
            if addkeyframe == True:
                bpy.ops.anim.keyframe_insert(type="LocRotScale")         
            for obj in bpy.context.selected_objects:
                if obj.animation_data:
                    for c in obj.animation_data.action.fcurves:
                        if c.data_path.startswith(type):
                            # clean modifiers
                            for m in c.modifiers : 
                                c.modifiers.remove(m)
                            # add noide modifiers
                            n = c.modifiers.new('NOISE')
                            n.strength = amplitude
                            n.scale = time_scale
                            n.phase = random.randint(0,999)
        return{"FINISHED"}

################## ################## ################## ############
## Curve Grow Animation
## Animate curve radius over length of time
################## ################## ################## ############     
class OBJECT_OT_curvegrow(bpy.types.Operator):
    bl_idname = 'curve.btgrow'
    bl_label = 'Run Script'
    bl_description = 'Keyframe points radius'
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type in {'CURVE'})
    
    def execute(self, context):
        bTrace = bpy.context.window_manager.curve_tracer
        anim_f_start, anim_length, anim_auto = bTrace.anim_f_start, bTrace.anim_length, bTrace.anim_auto
        curve_resolution, curve_depth = bTrace.curve_resolution, bTrace.curve_depth
        # make the curve visible
        objs = bpy.context.selected_objects
        for i in objs: # Execute on multiple selected objects
            bpy.context.scene.objects.active = i
            obj = bpy.context.active_object
            try: obj.data.fill_mode = 'FULL'
            except: obj.data.use_fill_front = obj.data.use_fill_back = False
            if not obj.data.bevel_resolution:
                obj.data.bevel_resolution = curve_resolution
            if not obj.data.bevel_depth:
                obj.data.bevel_depth = curve_depth
            if anim_auto:
                anim_f_start = bpy.context.scene.frame_start
                anim_length = bpy.context.scene.frame_end
            # get points data and beautify
            actual, total = anim_f_start, 0
            for sp in obj.data.splines:
                total += len(sp.points) + len(sp.bezier_points)
            step = anim_length / total
            for sp in obj.data.splines:
                sp.radius_interpolation = 'BSPLINE'
                po = [p for p in sp.points] + [p for p in sp.bezier_points]
                if not bTrace.anim_keepr:
                    for p in po: 
                        p.radius = 1
                if bTrace.anim_tails and not sp.use_cyclic_u:
                    po[0].radius = po[-1].radius = 0
                    po[1].radius = po[-2].radius = .65
                ra = [p.radius for p in po]

                # record the keyframes
                for i in range(len(po)):
                    po[i].radius = 0
                    po[i].keyframe_insert('radius', frame=actual)
                    actual += step
                    po[i].radius = ra[i]
                    po[i].keyframe_insert('radius', frame=(actual + bTrace.anim_delay))

                    if bTrace.anim_f_fade:
                        po[i].radius = ra[i]
                        po[i].keyframe_insert('radius', frame=(actual + bTrace.anim_f_fade - step))
                        po[i].radius = 0
                        po[i].keyframe_insert('radius', frame=(actual + bTrace.anim_delay + bTrace.anim_f_fade))

            bpy.context.scene.frame_set(bTrace.anim_f_start)
        return{'FINISHED'}

################## ################## ################## ############
## Remove animation and curve radius data
################## ################## ################## ############
class OBJECT_OT_reset(bpy.types.Operator):
    bl_idname = 'object.btreset'
    bl_label = 'Clear animation'
    bl_description = 'Remove animation / curve radius data'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objs = bpy.context.selected_objects
        for i in objs: # Execute on multiple selected objects
            bpy.context.scene.objects.active = i
            obj = bpy.context.active_object
            obj.animation_data_clear()
            if obj.type == 'CURVE':
                for sp in obj.data.splines:
                    po = [p for p in sp.points] + [p for p in sp.bezier_points]
                    for p in po:
                        p.radius = 1
        return{'FINISHED'}

### Define Classes to register
classes = [TracerProperties,
    addTracerObjectPanel,
    OBJECT_OT_convertcurve,
    OBJECT_OT_objecttrace,
    OBJECT_OT_objectconnect,
    OBJECT_OT_writing,
    OBJECT_OT_particletrace,
    OBJECT_OT_traceallparticles,
    OBJECT_OT_curvegrow,
    OBJECT_OT_reset,
    OBJECT_OT_fcnoise,
    OBJECT_OT_meshfollow
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.WindowManager.curve_tracer = bpy.props.PointerProperty(type=TracerProperties)
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.WindowManager.curve_tracer
if __name__ == "__main__":
    register()
