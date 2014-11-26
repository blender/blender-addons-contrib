### BEGIN GPL LICENSE BLOCK #####
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

# <pep8 compliant>

import bpy, os
from bpy.types import Operator, Panel
from bpy.props import *

from object_physics_meadow import meadow, settings as _settings, patch, blob

class OBJECT_PT_Meadow(Panel):
    """Settings for meadow components"""
    bl_label = "Meadow"
    bl_idname = "OBJECT_PT_meadow"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    def draw(self, context):
        settings = _settings.get(context)
        ob = context.object
        layout = self.layout
        
        # draw general settings here as well
        type(settings).draw_ex(settings, layout, context)
        
        layout.operator("scene.generate_meadow", icon='PARTICLE_PATH')
        layout.operator("scene.rebake_meadow")
        
        if ob:
            meadow = ob.meadow
            
            layout.separator()
            
            layout.prop(meadow, "type", expand=True)
            
            if meadow.type == 'TEMPLATE':
                layout.prop(meadow, "use_as_dupli")
            elif meadow.type == 'BLOBGRID':
                layout.prop(meadow, "seed")
                
                layout.prop(meadow, "patch_radius")
                layout.prop(meadow, "max_patches")


class MeadowOperatorBase():
    def find_meadow_object(self, context, type):
        scene = context.scene
        for ob in scene.objects:
            if ob.meadow.type == type:
                return ob


class GenerateMeadowOperator(MeadowOperatorBase, Operator):
    """Generate meadow instances"""
    bl_idname = "scene.generate_meadow"
    bl_label = "Generate Meadow"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def verify_cache_dir(self):
        if not bpy.data.is_saved:
            self.report({'ERROR'}, "File must be saved for generating external cache directory")
            return False, ""
        
        cache_dir = bpy.path.abspath("//meadow_cache")
        if os.path.exists(cache_dir):
            if not os.path.isdir(cache_dir):
                self.report({'ERROR'}, "%s is not a directory" % cache_dir)
                return False, ""
        else:
            try:
                os.mkdir(cache_dir)
            except OSError as err:
                self.report({'ERROR'}, "{0}".format(err))
                return False, ""
        return True, cache_dir
    
    def execute(self, context):
        scene = context.scene
        settings = _settings.get(context)
        
        #cache_ok, cache_dir = self.verify_cache_dir()
        #if not cache_ok:
        #    return {'CANCELLED'}
        
        if not settings.patch_group(context):
            # patch group is filled by us, so can just create it
            bpy.data.groups.new(settings.patch_groupname)
        if not settings.blob_group(context):
            # blob group is filled by us, so can just create it
            bpy.data.groups.new(settings.blob_groupname)
        
        groundob = self.find_meadow_object(context, 'GROUND')
        if not groundob:
            self.report({'ERROR'}, "Could not find meadow Ground object")
            return {'CANCELLED'}
        blobgridob = self.find_meadow_object(context, 'BLOBGRID')
        if not blobgridob:
            self.report({'ERROR'}, "Could not find meadow Blob Grid object")
            return {'CANCELLED'}
        
        meadow.generate_meadow(context, blobgridob, groundob)
        
        return {'FINISHED'}


class RebakeMeadowOperator(MeadowOperatorBase, Operator):
    """Rebake meadow simulation"""
    bl_idname = "scene.rebake_meadow"
    bl_label = "Rebake Meadow"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        patch.patch_objects_rebake(context)
        return {'FINISHED'}


def menu_generate_meadow(self, context):
    self.layout.operator("scene.generate_meadow", icon='PARTICLE_PATH')

def register():
    bpy.utils.register_class(OBJECT_PT_Meadow)
    
    bpy.utils.register_class(GenerateMeadowOperator)
    bpy.utils.register_class(RebakeMeadowOperator)
    bpy.types.INFO_MT_add.append(menu_generate_meadow)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_Meadow)
    
    bpy.types.INFO_MT_add.remove(menu_generate_meadow)
    bpy.utils.unregister_class(GenerateMeadowOperator)
    bpy.utils.unregister_class(RebakeMeadowOperator)
