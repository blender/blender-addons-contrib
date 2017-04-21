bl_info = {
    "name": "KTX Mesh Versions",
    "author": "Roel Koster, @koelooptiemanna, irc:kostex",
    "version": (1, 4),
    "blender": (2, 7, 0),
    "location": "View3D > Properties",
    "category": "Object"}

import bpy,time
from datetime import datetime
from bpy.types import Menu, Panel
from bpy.props import StringProperty, BoolProperty, IntProperty

class KTX_MeshInit(bpy.types.Operator):
    bl_label = "Initialise Mesh Versioning"
    bl_idname = "ktx.meshversions_init"
    bl_description = "Initialise the current object to support versioning (Rename object/mesh to unique name)"
        
    def execute(self, context):
        c_mode=bpy.context.object.mode
        if c_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        obj = context.object
        dt = datetime.now().strftime('_%y%m%d%H%M%S')
        obj.name=obj.name+dt
        obj.data.name=obj.name
        bpy.ops.object.mode_set(mode=c_mode)
        return {'FINISHED'}


class KTX_MeshSelect(bpy.types.Operator):
    bl_label = "select mesh"
    bl_idname = "ktx.meshversions_select"
    bl_description = "Change the current mesh to this version"
    
    m_index = StringProperty()
    
    def execute(self, context):
        c_mode=bpy.context.object.mode
        if c_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        obj = context.object
        obj.data = bpy.data.meshes[self.m_index]
        bpy.ops.object.mode_set(mode=c_mode)
        return {'FINISHED'}

class KTX_MeshRemove(bpy.types.Operator):
    bl_label = "remove mesh"
    bl_idname = "ktx.meshversions_remove"
    bl_description = "Remove the current mesh"
    
    m_index = StringProperty()
    
    def execute(self, context):
        bpy.data.meshes.remove(bpy.data.meshes[self.m_index])
        return {'FINISHED'}


class KTX_MeshFake(bpy.types.Operator):
    bl_label = "mesh fake user"
    bl_idname = "ktx.meshversions_fakeuser"
    bl_description = "If pinned (FAKE_USER=TRUE) this mesh will be saved in the blend file\nIf unpinned (FAKE_USER=FALSE) this mesh will be discarded when saving the blend file"
    
    m_index = StringProperty()
    
    def execute(self, context):
        me=bpy.data.meshes
        if me[self.m_index].use_fake_user:
            me[self.m_index].use_fake_user=False
        else:
            me[self.m_index].use_fake_user=True

        return {'FINISHED'}


class KTX_MeshCreate(bpy.types.Operator):
    bl_label = "Create Mesh Version"
    bl_idname = "ktx.meshversions_create"
    bl_description=("Create a copy of the mesh data of the current object\n"
                    "and set it as active")
    def execute(self, context):
        defpin = bpy.context.scene.ktx_defpin
        obj = context.object
        if obj.type=='MESH':
            c_mode=bpy.context.object.mode
            me=obj.data
            if c_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            new_mesh=me.copy()
            obj.data=new_mesh
            obj.data.use_fake_user=defpin
            bpy.ops.object.mode_set(mode=c_mode)

        return {'FINISHED'}


class KTX_Mesh_Versions(bpy.types.Panel):
    bl_label = "KTX Mesh Versions"
    bl_idname = "ktx.meshversions"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scene = context.scene
        obj = context.object

        layout = self.layout
        col = layout.column()
        if obj == None:
            col.label('Select/Create something first!')
        else:
            if obj.type == 'MESH':
                if len(obj.name) > 14:
                    if obj.name[-13] == '_' and obj.name[-12:].isdigit():
                        col.operator("ktx.meshversions_create")
                        col.prop(scene, "ktx_defpin")
                        box = layout.box()
                        box.label("Versions of Active Object: " + obj.name)
                        len_obj=len(obj.name)
                        for m in bpy.data.meshes:
                            len_m=len(m.name)
                            if m.name[:len_obj] == obj.name:
                                row = box.row()
                                row.operator("ktx.meshversions_select",text=m.name).m_index = m.name
                                if m.users == 0:
                                    row.operator("ktx.meshversions_remove",text="",icon="X").m_index = m.name
                        
                                if bpy.data.meshes[m.name].use_fake_user:
                                    row.operator("ktx.meshversions_fakeuser", text="",icon="PINNED").m_index = m.name
                                else:
                                    row.operator("ktx.meshversions_fakeuser", text="",icon="UNPINNED").m_index = m.name
                else:
                    col.operator("ktx.meshversions_init")
            else:
                col.label('Select a Mesh Object in the Scene!')
                box = layout.box()
                box.label('Or either remove unwanted or pin important meshes:')
                for m in bpy.data.meshes:
                    row = box.row()
                    row.label(m.name)
                    if m.users == 0:
                        row.operator("ktx.meshversions_remove",text="",icon="X").m_index = m.name

                    if bpy.data.meshes[m.name].use_fake_user:
                        row.operator("ktx.meshversions_fakeuser", text="",icon="PINNED").m_index = m.name
                    else:
                        row.operator("ktx.meshversions_fakeuser", text="",icon="UNPINNED").m_index = m.name


def register():
    bpy.types.Scene.ktx_defpin = bpy.props.BoolProperty(name="Auto Pinning", description="When creating a copy set pinning to ON automatically (FAKE_USER=TRUE)", default=False)
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.ktx_defpin

if __name__ == "__main__":
    register()
