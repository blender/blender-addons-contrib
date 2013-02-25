bl_info = {
    "name": "BProjection",
    "description": "Help Clone tool",
    "author": "kgeogeo",
    "version": (2, 0),
    "blender": (2, 66, 0),
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/bprojection",
    "tracker_url":"http://projects.blender.org/tracker/index.php?func=detail&aid=30521&group_id=153&atid=468",
    "category": "Paint"}

import bpy
from bpy.app.handlers import persistent
from bpy.types import Panel, Operator
from bpy.props import IntProperty, FloatProperty, BoolProperty, IntVectorProperty, StringProperty, FloatVectorProperty, CollectionProperty
from bpy_extras import view3d_utils
import math
from math import *
import mathutils
from mathutils import *


# Oprerator Class to rotate the view3D
class RotateView3D(Operator):
    bl_idname = "view3d.rotate_view3d"
    bl_label = "Rotate the View3D"
    
    first_mouse = Vector((0,0))
    
    def turnable(self, context, mx, my, origine):
        sd = context.space_data
        vz = Vector((0,0,1))
        qz =  Quaternion(vz,-(mx-self.first_mouse.x)*pi/180)
        sd.region_3d.view_rotation.rotate(qz)
        sd.region_3d.update()

        vx = Vector((1,0,0))
        vx.rotate(sd.region_3d.view_rotation)        
        qx =  Quaternion(vx,(my-self.first_mouse.y)*pi/180)        
        sd.region_3d.view_rotation.rotate(qx)                
        sd.region_3d.update()
                
        self.first_mouse = Vector((mx, my))
                
    def modal(self, context, event):                                

        reg = context.region        

        if event.type == 'MOUSEMOVE':  
            self.turnable(context, event.mouse_region_x, event.mouse_region_y,Vector((0,0,0)))
        if event.type == 'ESC':
            return {'FINISHED'}   
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.first_mouse = Vector((event.mouse_region_x,event.mouse_region_y))

        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_module(__name__)
    km = bpy.data.window_managers['WinMan'].keyconfigs['Blender'].keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.idname == 'view3d.rotate':
            kmi.idname = 'view3d.rotate_view3d'

def unregister():
    bpy.utils.unregister_module(__name__)
    km = bpy.data.window_managers['WinMan'].keyconfigs['Blender'].keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.idname == 'view3d.rotate_view3d':
            kmi.idname = 'view3d.rotate'  

if __name__ == "__main__":
    register()
