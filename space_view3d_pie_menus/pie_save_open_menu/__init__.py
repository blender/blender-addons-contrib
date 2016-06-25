
bl_info = {
    "name": "Save Open: Key: 'Ctrl S'",
    "description": "Align Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "Alt X key",
    "warning": "",
    "wiki_url": "",
    "category": "Pie"
}

import bpy, bmesh
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty
from mathutils import *
import math
import os

# Pie Save/Open
class PieSaveOpen(Menu):
    bl_idname = "pie.saveopen"
    bl_label = "Pie Save/Open"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("wm.read_homefile", text="New", icon='NEW')
        # 6 - RIGHT
        pie.operator("file.save_incremental", text="Incremental Save", icon='SAVE_COPY')
        # 2 - BOTTOM
        pie.menu("pie.fileio", text="Import/Export", icon='IMPORT')
        # 8 - TOP
        pie.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')
        # 7 - TOP - LEFT
        pie.operator("wm.open_mainfile", text="Open file", icon='FILE_FOLDER')
        # 9 - TOP - RIGHT
        pie.operator("wm.save_as_mainfile", text="Save As...", icon='SAVE_AS')
        # 1 - BOTTOM - LEFT
        pie.menu("pie.recover", text="Recovery", icon='RECOVER_LAST')
        # 3 - BOTTOM - RIGHT
        pie.menu("pie.link", text="Link", icon='LINK_BLEND')

class pie_link(bpy.types.Menu):
    bl_idname = "pie.link"
    bl_label = "Link"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("wm.link", text="Link", icon='LINK_BLEND')
        box.operator("wm.append", text="Append", icon='APPEND_BLEND')
        box.menu("external.data", text="External Data", icon='EXTERNAL_DATA')

class pie_recover(bpy.types.Menu):
    bl_idname = "pie.recover"
    bl_label = "Recovery"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("wm.recover_auto_save", text="Recover Auto Save...", icon='RECOVER_AUTO')
        box.operator("wm.recover_last_session", text="Recover Last Session", icon='RECOVER_LAST')
        box.operator("wm.revert_mainfile", text="Revert", icon='FILE_REFRESH')

class pie_fileio(bpy.types.Menu):
    bl_idname = "pie.fileio"
    bl_label = "Import/Export"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        row = box.row(align=True)
        box.operator("import_scene.obj", text="Import OBJ", icon='IMPORT')
        box.operator("export_scene.obj", text="Export OBJ", icon='EXPORT')
        box.separator()
        box.operator("import_scene.fbx", text="Import FBX", icon='IMPORT')
        box.operator("export_scene.fbx", text="Export FBX", icon='EXPORT')

class ExternalData(bpy.types.Menu):
    bl_idname = "external.data"
    bl_label = "External Data"

    def draw(self, context):
        layout = self.layout

        layout.operator("file.autopack_toggle", text="Automatically Pack Into .blend")
        layout.separator()
        layout.operator("file.pack_all", text="Pack All Into .blend")
        layout.operator("file.unpack_all", text="Unpack All Into Files")
        layout.separator()
        layout.operator("file.make_paths_relative", text="Make All Paths Relative")
        layout.operator("file.make_paths_absolute", text="Make All Paths Absolute")
        layout.operator("file.report_missing_files", text="Report Missing Files")
        layout.operator("file.find_missing_files", text="Find Missing Files")

# Save Incremental
class FileIncrementalSave(bpy.types.Operator):
    bl_idname = "file.save_incremental"
    bl_label = "Save Incremental"
    bl_options = {"REGISTER"}

    def execute(self, context):
        f_path = bpy.data.filepath
        if f_path.find("_") != -1:
            # fix for cases when there is an underscore in the name like my_file.blend
            try:
                str_nb = f_path.rpartition("_")[-1].rpartition(".blend")[0]
                int_nb = int(str(str_nb))
                new_nb = str_nb.replace(str(int_nb), str(int_nb + 1))
                output = f_path.replace(str_nb, new_nb)

                i = 1
                while os.path.isfile(output):
                    str_nb = f_path.rpartition("_")[-1].rpartition(".blend")[0]
                    i += 1
                    new_nb = str_nb.replace(str(int_nb), str(int_nb + i))
                    output = f_path.replace(str_nb, new_nb)
            except ValueError:
                output = f_path.rpartition(".blend")[0] + "_001" + ".blend"
        else:
            output = f_path.rpartition(".blend")[0] + "_001" + ".blend"
        bpy.ops.wm.save_as_mainfile(filepath=output)

        self.report({'INFO'}, "File: {0} - Created at: {1}".format(output[len(bpy.path.abspath("//")):], output[:len(bpy.path.abspath("//"))]))
        return {'FINISHED'}


classes = [
    PieSaveOpen,
    ExternalData,
    FileIncrementalSave,
    pie_fileio,
    pie_recover,
    pie_link,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Save/Open/...
        km = wm.keyconfigs.addon.keymaps.new(name='Window')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'S', 'PRESS', ctrl=True)
        kmi.properties.name = "pie.saveopen"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Window']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.saveopen":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
