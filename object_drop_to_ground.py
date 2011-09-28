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
    "api": 39740,
    "location": "Tool shelf",
    "description": "Drops the selected objects to the active object",
    "warning": "Before using it do :- ctrl+a -> apply rotation on the object to be dropped",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Object/Drop_to_ground",
    "tracker_url": "http://projects.blender.org/tracker/?func=detail&atid=467&aid=25349",
    "category": "Object"}
 
import bpy
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
    
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.align_object
    del bpy.types.Scene.use_center

if __name__ == '__main__':
    register()
