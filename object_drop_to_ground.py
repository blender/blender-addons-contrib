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
    "name": "Drop to ground",
    "author": "Unnikrishnan(kodemax), Florian Meyer(testscreenings)",
    "version": (1, 1),
    "blender": (2, 5, 9),
    "location": "Tool shelf",
    "description": "Drops the selected objects to the active object",
    "warning": "Before using it do :- ctrl+a -> apply rotation on the object to be dropped",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Object/Drop_to_ground",
    "tracker_url": "http://projects.blender.org/tracker/?func=detail&atid=467&aid=25349",
    "category": "Object"}
 
import bpy , random
from bpy.props import *
import mathutils
import math
 
def get_align_matrix(location, normal):
    up = mathutils.Vector((0,0,1))                      
    angle = normal.angle(up)
    axis = up.cross(normal)                            
    mat_rot = mathutils.Matrix.Rotation(angle, 4, axis) 
    mat_loc = mathutils.Matrix.Translation(location)
    mat_align = mat_rot * mat_loc                      
    return mat_align


def get_lowest_Coord1(ob):
    matrix = ob.matrix_world.copy()
    verts = ob.data.vertices
    lowest = mathutils.Vector((0,0,10000))
    for vert in verts:
        if (matrix * vert.co).z < lowest.z:
            lowest = matrix * vert.co
    return lowest


def do_drop(context,tmpObj, ob):
    print('\n', ob.name)
    align_object = context.scene.align_object
    use_center = context.scene.use_center
    lowest = get_lowest_Coord1(ob)
    location, normal, index = tmpObj.ray_cast(lowest, lowest + mathutils.Vector((0,0,-10000)))
        
    if not index == -1:
        if not use_center:
            temp = (bpy.context.scene.cursor_location).copy()
            bpy.context.scene.cursor_location = lowest
            bpy.ops.object.origin_set(type = 'ORIGIN_CURSOR')
            
        if align_object:
            sca = ob.scale.copy()
            mat_align = get_align_matrix(location, normal)
            ob.matrix_world = mat_align
            ob.scale = sca 
            
        else:
            ob.location = location
         
        
        if not use_center:
            bpy.context.scene.cursor_location = temp
            bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
   
    else:
        print('\nno hit')
        return    

# compute randomisation based on the general or specific percentage chosen
# if the specific percentage is zero then the general percentage is used
def compute_percentage(min,max,value,percentage):
    range = max-min
    general_percentage = 100
    
    if percentage == 0:
        percentage_random = ( value -((range*(general_percentage/100))/2) )+ (range * (general_percentage / 100) * random.random())
    else:
        percentage_random = ( value - ((range*(percentage/100))/2)) + (range * (percentage / 100) * random.random())
         
    if percentage_random > max:
        percentage_random = max
    if percentage_random < min:
        percentage_random = min
    
    return percentage_random 

def main(self, context):

    print('\n_______START__________')
    obs = bpy.context.selected_objects
    ground = bpy.context.active_object
    obs.remove(ground)
    context = bpy.context
    sc = context.scene


    tmpMesh = ground.to_mesh(sc, True, 'PREVIEW')
    tmpMesh.transform(ground.matrix_world)
    tmpObj = bpy.data.objects.new('tmpGround', tmpMesh)
    """tmpObj.update(sc, 1, 1, 1)"""
    sc.objects.link(tmpObj)
    sc.update()

    for ob in obs:
        bpy.ops.object.select_all(action='DESELECT')
        ob.select = True
        
        #randomise location it its enabled
        if sc.random_loc :
            print("randomising the location of object : ", ob.name)
            print("current location :" + str(ob.location))
            bpy.ops.transform.translate(value=(compute_percentage(sc.rl_min_x,sc.rl_max_x,0,100),
                           compute_percentage(sc.rl_min_y,sc.rl_max_y,0,100),
                           compute_percentage(sc.rl_min_z,sc.rl_max_z,0,100)))
            print("randomised location : ", str(ob.location))
        do_drop(context, tmpObj, ob)

    bpy.ops.object.select_all(action='DESELECT')
    tmpObj.select = True
    bpy.ops.object.delete('EXEC_DEFAULT')

    for ob in obs:
        ob.select = True
    ground.select = True

 
class VIEW3D_PT_tools_drop_to_ground(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Drop to ground"
    bl_context = "objectmode"

    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout
        col = layout.column(align=True)
        col.operator("object.drop_to_ground", text="Drop")
        col.prop(context.scene, "align_object")
        col.prop(context.scene, "use_center")
        box= layout.box()
        box.prop(context.scene, "random_loc")
        
        # random location gui appears only if its enabled
        if bpy.context.scene.random_loc:
            
            row = box.row()
            row.label(text="(X,Y,Z) [min/max]")
            row = box.row()
            a = row.split(percentage = 0.5, align = True)
            a.prop(context.scene, "rl_min_x")
            a.prop(context.scene, "rl_max_x")
            row = box.row()
            b = row.split(percentage = 0.5, align = True)
            b.prop(context.scene, "rl_min_y")
            b.prop(context.scene, "rl_max_y")
            row = box.row()
            b = row.split(percentage = 0.5, align = True)
            b.prop(context.scene, "rl_min_z")
            b.prop(context.scene, "rl_max_z")
        
class OBJECT_OT_drop_to_ground(bpy.types.Operator):
    """Drop to ground"""
    bl_idname = "object.drop_to_ground"
    bl_label = "Drop to ground"
    bl_description = "Drops selected objects onto the active object"
    bl_options = {'REGISTER', 'UNDO'}
 
    def execute(self, context):
        main(self, context)
        return {'FINISHED'}

 
 
#### REGISTER ####

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.align_object = BoolProperty(
        name="Align object to ground",
        description="Aligns the object to the ground",
        default=True)
    bpy.types.Scene.use_center = BoolProperty(
        name="Use the center to drop",
        description="When dropping the object will be relocated on the basis of its senter",
        default=False)
    
    #random location props
    bpy.types.Scene.random_loc = BoolProperty(
        name="Random Location",
        description="When dropping the object will be relocated randomly ",
        default=False)
    bpy.types.Scene.rl_min_x =  IntProperty(name="min", description = " Minimum of location randomisation while droped to the ground for the x axis", default = 0)
    bpy.types.Scene.rl_max_x =  IntProperty(name="max", description = " Maximum of location randomisation while droped to the ground for the x axis", default = 0)
    bpy.types.Scene.rl_min_y =  IntProperty(name="min", description = " Minimum of location randomisation while droped to the ground for the y axis", default = 0)
    bpy.types.Scene.rl_max_y =  IntProperty(name="max", description = " Maximum of location randomisation while droped to the ground for the y axis", default = 0)
    bpy.types.Scene.rl_min_z =  IntProperty(name="min", description = " Minimum of location randomisation while droped to the ground for the z axis", default = 0)
    bpy.types.Scene.rl_max_z =  IntProperty(name="max", description = " Maximum of location randomisation while droped to the ground for the z axis", default = 0)
     
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.align_object
    del bpy.types.Scene.use_center
    del bpy.types.Scene.random_loc
    del bpy.types.Scene.rl_min_x
    del bpy.types.Scene.rl_max_x
    del bpy.types.Scene.rl_min_y
    del bpy.types.Scene.rl_max_y
    del bpy.types.Scene.rl_min_z
    del bpy.types.Scene.rl_max_z
    
if __name__ == '__main__':
    register()
