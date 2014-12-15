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
from object_physics_meadow.settings import find_meadow_object
from object_physics_meadow.util import *

class OBJECT_PT_Meadow(Panel):
    """Settings for meadow components"""
    bl_label = "Meadow"
    bl_idname = "OBJECT_PT_meadow"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob:
            return False
        return True
    
    def draw(self, context):
        settings = _settings.get(context)
        ob = context.object
        meadow = ob.meadow
        layout = self.layout
        
        layout.prop(meadow, "type", expand=True)
        
        layout.separator()
        
        if meadow.type == 'TEMPLATE':
            row = layout.row()
            groundob = find_meadow_object(context, 'GROUND')
            if groundob:
                row.prop_search(meadow, "density_vgroup_name", groundob, "vertex_groups", text="Density Vertex Group")
            else:
                row.active = False
                row.prop(meadow, "density_vgroup_name", text="Density Vertex Group")
            
            row = layout.row()
            row.prop(meadow, "use_as_dupli")
            sub = row.row()
            sub.enabled = meadow.use_as_dupli
            sub.prop(meadow, "use_centered")
        
        elif meadow.type == 'GROUND':
            layout.prop(meadow, "seed")
            
            col = layout.column(align=True)
            col.prop(meadow, "patch_radius")
            col.prop(meadow, "max_patches")
            
            layout.prop(meadow, "sampling_levels")
        
        layout.separator()
        
        layout.operator("meadow.make_blobs", icon='STICKY_UVS_DISABLE')
        layout.operator("meadow.make_patches", icon='PARTICLE_PATH')
        layout.operator("meadow.rebake_meadow")


class MeadowOperatorBase():
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


class MakeBlobsOperator(MeadowOperatorBase, Operator):
    """Generate Blob objects storing dupli distribution"""
    bl_idname = "meadow.make_blobs"
    bl_label = "Make Blobs"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        settings = _settings.get(context)
        
        #cache_ok, cache_dir = self.verify_cache_dir()
        #if not cache_ok:
        #    return {'CANCELLED'}
        if not settings.blob_group(context):
            bpy.data.groups.new(settings.blob_groupname)
        
        groundob = find_meadow_object(context, 'GROUND')
        if not groundob:
            self.report({'ERROR'}, "Could not find meadow Ground object")
            return {'CANCELLED'}
        blobgridob = find_meadow_object(context, 'BLOBGRID')
        if not blobgridob:
            self.report({'ERROR'}, "Could not find meadow Blob Grid object")
            return {'CANCELLED'}
        
        with ObjectSelection():
            meadow.make_blobs(context, blobgridob, groundob)
        
        return {'FINISHED'}


class MakePatchesOperator(MeadowOperatorBase, Operator):
    """Make Patch copies across the grid for simulation and set up duplis"""
    bl_idname = "meadow.make_patches"
    bl_label = "Make Patches"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        settings = _settings.get(context)
        
        if not settings.patch_group(context):
            bpy.data.groups.new(settings.patch_groupname)
        if not settings.blob_group(context):
            bpy.data.groups.new(settings.blob_groupname)
        
        groundob = find_meadow_object(context, 'GROUND')
        if not groundob:
            self.report({'ERROR'}, "Could not find meadow Ground object")
            return {'CANCELLED'}
        blobgridob = find_meadow_object(context, 'BLOBGRID')
        if not blobgridob:
            self.report({'ERROR'}, "Could not find meadow Blob Grid object")
            return {'CANCELLED'}
        
        with ObjectSelection():
            meadow.make_patches(context, blobgridob, groundob)
        
        return {'FINISHED'}


# Combines blob + patches operator for menu entry
class MakeMeadowOperator(MeadowOperatorBase, Operator):
    """Make blobs and patches based on designated meadow objects"""
    bl_idname = "meadow.make_meadow"
    bl_label = "Make Meadow"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        result = bpy.ops.meadow.make_blobs()
        if 'FINISHED' not in result:
            return result
        result = bpy.ops.meadow.make_patches()
        if 'FINISHED' not in result:
            return result
        
        return {'FINISHED'}


class RebakeMeadowOperator(MeadowOperatorBase, Operator):
    """Rebake meadow simulation"""
    bl_idname = "meadow.rebake_meadow"
    bl_label = "Rebake Meadow"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        with ObjectSelection():
            # XXX Note: wm.progress updates are disabled for now, because the bake
            # operator overrides this with it's own progress numbers ...
            patch.patch_objects_rebake(context, progress_reporter=make_progress_reporter(show_progress_bar=False, show_stdout=True))
        return {'FINISHED'}


def menu_generate_meadow(self, context):
    self.layout.operator("meadow.make_meadow", icon='PARTICLE_PATH')

def register():
    bpy.utils.register_class(OBJECT_PT_Meadow)
    
    bpy.utils.register_class(MakeBlobsOperator)
    bpy.utils.register_class(MakePatchesOperator)
    bpy.utils.register_class(MakeMeadowOperator)
    bpy.utils.register_class(RebakeMeadowOperator)
    bpy.types.INFO_MT_add.append(menu_generate_meadow)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_Meadow)
    
    bpy.types.INFO_MT_add.remove(menu_generate_meadow)
    bpy.utils.unregister_class(MakeBlobsOperator)
    bpy.utils.unregister_class(MakePatchesOperator)
    bpy.utils.unregister_class(MakeMeadowOperator)
    bpy.utils.unregister_class(RebakeMeadowOperator)
