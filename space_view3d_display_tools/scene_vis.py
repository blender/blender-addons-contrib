# space_view_3d_display_tools.py Copyright (C) 2014, Jordi Vall-llovera
#
# Multiple display tools for fast navigate/interact with the viewport
#
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

bl_info = {
    "name": "Display Tools",
    "author": "Jordi Vall-llovera Medina, Jhon Wallace",
    "version": (1, 6, 0),
    "blender": (2, 7, 0),
    "location": "Toolshelf",
    "description": "Display tools for fast navigate/interact with the viewport",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/"
                "3D_interaction/Display_Tools",
    "tracker_url": "",
    "category": "Addon Factory"}

"""
Additional links:
    Author Site: http://www.jordiart.com
"""

import bpy
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        AddonPreferences,
        )
from bpy.props import (
        IntProperty,
        BoolProperty,
        EnumProperty,
        StringProperty,
        )


# define base dummy class for inheritance
class BasePollCheck:
    @classmethod
    def poll(cls, context):
        return True

# Set Render Settings
def set_render_settings(context):
    scene = context.scene
    render = scene.render
    render.simplify_subdivision = 0
    render.simplify_shadow_samples = 0
    render.simplify_child_particles = 0
    render.simplify_ao_sss = 0





# register the classes and props
def register():
    bpy.utils.register_module(__name__)
    # Register Scene Properties



def unregister():

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
