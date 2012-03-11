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
    "name": "Render Time Estimation",
    "author": "Jason van Gumster (Fweeb)",
    "version": (0, 4, 0),
    "blender": (2, 6, 2),
    "api": 44810,
    "location": "UV/Image Editor > Properties > Image",
    "description": "Estimates the time to complete rendering on animations",
    "warning": "Does not work on OpenGL renders",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Render/Render_Time_Estimation",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=30452&group_id=153&atid=467",
    "category": "Render"}


import bpy, time
from bpy.app.handlers import persistent
from datetime import timedelta


timer = {"average": 0.0, "total": 0.0, "time_start": 0.0, "is_rendering": False}

def set_rendering(scene):
    timer["is_rendering"] = True

@persistent
def unset_rendering(scene):
    timer["is_rendering"] = False

@persistent
def start_timer(scene):
    set_rendering(scene)

    if scene.frame_current == scene.frame_start:
        timer["average"] = 0.0
        timer["total"] = 0.0

    timer["time_start"] = time.time()

@persistent
def end_timer(scene):
    render_time = time.time() - timer["time_start"]
    timer["total"] += render_time
    if scene.frame_current == scene.frame_start:
        timer["average"] = render_time
    else:
        timer["average"] = (timer["average"] + render_time) / 2

    print("Total render time: " + str(timedelta(seconds = timer["total"])))
    print("Estimated completion: " + str(timedelta(seconds = (timer["average"] * (scene.frame_end - scene.frame_current)))))


# UI

def image_panel_rendertime(self, context):
    scene = context.scene
    layout = self.layout

    if context.space_data.image is not None and context.space_data.image.type == 'RENDER_RESULT':
        layout.label(text = "Total render time: " + str(timedelta(seconds = timer["total"])))

        if timer["is_rendering"] and scene.frame_current != scene.frame_start:
            layout.label(text = "Estimated completion: " + str(timedelta(seconds = (timer["average"] * (scene.frame_end - scene.frame_current)))))


# Registration

def register():
    bpy.app.handlers.render_complete.append(unset_rendering)
    bpy.app.handlers.render_cancel.append(unset_rendering)
    bpy.app.handlers.render_pre.append(start_timer)
    bpy.app.handlers.render_post.append(end_timer)
    bpy.types.IMAGE_PT_image_properties.append(image_panel_rendertime)


def unregister():
    bpy.app.handlers.render_pre.remove(start_timer)
    bpy.app.handlers.render_post.remove(end_timer)
    bpy.app.handlers.render_cancel.append(unset_rendering)
    bpy.app.handlers.render_complete.remove(unset_rendering)
    bpy.types.IMAGE_PT_image_properties.remove(image_panel_rendertime)

if __name__ == '__main__':
    register()
