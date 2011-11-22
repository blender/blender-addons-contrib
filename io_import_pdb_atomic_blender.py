# 
#
#  Authors           : Clemens Barth (Blendphys@root-1.de), ...
#
#  Homepage(Wiki)    : http://development.root-1.de/Atomic_Blender.php
#  Tracker           : http://projects.blender.org/tracker/index.php?func=detail&aid=29226&group_id=153&atid=467
#
#  Start of project              : 2011-08-31 by Clemens Barth
#  First publication in Blender  : 2011-11-11
#  Last modified                 : 2011-11-21
#
#
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
#
#
#
#

bl_info = {
  "name": "PDB Atomic Blender",
  "description": "Loading and manipulating atoms from PDB files",
  "author": "Dr. Clemens Barth",
  "version": (2,0),
  "blender": (2,6),
  "api": 31236,
  "location": "File -> Import -> PDB (.pdb)",
  "warning": "",
  "wiki_url": "http://development.root-1.de/Atomic_Blender.php",
  "tracker_url": "http://projects.blender.org/tracker/?func=detail&atid=467&aid=29226&group_id=153",
  "category": "Import-Export"
}

import bpy
import io
import sys
import math
import os
from mathutils import Vector, Matrix
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty


# These are variables, which contain the name of the PDB file and
# the path of the PDB file.
# They are used almost everywhere, which is the reason why they 
# should stay global. First, they are empty and get 'filled' directly
# after having chosen the PDB file (see 'class LoadPDB' further below).

PDBFILEPATH       = ""
PDBFILENAME       = ""

# Some string stuff for the console.
Atomic_Blender_string     = "Atomic Blender 2.0\n==================="
Atomic_Blender_panel_name = "PDB - Atomic Blender"

# This is a list that contains some data of all possible atoms. The structure is as follows:
#
# 1, "Hydrogen", "H", [0.0,0.0,1.0], 0.32, 0.32, 0.32 , -1 , 1.54   means
#
# Number, name of atom, short name, color, radius (used for Blender), radius (covalent), radius (atomic), ... 
#
# ... then the charge state: charge state, radius (ionic), charge state, radius (ionic), ... all charge states 
# for any atom are listed, if existing.

Data_all_atoms = (
( 1,      "Hydrogen",        "H", (  0.0,   0.0,   1.0), 0.32, 0.32, 0.32 , -1 , 1.54 ),
( 2,        "Helium",       "He", ( 0.20,  0.56,  0.20), 0.93, 0.93, 0.93 ,  1 , 0.68 ),
( 3,     "Beryllium",       "Be", ( 0.44,  0.72,  0.30), 0.90, 0.90, 0.90 ,  1 , 0.44 ,  2 , 0.35 ),
( 4,         "Boron",        "B", (  1.0,   1.0,   1.0), 0.82, 0.82, 0.82 ,  1 , 0.35 ,  3 , 0.23 ),
( 5,        "Carbon",        "C", (  0.0,   0.0,   0.0), 0.77, 0.77, 0.77 , -4 , 2.60 ,  4 , 0.16 ),
( 6,      "Nitrogen",        "N", (  0.0,   0.0,   1.0), 0.75, 0.75, 0.75 , -3 , 1.71 ,  1 , 0.25 ,  3 , 0.16 ,  5 , 0.13 ),
( 7,        "Oxygen",        "O", (  1.0,   0.0,   0.0), 0.73, 0.73, 0.73 , -2 , 1.32 , -1 , 1.76 ,  1 , 0.22 ,  6 , 0.09 ),
( 8,      "Fluorine",        "F", (  0.0,   1.0,   0.0), 0.72, 0.72, 0.72 , -1 , 1.33 ,  7 , 0.08 ),
( 9,          "Neon",       "Ne", ( 0.53,  0.60,  0.52), 0.71, 0.71, 0.71 ,  1 , 1.12 ),
(10,        "Sodium",       "Na", (  0.0,   0.0,   1.0), 1.54, 1.54, 1.54 ,  1 , 0.97 ),
(11,     "Magnesium",       "Mg", (  1.0,   1.0,   1.0), 1.36, 1.36, 1.36 ,  1 , 0.82 ,  2 , 0.66 ),
(12,     "Aluminium",       "Al", ( 0.70,   0.2,  0.62), 1.18, 1.18, 1.18 ,  3 , 0.51 ),
(13,       "Silicon",       "Si", ( 0.65,  0.64,  0.27), 1.11, 1.11, 1.11 , -4 , 2.71 , -1 , 3.84 ,  1 , 0.65 ,  4 , 0.42 ),
(14,    "Phosphorus",        "P", (  1.0,   1.0,   0.0), 1.06, 1.06, 1.06 , -3 , 2.12 ,  3 , 0.44 ,  5 , 0.35 ),
(15,        "Sulfur",        "S", (  1.0,   1.0,  0.50), 1.02, 1.02, 1.02 , -2 , 1.84 ,  2 , 2.19 ,  4 , 0.37 ,  6 , 0.30 ),
(16,      "Chlorine",       "Cl", (  0.0,   1.0,   0.0), 0.99, 0.99, 0.99 , -1 , 1.81 ,  5 , 0.34 ,  7 , 0.27 ),
(17,         "Argon",       "Ar", ( 0.31,  0.32,  0.74), 0.98, 0.98, 0.98 ,  1 , 1.54 ),
(18,     "Potassium",        "K", ( 0.81,  0.23,  0.42), 2.03, 2.03, 2.03 ,  1 , 0.81 ),
(19,       "Calcium",       "Ca", (  1.0,   1.0,   1.0), 1.74, 1.74, 1.74 ,  1 , 1.18 ,  2 , 0.99 ),
(20,      "Scandium",       "Sc", ( 0.66,  0.44,  0.31), 1.44, 1.44, 1.44 ,  3 , 0.73 ),
(21,      "Titanium",       "Ti", ( 0.27,  0.53,  0.68), 1.32, 1.32, 1.32 ,  1 , 0.96 ,  2 , 0.94 ,  3 , 0.76 ,  4 , 0.68 ),
(22,      "Vanadium",        "V", ( 0.27,  0.24,  0.63), 1.22, 1.22, 1.22 ,  2 , 0.88 ,  3 , 0.74 ,  4 , 0.63 ,  5 , 0.59 ),
(23,      "Chromium",       "Cr", ( 0.80,  0.28,  0.81), 1.18, 1.18, 1.18 ,  1 , 0.81 ,  2 , 0.89 ,  3 , 0.63 ,  6 , 0.52 ),
(24,     "Manganese",       "Mn", ( 0.75,  0.35,  0.55), 1.17, 1.17, 1.17 ,  2 , 0.80 ,  3 , 0.66 ,  4 , 0.60 ,  7 , 0.46 ),
(25,          "Iron",       "Fe", (  1.0,   0.0,   0.0), 1.17, 1.17, 1.17 ,  2 , 0.74 ,  3 , 0.64 ),
(26,        "Cobalt",       "Co", ( 0.27,  0.21,  0.75), 1.16, 1.16, 1.16 ,  2 , 0.72 ,  3 , 0.63 ),
(27,        "Nickel",       "Ni", ( 0.43,  0.36,  0.86), 1.15, 1.15, 1.15 ,  2 , 0.69 ),
(28,        "Copper",       "Cu", ( 0.60,   0.0,   0.0), 1.17, 1.17, 1.17 ,  1 , 0.96 ,  2 , 0.72 ),
(29,          "Zinc",       "Zn", ( 0.42,  0.36,  0.45), 1.25, 1.25, 1.25 ,  1 , 0.88 ,  2 , 0.74 ),
(30,       "Gallium",       "Ga", ( 0.63,  0.72,  0.33), 1.26, 1.26, 1.26 ,  1 , 0.81 ,  3 , 0.62 ),
(31,     "Germanium",       "Ge", ( 0.42,  0.75,  0.30), 1.22, 1.22, 1.22 , -4 , 2.72 ,  2 , 0.73 ,  4 , 0.53 ),
(32,       "Arsenic",       "As", ( 0.39,  0.77,  0.25), 1.20, 1.20, 1.20 , -3 , 2.22 ,  3 , 0.58 ,  5 , 0.46 ),
(33,      "Selenium",       "Se", ( 0.95,  0.27,  0.90), 1.16, 1.16, 1.16 , -2 , 1.91 , -1 , 2.32 ,  1 , 0.66 ,  4 , 0.50 ,  6 , 0.42 ),
(34,       "Bromine",       "Br", (  0.0,  0.49,   0.0), 1.14, 1.14, 1.14 , -1 , 1.96 ,  5 , 0.47 ,  7 , 0.39 ),
(35,       "Krypton",       "Kr", ( 0.22,  0.43,  0.19), 1.31, 1.31, 1.31 ,  1 , 1.47 ),
(36,     "Strontium",       "Sr", (  1.0,   1.0,   1.0), 1.91, 1.91, 1.91 ,  2 , 1.12 ),
(37,       "Yttrium",        "Y", (  1.0,   1.0,   1.0), 1.62, 1.62, 1.62 ,  3 , 0.89 ),
(38,     "Zirconium",       "Zr", (  1.0,   1.0,   1.0), 1.45, 1.45, 1.45 ,  1 , 1.09 ,  4 , 0.79 ),
(39,       "Niobium",       "Nb", (  1.0,   1.0,   1.0), 1.34, 1.34, 1.34 ,  1 , 1.00 ,  4 , 0.74 ,  5 , 0.69 ),
(40,    "Molybdenum",       "Mo", (  1.0,   1.0,   1.0), 1.30, 1.30, 1.30 ,  1 , 0.93 ,  4 , 0.70 ,  6 , 0.62 ),
(41,    "Technetium",       "Tc", (  1.0,   1.0,   1.0), 1.27, 1.27, 1.27 ,  7 , 0.97 ),
(42,     "Ruthenium",       "Ru", (  1.0,   1.0,   1.0), 1.25, 1.25, 1.25 ,  4 , 0.67 ),
(43,       "Rhodium",       "Rh", (  1.0,   1.0,   1.0), 1.25, 1.25, 1.25 ,  3 , 0.68 ),
(44,     "Palladium",       "Pd", (  1.0,   1.0,   1.0), 1.28, 1.28, 1.28 ,  2 , 0.80 ,  4 , 0.65 ),
(45,        "Silver",       "Ag", (  1.0,   1.0,   1.0), 1.34, 1.34, 1.34 ,  1 , 1.26 ,  2 , 0.89 ),
(46,       "Cadmium",       "Cd", (  1.0,   1.0,   1.0), 1.48, 1.48, 1.48 ,  1 , 1.14 ,  2 , 0.97 ),
(47,        "Indium",       "In", (  1.0,   1.0,   1.0), 1.44, 1.44, 1.44 ,  3 , 0.81 ),
(48,           "Tin",       "Sn", (  1.0,   1.0,   1.0), 1.41, 1.41, 1.41 , -4 , 2.94 , -1 , 3.70 ,  2 , 0.93 ,  4 , 0.71 ),
(49,      "Antimony",       "Sb", (  1.0,   1.0,   1.0), 1.40, 1.40, 1.40 , -3 , 2.45 ,  3 , 0.76 ,  5 , 0.62 ),
(50,     "Tellurium",       "Te", (  1.0,   1.0,   1.0), 1.36, 1.36, 1.36 , -2 , 2.11 , -1 , 2.50 ,  1 , 0.82 ,  4 , 0.70 ,  6 , 0.56 ),
(51,        "Iodine",        "I", (  0.0,  0.49,  0.49), 1.33, 1.33, 1.33 , -1 , 2.20 ,  5 , 0.62 ,  7 , 0.50 ),
(52,         "Xenon",       "Xe", (  1.0,   1.0,   1.0), 1.31, 1.31, 1.31 ,  1 , 1.67 ),
(53,        "Barium",       "Ba", (  1.0,   1.0,   1.0), 1.98, 1.98, 1.98 ,  1 , 1.53 ,  2 , 1.34 ),
(54,     "Lanthanum",       "La", (  1.0,   1.0,   1.0), 1.69, 1.69, 1.69 ,  1 , 1.39 ,  3 , 1.06 ),
(55,        "Cerium",       "Ce", (  1.0,   1.0,   1.0), 1.65, 1.65, 1.65 ,  1 , 1.27 ,  3 , 1.03 ,  4 , 0.92 ),
(56,  "Praseodymium",       "Pr", (  1.0,   1.0,   1.0), 1.65, 1.65, 1.65 ,  3 , 1.01 ,  4 , 0.90 ),
(57,     "Neodymium",       "Nd", (  1.0,   1.0,   1.0), 1.64, 1.64, 1.64 ,  3 , 0.99 ),
(58,    "Promethium",       "Pm", (  1.0,   1.0,   1.0), 1.63, 1.63, 1.63 ,  3 , 0.97 ),
(59,      "Samarium",       "Sm", (  1.0,   1.0,   1.0), 1.62, 1.62, 1.62 ,  3 , 0.96 ),
(60,      "Europium",       "Eu", (  1.0,   1.0,   1.0), 1.85, 1.85, 1.85 ,  2 , 1.09 ,  3 , 0.95 ),
(61,    "Gadolinium",       "Gd", (  1.0,   1.0,   1.0), 1.61, 1.61, 1.61 ,  3 , 0.93 ),
(62,       "Terbium",       "Tb", (  1.0,   1.0,   1.0), 1.59, 1.59, 1.59 ,  3 , 0.92 ,  4 , 0.84 ),
(63,    "Dysprosium",       "Dy", (  1.0,   1.0,   1.0), 1.59, 1.59, 1.59 ,  3 , 0.90 ),
(64,       "Holmium",       "Ho", (  1.0,   1.0,   1.0), 1.58, 1.58, 1.58 ,  3 , 0.89 ),
(65,        "Erbium",       "Er", ( 0.48,  0.48,  0.48), 1.57, 1.57, 1.57 ,  3 , 0.88 ),
(66,       "Thulium",       "Tm", (  1.0,   1.0,   1.0), 1.56, 1.56, 1.56 ,  3 , 0.87 ),
(67,     "Ytterbium",       "Yb", (  1.0,   1.0,   1.0), 1.74, 1.74, 1.74 ,  2 , 0.93 ,  3 , 0.85 ),
(68,      "Lutetium",       "Lu", (  1.0,   1.0,   1.0), 1.56, 1.56, 1.56 ,  3 , 0.85 ),
(69,       "Hafnium",       "Hf", (  1.0,   1.0,   1.0), 1.44, 1.44, 1.44 ,  4 , 0.78 ),
(70,      "Tantalum",       "Ta", (  1.0,   1.0,   1.0), 1.34, 1.34, 1.34 ,  5 , 0.68 ),
(71,      "Tungsten",        "W", (  1.0,   1.0,   1.0), 1.30, 1.30, 1.30 ,  4 , 0.70 ,  6 , 0.62 ),
(72,       "Rhenium",       "Re", (  1.0,   1.0,   1.0), 1.28, 1.28, 1.28 ,  4 , 0.72 ,  7 , 0.56 ),
(73,        "Osmium",       "Os", (  1.0,   1.0,   1.0), 1.26, 1.26, 1.26 ,  4 , 0.88 ,  6 , 0.69 ),
(74,       "Iridium",       "Ir", (  1.0,   1.0,   1.0), 1.27, 1.27, 1.27 ,  4 , 0.68 ),
(75,     "Platinium",       "Pt", (  1.0,   1.0,   1.0), 1.30, 1.30, 1.30 ,  2 , 0.80 ,  4 , 0.65 ),
(76,          "Gold",       "Au", (  1.0,   1.0,   1.0), 1.34, 1.34, 1.34 ,  1 , 1.37 ,  3 , 0.85 ),
(77,       "Mercury",       "Hg", (  1.0,   1.0,   1.0), 1.49, 1.49, 1.49 ,  1 , 1.27 ,  2 , 1.10 ),
(78,      "Thallium",       "Tl", (  1.0,   1.0,   1.0), 1.48, 1.48, 1.48 ,  1 , 1.47 ,  3 , 0.95 ),
(79,          "Lead",       "Pb", ( 0.49,  0.49,  0.49), 1.47, 1.47, 1.47 ,  2 , 1.20 ,  4 , 0.84 ),
(80,       "Bismuth",       "Bi", (  1.0,   1.0,   1.0), 1.46, 1.46, 1.46 ,  1 , 0.98 ,  3 , 0.96 ,  5 , 0.74 ),
(81,      "Polonium",       "Po", (  1.0,   1.0,   1.0), 1.46, 1.46, 1.46 ,  6 , 0.67 ),
(82,      "Astatine",       "At", (  1.0,   1.0,   1.0), 1.45, 1.45, 1.45 , -3 , 2.22 ,  3 , 0.85 ,  5 , 0.46 ),
(83,         "Radon",       "Rn", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ,  1 , 1.80 ),
(84,        "Radium",       "Ra", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ,  2 , 1.43 ),
(85,      "Actinium",       "Ac", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.18 ),
(86,       "Thorium",       "Th", (  1.0,   1.0,   1.0), 1.65, 1.65, 1.65 ,  4 , 1.02 ),
(87,  "Protactinium",       "Pa", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.13 ,  4 , 0.98 ,  5 , 0.89 ),
(88,       "Uranium",        "U", (  1.0,   1.0,   1.0), 1.42, 1.42, 1.42 ,  4 , 0.97 ,  6 , 0.80 ),
(89,     "Neptunium",       "Np", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.10 ,  4 , 0.95 ,  7 , 0.71 ),
(90,     "Plutonium",       "Pu", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.08 ,  4 , 0.93 ),
(91,     "Americium",       "Am", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.07 ,  4 , 0.92 ),
(92,        "Curium",       "Cm", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00 ),
(93,       "Vacancy",      "Vac", (  0.5,   0.5,   0.5), 1.00, 0.00, 0.00),
(94,       "Default",  "Default", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00),
(95,         "Stick",    "Stick", (  0.5,   0.5,   0.5), 0.00, 0.00, 0.00))

ALL_EXISTING_ATOMS = 95
    
# List of loaded structures (molecules, crystals, etc.). Each sub list contains 
# all objects of one loaded structure. These list are used to identify the 
# all structure, which are loaded during a session. 
LOADED_STRUCTURES       = []
LOADED_STRUCTURES_DUPLI = []     
    
    
    
    
    
    

# The panel, which is loaded after the file has been
# chosen via the menu 'File -> Import'
class CLASS_PDB_Panel(bpy.types.Panel):
    bl_label       = Atomic_Blender_panel_name
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "physics"
    # This could be also an option ... :
    #bl_space_type  = "VIEW_3D"
    #bl_region_type = "TOOL_PROPS"

    # This 'poll thing' has taken 3 hours of a hard search and understanding.
    # I explain it in the following from my point of view:
    #
    # Before this class is entirely treaten (here: drawing the panel) the
    # poll method is called first. Basically, some conditions are 
    # checked before other things in the class are done afterwards. If a 
    # condition is not valid, one returns 'False' such that nothing further 
    # is done. 'True' means: 'Go on'
    #
    # In the case here, it is verified if the PDBFILEPATH variable contains
    # a name. If not - and this is the case directly after having started the
    # script - the panel does not appear because 'False' is returned. However,
    # as soon as a file has been chosen, the panel appears because PDBFILEPATH
    # contains a name.
    #
    # Please, correct me if I'm wrong. 
    @classmethod
    def poll(self, context):
        if PDBFILEPATH == "":
            return False
        else:
            return True

    def draw(self, context):
        layout = self.layout
        scn    = bpy.context.scene

        row = layout.row()
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_PDB_filename") 
        col.prop(scn, "atom_pdb_PDB_file")
        row = layout.row()
        row = layout.row() 
        
        col = row.column()
        col.prop(scn, "use_atom_pdb_dupliverts")

        row = layout.row()
        col = row.column(align=True)        
        col.prop(scn, "use_atom_pdb_mesh")
        col.prop(scn, "atom_pdb_mesh_azimuth")
        col.prop(scn, "atom_pdb_mesh_zenith")        
        col = row.column(align=True)        
        col.label(text="Scaling factors")
        col.prop(scn, "atom_pdb_scale_ballradius")
        col.prop(scn, "atom_pdb_scale_distances")
        col = row.column(align=True) 
        col.prop(scn, "use_atom_pdb_sticks")
        col.prop(scn, "atom_pdb_sticks_sectors")
        col.prop(scn, "atom_pdb_sticks_radius")

        row = layout.row()        
        col = row.column(align=True)  
        col.prop(scn, "atom_pdb_offset_x")
        col.prop(scn, "atom_pdb_offset_y")
        col.prop(scn, "atom_pdb_offset_z")
        col = row.column()         
        col.prop(scn, "use_atom_pdb_center")

        layout.separator()  
        row = layout.row(align=True)        
        col = row.column()
        col.prop(scn, "use_atom_pdb_cam")
        col.prop(scn, "use_atom_pdb_lamp")        
        col = row.column() 
        col.operator( "atom_pdb.button_start" )
        row2 = col.row()
        row2.label(text="Number of atoms")
        row2.prop(scn, "atom_pdb_number_atoms")
        layout.separator()
              
        row = layout.row()             
        row.operator( "atom_pdb.button_distance")
        row.prop(scn, "atom_pdb_distance") 
        layout.separator()
            
        row = layout.row()                   
        row.label(text="Modification of the radii of one type of atom")            
            
        row = layout.row()     
        split = row.split(percentage=0.40)
        col = split.column()
        col.prop(scn, "atom_pdb_mod_atomname") 
        split = split.split(percentage=0.50)
        col = split.column()
        col.prop(scn, "atom_pdb_mod_pm_radius")
        split = split.split(percentage=1.0)
        col = split.column()
        col.operator("atom_pdb.button_modify_single")
            
        row = layout.row()     
        split = row.split(percentage=0.40)
        col = split.column()
        split = split.split(percentage=0.50)
        col = split.column()
        col.prop(scn, "atom_pdb_mod_rel_radius")
        split = split.split(percentage=1.0)
        col = split.column(align=True)
        col.operator( "atom_pdb.button_bigger_single" )            
        col.operator( "atom_pdb.button_smaller_single" ) 
                                             
        row = layout.row()            
        row.label(text="Modification of all atom radii")
        row = layout.row()
        col = row.column() 
        col.prop(scn, "atom_pdb_mod_all_radii")
        col = row.column(align=True) 
        col.operator( "atom_pdb.button_modify_all" )
        col.operator( "atom_pdb.button_invert_all" )



class CLASS_Input_Output(bpy.types.PropertyGroup):
    bpy.types.Scene.atom_pdb_PDB_filename        = bpy.props.StringProperty(name = "File name", default="", description = "PDB file name")
    bpy.types.Scene.atom_pdb_PDB_file            = bpy.props.StringProperty(name = "Path to file", default="", description = "Path of the PDB file")
    bpy.types.Scene.use_atom_pdb_dupliverts      = bpy.props.BoolProperty  (name = "Use dupliverts (Loading much faster)", default=True, description = "Use the dublication method via vertice referencing (Much faster loading!)")    
    bpy.types.Scene.use_atom_pdb_mesh            = bpy.props.BoolProperty  (name = "Mesh balls", default=False, description = "Do you want to use mesh balls instead of NURBS?")    
    bpy.types.Scene.atom_pdb_mesh_azimuth        = bpy.props.IntProperty   (name = "Azimuth", default=32, min=0, description = "Number of sectors (azimuth)")
    bpy.types.Scene.atom_pdb_mesh_zenith         = bpy.props.IntProperty   (name = "Zenith", default=32, min=0, description = "Number of sectors (zenith)")
    bpy.types.Scene.atom_pdb_scale_ballradius    = bpy.props.FloatProperty (name = "Balls", default=1.0, min=0.0, description = "Scale factor for all atom radii")
    bpy.types.Scene.atom_pdb_scale_distances     = bpy.props.FloatProperty (name = "Distances", default=1.0, min=0.0, description = "Scale factor for all distances")
    bpy.types.Scene.use_atom_pdb_center          = bpy.props.BoolProperty  (name = "Object to origin", default=True, description = "Shall the object first put into the global origin before applying the offsets on the left?")    
    bpy.types.Scene.atom_pdb_offset_x            = bpy.props.FloatProperty (name = "X", default=0.0, description = "Offset in X")
    bpy.types.Scene.atom_pdb_offset_y            = bpy.props.FloatProperty (name = "Y", default=0.0, description = "Offset in Y")
    bpy.types.Scene.atom_pdb_offset_z            = bpy.props.FloatProperty (name = "Z", default=0.0, description = "Offset in Z")
    bpy.types.Scene.use_atom_pdb_sticks          = bpy.props.BoolProperty  (name = "Use sticks", default=False, description = "Do you want to display also the sticks?")    
    bpy.types.Scene.atom_pdb_sticks_sectors      = bpy.props.IntProperty   (name = "Sector", default = 20, min=0,   description = "Number of sectors of a stick")        
    bpy.types.Scene.atom_pdb_sticks_radius       = bpy.props.FloatProperty (name = "Radius", default =  0.1, min=0.0, description = "Radius of a stick")  
    bpy.types.Scene.use_atom_pdb_cam             = bpy.props.BoolProperty  (name = "Camera", default=False, description = "Do you need a camera?")   
    bpy.types.Scene.use_atom_pdb_lamp            = bpy.props.BoolProperty  (name = "Lamp", default=False, description = "Do you need a lamp?")
    bpy.types.Scene.atom_pdb_number_atoms        = bpy.props.StringProperty(name = "", default="Number", description = "This output shows the number of atoms which have been loaded")
    bpy.types.Scene.atom_pdb_distance            = bpy.props.StringProperty(name = "", default="Distance (Angstrom)", description = "Distance of 2 objects in Angstrom")  
    bpy.types.Scene.atom_pdb_mod_atomname        = bpy.props.StringProperty(name = "", default = "Atom name", description="Put in the name of the atom (e.g. Hydrogen)")
    bpy.types.Scene.atom_pdb_mod_pm_radius       = bpy.props.FloatProperty (name = "", default = 100.0, min=0.0, description="Put in the radius of the atom (in pm)")
    bpy.types.Scene.atom_pdb_mod_rel_radius      = bpy.props.FloatProperty (name = "", default = 1.05, min=1.0, description="Put in the scale factor")
    bpy.types.Scene.atom_pdb_mod_all_radii       = bpy.props.FloatProperty (name = "Scale", default = 1.05, min=1.0, description="Put in the scale factor")


# Button for measuring the distance of the active objects
class CLASS_Distance_Button(bpy.types.Operator):
    bl_idname = "atom_pdb.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two objects"

    def execute(self, context):
        scn    = bpy.context.scene
        dist   = Measure_distance_in_scene()

        if dist != "-1.0":
           # The string length is cut, 3 digits after the first 3 digits 
           # after the '.'. Append also "Angstrom". 
           # Remember: 1 Angstrom = 10^(-10) m 
           pos    = str.find(dist, ".")
           dist   = dist[:pos+4] 
           dist   = dist + " Angstrom"

        # Put the distance into the string of the output field.
        scn.atom_pdb_distance = dist
        return {'FINISHED'}
  

# Button for changing the radii (in pm) of atoms of one type
class CLASS_Modify_Single_Button(bpy.types.Operator):
    bl_idname = "atom_pdb.button_modify_single"
    bl_label = "Modify ..."
    bl_description = "Change the radii of atoms of one type in pm"

    def execute(self, context):
        scn = bpy.context.scene
        Modify_atom_radii_type_pm(scn.atom_pdb_mod_atomname, scn.atom_pdb_mod_pm_radius)
        return {'FINISHED'}


# Button for increasing the radii of atoms of one type
class CLASS_Bigger_Single_Button(bpy.types.Operator):
    bl_idname = "atom_pdb.button_bigger_single"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of atoms of one type"

    def execute(self, context):
        scn = bpy.context.scene
        Modify_atom_radii_type_scale(scn.atom_pdb_mod_atomname, scn.atom_pdb_mod_rel_radius)
        return {'FINISHED'}


# Button for decreasing the radii of atoms of one type
class CLASS_Smaller_Single_Button(bpy.types.Operator):
    bl_idname = "atom_pdb.button_smaller_single"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of atoms of one type"

    def execute(self, context):
        scn = bpy.context.scene
        Modify_atom_radii_type_scale(scn.atom_pdb_mod_atomname, 1.0/scn.atom_pdb_mod_rel_radius)
        return {'FINISHED'}


# Button for increasing the radii of all atoms
class CLASS_Bigger_All_Button(bpy.types.Operator):
    bl_idname = "atom_pdb.button_modify_all"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of all atoms"

    def execute(self, context):
        scn     = bpy.context.scene
        Modify_all_atom_radii(scn.atom_pdb_mod_all_radii)
        return {'FINISHED'}


# Button for decreasing the radii of all atoms
class CLASS_Smaller_All_Button(bpy.types.Operator):
    bl_idname = "atom_pdb.button_invert_all"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of all atoms"

    def execute(self, context):
        scn     = bpy.context.scene
        Modify_all_atom_radii(1.0/scn.atom_pdb_mod_all_radii)
        return {'FINISHED'}


# The button for loading the atoms and creating the scene
class CLASS_Start_Button(bpy.types.Operator):
    bl_idname = "atom_pdb.button_start"
    bl_label = "DRAW THE ATOMS ..."
    bl_description = "Start to load and draw the atoms and sticks"
    
    def execute(self, context):
        scn = bpy.context.scene

        azimuth    = scn.atom_pdb_mesh_azimuth
        zenith     = scn.atom_pdb_mesh_zenith 
        bradius    = scn.atom_pdb_scale_ballradius
        bdistance  = scn.atom_pdb_scale_distances
        center     = scn.use_atom_pdb_center 
        x          = scn.atom_pdb_offset_x
        y          = scn.atom_pdb_offset_y
        z          = scn.atom_pdb_offset_z
        yn         = scn.use_atom_pdb_sticks 
        ssector    = scn.atom_pdb_sticks_sectors
        sradius    = scn.atom_pdb_sticks_radius
        cam        = scn.use_atom_pdb_cam 
        lamp       = scn.use_atom_pdb_lamp
        mesh       = scn.use_atom_pdb_mesh 
        dupliverts = scn.use_atom_pdb_dupliverts
        
        atom_number               = Draw_scene(dupliverts,mesh,azimuth,zenith,bradius,bdistance,x,y,z,yn,ssector,sradius,center,cam,lamp)
        scn.atom_pdb_number_atoms = str(atom_number)

        return {'FINISHED'}


# This is the class for the file dialog.
class CLASS_LoadPDB(bpy.types.Operator, ExportHelper):
    bl_idname = "import_pdb.pdb"
    bl_label  = "Import PDB"
    
    filename_ext = ".pdb"
    filter_glob  = StringProperty(default="*.pdb", options={'HIDDEN'},)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):   
        global PDBFILEPATH
        global PDBFILENAME
      
        # In the following the name and path of the PDB file
        # is stored into the global variables.
        scn = bpy.context.scene
        PDBFILEPATH     = self.filepath
        PDBFILENAME     = os.path.basename(PDBFILEPATH)
        scn.atom_pdb_PDB_filename = PDBFILENAME
        scn.atom_pdb_PDB_file     = PDBFILEPATH
        return {'FINISHED'}




# The entry into the menu 'file -> import'
def menu_func(self, context):
    self.layout.operator(CLASS_LoadPDB.bl_idname, text="PDB (.pdb)")


def register():
    bpy.utils.register_class(CLASS_PDB_Panel)
    bpy.utils.register_class(CLASS_Input_Output)
    bpy.utils.register_class(CLASS_Start_Button)
    bpy.utils.register_class(CLASS_Modify_Single_Button)
    bpy.utils.register_class(CLASS_Bigger_Single_Button)
    bpy.utils.register_class(CLASS_Smaller_Single_Button)
    bpy.utils.register_class(CLASS_Bigger_All_Button)
    bpy.utils.register_class(CLASS_Smaller_All_Button)
    bpy.utils.register_class(CLASS_Distance_Button)
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_class(CLASS_PDB_Panel)
    bpy.utils.unregister_class(CLASS_Input_Output)
    bpy.utils.unregister_class(CLASS_Start_Button)
    bpy.utils.unregister_class(CLASS_Modify_Single_Button)
    bpy.utils.unregister_class(CLASS_Bigger_Single_Button)
    bpy.utils.unregister_class(CLASS_Smaller_Single_Button)    
    bpy.utils.unregister_class(CLASS_Bigger_All_Button)
    bpy.utils.unregister_class(CLASS_Smaller_All_Button)
    bpy.utils.unregister_class(CLASS_Distance_Button)  
    bpy.utils.unregister_module(__name__)  
    bpy.types.INFO_MT_file_import.remove(menu_func)
        

if __name__ == "__main__":

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

    

# Routine to modify the radii of a specific type of atom
def Modify_atom_radii_type_pm(atomname, radius_pm):

    for structure in LOADED_STRUCTURES:
        for obj in structure:
            if atomname in obj.name:
                obj.scale = (radius_pm/100,radius_pm/100,radius_pm/100)
                
    for obj in LOADED_STRUCTURES_DUPLI:
        if atomname in obj.name:
            obj.scale = (radius_pm/100,radius_pm/100,radius_pm/100)

                

# Routine to modify the radii of a specific type of atom
def Modify_atom_radii_type_scale(atomname, radius_rel):

    for structure in LOADED_STRUCTURES:
        for obj in structure:
            if atomname in obj.name:
                radius = obj.scale[0]
                obj.scale = (radius_rel * obj.scale[0],radius_rel * obj.scale[0],radius_rel * obj.scale[0])
                
    for obj in LOADED_STRUCTURES_DUPLI:
        if atomname in obj.name:
            radius = obj.scale[0]
            obj.scale = (radius_rel * radius, radius_rel * radius, radius_rel * radius)


# Routine to scale the radii of all atoms
def Modify_all_atom_radii(scale):

    for structure in LOADED_STRUCTURES:
        for obj in structure:
            if "Stick" not in obj.name:
                radius = obj.scale[0]
                obj.scale = (radius * scale,radius * scale,radius * scale)
                
    for obj in LOADED_STRUCTURES_DUPLI:
        if "Stick" not in obj.name:
            radius = obj.scale[0]
            obj.scale = (radius * scale,radius * scale,radius * scale)                



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
    # An atom number can have max 5 letters! This automatically means that
    # up to 99999 atoms can be loaded max. - Well, this should be sufficient.
    counter_letters = 5 
   
    # I know that what follows is somewhat 'confusing'! However, the strings of
    # the atom numbers do have a clear position in the file (From 1 to 5, 
    # from 6 to 10 and so on.) and one needs to consider this. One could also use
    # the split function but then one gets into trouble if there are many atoms:
    # For instance, it may happen that one has
    #
    # CONECT 11111  22244444
    #
    # In Fact it means that atom No. 11111 has a stick with atom No. 222 but also
    # with atom No. 44444. The split function would give me only two numbers (11111
    # and 22244444), which is wrong. However, the following code supplies 
    # the three correct numbers: 
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



def Draw_scene(used_dupliverts,used_mesh,Ball_azimuth,Ball_zenith,Ball_radius_factor,Ball_distance_factor,offset_x,offset_y,offset_z,used_stick,Stick_sectors,Stick_diameter, put_to_center, used_camera, used_lamp):

    global PDBFILEPATH
    global PDBFILENAME

    global LOADED_STRUCTURES
    global LOADED_STRUCTURES_DUPLI  

    # This is in order to solve this strange 'relative path' thing.
    PDBFILEPATH  = bpy.path.abspath(PDBFILEPATH)
   
    # Properties for atoms
    atom_element   = []
    atom_name      = []
    atom_charge    = []
    atom_color     = []
    atom_material  = []   
    atom_x         = []
    atom_y         = []
    atom_z         = []
    atom_R         = []
    # The sticks
    stick_atom1    = []
    stick_atom2    = []
   
    # Materials
    atom_material_list = []






    #
    #
    #
    #
    #          READING DATA OF ATOMS
    #
    #
    #


    # Open the file ...
    PDBFILEPATH_p = io.open(PDBFILEPATH, "r")

    #Go to the line, in which "ATOM" or "HETATM" appears.
    for line in PDBFILEPATH_p:
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
                        
            for i in list(range(ALL_EXISTING_ATOMS)):
                if str.upper(split_list[-1]) == str.upper(Data_all_atoms[i][2]):
                    # Give the atom its proper name and radius:
                    atom_element.append(str.upper(Data_all_atoms[i][2]))
                    atom_name.append(Data_all_atoms[i][1])
                    atom_R.append(float(Data_all_atoms[i][4]))
                    atom_color.append(Data_all_atoms[i][3])
                    break

            # 1. case: These are 'unknown' atoms. In some cases, atoms are named with an additional label like H1 (hydrogen1)
            # 2. case: The last column 'split_list[-1]' does not exist, we take then column 3 in the PDB file.
            if i == ALL_EXISTING_ATOMS-1:

                # Give this atom also a name. If it is an 'X' then it is a vacancy. Otherwise ...
                if "X" in str.upper(split_list[2]):
                    atom_element.append("VAC")
                    atom_name.append("Vacancy")
                # ... take what is written in the PDB file.
                else:
                    atom_element.append(str.upper(split_list[2]))
                    atom_name.append(str.upper(split_list[2]))

                # Default values for the atom.
                atom_R.append(float(Data_all_atoms[ALL_EXISTING_ATOMS-2][4]))
                atom_color.append(Data_all_atoms[ALL_EXISTING_ATOMS-2][3])
         
                 
         
            # The list that contains info about all types of atoms is created here.
            # It is used for building the material properties for instance. 
            
            # If the name of the atom is already in the list, FLAG on 'True'. 
            FLAG_FOUND = False
            for atom_type in atom_all_types_list:
                if atom_type[0] == atom_name[-1]:
                    FLAG_FOUND = True
                    break
            # No name in the current list has been found? => New entry.
            if FLAG_FOUND == False:
                # Stored are: Atom label (e.g. 'Na'), the corresponding atom name (e.g. 'Sodium') and its color.
                atom_all_types_list.append([atom_name[-1],atom_element[-1],atom_color[-1]])


                 
            # Now the coordinates x, y and z are read.
            coor   = 1
         
            # The coordinates x, y and z are identified as such by the dot (e.g., 5.678) - a dot
            # in the line appears only in the coordinates. The coordinates are listed as follwos: 
            # x, y and z.
            # If the first coordinate (x) is read, increase coor (y).
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
           
               
        line = PDBFILEPATH_p.readline()
        line = line[:-1]

    PDBFILEPATH_p.close()
    # From above it can be clearly seen that j is now the number of all atoms.
    Number_of_total_atoms = j


    #
    #
    #
    #
    #          MATERIAL PROPERTIES FOR ATOMS
    #
    #
    #



    # Here, the atoms get already their material properties. Why already here? Because
    # then it is done and the atoms can be drawn in a fast way (see drawing part at the end 
    # of this script, further below). 
    # Note that all atoms of one type (e.g. all hydrogens) get only ONE material! This 
    # is good because then, by activating one atom in the Blender scene and changing 
    # the color of this atom, one changes the color of ALL atoms of the same type at the 
    # same time.
   
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
                # ... and give the atom its material properties. 
                # However, before we check, if it is a vacancy, because then it
                # gets some additional preparation. The vacancy is represented by
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


    # Open the PDB file again such that the file pointer is in the first line ...
    # Stupid, I know ... ;-)
    PDBFILEPATH_p = io.open(PDBFILEPATH, "r")

    split_list = line.split(' ')

    # Go to the first entry
    if "CONECT" not in split_list[0]:
        for line in PDBFILEPATH_p:
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
        # ... or here, when no 'CONECT' appears anymore.
        if "CONECT" not in line:
            break
         
        line = line.rstrip()
        
        # Read the sticks for the actual atom (sub routine). One gets a list of
        # sticks.
        atoms_list        = Read_atom_for_stick(line)
        # Determine the length of the list
        atoms_list_length = len(atoms_list)

        # For all sticks in the list do:
        q = 0
        for each_element in atoms_list:
      
            # End == break
            if q == atoms_list_length - 1:
                break
      
            # The first atom is connected with all the others in the list.
            atom1 = atoms_list[-1]
            # The second, third, ... partner atom
            atom2 = each_element

            FLAG_BAR = False
 
            # Note that in a PDB file, sticks of one atom pair can appear a couple
            # of times. (Only god knows why ...) 
            # So, does a stick between the considered atoms already exist?
            for k in list(range(j)):
                if (stick_atom1[k] == atom1 and stick_atom2[k] == atom2) or (stick_atom1[k] == atom2 and stick_atom2[k] == atom1):
                    doppelte_bars += 1
                    # If yes, then FLAG on 'True'.
                    FLAG_BAR       = True
                    break

            # If the stick is not yet registered (FLAG_BAR == False), then 
            # register it!
            if FLAG_BAR == False:
                stick_atom1.append(atom1)
                stick_atom2.append(atom2)      
                Number_of_sticks += 1   
                j += 1
 
            q += 1

        line = PDBFILEPATH_p.readline()
        line = line.rstrip()

    PDBFILEPATH_p.close()
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

    camera_factor = 15.0

    # Here a camera is put into the scene, if chosen.
    if used_camera == True:

        # Assume that the object is put into the global origin. Then, the camera
        # is moved in x and z direction, not in y. The object has its size at distance
        # math.sqrt(object_size) from the origin. So, move the camera by this distance
        # times a factor of camera_factor in x and z. Then add x, y and z of the origin of the
        # object.   
        camera_x = object_center[0] + math.sqrt(object_size) * camera_factor
        camera_y = object_center[1]
        camera_z = object_center[2] + math.sqrt(object_size) * camera_factor
        camera_pos    = [camera_x,camera_y,camera_z]
        # Create the camera
        current_layers=bpy.context.scene.layers
        bpy.ops.object.camera_add(view_align=False, enter_editmode=False, location=camera_pos, rotation=(0.0, 0.0, 0.0), layers=current_layers)
        # Some properties of the camera are changed.
        camera               = bpy.context.scene.objects.active
        camera.name          = "A_camera"
        camera.data.name     = "A_camera"
        camera.data.lens     = 45
        camera.data.clip_end = 500.0

        # Here the camera is rotated such it looks towards the center of the object.
        
        # The vector between camera and origin of the object
        vec_cam_obj            = Vector(camera_pos) - Vector(object_center)
        # The [0.0, 0.0, 1.0] vector along the z axis
        vec_up_axis            = Vector((0.0, 0.0, 1.0))
        # The angle between the last two vectors
        angle                  = vec_cam_obj.angle(vec_up_axis, 0)
        # The cross-product of the [0.0, 0.0, 1.0] vector and vec_cam_obj
        # It is the resulting vector which stands up perpendicular on vec_up_axis and vec_cam_obj
        axis                   = vec_up_axis.cross(vec_cam_obj)
        # Rotate axis 'axis' by angle 'angle' and convert this to euler parameters. 4 is the size
        # of the matrix.
        euler                  = Matrix.Rotation(angle, 4, axis).to_euler()
        camera.rotation_euler  = euler

        # Rotate the camera around its axis by 90° such that we have a nice camera position
        # and view onto the object.
        bpy.ops.transform.rotate(value=(90.0*2*math.pi/360.0,), axis=vec_cam_obj, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)


        # This does not work, I don't know why. 
        #
        #for area in bpy.context.screen.areas:
        #    if area.type == 'VIEW_3D':
        #        area.spaces[0].region_3d.view_perspective = 'CAMERA'


    # Here a lamp is put into the scene, if chosen.
    if used_lamp == True:


        # This is the distance from the object measured in terms of % of the camera 
        # distance. It is set onto 50% (1/2) distance.
        lamp_dl                        = math.sqrt(object_size) * 15 * 0.5
        # This is a factor to which extend the lamp shall go to the right (from the camera 
        # point of view).
        lamp_dy_right                  = lamp_dl * (3.0/4.0)
        
        # Create x, y and z for the lamp.
        lamp_x                         = object_center[0] + lamp_dl
        lamp_y                         = object_center[1] + lamp_dy_right
        lamp_z                         = object_center[2] + lamp_dl
        lamp_pos                       = [lamp_x, lamp_y, lamp_z]
        # Create the lamp
        current_layers=bpy.context.scene.layers
        bpy.ops.object.lamp_add  (type = 'POINT', view_align=False,         location=lamp_pos,   rotation=(0.0, 0.0, 0.0), layers=current_layers)
        # Some properties of the lamp are changed.
        lamp                           = bpy.context.scene.objects.active
        lamp.data.name                 = "A_lamp"
        lamp.name                      = "A_lamp"
        lamp.data.distance             = 500.0 
        lamp.data.energy               = 3.0 
        lamp.data.shadow_method        = 'RAY_SHADOW'

        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.world.light_settings.ao_factor = 0.2



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
    #    print(str(stick_atom1[i]) + "   " + str(stick_atom2[i]))
   
    print()
    print()
    print()
    print(Atomic_Blender_string)
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



    # Lists of atoms of one type are created. If it is atoms, all theses lists are put into one 
    # single list called 'draw_atom_type_list'. The vacancies have their extra list 
    # 'draw_atom_type_list_vacancy' 
   
    # The list containing all lists, which each contains all atoms of one type
    draw_atom_type_list           = []
    # The list which contains all vacancies
    draw_atom_type_list_vacancy   = []


    # Go through the list which contains all types of atoms. It is the list, which has been
    # created on the top during reading the PDB file. 
    # Example: atom_all_types_list = ["hydrogen", "carbon", ...]
    for atom_type in atom_all_types_list:
   
        # This is the draw list, which contains all atoms of one type (e.g. all hydrogens) ...
        draw_atom_list = []  
      
        # Go through all atoms ...
        for i in range(0, Number_of_total_atoms):
            # ... select the atoms of the considered type via comparison ...
            if atom_type[0] == atom_name[i]:

                # Vacancy
                if atom_type[0] == "Vacancy":
                    draw_atom_type_list_vacancy.append([atom_name[i], atom_material[i], [atom_x[i], atom_y[i], atom_z[i]], atom_R[i]])
                # ... and append them to the list 'draw_atom_list'.
                else:
                    draw_atom_list.append([atom_name[i], atom_material[i], [atom_x[i], atom_y[i], atom_z[i]], atom_R[i]])
    
        # Now append the atom list to the list of all types of atoms
        if atom_type[0] != "Vacancy":
            draw_atom_type_list.append(draw_atom_list)
   








    #
    # DRAW ATOMS
    #

    # The comments in the follwoing block of code (NURBS) are basically the same
    # for the code, which is used to draw meshes and the vacancies.
   
    # This is the number of all atoms which are put into the scene.
    number_loaded_atoms = 0 
    bpy.ops.object.select_all(action='DESELECT')    
    # Draw NURBS or ...
    if used_mesh == False:
        # For each list of atoms of ONE type (e.g. Hydrogen)
        for atom_list in draw_atom_type_list:

            if used_dupliverts == False:

                # For each atom in a group do ...
                structure = []
                for atom in atom_list:
                    # First print in the terminal the number of atom that will be build right now.
                    sys.stdout.write("Atom No. %d has been built\r" % (number_loaded_atoms+1) )
                    sys.stdout.flush()

                    # Build a sphere (atom)
                    current_layers=bpy.context.scene.layers
                    bpy.ops.surface.primitive_nurbs_surface_sphere_add(view_align=False, enter_editmode=False, location=atom[2], rotation=(0.0, 0.0, 0.0), layers=current_layers)
                    ball                 = bpy.context.scene.objects.active
                    ball.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
                    ball.name            = atom[0]
                    ball.active_material = atom[1]
                    structure.append(ball)
                    number_loaded_atoms += 1  
                LOADED_STRUCTURES.append(structure)


            if used_dupliverts == True:

                # Create first the vertices composed of the coordinates of all atoms of one type
                atom_vertices = []
                for atom in atom_list:
                    atom_vertices.append( (atom[2][0], atom[2][1], atom[2][2]) )

                # Build the mesh
                atom_mesh = bpy.data.meshes.new("Mesh_"+atom[0])
                atom_mesh.from_pydata(atom_vertices, [], [])
                atom_mesh.update()
                new_atom_mesh = bpy.data.objects.new(atom[0], atom_mesh)
                bpy.context.scene.objects.link(new_atom_mesh)

                # Now, build a representative sphere (atom)
                current_layers=bpy.context.scene.layers
                bpy.ops.surface.primitive_nurbs_surface_sphere_add(view_align=False, enter_editmode=False, location=(0,0,0), rotation=(0.0, 0.0, 0.0), layers=current_layers)
                ball                 = bpy.context.scene.objects.active
                ball.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
                ball.name            = "Ball (NURBS)_"+atom[0]
                ball.active_material = atom[1]
                ball.parent = new_atom_mesh
                new_atom_mesh.dupli_type = 'VERTS'
                LOADED_STRUCTURES_DUPLI.append(ball)
                   
            
    # ... draw Mesh balls  
    else: 
        for atom_list in draw_atom_type_list:

            if used_dupliverts == False:  

                structure = []
                for atom in atom_list:
                    sys.stdout.write("Atom No. %d has been built\r" % (number_loaded_atoms+1) )
                    sys.stdout.flush()

                    current_layers=bpy.context.scene.layers
                    bpy.ops.mesh.primitive_uv_sphere_add(segments=Ball_azimuth, ring_count=Ball_zenith, size=1, view_align=False, enter_editmode=False, location=atom[2], rotation=(0, 0, 0), layers=current_layers)
                    ball                 = bpy.context.scene.objects.active
                    ball.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
                    ball.name            = atom[0]
                    ball.active_material = atom[1]
                    structure.append(ball)
                    number_loaded_atoms += 1         
                LOADED_STRUCTURES.append(structure)
  

            if used_dupliverts == True:

                atom_vertices = []       
                for atom in atom_list:
                    atom_vertices.append( (atom[2][0], atom[2][1], atom[2][2]) )

                atom_mesh = bpy.data.meshes.new("Mesh_"+atom[0])
                atom_mesh.from_pydata(atom_vertices, [], [])
                atom_mesh.update()
                new_atom_mesh = bpy.data.objects.new(atom[0], atom_mesh)
                bpy.context.scene.objects.link(new_atom_mesh)

                current_layers=bpy.context.scene.layers
                bpy.ops.mesh.primitive_uv_sphere_add(segments=Ball_azimuth, ring_count=Ball_zenith, size=1, view_align=False, enter_editmode=False, location=(0,0,0), rotation=(0, 0, 0), layers=current_layers)    
                ball                 = bpy.context.scene.objects.active
                ball.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
                ball.name            = "Ball (UV)_"+atom[0]
                ball.active_material = atom[1]
                ball.parent = new_atom_mesh
                new_atom_mesh.dupli_type = 'VERTS'    
                LOADED_STRUCTURES_DUPLI.append(ball)
        

         


    #
    # DRAW VACANCIES
    #
    
    bpy.ops.object.select_all(action='DESELECT')
    
    if draw_atom_type_list_vacancy != []:
    
        if used_dupliverts == False:  
     
            structure = []   
            for atom in atom_list:
                sys.stdout.write("Atom No. %d has been built\r" % (number_loaded_atoms+1) )
                sys.stdout.flush()
                
                current_layers=bpy.context.scene.layers
                bpy.ops.mesh.primitive_cube_add(view_align=False, enter_editmode=False, location=atom[2], rotation=(0.0, 0.0, 0.0), layers=current_layers)
                ball                 = bpy.context.scene.objects.active
                ball.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
                ball.name            = atom[0]
                ball.active_material = atom[1]
                structure.append(ball)
                number_loaded_atoms += 1   
            LOADED_STRUCTURES.append(structure) 
    
    
        if used_dupliverts == True:
   
            atom_vertices = []
            for atom in draw_atom_type_list_vacancy:
                atom_vertices.append( (atom[2][0], atom[2][1], atom[2][2]) )
            
            atom_mesh = bpy.data.meshes.new("Mesh_"+atom[0])
            atom_mesh.from_pydata(atom_vertices, [], [])
            atom_mesh.update()
            new_atom_mesh = bpy.data.objects.new(atom[0], atom_mesh)
            bpy.context.scene.objects.link(new_atom_mesh)
            
            current_layers=bpy.context.scene.layers
            bpy.ops.mesh.primitive_cube_add(view_align=False, enter_editmode=False, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), layers=current_layers)
            ball                 = bpy.context.scene.objects.active
            ball.scale           = (atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor,atom[3]*Ball_radius_factor)
            ball.name            = "Cube_"+atom[0]
            ball.active_material = atom[1]
            ball.parent = new_atom_mesh
            new_atom_mesh.dupli_type = 'VERTS'  
            LOADED_STRUCTURES_DUPLI.append(ball)



    print()    
      
      
      
    #
    #
    #
    #
    #          DRAWING OF STICKS
    #
    #
    #



    if used_stick == True:
 
        # Create a new material with the corresponding color. The
        # color is taken from the all_atom list, it is the last entry
        # in the data file (index -1).
        bpy.ops.object.material_slot_add()
        stick_material               = bpy.data.materials.new(Data_all_atoms[ALL_EXISTING_ATOMS-1][2])  
        stick_material.diffuse_color = Data_all_atoms[ALL_EXISTING_ATOMS-1][3]
 
        # This is the unit vector of the z axis
        up_axis = Vector((0.0, 0.0, 1.0))
 
 
        # For all sticks, do ...
        for i in range(0,Number_of_sticks):
            # Print on the terminal the actual number of the stick that is build
            sys.stdout.write("Stick No. %d has been built\r" % (i+1) )
            sys.stdout.flush()
            # The vectors of the two atoms are build 
            k1 = Vector((atom_x[stick_atom1[i]-1],atom_y[stick_atom1[i]-1],atom_z[stick_atom1[i]-1]))
            k2 = Vector((atom_x[stick_atom2[i]-1],atom_y[stick_atom2[i]-1],atom_z[stick_atom2[i]-1]))
            # This is the difference of both vectors
            v = (k2-k1)
            # Angle with respect to the z-axis
            angle   = v.angle(up_axis, 0)
            # Cross-product between v and the z-axis vector. It is the vector of
            # rotation.
            axis    = up_axis.cross(v)
            # Calculate Euler angles
            euler   = Matrix.Rotation(angle, 4, axis).to_euler()
            # Create stick
            current_layers=bpy.context.scene.layers
            bpy.ops.mesh.primitive_cylinder_add(vertices=Stick_sectors, radius=Stick_diameter, depth= v.length, cap_ends=True, view_align=False, enter_editmode=False, location= ((k1+k2)*0.5), rotation=(0,0,0), layers=current_layers)
            # Put the stick into the scene ...
            stick                 = bpy.context.scene.objects.active
            # ... and rotate the stick.
            stick.rotation_euler  = euler
            # Material ... 
            stick.active_material = stick_material
            # ... and name
            stick.name            = Data_all_atoms[ALL_EXISTING_ATOMS-1][1]


    print("\n\nAll atoms and sticks have been drawn - finished (%d) .\n\n" % Number_of_total_atoms)

    return Number_of_total_atoms
