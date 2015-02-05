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

import bpy
from bpy.types import Operator
from bpy.props import *


def meshcache_export(context):

    scene = context.scene
    objects = []
    howmany_exported = 0
    howmany_excluded = 0

    if scene.use_meshcache_exclude_names:
        excluded = []

        if scene.meshcache_exclude_names:
            for ex in scene.meshcache_exclude_names:
                if ex.name != '':
                    excluded.append(ex.name)

    print("\n== Meshcache Export Start ==")

    if scene.meshcache_apply_to == 'GROUP':
        objects = bpy.data.groups[scene.meshcache_group].objects
    else:
        objects = bpy.context.selected_objects

    for ob in objects:
        if ob and ob.type == 'MESH':

            is_excluded = False

            if scene.use_meshcache_exclude_names:
                for e in excluded:
                    if e in ob.name:
                        is_excluded = True

            if is_excluded:
                howmany_excluded += 1
                print("** {0} - Excluded".format(ob.name))
            else:
                filename = scene.meshcache_folder + "/" + scene.meshcache_group + "_" + ob.name + ".cache.mdd"

                if ob.modifiers:
                    for mo in ob.modifiers:
                        if mo.type == 'SUBSURF':
                            mo.show_viewport = False

                context.scene.objects.active = ob

                bpy.ops.export_shape.mdd(filepath=filename,
                                         frame_start=scene.meshcache_frame_start,
                                         frame_end=scene.meshcache_frame_end,
                                         fps=scene.meshcache_frame_rate)
                print("{0} - Exported".format(ob.name))
                howmany_exported += 1

    MESH_OP_MeshcacheExport.howmany_exported = howmany_exported
    MESH_OP_MeshcacheExport.howmany_excluded = howmany_excluded

    print("\n== Meshcache Export Finished ==")
    print("== {0} Exported, {1} Excluded ==".format(
           howmany_exported, howmany_excluded))


def meshcache_import(context):

    scene = context.scene
    mc_mod_name = "MeshCacheAM"
    objects = []
    howmany_imported = 0
    howmany_excluded = 0

    import os.path

    if scene.use_meshcache_exclude_names:
        excluded = []

        if scene.meshcache_exclude_names:
            for ex in scene.meshcache_exclude_names:
                if ex.name != '':
                    excluded.append(ex.name)

    print("\n== Meshcache Import Start ==")

    if scene.meshcache_apply_to == 'GROUP':
        objects = bpy.data.groups[scene.meshcache_group].objects
    else:
        objects = bpy.context.selected_objects

    for ob in objects:
        if ob and ob.type == 'MESH':

            is_excluded = False

            if scene.use_meshcache_exclude_names:
                for e in excluded:
                    if e in ob.name:
                        is_excluded = True

            if is_excluded:
                howmany_excluded += 1
                print("** {0} - Excluded".format(ob.name))
            else:
                filename = scene.meshcache_folder + "/" + scene.meshcache_group + "_" + ob.name + ".cache.mdd"

                if os.path.isfile(filename):
                    has_meshcache = False

                    if ob.modifiers:
                        for mo in ob.modifiers:
                            if mo.type == 'MESH_CACHE':
                                has_meshcache = True
                                mo.name = mc_mod_name

                    if not has_meshcache:
                        ob.modifiers.new(mc_mod_name, "MESH_CACHE")

                    ob.modifiers[mc_mod_name].filepath = filename
                    ob.modifiers[mc_mod_name].frame_start = scene.meshcache_frame_start

                    print("{0} - Imported".format(ob.name))
                    howmany_imported += 1
                else:
                    print("! No Meshcache found for {0}".format(ob.name))


    MESH_OP_MeshcacheImport.howmany_imported = howmany_imported
    MESH_OP_MeshcacheImport.howmany_excluded = howmany_excluded

    print("\n== Meshcache Import Finished ==")
    print("== {0} Imported, {1} Excluded ==".format(
           howmany_imported, howmany_excluded))


class MESH_OP_MeshcacheExport(Operator):
    """Export Meshcache"""
    bl_idname = "object.meshcache_export"
    bl_label = "Export Mesh Cache"
    howmany_exported = 0
    howmany_excluded = 0

    @classmethod
    def poll(cls, context):
        if context.scene.meshcache_apply_to == 'GROUP':
            return len(bpy.data.groups) != 0
        else:
            return context.active_object is not None

    def execute(self, context):
        meshcache_export(context)
        self.report({'INFO'}, "Meshcache Exported")
        return {'FINISHED'}


class MESH_OP_MeshcacheImport(Operator):
    """Import Meshcache (creates Meshcache modifiers when necessary)"""
    bl_idname = "object.meshcache_import"
    bl_label = "Import Mesh Cache"
    howmany_imported = 0
    howmany_excluded = 0

    @classmethod
    def poll(cls, context):
        if context.scene.meshcache_apply_to == 'GROUP':
            return len(bpy.data.groups) != 0
        else:
            return context.active_object is not None

    def execute(self, context):
        meshcache_import(context)
        self.report({'INFO'}, "Meshcache Imported")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MESH_OP_MeshcacheExport)
    bpy.utils.register_class(MESH_OP_MeshcacheImport)

def unregister():
    bpy.utils.unregister_class(MESH_OP_MeshcacheExport)
    bpy.utils.unregister_class(MESH_OP_MeshcacheImport)
