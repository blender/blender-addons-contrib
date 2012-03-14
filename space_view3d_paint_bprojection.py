bl_info = {
    "name": "BProjection",
    "description": "Help Clone tool",
    "author": "kgeogeo",
    "version": (1, 0),
    "blender": (2, 6, 3),
    "category": "Paint"}

import bpy
from bpy.types import Panel, Operator
from bpy.props import IntProperty, FloatProperty, BoolProperty, IntVectorProperty, StringProperty
from bpy_extras import view3d_utils
from mathutils import *
from math import * 
import mathutils
import math

def align_to_view(context):
    ob = context.object        
    rotation = ob.custom_rotation
    scale = ob.custom_scale
    z = ob.custom_z
    posx = ob.custom_location[0]
    posy = ob.custom_location[1]

    reg = bpy.context.area.regions[4]        
    width = reg.width
    height = reg.height 
        
    r3d =  context.space_data.region_3d        
    r3d.update()
    vl = r3d.view_location
    vr = r3d.view_rotation
    quat = mathutils.Quaternion((0.0, 0.0, 1.0), math.radians(float(rotation)))
        
    v = Vector((1,0,z))
    v.rotate(vr)

    pos = (posx,posy) 

    em = bpy.data.objects['Empty for clone']
    img = bpy.data.textures['Texture for clone'].image
    if img and img.size[1] != 0:
        prop = img.size[0]/img.size[1]
        em.scale[0] = prop
    else: prop = 1    
        
    em.scale =  Vector((prop*scale, scale, scale))
    em.location = view3d_utils.region_2d_to_location_3d(context.area.regions[4], r3d, pos, v)        
    em.rotation_euler = Quaternion.to_euler(vr*quat)

class HelpClone(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Help Clone"

    @classmethod
    def poll(cls, context):
        return (context.image_paint_object)

    def draw(self, context):        
        layout = self.layout
                
        try: 
            bpy.data.objects['Empty for clone']

            col = layout.column(align =True)
            col.operator("object.removecloneplane", text="Remove clone plane")
        
            tex = bpy.data.textures['Texture for clone']

            layout.template_ID_preview(tex, "image", open="image.open", rows=3, cols=3)
        
            col = layout.column(align =True)
            col.operator('object.applyimage', text = "Apply image")
            col = layout.column(align =True)
            ob = context.object
            col.prop(ob, "custom_c3d",text="Capture Cursor3d")
            col.prop(ob, "custom_rot",text="Rotate around selection")
            col = layout.column(align =True)
            col.prop(ob,'custom_rotation', slider = True)
            col.prop(ob,'custom_scale', slider = True) 
            col.prop(ob,'custom_z', slider = True) 
            col.prop(ob,'custom_location')
            col = layout.column(align =True)
            col.prop(ob,'custom_scaleuv', slider = True)
            col = layout.column(align =True)
            col.prop(ob.material_slots['Material for clone'].material,'alpha', slider = True)

        except:
            col = layout.column(align =True)
            col.operator("object.addcloneplane", text="Add clone plan")             
                
class ApplyImage(Operator):
    bl_idname = "object.applyimage"
    bl_label = "Apply image"

    def execute(self, context):        
        img = bpy.data.textures['Texture for clone'].image
        em = bpy.data.objects['Empty for clone']
        uvdata = bpy.context.object.data.uv_textures.active.data        
        uvdata[len(uvdata)-1].image = img
        if img and img.size[1] != 0:        
            prop = img.size[0]/img.size[1]                
            em.scale[0] = prop
            
        context.object.data.update()
        align_to_view(context)
        
        return {'FINISHED'}

class DrawLines(Operator):
    bl_idname = "object.drawlines"
    bl_label = "Draw lines"

    def invoke(self, context, event):
        
        x = event.mouse_region_x
        y = event.mouse_region_y                
        if len(bpy.context.object.grease_pencil.layers.active.frames)==0: 
            bpy.ops.gpencil.draw(mode='DRAW', stroke=[{"name":"", "pen_flip":False,
                                                                "is_start":True, "location":(0, 0, 0),
                                                                "mouse":(x,y), "pressure":1, "time":0}])
        else:
            if len(bpy.context.object.grease_pencil.layers.active.frames[0].strokes) < 4:
                bpy.ops.gpencil.draw(mode='DRAW', stroke=[{"name":"", "pen_flip":False,
                                                                    "is_start":True, "location":(0, 0, 0),
                                                                    "mouse":(x,y), "pressure":1, "time":0}])
            if len(bpy.context.object.grease_pencil.layers.active.frames[0].strokes) == 4:
                s = bpy.context.object.grease_pencil.layers.active.frames[0]
                v1 = s.strokes[1].points[0].co - s.strokes[0].points[0].co
                v2 = s.strokes[3].points[0].co - s.strokes[2].points[0].co
                prop = v1.x/v2.x
                bpy.context.object.custom_scale *= abs(prop)
                bpy.ops.gpencil.active_frame_delete()
        
        return {'FINISHED'}

class AddClonePlane(Operator):
    bl_idname = "object.addcloneplane"
    bl_label = "Configure"
    
    def creatematerial(self, context):        
        try:
            matclone = bpy.data.materials['Material for clone']
        except:            
            bpy.data.textures.new(name='Texture for clone',type='IMAGE')
    
            bpy.data.materials.new(name='Material for clone')
            
            matclone = bpy.data.materials['Material for clone']
            matclone.texture_slots.add()
            matclone.use_shadeless = True
            matclone.use_transparency = True
            matclone.active_texture = bpy.data.textures['Texture for clone']
        
            index = matclone.active_texture_index
            matclone.texture_slots[index].texture_coords = 'UV'
     
        old_index = context.object.active_material_index
        bpy.ops.object.material_slot_add()
        index = context.object.active_material_index
        bpy.context.object.material_slots[index].material = bpy.data.materials['Material for clone']
        bpy.ops.object.material_slot_assign()
        context.object.active_material_index = old_index
            
    def execute(self, context):    
        try:
            bpy.data.objects['Empty for clone']

        except:            
            bpy.ops.paint.texture_paint_toggle()
            
            bpy.context.space_data.show_relationship_lines = False
            
            ob = bpy.context.object
        
            bpy.ops.object.add()
            em = bpy.context.object
            em.name = "Empty for clone"
                        
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
    
            em.select = True
            bpy.ops.object.hook_add_selob()
            
            self.creatematerial(context)
            
            bpy.ops.gpencil.data_add()
            bpy.context.object.grease_pencil.draw_mode = 'VIEW'
            bpy.ops.gpencil.layer_add()
            bpy.context.object.grease_pencil.layers.active.color = [1.0,0,0]

            bpy.ops.mesh.hide()
            
            em.select = False
            em.hide = True
            
            bpy.ops.object.editmode_toggle()
                    
            bpy.ops.object.applyimage()
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
            km = bpy.context.window_manager.keyconfigs.default.keymaps['Image Paint']
            kmi = km.keymap_items.new("object.drawlines", 'LEFTMOUSE', 'PRESS', shift=True)
                        
            align_to_view(context)
            
            bpy.ops.paint.texture_paint_toggle()
            
        return {'FINISHED'}
    
class RemoveClonePlane(Operator):
    bl_idname = "object.removecloneplane"
    bl_label = "Configure"

    def removematerial(self, context):
        i = 0
        for ms in context.object.material_slots:
            if ms.name == 'Material for clone':
                index = i
            i+=1
                
        context.object.active_material_index = index
        bpy.ops.object.material_slot_remove()
    
    def execute(self, context):
        try:               
            bpy.ops.paint.texture_paint_toggle()
            
            context.space_data.show_relationship_lines = True
            
            bpy.ops.object.modifier_remove(modifier="Hook-Empty for clone")
            
            self.removematerial(context)

            ob = bpy.context.object
    
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
                
            em = bpy.data.objects['Empty for clone']
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
            
            km = bpy.context.window_manager.keyconfigs.default.keymaps['Image Paint']
            for kmi in km.keymap_items:
                if kmi.idname in ["object.drawlines"]:
                    km.keymap_items.remove(kmi)
            
            bpy.ops.paint.texture_paint_toggle()
                    
        except:
            nothing
        
        return {'FINISHED'}

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
    first_time = True
    
    def vect_sphere(self,mx,my):
        width = bpy.context.area.regions[4].width
        height = bpy.context.area.regions[4].height
           
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
    
    def tracball(self,mx,my,origine):
        pos_init_cursor = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, bpy.context.space_data.cursor_location)        
        if bpy.context.object.custom_rot:
            pos_init = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, origine)
            bpy.context.space_data.region_3d.view_location = origine
        
        v1 = self.vect_sphere(self.first_mouse_x,self.first_mouse_y)
        v2 = self.vect_sphere(mx,my)
                        
        axis = Vector.cross(v1, v2);
        angle = Vector.angle(v1, v2);
            
        q =  Quaternion(axis,-2*angle)
                        
        bpy.context.space_data.region_3d.view_rotation *=q
        bpy.context.space_data.region_3d.update()
        
        if bpy.context.object.custom_rot:
            pos_end = view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, pos_init, Vector((0,0,0)))                
            bpy.context.space_data.region_3d.view_location =  -1*pos_end

        if bpy.context.object.custom_c3d:
            bpy.context.space_data.region_3d.update()       
            bpy.context.space_data.cursor_location = view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, pos_init_cursor, Vector((0,0,0)))
        
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
            
        if event.type == 'MOUSEMOVE':                        
            
            if self.rkey == False and self.skey == False and self.gkey == False and self.zkey == False and self.ukey == False:
                self.tracball(event.mouse_region_x,event.mouse_region_y,bpy.context.object.location)
                align_to_view(context)
                if self.first_time:
                    rot_ang = bpy.context.user_preferences.view.rotation_angle            
                    bpy.context.user_preferences.view.rotation_angle = 0
                    bpy.ops.view3d.view_orbit(type='ORBITLEFT')
                    bpy.context.user_preferences.view.rotation_angle = rot_ang   
                    bpy.ops.view3d.view_persportho()         
                    bpy.ops.view3d.view_persportho()
                    self.first_time = False
          
            deltax = event.mouse_region_x - self.panx
            deltay = event.mouse_region_y - self.pany           

            if self.rkey == False and self.skey == False and self.gkey == True and self.zkey == False and self.ukey == False:       
                bpy.context.object.custom_location[0]+=deltax
                bpy.context.object.custom_location[1]+=deltay                
                                   
            if self.rkey == False and self.skey == True and self.gkey == False and self.zkey == False and self.ukey == False:                
                bpy.context.object.custom_scale+=deltax/10
                                          
            if self.rkey == False and self.skey == False and self.gkey == False and self.zkey == True and self.ukey == False:                
                bpy.context.object.custom_z+=deltax/10
                      
            if self.rkey == True and self.skey == False and self.gkey == False and self.zkey == False and self.ukey == False:
                bpy.context.object.custom_rotation+=deltax

            if self.rkey == False and self.skey == False and self.gkey == False and self.zkey == False and self.ukey == True:
                bpy.context.object.custom_scaleuv+=deltax/10                

            self.panx = event.mouse_region_x
            self.pany = event.mouse_region_y
            self.first_mouse_x = event.mouse_region_x
            self.first_mouse_y = event.mouse_region_y
            
        elif event.type == 'MIDDLEMOUSE'and event.value == 'RELEASE':

            return {'FINISHED'}
        
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

class PresetView3D(Operator):
    bl_idname = "view3d.preset_view3d"
    bl_label = "Preset View3D"

    view = StringProperty(name="View", description="Select the view", default='TOP',)

    def invoke(self, context, event):                   
        origine = bpy.context.object.location
        
        pos_init_cursor = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, bpy.context.space_data.cursor_location)

        if bpy.context.object.custom_rot:
            pos_init = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, origine)
            bpy.context.space_data.region_3d.view_location = origine

        tmp = bpy.context.user_preferences.view.smooth_view
        bpy.context.user_preferences.view.smooth_view = 0
        bpy.ops.view3d.viewnumpad(type=self.view)        
        align_to_view(context)
        bpy.context.user_preferences.view.smooth_view = tmp

        if bpy.context.object.custom_rot:
            pos_end = view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, pos_init, Vector((0,0,0)))                
            bpy.context.space_data.region_3d.view_location =  -1*pos_end
            align_to_view(context)

        if bpy.context.object.custom_c3d:
            bpy.context.space_data.region_3d.update()       
            bpy.context.space_data.cursor_location = view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, pos_init_cursor, Vector((0,0,0)))        
                    
        return {'FINISHED'}


class PanView3D(bpy.types.Operator):
    bl_idname = "view3d.pan_view3d"
    bl_label = "Pan View3D"

    
    first_mouse_x = 0
    first_mouse_y = 0 

    panx = 0
    pany = 0

    def modal(self, context, event):
        width = bpy.context.area.regions[4].width
        height = bpy.context.area.regions[4].height

        deltax = event.mouse_region_x - self.first_mouse_x
        deltay = event.mouse_region_y - self.first_mouse_y                
               
        l =  bpy.context.space_data.region_3d
        vr = l.view_rotation
        
        v = Vector((deltax/max(width,height),deltay/max(width,height),0))
        v.rotate(vr)
        
        pos = [0,0]
        v1 = view3d_utils.region_2d_to_location_3d(bpy.context.region, l, pos, v)
        pos = [width,height]
        v2 = view3d_utils.region_2d_to_location_3d(bpy.context.region, l, pos, v)
        
        v3 = (v2 - v1)
        
        pos_init_cursor = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, bpy.context.space_data.cursor_location)
        
        bpy.context.space_data.region_3d.view_location -= v*v3.length
        
        bpy.context.space_data.region_3d.update()       
        bpy.context.space_data.cursor_location = view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, pos_init_cursor, Vector((0,0,0)))
            
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

def update_func(self, context):          
    v = Vector((0.5,0.5))
    for i in range(4):
        vres =  v - bpy.context.object.data.uv_loop_layers.active.data[len(bpy.context.object.data.uv_loop_layers.active.data)-1-i].uv 
        vres /= vres.length
        for j in range(2):
            if abs(vres[j-1])>0:
                vres[j-1] /= abs(vres[j-1])
        bpy.context.object.data.uv_loop_layers.active.data[len(bpy.context.object.data.uv_loop_layers.active.data)-1-i].uv = v - vres*bpy.context.object.custom_scaleuv/2
    
    align_to_view(context)

def createcustomprops():
    Ob = bpy.types.Object    
    Ob.custom_rotation = IntProperty(name="Rotation", description="Rotate the plane", min=-180, max=180, default=0,update = update_func)
    Ob.custom_scale = FloatProperty(name="Scale", description="Scale the plane", min=0, max=10, default=1.0,update = update_func)
    Ob.custom_z = FloatProperty(name="Z", description="Z axis for the plane", min=-10, max=10, default=-1.0,update = update_func)
    Ob.custom_scaleuv = FloatProperty(name="ScaleUV", description="Scale the texture's UV", min=1.0, max=10, default=1.0,update = update_func)
    Ob.custom_location = IntVectorProperty(name="Location", description="Location of the plan", default=(0, 0), subtype = 'XYZ', size=2, update = update_func)
    Ob.custom_c3d = BoolProperty(name="c3d", default=True)
    Ob.custom_rot = BoolProperty(name="rot", default=True)

def register():
    bpy.utils.register_module(__name__)
    createcustomprops()

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
   
       
