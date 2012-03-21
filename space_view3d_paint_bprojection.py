bl_info = {
    "name": "BProjection",
    "description": "Help Clone tool",
    "author": "kgeogeo",
    "version": (1, 0),
    "blender": (2, 6, 3),
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/bprojection",
    "tracker_url":"http://projects.blender.org/tracker/index.php?func=detail&aid=30521&group_id=153&atid=468",
    "category": "Paint"}

import bpy
from bpy.types import Panel, Operator
from bpy.props import IntProperty, FloatProperty, BoolProperty, IntVectorProperty, StringProperty, FloatVectorProperty
from bpy_extras import view3d_utils
import math
from math import *
import mathutils
from mathutils import * 

# Main function for align the plan to view
def align_to_view(context):
    ob = context.object        
    rotation = ob.custom_rotation
    scale = ob.custom_scale
    z = ob.custom_z
    pos = [ob.custom_location[0], ob.custom_location[1]]

    reg = context.area.regions[4]        
    width = reg.width
    height = reg.height 
        
    r3d = context.space_data.region_3d        
    r3d.update()
    vl = r3d.view_location
    vr = r3d.view_rotation
    quat = mathutils.Quaternion((0.0, 0.0, 1.0), math.radians(float(rotation)))
        
    v = Vector((1,0,z))
    v.rotate(vr)

    em = bpy.data.objects['Empty for BProjection']
    img = bpy.data.textures['Texture for BProjection'].image
    if img and img.size[1] != 0:
        prop = img.size[0]/img.size[1]
    else: prop = 1    
    
    if ob.custom_linkscale:    
        em.scale = Vector((prop*scale[0], scale[0], 1))
    else:
        em.scale = Vector((prop*scale[0], scale[1], 1))
            
    em.location = view3d_utils.region_2d_to_location_3d(context.area.regions[4], r3d, pos, v)        
    em.rotation_euler = Quaternion.to_euler(vr*quat)

# Function to update the properties
def update_props(self, context):          
    align_to_view(context)

# Function to update the scaleUV
def update_UVScale(self, context):
    v = Vector((0.5,0.5))
    l = Vector((0.0,0.0))
    scale = context.object.custom_scaleuv - context.object.custom_old_scaleuv
    s = context.object.custom_scaleuv
    o = context.object.custom_old_scaleuv 
    uvdata = context.object.data.uv_loop_layers.active.data
    for i in range(484):
        vres =  v - uvdata[len(uvdata)-1-i].uv 
        l.x = vres.x
        l.y = vres.y   

        if context.object.custom_linkscaleuv:
            uvdata[len(uvdata)-1-i].uv = [v.x - l.x/o[0]*s[0], v.y - l.y/o[0]*s[0]]
        else:
            uvdata[len(uvdata)-1-i].uv = [v.x - l.x/o[0]*s[0], v.y - l.y/o[1]*s[1]]    

    context.object.custom_old_scaleuv = context.object.custom_scaleuv
    
    align_to_view(context)

# Function to update the flip horizontal
def update_FlipUVX(self, context):          
    uvdata = context.object.data.uv_loop_layers.active.data
    for i in range(484):
        x = uvdata[len(uvdata)-1-i].uv[0]
        l = 0.5 - x
        uvdata[len(uvdata)-1-i].uv[0] = 0.5 + l
    
    align_to_view(context)

# Function to update the flip vertical
def update_FlipUVY(self, context):          
    uvdata = context.object.data.uv_loop_layers.active.data
    for i in range(484):
        x = uvdata[len(uvdata)-1-i].uv[1]
        l = 0.5 - x
        uvdata[len(uvdata)-1-i].uv[1] = 0.5 + l
    
    align_to_view(context)

# Function to update
def update_Rotation(self, context):              
    if context.object.custom_rotc3d:
        angle = context.object.custom_rotation - context.object.custom_old_rotation
        c3d = context.space_data.cursor_location
        em = bpy.data.objects['Empty for BProjection'].location
        c = c3d
        e = em
        v1 = e-c
        vo = Vector((0.0, 0.0, 1.0))
        vo.rotate(context.space_data.region_3d.view_rotation)
        quat = mathutils.Quaternion(vo, math.radians(float(angle)))        
        quat = quat
        v2 = v1.copy()
        v2.rotate(quat)
        v = v1 - v2
        res = e - v
        context.space_data.region_3d.update()
        x = view3d_utils.location_3d_to_region_2d(context.area.regions[4], context.space_data.region_3d, res)
        y=[round(x[0]), round(x[1])]
        
        context.object.custom_location = y       
    else:
        align_to_view(context)
    context.object.custom_old_rotation = context.object.custom_rotation

# Function to create custom properties
def createcustomprops(context):
    Ob = bpy.types.Object    
    
    # plane properties 
    Ob.custom_location = IntVectorProperty(name="Location", description="Location of the plan",
                                           default=(trunc(context.area.regions[4].width*3/4),trunc( context.area.regions[4].height*3/4)),
                                           subtype = 'XYZ', size=2, update = update_props)
                                           
    Ob.custom_rotation = IntProperty(name="Rotation", description="Rotate the plane",
                                     min=-180, max=180, default=0,update = update_Rotation)
                                     
    Ob.custom_old_rotation = IntProperty(name="old_Rotation", description="Old Rotate the plane",
                                         min=-180, max=180, default=0)
                                         
    Ob.custom_scale = FloatVectorProperty(name="Scales", description="Scale the planes",
                                          subtype = 'XYZ', default=(1.0, 1.0),min = 0.1, size=2,update = update_props)
    Ob.custom_linkscale = BoolProperty(name="linkscale", default=True, update = update_props)
    
    Ob.custom_z = FloatProperty(name="Z", description="Z axis for the plane",
                                min=-10, max=10, default=-1.0,update = update_props)
    
    # UV properties
    Ob.custom_scaleuv = FloatVectorProperty(name="ScaleUV", description="Scale the texture's UV",
                                            default=(1.0,1.0),min = 0.1, subtype = 'XYZ', size=2,update = update_UVScale)    
    Ob.custom_old_scaleuv = FloatVectorProperty(name="old_ScaleUV", description="Scale the texture's UV",
                                                default=(1.0,1.0),min = 0.1, subtype = 'XYZ', size=2)
    Ob.custom_linkscaleuv = BoolProperty(name="linkscaleUV", default=True, update = update_UVScale)
    Ob.custom_flipuvx = BoolProperty(name="flipuvx", default=False, update = update_FlipUVX)
    Ob.custom_flipuvy = BoolProperty(name="flipuvy", default=False, update = update_FlipUVY)
    
    # other properties    
    Ob.custom_c3d = BoolProperty(name="c3d", default=True)
    Ob.custom_rot = BoolProperty(name="rot", default=True)
    Ob.custom_rotc3d = BoolProperty(name="rotc3d", default=False)    


def removecustomprops():    
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_location')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_rotation')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_old_rotation')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_scale')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_z')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_c3d')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_rot')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_rotc3d')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_scaleuv')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_flipuvx')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_flipuvy')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_linkscale')
    except:
        nothing = 0
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_linkscaleuv')
    except:
        nothing = 0 
    try:
        bpy.ops.wm.properties_remove(data_path='object',property='custom_old_scaleuv')
    except:
        nothing = 0        
        

# Draw Class to show the panel
class BProjection(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "BProjection"

    @classmethod
    def poll(cls, context):
        return (context.image_paint_object or context.sculpt_object)

    def draw(self, context):        
        layout = self.layout
                
        try: 
            bpy.data.objects['Empty for BProjection']

            col = layout.column(align =True)
            col.operator("object.removebprojectionplane", text="Remove BProjection plane")
        
            tex = bpy.data.textures['Texture for BProjection']

            layout.template_ID_preview(tex, "image", open="image.open", rows=3, cols=3)
        
            col = layout.column(align =True)
            col.operator('object.applyimage', text="Apply image", icon = 'FILE_TICK')
            col = layout.column(align =True)
            ob = context.object
            col.prop(ob, "custom_c3d",text="Capture Cursor3d", icon='CURSOR')
            col.prop(ob, "custom_rot",text="Rotate around selection", icon='ROTATE')
            col = layout.column(align =True)
            col.prop(ob,'custom_location', text='Plane Properties')
            col.prop(ob,'custom_z') 
            col.prop(ob,'custom_rotation')
            col.prop(ob,'custom_rotc3d',text="Rotate around 3D Cursor",icon='MANIPUL')            
            row = layout.row()
            col = row.column(align =True)
            col.prop(ob,'custom_scale')
            if ob.custom_linkscale :
                col.prop(ob, "custom_linkscale",text="Linked",icon='LINKED')
            else: 
                col.prop(ob, "custom_linkscale",text="Unlinked",icon='UNLINKED')                 
            col = layout.column(align =True)
            col.prop(ob,'custom_scaleuv')
            if ob.custom_linkscaleuv:
                col.prop(ob, "custom_linkscaleuv",text="Linked",icon='LINKED')
            else: 
                col.prop(ob, "custom_linkscaleuv",text="Uninked",icon='UNLINKED') 
            row = layout.row()
            col = row.column(align =True)
            col.prop(ob, "custom_flipuvx",text="Flip X",icon='ARROW_LEFTRIGHT')   
            col = row.column(align =True)
            col.prop(ob, "custom_flipuvy",text="Flip Y",icon='FULLSCREEN_ENTER')            
            col = layout.column(align =True)
            col.prop(ob.material_slots['Material for BProjection'].material,'alpha', slider = True)

        except:
            col = layout.column(align = True)
            col.operator("object.addbprojectionplane", text="Add BProjection plan")             

# Oprerator Class to apply the image to the plane             
class ApplyImage(Operator):
    bl_idname = "object.applyimage"
    bl_label = "Apply image"

    def execute(self, context):        
        img = bpy.data.textures['Texture for BProjection'].image
        em = bpy.data.objects['Empty for BProjection']
        
        bpy.ops.object.editmode_toggle()
        f = context.object.data.polygons
        nbface = len(context.object.data.polygons)
        uvdata = context.object.data.uv_textures.active.data 
        wasnul = False
        if len(uvdata) == 0:
            bpy.ops.object.editmode_toggle()
            uvdata = context.object.data.uv_textures.active.data
            wasnul = True                        
        
        nbcut = 10
        vglen = trunc(pow(nbcut+1, 2))
        
        for i in range(vglen):  
            uvdata[f[nbface-i-1-1].index].image = img
        
        if wasnul == False:
            bpy.ops.object.editmode_toggle()
        else:
            bpy.ops.paint.texture_paint_toggle()
                                   
        context.object.custom_scale = [1,1]                       
        context.object.data.update()
        align_to_view(context)
        
        return {'FINISHED'}

# Oprerator Class to make the 4 or 6 point and scale the plan
class IntuitiveScale(Operator):
    bl_idname = "object.intuitivescale"
    bl_label = "Draw lines"

    def invoke(self, context, event):
        
        x = event.mouse_region_x
        y = event.mouse_region_y                
        if len(context.object.grease_pencil.layers.active.frames) == 0: 
            bpy.ops.gpencil.draw(mode='DRAW', stroke=[{"name":"", "pen_flip":False,
                                                       "is_start":True, "location":(0, 0, 0),
                                                       "mouse":(x,y), "pressure":1, "time":0}])
        else:
            if context.object.custom_linkscale:
                nb_point = 4
            else:
                nb_point = 6
                   
            if len(context.object.grease_pencil.layers.active.frames[0].strokes) < nb_point:
                bpy.ops.gpencil.draw(mode='DRAW', stroke=[{"name":"", "pen_flip":False,
                                                           "is_start":True, "location":(0, 0, 0),
                                                           "mouse":(x,y), "pressure":1, "time":0}])
                                                           
            if len(context.object.grease_pencil.layers.active.frames[0].strokes) == nb_point:
                s = context.object.grease_pencil.layers.active.frames[0]
                v1 = s.strokes[1].points[0].co - s.strokes[0].points[0].co
                if not context.object.custom_linkscale:
                    v2 = s.strokes[4].points[0].co - s.strokes[3].points[0].co
                else:
                    v2 = s.strokes[3].points[0].co - s.strokes[2].points[0].co
                propx = v1.x/v2.x                
                context.object.custom_scale[0] *= abs(propx)
                
                if not context.object.custom_linkscale:
                    v1 = s.strokes[2].points[0].co - s.strokes[0].points[0].co
                    v2 = s.strokes[5].points[0].co - s.strokes[3].points[0].co
                    propy = v1.y/v2.y
                    context.object.custom_scale[1] *= abs(propy)
                bpy.ops.gpencil.active_frame_delete()
        
        return {'FINISHED'}

# Oprerator Class to configure all wath is needed
class AddBProjectionPlane(Operator):
    bl_idname = "object.addbprojectionplane"
    bl_label = "Configure"
    
    def creatematerial(self, context):        
        try:
            matBProjection = bpy.data.materials['Material for BProjection']
        except:            
            bpy.data.textures.new(name='Texture for BProjection',type='IMAGE')
    
            bpy.data.materials.new(name='Material for BProjection')
            
            matBProjection = bpy.data.materials['Material for BProjection']
            matBProjection.texture_slots.add()
            matBProjection.use_shadeless = True
            matBProjection.use_transparency = True
            matBProjection.active_texture = bpy.data.textures['Texture for BProjection']
        
            index = matBProjection.active_texture_index
            matBProjection.texture_slots[index].texture_coords = 'UV'
     
        old_index = context.object.active_material_index
        bpy.ops.object.material_slot_add()
        index = context.object.active_material_index
        context.object.material_slots[index].material = bpy.data.materials['Material for BProjection']
        bpy.ops.object.material_slot_assign()
        context.object.active_material_index = old_index
        context.object.data.update()
            
    def execute(self, context):    
        try:
            bpy.data.objects['Empty for BProjection']

        except:            
            createcustomprops(context)
            bpy.ops.paint.texture_paint_toggle()
            
            context.space_data.show_relationship_lines = False
            
            ob = context.object
        
            bpy.ops.object.add()
            em = context.object
            em.name = "Empty for BProjection"
                        
            bpy.data.scenes['Scene'].objects.active = ob
            ob.select = True
    
            bpy.ops.object.editmode_toggle()
    
            bpy.ops.mesh.primitive_plane_add()
            bpy.ops.object.vertex_group_assign(new = True)
            ob.vertex_groups.active.name = 'texture plane'   
            bpy.ops.uv.unwrap()
            
            bpy.ops.object.editmode_toggle()
            for i in range(4):
                ob.data.edges[len(ob.data.edges)-1-i].crease = 1
            bpy.ops.object.editmode_toggle()

            nbcut = 10
            bpy.ops.mesh.subdivide(number_cuts = nbcut)
    
            em.select = True
            bpy.ops.object.hook_add_selob()
            em.select = False
            em.hide = True   
                     
            self.creatematerial(context)

            bpy.ops.object.applyimage()  
          
            bpy.ops.gpencil.data_add()
            context.object.grease_pencil.draw_mode = 'VIEW'
            bpy.ops.gpencil.layer_add()
            context.object.grease_pencil.layers.active.color = [1.0,0,0]
            
            bpy.ops.object.editmode_toggle()
                    
            km = bpy.data.window_managers['WinMan'].keyconfigs['Blender'].keymaps['3D View']
            km.keymap_items[3-1].idname = 'view3d.rotate_view3d'
            km.keymap_items[19-1].idname = 'view3d.zoom_view3d'
            km.keymap_items[19-1].properties.delta = 1.0
            km.keymap_items[20-1].idname = 'view3d.zoom_view3d'
            km.keymap_items[20-1].properties.delta = -1.0
            km.keymap_items[4-1].idname = 'view3d.pan_view3d'
            km.keymap_items[26-1].idname = 'view3d.preset_view3d'
            km.keymap_items[26-1].properties.view = 'FRONT'
            km.keymap_items[28-1].idname = 'view3d.preset_view3d'
            km.keymap_items[28-1].properties.view = 'RIGHT'            
            km.keymap_items[32-1].idname = 'view3d.preset_view3d'
            km.keymap_items[32-1].properties.view = 'TOP'
            km.keymap_items[34-1].idname = 'view3d.preset_view3d'
            km.keymap_items[34-1].properties.view = 'BACK'
            km.keymap_items[35-1].idname = 'view3d.preset_view3d'
            km.keymap_items[35-1].properties.view = 'LEFT'            
            km.keymap_items[36-1].idname = 'view3d.preset_view3d'
            km.keymap_items[36-1].properties.view = 'BOTTOM'                                   
            km = context.window_manager.keyconfigs.default.keymaps['Image Paint']
            kmi = km.keymap_items.new("object.intuitivescale", 'LEFTMOUSE', 'PRESS', shift=True)
                        
            align_to_view(context)
            
            bpy.ops.paint.texture_paint_toggle()
            
        return {'FINISHED'}

# Oprerator Class to remove what is no more needed    
class RemoveBProjectionPlane(Operator):
    bl_idname = "object.removebprojectionplane"
    bl_label = "Configure"

    def removematerial(self, context):
        i = 0
        for ms in context.object.material_slots:
            if ms.name == 'Material for BProjection':
                index = i
            i+=1
                
        context.object.active_material_index = index
        bpy.ops.object.material_slot_remove()
    
    def execute(self, context):
        try:               
            bpy.ops.paint.texture_paint_toggle()
            
            context.space_data.show_relationship_lines = True
            
            bpy.ops.object.modifier_remove(modifier="Hook-Empty for BProjection")
            
            self.removematerial(context)

            ob = context.object
    
            bpy.ops.object.editmode_toggle()
    
            bpy.ops.mesh.reveal()
                                   
            bpy.ops.mesh.select_all()
            bpy.ops.object.editmode_toggle() 
            if ob.data.vertices[0].select:
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all()
                bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()                    
            
            ob.vertex_groups.active.name = 'texture plane'
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.delete()
            bpy.ops.object.vertex_group_remove()
    
            bpy.ops.object.editmode_toggle()
   
            ob.select = False
                
            em = bpy.data.objects['Empty for BProjection']
            bpy.data.scenes['Scene'].objects.active = em
            em.hide = False
            em.select = True
            bpy.ops.object.delete()
    
            bpy.data.scenes['Scene'].objects.active = ob
            ob.select = True
            
            km = bpy.data.window_managers['WinMan'].keyconfigs['Blender'].keymaps['3D View']
            km.keymap_items[3-1].idname = 'view3d.rotate'
            km.keymap_items[19-1].idname = 'view3d.zoom'
            km.keymap_items[19-1].properties.delta = 1.0
            km.keymap_items[20-1].idname = 'view3d.zoom'
            km.keymap_items[20-1].properties.delta = -1.0
            km.keymap_items[4-1].idname = 'view3d.move'
            km.keymap_items[26-1].idname = 'view3d.viewnumpad'
            km.keymap_items[26-1].properties.type = 'FRONT'
            km.keymap_items[28-1].idname = 'view3d.viewnumpad'
            km.keymap_items[28-1].properties.type = 'RIGHT'            
            km.keymap_items[32-1].idname = 'view3d.viewnumpad'
            km.keymap_items[32-1].properties.type = 'TOP'
            km.keymap_items[34-1].idname = 'view3d.viewnumpad'
            km.keymap_items[34-1].properties.type = 'BACK'
            km.keymap_items[35-1].idname = 'view3d.viewnumpad'
            km.keymap_items[35-1].properties.type = 'LEFT'            
            km.keymap_items[36-1].idname = 'view3d.viewnumpad'
            km.keymap_items[36-1].properties.type = 'BOTTOM'            
            
            km = context.window_manager.keyconfigs.default.keymaps['Image Paint']
            for kmi in km.keymap_items:
                if kmi.idname in ["object.intuitivescale"]:
                    km.keymap_items.remove(kmi)
            
            bpy.ops.paint.texture_paint_toggle()
            removecustomprops()
                    
        except:
            nothing = 0
        
        return {'FINISHED'}

# Oprerator Class to rotate the view3D
class RotateView3D(Operator):
    bl_idname = "view3d.rotate_view3d"
    bl_label = "Rotate the View3D"
    
    first_mouse_x = 0
    first_mouse_y = 0 

    panx = 0
    pany = 0

    rkey = False
    skey = False
    gkey = False
    zkey = False
    ukey = False
    ckey = False
    first_time = True
    
    def vect_sphere(self, context, mx, my):
        width = context.area.regions[4].width
        height = context.area.regions[4].height
           
        if width >= height:
            ratio = height/width
        
            x = 2*mx/width
            y = 2*ratio*my/height
            
            x = x - 1
            y = y - ratio
        else:
            ratio = width/height
        
            x = 2*ratio*mx/width
            y = 2*my/height
 
            x = x - ratio
            y = y - 1
        
        z2 = 1 - x * x - y * y
        if z2 > 0:
            z= sqrt(z2)
        else : z=0
            
        p = Vector((x, y, z))
        p.normalize()
        return p
    
    def tracball(self, context, mx, my, origine):
        pos_init_cursor = view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, context.space_data.cursor_location)        
        if context.object.custom_rot:
            pos_init = view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, origine)
            context.space_data.region_3d.view_location = origine
        
        v1 = self.vect_sphere(context, self.first_mouse_x, self.first_mouse_y)
        v2 = self.vect_sphere(context, mx, my)
                        
        axis = Vector.cross(v1,v2);
        angle = Vector.angle(v1,v2);
            
        q =  Quaternion(axis,-2*angle)
                        
        context.space_data.region_3d.view_rotation *=q
        context.space_data.region_3d.update()
        
        if context.object.custom_rot:
            pos_end = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, pos_init, Vector((0,0,0)))                
            context.space_data.region_3d.view_location =  -1*pos_end

        if context.object.custom_c3d:
            context.space_data.region_3d.update()       
            context.space_data.cursor_location = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, pos_init_cursor, Vector((0,0,0)))
        
        self.first_mouse_x = mx
        self.first_mouse_y = my
                
    def modal(self, context, event):                                
        if event.value == 'PRESS':
            self.panx = event.mouse_region_x
            self.pany = event.mouse_region_y
                    
            if event.type == 'S':
                self.skey = True
            
            if event.type == 'R':
                self.rkey = True    

            if event.type == 'G':
                self.gkey = True

            if event.type == 'Z':
                self.zkey = True            

            if event.type == 'U':
                self.ukey = True 

            if event.type == 'C':
                self.ckey = True 
                            
        if event.value == 'RELEASE':
            if event.type == 'S':
                self.skey = False
            
            if event.type == 'R':
                self.rkey = False
            
            if event.type == 'G':
                self.gkey = False            

            if event.type == 'Z':
                self.zkey = False 

            if event.type == 'U':
                self.ukey = False                 

            if event.type == 'C':
                self.ckey = False             

        if event.type == 'MOUSEMOVE':                        
            
            if self.rkey == False and self.skey == False and self.gkey == False and self.zkey == False and self.ukey == False:
                self.tracball(context, event.mouse_region_x, event.mouse_region_y,context.object.location)
                align_to_view(context)
                if self.first_time:
                    rot_ang = context.user_preferences.view.rotation_angle            
                    context.user_preferences.view.rotation_angle = 0
                    bpy.ops.view3d.view_orbit(type='ORBITLEFT')
                    context.user_preferences.view.rotation_angle = rot_ang   
                    bpy.ops.view3d.view_persportho()         
                    bpy.ops.view3d.view_persportho()
                    self.first_time = False
          
            deltax = event.mouse_region_x - self.panx
            deltay = event.mouse_region_y - self.pany           

            if self.rkey == False and self.skey == False and self.gkey == True and self.zkey == False and self.ukey == False:       
                cl = context.object.custom_location
                context.object.custom_location = [cl[0] + deltax,cl[1] + deltay]               
                                   
            if self.rkey == False and self.skey == True and self.gkey == False and self.zkey == False and self.ukey == False:                
                s = context.object.custom_scale
                context.object.custom_scale = [s[0] + deltax/20, s[1] + deltay/20]
                                          
            if self.rkey == False and self.skey == False and self.gkey == False and self.zkey == True and self.ukey == False:                
                context.object.custom_z+=deltax/10
                      
            if self.rkey == True and self.skey == False and self.gkey == False and self.zkey == False and self.ukey == False:
                context.object.custom_rotation+=deltax
                    
            if self.rkey == False and self.skey == False and self.gkey == False and self.zkey == False and self.ukey == True:
                suv = context.object.custom_scaleuv
                context.object.custom_scaleuv[0]= [suv + deltax/10 , suv + deltay/10]               

            self.panx = event.mouse_region_x
            self.pany = event.mouse_region_y
            self.first_mouse_x = event.mouse_region_x
            self.first_mouse_y = event.mouse_region_y
            
        elif event.type == 'MIDDLEMOUSE'and event.value == 'RELEASE':       
            
            return {'FINISHED'}
        
        if self.ckey:
            if self.skey:
                context.object.custom_scale = [1,1]
            if self.rkey:
                context.object.custom_rotation = 0
            return {'RUNNING_MODAL'}
                    
        return {'RUNNING_MODAL'}
    
    def execute(self, context):        
        align_to_view(context)  
        
        return{'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.first_mouse_x = event.mouse_region_x
        self.first_mouse_y = event.mouse_region_y
        self.first_time = True
        
        return {'RUNNING_MODAL'}

# Oprerator Class to pan the view3D
class PanView3D(bpy.types.Operator):
    bl_idname = "view3d.pan_view3d"
    bl_label = "Pan View3D"

    
    first_mouse_x = 0
    first_mouse_y = 0 

    panx = 0
    pany = 0

    def modal(self, context, event):
        width = context.area.regions[4].width
        height = context.area.regions[4].height

        deltax = event.mouse_region_x - self.first_mouse_x
        deltay = event.mouse_region_y - self.first_mouse_y                
               
        l =  context.space_data.region_3d
        vr = l.view_rotation
        
        v = Vector((deltax/max(width,height),deltay/max(width,height),0))
        v.rotate(vr)
        
        pos = [0,0]
        v1 = view3d_utils.region_2d_to_location_3d(context.region, l, pos, v)
        pos = [width,height]
        v2 = view3d_utils.region_2d_to_location_3d(context.region, l, pos, v)
        
        v3 = (v2 - v1)
        
        pos_init_cursor = view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, context.space_data.cursor_location)
        
        context.space_data.region_3d.view_location -= v*v3.length
        
        context.space_data.region_3d.update()       
        context.space_data.cursor_location = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, pos_init_cursor, Vector((0,0,0)))
            
        align_to_view(context)

        self.first_mouse_x = event.mouse_region_x
        self.first_mouse_y = event.mouse_region_y

        if event.type == 'MIDDLEMOUSE'and event.value == 'RELEASE':
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
                
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.first_mouse_x = event.mouse_region_x
        self.first_mouse_y = event.mouse_region_y   
        
        return {'RUNNING_MODAL'}

    def execute(self, context):        
        align_to_view(context)  
        
        return{'FINISHED'}

# Oprerator Class to zoom the view3D
class ZoomView3D(Operator):
    bl_idname = "view3d.zoom_view3d"
    bl_label = "Zoom View3D"

    delta = FloatProperty(
        name="delta",
        description="Delta",
        min=-1.0, max=1,
        default=1.0,
        )

    def invoke(self, context, event):                   
        bpy.ops.view3d.zoom(delta = self.delta)
        
        align_to_view(context)
        
        return {'FINISHED'}

    def execute(self, context):        
        align_to_view(context)
        
        return{'FINISHED'}

# Oprerator Class to use numpad shortcut
class PresetView3D(Operator):
    bl_idname = "view3d.preset_view3d"
    bl_label = "Preset View3D"

    view = StringProperty(name="View", description="Select the view", default='TOP',)

    def invoke(self, context, event):                   
        origine = context.object.location
        
        pos_init_cursor = view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, context.space_data.cursor_location)

        if context.object.custom_rot:
            pos_init = view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, origine)
            context.space_data.region_3d.view_location = origine

        tmp = context.user_preferences.view.smooth_view
        context.user_preferences.view.smooth_view = 0
        bpy.ops.view3d.viewnumpad(type=self.view)        
        align_to_view(context)
        context.user_preferences.view.smooth_view = tmp

        if context.object.custom_rot:
            pos_end = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, pos_init, Vector((0,0,0)))                
            context.space_data.region_3d.view_location =  -1*pos_end
            align_to_view(context)

        if context.object.custom_c3d:
            context.space_data.region_3d.update()       
            context.space_data.cursor_location = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, pos_init_cursor, Vector((0,0,0)))        
                    
        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
   
       