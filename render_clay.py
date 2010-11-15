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

# <pep8 compliant>

bl_addon_info = {
    "name": "Clay Render",
    "author": "Fabio Russo <ruesp83@libero.it>",
    "version": (0, 5),
    "blender": (2, 5, 5),
    "location": "Render > Clay Render",
    "description": "This script, applies a temporary material to all objects"\
        "of the scene.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Clay_Render",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22971&group_id=153&atid=467",
    "category": "Render"}

import bpy

from bpy.props import BoolProperty


bpy.types.Scene.Clay = BoolProperty(
    name='Clay Render',
    description='Use Clay Render',
    default=False)


def search():
    mats = bpy.data.materials
    Find = False
    id = None
    for m in mats:
        if m.name == "Clay_Render":
            id = m
            Find = True
            break
    return id


def create_mat():
    id = search()
    if id == None:
        id = bpy.data.materials.new("Clay_Render")
        #diffuse
        id.diffuse_shader = "OREN_NAYAR"
        id.diffuse_color = 0.800, 0.741, 0.536
        id.diffuse_intensity = 1
        id.roughness = 0.909
        #specular
        id.specular_shader = "COOKTORR"
        id.specular_color = 1, 1, 1
        id.specular_hardness = 10
        id.specular_intensity = 0.115


def draw_clay(self, context):
        layout = self.layout
        sd = context.scene
        rnd = context.scene.render
        rnl = rnd.layers.active

        create_mat()

        split = layout.split()
        col = split.column()

        col.prop(sd, "Clay",)

        col = split.column()

        id = search()
        col.prop(id, "diffuse_color", text="")
        self.layout.separator()
        App_Clay = context.scene.Clay
        if App_Clay:
            rnl.material_override = id
            col.active = True
        else:
            rnl.material_override = None
            col.active = False


def register():
    bpy.types.RENDER_PT_render.prepend(draw_clay)
    pass


def unregister():
    rnd = bpy.context.scene.render
    rnl = rnd.layers.active
    rnl.material_override = None
    bpy.types.RENDER_PT_render.remove(draw_clay)
    pass

if __name__ == "__main__":
    register()
