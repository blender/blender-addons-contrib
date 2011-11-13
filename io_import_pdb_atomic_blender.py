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
#  The main author of the script is Dr. Clemens Barth.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
  "name": "Atomic Blender",
  "description": "Loading and manipulating atoms from PDB files",
  "author": "Dr. Clemens Barth",
  "version": (1,11),
  "blender": (2,6),
  "api": 31236,
  "location": "Properties > Physics => Panel Atomic Blender",
  "warning": "",
  "wiki_url": "http://development.root-1.de/Atomic_Blender.php",
  "tracker_url": "http://projects.blender.org/tracker/?func=detail&atid=467&aid=29226&group_id=153",
  "category": "Import-Export"
}

import bpy
import io
import sys
import os
from math import *
import mathutils, math
from mathutils import Vector
#
PDBFILE   = "PATH TO PDB FILE"
DATAFILE  = "PATH TO DATA FILE"

Atomic_Blender_string     = "Atomic Blender 1.1 -- Dr. Clemens Barth -- November 2011\n======================================================="
Atomic_Blender_panel_name = "Atomic Blender 1.1"


class OBJECT_PDB_Panel(bpy.types.Panel):
    bl_label       = Atomic_Blender_panel_name
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "physics"

    def draw(self, context):
        layout = self.layout
        scn    = bpy.context.scene


        layout.operator( "fp.button_delete_all" )
        row = layout.row()
        layout.operator( "fp.button_delete_atoms" )
        layout.operator( "fp.button_delete_camlamp" )
        row = layout.row()
        layout.prop(scn, "pdb_filepath")
        layout.prop(scn, "data_filepath")
        row = layout.row()

        row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

        row = layout.row()
        row.prop(scn, "entry_group_atoms_yesno")
        row = layout.row()
        row.prop(scn, "entry_group_atoms_dn")
        row = layout.row()

        row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        row = layout.row()
        
        row.prop(scn, "entry_mesh_yesno")
        row = layout.row()
        row.prop(scn, "entry_sectors_azimuth")
        row.prop(scn, "entry_sectors_zenith")
        
        row = layout.row()
        row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        row = layout.row()

        row.label(text="Scaling factors")
        row = layout.row()
        row.prop(scn, "entry_ball_radius")
        row.prop(scn, "entry_distances")

        row = layout.row()
        row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        row = layout.row()
        
        row.prop(scn, "entry_sticks_yesno")
        row = layout.row()
        row.prop(scn, "entry_sticks_sectors")
        row.prop(scn, "entry_sticks_radius")

        row = layout.row()
        row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        row = layout.row()
        
        row.prop(scn, "entry_center_yesno")
        row = layout.row()    
        row = layout.row()
        row.label(text="Now, use an offset for all objects")
        row = layout.row()
        row.prop(scn, "entry_scene_x")
        row.prop(scn, "entry_scene_y")
        row.prop(scn, "entry_scene_z")
       
        row = layout.row()
        row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        row = layout.row()
        
        row.prop(scn, "entry_cam_yesno")
        row.prop(scn, "entry_lamp_yesno")
        row = layout.row()  
        layout.operator( "fp.button_start" )
        row = layout.row()  
        row.label(text="No. of atoms: ")
        row.prop(scn, "entry_start_number_atoms")
        
        if scn.entry_group_atoms_yesno == False:        
            row = layout.row()       
            row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
            row = layout.row()
            row.prop(scn, "entry_distance")
            layout.operator( "fp.button_distance" )        
            row = layout.row()       
            row.label("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
            row = layout.row()
            row.label(text="Modification of the radii of one type of atom")
            row = layout.row()
            row.prop(scn, "entry_mod_atomname")
            row = layout.row()
            row.prop(scn, "entry_mod_pm_yesno")
            row.prop(scn, "entry_mod_pm_radius")
            row = layout.row()
            row.prop(scn, "entry_mod_rel_yesno")
            row.prop(scn, "entry_mod_rel_radius")
            layout.operator( "fp.button_modify" )
            row = layout.row()
            row.label(text="Modification of all atom radii")
            row = layout.row()
            row.prop(scn, "entry_mod_all_radii")
            layout.operator( "fp.button_modify_2" )




class CLASS_Distance_Button(bpy.types.Operator):
    bl_idname = "fp.button_distance"
    bl_label = "Measure ..."

    def execute(self, context):
        dist   = Measure_distance_in_scene()

        if dist != "-1.0":
           # The string length gets cut. Cut 3 digits after the '.' the string. 
           pos    = str.find(dist, ".")
           dist   = dist[:pos+4] 

        # Actualization of the distance in the string input.
        scn                = bpy.context.scene
        scn.entry_distance = dist
        return {'FINISHED'}

class CLASS_Deleteall_Button(bpy.types.Operator):
    bl_idname = "fp.button_delete_all"
    bl_label = "Delete all in the scene ..."

    def execute(self, context):
        Delete_all_in_scene()
        return {'FINISHED'}
        
class CLASS_Delete_atoms_Button(bpy.types.Operator):
    bl_idname = "fp.button_delete_atoms"
    bl_label = "Delete all atoms ..."

    def execute(self, context):
        Delete_atoms_in_scene()
        return {'FINISHED'}      
        
class CLASS_Delete_camlamp_Button(bpy.types.Operator):
    bl_idname = "fp.button_delete_camlamp"
    bl_label = "Delete cameras and lamps ..."

    def execute(self, context):
        Delete_camlamp_in_scene()
        return {'FINISHED'}   
  
class CLASS_Modify_Button(bpy.types.Operator):
    bl_idname = "fp.button_modify"
    bl_label = "Modify ..."

    def execute(self, context):
        scn = bpy.context.scene
        atomname   = scn.entry_mod_atomname
        radius_pm  = scn.entry_mod_pm_radius
        radius_rel = scn.entry_mod_rel_radius
        check_pm   = scn.entry_mod_pm_yesno
        check_rel  = scn.entry_mod_rel_yesno
        Modify_atom_radii_scene(atomname, radius_pm, check_pm, radius_rel, check_rel)
        return {'FINISHED'}

class CLASS_Modify_Button_2(bpy.types.Operator):
    bl_idname = "fp.button_modify_2"
    bl_label = "Modify ..."

    def execute(self, context):
        scn = bpy.context.scene
        scale   = scn.entry_mod_all_radii
        Modify_atom_radii_scene_2(scale)
        return {'FINISHED'}

class CLASS_Start_Button(bpy.types.Operator):
    bl_idname = "fp.button_start"
    bl_label = "DRAW THE OBJECT ..."
    
    def execute(self, context):
        scn = bpy.context.scene

        azimuth   = scn.entry_sectors_azimuth
        zenith    = scn.entry_sectors_zenith 
        bradius   = scn.entry_ball_radius
        bdistance = scn.entry_distances
        center    = scn.entry_center_yesno 
        x         = scn.entry_scene_x
        y         = scn.entry_scene_y
        z         = scn.entry_scene_z
        yn        = scn.entry_sticks_yesno 
        ssector   = scn.entry_sticks_sectors
        sradius   = scn.entry_sticks_radius
        pdb       = scn.pdb_filepath
        data      = scn.data_filepath
        cam       = scn.entry_cam_yesno 
        lamp      = scn.entry_lamp_yesno
        mesh      = scn.entry_mesh_yesno 
        group     = scn.entry_group_atoms_yesno
        dn        = scn.entry_group_atoms_dn
        
        # This here is just to study this strange 'relative path' thing in the file dialog.
        # Sometimes it doesn't work.
        #print(scn.pdb_filepath)
        #return {'FINISHED'}
        
        atom_number                  = Draw_scene(group,dn,mesh,azimuth,zenith,bradius,bdistance,x,y,z,yn,ssector,sradius,center,cam,lamp,pdb,data)
        scn.entry_start_number_atoms = atom_number

        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_PDB_Panel)
    bpy.utils.register_class(CLASS_Start_Button)
    bpy.utils.register_class(CLASS_Modify_Button)
    bpy.utils.register_class(CLASS_Modify_Button_2)
    bpy.utils.register_class(CLASS_Deleteall_Button)
    bpy.utils.register_class(CLASS_Delete_atoms_Button)
    bpy.utils.register_class(CLASS_Delete_camlamp_Button)
    bpy.utils.register_class(CLASS_Distance_Button)

def unregister():
    bpy.utils.unregister_class(OBJECT_PDB_Panel)
    bpy.utils.unregister_class(CLASS_Start_Button)
    bpy.utils.unregister_class(CLASS_Modify_Button)
    bpy.utils.unregister_class(CLASS_Modify_Button_2)
    bpy.utils.unregister_class(CLASS_Deleteall_Button)
    bpy.utils.unregister_class(CLASS_Delete_atoms_Button)
    bpy.utils.unregister_class(CLASS_Delete_camlamp_Button)
    bpy.utils.unregister_class(CLASS_Distance_Button)    
        

if __name__ == "__main__":

    bpy.types.Scene.pdb_filepath              = bpy.props.StringProperty(name = "PDB  File", description="Path to the PDB file", maxlen = 256, default = PDBFILE, subtype='FILE_PATH', options={'HIDDEN'})
    bpy.types.Scene.data_filepath             = bpy.props.StringProperty(name = "DATA File", description="Path to the dat file", maxlen = 256, default = DATAFILE, subtype='FILE_PATH')
    bpy.types.Scene.entry_group_atoms_yesno   = bpy.props.BoolProperty  (name = "Group same type of atoms", default=False, description = "Grouping same type of atoms speeds up the loading of large-atom-PDB files")    
    bpy.types.Scene.entry_group_atoms_dn      = bpy.props.IntProperty   (name = "Delta N", default=200, min=0, description = "")
    bpy.types.Scene.entry_mesh_yesno          = bpy.props.BoolProperty  (name = "Mesh instead of NURBS", default=False, description = "Yes or no")    
    bpy.types.Scene.entry_sectors_azimuth     = bpy.props.IntProperty   (name = "Azimuth", default=32, min=0, description = "")
    bpy.types.Scene.entry_sectors_zenith      = bpy.props.IntProperty   (name = "Zenith", default=32, min=0, description = "")
    bpy.types.Scene.entry_ball_radius         = bpy.props.FloatProperty (name = "Ball", default=1.0, min=0.0, description = "Ball radius")
    bpy.types.Scene.entry_distances           = bpy.props.FloatProperty (name = "Distance", default=1.0, min=0.0, description = "All distances")
    bpy.types.Scene.entry_center_yesno        = bpy.props.BoolProperty  (name = "Put to center", default=True, description = "Yes or no")    
    bpy.types.Scene.entry_scene_x             = bpy.props.FloatProperty (name = "X", default=0.0, description = "X coordinate")
    bpy.types.Scene.entry_scene_y             = bpy.props.FloatProperty (name = "Y", default=0.0, description = "Y coordinate")
    bpy.types.Scene.entry_scene_z             = bpy.props.FloatProperty (name = "Z", default=0.0, description = "Z coordinate")
    bpy.types.Scene.entry_sticks_yesno        = bpy.props.BoolProperty  (name = "Use sticks", default=False, description = "Shall sticks connect the atoms?")    
    bpy.types.Scene.entry_sticks_sectors      = bpy.props.IntProperty   (name = "Sector", default = 20, min=0,   description = "Number of sectors of a stick")        
    bpy.types.Scene.entry_sticks_radius       = bpy.props.FloatProperty (name = "Radius", default =  0.1, min=0.0, description = "Radius of a stick")  
    bpy.types.Scene.entry_cam_yesno           = bpy.props.BoolProperty  (name = "Camera", default=False, description = "Do you need a camera?")   
    bpy.types.Scene.entry_lamp_yesno          = bpy.props.BoolProperty  (name = "Lamp", default=False, description = "Do you need a lamp?")
    bpy.types.Scene.entry_start_number_atoms  = bpy.props.StringProperty(name = "", default="Number", description = "This output shows the number of atoms")
    bpy.types.Scene.entry_distance            = bpy.props.StringProperty(name = "", default="Distance", description = "Distance of 2 objects in Angstrom")  
    bpy.types.Scene.entry_mod_atomname        = bpy.props.StringProperty(name = "", default = "Name of atom", description="Put in the name of the atom (e.g. Hydrogen)")
    bpy.types.Scene.entry_mod_pm_yesno        = bpy.props.BoolProperty  (name = "Radius (pm)", default=False, description = "Modify the absolute value for the radius in pm")
    bpy.types.Scene.entry_mod_pm_radius       = bpy.props.FloatProperty (name = "", default = 100.0, min=0.0, description="Put in the radius of the atom (in pm)")
    bpy.types.Scene.entry_mod_rel_yesno       = bpy.props.BoolProperty  (name = "Radius (scale)", default=False, description = "Scale the radius with a factor")
    bpy.types.Scene.entry_mod_rel_radius      = bpy.props.FloatProperty (name = "", default = 1.0, min=0.0, description="Put in the scale factor")
    bpy.types.Scene.entry_mod_all_radii       = bpy.props.FloatProperty (name = "Radius (scale)", default = 1.0, min=0.0, description="Put in the scale factor")
           
    register()





########################################################
#
#
#
#
#
#
#          Some small routines
#
#
#
#
#
########################################################



# This function measures the distance between two objects (atoms), which are marked.
def Measure_distance_in_scene():

    if len(bpy.context.selected_bases) > 1:
        object_1 = bpy.context.selected_objects[0]
        object_2 = bpy.context.selected_objects[1]
    else:
        return "-1.0"

    v1     = object_1.location
    v2     = object_2.location
    dv     = (v2 - v1)
    length = str(dv.length)
    return length 


# This delets all what is in the scene.
def Delete_all_in_scene():

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # This seems to be stupid. But it is not!
    # The panel is in the 'physics' tab. If the user deletes all objects, the physics tab is
    # not visible anymore. In order to have at least one object that can be chosen in the object list, 
    # a cube is created at almost infinity.
    bpy.ops.mesh.primitive_cube_add(view_align=False, enter_editmode=False, location=(100000.0, 100000.0, 100000.0), rotation=(0.0, 0.0, 0.0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    tmp_object = bpy.context.scene.objects[0]
    
    
# This part is for deleting all existing atoms.
def Delete_atoms_in_scene():
  
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Go through all objects
    for obj in bpy.data.objects:

        # If a camera or lamp is not found, select the object
        if "camera" not in obj.name:
            if "lamp" not in obj.name:
                bpy.ops.object.select_name(name = obj.name, extend=True)
               
    #delete marked atoms
    bpy.ops.object.delete()
   
    bpy.ops.mesh.primitive_cube_add(view_align=False, enter_editmode=False, location=(100000.0, 100000.0, 100000.0), rotation=(0.0, 0.0, 0.0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    tmp_object = bpy.context.scene.objects[0]   
    bpy.ops.object.select_name(name = bpy.data.objects[0].name, extend=True)


# This part is for deleting all existing cameras and lamps.
def Delete_camlamp_in_scene():
   
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Go through all objects
    for obj in bpy.data.objects:

        # If a camera is found, select the camera
        if "camera" in obj.name:
            bpy.ops.object.select_name(name = obj.name, extend=True)

        # If a lamp is found, select the camera
        if "lamp" in obj.name:
            bpy.ops.object.select_name(name = obj.name, extend=True)
            
    #delete marked objects
    bpy.ops.object.delete()
    bpy.ops.mesh.primitive_cube_add(view_align=False, enter_editmode=False, location=(100000.0, 100000.0, 100000.0), rotation=(0.0, 0.0, 0.0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    tmp_object = bpy.context.scene.objects[0]      
    bpy.ops.object.select_name(name = bpy.data.objects[0].name, extend=True)


# Routine to modify the radii of a specific type of atom
def Modify_atom_radii_scene(atomname, radius_pm, check_pm, radius_rel, check_rel):

    for obj in bpy.data.objects:

        if atomname in obj.name:

            if check_pm == True:
                bpy.data.objects[obj.name].scale = (radius_pm/100,radius_pm/100,radius_pm/100)
            if check_rel == True:
                value = bpy.data.objects[obj.name].scale[0]
                bpy.data.objects[obj.name].scale = (radius_rel * value,radius_rel * value,radius_rel * value)


# Routine to scale the radii of all atoms
def Modify_atom_radii_scene_2(scale):

    for obj in bpy.data.objects:

        if "SURFACE" in obj.type:

            radius = bpy.data.objects[obj.name].scale[0]
            bpy.data.objects[obj.name].scale = (radius * scale,radius * scale,radius * scale)



########################################################
#
#
#
#
#
#          For reading the sticks inside the PDB file
#
#
#
#
#
########################################################



def Read_atom_for_stick(string):

    string_length = len(string)

    j               = 0
    string_reversed = ""
    atoms           = []
    space           = False
    # An atom number can have max 5 letters
    counter_letters = 5 
   
    for i in list(range(string_length)):
   
        # If the 'T' of 'CONECT' is read => exit
        if string[string_length-i-1] == 'T':
            break

        # Continue, if a space is read but no letter is present in 'string_reversed'.
        # This happens, when there are spaces behind the last atom number in the
        # string. 
        if string[string_length-i-1] == ' ' and string_reversed == "":
            continue
   
        if string[string_length-i-1] == ' ' or counter_letters == 0:
      
            string_correct         = ""
            string_reversed_length = len(string_reversed)
            l                      = 0
            for k in list(range(string_reversed_length)):
                string_correct = string_correct + string_reversed[string_reversed_length-k-1]
                l += 1
      
            # If the first 'space' is found, we found the number of an atom
            # Transform the string into an integer and append this to the overall list
            if space == False:
                atom            = int(string_correct)
                atoms.append(atom)
                # Initialization of the variables
                string_reversed = ""
                space           = True
            
            
            # If it was only a 'space' then go up the 'for loop'.
            if counter_letters != 0:
                counter_letters  = 5
                continue
            
            counter_letters = 5
   
   
        space            = False
        string_reversed  = string_reversed + string[string_length-i-1]
        j               += 1
        # One letter has been read, so one down with the counter. 
        # Max is 5! 
        counter_letters -= 1
      
    # Return the list of atoms   
    return atoms






























########################################################
#
#
#
#
#
#          The main routine
#
#
#
#
#
########################################################



def Draw_scene(FLAG_group_atoms,group_atoms_dn,mesh_yn,Ball_azimuth,Ball_zenith,Ball_radius_factor,Ball_distance_factor,offset_x,offset_y,offset_z,Stick_yn,Stick_sectors,Stick_diameter, put_to_center, camera_yn, lamp_yn, Pdb_file, Data_file):

    # This is in order to solve this strange 'relative path' thing.
    Pdb_file = bpy.path.abspath(Pdb_file)
    Data_file = bpy.path.abspath(Data_file)
   
   
    # Lists for all atoms in the data file
    Data_Number        = []
    Data_Atomname      = []
    Data_Shortname     = []
    Data_Color         = []
    Data_Radius        = []

    # Lists for atoms in the PDB file
    atom_object    = []
    atom_element   = []
    atom_name      = []
    atom_charge    = []
    atom_color     = []
    atom_material  = []   
    atom_x         = []
    atom_y         = []
    atom_z         = []
    atom_R         = []
    bar_atom1      = []
    bar_atom2      = []
   
    # Materials
    atom_material_list = []
   

    #
    #
    #
    #
    #          READING DATA OF ALL POSSIBLE ATOMS FROM THE DATA FILE
    #         
    #
    #
    #


    # Read the data file, which contains all data (atom name, radii, colors, etc.)
    Data_file_p = io.open(Data_file, "r")

    i = 0
    for line in Data_file_p:

      if "Atom" in line:

          line              = str(Data_file_p.readline())
 
          line              = str(Data_file_p.readline())
          pos               = str.find(line, ":")
          Data_Number.append(line[pos+2:-1])

          line              = str(Data_file_p.readline())
          pos               = str.find(line, ":")
          Data_Atomname.append(line[pos+2:-1])

          line              = str(Data_file_p.readline())
          pos               = str.find(line, ":")
          Data_Shortname.append(line[pos+2:-1])

          line              = str(Data_file_p.readline())
          pos               = str.find(line, ":")
          color_value       = line[pos+2:-1].split(',')
          Data_Color.append([float(color_value[0]),float(color_value[1]),float(color_value[2])]) 

          line              = str(Data_file_p.readline())
          pos               = str.find(line, ":")
          Data_Radius.append(line[pos+2:-1])

          i += 1

    Data_file_p.close()
    
    all_existing_atoms = i


    #
    #
    #
    #
    #          READING DATA OF ATOMS
    #
    #
    #


    # Open the file ...
    Pdb_file_p = io.open(Pdb_file, "r")

    #Go to the line, in which "ATOM" or "HETATM" appears.
    for line in Pdb_file_p:
        split_list = line.split(' ')
        if "ATOM" in split_list[0]:
            break
        if "HETATM" in split_list[0]:
            break
 
    # This is the list, which contains the names of all type of atoms.
    atom_all_types_list = []

    j = 0
    # This is in fact an endless 'while loop', ...
    while j > -1:

        # ... the loop is broken here (EOF) ...
        if line == "":
            break  

        # If 'ATOM4 or 'HETATM' appears in the line then do ...
        if "ATOM" in line or "HETATM" in line:
        
            # Split the line into its parts (devided by a ' ') and analyse it. The first line is read.
            split_list = line.rsplit()
         
            for i in list(range(all_existing_atoms)):
                if str.upper(split_list[-1]) == str.upper(Data_Shortname[i]):
                    # Give the atom its proper name and radius:
                    atom_element.append(str.upper(Data_Shortname[i]))
                    atom_name.append(Data_Atomname[i])
                    atom_R.append(float(Data_Radius[i]))
                    atom_color.append(Data_Color[i])
                    break

            # 1. case: These are 'unknown' atoms. In some cases, atoms are named with an additional label like H1 (hydrogen1)
            # 2. case: The last column 'split_list[-1]' does not exist, we take then column 3 in the PDB file.
            if i == all_existing_atoms-1:

                # Give this atom also a name. If it is an 'X' then it is a vacancy. Otherwise ...
                if "X" in str.upper(split_list[2]):
                    atom_element.append("VAC")
                    atom_name.append("Vacancy")
                # ... take what is written in the PDB file.
                else:
                    atom_element.append(str.upper(split_list[2]))
                    atom_name.append(str.upper(split_list[2]))

                # Default values for the atom.
                atom_R.append(float(Data_Radius[all_existing_atoms-2]))
                atom_color.append(Data_Color[all_existing_atoms-2])
         
                 
         
            # The list that contains all types of atoms is created here.
            # If the name of the atom is already in the list, FLAG on 'found'. 
            FLAG_FOUND = False
            for atom_type in atom_all_types_list:
                if atom_type[0] == atom_name[-1]:
                    FLAG_FOUND = True
                    break
            # No name in the current list has been found? => New entry.
            if FLAG_FOUND == False:
                atom_all_types_list.append([atom_name[-1],atom_element[-1],atom_color[-1]])


                 
            # 'coor' increases by 1 if 'x, y, z' are found
            coor   = 1
            number = 0
         
            for each_element in split_list:
    
                # If there is a dot, it is an coordinate.
                if "." in each_element:
                    if coor == 1:
                        atom_x.append(float(each_element))
                        coor     += 1
                    elif coor == 2:
                        atom_y.append(float(each_element))
                        coor     += 1
                    elif coor == 3:
                        atom_z.append(float(each_element))
                        coor     += 1        
      
            j += 1
           
               
        line = Pdb_file_p.readline()
        line = line[:-1]

    Pdb_file_p.close()
    Number_of_total_atoms = j


    #
    #
    #
    #
    #          MATERIAL PROPERTIES FOR ATOMS
    #
    #
    #



    # Here, the atoms get already their material properties. Why already here? Because,
    # then it is done and the atoms can be drawn in a fast way (see drawing part at the end 
    # of this script below). 
   
    # Create first a new list of materials for each type of atom (e.g. hydrogen)
    for atom_type in atom_all_types_list:
   
        bpy.ops.object.material_slot_add()
        material               = bpy.data.materials.new(atom_type[1])
        material.name          = atom_type[0]
        material.diffuse_color = atom_type[2]
        atom_material_list.append(material)
   
    # Now, we go through all atoms and give them a material. For all atoms ...   
    for i in range(0, Number_of_total_atoms):
        # ... and all materials ...
        for material in atom_material_list:
            # ... select the correct material for the current atom via name-comparison ...
            if atom_name[i] in material.name:
                # ... and give the atom its material properties. Before we check, if it is a
                # vacancy, because then it gets some additional preparation. The vacancy is represented by
                # a transparent cube.
                if atom_name[i] == "Vacancy":
                    material.transparency_method                  = 'Z_TRANSPARENCY'
                    material.alpha                                = 1.3
                    material.raytrace_transparency.fresnel        = 1.6
                    material.raytrace_transparency.fresnel_factor = 1.6                   
                    material.use_transparency                     = True      
                # The atom gets its properties.
                atom_material.append(material)   


    #
    #
    #
    #
    #          READING DATA OF STICKS
    #
    #
    #


    # Open the PDB file again such that the file pointer
    # is in the first line ...
    Pdb_file_p = io.open(Pdb_file, "r")

    split_list = line.split(' ')

    # Go to the first entry
    if "CONECT" not in split_list[0]:
        for line in Pdb_file_p:
            split_list = line.split(' ')
            if "CONECT" in split_list[0]:
                break

  
    Number_of_sticks = 0
    doppelte_bars  = 0
    j              = 0
    # This is in fact an endless while loop, ...
    while j > -1:
 

        # ... which is broken here (EOF) ...
        if line == "":
            break  
        # ... or here, when no 'CONNECT' appears anymore.
        if "CONECT" not in line:
            break
         
        if line[-1] == '\n':
            line = line[:-1]

        atoms_list        = Read_atom_for_stick(line)
        atoms_list_length = len(atoms_list)

        q = 0
        for each_element in atoms_list:
      
            if q == atoms_list_length - 1:
                break
      
            atom1 = atoms_list[-1]
            atom2 = each_element

            FLAG_BAR = "all is okay"

            for k in list(range(j)):
                if (bar_atom1[k] == atom1 and bar_atom2[k] == atom2) or (bar_atom1[k] == atom2 and bar_atom2[k] == atom1):
                    doppelte_bars += 1
                    FLAG_BAR       = "double!"
                    break

            if FLAG_BAR == "all is okay":
                bar_atom1.append(atom1)
                bar_atom2.append(atom2)      
                Number_of_sticks += 1   
                j += 1

            
            q += 1

        line = Pdb_file_p.readline()
        line = line[:-1]

    Pdb_file_p.close()
    # So far, all atoms and sticks have been registered.



    #
    #
    #
    #
    #          TRANSLATION OF THE OBJECT TO THE ORIGIN
    #
    #
    #



    # If chosen, the objects are first put into the center of the scene.
    if put_to_center == True:

        sum_x = 0
        sum_y = 0
        sum_z = 0

        # Sum of all atom coordinates
        for i in list(range(Number_of_total_atoms)):

            sum_x = sum_x + atom_x[i]
            sum_y = sum_y + atom_y[i]
            sum_z = sum_z + atom_z[i]

        # Then the average is taken
        sum_x = sum_x / Number_of_total_atoms
        sum_y = sum_y / Number_of_total_atoms
        sum_z = sum_z / Number_of_total_atoms

        # After, for each atom the center of gravity is substracted
        for i in list(range(Number_of_total_atoms)):

            atom_x[i] = atom_x[i] - sum_x
            atom_y[i] = atom_y[i] - sum_y
            atom_z[i] = atom_z[i] - sum_z



    #
    #
    #
    #
    #          SCALING GEOMETRIC PROPERTIES
    #
    #
    #


    # Take all atoms and ...
    # - adjust their radii,
    # - scale the distances,
    # - and move the center of the whole ('+= offset_x', in Angstroem)
    for i in list(range(Number_of_total_atoms)):

        atom_charge.append(1.0)  
        atom_x[i] += offset_x
        atom_y[i] += offset_y
        atom_z[i] += offset_z
        atom_x[i] *= Ball_distance_factor
        atom_y[i] *= Ball_distance_factor
        atom_z[i] *= Ball_distance_factor



    #
    #
    #
    #
    #          DETERMINATION OF SOME GEOMETRIC PROPERTIES
    #
    #
    #


    # In the following, some geometric properties of the whole object are 
    # determined: center, size, etc. 
    sum_x = 0
    sum_y = 0
    sum_z = 0

    # First the center is determined. All coordinates are summed up ...
    for i in list(range(Number_of_total_atoms)):
        sum_x = sum_x + atom_x[i]
        sum_y = sum_y + atom_y[i]
        sum_z = sum_z + atom_z[i]
    # ... and the average is taken. This gives the center of the object.
    object_center = [sum_x / Number_of_total_atoms, sum_y / Number_of_total_atoms, sum_z / Number_of_total_atoms]

    # Now, we determine the size. All coordinates are analyzed ...
    object_size = 0.0
    for i in list(range(Number_of_total_atoms)):

        diff_x = atom_x[i] - object_center[0]
        diff_y = atom_y[i] - object_center[1]
        diff_z = atom_z[i] - object_center[2]

        # This is needed in order to estimate the size of the object.
        # The farest atom from the object center is taken as a measure.
        distance_to_object_center = math.sqrt(diff_x*diff_x + diff_y*diff_y + diff_z*diff_z)
        if distance_to_object_center > object_size:
            object_size = distance_to_object_center


    #
    #
    #
    #
    #          CAMERA AND LAMP
    #
    #
    #

    dist   = object_size / math.sqrt(object_size)
   
   
    # Here a camera is put into the scene, if chosen.
    if camera_yn == True:

        camera_factor = 10.0
        camera_x = object_center[0]+dist*camera_factor
        camera_y = object_center[1]
        camera_z = object_center[2]+dist*camera_factor
        camera_pos    = [camera_x,camera_y,camera_z]
        bpy.ops.object.camera_add(view_align=False, enter_editmode=False, location=camera_pos, rotation=(0.0, 0.0, 0.0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
        # Some properties of the camera are changed.
        camera          = bpy.data.objects['Camera'].data
        bpy.data.objects['Camera'].name = "A_camera"
        camera.name     = "A_camera"
        camera.lens     = 45
        camera.clip_end = 500.0

        # Turning the camera

        # The vector between camera and origin of the object
        vec_cam_obj            = (mathutils.Vector(camera_pos) - mathutils.Vector(object_center))
        # A [0.0, 0.0, 1.0] vector along the z axis
        vec_up_axis            = mathutils.Vector([0.0, 0.0, 1.0])
        # The angle between the last two vectors
        angle                  = vec_cam_obj.angle(vec_up_axis, 0)
        # The cross-product of the [0.0, 0.0, 1.0] vector and vec_cam_obj
        axis                   = vec_up_axis.cross(vec_cam_obj)
        euler                  = mathutils.Matrix.Rotation(angle, 4, axis).to_euler()
        object                 = bpy.data.objects['A_camera']
        object.rotation_euler  = euler



    # Here a lamp is put into the scene, if chosen.
    if lamp_yn == True:

        lamp_factor                    = 0.7
        lamp_x                         = camera_x * lamp_factor  
        lamp_y                         = camera_y * lamp_factor + dist * camera_factor * lamp_factor * 0.2
        lamp_z                         = camera_z * lamp_factor 
        lamp_pos                       = [lamp_x, lamp_y, lamp_z]
        bpy.ops.object.lamp_add  (type = 'POINT', view_align=False,         location=lamp_pos,   rotation=(0.0, 0.0, 0.0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
        # Some properties of the lamp are changed.
        lamp                           = bpy.data.objects['Point'].data
        bpy.data.objects['Point'].name = "A_lamp"
        lamp.name                      = "A_lamp"
        lamp.distance                  = 500.0 
        lamp.energy                    = 2.0 
        lamp.shadow_method             = 'RAY_SHADOW'





    #
    #
    #
    #
    #          SOME OUTPUT ON THE CONSOLE
    #
    #
    #

   
    # The following two loops give a huge printout in the terminal. If needed one can uncomment these lines
   
    # Atoms
    # print("\nCoordinates of the atoms:")
    # for i in list(range(Number_of_total_atoms)):
    #   print(str(i+1) + "	" + str(atom_x[i]) + "	" + str(atom_y[i]) + "	" + str(atom_z[i]) + "	" + str(atom_R[i]) + "	" + atom_element[i])

    # Sticks
    # print("\nSticks, which connect two atoms with indices:")
    # for i in list(range(Number_of_sticks)):
    #    print(str(bar_atom1[i]) + "   " + str(bar_atom2[i]))
   
    print()
    print()
    print()
    print(Atomic_Blender_string)
    print()
    print()
    print()
    print("Total number of atoms   : " + str(Number_of_total_atoms))
    print("Total number of sticks  : " + str(Number_of_sticks))
    print("Center of object        : ", object_center)
    print("Size of object          : ", object_size)
    print()














    #
    #
    #
    #
    #          DRAWING OF ATOMS
    #
    #
    #

    # This part was the main issue in earlier versions: the loading of atoms has taken too much time!
    # Example: a surface can be easily composed of 5000 atoms => Loading 5000 NURBS needs quite a long time. 
    # There are two things I have done: 
    #                                      1. Remove any 'if's in the drawing loop
    #                                      2. Group atoms of one type

    # Lists of atoms of one type are first created. If it is atoms, all theses lists are put into
    # 'draw_atom_type_list'. The vacancies have their extra list 'draw_atom_type_list_vacancy' 
   
    draw_atom_type_list           = []
    draw_atom_type_list_vacancy   = []
    for atom_type in atom_all_types_list:
   
        # This is the draw list ...
        draw_atom_list = []  
      
        for i in range(0, Number_of_total_atoms):
            # ... select all atoms of one type ...
            if atom_type[0] == atom_name[i]:
                # ...           
                draw_atom_list.append([atom_name[i], atom_material[i], [atom_x[i], atom_y[i], atom_z[i]], atom_R[i]])
      
        if atom_type[0] == "Vacancy":
            draw_atom_type_list_vacancy.append(draw_atom_list)
        else:
            draw_atom_type_list.append(draw_atom_list)
   

    #
    # DRAW ATOMS
    #

   
    i = 0 
    bpy.ops.object.select_all(action='DESELECT')    
    # Draw NURBS or ...
    if mesh_yn == False:
        for atom_list in draw_atom_type_list:
            group_counter = 0
            groups        = []
            for atom in atom_list:
                sys.stdout.write("Atom No. %d has been built\r" % (i+1) )
                sys.stdout.flush()

                bpy.ops.surface.primitive_nurbs_surface_sphere_add(view_align=False, enter_editmode=False, location=atom[2], rotation=(0.0, 0.0, 0.0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
                aobject                 = bpy.context.scene.objects[0]
                aobject.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
                aobject.name            = atom[0]
                aobject.active_material = atom[1]
                atom_object.append(aobject)
            
                i += 1         
                group_counter += 1 
                if FLAG_group_atoms == True:
                    if group_counter == group_atoms_dn:
                        for z in range(i-group_counter,i):
                            bpy.ops.object.select_name(name = atom_object[z].name, extend=True)
                        bpy.ops.object.join()
                        groups.append(bpy.context.scene.objects[0])
                        bpy.ops.object.select_all(action='DESELECT')
                        group_counter = 0
 
            if FLAG_group_atoms == True:
                for z in range(i-group_counter,i):
                    bpy.ops.object.select_name(name = atom_object[z].name, extend=True)
                bpy.ops.object.join()
                groups.append(bpy.context.scene.objects[0])
                bpy.ops.object.select_all(action='DESELECT')
         
            for group in groups:
                bpy.ops.object.select_name(name = group.name, extend=True)
            bpy.ops.object.join()   
            
    # ... draw Mesh balls  
    else: 
        for atom_list in draw_atom_type_list:
            group_counter = 0
            groups        = []
            for atom in atom_list:
                sys.stdout.write("Atom No. %d has been built\r" % (i+1) )
                sys.stdout.flush()

                bpy.ops.mesh.primitive_uv_sphere_add(segments=Ball_azimuth, ring_count=Ball_zenith, size=1, view_align=False, enter_editmode=False, location=atom[2], rotation=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
                aobject                 = bpy.context.scene.objects[0]
                aobject.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
                aobject.name            = atom[0]
                aobject.active_material = atom[1]
                atom_object.append(aobject)

                i += 1         
                group_counter += 1 
                if FLAG_group_atoms == True:
                    if group_counter == group_atoms_dn:
                        for z in range(i-group_counter,i):
                            bpy.ops.object.select_name(name = atom_object[z].name, extend=True)
                        bpy.ops.object.join()
                        groups.append(bpy.context.scene.objects[0])
                        bpy.ops.object.select_all(action='DESELECT')
                        group_counter = 0
         
            if FLAG_group_atoms == True:
                for z in range(i-group_counter,i):
                    bpy.ops.object.select_name(name = atom_object[z].name, extend=True)
                bpy.ops.object.join()
                groups.append(bpy.context.scene.objects[0])
                bpy.ops.object.select_all(action='DESELECT')  

            for group in groups:
                bpy.ops.object.select_name(name = group.name, extend=True)
            bpy.ops.object.join()  

    #
    # DRAW VACANCIES
    #


    bpy.ops.object.select_all(action='DESELECT') 
    for atom_list in draw_atom_type_list_vacancy:
        group_counter = 0
        groups        = []
        for atom in atom_list:
            sys.stdout.write("Atom No. %d has been built\r" % (i+1) )
            sys.stdout.flush()
            bpy.ops.mesh.primitive_cube_add(view_align=False, enter_editmode=False, location=atom[2], rotation=(0.0, 0.0, 0.0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
            aobject                 = bpy.context.scene.objects[0]
            aobject.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
            aobject.name            = atom[0]
            aobject.active_material = atom[1]
            atom_object.append(aobject)
         
            i += 1         
            group_counter += 1 
            if FLAG_group_atoms == True:
                if group_counter == group_atoms_dn:
                    for z in range(i-group_counter,i):
                        bpy.ops.object.select_name(name = atom_object[z].name, extend=True)
                    bpy.ops.object.join()
                    groups.append(bpy.context.scene.objects[0])
                    bpy.ops.object.select_all(action='DESELECT')
                    group_counter = 0
        if FLAG_group_atoms == True:
            for z in range(i-group_counter,i):
                bpy.ops.object.select_name(name = atom_object[z].name, extend=True)
            bpy.ops.object.join()
            groups.append(bpy.context.scene.objects[0])
            bpy.ops.object.select_all(action='DESELECT')  
         
        for group in groups:
            bpy.ops.object.select_name(name = group.name, extend=True)
        bpy.ops.object.join()  
      
    print()    
      
      
      
      
      
      
      
      
    #
    #
    #
    #
    #          DRAWING OF STICKS
    #
    #
    #



    if Stick_yn == True:
 
        # Check first if the material already exists.
        FLAG_FOUND = False
        for material in bpy.data.materials:
      
            # If the material with its color already exists in the material list, then
            # take of course this material. Put the FLAG onto 'found!".
            if material.name == "Stick":
                stick_material = material
                FLAG_FOUND = True
                break

        # If the FLAG is still 'False', a material with the color could not
        # be found. Create a new material with the corresponding color. The
        # color is taken from the all_atom list.
        if FLAG_FOUND == False:

            bpy.ops.object.material_slot_add()
            stick_material               = bpy.data.materials.new(Data_Shortname[all_existing_atoms-1])
            stick_material.name          = Data_Atomname[all_existing_atoms-1]
            stick_material.diffuse_color = Data_Color [all_existing_atoms-1]
 
 
        up_axis = mathutils.Vector([0.0, 0.0, 1.0])
 
        for i in range(0,Number_of_sticks):
            sys.stdout.write("Stick No. %d has been built\r" % (i+1) )
            sys.stdout.flush()
            k1 = mathutils.Vector([atom_x[bar_atom1[i]-1],atom_y[bar_atom1[i]-1],atom_z[bar_atom1[i]-1]])
            k2 = mathutils.Vector([atom_x[bar_atom2[i]-1],atom_y[bar_atom2[i]-1],atom_z[bar_atom2[i]-1]])
            v = (k2-k1)
            angle   = v.angle(up_axis, 0)
            axis    = up_axis.cross(v)
            euler   = mathutils.Matrix.Rotation(angle, 4, axis).to_euler()
            bpy.ops.mesh.primitive_cylinder_add(vertices=Stick_sectors, radius=Stick_diameter, depth= v.length, cap_ends=True, view_align=False, enter_editmode=False, location= ((k1+k2)*0.5), rotation=(0,0,0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
            stick                 = bpy.context.scene.objects[0]
            stick.rotation_euler  = euler
            stick.active_material = stick_material
            stick.name            = Data_Atomname[all_existing_atoms-1]

    print()
    print()
    print("All atoms and sticks have been drawn - finished.")
    print()
    print()


    return str(Number_of_total_atoms)
            
            
