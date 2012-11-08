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
#  Last modified                 : 2012-11-08
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
    "version": (0,5),
    "blender": (2,6),
    "location": "Panel: View 3D - Tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/Import-Export/PDB",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "index.php?func=detail&aid=33071&group_id=153&atid=467",
    "category": "Import-Export"
}

import os
import io
import bpy
import bmesh
from bpy.types import Operator, Panel
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)

from . import io_atomblend_utilities


# -----------------------------------------------------------------------------
#                                                                           GUI

# This is the panel, which can be used to prepare the scene.
# It is loaded after the file has been chosen via the menu 'File -> Import'
class PreparePanel(Panel):
    bl_label       = "Atomic Blender Utilities"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"

    def draw(self, context):
        layout = self.layout
        scn    = context.scene.atom_blend[0]

        row = layout.row()
        row.label(text="Custom data file")
        box = layout.box()
        row = box.row()
        row.label(text="Custom data file")
        row = box.row()
        col = row.column()
        col.prop(scn, "datafile")
        col.operator("atom_blend.datafile_apply")
        row = box.row()
        row.operator("atom_blend.button_distance")
        row.prop(scn, "distance")
        row = layout.row()
        row.label(text="Choice of atom radii")
        box = layout.box()
        row = box.row()
        row.label(text="All changes concern:")
        row = box.row()
        row.prop(scn, "radius_how")
        row = box.row()
        row.label(text="1. Change type of radii")
        row = box.row()
        row.prop(scn, "radius_type")
        row = box.row()
        row.label(text="2. Change atom radii in pm")
        row = box.row()
        row.prop(scn, "radius_pm_name")
        row = box.row()
        row.prop(scn, "radius_pm")
        row = box.row()
        row.label(text="3. Change atom radii by scale")
        row = box.row()
        col = row.column()
        col.prop(scn, "radius_all")
        col = row.column(align=True)
        col.operator( "atom_blend.radius_all_bigger" )
        col.operator( "atom_blend.radius_all_smaller" )

        layout.separator()
        row = box.row()
        row.active = (bpy.context.mode == 'EDIT_MESH')
        row.operator( "atom_blend.separate_atom" )



class PanelProperties(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scn = bpy.context.scene.atom_blend[0]
        io_atomblend_utilities.DEF_atom_blend_radius_type(
                scn.radius_type,
                scn.radius_how,)

    def Callback_radius_pm(self, context):
        scn = bpy.context.scene.atom_blend[0]
        io_atomblend_utilities.DEF_atom_blend_radius_pm(
                scn.radius_pm_name,
                scn.radius_pm,
                scn.radius_how,)

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
    radius_how = EnumProperty(
        name="",
        description="Which objects shall be modified?",
        items=(('ALL_ACTIVE',"all active objects", "in the current layer"),
               ('ALL_IN_LAYER',"all"," in active layer(s)")),
               default='ALL_ACTIVE',)
    radius_type = EnumProperty(
        name="Type",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii")),
               default='0',update=Callback_radius_type)
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



# Button loading a custom data file
class DatafileApply(Operator):
    bl_idname = "atom_blend.datafile_apply"
    bl_label = "Apply"
    bl_description = "Use color and radii values stored in the custom file"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]

        if scn.datafile == "":
            return {'FINISHED'}

        io_atomblend_utilities.DEF_atom_blend_custom_datafile(scn.datafile)

        for obj in bpy.context.selected_objects:
            if len(obj.children) != 0:
                child = obj.children[0]
                if child.type in {'SURFACE', 'MESH'}:
                    for element in io_atomblend_utilities.ATOM_BLEND_ELEMENTS:
                        if element.name in obj.name:
                            child.scale = (element.radii[0],) * 3
                            child.active_material.diffuse_color = element.color
            else:
                if obj.type in {'SURFACE', 'MESH'}:
                    for element in io_atomblend_utilities.ATOM_BLEND_ELEMENTS:
                        if element.name in obj.name:
                            obj.scale = (element.radii[0],) * 3
                            obj.active_material.diffuse_color = element.color

        return {'FINISHED'}


# Button for separating a single atom from a structure
class SeparateAtom(Operator):
    bl_idname = "atom_blend.separate_atom"
    bl_label = "Separate atoms"
    bl_description = ("Separate atoms you have selected. "
                      "You have to be in the 'Edit Mode'")

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]

        # Get first all important properties from the atoms, which the user
        # has chosen: location, color, scale
        obj = bpy.context.edit_object
        
        # Do nothing if it is not a dupliverts structure.
        if not obj.dupli_type == "VERTS":
            return {'FINISHED'}
        
        bm = bmesh.from_edit_mesh(obj.data)

        locations = []

        for v in bm.verts:
            if v.select:
                locations.append(obj.matrix_world * v.co)

        bm.free()
        del(bm)

        name  = obj.name
        scale = obj.children[0].scale
        material = obj.children[0].active_material

        # Separate the vertex from the main mesh and create a new mesh.
        bpy.ops.mesh.separate()
        new_object = bpy.context.scene.objects[0]
        # And now, switch to the OBJECT mode such that we can ...
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # ... delete the new mesh including the separated vertex
        bpy.ops.object.select_all(action='DESELECT')
        new_object.select = True
        bpy.ops.object.delete()  

        # Create new atoms/vacancies at the position of the old atoms
        current_layers=bpy.context.scene.layers

        # For all selected positions do:
        for location in locations:
            # For any ball do ...
            if "Vacancy" not in name:
                # NURBS ball
                if obj.children[0].type == "SURFACE":
                    bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                    view_align=False, enter_editmode=False,
                                    location=location,
                                    rotation=(0.0, 0.0, 0.0),
                                    layers=current_layers)
                # Mesh ball                    
                elif obj.children[0].type == "MESH":
                    bpy.ops.mesh.primitive_uv_sphere_add(
                                segments=32,
                                ring_count=32,                    
                                #segments=scn.mesh_azimuth,
                                #ring_count=scn.mesh_zenith,
                                size=1, view_align=False, enter_editmode=False,
                                location=location,
                                rotation=(0, 0, 0),
                                layers=current_layers)
            # If it is a vacancy create a cube ...                    
            else:
                bpy.ops.mesh.primitive_cube_add(
                               view_align=False, enter_editmode=False,
                               location=location,
                               rotation=(0.0, 0.0, 0.0),
                               layers=current_layers)

            new_atom = bpy.context.scene.objects.active
            # Scale, material and name it.
            new_atom.scale = scale
            new_atom.active_material = material
            new_atom.name = name + "_sep"
            new_atom.select = True

        bpy.context.scene.objects.active = obj
        #bpy.ops.object.select_all(action='DESELECT')

        return {'FINISHED'}


# Button for measuring the distance of the active objects
class DistanceButton(Operator):
    bl_idname = "atom_blend.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two objects"

    def execute(self, context):
        scn  = bpy.context.scene.atom_blend[0]
        dist = io_atomblend_utilities.DEF_atom_blend_distance()

        if dist != "N.A.":
            # The string length is cut, 3 digits after the first 3 digits
            # after the '.'. Append also "Angstrom".
            # Remember: 1 Angstrom = 10^(-10) m
            pos    = str.find(dist, ".")
            dist   = dist[:pos+4]
            dist   = dist + " A"

        # Put the distance into the string of the output field.
        scn.distance = dist
        return {'FINISHED'}


# Button for increasing the radii of all atoms
class RadiusAllBiggerButton(Operator):
    bl_idname = "atom_blend.radius_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]
        io_atomblend_utilities.DEF_atom_blend_radius_all(
                scn.radius_all,
                scn.radius_how,
                )
        return {'FINISHED'}


# Button for decreasing the radii of all atoms
class RadiusAllSmallerButton(Operator):
    bl_idname = "atom_blend.radius_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]
        io_atomblend_utilities.DEF_atom_blend_radius_all(
                1.0/scn.radius_all,
                scn.radius_how,
                )
        return {'FINISHED'}




def register():
    io_atomblend_utilities.DEF_atom_blend_read_elements()  
    bpy.utils.register_module(__name__)
    bpy.types.Scene.atom_blend = bpy.props.CollectionProperty(type=
                                                   PanelProperties)
    bpy.context.scene.atom_blend.add()


    
def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":

    register()
