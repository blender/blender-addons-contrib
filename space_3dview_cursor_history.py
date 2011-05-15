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
    'name': 'Cursor History',
    'author': 'Morgan Mörtsell (Seminumerical)',
    'version': (0, 6, 0),
    'blender': (2, 5, 7),
    'api': 36147,
    'location': 'View3D > Properties > Cursor',
    'description': 'Remembers the positions of the 3D-cursor and lets you navigate back and forth through the history.',
    'warning': '', # used for warning icon and text in addons panel
    'wiki_url': 'http://blenderpythonscripts.wordpress.com/',
    'tracker_url': '',
    'category': '3D View'}



"""
  TODO:

      IDEAS:

      LATER:

      ISSUES:
          Bugs:
              Seg-faults when unregistering addon...
          Mites:
            * History back button does not light up on first cursor move.
              It does light up on the second, or when mouse enters the tool-area
            * Switching between local and global view triggers new cursor position in history trace.
            * Each consecutive click on the linex operator triggers new cursor position in history trace.
                 (2011-01-16) Was not able to fix this because of some strange script behaviour
                              while trying to clear linexChoice from addHistoryLocation

      QUESTIONS:



  2011-05-10 - Refactoring: changes due to splitting of misc_utils.py...
  2011-05-08 - Refactoring: changes due to seminumerical.py renamed to misc_utils.py...
                 ...and moved bl_info
  --- 0.6.0 ---------------------------------------------------------------------------------------
  2011-04-21 - Adaptations for the 2.57 API
                  Updated registration procedures
  --- pre 0.5.0 -----------------------------------------------------------------------------------
  2011-01-29 - Refactoring: History addon separated from Cursor Control
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



class CursorHistoryData(bpy.types.PropertyGroup):
    # History tracker
    historyDraw = bpy.props.BoolProperty(description="Draw history trace in 3D view",default=1)
    historyDepth = 144
    historyWindow = 12
    historyPosition = [-1] # Integer must be in a list or else it can not be written to
    historyLocation = []
    #historySuppression = [False] # Boolean must be in a list or else it can not be written to

    def addHistoryLocation(self, l):
        if(self.historyPosition[0]==-1):
            self.historyLocation.append(l.copy())
            self.historyPosition[0]=0
            return
        if(l==self.historyLocation[self.historyPosition[0]]):
            return
        #if self.historySuppression[0]:
            #self.historyPosition[0] = self.historyPosition[0] - 1
        #else:
            #self.hideLinexChoice()
        while(len(self.historyLocation)>self.historyPosition[0]+1):
            self.historyLocation.pop(self.historyPosition[0]+1)
        #self.historySuppression[0] = False
        self.historyLocation.append(l.copy())
        if(len(self.historyLocation)>self.historyDepth):
            self.historyLocation.pop(0)
        self.historyPosition[0] = len(self.historyLocation)-1
        #print (self.historyLocation)

    #def enableHistorySuppression(self):
        #self.historySuppression[0] = True

    def previousLocation(self):
        if(self.historyPosition[0]<=0):
            return
        self.historyPosition[0] = self.historyPosition[0] - 1
        CursorAccess.setCursor(self.historyLocation[self.historyPosition[0]].copy())

    def nextLocation(self):
        if(self.historyPosition[0]<0):
            return
        if(self.historyPosition[0]+1==len(self.historyLocation)):
            return
        self.historyPosition[0] = self.historyPosition[0] + 1
        CursorAccess.setCursor(self.historyLocation[self.historyPosition[0]].copy())



class VIEW3D_OT_cursor_previous(bpy.types.Operator):
    '''Previous cursor location.'''
    bl_idname = "view3d.cursor_previous"
    bl_label = "Previous cursor location."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_history
        cc.previousLocation()
        return {'FINISHED'}



class VIEW3D_OT_cursor_next(bpy.types.Operator):
    '''Next cursor location.'''
    bl_idname = "view3d.cursor_next"
    bl_label = "Next cursor location."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_history
        cc.nextLocation()
        return {'FINISHED'}



class VIEW3D_OT_cursor_history_show(bpy.types.Operator):
    '''Show cursor trace.'''
    bl_idname = "view3d.cursor_history_show"
    bl_label = "Show cursor trace."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_history
        cc.historyDraw = True
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_history_hide(bpy.types.Operator):
    '''Hide cursor trace.'''
    bl_idname = "view3d.cursor_history_hide"
    bl_label = "Hide cursor trace."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_history
        cc.historyDraw = False
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_PT_cursor_history(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Cursor History"
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
        cc = context.scene.cursor_history
        if cc.historyDraw:
            GUI.drawIconButton(True, layout, 'RESTRICT_VIEW_OFF', "view3d.cursor_history_hide", False)
        else:
            GUI.drawIconButton(True, layout, 'RESTRICT_VIEW_ON' , "view3d.cursor_history_show", False)

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        cc = context.scene.cursor_history

        row = layout.row()
        row.label("Navigation: ")
        GUI.drawIconButton(cc.historyPosition[0]>0, row, 'PLAY_REVERSE', "view3d.cursor_previous")
        #if(cc.historyPosition[0]<0):
            #row.label("  --  ")
        #else:
            #row.label("  "+str(cc.historyPosition[0])+"  ")
        GUI.drawIconButton(cc.historyPosition[0]<len(cc.historyLocation)-1, row, 'PLAY', "view3d.cursor_next")

        row = layout.row()
        col = row.column()
        col.prop(CursorAccess.findSpace(), "cursor_location")

        cc.addHistoryLocation(CursorAccess.getCursor())
  
                

class VIEW3D_PT_cursor_history_init(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Register callback"
    bl_default_closed = True

    initDone = False

    @classmethod
    def poll(cls, context):
        if VIEW3D_PT_cursor_history_init.initDone:
            return 0
        print ("Cursor History draw-callback registration...")
        sce = context.scene
        if context.area.type == 'VIEW_3D':
            for reg in context.area.regions:
                if reg.type == 'WINDOW':
                    # Register callback for SL-draw
                    reg.callback_add(
                        cursor_history_draw,
                        (cls,context),
                        'POST_PIXEL')
                    VIEW3D_PT_cursor_history_init.initDone = True
                    print ("Cursor History draw-callback registered")
                    # Unregister to prevent double registration...
                    # Started to fail after v2.57
                    # bpy.types.unregister(VIEW3D_PT_cursor_history_init)
        else:
            print("View3D not found, cannot run operator")
        return 0

    def draw_header(self, context):
        pass

    def draw(self, context):
        pass



def cursor_history_draw(cls,context):
    cc = context.scene.cursor_history

    draw = 0
    if hasattr(cc, "historyDraw"):
        draw = cc.historyDraw

    if(draw):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glShadeModel(bgl.GL_FLAT)
        alpha = 1-PHI_INV
        # History Trace
        if cc.historyPosition[0]<0:
            return
        bgl.glBegin(bgl.GL_LINE_STRIP)
        ccc = 0
        for iii in range(cc.historyWindow+1):
            ix_rel = iii - int(cc.historyWindow / 2)
            ix = cc.historyPosition[0] + ix_rel
            if(ix<0 or ix>=len(cc.historyLocation)):
                continue
            ppp = region3d_get_2d_coordinates(context, cc.historyLocation[ix])
            if(ix_rel<=0):
                bgl.glColor4f(0, 0, 0, alpha)
            else:
                bgl.glColor4f(1, 0, 0, alpha)
            bgl.glVertex2f(ppp[0], ppp[1])
            ccc = ccc + 1
        bgl.glEnd()



def register():
    bpy.utils.register_module(__name__)
    # Register Cursor Control Structure
    bpy.types.Scene.cursor_history = bpy.props.PointerProperty(type=CursorHistoryData, name="")
        

def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
