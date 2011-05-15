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
    'name': 'Cursor Control',
    'author': 'Morgan Mörtsell (Seminumerical)',
    'version': (0, 6, 0),
    'blender': (2, 5, 7),
    'api': 36147,
    'location': 'View3D > Properties > Cursor',
    'description': 'Control the Cursor',
    'warning': '', # used for warning icon and text in addons panel
    'wiki_url': 'http://blenderpythonscripts.wordpress.com/',
    'tracker_url': '',
    'category': '3D View'}



"""
  TODO:

      IDEAS:
          More saved locations... add, remove, lock, caption

      LATER:
          Blender SVN upload...

      ISSUES:
          Bugs:
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
  2011-04-23 - Adaptations for the 2.57 API
                  Matrix.invert() now mutates 'self'
                  Vector.normalize() now mutates 'self'
  2011-04-21 - Adaptations for the 2.57 API
                  Updated registration procedures
                  Forced to change some identifiers to all lower case
               Removed some old code interferring with Cursor History
--- pre 0.5.0 -----------------------------------------------------------------------------------
  2011-01-29 - Refactoring: Cursor Memory extracted to separate source.
               Refactoring: Cursor History extracted to separate source.
               Added menu under Mesh->Snap
               Bugfix: move to and mirror around saved location works again.
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
from geometry_utils import *



PRECISION = 4



class CursorControlData(bpy.types.PropertyGroup):
    # Step length properties
    stepLengthEnable = bpy.props.BoolProperty(name="Use step length",description="Use step length",default=0)
    stepLengthMode = bpy.props.EnumProperty(items=[
        ("Mode", "Mode", "Mode"),
        ("Absolute", "Absolute", "Absolute"),
        ("Proportional", "Proportional", "Proportional")],
        default="Proportional")
    stepLengthValue = bpy.props.FloatProperty(name="",precision=PRECISION,default=PHI)
    # Property for linex result select...
    linexChoice = bpy.props.IntProperty(name="",default=-1)

    def hideLinexChoice(self):
        self.linexChoice = -1

    def cycleLinexCoice(self,limit):
        qc = self.linexChoice + 1
        if qc<0:
            qc = 1
        if qc>=limit:
            qc = 0
        self.linexChoice = qc
  
    def setCursor(self,v):
        if self.stepLengthEnable:
            c = CursorAccess.getCursor()
            if((Vector(c)-Vector(v)).length>0):
                if self.stepLengthMode=='Absolute':
                    v = Vector(v)-Vector(c)
                    v.normalize()
                    v = v*self.stepLengthValue + Vector(c)
                if self.stepLengthMode=='Proportional':
                    v = (Vector(v)-Vector(c))*self.stepLengthValue + Vector(c)
        CursorAccess.setCursor(Vector(v))
        
    def guiStates(self,context):
        tvs = 0
        tes = 0
        tfs = 0
        edit_mode = False
        obj = context.active_object
        if (context.mode == 'EDIT_MESH'):
            if (obj and obj.type=='MESH' and obj.data):
                tvs = obj.data.total_vert_sel

                tes = obj.data.total_edge_sel
                tfs = obj.data.total_face_sel
                edit_mode = True
        return (tvs, tes, tfs, edit_mode)



class VIEW3D_OT_cursor_to_origin(bpy.types.Operator):
    '''Move to world origin.'''
    bl_idname = "view3d.cursor_to_origin"
    bl_label = "Move to world origin."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        cc.setCursor([0,0,0])
        return {'FINISHED'}



class VIEW3D_OT_cursor_to_active_object_center(bpy.types.Operator):
    '''Move to active object origin.'''
    bl_idname = "view3d.cursor_to_active_object_center"
    bl_label = "Move to active object origin."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        cc.setCursor(context.active_object.location)
        return {'FINISHED'}



#class VIEW3D_OT_cursor_to_nearest_object(bpy.types.Operator):
    #'''Move to center of nearest object.'''
    #bl_idname = "view3d.cursor_to_nearest_object"
    #bl_label = "Move to center of nearest object."
    #bl_options = {'REGISTER'}

    #def modal(self, context, event):
        #return {'FINISHED'}

    #def execute(self, context):
        #cc.setCursor(context.active_object.location)
        #return {'FINISHED'}



#class VIEW3D_OT_cursor_to_selection_midpoint(bpy.types.Operator):
    #'''Move to active objects median.'''
    #bl_idname = "view3d.cursor_to_selection_midpoint"
    #bl_label = "Move to active objects median."
    #bl_options = {'REGISTER'}

    #def modal(self, context, event):
        #return {'FINISHED'}

    #def execute(self, context):
        #location = Vector((0,0,0))
        #n = 0
        #for obj in context.selected_objects:
            #location = location + obj.location
            #n += 1
        #if (n==0):
            #return {'CANCELLED'}
        #location = location / n
        #cc.setCursor(location)
        #return {'FINISHED'}



class VIEW3D_OT_cursor_to_sl(bpy.types.Operator):
    '''Move to saved location.'''
    bl_idname = "view3d.cursor_to_sl"
    bl_label = "Move to saved location."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        if hasattr(context.scene, "cursor_memory"):
            cm = context.scene.cursor_memory
            cc.hideLinexChoice()
            cc.setCursor(cm.savedLocation)
        return {'FINISHED'}



class VIEW3D_OT_cursor_to_sl_mirror(bpy.types.Operator):
    '''Mirror cursor around SL or selection.'''
    bl_idname = "view3d.cursor_to_sl_mirror"
    bl_label = "Mirror cursor around SL or selection."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def mirror(self, cc, p):
        v = p - Vector(CursorAccess.getCursor())
        cc.setCursor(p + v)

    def execute(self, context):
        BlenderFake.forceUpdate()
        obj = context.active_object
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        
        if obj==None or obj.data.total_vert_sel==0:
            if hasattr(context.scene, "cursor_memory"):
                cm = context.scene.cursor_memory
                self.mirror(cc, Vector(cm.savedLocation))
            return {'FINISHED'}

        mat = obj.matrix_world

        if obj.data.total_vert_sel==1:
            sf = [f for f in obj.data.vertices if f.select == 1]
            self.mirror(cc, Vector(sf[0].co)*mat)
            return {'FINISHED'}

        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati

        if obj.data.total_vert_sel==2:
            sf = [f for f in obj.data.vertices if f.select == 1]
            p = G3.closestP2L(c, Vector(sf[0].co), Vector(sf[1].co))
            self.mirror(cc, p*mat)
            return {'FINISHED'}
            
        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();            
            p = G3.closestP2S(c, v0, normal)
            self.mirror(cc, p*mat)
            return {'FINISHED'}
              
        if obj.data.total_face_sel==1:
            sf = [f for f in obj.data.faces if f.select == 1]
            v0 = Vector(obj.data.vertices[sf[0].vertices[0]].co)
            v1 = Vector(obj.data.vertices[sf[0].vertices[1]].co)
            v2 = Vector(obj.data.vertices[sf[0].vertices[2]].co)
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();            
            p = G3.closestP2S(c, v0, normal)
            self.mirror(cc, p*mat)
            return {'FINISHED'}

        return {'CANCELLED'}


class VIEW3D_OT_cursor_to_vertex(bpy.types.Operator):
    '''Move to closest vertex.'''
    bl_idname = "view3d.cursor_to_vertex"
    bl_label = "Move to closest vertex."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = context.active_object
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        vs = obj.data.vertices
        c = Vector(CursorAccess.getCursor())*mati
        v = None
        d = -1
        for vv in vs:
            if not vv.select:
                continue
            w = Vector(vv.co)
            dd = G3.distanceP2P(c, w)
            if d<0 or dd<d:
                v = w
                d = dd
        if v==None:
            return
        cc.setCursor(v*mat)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_line(bpy.types.Operator):
    '''Move to closest point on line.'''
    bl_idname = "view3d.cursor_to_line"
    bl_label = "Move to closest point on line."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mat = obj.matrix_world
        if obj.data.total_vert_sel==2:
            sf = [f for f in obj.data.vertices if f.select == 1]
            p = CursorAccess.getCursor()
            v0 = sf[0].co*mat
            v1 = sf[1].co*mat
            q = G3.closestP2L(p, v0, v1)
            cc.setCursor(q)
            return {'FINISHED'}
        if obj.data.total_edge_sel<2:
            return {'CANCELLED'}
        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati
        q = None
        d = -1
        for ee in obj.data.edges:
            if not ee.select:
                continue
            e1 = Vector(obj.data.vertices[ee.vertices[0]].co)
            e2 = Vector(obj.data.vertices[ee.vertices[1]].co)
            qq = G3.closestP2L(c, e1, e2)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}
        cc.setCursor(q*mat)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_edge(bpy.types.Operator):
    '''Move to closest point on edge.'''
    bl_idname = "view3d.cursor_to_edge"
    bl_label = "Move to closest point on edge."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mat = obj.matrix_world
        if obj.data.total_vert_sel==2:
            sf = [f for f in obj.data.vertices if f.select == 1]
            p = CursorAccess.getCursor()
            v0 = sf[0].co*mat
            v1 = sf[1].co*mat
            q = G3.closestP2E(p, v0, v1)
            cc.setCursor(q)
            return {'FINISHED'}
        if obj.data.total_edge_sel<2:
            return {'CANCELLED'}
        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati
        q = None
        d = -1
        for ee in obj.data.edges:
            if not ee.select:
                continue
            e1 = Vector(obj.data.vertices[ee.vertices[0]].co)
            e2 = Vector(obj.data.vertices[ee.vertices[1]].co)
            qq = G3.closestP2E(c, e1, e2)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}
        cc.setCursor(q*mat)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_plane(bpy.types.Operator):
    '''Move to closest point on a plane.'''
    bl_idname = "view3d.cursor_to_plane"
    bl_label = "Move to closest point on a plane"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();
            p = CursorAccess.getCursor()
            n = normal*mat-obj.location
            v = v0*mat
            k = - (p-v).dot(n) / n.dot(n)
            q = p+n*k
            cc.setCursor(q)
            return {'FINISHED'}

        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati
        q = None
        d = -1
        for ff in obj.data.faces:
            if not ff.select:
                continue
            qq = G3.closestP2S(c, Vector(obj.data.vertices[ff.vertices[0]].co), ff.normal)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}
        cc.setCursor(q*mat)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_face(bpy.types.Operator):
    '''Move to closest point on a face.'''
    bl_idname = "view3d.cursor_to_face"
    bl_label = "Move to closest point on a face"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati
        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            fv = [v0, v1, v2]
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();
            q = G3.closestP2F(c, fv, normal)
            cc.setCursor(q*mat)
            return {'FINISHED'}

        #visual = True

        qqq = []
        q = None
        d = -1
        for ff in obj.data.faces:
            if not ff.select:
                continue
            fv=[]
            for vi in ff.vertices:
                fv.append(Vector(obj.data.vertices[vi].co))
            qq = G3.closestP2F(c, fv, ff.normal)
            #if visual:
                #qqq.append(qq)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}

        #if visual:
            #ci = MeshEditor.addVertex(c)
            #for qq in qqq:
                #qqi = MeshEditor.addVertex(qq)
                #MeshEditor.addEdge(ci, qqi)

        cc.setCursor(q*mat)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_vertex_median(bpy.types.Operator):
    '''Move to median of vertices.'''
    bl_idname = "view3d.cursor_to_vertex_median"
    bl_label = "Move to median of vertices."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = context.active_object
        mat = obj.matrix_world
        vs = obj.data.vertices
        selv = [v for v in vs if v.select == 1]
        location = Vector((0,0,0))
        for v in selv:
            location = location + v.co
        n = len(selv)
        if (n==0):
            return {'CANCELLED'}
        location = location / n
        cc.setCursor(location*mat)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_linex(bpy.types.Operator):
    '''Alternate between closest encounter points of two lines.'''
    bl_idname = "view3d.cursor_to_linex"
    bl_label = "Alternate between to closest encounter points of two lines."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        obj = bpy.context.active_object
        mat = obj.matrix_world

        se = [e for e in obj.data.edges if (e.select == 1)]
        e1v1 = obj.data.vertices[se[0].vertices[0]].co
        e1v2 = obj.data.vertices[se[0].vertices[1]].co
        e2v1 = obj.data.vertices[se[1].vertices[0]].co
        e2v2 = obj.data.vertices[se[1].vertices[1]].co

        qq = geometry.intersect_line_line (e1v1, e1v2, e2v1, e2v2)

        q = None
        if len(qq)==0:
            #print ("lx 0")
            return {'CANCELLED'}

        if len(qq)==1:
            #print ("lx 1")
            q = qq[0]
        
        if len(qq)==2:
            cc = context.scene.cursor_control
            cc.cycleLinexCoice(2)
            q = qq[cc.linexChoice]

        #q = geometry.intersect_line_line (e1v1, e1v2, e2v1, e2v2)[qc] * mat
        #i2 = geometry.intersect_line_line (e2v1, e2v2, e1v1, e1v2)[0] * mat
        cc.setCursor(q*mat)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_cylinderaxis(bpy.types.Operator):
    '''Move to closest point on cylinder axis.'''
    bl_idname = "view3d.cursor_to_cylinderaxis"
    bl_label = "Move to closest point on cylinder axis."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati

        sf = [f for f in obj.data.vertices if f.select == 1]
        v0 = Vector(sf[0].co)
        v1 = Vector(sf[1].co)
        v2 = Vector(sf[2].co)
        fv = [v0, v1, v2]
        q = G3.closestP2CylinderAxis(c, fv)
        if(q==None):
            return {'CANCELLED'}
        cc.setCursor(q*mat)
        return {'FINISHED'}     


class VIEW3D_OT_cursor_to_spherecenter(bpy.types.Operator):
    '''Move to center of cylinder or sphere.'''
    bl_idname = "view3d.cursor_to_spherecenter"
    bl_label = "Move to center of cylinder or sphere."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati

        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            fv = [v0, v1, v2]
            q = G3.closestP2CylinderAxis(c, fv)
            #q = G3.centerOfSphere(fv)
            if(q==None):
                return {'CANCELLED'}
            cc.setCursor(q*mat)
            return {'FINISHED'}
        if obj.data.total_vert_sel==4:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            v3 = Vector(sf[3].co)
            fv = [v0, v1, v2, v3]
            q = G3.centerOfSphere(fv)
            if(q==None):
                return {'CANCELLED'}
            cc.setCursor(q*mat)
            return {'FINISHED'}
        return {'CANCELLED'}



class VIEW3D_OT_cursor_to_perimeter(bpy.types.Operator):
    '''Move to perimeter of cylinder or sphere.'''
    bl_idname = "view3d.cursor_to_perimeter"
    bl_label = "Move to perimeter of cylinder or sphere."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati

        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            fv = [v0, v1, v2]
            q = G3.closestP2Cylinder(c, fv)
            if(q==None):
                return {'CANCELLED'}
            #q = G3.centerOfSphere(fv)
            cc.setCursor(q*mat)
            return {'FINISHED'}
        if obj.data.total_vert_sel==4:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            v3 = Vector(sf[3].co)
            fv = [v0, v1, v2, v3]
            q = G3.closestP2Sphere(c, fv)
            if(q==None):
                return {'CANCELLED'}
            cc.setCursor(q*mat)
            return {'FINISHED'}
        return {'CANCELLED'}



#class VIEW3D_OT_cursor_offset_from_radius(bpy.types.Operator):
    #'''Calculate offset from radius.'''
    #bl_idname = "view3d.cursor_offset_from_radius"
    #bl_label = "Calculate offset from radius."
    #bl_options = {'REGISTER'}

    #def modal(self, context, event):
        #return {'FINISHED'}

    #def execute(self, context):
        #BlenderFake.forceUpdate()
        #cc = context.scene.cursor_control
        #cc.hideLinexChoice()
        #obj = bpy.context.active_object
        #mesh = obj.data.vertices
        #mat = obj.matrix_world
        #mati = mat.copy()
        #mati.invert()
        #c = Vector(CursorAccess.getCursor())*mati

        #if obj.data.total_vert_sel==3:
            #sf = [f for f in obj.data.vertices if f.select == 1]
            #v0 = Vector(sf[0].co)
            #v1 = Vector(sf[1].co)
            #v2 = Vector(sf[2].co)
            #fv = [v0, v1, v2]
            #q = G3.centerOfSphere(fv)
            #d = (v0-q).length
            #cc.stepLengthValue = d
            #return {'FINISHED'}
        #if obj.data.total_vert_sel==4:
            #sf = [f for f in obj.data.vertices if f.select == 1]
            #v0 = Vector(sf[0].co)
            #v1 = Vector(sf[1].co)
            #v2 = Vector(sf[2].co)
            #v3 = Vector(sf[3].co)
            #fv = [v0, v1, v2, v3]
            #q = G3.centerOfSphere(fv)
            #d = (v0-q).length
            #cc.stepLengthValue = d
            #return {'FINISHED'}
        #return {'CANCELLED'}



class VIEW3D_OT_cursor_stepval_phinv(bpy.types.Operator):
    '''Set step value to 1/Phi.'''
    bl_idname = "view3d.cursor_stepval_phinv"
    bl_label = "Set step value to 1/Phi."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.stepLengthValue = PHI_INV
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_stepval_phi(bpy.types.Operator):
    '''Set step value to Phi.'''
    bl_idname = "view3d.cursor_stepval_phi"
    bl_label = "Set step value to Phi."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.stepLengthValue = PHI
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_stepval_phi2(bpy.types.Operator):
    '''Set step value to Phi².'''
    bl_idname = "view3d.cursor_stepval_phi2"
    bl_label = "Set step value to Phi²."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.stepLengthValue = PHI_SQ
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_stepval_vvdist(bpy.types.Operator):
    '''Set step value to distance vertex-vertex.'''
    bl_idname = "view3d.cursor_stepval_vvdist"
    bl_label = "Set step value to distance vertex-vertex."
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = Vector(CursorAccess.getCursor())*mati

        sf = [f for f in obj.data.vertices if f.select == 1]
        v0 = Vector(sf[0].co)
        v1 = Vector(sf[1].co)
        q = (v0-v1).length
        cc.stepLengthValue = q

        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_PT_cursor(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Cursor Control"
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
        pass
 
    def draw(self, context):
        layout = self.layout
        sce = context.scene

        cc = context.scene.cursor_control
        (tvs,tes,tfs,edit_mode) = cc.guiStates(context)

        # Mesh data elements
        if(edit_mode):
            row = layout.row()
            GUI.drawIconButton(tvs>=1          , row, 'STICKY_UVS_DISABLE', "view3d.cursor_to_vertex")
            GUI.drawIconButton(tvs==2 or tes>=1, row, 'MESH_DATA'         , "view3d.cursor_to_line")
            GUI.drawIconButton(tvs==2 or tes>=1, row, 'OUTLINER_OB_MESH'  , "view3d.cursor_to_edge")
            GUI.drawIconButton(tvs==3 or tfs>=1, row, 'SNAP_FACE'         , "view3d.cursor_to_plane")
            GUI.drawIconButton(tvs==3 or tfs>=1, row, 'FACESEL'           , "view3d.cursor_to_face")

        # Geometry from mesh
        if(edit_mode):
            row = layout.row()
            GUI.drawIconButton(tvs<=3 or tfs==1 , row, 'MOD_MIRROR'  , "view3d.cursor_to_sl_mirror")
            GUI.drawIconButton(tes==2, row, 'PARTICLE_TIP', "view3d.cursor_to_linex")
            GUI.drawIconButton(tvs>1 , row, 'ROTATECENTER', "view3d.cursor_to_vertex_median")  #EDITMODE_HLT
            GUI.drawIconButton(tvs==3 or tvs==4, row, 'FORCE_FORCE'  , "view3d.cursor_to_spherecenter")
            GUI.drawIconButton(tvs==3 or tvs==4, row, 'MATERIAL'  , "view3d.cursor_to_perimeter")

        # Objects
        #row = layout.row()

        #GUI.drawIconButton(context.active_object!=None    , row, 'ROTATE'          , "view3d.cursor_to_active_object_center")
        #GUI.drawIconButton(len(context.selected_objects)>1, row, 'ROTATECOLLECTION', "view3d.cursor_to_selection_midpoint")
        #GUI.drawIconButton(len(context.selected_objects)>1, row, 'ROTATECENTER'    , "view3d.cursor_to_selection_midpoint")

        # References World Origin, Object Origin, SL and CL
        row = layout.row()
        GUI.drawIconButton(True                       , row, 'WORLD_DATA'    , "view3d.cursor_to_origin")
        GUI.drawIconButton(context.active_object!=None, row, 'ROTACTIVE'       , "view3d.cursor_to_active_object_center")
        GUI.drawIconButton(True                       , row, 'CURSOR'        , "view3d.cursor_to_sl")
        #GUI.drawIconButton(True, row, 'GRID'          , "view3d.cursor_sl_recall")
        #GUI.drawIconButton(True, row, 'SNAP_INCREMENT', "view3d.cursor_sl_recall")
        #row.label("("+str(cc.linexChoice)+")")
        cc = context.scene.cursor_control
        if cc.linexChoice>=0:
            col = row.column()
            col.enabled = False
            col.prop(cc, "linexChoice")

        # Limit/Clamping Properties
        row = layout.row()
        row.prop(cc, "stepLengthEnable")
        if (cc.stepLengthEnable):
            row = layout.row()
            row.prop(cc, "stepLengthMode")
            row.prop(cc, "stepLengthValue")
            row = layout.row()
            GUI.drawTextButton(True, row, '1/Phi'      , "view3d.cursor_stepval_phinv")
            GUI.drawTextButton(True, row, 'Phi'      , "view3d.cursor_stepval_phi")
            GUI.drawTextButton(True, row, 'Phi²'      , "view3d.cursor_stepval_phi2")
            GUI.drawIconButton(tvs==2, row, 'EDGESEL'      , "view3d.cursor_stepval_vvdist")


  
class CursorControlMenu(bpy.types.Menu):
    """menu"""
    bl_idname = "cursor_control_calls"
    bl_label = "Cursor Control"
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        #layout.operator(VIEW3D_OT_cursor_to_vertex.bl_idname, text = "Vertex")
        #layout.operator(VIEW3D_OT_cursor_to_line.bl_idname, text = "Line")
        #obj = context.active_object
        #if (context.mode == 'EDIT_MESH'):
            #if (obj and obj.type=='MESH' and obj.data):
        cc = context.scene.cursor_control
        (tvs,tes,tfs,edit_mode) = cc.guiStates(context)
        
        if(edit_mode):
            if(tvs>=1):
                layout.operator(VIEW3D_OT_cursor_to_vertex.bl_idname, text = "Closest Vertex")
            if(tvs==2 or tes>=1):
                layout.operator(VIEW3D_OT_cursor_to_line.bl_idname, text = "Closest Line")
            if(tvs==2 or tes>=1):
                layout.operator(VIEW3D_OT_cursor_to_edge.bl_idname, text = "Closest Edge")
            if(tvs==3 or tfs>=1):
                layout.operator(VIEW3D_OT_cursor_to_plane.bl_idname, text = "Closest Plane")
            if(tvs==3 or tfs>=1):
                layout.operator(VIEW3D_OT_cursor_to_face.bl_idname, text = "Closest Face")

        if(edit_mode):
            if(tvs<=3 or tfs==1):
                layout.operator(VIEW3D_OT_cursor_to_sl_mirror.bl_idname, text = "Mirror")
            if(tes==2):
                layout.operator(VIEW3D_OT_cursor_to_linex.bl_idname, text = "Line Intersection")
            if(tvs>1):
                layout.operator(VIEW3D_OT_cursor_to_vertex_median.bl_idname, text = "Vertex Median")
            if(tvs==3 or tvs==4):
                layout.operator(VIEW3D_OT_cursor_to_spherecenter.bl_idname, text = "Circle Center")
            if(tvs==3 or tvs==4):
                layout.operator(VIEW3D_OT_cursor_to_perimeter.bl_idname, text = "Circle Perimeter")
        
        layout.operator(VIEW3D_OT_cursor_to_origin.bl_idname, text = "World Origin")
        layout.operator(VIEW3D_OT_cursor_to_active_object_center.bl_idname, text = "Active Object")
        layout.operator(VIEW3D_OT_cursor_to_sl.bl_idname, text = "Cursor Memory")



def menu_callback(self, context):
    #obj = context.active_object
    #if (context.mode == 'EDIT_MESH'):
        #if (obj and obj.type=='MESH' and obj.data):
    self.layout.menu(CursorControlMenu.bl_idname, icon="PLUGIN")

def register():
    bpy.utils.register_module(__name__)
    # Register Cursor Control Structure
    bpy.types.Scene.cursor_control = bpy.props.PointerProperty(type=CursorControlData, name="")
    # Register menu
    bpy.types.VIEW3D_MT_snap.append(menu_callback)

def unregister():
    # Register menu
    bpy.types.VIEW3D_MT_snap.remove(menu_callback)
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
