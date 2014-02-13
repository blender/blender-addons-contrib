bl_info = {
    "name": "Mesh Cache Tools",
    "author": "Oscurart",
    "version": (1, 0),
    "blender": (2, 64, 0),
    "location": "Tools > Mesh Cache Tools",
    "description": "Tools for Management Mesh Cache Process",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}


import bpy
import sys
import os
import struct

class View3DMCPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

class OscEPc2ExporterPanel(View3DMCPanel, bpy.types.Panel):    
    """
    bl_label = "Mesh Cache Tools"
    bl_idname = "Mesh Cache Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    """
    bl_category = "Mesh Cache Tools"
    #bl_context = "objectmode"
    bl_label = "Mesh Cache Tools"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        row = layout.column(align=1)
        row.prop(bpy.context.scene, "muu_pc2_folder", text="Folder")
        row.operator("import_shape.pc2_copy", icon='FILESEL', text="Set Filepath")
        row.prop(bpy.context.scene, "muu_pc2_relative_path", text="Relative Path (Optional):")
        row = layout.box().column(align=1)
        row.label("EXPORTER:")
        row.operator("group.linked_group_to_local", text="Linked To Local", icon="LINKED")
        row.operator("object.remove_subsurf_modifier", text="Remove Gen Modifiers", icon="MOD_SUBSURF")
        row.operator("export_shape.pc2_selection", text="Export!", icon="POSE_DATA")
        row.prop(bpy.context.scene, "muu_pc2_world_space", text="World Space")
        row = layout.column(align=1)
        row.prop(bpy.context.scene, "muu_pc2_start", text="Frame Start")
        row.prop(bpy.context.scene, "muu_pc2_end", text="Frame End")
        row.prop_search(bpy.context.scene, "muu_pc2_group", bpy.data, "groups", text="")
        row = layout.box().column(align=1)
        row.label("IMPORTER:")
        row.operator("import_shape.pc2_selection", text="Import", icon="POSE_DATA")
        row.operator("object.modifier_mesh_cache_up", text="MC Top", icon="TRIA_UP")

def OscFuncExportPc2(self):
    start = bpy.context.scene.muu_pc2_start
    end = bpy.context.scene.muu_pc2_end
    folderpath = bpy.context.scene.muu_pc2_folder

    for ob in bpy.data.groups[bpy.context.scene.muu_pc2_group].objects[:]:
        bpy.context.window_manager.progress_begin(0, 100) #progressbar
        if ob.type == "MESH":
            with open("%s/%s.pc2" % (os.path.normpath(folderpath), ob.name), mode="wb") as file:
                #encabezado
                headerFormat = '<12siiffi'
                headerStr = struct.pack(headerFormat,
                         b'POINTCACHE2\0', 1, len(ob.data.vertices[:]), 0, 1.0, (end + 1) - start)
                file.write(headerStr)
                #bakeado
                obmat = ob.matrix_world
                for frame in range((end + 1) - start):
                    print("Percentage of %s bake: %s " % (ob.name, frame / end * 100))
                    bpy.context.window_manager.progress_update(frame / end * 100) #progressbarUpdate
                    bpy.context.scene.frame_set(frame)
                    me = bpy.data.meshes.new_from_object(
                        scene=bpy.context.scene,
                        object=ob,
                        apply_modifiers=True,
                        settings="RENDER",
                        calc_tessface=True,
                        calc_undeformed=False)
                    #rotate
                    if bpy.context.scene.muu_pc2_world_space:
                        me.transform(obmat)
                        me.calc_normals()
                    #creo archivo
                    for vert in me.vertices[:]:
                        file.write(struct.pack("<3f", *vert.co)) 
                    #dreno mesh
                    bpy.data.meshes.remove(me)

                print("%s Bake finished!" % (ob.name))
                
        bpy.context.window_manager.progress_end()#progressBarClose
    print("Bake Totally Finished!")

class OscPc2ExporterBatch(bpy.types.Operator):
    bl_idname = "export_shape.pc2_selection"
    bl_label = "Export pc2 for selected Objects"
    bl_description = "Export pc2 for selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.scene.muu_pc2_group != "" and bpy.context.scene.muu_pc2_folder != 'Set me Please!')

    def execute(self, context):
        OscFuncExportPc2(self)
        return {'FINISHED'}

class OscRemoveSubsurf(bpy.types.Operator):
    bl_idname = "object.remove_subsurf_modifier"
    bl_label = "Remove SubSurf Modifier"
    bl_description = "Remove SubSurf Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.scene.muu_pc2_group != "")

    def execute(self, context):
        GENERATE = ['MULTIRES', 'ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD', 'DECIMATE', 'MASK', 'MIRROR', 'REMESH', 'SCREW', 'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE']
        for OBJ in bpy.data.groups[bpy.context.scene.muu_pc2_group].objects[:]:
            for MOD in OBJ.modifiers[:]:
                if MOD.type in GENERATE:
                    OBJ.modifiers.remove(MOD)
        return {'FINISHED'}


class OscPc2iMporterBatch(bpy.types.Operator):
    bl_idname = "import_shape.pc2_selection"
    bl_label = "Import pc2 for selected Objects"
    bl_description = "Import pc2 for selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.scene.muu_pc2_folder != 'Set me Please!')

    def execute(self, context):
        for OBJ in bpy.context.selected_objects[:]:
            MOD = OBJ.modifiers.new("MeshCache", 'MESH_CACHE')
            MOD.filepath = "%s%s%s.pc2" % (bpy.context.scene.muu_pc2_folder, os.sep, OBJ.name)
            MOD.cache_format = "PC2"
            MOD.forward_axis = "POS_Y"
            MOD.up_axis = "POS_Z"
            MOD.flip_axis = set(())

        return {'FINISHED'}

class OscPc2iMporterCopy(bpy.types.Operator):
    bl_idname = "import_shape.pc2_copy"
    bl_label = "Copy Filepath"
    bl_description = "Copy Filepath"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        filefolder = os.path.dirname(bpy.data.filepath)
        os.chdir(filefolder)
        if bpy.context.scene.muu_pc2_relative_path != "":
            if os.path.exists("%s" % (os.path.join(filefolder,bpy.context.scene.muu_pc2_relative_path))):
                print("Folder Already Exists.")
            else:
                os.mkdir("%s" % (os.path.join(filefolder,bpy.context.scene.muu_pc2_relative_path)))
            bpy.context.scene.muu_pc2_folder = "%s" % (os.path.join(filefolder,bpy.context.scene.muu_pc2_relative_path))
        else:
            bpy.context.scene.muu_pc2_folder = "%s" % (filefolder)

        return {'FINISHED'}

def OscLinkedGroupToLocal():
    ACTOBJ = bpy.context.active_object
    GROBJS = [ob for ob in ACTOBJ.id_data.dupli_group.objects[:] if ob.type == "MESH"]

    for ob in ACTOBJ.id_data.dupli_group.objects[:]:
        bpy.context.scene.objects.link(ob)
    NEWGROUP = bpy.data.groups.new("%s_CLEAN" % (ACTOBJ.name))
    bpy.context.scene.objects.unlink(ACTOBJ)
    NEWOBJ = []
    for ob in GROBJS:
        NEWGROUP.objects.link(ob)
        NEWOBJ.append(ob)
    for ob in NEWOBJ:
        if ob.type == "MESH":
            if len(ob.modifiers):
                for MODIFIER in ob.modifiers[:]:
                    if MODIFIER.type == "SUBSURF" or MODIFIER.type == "MASK":
                        ob.modifiers.remove(MODIFIER)

class OscGroupLinkedToLocal(bpy.types.Operator):
    bl_idname = "group.linked_group_to_local"
    bl_label = "Group Linked To Local"
    bl_description = "Group Linked To Local"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.scene.muu_pc2_group != "")

    def execute(self, context):
        OscLinkedGroupToLocal()
        return {'FINISHED'}

class OscMeshCacheUp(bpy.types.Operator):
    bl_idname = "object.modifier_mesh_cache_up"
    bl_label = "Mesh Cache To Top"
    bl_description = "Send Mesh Cache Modifiers top"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == "MESH")

    def execute(self, context):

        actob = bpy.context.scene.objects.active

        for ob in bpy.context.selected_objects[:]:
            bpy.context.scene.objects.active = ob
            for mod in ob.modifiers[:]:
                if mod.type == "MESH_CACHE":
                    for up in range(ob.modifiers.keys().index(mod.name)):
                        bpy.ops.object.modifier_move_up(modifier=mod.name)

        bpy.context.scene.objects.active = actob

        return {'FINISHED'}


def register():
    from bpy.types import Scene
    from bpy.props import (BoolProperty,
                           IntProperty,
                           StringProperty,
                           )

    Scene.muu_pc2_rotx = BoolProperty(default=True, name="Rotx = 90")
    Scene.muu_pc2_world_space = BoolProperty(default=True, name="World Space")
    Scene.muu_pc2_modifiers = BoolProperty(default=True, name="Apply Modifiers")
    Scene.muu_pc2_subsurf = BoolProperty(default=True, name="Turn Off SubSurf")
    Scene.muu_pc2_start = IntProperty(default=0, name="Frame Start")
    Scene.muu_pc2_end = IntProperty(default=100, name="Frame End")
    Scene.muu_pc2_group = StringProperty()
    Scene.muu_pc2_folder = StringProperty(default="Set me Please!")
    Scene.muu_pc2_relative_path = StringProperty(default="")

    bpy.utils.register_module(__name__)


def unregister():
    from bpy.types import Scene

    del Scene.muu_pc2_rotx
    del Scene.muu_pc2_world_space
    del Scene.muu_pc2_modifiers
    del Scene.muu_pc2_subsurf
    del Scene.muu_pc2_start
    del Scene.muu_pc2_end
    del Scene.muu_pc2_group
    del Scene.muu_pc2_folder
    del Scene.muu_pc2_relative_path

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()