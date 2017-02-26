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


# Fast Navigate toggle function
def trigger_fast_navigate(trigger):
    scene = bpy.context.scene.display_tools
    scene.FastNavigateStop = False

    trigger = not trigger


# Control how to display particles during fast navigate
def display_particles(mode):
    scene = bpy.context.scene.display_tools

    if mode is True:
        for particles in bpy.data.particles:
            if particles.type == 'EMITTER':
                particles.draw_method = 'DOT'
                particles.draw_percentage = 100
            else:
                particles.draw_method = 'RENDER'
                particles.draw_percentage = 100
    else:
        for particles in bpy.data.particles:
            if particles.type == 'EMITTER':
                particles.draw_method = 'DOT'
                particles.draw_percentage = scene.ParticlesPercentageDisplay
            else:
                particles.draw_method = 'RENDER'
                particles.draw_percentage = scene.ParticlesPercentageDisplay


# Fast Navigate operator
class FastNavigate(Operator):
    bl_idname = "view3d.fast_navigate_operator"
    bl_label = "Fast Navigate"
    bl_description = "Operator that runs Fast navigate in modal mode"

    trigger = BoolProperty(default=False)
    mode = BoolProperty(default=False)

    def modal(self, context, event):
        context.area.tag_redraw()
        scene = context.scene.display_tools

        if scene.FastNavigateStop is True:
            self.cancel(context)
            return {'FINISHED'}

        if scene.EditActive is True:
            self.fast_navigate_stuff(context, event)
            return {'PASS_THROUGH'}
        else:
            obj = context.active_object
            if obj:
                if obj.mode != 'EDIT':
                    self.fast_navigate_stuff(context, event)
                    return {'PASS_THROUGH'}
                else:
                    return {'PASS_THROUGH'}
            else:
                self.fast_navigate_stuff(context, event)
                return {'PASS_THROUGH'}

    def execute(self, context):
        context.window_manager.modal_handler_add(self)
        trigger_fast_navigate(self.trigger)
        scene = context.scene.display_tools
        scene.DelayTime = scene.DelayTimeGlobal
        return {'RUNNING_MODAL'}

    # Do repetitive fast navigate related stuff
    def fast_navigate_stuff(self, context, event):
        scene = context.scene.display_tools
        view = context.space_data

        if context.area.type != 'VIEW_3D':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'ESC' or event.type == 'RET' or event.type == 'SPACE':
            self.cancel(context)
            return {'CANCELLED'}

        if scene.FastNavigateStop is True:
            self.cancel(context)
            return {'CANCELLED'}

        # fast navigate while orbit/panning
        if event.type == 'MIDDLEMOUSE':
            if scene.Delay is True:
                if scene.DelayTime < scene.DelayTimeGlobal:
                    scene.DelayTime += 1
            view.viewport_shade = scene.FastMode
            self.mode = False

        # fast navigate while transform operations
        if event.type == 'G' or event.type == 'R' or event.type == 'S':
            if scene.Delay is True:
                if scene.DelayTime < scene.DelayTimeGlobal:
                    scene.DelayTime += 1
            view.viewport_shade = scene.FastMode
            self.mode = False

        # fast navigate while menu popups or duplicates
        if event.type == 'W' or event.type == 'D' or event.type == 'L'\
          or event.type == 'U' or event.type == 'I' or event.type == 'M'\
          or event.type == 'A' or event.type == 'B':
            if scene.Delay is True:
                if scene.DelayTime < scene.DelayTimeGlobal:
                    scene.DelayTime += 1
            view.viewport_shade = scene.FastMode
            self.mode = False

        # fast navigate while numpad navigation
        if (event.type == 'NUMPAD_PERIOD' or event.type == 'NUMPAD_1' or
           event.type == 'NUMPAD_2' or event.type == 'NUMPAD_3' or
           event.type == 'NUMPAD_4' or event.type == 'NUMPAD_5' or
           event.type == 'NUMPAD_6' or event.type == 'NUMPAD_7' or
           event.type == 'NUMPAD_8' or event.type == 'NUMPAD_9'):

            if scene.Delay is True:
                if scene.DelayTime < scene.DelayTimeGlobal:
                    scene.DelayTime += 1
            view.viewport_shade = scene.FastMode
            self.mode = False

        # fast navigate while zooming with mousewheel too
        if event.type == 'WHEELUPMOUSE' or event.type == 'WHEELDOWNMOUSE':
            scene.DelayTime = scene.DelayTimeGlobal
            view.viewport_shade = scene.FastMode
            self.mode = False

        if event.type == 'MOUSEMOVE':
            if scene.Delay is True:
                if scene.DelayTime == 0:
                    scene.DelayTime = scene.DelayTimeGlobal
                    view.viewport_shade = scene.OriginalMode
                    self.mode = True
            else:
                view.viewport_shade = scene.OriginalMode
                self.mode = True

        if scene.Delay is True:
            scene.DelayTime -= 1
            if scene.DelayTime == 0:
                scene.DelayTime = scene.DelayTimeGlobal
                view.viewport_shade = scene.OriginalMode
                self.mode = True

        if scene.ShowParticles is False:
            for particles in bpy.data.particles:
                if particles.type == 'EMITTER':
                    particles.draw_method = 'NONE'
                else:
                    particles.draw_method = 'NONE'
        else:
            display_particles(self.mode)

    def cancel(self, context):
        scene = context.scene.display_tools
        for particles in bpy.data.particles:
            particles.draw_percentage = scene.InitialParticles


# Fast Navigate Stop
def fast_navigate_stop(context):
    scene = context.scene.display_tools
    scene.FastNavigateStop = True


# Fast Navigate Stop Operator
class FastNavigateStop(Operator):
    bl_idname = "view3d.fast_navigate_stop"
    bl_label = "Stop"
    bl_description = "Stop Fast Navigate Operator"

    def execute(self, context):
        fast_navigate_stop(context)
        return {'FINISHED'}


# register the classes and props
def register():
    bpy.utils.register_module(__name__)
    # Register Scene Properties


def unregister():

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
