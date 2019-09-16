### BEGIN GPL LICENSE BLOCK #####
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

# --------------------------------------------------------------------------
# The sun positioning algorithms are based on the National Oceanic
# and Atmospheric Administration's (NOAA) Solar Position Calculator
# which rely on calculations of Jean Meeus' book "Astronomical Algorithms."
# Use of NOAA data and products are in the public domain and may be used
# freely by the public as outlined in their policies at
#               www.nws.noaa.gov/disclaimer.php
# --------------------------------------------------------------------------
# The world map images have been composited from two NASA images.
# NASA's image use policy can be found at:
# http://www.nasa.gov/audience/formedia/features/MP_Photo_Guidelines.html
# --------------------------------------------------------------------------

# <pep8 compliant>

bl_info = {
    "name": "Sun Position 2.8",
    "author": "Michael Martin, Kevan Cress",
    "version": (3, 0, 1),
    "blender": (2, 80, 0),
    "location": "World > Sun Position",
    "description": "Show sun position with objects and/or sky texture",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/" \
        "Scripts/3D_interaction/Sun_Position",
        "tracker_url": "https://projects.blender.org/tracker/" \
        "index.php?func=detail&aid=29714",
    "category": "3D View"}  #  "Lighting"} ?

import bpy
from . properties import *
from . ui_sun import *
from . map import SunPos_Help
from . hdr import SunPos_HdrHelp

############################################################################

classes = (
    SunPos_OT_Controller,
    SunPos_OT_Preferences,
    SunPos_OT_PreferencesDone,
    SunPos_OT_DayRange,
    SunPos_OT_SetObjectGroup,
    SunPos_OT_ClearObjectGroup,
    SunPos_OT_TimePlace,
    SunPos_OT_Map,
    SunPos_OT_Hdr,
    SPOS_PT_Panel,
    SunPos_OT_MapChoice,
    SunPos_Help,
    SunPos_HdrHelp,
)

def register():
    bpy.utils.register_class(SunPosSettings)
    bpy.types.Scene.SunPos_property = (
        bpy.props.PointerProperty(type=SunPosSettings,
                        name="Sun Position",
                        description="Sun Position Settings"))
    bpy.utils.register_class(SunPosPreferences)
    bpy.types.Scene.SunPos_pref_property = (
        bpy.props.PointerProperty(type=SunPosPreferences,
                        name="Sun Position Preferences",
                        description="SP Preferences"))

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.SunPos_pref_property
    bpy.utils.unregister_class(SunPosPreferences)
    del bpy.types.Scene.SunPos_property
    bpy.utils.unregister_class(SunPosSettings)
