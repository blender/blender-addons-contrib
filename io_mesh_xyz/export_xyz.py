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

import bpy
import io
import math
import os
import copy
from math import pi, cos, sin
from mathutils import Vector, Matrix
from copy import copy

from . import import_xyz

ATOM_XYZ_FILEPATH = ""
ATOM_XYZ_XYZTEXT  = (  "This XYZ file has been created with Blender "
                     + "and the addon Atomic Blender - XYZ. "
                     + "For more details see: wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/XYZ\n")


class CLASS_atom_xyz_atoms_export(object):  
    __slots__ = ('element', 'location')
    def __init__(self, element, location):
        self.element  = element
        self.location = location


def DEF_atom_xyz_export(obj_type):

    list_atoms = []
    counter = 0
    for obj in bpy.context.selected_objects:
    
        if "Stick" in obj.name:
            continue
            
        if obj.type != "SURFACE" and obj.type != "MESH":
            continue 
       
        name = ""
        for element in import_xyz.ATOM_XYZ_ELEMENTS_DEFAULT:
            if element[1] in obj.name:
                if element[2] == "Vac":
                    name = "X"
                else:
                    name = element[2]
            elif element[1][:3] in obj.name:
                if element[2] == "Vac":
                    name = "X"
                else:
                    name = element[2]
        
        if name == "":
            if obj_type == "0":
                name = "?"
            else:
                continue

        if len(obj.children) != 0:
            for vertex in obj.data.vertices:
                location = obj.matrix_world*vertex.co
                list_atoms.append(CLASS_atom_xyz_atoms_export(
                                                       name,
                                                       location))
                counter += 1                                       
        else:
            if not obj.parent:
                location = obj.location
                list_atoms.append(CLASS_atom_xyz_atoms_export(
                                                       name,
                                                       location))                                   
                counter += 1                                               

    xyz_file_p = open(ATOM_XYZ_FILEPATH, "w")
    xyz_file_p.write(str(counter)+"\n")
    xyz_file_p.write(ATOM_XYZ_XYZTEXT)

    for i, atom in enumerate(list_atoms):
        string = "%3s%15.5f%15.5f%15.5f\n" % (
                                      atom.element,
                                      atom.location[0],
                                      atom.location[1],
                                      atom.location[2])
        xyz_file_p.write(string)

    xyz_file_p.close()

    return True

