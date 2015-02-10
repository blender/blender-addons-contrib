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

# <pep8 compliant>

import bpy, os
from bpy.types import Operator, PropertyGroup
from bpy.props import *

from data_overrides.util import *

# ======================================================================================

class Override(PropertyGroup):
    id_name = StringProperty(name="ID Name", description="Name of the overridden ID datablock")
    id_library = StringProperty(name="ID Library", description="Library file path of the overridden ID datablock")

    show_expanded = BoolProperty(name="Show Expanded", description="Expand override details in the interface", default=True)

    def find_id_data(self, blend_data):
        return find_id_data(blend_data, self.id_name, self.id_library)

    @property
    def label(self):
        return "{}".format(self.id_name)

    def draw(self, context, layout):
        id_data = self.find_id_data(context.blend_data)
        if not id_data:
            return

        split = layout.split(0.05)

        col = split.column()
        col.prop(self, "show_expanded", emboss=False, icon_only=True, icon='TRIA_DOWN' if self.show_expanded else 'TRIA_RIGHT')

        col = split.column()
        icon = bpy.types.UILayout.icon(id_data)
        col.label(text=self.label, icon_value=icon)

def target_library(target):
    id_data = target.id_data
    return id_data.library.filepath if id_data.library else ""

# This name is not human-readable, but is unique and avoids issues with escaping
# when combining file paths and ID names and RNA paths
# For lookup and display in the UI other name/path properties of the override should be used
def target_identifier(target):
    id_data = target.id_data
    try:
        path = target.path_from_id()
    # ValueError is raise when the target type does not support path_from_id
    except ValueError:
        path = ""
    identifier, number = data_uuid(id_data, path)
    return identifier

def find_override(scene, target):
    return scene.overrides.get(target_identifier(target), None)

def add_override(scene, target):
    id_data = target.id_data

    override = scene.overrides.add()
    override.name = target_identifier(target)
    override.id_name = id_data.name
    override.id_library = id_data.library.filepath if id_data.library else ""
    #override.init(target) # TODO

def remove_override(scene, target):
    override = scene.overrides.find(target)
    if override:
        scene.overrides.remove(override)

# ======================================================================================

def register_property_groups():
    bpy.utils.register_class(Override)

    bpy.types.Scene.overrides = CollectionProperty(type=Override)

def unregister_property_groups():
    del bpy.types.Scene.overrides
    bpy.utils.register_class(Override)

# ======================================================================================

def register():
    register_property_groups()

def unregister():
    unregister_property_groups()
