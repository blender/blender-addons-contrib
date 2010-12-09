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
    "version": (0, 8),
    "blender": (2, 5, 5),
    "api": 33568,
    "location": "Render > Clay Render",
    "description": "This script, applies a temporary material to all objects"\
        " of the scene.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Clay_Render",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22971&group_id=153&atid=467",
    "category": "Render"}

import bpy
from bpy.props import BoolProperty


def Create_Mat():
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


def Get_Mat():
    Mat = bpy.data.materials["Clay_Render"]
    return Mat


def Exist_Mat():
    if bpy.data.materials.get("Clay_Render"):
        return True

    else:
        return False


class CheckClay(bpy.types.Operator):
    bl_idname = "render.clay"
    bl_label = "Clay Render"

    def execute(self, context):
        if bpy.types.Scene.Clay:
            if not Exist_Mat():
                Create_Mat()
            context.scene.render.layers.active.material_override = Get_Mat()
            bpy.types.Scene.Clay = False
        else:
            context.scene.render.layers.active.material_override = None
            bpy.types.Scene.Clay = True
        return {'FINISHED'}


def draw_clay(self, context):
    ok_clay = not bpy.types.Scene.Clay

    rnd = context.scene.render
    rnl = rnd.layers.active
    split = self.layout.split()
    col = split.column()

    col.operator(CheckClay.bl_idname, emboss=False, icon='CHECKBOX_HLT' \
    if ok_clay else 'CHECKBOX_DEHLT')
    col = split.column()
    if Exist_Mat():
        im = Get_Mat()
        col.prop(im, "diffuse_color", text="")
    self.layout.separator()


def register():
    bpy.types.Scene.Clay = BoolProperty(
    name='Clay Render',
    description='Use Clay Render',
    default=False)
    bpy.types.RENDER_PT_render.prepend(draw_clay)


def unregister():
    rnd = bpy.context.scene.render
    rnl = rnd.layers.active
    rnl.material_override = None
    if Exist_Mat():
        bpy.data.materials.remove(Get_Mat())
    del bpy.types.Scene.Clay
    bpy.types.RENDER_PT_render.remove(draw_clay)


if __name__ == "__main__":
    register()
