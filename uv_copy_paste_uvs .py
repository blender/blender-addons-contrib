# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Copy/Paste UVs",
    "author": "Jace Priester",
    "version": (1, 1),
    "blender": (2, 6, 3),
    "location": "UV Mapping > Copy/Paste UVs",
    "description":
    "Copy/Paste UV data between groups "
    "of vertices in the same mesh object",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.6/"
    "Py/Scripts/Mesh/Copy_Paste_UVs",
    "tracker_url": "http://projects.blender.org/tracker/"
    "?group_id=153&atid=467&func=detail&aid=32562",
    "category": "UV"}


import bpy


source_object = None
copy_buffer = ''


class CopyPasteUVs_Copy(bpy.types.Operator):

    ''''''
    bl_idname = "uv.copy_uvs"
    bl_label = "Copy UVs"
    bl_description = "Copy UVs"
    bl_options = {'REGISTER', 'UNDO'}

    ''' Properties
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'error', expand=True) '''

    # execute
    def execute(self, context):
        # print("------START------")

        global copy_buffer
        global source_object

        copy_buffer = []
        source_object = None

        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')

        vertex_indexes = [i for i, v in enumerate(obj.data.vertices) if v.select]

        if len(vertex_indexes) == 0:
            self.report({'WARNING'}, "Must have selected vertices to copy.")
        else:
            copy_buffer = vertex_indexes
            source_object = obj

        bpy.ops.object.mode_set(mode='EDIT')

        # print("-------END-------")
        return {'FINISHED'}


class CopyPasteUVs_Paste(bpy.types.Operator):

    ''''''
    bl_idname = "uv.paste_uvs"
    bl_label = "Paste UVs"
    bl_description = "Paste UVs"
    bl_options = {'REGISTER', 'UNDO'}

    ''' Properties
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'error', expand=True) '''

    # execute
    def execute(self, context):
        # print("------START------")

        global copy_buffer
        global source_object

        if len(copy_buffer) == 0:
            print("Must have copied first!")
        else:
            obj = bpy.context.active_object
            bpy.ops.object.mode_set(mode='OBJECT')

            vertex_indexes = [i for i, v in enumerate(obj.data.vertices) if v.select]

            if len(vertex_indexes) == 0:
                self.report(
                    {'WARNING'},
                    "Must have vertices selected to paste.")
            elif len(vertex_indexes) != len(copy_buffer):
                self.report(
                    {'WARNING'},
                    "Number of copied verts is not the same as number selected now.")
            else:

                for i, source_index in enumerate(copy_buffer):
                    #source_index = copy_buffer[i]
                    destination_index = vertex_indexes[i]

                    source_loops = []
                    destination_loops = []

                    for loop_index, loop_obj in enumerate(obj.data.loops):
                        if obj.data.loops[loop_index].vertex_index == destination_index:
                            destination_loops.append(loop_index)

                    for loop_index, loop_obj in enumerate(source_object.data.loops):
                        if source_object.data.loops[loop_index].vertex_index == source_index:
                            source_loops.append(loop_index)

                    if len(source_loops) != len(destination_loops):
                        self.report(
                            {'WARNING'},
                            "Error; source loops and destination loops do not "
                            "match; geometry seems dissimilar")
                    else:

                        uvlayer_destination = obj.data.uv_layers.active
                        uvlayer_source = source_object.data.uv_layers.active

                        for j, source in enumerate(source_loops):
                            #source = source_loops[j]
                            dest = destination_loops[j]

                            uvlayer_destination.data[
                                dest].uv = uvlayer_source.data[source].uv

        bpy.ops.object.mode_set(mode='EDIT')

        # print("-------END-------")
        return {'FINISHED'}


#
# REGISTER ###################################
#

def add_to_menu(self, context):
    self.layout.operator("uv.copy_uvs")
    self.layout.operator("uv.paste_uvs")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_uv_map.append(add_to_menu)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_uv_map.remove(add_to_menu)

if __name__ == "__main__":
    register()
