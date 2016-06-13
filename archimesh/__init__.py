# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


#----------------------------------------------------------
# File: __init__.py
# Author: Antonio Vazquez (antonioya)
#----------------------------------------------------------
 
#----------------------------------------------
# Define Addon info
#----------------------------------------------
bl_info = {
    "name": "Archimesh",
    "author": "Antonio Vazquez (antonioya)",
    "location": "View3D > Add > Mesh > Archimesh",
    "version": (0, 8, 1),
    "blender": (2, 7, 7),
    "description": "Generate rooms, doors, windows, kitchen cabinets, shelves, roofs, stairs and other architecture stuff.",
    "category": "Add Mesh"}

import sys,os

#----------------------------------------------
# Add to Phyton path (once only)
#----------------------------------------------
path = sys.path
flag = False
for item in path:
    if "archimesh" in item:
        flag = True
if flag == False:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'archimesh'))
    print("archimesh: added to phytonpath")

#----------------------------------------------
# Import modules
#----------------------------------------------
if "bpy" in locals():
    import imp
    imp.reload(room_maker)
    imp.reload(door_maker)
    imp.reload(window_maker)
    imp.reload(roof_maker)
    imp.reload(column_maker)
    imp.reload(stairs_maker)
    imp.reload(kitchen_maker)
    imp.reload(shelves_maker)
    imp.reload(books_maker)
    imp.reload(lamp_maker)
    imp.reload(curtain_maker)
    imp.reload(main_panel)
    print("archimesh: Reloaded multifiles")
else:
    from . import room_maker, door_maker,roof_maker,column_maker,stairs_maker,kitchen_maker,shelves_maker
    from . import books_maker,curtain_maker,window_maker,lamp_maker,main_panel
    print("archimesh: Imported multifiles")

import bpy 
from bpy.props import *

#----------------------------------------------------------
# Decoration assets
#----------------------------------------------------------
class INFO_MT_mesh_decoration_add(bpy.types.Menu):
    # Define the "Math Function" menu
    bl_idname = "INFO_MT_mesh_decoration_add"
    bl_label = "Decoration assets"

    def draw(self, context):
        self.layout.operator("mesh.archimesh_books", text="Add Books",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_lamp", text="Add Lamp",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_roller", text="Add Roller curtains",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_venetian", text="Add Venetian blind",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_japan", text="Add Japanese curtains",icon="PLUGIN")
    
#----------------------------------------------------------
# Registration
#----------------------------------------------------------
class INFO_MT_mesh_custom_menu_add(bpy.types.Menu):
    bl_idname = "INFO_MT_mesh_custom_menu_add"
    bl_label = "Archimesh"
    
    def draw(self, context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.operator("mesh.archimesh_room", text="Add Room",icon="PLUGIN");
        self.layout.operator("mesh.archimesh_door", text="Add Door",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_window", text="Add Window",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_kitchen", text="Add Cabinet",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_shelves", text="Add Shelves",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_column", text="Add Column",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_stairs", text="Add Stairs",icon="PLUGIN")
        self.layout.operator("mesh.archimesh_roof", text="Add Roof",icon="PLUGIN")
        self.layout.menu("INFO_MT_mesh_decoration_add", text="Decoration props",icon="GROUP")

#--------------------------------------------------------------
# Register all operators and panels
#--------------------------------------------------------------
# Define menu
def menu_func(self, context):
    self.layout.menu("INFO_MT_mesh_custom_menu_add", icon="PLUGIN")

def register():
    bpy.utils.register_class(INFO_MT_mesh_custom_menu_add)
    bpy.utils.register_class(INFO_MT_mesh_decoration_add)
    bpy.utils.register_class(room_maker.ROOM)
    bpy.utils.register_class(room_maker.RoomGeneratorPanel)
    bpy.utils.register_class(room_maker.EXPORT_ROOM)
    bpy.utils.register_class(room_maker.IMPORT_ROOM)
    bpy.utils.register_class(door_maker.DOOR)
    bpy.utils.register_class(window_maker.WINDOWS)
    bpy.utils.register_class(roof_maker.ROOF)
    bpy.utils.register_class(column_maker.COLUMN)
    bpy.utils.register_class(stairs_maker.STAIRS)
    bpy.utils.register_class(kitchen_maker.KITCHEN)
    bpy.utils.register_class(kitchen_maker.EXPORT_INVENTORY)
    bpy.utils.register_class(shelves_maker.SHELVES)
    bpy.utils.register_class(books_maker.BOOKS)
    bpy.utils.register_class(lamp_maker.LAMP)
    bpy.utils.register_class(curtain_maker.ROLLER)
    bpy.utils.register_class(curtain_maker.VENETIAN)
    bpy.utils.register_class(curtain_maker.JAPAN)
    bpy.utils.register_class(main_panel.ArchimeshMainPanel)
    bpy.utils.register_class(main_panel.holeAction)
    bpy.types.INFO_MT_mesh_add.append(menu_func)
    
    # Define properties
    bpy.types.Scene.archimesh_select_only = bpy.props.BoolProperty(name = "Only selected"
                                                                   ,description="Apply auto holes only to selected objects",default = False)
    
    
def unregister():
    bpy.utils.unregister_class(INFO_MT_mesh_custom_menu_add)
    bpy.utils.unregister_class(INFO_MT_mesh_decoration_add)
    bpy.utils.unregister_class(room_maker.ROOM)
    bpy.utils.unregister_class(room_maker.RoomGeneratorPanel)
    bpy.utils.unregister_class(room_maker.EXPORT_ROOM)
    bpy.utils.unregister_class(room_maker.IMPORT_ROOM)
    bpy.utils.unregister_class(door_maker.DOOR)
    bpy.utils.unregister_class(window_maker.WINDOWS)
    bpy.utils.unregister_class(roof_maker.ROOF)
    bpy.utils.unregister_class(column_maker.COLUMN)
    bpy.utils.unregister_class(stairs_maker.STAIRS)
    bpy.utils.unregister_class(kitchen_maker.KITCHEN)
    bpy.utils.unregister_class(kitchen_maker.EXPORT_INVENTORY)
    bpy.utils.unregister_class(shelves_maker.SHELVES)
    bpy.utils.unregister_class(books_maker.BOOKS)
    bpy.utils.unregister_class(lamp_maker.LAMP)
    bpy.utils.unregister_class(curtain_maker.ROLLER)
    bpy.utils.unregister_class(curtain_maker.VENETIAN)
    bpy.utils.unregister_class(curtain_maker.JAPAN)
    bpy.utils.unregister_class(main_panel.ArchimeshMainPanel)
    bpy.utils.unregister_class(main_panel.holeAction)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    
    # Remove properties
    del bpy.types.Scene.archimesh_select_only

if __name__ == '__main__':
    register()

