bl_info = {
    "name": "Mesh Cache Tools",
    "author": "Oscurart",
    "version": (1, 0),
    "blender": (2, 6, 4),
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

bpy.types.Scene.muu_pc2_rotx = bpy.props.BoolProperty(default=True, name="Rotx = 90")
bpy.types.Scene.muu_pc2_world_space = bpy.props.BoolProperty(default=True, name="World Space")
bpy.types.Scene.muu_pc2_modifiers = bpy.props.BoolProperty(default=True, name="Apply Modifiers")
bpy.types.Scene.muu_pc2_subsurf = bpy.props.BoolProperty(default=True, name="Turn Off SubSurf")
bpy.types.Scene.muu_pc2_start = bpy.props.IntProperty(default=0, name="Frame Start")
bpy.types.Scene.muu_pc2_end = bpy.props.IntProperty(default=100, name="Frame End")
bpy.types.Scene.muu_pc2_group = bpy.props.StringProperty()
bpy.types.Scene.muu_pc2_folder = bpy.props.StringProperty(default="Set me Please!")

class OscEPc2ExporterPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mesh Cache Tools"
    bl_idname = "Mesh Cache Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout

        obj = context.object
        row = layout.column(align=1)
        row.prop(bpy.context.scene, "muu_pc2_folder", text="Folder")
        row.operator("import_shape.pc2_copy", icon='FILESEL', text="Set Filepath")
        row = layout.box().column(align=1)
        row.label("EXPORTER:")
        row.operator("group.linked_group_to_local", text="Linked To Local", icon="LINKED")
        row.operator("object.remove_subsurf_modifier", text="Remove Gen Modifiers", icon="MOD_SUBSURF")
        row.operator("export_shape.pc2_selection", text="Export!", icon="POSE_DATA")
        #row.prop(bpy.context.scene,"muu_pc2_rotx", text= "RotX90")
        row.prop(bpy.context.scene, "muu_pc2_world_space", text="World Space")
        #row.prop(bpy.context.scene,"muu_pc2_modifiers", text="Apply Modifiers")
        #row.prop(bpy.context.scene,"muu_pc2_subsurf", text="Turn Off SubSurf")
        row = layout.column(align=1)
        row.prop(bpy.context.scene, "muu_pc2_start", text="Frame Start")
        row.prop(bpy.context.scene, "muu_pc2_end", text="Frame End")
        row.prop_search(bpy.context.scene, "muu_pc2_group", bpy.data, "groups", text="")
        row = layout.box().column(align=1)
        row.label("IMPORTER:")
        row.operator("import_shape.pc2_selection", text="Import", icon="POSE_DATA")

def OscFuncExportPc2(self):
    start = bpy.context.scene.muu_pc2_start
    end = bpy.context.scene.muu_pc2_end
    folderpath = bpy.context.scene.muu_pc2_folder

    for ob in bpy.data.groups[bpy.context.scene.muu_pc2_group].objects[:]:
        pc2list = []
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
                        pc2list.append((
                            float(vert.co[0]),
                            float(vert.co[1]),
                            float(vert.co[2])
                            ))

                    #dreno mesh
                    bpy.data.meshes.remove(me)

                print("%s Bake finished! \nAwaiting Compile file..." % (ob.name))

                # write file
                for i, frame in enumerate(pc2list):
                    #print("Percentage of %s Compiled file: %s " % ( ob.name, i*100/len(pc2list)))
                    file.write(struct.pack("<3f", *frame))
                print("%s File Compiled Write finished!" % (ob.name))
                del(pc2list)

    print("Bake Finished!")

class OscPc2ExporterBatch(bpy.types.Operator):
    bl_idname = "export_shape.pc2_selection"
    bl_label = "Export pc2 for selected Objects"
    bl_description = "Export pc2 for selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        OscFuncExportPc2(self)
        return {'FINISHED'}

class OscRemoveSubsurf(bpy.types.Operator):
    bl_idname = "object.remove_subsurf_modifier"
    bl_label = "Remove SubSurf Modifier"
    bl_description = "Remove SubSurf Modifier"
    bl_options = {'REGISTER', 'UNDO'}

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
        bpy.context.scene.muu_pc2_folder = str(bpy.data.filepath.rpartition(os.sep)[0])
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

    def execute(self, context):
        OscLinkedGroupToLocal()
        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()