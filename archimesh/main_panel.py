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
# File: main_panel.py
# Main panel for different Archimesh general actions
# Author: Antonio Vazquez (antonioya)
#
#----------------------------------------------------------
import bpy
from tools import *

#-----------------------------------------------------
# Verify if boolean already exist
#-----------------------------------------------------
def isBoolean(myObject,childObject):
    flag = False
    for mod in myObject.modifiers:
            if mod.type == 'BOOLEAN':
                if mod.object == childObject:
                    flag = True
                    break
    return flag        
#------------------------------------------------------
# Button: Action to link windows and doors
#------------------------------------------------------
class holeAction(bpy.types.Operator):
    bl_idname = "object.archimesh_cut_holes"
    bl_label = "Auto Holes"
    bl_description = "Enable windows and doors holes for any selected object"
    bl_category = 'Archimesh'

    #------------------------------
    # Execute
    #------------------------------
    def execute(self, context):
        scene = context.scene
        listObj = []
        #---------------------------------------------------------------------
        # Save the list of selected objects because the select flag is missed
        # only can be windows or doors
        #---------------------------------------------------------------------
        for obj in bpy.context.scene.objects:
            try:
                if obj["archimesh.hole_enable"] == True:
                    if obj.select == True or scene.archimesh_select_only == False:
                        listObj.extend([obj])   
            except:
                continue
        #---------------------------
        # Get the baseboard object  
        #---------------------------
        myBaseBoard = None
        for child in context.object.children:
            try:
                if child["archimesh.room_baseboard"] == True:
                    myBaseBoard = child 
            except:
                continue                
        #-----------------------------
        # Now apply Wall holes
        #-----------------------------
        for obj in listObj:
            parentObj = context.object
            # Parent the empty to the room (the parent of frame)
            if obj.parent != None:
                bpy.ops.object.select_all(action='DESELECT')
                parentObj.select = True
                obj.parent.select = True # parent of object
                bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)                    
            #---------------------------------------
            # Add the modifier to controller
            # and the scale to use the same thickness
            #---------------------------------------
            for child in obj.parent.children:
                try:
                    if child["archimesh.ctrl_hole"] == True:
                        # apply scale
                        t = parentObj.RoomGenerator[0].wall_width
                        if t > 0:
                            child.scale.y = (t  + 0.35) / (child.dimensions.y/child.scale.y) # Add some gap
                        else:
                            child.scale.y = 1     
                        # add boolean modifier
                        if isBoolean(context.object,child) == False:
                            set_modifier_boolean(context.object,child)
                except:
                    x = 1 # dummy            
        #---------------------------------------
        # Now add the modifiers to baseboard
        #---------------------------------------
        if myBaseBoard != None:
            for obj in bpy.context.scene.objects:
                try:
                    if obj["archimesh.ctrl_base"] == True:
                        if obj.select == True or scene.archimesh_select_only == False:
                            # add boolean modifier
                            if isBoolean(myBaseBoard,obj) == False:
                                set_modifier_boolean(myBaseBoard,obj)
                except:
                    x = 1 # dummy            
                    
        return {'FINISHED'}

#------------------------------------------------------------------
# Define panel class for main functions.
#------------------------------------------------------------------
class ArchimeshMainPanel(bpy.types.Panel):
    bl_idname      ="archimesh_main_panel"
    bl_label       ="Archimesh"
    bl_space_type  ='VIEW_3D'
    bl_region_type = "TOOLS"
    bl_category = 'Archimesh'

    #------------------------------
    # Draw UI
    #------------------------------
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        myObj = context.object
        #-------------------------------------------------------------------------
        # If the selected object didn't be created with the group 'RoomGenerator', 
        # this button is not created.
        #-------------------------------------------------------------------------
        try:
            if 'RoomGenerator' in myObj:
                box = layout.box()
                box.label("Room Tools",icon='MODIFIER')
                row = box.row(align=False)
                row.operator("object.archimesh_cut_holes", icon='GRID')
                row.prop(scene,"archimesh_select_only")
    
                # Export/Import
                row = box.row(align=False)
                row.operator("io_import.roomdata", text="Import",icon='COPYDOWN')
                row.operator("io_export.roomdata", text="Export",icon='PASTEDOWN')
        except:
            x = 1 # dummy line   
        #-------------------------------------------------------------------------
        # If the selected object isn't a kitchen 
        # this button is not created.
        #-------------------------------------------------------------------------
        try:
            if myObj["archimesh.sku"] != None:
                box = layout.box()
                box.label("Kitchen Tools",icon='MODIFIER')
                # Export
                row = box.row(align=False)
                row.operator("io_export.kitchen_inventory", text="Export inventory",icon='PASTEDOWN')
        except:
            x = 1 # dummy line   
            
        #------------------------------
        # Elements Buttons
        #------------------------------
        box = layout.box()
        box.label("Elements", icon='GROUP')
        row = box.row()
        row.operator("mesh.archimesh_room")
        row.operator("mesh.archimesh_column")
        row = box.row()
        row.operator("mesh.archimesh_door")
        row.operator("mesh.archimesh_window")
        row = box.row()
        row.operator("mesh.archimesh_kitchen")
        row.operator("mesh.archimesh_shelves")
        row = box.row()
        row.operator("mesh.archimesh_stairs")
        row.operator("mesh.archimesh_roof")
        
        #------------------------------
        # Prop Buttons
        #------------------------------
        box = layout.box()
        box.label("Props",icon='LAMP_DATA')
        row = box.row()
        row.operator("mesh.archimesh_books")
        row.operator("mesh.archimesh_lamp")
        row = box.row()
        row.operator("mesh.archimesh_venetian")
        row.operator("mesh.archimesh_roller")
        row = box.row()
        row.operator("mesh.archimesh_japan")
            
