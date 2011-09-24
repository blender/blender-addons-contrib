# -*- coding: utf-8 -*-
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



# Blender Add-Ons menu registration (in User Prefs)
bl_info = {
    'name': 'Cursor Memory',
    'author': 'Morgan Mörtsell (Seminumerical)',
    'version': (0, 6, 1),
    'blender': (2, 5, 9),
    'api': 39307,
    'location': 'View3D > Properties > Cursor',
    'description': '3D-cursor memory',
    'warning': '', # used for warning icon and text in addons panel
    'wiki_url': 'http://blenderpythonscripts.wordpress.com/',
    'tracker_url': '',
    'category': '3D View'}



"""
  TODO:

      IDEAS:
	  Add/Subtract
	  
      LATER:

      ISSUES:
          Bugs:
              Seg-faults when unregistering addon...
          Mites:
	      CTRL-Z forces memory to world origin (0,0,0)... why??
		  Happens only if undo reaches 'default world state'
		  How to Reproduce:
		      1. File->New
		      2. Move 3D-cursor
		      3. Set memory
		      4. Move cube
		      5. CTRL-Z

      QUESTIONS:
  
  
  --- 0.6.1 ---------------------------------------------------------------------------------------
  2011-09-23 - Adaptations for the 2.59 API
  2011-05-10 - Refactoring: changes due to splitting of misc_utils.py...
  2011-05-08 - Refactoring: changes due to seminumerical.py renamed to misc_utils.py...
                   ...and moved bl_info
  --- 0.6.0 ---------------------------------------------------------------------------------------
  2011-04-21 - Adaptations for the 2.57 API
                  Updated registration procedures
  --- pre 0.5.0 -----------------------------------------------------------------------------------
  2011-01-29 - Refactoring: Memory addon separated from Cursor Control
	       Refactoring: Changed some names to something more suitable
  2011-01-16 - Small cleanup
               Step length added to Control panel
               Added move_to_SL to Control, and reworked SL_recall for Memory panel
               More changes due to refactoring in the seminumerical module
  2011-01-13 - Changes due to refactoring in the seminumerical module
               Changes due to bugfix in seminumerical module
               Bugfix: Mirror now correctly ignores additional vertices when a face is selected.
               Improved history tracker with back and forward buttons.
               Split addon into three panels (Control, Memory and History)
  2011-01-12 - Some buttons are now hidden in edit mode.
               Changed some icons
               Changed some operator names
               Refactored setCursor into the CursorControl class.
               A working version of the move-to-with-offset feature
               Changed the workings of move to center of cylinder and sphere.
               Changed the workings of move to perimeter of cylinder and sphere.
               Basic history tracker with undo working
  --- pre 0.4.1 -----------------------------------------------------------------------------------
  2011-01-09 - Support for Blender 2.56a
  --- pre 0.4 -----------------------------------------------------------------------------------
  2010-11-15 - Support for Blender 2.55b
  2010-10-28 - Added Cursor Location to the panel
  2010-10-10 - Refactored drawButton into utility class seminumerical.GUI
  2010-10-06 - Desaturated color of SL-cursor
  2010-10-02 - SL is now drawn as a dimmed replica of 3D-cursor 
               Four point sphere.
  2010-09-27 - Some cleanup and refactoring.
               Gathered all properties in a single structure (CursorControlData).
               Updates due to refactoring of the seminumerical module
  2010-09-15 - Default value of view3d_cursor_linex_choice is now -1
               Improved some operator descriptions.
               Changed bl_addon_info.name
  --- pre 0.3 -----------------------------------------------------------------------------------
  2010-09-15 - Closest point on 3-point sphere
               Fixed bug in cc_closestP2F. It now works as intended on quad faces.
               Changed 'circum center' to the more generic 'closest point on cylinder axis'
               SL is nolonger destroyed by cursor_to_linex
               Changed some icons in the UI
  --- pre 0.2.1 -----------------------------------------------------------------------------------
  2010-09-14 - Support for Blender 2.54b
  --- pre 0.2.0 -----------------------------------------------------------------------------------
  2010-09-14 - Fixed bug in cursor_to_face
  2010-09-13 - Triangle circumcenter (3-point circle center)
               View now updates when enable/disable draw is clicked
               Expand / contract SL properties.
  2010-09-12 - Fixed enable/disable buttons
               Move to closest vertex/line/edge/plane/face
               UI redesigned
  2010-09-11 - Local view now works like a charm
  --- pre 0.1.0 -----------------------------------------------------------------------------------
  2010-09-06 - Force update callback was interfering with undo.
               Thankfully the verts, edge and face select-count updates as it should,
               so I was able to read get the necessary information from there.
               Forced update is now done inside the operators where mesh data is accessed.
  2010-09-05 - Force update for edit mode is now working.
               Thanks to Buerbaum Martin (Pontiac). I peeked a bit at his code for registering a callback...
"""



import bpy
import bgl
import math
from mathutils import Vector, Matrix
from mathutils import geometry
from misc_utils import *
from constants_utils import *
from cursor_utils import *
from ui_utils import *



PRECISION = 4



class CursorMemoryData(bpy.types.PropertyGroup):

    savedLocationDraw = bpy.props.BoolProperty(description="Draw SL cursor in 3D view",default=1)
    savedLocation = bpy.props.FloatVectorProperty(name="",description="Saved Location",precision=PRECISION)


class VIEW3D_OT_cursor_memory_save(bpy.types.Operator):
    '''Save cursor location.'''
    bl_idname = "view3d.cursor_memory_save"
    bl_label = "Save cursor location."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_memory
        cc.savedLocation = CursorAccess.getCursor()
        CursorAccess.setCursor(cc.savedLocation)
        return {'FINISHED'}



class VIEW3D_OT_cursor_memory_swap(bpy.types.Operator):
    '''Swap cursor location.'''
    bl_idname = "view3d.cursor_memory_swap"
    bl_label = "Swap cursor location."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        location = CursorAccess.getCursor().copy()
        cc = context.scene.cursor_memory
        CursorAccess.setCursor(cc.savedLocation)
        cc.savedLocation = location
        return {'FINISHED'}



class VIEW3D_OT_cursor_memory_recall(bpy.types.Operator):
    '''Recall cursor location.'''
    bl_idname = "view3d.cursor_memory_recall"
    bl_label = "Recall cursor location."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_memory
        CursorAccess.setCursor(cc.savedLocation)
        return {'FINISHED'}



class VIEW3D_OT_cursor_memory_show(bpy.types.Operator):
    '''Show cursor memory.'''
    bl_idname = "view3d.cursor_memory_show"
    bl_label = "Show cursor memory."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_memory
        cc.savedLocationDraw = True
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_memory_hide(bpy.types.Operator):
    '''Hide cursor memory.'''
    bl_idname = "view3d.cursor_memory_hide"
    bl_label = "Hide cursor memory."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_memory
        cc.savedLocationDraw = False
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_PT_cursor_memory(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Cursor Memory"
    bl_default_closed = True

    @classmethod
    def poll(self, context):
        # Display in object or edit mode.
        if (context.area.type == 'VIEW_3D' and
            (context.mode == 'EDIT_MESH'
            or context.mode == 'OBJECT')):
            return 1

        return 0

    def draw_header(self, context):
        layout = self.layout
        cc = context.scene.cursor_memory
        if cc.savedLocationDraw:
            GUI.drawIconButton(True, layout, 'RESTRICT_VIEW_OFF', "view3d.cursor_memory_hide", False)
        else:
            GUI.drawIconButton(True, layout, 'RESTRICT_VIEW_ON' , "view3d.cursor_memory_show", False)
        #layout.prop(sce, "cursor_memory.savedLocationDraw")

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        cc = context.scene.cursor_memory

        row = layout.row()
        col = row.column()
        row2 = col.row()
        GUI.drawIconButton(True, row2, 'FORWARD', "view3d.cursor_memory_save")
        row2 = col.row()
        GUI.drawIconButton(True, row2, 'FILE_REFRESH', "view3d.cursor_memory_swap")
        row2 = col.row()
        GUI.drawIconButton(True, row2, 'BACK'        , "view3d.cursor_memory_recall")
        col = row.column()
        col.prop(cc, "savedLocation")



class VIEW3D_PT_cursor_memory_init(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Register callback"
    bl_default_closed = True

    initDone = False

    @classmethod
    def poll(cls, context):
        if VIEW3D_PT_cursor_memory_init.initDone:
            return 0
        print ("Cursor Memory draw-callback registration...")
        sce = context.scene
        if context.area.type == 'VIEW_3D':
            for reg in context.area.regions:
                if reg.type == 'WINDOW':
                    # Register callback for SL-draw
                    reg.callback_add(
                        cursor_memory_draw,
                        (cls,context),
                        'POST_PIXEL')
                    VIEW3D_PT_cursor_memory_init.initDone = True
                    print ("Cursor Memory draw-callback registered")
                    # Unregister to prevent double registration...
                    # Started to fail after v2.57
                    # bpy.types.unregister(VIEW3D_PT_cursor_memory_init)
        else:
            print("View3D not found, cannot run operator")
        return 0

    def draw_header(self, context):
        pass

    def draw(self, context):
        pass



def cursor_memory_draw(cls,context):
    cc = context.scene.cursor_memory

    draw = 0
    if hasattr(cc, "savedLocationDraw"):
        draw = cc.savedLocationDraw

    if(draw):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glShadeModel(bgl.GL_FLAT)
        p1 = Vector(cc.savedLocation)
        location = region3d_get_2d_coordinates(context, p1)
        alpha = 1-PHI_INV
        # Circle
        color = ([0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1])
        offset = ([-4.480736161291701, -8.939966636005579],
            [-0.158097634992133, -9.998750178787843],
            [4.195854066857877, -9.077158622037636],
            [7.718765411993642, -6.357724476147943],
            [9.71288060283854, -2.379065025383466],
            [9.783240669628, 2.070797430975971],
            [7.915909938224691, 6.110513059466902],
            [4.480736161291671, 8.939966636005593],
            [0.15809763499209872, 9.998750178787843],
            [-4.195854066857908, 9.077158622037622],
            [-7.718765411993573, 6.357724476148025],
            [-9.712880602838549, 2.379065025383433],
            [-9.783240669627993, -2.070797430976005],
            [-7.915909938224757, -6.110513059466818])
        bgl.glBegin(bgl.GL_LINE_LOOP)
        for i in range(14):
            bgl.glColor4f(color[i][0], color[i][1], color[i][2], alpha)
            bgl.glVertex2f(location[0]+offset[i][0], location[1]+offset[i][1])
        bgl.glEnd()

        # Crosshair
        offset2 = 20
        offset = 5
        bgl.glColor4f(0, 0, 0, alpha)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0]-offset2, location[1])
        bgl.glVertex2f(location[0]- offset, location[1])
        bgl.glEnd()
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0]+ offset, location[1])
        bgl.glVertex2f(location[0]+offset2, location[1])
        bgl.glEnd()
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0], location[1]-offset2)
        bgl.glVertex2f(location[0], location[1]- offset)
        bgl.glEnd()
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0], location[1]+ offset)
        bgl.glVertex2f(location[0], location[1]+offset2)
        bgl.glEnd()
        
        

def register():
    bpy.utils.register_module(__name__)
    # Register Cursor Memory Structure
    bpy.types.Scene.cursor_memory = bpy.props.PointerProperty(type=CursorMemoryData, name="")
        


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
