# ##### BEGIN GPL LICENSE BLOCK #####
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

#
#
#  Authors           : Clemens Barth (Blendphys@root-1.de), ...
#
#  Homepage(Wiki)    : http://development.root-1.de/Atomic_Blender.php
#
#  Start of project              : 2011-12-01 by Clemens Barth
#  First publication in Blender  : 2012-11-03
#  Last modified                 : 2013-01-17
#
#  Acknowledgements 
#  ================
#
#  Blender: ideasman, meta_androcto, truman, kilon, CoDEmanX, dairin0d, PKHG, 
#           Valter, ...
#  Other: Frank Palmino
#

bl_info = {
    "name": "Atomic Blender - Utilities",
    "description": "Utilities for manipulating atom structures",
    "author": "Clemens Barth",
    "version": (0, 8),
    "blender": (2, 60, 0),
    "location": "Panel: View 3D - Tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/Import-Export/PDB",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "index.php?func=detail&aid=33071&group_id=153&atid=467",
    "category": "Import-Export"
}

import bpy
from bpy.types import Operator, Panel
from bpy.props import (StringProperty,
                       EnumProperty,
                       FloatProperty)

from . import io_atomblend_utilities

# -----------------------------------------------------------------------------
#                                                                           GUI

# The panel.
class PreparePanel(Panel):
    bl_label       = "Atomic Blender Utilities"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"

    def draw(self, context):
        layout = self.layout
        scn    = context.scene.atom_blend

        box = layout.box()
        col = box.column(align=True) 
        col.label(text="Custom data file")
        col.prop(scn, "datafile")
        col.operator("atom_blend.datafile_apply")
        
        box = layout.box()  
        col = box.column(align=True)   
        col.label(text="Measure distances")
        col.operator("atom_blend.button_distance")
        col.prop(scn, "distance")
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="All changes concern:")
        col.prop(scn, "obj_who")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Change atom size")
        col.label(text="1. Type of radii")
        col.prop(scn, "radius_type")
        col2 = col.column()
        col2.active = (scn.radius_type == '3')
        col2.prop(scn, "radius_type_ionic")   
        col = box.column(align=True)
        col.label(text="2. Radii in pm")
        col.prop(scn, "radius_pm_name")
        col.prop(scn, "radius_pm")
        col = box.column(align=True)
        col.label(text="3. Radii by scale")
        col.prop(scn, "radius_all")
        row = col.row()
        row.operator("atom_blend.radius_all_smaller")
        row.operator("atom_blend.radius_all_bigger")
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Change stick size")
        col.prop(scn, "sticks_all")
        row = col.row()
        row.operator("atom_blend.sticks_all_smaller")
        row.operator("atom_blend.sticks_all_bigger")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Separate atoms")
        col2 = col.column()
        col2.active = (bpy.context.mode == 'EDIT_MESH')
        col2.prop(scn, "separate_objs")
        col2.operator("atom_blend.separate_atom")
        


# The properties of buttons etc. in the panel.
class PanelProperties(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scn = bpy.context.scene.atom_blend
        io_atomblend_utilities.choose_objects("radius_type", 
                                              scn.obj_who, 
                                              None,
                                              None,
                                              scn.radius_type,
                                              scn.radius_type_ionic,
                                              None) 
    def Callback_radius_pm(self, context):
        scn = bpy.context.scene.atom_blend
        io_atomblend_utilities.choose_objects("radius_pm", 
                                              scn.obj_who, 
                                              None,
                                              [scn.radius_pm_name,
                                              scn.radius_pm],
                                              None,
                                              None,
                                              None) 
        
    datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    XYZ_file = StringProperty(
        name = "Path to file", default="",
        description = "Path of the XYZ file")
    number_atoms = StringProperty(name="",
        default="Number", description = "This output shows "
        "the number of atoms which have been loaded")
    distance = StringProperty(
        name="", default="Distance (A)",
        description="Distance of 2 objects in Angstrom")
    obj_who = EnumProperty(
        name="",
        description="Which objects shall be modified?",
        items=(('ALL_ACTIVE',"all active objects", "in the current layer"),
               ('ALL_IN_LAYER',"all in all selected layers",
                "in selected layer(s)")),
               default='ALL_ACTIVE',)
    radius_type = EnumProperty(
        name="Type",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii"),
               ('3',"ionic radii", "Use ionic radii")),
               default='0',update=Callback_radius_type)
    radius_type_ionic = EnumProperty(
        name="Charge",
        description="Charge state of the ions if existing.",
        items=(('0',"-4", "Charge state -4"),
               ('1',"-3", "Charge state -3"),
               ('2',"-2", "Charge state -2"),
               ('3',"-1", "Charge state -1"),
               ('4'," 0", "Charge state  0: nothing is done"),              
               ('5',"+1", "Charge state +1"),
               ('6',"+2", "Charge state +2"),
               ('7',"+3", "Charge state +3"),
               ('8',"+4", "Charge state +4"),
               ('9',"+5", "Charge state +5"),
               ('10',"+6", "Charge state +6"),
               ('11',"+7", "Charge state +7")),
               default='4',update=Callback_radius_type)           
    radius_pm_name = StringProperty(
        name="", default="Atom name",
        description="Put in the name of the atom (e.g. Hydrogen)")
    radius_pm = FloatProperty(
        name="", default=100.0, min=0.0,
        description="Put in the radius of the atom (in pm)",
        update=Callback_radius_pm)
    radius_all = FloatProperty(
        name="Scale", default = 1.05, min=1.0, max=5.0,
        description="Put in the scale factor")
    sticks_all = FloatProperty(
        name="Scale", default = 1.05, min=1.0, max=5.0,
        description="Put in the scale factor")
    separate_objs = EnumProperty(
        name="Object",
        description="Replace ball by another object.",
        items=(('0',"Unchanged", "Use again a ball"),
               ('1',"Cube", "Replace with a cube"),
               ('2',"Plane", "Replace with a plane"),
               ('3',"Circle", "Replace with a circle"),
               ('4',"Icosphere", "Replace with a icosphere"),              
               ('5',"Cylinder", "Replace with a cylinder"),
               ('6',"Cone", "Replace with a cone"),
               ('7',"Torus", "Replace with a torus")),
               default='0',)     

# Button loading a custom data file
class DatafileApply(Operator):
    bl_idname = "atom_blend.datafile_apply"
    bl_label = "Apply"
    bl_description = "Use color and radii values stored in the custom file"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend

        if scn.datafile == "":
            return {'FINISHED'}

        io_atomblend_utilities.custom_datafile(scn.datafile)
        io_atomblend_utilities.custom_datafile_change_atom_props()

        return {'FINISHED'}


# Button for separating single atoms from a dupliverts structure
class SeparateAtom(Operator):
    bl_idname = "atom_blend.separate_atom"
    bl_label = "Separate atoms"
    bl_description = ("Separate atoms you have selected. "
                      "You have to be in the 'Edit Mode'")

    def execute(self, context):
        scn = bpy.context.scene.atom_blend

        io_atomblend_utilities.separate_atoms(scn)

        return {'FINISHED'}


# Button for measuring the distance of active objects
class DistanceButton(Operator):
    bl_idname = "atom_blend.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two objects"

    def execute(self, context):
        scn  = bpy.context.scene.atom_blend
        dist = io_atomblend_utilities.distance()

        # Put the distance into the string of the output field.
        scn.distance = dist
        return {'FINISHED'}


# Button for increasing the radii of all selected atoms
class RadiusAllBiggerButton(Operator):
    bl_idname = "atom_blend.radius_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend     
        io_atomblend_utilities.choose_objects("radius_all", 
                                              scn.obj_who, 
                                              scn.radius_all, 
                                              None,
                                              None,
                                              None,
                                              None)        
        return {'FINISHED'}


# Button for decreasing the radii of all selected atoms
class RadiusAllSmallerButton(Operator):
    bl_idname = "atom_blend.radius_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        io_atomblend_utilities.choose_objects("radius_all", 
                                              scn.obj_who, 
                                              1.0/scn.radius_all, 
                                              None,
                                              None,
                                              None,
                                              None)                                     
        return {'FINISHED'}

# Button for increasing the radii of all selected sticks
class SticksAllBiggerButton(Operator):
    bl_idname = "atom_blend.sticks_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of the sticks"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend     
        io_atomblend_utilities.choose_objects("sticks_all", 
                                              scn.obj_who, 
                                              None, 
                                              None,
                                              None,
                                              None,
                                              scn.sticks_all)        
        return {'FINISHED'}


# Button for decreasing the radii of all selected sticks
class SticksAllSmallerButton(Operator):
    bl_idname = "atom_blend.sticks_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of the sticks"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        io_atomblend_utilities.choose_objects("sticks_all", 
                                              scn.obj_who, 
                                              None, 
                                              None,
                                              None,
                                              None,
                                              1.0/scn.sticks_all)                                     
        return {'FINISHED'}


def register():
    io_atomblend_utilities.read_elements()  
    bpy.utils.register_module(__name__)
    bpy.types.Scene.atom_blend = bpy.props.PointerProperty(type=
                                                   PanelProperties)

def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":

    register()
