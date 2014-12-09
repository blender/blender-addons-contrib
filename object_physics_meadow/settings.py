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

import bpy
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import *

def copy_rna_enum_items(type, prop):
    return [(item.identifier, item.name, item.description) for item in type.bl_rna.properties[prop].enum_items]

def find_meadow_object(context, type):
    scene = context.scene
    for ob in scene.objects:
        if ob.meadow.type == type:
            return ob

#-----------------------------------------------------------------------

class MeadowAddonPreferences(AddonPreferences):
    bl_idname = __package__

    patch_groupname = StringProperty(
        name="Patch Group Name",
        description="Object group for storing patch copies of templates",
        default="Patches"
        )
    blob_groupname = StringProperty(
        name="Blob Group Name",
        description="Object group for storing blob duplicators",
        default="Blobs"
        )

    def patch_group(self, context):
        return bpy.data.groups.get(self.patch_groupname)
    def blob_group(self, context):
        return bpy.data.groups.get(self.blob_groupname)

    def draw_ex(self, layout, context):
        layout.prop(self, "patch_groupname")
        layout.prop(self, "blob_groupname")

    def draw(self, context):
        self.draw_ex(self, self.layout, context)

def get(context):
    userprefs = context.user_preferences
    return userprefs.addons[__package__].preferences

#-----------------------------------------------------------------------

type_items = [
    ('NONE', 'None', ''),
    ('GROUND', 'Ground', 'Base mesh defining the ground surface'),
    ('BLOBGRID', 'Blob Grid', 'Grid vertex positions for simulated blobs'),
    ('TEMPLATE', 'Template', 'Template for copies and instancing'),
    ]
unique_types = {'GROUND', 'BLOBGRID'}

def type_update(self, context):
    if self.type in unique_types:
        scene = context.scene
        for ob in scene.objects:
            if ob != self.id_data and ob.meadow.type == self.type:
                ob.meadow.type = 'NONE'

def vgroup_items(self, context):
    groundob = find_meadow_object(context, 'GROUND')
    if groundob:
        return [(v.name, v.name, "", 'NONE', v.index) for v in groundob.vertex_groups]
    return []

class MeadowObjectSettings(PropertyGroup):
    type = EnumProperty(
        name="Type",
        description="Role of the object in the meadow simulation",
        items=type_items,
        update=type_update
        )
    
    use_as_dupli = BoolProperty(
        name="Use as Dupli",
        description="Use the object for dupli instances",
        default=True
        )
    
    seed = IntProperty(
        name="Seed",
        description="General random number seed value",
        default=12345
        )
    sampling_levels = IntProperty(
        name="Sampling Levels",
        description="Maximum number of sampling subdivision levels",
        default=4
        )
    
    patch_radius = FloatProperty(
        name="Patch Radius",
        description="Free area around each patch where no other patch overlaps",
        default=1.0,
        min=0.01
        )
    max_patches = IntProperty(
        name="Maximum Patch Number",
        description="Maximum number of patches",
        default=1000,
        max=1000000,
        soft_max=10000
        )
    
    density_vgroup_name = StringProperty(
        name="Density Vertex Group Name",
        description="Name of the vertex group to use for patch density",
        default=""
        )

    # XXX enum wrapper would be more convenient, but harder to manage
#    density_vgroup = EnumProperty(
#        name="Density Vertex Group",
#        description="Vertex group to use for patch density",
#        items=vgroup_items
#        )

    # internal
    blob_index = IntProperty(
        name="Blob Index",
        description="Unique blob index of the object",
        default=-1,
        options={'HIDDEN'}
        )

#-----------------------------------------------------------------------

def register():
    bpy.utils.register_class(MeadowAddonPreferences)
    
    bpy.utils.register_class(MeadowObjectSettings)
    bpy.types.Object.meadow = PointerProperty(type=MeadowObjectSettings)

def unregister():
    bpy.utils.unregister_class(MeadowAddonPreferences)
    
    del bpy.types.Object.meadow
    bpy.utils.unregister_class(MeadowObjectSettings)
