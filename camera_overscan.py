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

bl_info = {
    "name": "Camera Overscan",
    "author": "John Roper, Barnstorm VFX, Luca Scheller, dskjal",
    "version": (1, 3, 0),
    "blender": (3, 1, 0),
    "location": "Render Settings > Camera Overscan",
    "description": "Render Overscan",
    "warning": "",
    "doc_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Render/Camera_Overscan",
    "tracker_url": "",
    "category": "Render"}

import bpy
from bpy.types import (
        Panel,
        Operator,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        StringProperty,
        PointerProperty,
        )


class CODuplicateCamera(Operator):
    bl_idname = "scene.co_duplicate_camera"
    bl_label = "Bake to New Camera"
    bl_description = ("Make a new overscan camera with all the settings builtin\n"
                      "Needs an active Camera type in the Scene")

    @classmethod
    def poll(cls, context):
        active_cam = getattr(context.scene, "camera", None)
        return active_cam is not None

    def execute(self, context):
        active_cam = getattr(context.scene, "camera", None)
        try:
            if active_cam and active_cam.type == 'CAMERA':
                cam_obj = active_cam.copy()
                cam_obj.data = active_cam.data.copy()
                cam_obj.name = "Camera_Overscan"
                context.collection.objects.link(cam_obj)
        except:
            self.report({'WARNING'}, "Setting up a new Overscan Camera has failed")
            return {'CANCELLED'}

        return {'FINISHED'}

# foldable panel
class RenderOutputButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)

# ui panel
class RENDER_PT_overscan(RenderOutputButtonsPanel, Panel):
    bl_label = "Overscan"
    bl_parent_id = "RENDER_PT_format"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw_header(self, context):
        overscan = context.scene.camera_overscan
        self.layout.prop(overscan, "RO_Activate", text="")

    def draw(self, context):
        scene = context.scene
        overscan = scene.camera_overscan
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        active_cam = getattr(scene, "camera", None)

        if active_cam and active_cam.type == 'CAMERA':
            col_enable = row.column(align=True)
            if not overscan.RO_Activate:
                col_enable.enabled = False
            col_enable.prop(overscan, 'RO_Custom_Res_X', text="X")
            col_enable.prop(overscan, 'RO_Custom_Res_Y', text="Y")
            col_enable.prop(overscan, 'RO_Custom_Res_Scale', text="%")
            row = layout.row()
            if not overscan.RO_Activate:
                row.enabled = False

            row = layout.row()

            col_enable = row.column(align=True)
            col_enable.prop(overscan, 'RO_Custom_Res_Offset_X', text="dX")
            col_enable.prop(overscan, 'RO_Custom_Res_Offset_Y', text="dY")
            col_enable.prop(overscan, 'RO_Custom_Res_Retain_Aspect_Ratio', text="Retain Aspect Ratio")
            if not overscan.RO_Activate:
                col_enable.enabled = False

            col = layout.column()
            col.separator()
            col.separator()
            col.operator("scene.co_duplicate_camera", icon="RENDER_STILL")
        else:
            row.label(text="No active Camera type in the Scene", icon='INFO')

def RO_Update(self, context):
    scene = context.scene
    overscan = scene.camera_overscan
    render_settings = scene.render
    active_camera = getattr(scene, "camera", None)
    active_cam = getattr(active_camera, "data", None)

    # Check if there is a camera type in the scene (Object as camera doesn't work)
    if not active_cam or active_camera.type not in {'CAMERA'}:
        return None

    if overscan.RO_Activate:
        if overscan.RO_Safe_SensorSize == -1:
            # Save Property Values
            overscan.RO_Safe_Res_X = render_settings.resolution_x
            overscan.RO_Safe_Res_Y = render_settings.resolution_y
            overscan.RO_Safe_SensorSize = active_cam.sensor_width
            overscan.RO_Safe_SensorFit = active_cam.sensor_fit

        if overscan.RO_Custom_Res_X == 0 or overscan.RO_Custom_Res_Y == 0:
            # avoid infinite recursion on props update
            if overscan.RO_Custom_Res_X != render_settings.resolution_x:
                overscan.RO_Custom_Res_X = render_settings.resolution_x
            if overscan.RO_Custom_Res_Y != render_settings.resolution_y:
                overscan.RO_Custom_Res_Y = render_settings.resolution_y

        # Reset Property Values
        active_cam.sensor_width = scene.camera_overscan.RO_Safe_SensorSize

        # Calc Sensor Size
        active_cam.sensor_fit = 'HORIZONTAL'
        dx = overscan.RO_Custom_Res_Offset_X
        dy = overscan.RO_Custom_Res_Offset_Y
        scale = overscan.RO_Custom_Res_Scale * 0.01
        x = int(overscan.RO_Custom_Res_X * scale + dx)
        y = int(overscan.RO_Custom_Res_Y * scale + dy)
        sensor_size_factor = x / overscan.RO_Safe_Res_X

        # Set New Property Values
        active_cam.sensor_width = active_cam.sensor_width * sensor_size_factor
        render_settings.resolution_x = x
        render_settings.resolution_y = y

    else:
        if overscan.RO_Safe_SensorSize != -1:
            # Restore Property Values
            render_settings.resolution_x = int(overscan.RO_Safe_Res_X)
            render_settings.resolution_y = int(overscan.RO_Safe_Res_Y)
            active_cam.sensor_width = overscan.RO_Safe_SensorSize
            active_cam.sensor_fit = overscan.RO_Safe_SensorFit
            overscan.RO_Safe_SensorSize = -1

def get_overscan_object(self, context):
    scene = context.scene
    overscan = scene.camera_overscan
    active_camera = getattr(scene, "camera", None)
    active_cam = getattr(active_camera, "data", None)
    if not active_cam or active_camera.type not in {'CAMERA'} or not overscan.RO_Activate:
        return None
    return overscan

def RO_Update_X_Offset(self, context):
    overscan = get_overscan_object(self, context)
    if overscan == None:
        return None

    if overscan.RO_Custom_Res_Retain_Aspect_Ratio:
        overscan.RO_Activate = False # recursion guard
        overscan.RO_Custom_Res_Offset_Y = overscan.RO_Custom_Res_Offset_X * overscan.RO_Safe_Res_Y / overscan.RO_Safe_Res_X

    overscan.RO_Activate = True
    RO_Update(self, context)


def RO_Update_Y_Offset(self, context):
    overscan = get_overscan_object(self, context)
    if overscan == None:
        return None

    if overscan.RO_Custom_Res_Retain_Aspect_Ratio:
        overscan.RO_Activate = False # recursion guard
        overscan.RO_Custom_Res_Offset_X = int(overscan.RO_Custom_Res_Offset_Y * overscan.RO_Safe_Res_X / overscan.RO_Safe_Res_Y)

    overscan.RO_Activate = True
    RO_Update(self, context)


class camera_overscan_props(PropertyGroup):
    RO_Activate: BoolProperty(
                        default=False,
                        description="Enable/Disable Camera Overscan\n"
                                    "Affects the active Scene Camera only\n"
                                    "(Objects as cameras are not supported)",
                        update=RO_Update
                        )
    RO_Custom_Res_X: IntProperty(
                        default=0,
                        min=0,
                        max=65536,
                        update=RO_Update
                        )
    RO_Custom_Res_Y: IntProperty(
                        default=0,
                        min=0,
                        max=65536,
                        update=RO_Update
                        )
    RO_Custom_Res_Scale: FloatProperty(
                        default=100,
                        min=0,
                        max=1000,
                        step=100,
                        update=RO_Update
    )
    RO_Custom_Res_Offset_X: IntProperty(
                        default=0,
                        min=-65536,
                        max=65536,
                        update=RO_Update_X_Offset
    )
    RO_Custom_Res_Offset_Y: IntProperty(
                        default=0,
                        min=-65536,
                        max=65536,
                        update=RO_Update_Y_Offset
    )
    RO_Custom_Res_Retain_Aspect_Ratio: BoolProperty(
                        default=False,
                        description="Affects dX, dY"
    )

    RO_Safe_Res_X: FloatProperty()
    RO_Safe_Res_Y: FloatProperty()

    # the hard limit is sys.max which is too much, used 65536 instead
    RO_Safe_SensorSize: FloatProperty(
                        default=-1,
                        min=-1,
                        max=65536
                        )
    RO_Safe_SensorFit: StringProperty()


def register():
    bpy.utils.register_class(CODuplicateCamera)
    bpy.utils.register_class(camera_overscan_props)
    bpy.utils.register_class(RENDER_PT_overscan)
    bpy.types.Scene.camera_overscan = PointerProperty(
                                        type=camera_overscan_props
                                        )


def unregister():
    bpy.utils.unregister_class(RENDER_PT_overscan)
    bpy.utils.unregister_class(CODuplicateCamera)
    bpy.utils.unregister_class(camera_overscan_props)
    del bpy.types.Scene.camera_overscan


if __name__ == "__main__":
    register()
