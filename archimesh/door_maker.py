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

#----------------------------------------------------------
# File: door_maker.py
# Automatic generation of doors
# Author: Antonio Vazquez (antonioya)
#
#----------------------------------------------------------
import bpy
import math
from tools import *


#------------------------------------------------------------------
# Define UI class
# Doors
#------------------------------------------------------------------
class DOOR(bpy.types.Operator):
    bl_idname = "mesh.archimesh_door"
    bl_label = "Door"
    bl_description = "Door Generator"
    bl_category = 'Archimesh'
    bl_options = {'REGISTER', 'UNDO'}
    
    # Define properties
    frame_width= bpy.props.FloatProperty(name='Frame width',min=0.25,max= 10, default= 1,precision=2, description='Doorframe width')
    frame_height= bpy.props.FloatProperty(name='Frame height',min=0.25,max= 10, default= 2.1,precision=2, description='Doorframe height')
    frame_thick= bpy.props.FloatProperty(name='Frame thickness',min=0.05,max= 0.50, default= 0.08,precision=2, description='Doorframe thickness')
    frame_size= bpy.props.FloatProperty(name='Frame size',min=0.05,max= 0.25, default= 0.08,precision=2, description='Doorframe size')
    crt_mat = bpy.props.BoolProperty(name = "Create default Cycles materials",description="Create default materials for Cycles render.",default = True)
    factor= bpy.props.FloatProperty(name='',min=0.2,max= 1, default= 0.5,precision=3, description='Door ratio')

    openside = bpy.props.EnumProperty(items = (('1',"Right open",""),
                                ('2',"Left open",""),
                                ('3',"Both sides","")),
                                name="Open side",
                                description="Defines the direction for opening the door")

    model = bpy.props.EnumProperty(items = (('1',"Model 01",""),
                                ('2',"Model 02",""),
                                ('3',"Model 03",""),
                                ('4',"Model 04",""),
                                ('5',"Model 05","Glass"),
                                ('6',"Model 06","Glass")),
                                name="Model",
                                description="Door model")
    
    handle = bpy.props.EnumProperty(items = (('1',"Handle 01",""),
                                ('2',"Handle 02",""),
                                ('3',"Handle 03",""),
                                ('4',"Handle 04",""),
                                ('0',"None","")),
                                name="Handle",
                                description="Handle model")
    
    #-----------------------------------------------------
    # Draw (create UI interface)
    #-----------------------------------------------------
    def draw(self, context):
        layout = self.layout
        space = bpy.context.space_data
        if (not space.local_view):
            # Imperial units warning
            if (bpy.context.scene.unit_settings.system == "IMPERIAL"):
                row=layout.row()
                row.label("Warning: Imperial units not supported", icon='COLOR_RED')
            box=layout.box()
            row=box.row()
            row.prop(self,'frame_width')
            row.prop(self,'frame_height')
            row=box.row()
            row.prop(self,'frame_thick')
            row.prop(self,'frame_size')
            
            box=layout.box()
            row=box.row()
            row.prop(self,'openside')
            if (self.openside == "3"):
                row.prop(self,"factor")
                
            layout.prop(self,'model')
            layout.prop(self,'handle')
            
            box=layout.box()
            box.prop(self,'crt_mat')
        else:
            row=layout.row()
            row.label("Warning: Operator does not work in local view mode", icon='ERROR')
        
    #-----------------------------------------------------
    # Execute
    #-----------------------------------------------------
    def execute(self, context):
        if (bpy.context.mode == "OBJECT"):
            myFrame = create_door_mesh(self,context)
            #-------------------------
            # Create empty and parent
            #-------------------------
            bpy.ops.object.empty_add(type='PLAIN_AXES')
            myEmpty = bpy.data.objects[bpy.context.active_object.name]
            myEmpty.location = bpy.context.scene.cursor_location
            myEmpty.name = "Door_Group"
            myFrame.location = (0,0,0)
            myFrame.parent = myEmpty 
            myFrame["archimesh.hole_enable"] = True
            # Create control box to open wall holes
            gap = 0.002
            myCtrl = create_control_box("CTRL_Hole"
                               ,self.frame_width-gap,self.frame_thick,self.frame_height)
            # Add custom property to detect Controller
            myCtrl["archimesh.ctrl_hole"] = True
            
            set_normals(myCtrl)
            myCtrl.parent = myEmpty
            myCtrl.location.x = 0
            myCtrl.location.y = -self.frame_thick/3
            myCtrl.location.z = -gap
            myCtrl.draw_type = 'WIRE'
            myCtrl.hide = True
            myCtrl.hide_render = True
            
            # Create control box for baseboard
            myCtrlBase = create_control_box("CTRL_Baseboard"
                               ,self.frame_width,0.40,0.40
                               ,False)
            # Add custom property to detect Controller
            myCtrlBase["archimesh.ctrl_base"] = True
            
            set_normals(myCtrlBase)
            myCtrlBase.parent = myEmpty
            myCtrlBase.location.x = 0
            myCtrlBase.location.y = -0.15 - (self.frame_thick / 3)
            myCtrlBase.location.z = -0.10
            myCtrlBase.draw_type = 'WIRE'
            myCtrlBase.hide = True
            myCtrlBase.hide_render = True

            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}

#------------------------------------------------------------------------------
# Generate mesh data
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_door_mesh(self,context):

    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
            
    bpy.ops.object.select_all(False)

    myFrame = create_doorframe(self,context)
    
    if (self.openside != "3"):
        make_one_door(self,context, myFrame, self.frame_width, self.openside)
    else:
        w = self.frame_width
        widthL = (w * self.factor)
        widthR = w - widthL

        # left door
        myDoor = make_one_door(self,context, myFrame, widthL + self.frame_size, "2")    
        myDoor.location.x = -self.frame_width/2 + self.frame_size
        # right door (pending width)
        myDoor = make_one_door(self,context, myFrame, widthR + self.frame_size, "1")    
        myDoor.location.x = self.frame_width/2 - self.frame_size
    
    
    
    if (self.crt_mat):
        mat = create_diffuse_material("Door_material", False, 0.8, 0.8, 0.8)
        set_material(myFrame, mat)
            
    bpy.ops.object.select_all(False)    
    myFrame.select = True
    bpy.context.scene.objects.active = myFrame
    
    return myFrame
#------------------------------------------------------------------------------
# Make one door
# 
#------------------------------------------------------------------------------
def make_one_door(self,context, myFrame, width, openside):
    myDoor = create_door_data(self, context, myFrame, width, openside)
    if (self.handle != "0"):
        handle1 = create_handle(self, context, myFrame, myDoor, "Front",width,openside)
        handle1.select = True
        bpy.context.scene.objects.active = handle1
        set_smooth(handle1)
        set_modifier_subsurf(handle1)
        handle2 = create_handle(self, context, myFrame, myDoor, "Back",width,openside)
        set_smooth(handle2)
        set_modifier_subsurf(handle2)
# Create materials
    if (self.crt_mat):
        # Door material
        mat = create_diffuse_material("Door_material", False, 0.8, 0.8, 0.8)
        set_material(myDoor, mat)
        # Handle material
        if (self.handle != "0"):
            mat = create_glossy_material("Handle_material", False, 0.733, 0.779, 0.8)
            set_material(handle1, mat)
            set_material(handle2, mat)
        if (self.model == "5" or self.model == "6"):
            mat = create_glass_material("DoorGlass_material", False)
            myDoor.data.materials.append(mat)
            if (self.model == "5"):
                select_faces(myDoor, 20, True)
                select_faces(myDoor, 41, False)
            if (self.model == "6"):
                select_faces(myDoor, 37, True)
                select_faces(myDoor, 76, False)
            set_material_faces(myDoor, 1)
            
    return myDoor

#------------------------------------------------------------------------------
# Create Doorframe
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_doorframe(self,context):
    tf = self.frame_thick/3
    sf = self.frame_size
    wf = (self.frame_width/2) - sf
    hf = self.frame_height - sf
    gap = 0.02
    deep = self.frame_thick * 0.50

    
    verts = [(-wf - sf   , -tf        , 0),
            (-wf - sf    , tf * 2     , 0),
            (-wf         , tf * 2     , 0),
            (-wf - sf    , -tf        , hf + sf),
            (-wf - sf    , tf * 2     , hf + sf),
            (wf + sf     , tf * 2     , hf + sf),
            (wf + sf     , -tf        , hf + sf),
            (wf          , -tf        , hf),
            (-wf         , tf * 2     , hf),
            (wf          , -tf        , 0),
            (wf + sf     , -tf        , 0),
            (wf + sf     , tf * 2     , 0),
            (wf          , -tf + deep , hf),
            (-wf         , -tf + deep , hf),
            (-wf         , -tf + deep , 0),
            (-wf + gap   , -tf + deep , hf),
            (-wf + gap   , -tf + deep , 0),
            (-wf + gap   , tf * 2     , hf),
            (-wf + gap   , tf * 2     , 0),
            (wf          , -tf + deep , 0),
            (-wf         , -tf        , hf),
            (-wf         , -tf        , 0),
            (wf          , tf * 2     , hf),
            (wf          , tf * 2     , 0),
            (wf - gap    , tf * 2     , 0),
            (wf - gap    , -tf + deep , 0),
            (wf - gap    , tf * 2     , hf),
            (wf - gap    , -tf + deep , hf - gap),
            (wf - gap    , -tf + deep , hf),
            (-wf + gap   , tf * 2     , hf - gap),
            (-wf + gap   , -tf + deep , hf - gap),
            (wf - gap    , tf * 2     , hf - gap)]

    faces = [(3, 4, 1, 0), (7, 12, 19, 9), (4, 3, 6, 5), (10, 11, 5, 6), (13, 20, 21, 14), (17, 15, 16, 18), (11, 23, 22, 5),
            (20, 13, 12, 7), (20, 3, 0, 21), (9, 10, 6, 7), (13, 14, 16, 15), (4, 8, 2, 1), (29, 30, 27, 31), (7, 6, 3, 20),
            (8, 4, 5, 22), (14, 2, 18, 16), (17, 18, 2, 8), (28, 25, 19, 12), (28, 26, 24, 25), (25, 24, 23, 19), (22, 23, 24, 26),
            (29, 31, 26, 17), (15, 28, 27, 30), (8, 22, 26)]
    
    mymesh = bpy.data.meshes.new("Doorframe")
    myobject = bpy.data.objects.new("Doorframe", mymesh)
    
    myobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myobject)
    
    mymesh.from_pydata(verts, [], faces)
    mymesh.update(calc_edges=True)
    
    return myobject

#------------------------------------------------------------------------------
# Create Door
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_door_data(self,context,myFrame,width,openside):
    
    # Retry mesh data
    if (self.model == "1"):
        myData = door_model_01(self.frame_size,width,self.frame_height,self.frame_thick,openside)
    elif (self.model == "2"):
        myData = door_model_02(self.frame_size,width,self.frame_height,self.frame_thick,openside)
    elif (self.model == "3"):
        myData = door_model_03(self.frame_size,width,self.frame_height,self.frame_thick,openside)
    elif (self.model == "4"):
        myData = door_model_04(self.frame_size,width,self.frame_height,self.frame_thick,openside)
    elif (self.model == "5"):
        myData = door_model_04(self.frame_size,width,self.frame_height,self.frame_thick,openside) # uses the same mesh
    elif (self.model == "6"):
        myData = door_model_02(self.frame_size,width,self.frame_height,self.frame_thick,openside) # uses the same mesh
    else:    
        myData = door_model_01(self.frame_size,width,self.frame_height,self.frame_thick,openside) # default model
        
    # move data
    verts = myData[0]
    faces = myData[1]
    wf = myData[2]
    deep = myData[3]
    side = myData[4]
    
    mymesh = bpy.data.meshes.new("Door")
    myobject = bpy.data.objects.new("Door", mymesh)
    
    myobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myobject)
    
    mymesh.from_pydata(verts, [], faces)
    mymesh.update(calc_edges=True)
    
    # Translate to doorframe and parent
    myobject.parent = myFrame
    myobject.lock_rotation = (True, True, False)
    
    myobject.location.x = ((wf / 2) * side)
    myobject.location.y = -(deep * 0.65)
    myobject.location.z = self.frame_height / 2
    
    return myobject
#------------------------------------------------------------------------------
# Create Handles
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_handle(self,context,myFrame,myDoor,pos,frame_width,openside):
    # Retry mesh data
    if (self.handle == "1"):
        myData = handle_model_01(self,context)
    elif (self.handle == "2"):
        myData = handle_model_02(self,context)
    elif (self.handle == "3"):
        myData = handle_model_03(self,context)
    elif (self.handle == "4"):
        myData = handle_model_04(self,context)
    else:
        myData = handle_model_01(self,context) # default model

    # move data
    verts = myData[0]
    faces = myData[1]
    
    gap = 0.002
    sf = self.frame_size
    wf = frame_width - (sf * 2) - (gap * 2)
    deep = (self.frame_thick * 0.50)  - (gap * 3)    
    # Open to right or left
    if(openside == "1"):
        side = -1
    else:
        side = 1
        
    mymesh = bpy.data.meshes.new("Handle_" + pos)
    myobject = bpy.data.objects.new("Handle_" + pos, mymesh)
    
    myobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myobject)
    
    mymesh.from_pydata(verts, [], faces)
    mymesh.update(calc_edges=True)
    # Rotate if pos is front
    xrot = 0.0
    yrot = 0.0
    if (self.handle == "1"):
        if(openside != "1"):
            yrot = math.pi
    else:
        yrot = 0.0        
    
    if (pos == "Front"):
        xrot = math.pi
        
    myobject.rotation_euler = (xrot, yrot, 0.0) # radians PI=180
        
    # Translate to door and parent (depend of model of door)
    if (self.model == "1"):
        myobject.location.x = (wf * side) + (0.072 * side * -1)
        if (pos == "Front"):
            myobject.location.y = deep - 0.005
        else:
            myobject.location.y = 0.005
            
    if (self.model == "2" or self.model == "6"):
        myobject.location.x = (wf * side) + (0.060 * side * -1)
        if (pos == "Front"):
            myobject.location.y = deep - 0.011
        else:
            myobject.location.y = 0.00665
            
    if (self.model == "3"):
        myobject.location.x = (wf * side) + (0.060 * side * -1)
        if (pos == "Front"):
            myobject.location.y = deep - 0.011
        else:
            myobject.location.y = 0.00665
            
    if (self.model == "4" or self.model == "5"):
        myobject.location.x = (wf * side) + (0.060 * side * -1)
        if (pos == "Front"):
            myobject.location.y = deep - 0.011
        else:
            myobject.location.y = 0.00665
            
         
    myobject.location.z = 0
    myobject.parent = myDoor
    myobject.lock_rotation = (True, False, True)
    
    return myobject
#----------------------------------------------
# Door model 01
#----------------------------------------------
def door_model_01(frame_size,frame_width,frame_height,frame_thick,openside):
    #------------------------------------
    # Mesh data
    #------------------------------------
    gap = 0.002
    sf = frame_size
    wf = frame_width - (sf * 2) - (gap * 2)
    hf = (frame_height/2)- (gap * 2) 
    deep = (frame_thick * 0.50) - (gap * 3)
    # Open to right or left
    if(openside == "1"):
        side = 1
        minX = wf * -1
        maxX = 0.0
    else:
        side = -1
        minX = 0.0
        maxX = wf
    
    minY = 0.0 # locked
    maxY = deep
    minZ = -hf
    maxZ = hf - sf - gap
    
    # Vertex
    myVertex = [(minX,minY,minZ)
    ,(minX,maxY,minZ)
    ,(maxX,maxY,minZ)
    ,(maxX,minY,minZ)
    ,(minX,minY,maxZ)
    ,(minX,maxY,maxZ)
    ,(maxX,maxY,maxZ)
    ,(maxX,minY,maxZ)]
    
    # Faces
    myFaces = [(4, 5, 1, 0),(5, 6, 2, 1),(6, 7, 3, 2),(7, 4, 0, 3),(0, 1, 2, 3)
    ,(7, 6, 5, 4)]
        
    return (myVertex,myFaces,wf,deep,side)
  
#----------------------------------------------
# Door model 02
#----------------------------------------------
def door_model_02(frame_size,frame_width,frame_height,frame_thick,openside):
    gap = 0.002
    sf = frame_size
    wf = frame_width - (sf * 2) - (gap * 2)
    hf = (frame_height/2)- (gap * 2) 
    deep = (frame_thick * 0.50) 

    #------------------------------------
    # Mesh data
    #------------------------------------
    # Open to right or left
    if(openside == "1"):
        side = 1
        minX = wf * -1
        maxX = 0.0
    else:
        side = -1
        minX = 0.0
        maxX = wf
    
    minY = 0.0 # Locked
    
    maxY = deep
    minZ = -hf
    maxZ = hf - sf - gap 
    
    # Vertex
    myVertex = [(minX,-1.57160684466362e-08,minZ + 2.384185791015625e-06)
    ,(maxX,-1.5599653124809265e-08,minZ)
    ,(minX,-1.5599653124809265e-08,maxZ)
    ,(minX,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(minX,-1.57160684466362e-08,minZ + 0.2500007152557373)
    ,(maxX,-1.5599653124809265e-08,minZ + 0.25000011920928955)
    ,(maxX,-1.5599653124809265e-08,maxZ)
    ,(maxX,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(maxX - 0.11609852313995361,-1.5599653124809265e-08,maxZ)
    ,(maxX - 0.12357193231582642,-1.5599653124809265e-08,minZ)
    ,(maxX - 0.11658430099487305,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(maxX - 0.12263774871826172,-1.5599653124809265e-08,minZ + 0.25000011920928955)
    ,(minX,-1.57160684466362e-08,minZ + 0.8700000941753387)
    ,(maxX,-1.5599653124809265e-08,minZ + 0.8700000941753387)
    ,(maxX - 0.12076938152313232,-1.5599653124809265e-08,minZ + 0.7500001192092896)
    ,(minX + 0.11735659837722778,-1.57160684466362e-08,minZ + 0.25000011920928955)
    ,(minX + 0.12341010570526123,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(minX + 0.11642247438430786,-1.57160684466362e-08,minZ)
    ,(minX + 0.11967337131500244,-1.57160684466362e-08,minZ + 0.8700000941753387)
    ,(minX,-1.57160684466362e-08,minZ + 0.7500001192092896)
    ,(maxX - 0.12032097578048706,-1.5599653124809265e-08,minZ + 0.8700000941753387)
    ,(minX + 0.12389582395553589,-1.5599653124809265e-08,maxZ)
    ,(maxX,-1.5599653124809265e-08,minZ + 0.7500001192092896)
    ,(minX + 0.11922496557235718,-1.57160684466362e-08,minZ + 0.7500001192092896)
    ,(minX + 0.11922496557235718,-0.010000014677643776,minZ + 0.7500001192092896)
    ,(minX + 0.12341010570526123,-0.010000014677643776,maxZ - 0.12999999523162842)
    ,(maxX - 0.12032097578048706,-0.010000014677643776,minZ + 0.8700000941753387)
    ,(minX + 0.11735659837722778,-0.010000014677643776,minZ + 0.25000011920928955)
    ,(maxX - 0.11658430099487305,-0.010000014677643776,maxZ - 0.12999999523162842)
    ,(maxX - 0.12263774871826172,-0.010000014677643776,minZ + 0.25000011920928955)
    ,(minX + 0.11967337131500244,-0.010000014677643776,minZ + 0.8700000941753387)
    ,(maxX - 0.12076938152313232,-0.010000014677643776,minZ + 0.7500001192092896)
    ,(minX + 0.13388586044311523,-0.010000014677643776,minZ + 0.7375001013278961)
    ,(minX + 0.1321108341217041,-0.010000014677643776,minZ + 0.2625001072883606)
    ,(maxX - 0.1372986137866974,-0.010000014677643776,minZ + 0.2625001072883606)
    ,(maxX - 0.13552364706993103,-0.010000014677643776,minZ + 0.7375001013278961)
    ,(minX + 0.13802427053451538,-0.010000014677643776,maxZ - 0.14747536182403564)
    ,(maxX - 0.13493508100509644,-0.010000014677643776,minZ + 0.8866067305207253)
    ,(maxX - 0.13138526678085327,-0.010000014677643776,maxZ - 0.14747536182403564)
    ,(minX + 0.13447439670562744,-0.010000014677643776,minZ + 0.8866067305207253)
    ,(minX + 0.13388586044311523,-0.008776669390499592,minZ + 0.7375001013278961)
    ,(minX + 0.1321108341217041,-0.008776669390499592,minZ + 0.2625001072883606)
    ,(maxX - 0.1372986137866974,-0.008776669390499592,minZ + 0.2625001072883606)
    ,(maxX - 0.13552364706993103,-0.008776669390499592,minZ + 0.7375001013278961)
    ,(minX + 0.13802427053451538,-0.008776669390499592,maxZ - 0.14747536182403564)
    ,(maxX - 0.13493508100509644,-0.008776669390499592,minZ + 0.8866067305207253)
    ,(maxX - 0.13138526678085327,-0.008776669390499592,maxZ - 0.14747536182403564)
    ,(minX + 0.13447439670562744,-0.008776669390499592,minZ + 0.8866067305207253)
    ,(minX,maxY - 0.009999999776482582,minZ + 2.384185791015625e-06)
    ,(maxX,maxY - 0.009999999776482582,minZ)
    ,(minX,maxY - 0.009999999776482582,maxZ)
    ,(minX,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(minX,maxY - 0.009999999776482582,minZ + 0.2500007152557373)
    ,(maxX,maxY - 0.009999999776482582,minZ + 0.25000011920928955)
    ,(maxX,maxY - 0.009999999776482582,maxZ)
    ,(maxX,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(maxX - 0.11609852313995361,maxY - 0.009999999776482582,maxZ)
    ,(maxX - 0.12357193231582642,maxY - 0.009999999776482582,minZ)
    ,(maxX - 0.11658430099487305,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(maxX - 0.12263774871826172,maxY - 0.009999999776482582,minZ + 0.25000011920928955)
    ,(minX,maxY - 0.009999999776482582,minZ + 0.8700000941753387)
    ,(maxX,maxY - 0.009999999776482582,minZ + 0.8700000941753387)
    ,(maxX - 0.12076938152313232,maxY - 0.009999999776482582,minZ + 0.7500001192092896)
    ,(minX + 0.11735659837722778,maxY - 0.009999999776482582,minZ + 0.25000011920928955)
    ,(minX + 0.12341010570526123,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(minX + 0.11642247438430786,maxY - 0.009999999776482582,minZ)
    ,(minX + 0.11967337131500244,maxY - 0.009999999776482582,minZ + 0.8700000941753387)
    ,(minX,maxY - 0.009999999776482582,minZ + 0.7500001192092896)
    ,(maxX - 0.12032097578048706,maxY - 0.009999999776482582,minZ + 0.8700000941753387)
    ,(minX + 0.12389582395553589,maxY - 0.009999999776482582,maxZ)
    ,(maxX,maxY - 0.009999999776482582,minZ + 0.7500001192092896)
    ,(minX + 0.11922496557235718,maxY - 0.009999999776482582,minZ + 0.7500001192092896)
    ,(minX + 0.11922496557235718,maxY,minZ + 0.7500001192092896)
    ,(minX + 0.12341010570526123,maxY,maxZ - 0.12999999523162842)
    ,(maxX - 0.12032097578048706,maxY,minZ + 0.8700000941753387)
    ,(minX + 0.11735659837722778,maxY,minZ + 0.25000011920928955)
    ,(maxX - 0.11658430099487305,maxY,maxZ - 0.12999999523162842)
    ,(maxX - 0.12263774871826172,maxY,minZ + 0.25000011920928955)
    ,(minX + 0.11967337131500244,maxY,minZ + 0.8700000941753387)
    ,(maxX - 0.12076938152313232,maxY,minZ + 0.7500001192092896)
    ,(minX + 0.13388586044311523,maxY,minZ + 0.7375001013278961)
    ,(minX + 0.1321108341217041,maxY,minZ + 0.2625001072883606)
    ,(maxX - 0.1372986137866974,maxY,minZ + 0.2625001072883606)
    ,(maxX - 0.13552364706993103,maxY,minZ + 0.7375001013278961)
    ,(minX + 0.13802427053451538,maxY,maxZ - 0.14747536182403564)
    ,(maxX - 0.13493508100509644,maxY,minZ + 0.8866067305207253)
    ,(maxX - 0.13138526678085327,maxY,maxZ - 0.14747536182403564)
    ,(minX + 0.13447439670562744,maxY,minZ + 0.8866067305207253)
    ,(minX + 0.13388586044311523,maxY - 0.0012233443558216095,minZ + 0.7375001013278961)
    ,(minX + 0.1321108341217041,maxY - 0.0012233443558216095,minZ + 0.2625001072883606)
    ,(maxX - 0.1372986137866974,maxY - 0.0012233443558216095,minZ + 0.2625001072883606)
    ,(maxX - 0.13552364706993103,maxY - 0.0012233443558216095,minZ + 0.7375001013278961)
    ,(minX + 0.13802427053451538,maxY - 0.0012233443558216095,maxZ - 0.14747536182403564)
    ,(maxX - 0.13493508100509644,maxY - 0.0012233443558216095,minZ + 0.8866067305207253)
    ,(maxX - 0.13138526678085327,maxY - 0.0012233443558216095,maxZ - 0.14747536182403564)
    ,(minX + 0.13447439670562744,maxY - 0.0012233443558216095,minZ + 0.8866067305207253)]
    
    # Faces
    myFaces = [(15, 4, 0, 17),(21, 2, 3, 16),(23, 19, 4, 15),(6, 8, 10, 7),(8, 21, 16, 10)
    ,(16, 3, 12, 18),(11, 15, 17, 9),(20, 18, 23, 14),(18, 12, 19, 23),(5, 11, 9, 1)
    ,(22, 14, 11, 5),(7, 10, 20, 13),(13, 20, 14, 22),(20, 10, 28, 26),(10, 16, 25, 28)
    ,(16, 18, 30, 25),(18, 20, 26, 30),(15, 11, 29, 27),(14, 23, 24, 31),(23, 15, 27, 24)
    ,(11, 14, 31, 29),(31, 24, 32, 35),(24, 27, 33, 32),(27, 29, 34, 33),(29, 31, 35, 34)
    ,(26, 28, 38, 37),(30, 26, 37, 39),(28, 25, 36, 38),(25, 30, 39, 36),(33, 34, 42, 41)
    ,(36, 39, 47, 44),(34, 35, 43, 42),(37, 38, 46, 45),(32, 33, 41, 40),(38, 36, 44, 46)
    ,(35, 32, 40, 43),(39, 37, 45, 47),(18, 20, 10, 16),(14, 23, 15, 11),(63, 52, 48, 65)
    ,(69, 50, 51, 64),(71, 67, 52, 63),(54, 56, 58, 55),(56, 69, 64, 58),(64, 51, 60, 66)
    ,(59, 63, 65, 57),(68, 66, 71, 62),(66, 60, 67, 71),(53, 59, 57, 49),(70, 62, 59, 53)
    ,(55, 58, 68, 61),(61, 68, 62, 70),(68, 58, 76, 74),(58, 64, 73, 76),(64, 66, 78, 73)
    ,(66, 68, 74, 78),(63, 59, 77, 75),(62, 71, 72, 79),(71, 63, 75, 72),(59, 62, 79, 77)
    ,(79, 72, 80, 83),(72, 75, 81, 80),(75, 77, 82, 81),(77, 79, 83, 82),(74, 76, 86, 85)
    ,(78, 74, 85, 87),(76, 73, 84, 86),(73, 78, 87, 84),(81, 82, 90, 89),(84, 87, 95, 92)
    ,(82, 83, 91, 90),(85, 86, 94, 93),(80, 81, 89, 88),(86, 84, 92, 94),(83, 80, 88, 91)
    ,(87, 85, 93, 95),(66, 68, 58, 64),(62, 71, 63, 59),(50, 2, 21, 69),(8, 56, 69, 21)
    ,(6, 54, 56, 8),(54, 6, 7, 55),(55, 7, 13, 61),(61, 13, 22, 70),(5, 53, 70, 22)
    ,(1, 49, 53, 5),(49, 1, 9, 57),(57, 9, 17, 65),(0, 48, 65, 17),(48, 0, 4, 52)
    ,(52, 4, 19, 67),(12, 60, 67, 19),(3, 51, 60, 12),(2, 50, 51, 3)]
    
    
    return (myVertex,myFaces,wf,deep,side)  

#----------------------------------------------
# Door model 03
#----------------------------------------------
def door_model_03(frame_size,frame_width,frame_height,frame_thick,openside):
    gap = 0.002
    sf = frame_size
    wf = frame_width - (sf * 2) - (gap * 2)
    hf = (frame_height/2)- (gap * 2) 
    deep = (frame_thick * 0.50) 

    #------------------------------------
    # Mesh data
    #------------------------------------
    # Open to right or left
    if(openside == "1"):
        side = 1
        minX = wf * -1
        maxX = 0.0
    else:
        side = -1
        minX = 0.0
        maxX = wf
    
    minY = 0.0 # Locked
    
    maxY = deep
    minZ = -hf
    maxZ = hf - sf - gap 

    # Vertex
    myVertex = [(minX,-1.5599653124809265e-08,maxZ)
    ,(maxX,-1.5599653124809265e-08,maxZ)
    ,(minX,maxY,maxZ)
    ,(maxX,maxY,maxZ)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,maxZ)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,maxZ)
    ,(minX + 0.10429966449737549,maxY,maxZ)
    ,(minX,-1.5628756955266e-08,maxZ - 0.5012519359588623)
    ,(maxX,-1.5599653124809265e-08,maxZ - 0.5012525320053101)
    ,(minX,maxY,maxZ - 0.5012519359588623)
    ,(maxX,maxY,maxZ - 0.5012525320053101)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,maxZ - 0.501252293586731)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,maxZ - 0.5012521147727966)
    ,(minX + 0.10429966449737549,maxY,maxZ - 0.5012521147727966)
    ,(maxX - 0.10429960489273071,maxY,maxZ - 0.501252293586731)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,maxZ)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,maxZ)
    ,(minX + 0.11909735202789307,maxY,maxZ)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,maxZ - 0.5012521743774414)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,maxZ - 0.5012522339820862)
    ,(minX,-1.5629622041046787e-08,maxZ - 0.516154021024704)
    ,(maxX,-1.5599653124809265e-08,maxZ - 0.5161546468734741)
    ,(minX,maxY,maxZ - 0.516154021024704)
    ,(maxX,maxY,maxZ - 0.5161546468734741)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,maxZ - 0.516154408454895)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,maxZ - 0.5161541998386383)
    ,(maxX - 0.10429960489273071,maxY,maxZ - 0.516154408454895)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,maxZ - 0.5161543190479279)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,maxZ - 0.5161542594432831)
    ,(minX + 0.11909735202789307,maxY,maxZ - 0.5161542594432831)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,maxZ)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,maxZ)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,maxZ - 0.501252293586731)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,maxZ - 0.5012521147727966)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,maxZ)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,maxZ)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,maxZ - 0.5012521743774414)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,maxZ - 0.5012522339820862)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,maxZ - 0.516154408454895)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,maxZ - 0.5161541998386383)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,maxZ - 0.5161543190479279)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,maxZ - 0.5161542594432831)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,maxZ - 0.992994874715805)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,maxZ - 0.9929947257041931)
    ,(minX + 0.11909735202789307,maxY,maxZ - 0.9929947257041931)
    ,(maxX - 0.11909738183021545,maxY,maxZ - 0.992994874715805)
    ,(minX,-1.565730833874568e-08,maxZ - 0.9929942488670349)
    ,(maxX,-1.5599653124809265e-08,maxZ - 0.9929954260587692)
    ,(minX,maxY,maxZ - 0.9929942488670349)
    ,(maxX,maxY,maxZ - 0.9929954260587692)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,maxZ - 0.9929950088262558)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,maxZ - 0.9929945915937424)
    ,(maxX - 0.10429960489273071,maxY,maxZ - 0.9929950088262558)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,maxZ - 0.9929950088262558)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,maxZ - 0.9929945915937424)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,maxZ - 0.992994874715805)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,maxZ - 0.9929947257041931)
    ,(maxX - 0.11909729242324829,maxY - 0.0004077646881341934,maxZ - 0.992994874715805)
    ,(maxX - 0.10429960489273071,maxY - 0.0004077646881341934,maxZ - 0.9929950088262558)
    ,(maxX - 0.10429960489273071,maxY,maxZ)
    ,(maxX - 0.11909729242324829,maxY,maxZ)
    ,(maxX - 0.11909738183021545,maxY,maxZ - 0.5012522339820862)
    ,(minX + 0.11909735202789307,maxY,maxZ - 0.5012521743774414)
    ,(minX + 0.10429966449737549,maxY,maxZ - 0.5161541998386383)
    ,(maxX - 0.11909738183021545,maxY,maxZ - 0.5161543190479279)
    ,(minX + 0.10429966449737549,maxY,maxZ - 0.9929945915937424)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,maxZ)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,maxZ)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,maxZ - 0.5012521147727966)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,maxZ - 0.501252293586731)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,maxZ)
    ,(maxX - 0.11909729242324829,maxY - 0.008999999612569809,maxZ)
    ,(maxX - 0.11909738183021545,maxY - 0.008999999612569809,maxZ - 0.5012522339820862)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,maxZ - 0.5012521743774414)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,maxZ - 0.5161541998386383)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,maxZ - 0.516154408454895)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,maxZ - 0.5161542594432831)
    ,(maxX - 0.11909738183021545,maxY - 0.008999999612569809,maxZ - 0.5161543190479279)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,maxZ - 0.9929947257041931)
    ,(maxX - 0.11909738183021545,maxY - 0.008999999612569809,maxZ - 0.992994874715805)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,maxZ - 0.9929945915937424)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,maxZ - 0.9929950088262558)
    ,(minX,-1.5599653124809265e-08,minZ)
    ,(maxX,-1.5599653124809265e-08,minZ)
    ,(minX,maxY,minZ)
    ,(maxX,maxY,minZ)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,minZ)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,minZ)
    ,(minX + 0.10429966449737549,maxY,minZ)
    ,(minX,-1.5628756955266e-08,minZ + 0.5012519359588623)
    ,(minX,-1.5657860785722733e-08,minZ + 1.0025038719177246)
    ,(maxX,-1.5599653124809265e-08,minZ + 0.5012525320053101)
    ,(maxX,-1.5599653124809265e-08,minZ + 1.0025050640106201)
    ,(minX,maxY,minZ + 0.5012519359588623)
    ,(minX,maxY,minZ + 1.0025038719177246)
    ,(maxX,maxY,minZ + 0.5012525320053101)
    ,(maxX,maxY,minZ + 1.0025050640106201)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,minZ + 0.501252293586731)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,minZ + 1.0025046467781067)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,minZ + 0.5012521147727966)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,minZ + 1.0025042295455933)
    ,(minX + 0.10429966449737549,maxY,minZ + 0.5012521147727966)
    ,(minX + 0.10429966449737549,maxY,minZ + 1.0025042295455933)
    ,(maxX - 0.10429960489273071,maxY,minZ + 0.501252293586731)
    ,(maxX - 0.10429960489273071,maxY,minZ + 1.0025046467781067)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,minZ)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,minZ)
    ,(minX + 0.11909735202789307,maxY,minZ)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,minZ + 0.5012521743774414)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,minZ + 0.5012522339820862)
    ,(minX + 0.11909735202789307,maxY,minZ + 1.0025043686230788)
    ,(minX,-1.5629622041046787e-08,minZ + 0.516154021024704)
    ,(maxX,-1.5599653124809265e-08,minZ + 0.5161546468734741)
    ,(minX,maxY,minZ + 0.516154021024704)
    ,(maxX,maxY,minZ + 0.5161546468734741)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,minZ + 0.516154408454895)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,minZ + 0.5161541998386383)
    ,(maxX - 0.10429960489273071,maxY,minZ + 0.516154408454895)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,minZ + 0.5161543190479279)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,minZ + 0.5161542594432831)
    ,(minX + 0.11909735202789307,maxY,minZ + 0.5161542594432831)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,minZ)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,minZ)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,minZ + 0.501252293586731)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,minZ + 1.0025046467781067)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,minZ + 0.5012521147727966)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,minZ + 1.0025042295455933)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,minZ)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,minZ)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,minZ + 0.5012521743774414)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,minZ + 0.5012522339820862)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,minZ + 0.516154408454895)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,minZ + 0.5161541998386383)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,minZ + 0.5161543190479279)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,minZ + 0.5161542594432831)
    ,(maxX - 0.11909729242324829,-1.5832483768463135e-08,minZ + 0.992994874715805)
    ,(minX + 0.11909735202789307,-1.5832483768463135e-08,minZ + 0.9929947257041931)
    ,(minX + 0.11909735202789307,maxY,minZ + 0.9929947257041931)
    ,(maxX - 0.11909738183021545,maxY,minZ + 0.992994874715805)
    ,(minX,-1.565730833874568e-08,minZ + 0.9929942488670349)
    ,(maxX,-1.5599653124809265e-08,minZ + 0.9929954260587692)
    ,(minX,maxY,minZ + 0.9929942488670349)
    ,(maxX,maxY,minZ + 0.9929954260587692)
    ,(maxX - 0.10429960489273071,-1.5832483768463135e-08,minZ + 0.9929950088262558)
    ,(minX + 0.10429966449737549,-1.5832483768463135e-08,minZ + 0.9929945915937424)
    ,(maxX - 0.10429960489273071,maxY,minZ + 0.9929950088262558)
    ,(maxX - 0.10429960489273071,minY + 0.009999999776482582,minZ + 0.9929950088262558)
    ,(minX + 0.10429966449737549,minY + 0.009999999776482582,minZ + 0.9929945915937424)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,minZ + 1.0025043686231356)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,minZ + 1.0025045077006212)
    ,(maxX - 0.10429960489273071,maxY - 0.0004077646881341934,minZ + 1.0025046467781067)
    ,(maxX - 0.11909729242324829,maxY - 0.0004077646881341934,minZ + 1.0025045077006212)
    ,(maxX - 0.11909729242324829,minY + 0.009999999776482582,minZ + 0.992994874715805)
    ,(minX + 0.11909735202789307,minY + 0.009999999776482582,minZ + 0.9929947257041931)
    ,(maxX - 0.11909729242324829,maxY - 0.0004077646881341934,minZ + 0.992994874715805)
    ,(maxX - 0.10429960489273071,maxY - 0.0004077646881341934,minZ + 0.9929950088262558)
    ,(maxX - 0.10429960489273071,maxY,minZ)
    ,(maxX - 0.11909729242324829,maxY,minZ)
    ,(maxX - 0.11909738183021545,maxY,minZ + 0.5012522339820862)
    ,(minX + 0.11909735202789307,maxY,minZ + 0.5012521743774414)
    ,(maxX - 0.11909738183021545,maxY,minZ + 1.0025045077005643)
    ,(minX + 0.10429966449737549,maxY,minZ + 0.5161541998386383)
    ,(maxX - 0.11909738183021545,maxY,minZ + 0.5161543190479279)
    ,(minX + 0.10429966449737549,maxY,minZ + 0.9929945915937424)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,minZ)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,minZ)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,minZ + 0.5012521147727966)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,minZ + 1.0025042295455933)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,minZ + 0.501252293586731)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,minZ + 1.0025046467781067)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,minZ)
    ,(maxX - 0.11909729242324829,maxY - 0.008999999612569809,minZ)
    ,(maxX - 0.11909738183021545,maxY - 0.008999999612569809,minZ + 0.5012522339820862)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,minZ + 0.5012521743774414)
    ,(maxX - 0.11909738183021545,maxY - 0.008999999612569809,minZ + 1.0025045077005643)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,minZ + 1.0025043686230788)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,minZ + 0.5161541998386383)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,minZ + 0.516154408454895)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,minZ + 0.5161542594432831)
    ,(maxX - 0.11909738183021545,maxY - 0.008999999612569809,minZ + 0.5161543190479279)
    ,(minX + 0.11909735202789307,maxY - 0.008999999612569809,minZ + 0.9929947257041931)
    ,(maxX - 0.11909738183021545,maxY - 0.008999999612569809,minZ + 0.992994874715805)
    ,(minX + 0.10429966449737549,maxY - 0.008999999612569809,minZ + 0.9929945915937424)
    ,(maxX - 0.10429960489273071,maxY - 0.008999999612569809,minZ + 0.9929950088262558)]
    
    # Faces
    myFaces = [(2, 0, 5, 6),(3, 1, 8, 10),(49, 47, 92, 96),(0, 2, 9, 7),(46, 48, 94, 90)
    ,(5, 0, 7, 12),(51, 46, 90, 100),(52, 49, 96, 104),(1, 4, 11, 8),(47, 50, 98, 92)
    ,(12, 25, 39, 33),(2, 6, 13, 9),(5, 12, 33, 31),(16, 15, 18, 19),(18, 15, 34, 36)
    ,(10, 8, 21, 23),(7, 9, 22, 20),(12, 7, 20, 25),(14, 10, 23, 26),(8, 11, 24, 21)
    ,(51, 100, 126, 54),(24, 11, 32, 38),(16, 19, 37, 35),(34, 31, 33, 36),(30, 35, 37, 32)
    ,(36, 33, 39, 41),(32, 37, 40, 38),(37, 36, 41, 40),(19, 18, 36, 37),(28, 27, 40, 41)
    ,(20, 22, 48, 46),(11, 4, 30, 32),(23, 21, 47, 49),(50, 24, 38, 53),(25, 20, 46, 51)
    ,(26, 23, 49, 52),(21, 24, 50, 47),(27, 28, 43, 42),(25, 51, 54, 39),(98, 50, 53, 124)
    ,(55, 56, 148, 149),(126, 148, 56, 54),(42, 43, 56, 55),(124, 53, 55, 149),(61, 60, 71, 72)
    ,(35, 30, 66, 71),(31, 34, 70, 67),(71, 66, 69, 72),(79, 81, 169, 174),(67, 70, 73, 68)
    ,(80, 78, 175, 167),(78, 79, 174, 175),(72, 69, 75, 77),(68, 73, 76, 74),(73, 72, 77, 76)
    ,(77, 75, 81, 79),(74, 76, 78, 80),(62, 61, 72, 73),(65, 63, 74, 80),(59, 4, 1, 3)
    ,(59, 3, 10, 14),(48, 65, 102, 94),(17, 15, 16, 60),(17, 60, 61, 62),(9, 13, 63, 22)
    ,(43, 28, 41, 56),(27, 42, 55, 40),(22, 63, 65, 48),(29, 64, 45, 44),(41, 39, 54, 56)
    ,(38, 40, 55, 53),(29, 44, 78, 76),(63, 13, 68, 74),(17, 62, 73, 70),(52, 104, 169, 81)
    ,(64, 29, 76, 77),(13, 6, 67, 68),(59, 14, 69, 66),(44, 45, 79, 78),(45, 64, 77, 79)
    ,(14, 26, 75, 69),(26, 52, 81, 75),(102, 65, 80, 167),(84, 88, 87, 82),(85, 95, 91, 83)
    ,(142, 96, 92, 140),(82, 89, 93, 84),(139, 90, 94, 141),(87, 99, 89, 82),(144, 100, 90, 139)
    ,(145, 104, 96, 142),(83, 91, 97, 86),(140, 92, 98, 143),(99, 125, 132, 116),(84, 93, 101, 88)
    ,(87, 122, 125, 99),(106, 109, 108, 105),(108, 129, 127, 105),(95, 114, 112, 91),(89, 111, 113, 93)
    ,(99, 116, 111, 89),(103, 117, 114, 95),(91, 112, 115, 97),(144, 147, 126, 100),(115, 131, 123, 97)
    ,(106, 128, 130, 109),(127, 129, 125, 122),(121, 123, 130, 128),(129, 134, 132, 125),(123, 131, 133, 130)
    ,(130, 133, 134, 129),(109, 130, 129, 108),(119, 134, 133, 118),(111, 139, 141, 113),(97, 123, 121, 86)
    ,(114, 142, 140, 112),(143, 146, 131, 115),(116, 144, 139, 111),(117, 145, 142, 114),(112, 140, 143, 115)
    ,(118, 135, 136, 119),(116, 132, 147, 144),(98, 124, 146, 143),(152, 149, 148, 153),(126, 147, 153, 148)
    ,(135, 152, 153, 136),(124, 149, 152, 146),(158, 172, 171, 157),(128, 171, 164, 121),(122, 165, 170, 127)
    ,(171, 172, 168, 164),(181, 174, 169, 183),(165, 166, 173, 170),(182, 167, 175, 180),(180, 175, 174, 181)
    ,(172, 179, 177, 168),(166, 176, 178, 173),(173, 178, 179, 172),(179, 181, 183, 177),(176, 182, 180, 178)
    ,(159, 173, 172, 158),(163, 182, 176, 161),(156, 85, 83, 86),(156, 103, 95, 85),(141, 94, 102, 163)
    ,(107, 157, 106, 105),(107, 159, 158, 157),(93, 113, 161, 101),(136, 153, 134, 119),(118, 133, 152, 135)
    ,(113, 141, 163, 161),(120, 137, 138, 162),(134, 153, 147, 132),(131, 146, 152, 133),(120, 178, 180, 137)
    ,(161, 176, 166, 101),(107, 170, 173, 159),(145, 183, 169, 104),(162, 179, 178, 120),(101, 166, 165, 88)
    ,(160, 174, 175, 110),(156, 164, 168, 103),(137, 180, 181, 138),(138, 181, 179, 162),(103, 168, 177, 117)
    ,(117, 177, 183, 145),(102, 167, 182, 163)]
    
    
    return (myVertex,myFaces,wf,deep,side)  

#----------------------------------------------
# Door model 04
#----------------------------------------------
def door_model_04(frame_size,frame_width,frame_height,frame_thick,openside):
    gap = 0.002
    sf = frame_size
    wf = frame_width - (sf * 2) - (gap * 2)
    hf = (frame_height/2)- (gap * 2) 
    deep = (frame_thick * 0.50) 

    #------------------------------------
    # Mesh data
    #------------------------------------
    # Open to right or left
    if(openside == "1"):
        side = 1
        minX = wf * -1
        maxX = 0.0
    else:
        side = -1
        minX = 0.0
        maxX = wf
    
    minY = 0.0 # Locked
    
    maxY = deep
    minZ = -hf
    maxZ = hf - sf - gap 

    # Vertex
    myVertex = [(minX,-1.57160684466362e-08,minZ + 2.384185791015625e-06)
    ,(maxX,-1.5599653124809265e-08,minZ)
    ,(minX,-1.5599653124809265e-08,maxZ)
    ,(minX,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(minX,-1.57160684466362e-08,minZ + 0.2500007152557373)
    ,(maxX,-1.5599653124809265e-08,minZ + 0.25000011920928955)
    ,(maxX,-1.5599653124809265e-08,maxZ)
    ,(maxX,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(maxX - 0.11968576163053513,-1.5599653124809265e-08,maxZ)
    ,(maxX - 0.11968576163053513,-1.5599653124809265e-08,minZ)
    ,(maxX - 0.11968576163053513,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(maxX - 0.11968576163053513,-1.5599653124809265e-08,minZ + 0.25000011920928955)
    ,(minX + 0.12030857801437378,-1.5832483768463135e-08,minZ + 0.25000011920928955)
    ,(minX + 0.12030857801437378,-1.5599653124809265e-08,maxZ - 0.12999999523162842)
    ,(minX + 0.12030857801437378,-1.5832483768463135e-08,minZ)
    ,(minX + 0.12030857801437378,-1.5599653124809265e-08,maxZ)
    ,(minX + 0.12030857801437378,-0.010000014677643776,maxZ - 0.12999999523162842)
    ,(minX + 0.12030857801437378,-0.010000014677643776,minZ + 0.25000011920928955)
    ,(maxX - 0.11968576163053513,-0.010000014677643776,maxZ - 0.12999999523162842)
    ,(maxX - 0.11968576163053513,-0.010000014677643776,minZ + 0.25000011920928955)
    ,(maxX - 0.1353275030851364,-0.009388341568410397,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275030851364,-0.009388341568410397,maxZ - 0.14747536182403564)
    ,(minX + 0.13506758213043213,-0.009388341568410397,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275030851364,-0.008776669390499592,minZ + 0.26250016689300537)
    ,(minX + 0.13506758213043213,-0.009388341568410397,maxZ - 0.14747536182403564)
    ,(maxX - 0.1353275030851364,-0.0003883419558405876,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275030851364,-0.0003883419558405876,maxZ - 0.14747536182403564)
    ,(minX + 0.13506758213043213,-0.0003883419558405876,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275030851364,minY + 0.010223344899713993,minZ + 0.26250016689300537)
    ,(minX + 0.13506758213043213,-0.0003883419558405876,maxZ - 0.14747536182403564)
    ,(minX,maxY - 0.009999999776482582,minZ + 2.384185791015625e-06)
    ,(maxX,maxY - 0.009999999776482582,minZ)
    ,(minX,maxY - 0.009999999776482582,maxZ)
    ,(minX,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(minX,maxY - 0.009999999776482582,minZ + 0.2500007152557373)
    ,(maxX,maxY - 0.009999999776482582,minZ + 0.25000011920928955)
    ,(maxX,maxY - 0.009999999776482582,maxZ)
    ,(maxX,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(maxX - 0.11968576908111572,maxY - 0.009999999776482582,maxZ)
    ,(maxX - 0.11968576908111572,maxY - 0.009999999776482582,minZ)
    ,(maxX - 0.11968576908111572,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(maxX - 0.11968576908111572,maxY - 0.009999999776482582,minZ + 0.25000011920928955)
    ,(minX + 0.12030857801437378,maxY - 0.009999999776482582,minZ + 0.25000011920928955)
    ,(minX + 0.12030857801437378,maxY - 0.009999999776482582,maxZ - 0.12999999523162842)
    ,(minX + 0.12030857801437378,maxY - 0.009999999776482582,minZ)
    ,(minX + 0.12030857801437378,maxY - 0.009999999776482582,maxZ)
    ,(minX + 0.12030857801437378,maxY,maxZ - 0.12999999523162842)
    ,(minX + 0.12030857801437378,maxY,minZ + 0.25000011920928955)
    ,(maxX - 0.11968576908111572,maxY,maxZ - 0.12999999523162842)
    ,(maxX - 0.11968576908111572,maxY,minZ + 0.25000011920928955)
    ,(maxX - 0.1353275179862976,maxY - 0.0006116721779108047,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275179862976,maxY - 0.0006116721779108047,maxZ - 0.14747536182403564)
    ,(minX + 0.13506758213043213,maxY - 0.0006116721779108047,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275179862976,maxY - 0.0012233462184667587,minZ + 0.26250016689300537)
    ,(minX + 0.13506758213043213,maxY - 0.0006116721779108047,maxZ - 0.14747536182403564)
    ,(maxX - 0.1353275179862976,maxY - 0.009611671790480614,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275179862976,maxY - 0.009611671790480614,maxZ - 0.14747536182403564)
    ,(minX + 0.13506758213043213,maxY - 0.009611671790480614,minZ + 0.26250016689300537)
    ,(maxX - 0.1353275179862976,maxY - 0.010223345831036568,minZ + 0.26250016689300537)
    ,(minX + 0.13506758213043213,maxY - 0.009611671790480614,maxZ - 0.14747536182403564)]
    
    # Faces
    myFaces = [(12, 4, 0, 14),(15, 2, 3, 13),(6, 8, 10, 7),(8, 15, 13, 10),(11, 12, 14, 9)
    ,(5, 11, 9, 1),(10, 13, 16, 18),(12, 11, 19, 17),(3, 4, 12, 13),(5, 7, 10, 11)
    ,(23, 19, 17, 22),(18, 19, 20, 21),(17, 16, 24, 22),(17, 16, 13, 12),(11, 10, 18, 19)
    ,(21, 18, 16, 24),(22, 24, 29, 27),(21, 24, 29, 26),(21, 20, 25, 26),(23, 22, 27, 28)
    ,(25, 28, 27, 29, 26),(42, 34, 30, 44),(45, 32, 33, 43),(36, 38, 40, 37),(38, 45, 43, 40)
    ,(41, 42, 44, 39),(35, 41, 39, 31),(40, 43, 46, 48),(42, 41, 49, 47),(33, 34, 42, 43)
    ,(35, 37, 40, 41),(53, 49, 47, 52),(48, 49, 50, 51),(47, 46, 54, 52),(47, 46, 43, 42)
    ,(41, 40, 48, 49),(51, 48, 46, 54),(52, 54, 59, 57),(51, 54, 59, 56),(51, 50, 55, 56)
    ,(53, 52, 57, 58),(55, 58, 57, 59, 56),(36, 6, 8, 38),(38, 8, 15, 45),(2, 32, 45, 15)
    ,(6, 36, 37, 7),(7, 37, 35, 5),(31, 1, 5, 35),(1, 31, 39, 9),(9, 39, 44, 14)
    ,(30, 0, 14, 44),(34, 4, 3, 33),(32, 2, 3, 33),(34, 4, 0, 30)]
    
    
    return (myVertex,myFaces,wf,deep,side)  

#----------------------------------------------
# Handle model 01
#----------------------------------------------
def handle_model_01(self,context):
    #------------------------------------
    # Mesh data
    #------------------------------------
    minX = -0.04349547624588013
    maxX = 0.13793155550956726
    minY = -0.07251644879579544
    maxY = 0
    minZ = -0.04352371022105217
    maxZ = 0.04349301755428314
    
    # Vertex
    myVertex = [(minX + 0.013302795588970184,maxY - 0.002780601382255554,minZ + 0.010707870125770569)
    ,(minX + 0.0009496212005615234,maxY - 0.002942140679806471,minZ + 0.030204588547348976)
    ,(minX                 ,maxY - 0.003071820829063654,maxZ - 0.033750676549971104)
    ,(minX + 0.010708402842283249,maxY - 0.0031348932534456253,maxZ - 0.013303784653544426)
    ,(minX + 0.03020550962537527,maxY - 0.003114458406344056,maxZ - 0.0009501762688159943)
    ,(minX + 0.053267089650034904,maxY - 0.003015991533175111,maxZ - 0.0           )
    ,(minX + 0.07371381670236588,maxY - 0.0028658765368163586,maxZ - 0.010707847774028778)
    ,(minX + 0.08606699481606483,maxY - 0.0027043374720960855,maxZ - 0.030204561538994312)
    ,(minX + 0.08701662346720695,maxY - 0.0025746573228389025,minZ + 0.03375071194022894)
    ,(minX + 0.0763082429766655,maxY - 0.002511584199965,minZ + 0.013303810730576515)
    ,(minX + 0.05681113991886377,maxY - 0.0025320190470665693,minZ + 0.0009501948952674866)
    ,(minX + 0.03374955803155899,maxY - 0.0026304861530661583,minZ                 )
    ,(minX + 0.014472760260105133,maxY - 0.019589224830269814,minZ + 0.011804874986410141)
    ,(minX + 0.002567145973443985,maxY - 0.019744910299777985,minZ + 0.030595174990594387)
    ,(minX + 0.001651916652917862,maxY - 0.019869891926646233,maxZ - 0.034195657819509506)
    ,(minX + 0.011972300708293915,maxY - 0.019930677488446236,maxZ - 0.014489583671092987)
    ,(minX + 0.03076297417283058,maxY - 0.019910985603928566,maxZ - 0.0025835558772087097)
    ,(minX + 0.0529889902099967,maxY - 0.019816085696220398,maxZ - 0.0016677752137184143)
    ,(minX + 0.07269490510225296,maxY - 0.01967141032218933,maxZ - 0.011987630277872086)
    ,(minX + 0.0846005342900753,maxY - 0.01951572299003601,maxZ - 0.030777926556766033)
    ,(minX + 0.08551576733589172,maxY - 0.019390743225812912,minZ + 0.03401290811598301)
    ,(minX + 0.07519540190696716,maxY - 0.01932995393872261,minZ + 0.014306826516985893)
    ,(minX + 0.056404732167720795,maxY - 0.01934964768588543,minZ + 0.002400781959295273)
    ,(minX + 0.03417872078716755,maxY - 0.019444547593593597,minZ + 0.001484982669353485)
    ,(minX + 0.043508310547622386,maxY - 0.0028232389595359564,maxZ - 0.043508357635801076)
    ,(minX + 0.029034355655312538,maxY - 0.019612153992056847,minZ + 0.027617475017905235)
    ,(minX + 0.023084014654159546,maxY - 0.01968996599316597,minZ + 0.03700872650370002)
    ,(minX + 0.022626593708992004,maxY - 0.01975242979824543,maxZ - 0.03889966616407037)
    ,(minX + 0.027784643694758415,maxY - 0.019782811403274536,maxZ - 0.029050718992948532)
    ,(minX + 0.03717608004808426,maxY - 0.019772969186306,maxZ - 0.023100173100829124)
    ,(minX + 0.048284475691616535,maxY - 0.019725536927580833,maxZ - 0.022642474621534348)
    ,(minX + 0.058133346028625965,maxY - 0.019653232768177986,maxZ - 0.02780025824904442)
    ,(minX + 0.06408369168639183,maxY - 0.019575420767068863,maxZ - 0.0371915097348392)
    ,(minX + 0.06454112380743027,maxY - 0.019512956961989403,minZ + 0.03871688432991505)
    ,(minX + 0.059383073821663857,maxY - 0.019482573494315147,minZ + 0.02886793203651905)
    ,(minX + 0.04999163839966059,maxY - 0.019492419436573982,minZ + 0.022917380556464195)
    ,(minX + 0.038883245550096035,maxY - 0.0195398461073637,minZ + 0.022459672763943672)
    ,(minX + 0.029087782837450504,maxY - 0.03150090575218201,minZ + 0.027552824467420578)
    ,(minX + 0.023137442767620087,maxY - 0.03157871589064598,minZ + 0.036944076884537935)
    ,(minX + 0.022680018097162247,maxY - 0.03164118155837059,maxZ - 0.03896431624889374)
    ,(minX + 0.027838071808218956,maxY - 0.031671565026044846,maxZ - 0.029115368612110615)
    ,(minX + 0.0372295081615448,maxY - 0.03166172280907631,maxZ - 0.023164819926023483)
    ,(minX + 0.04833790427073836,maxY - 0.03161429241299629,maxZ - 0.022707123309373856)
    ,(minX + 0.05818677507340908,maxY - 0.03154198080301285,maxZ - 0.027864910662174225)
    ,(minX + 0.06413711979985237,maxY - 0.031464170664548874,maxZ - 0.037256159354001284)
    ,(minX + 0.06459455192089081,maxY - 0.03140170872211456,minZ + 0.038652234710752964)
    ,(minX + 0.059436503797769547,maxY - 0.03137132152915001,minZ + 0.028803281486034393)
    ,(minX + 0.05004506651312113,maxY - 0.031381167471408844,minZ + 0.022852730005979538)
    ,(minX + 0.038936673663556576,maxY - 0.03142859786748886,minZ + 0.022395022213459015)
    ,(minX + 0.029038896784186363,maxY - 0.020622700452804565,minZ + 0.027611978352069855)
    ,(minX + 0.02308855764567852,maxY - 0.02070051059126854,minZ + 0.0370032312348485)
    ,(minX + 0.02263113297522068,maxY - 0.020762978121638298,maxZ - 0.038905161898583174)
    ,(minX + 0.02778918668627739,maxY - 0.020793357864022255,maxZ - 0.029056214727461338)
    ,(minX + 0.037180622573941946,maxY - 0.02078351564705372,maxZ - 0.023105667904019356)
    ,(minX + 0.04828901821747422,maxY - 0.020736083388328552,maxZ - 0.02264796942472458)
    ,(minX + 0.05813788715749979,maxY - 0.020663777366280556,maxZ - 0.0278057549148798)
    ,(minX + 0.0640882346779108,maxY - 0.020585965365171432,maxZ - 0.03719700500369072)
    ,(minX + 0.06454566307365894,maxY - 0.020523501560091972,minZ + 0.0387113899923861)
    ,(minX + 0.05938761495053768,maxY - 0.020493119955062866,minZ + 0.028862436302006245)
    ,(minX + 0.04999618045985699,maxY - 0.020502964034676552,minZ + 0.022911883890628815)
    ,(minX + 0.03888778714463115,maxY - 0.02055039070546627,minZ + 0.02245417609810829)
    ,(minX + 0.03133368864655495,maxY - 0.031504075974226,minZ + 0.02999168261885643)
    ,(minX + 0.02630186453461647,maxY - 0.03156987577676773,minZ + 0.03793327230960131)
    ,(minX + 0.025915050879120827,maxY - 0.03162270039319992,maxZ - 0.039689837489277124)
    ,(minX + 0.0302768861874938,maxY - 0.031648389995098114,maxZ - 0.03136120364069939)
    ,(minX + 0.03821863234043121,maxY - 0.03164006769657135,maxZ - 0.026329202577471733)
    ,(minX + 0.04761230247095227,maxY - 0.03159996122121811,maxZ - 0.025942156091332436)
    ,(minX + 0.05594087019562721,maxY - 0.03153881058096886,maxZ - 0.030303767882287502)
    ,(minX + 0.06097269989550114,maxY - 0.03147301450371742,maxZ - 0.038245356641709805)
    ,(minX + 0.06135952286422253,maxY - 0.03142019361257553,minZ + 0.039377753622829914)
    ,(minX + 0.05699768662452698,maxY - 0.03139450028538704,minZ + 0.03104911558330059)
    ,(minX + 0.049055942334234715,maxY - 0.0314028225839138,minZ + 0.02601710893213749)
    ,(minX + 0.03966227453202009,maxY - 0.031442929059267044,minZ + 0.025630054995417595)
    ,(minX + 0.024973656982183456,maxY - 0.009611732326447964,minZ + 0.037668352015316486)
    ,(minX + 0.030362362042069435,maxY - 0.009541265666484833,minZ + 0.029163507744669914)
    ,(minX + 0.02455940842628479,maxY - 0.009668299928307533,maxZ - 0.03928851708769798)
    ,(minX + 0.029230606742203236,maxY - 0.009695813991129398,maxZ - 0.030369175598025322)
    ,(minX + 0.03773562144488096,maxY - 0.009686900302767754,maxZ - 0.02498028054833412)
    ,(minX + 0.04779553506523371,maxY - 0.009643946774303913,maxZ - 0.02456578239798546)
    ,(minX + 0.056714802980422974,maxY - 0.009578464552760124,maxZ - 0.02923674415796995)
    ,(minX + 0.0621035173535347,maxY - 0.009507997892796993,maxZ - 0.037741586565971375)
    ,(minX + 0.06251777522265911,maxY - 0.009451429359614849,minZ + 0.03921528346836567)
    ,(minX + 0.05784657597541809,maxY - 0.009423915296792984,minZ + 0.03029593825340271)
    ,(minX + 0.0493415636010468,maxY - 0.009432828985154629,minZ + 0.02490703947842121)
    ,(minX + 0.039281651843339205,maxY - 0.009475781582295895,minZ + 0.02449253387749195)
    ,(minX + 0.03144440520554781,maxY - 0.02431209199130535,minZ + 0.030186276882886887)
    ,(minX + 0.02647113800048828,maxY - 0.0243771281093359,minZ + 0.038035438396036625)
    ,(minX + 0.026088828220963478,maxY - 0.024429334327578545,maxZ - 0.03969699679873884)
    ,(minX + 0.030399901792407036,maxY - 0.02445472590625286,maxZ - 0.031465294770896435)
    ,(minX + 0.0382492202334106,maxY - 0.024446498602628708,maxZ - 0.026491858065128326)
    ,(minX + 0.04753356333822012,maxY - 0.024406857788562775,maxZ - 0.02610931731760502)
    ,(minX + 0.05576520040631294,maxY - 0.024346424266695976,maxZ - 0.03042016737163067)
    ,(minX + 0.060738470405340195,maxY - 0.024281391873955727,maxZ - 0.03826932841911912)
    ,(minX + 0.06112079136073589,maxY - 0.024229183793067932,minZ + 0.03946310793980956)
    ,(minX + 0.056809717789292336,maxY - 0.024203790351748466,minZ + 0.03123140148818493)
    ,(minX + 0.04896040167659521,maxY - 0.02421201765537262,minZ + 0.026257958263158798)
    ,(minX + 0.03967605973593891,maxY - 0.024251656606793404,minZ + 0.025875410065054893)
    ,(minX + 0.03160235192626715,minY + 0.013056624680757523,minZ + 0.02999513689428568)
    ,(minX + 0.02662908472120762,minY + 0.012991588562726974,minZ + 0.03784429794177413)
    ,(minX + 0.026246773079037666,minY + 0.012939386069774628,maxZ - 0.039888136787340045)
    ,(minX + 0.030557849444448948,minY + 0.012913990765810013,maxZ - 0.03165643382817507)
    ,(minX + 0.03840716602280736,minY + 0.012922219932079315,maxZ - 0.02668299712240696)
    ,(minX + 0.04769151005893946,minY + 0.012961860746145248,maxZ - 0.02630045637488365)
    ,(minX + 0.05592314712703228,minY + 0.013022292405366898,maxZ - 0.030611306428909302)
    ,(minX + 0.06089641526341438,minY + 0.013087328523397446,maxZ - 0.038460468873381615)
    ,(minX + 0.06127873808145523,minY + 0.013139534741640091,minZ + 0.03927196795120835)
    ,(minX + 0.05696766451001167,minY + 0.013164930045604706,minZ + 0.031040262430906296)
    ,(minX + 0.04911834839731455,minY + 0.013156700879335403,minZ + 0.026066819205880165)
    ,(minX + 0.0398340062238276,minY + 0.013117063790559769,minZ + 0.02568427100777626)
    ,(minX + 0.03166038449853659,minY + 0.00014262646436691284,minZ + 0.029924907721579075)
    ,(minX + 0.026687119156122208,minY + 7.76052474975586e-05,minZ + 0.0377740697003901)
    ,(minX + 0.026304809376597404,minY + 2.5391578674316406e-05,maxZ - 0.039958365727216005)
    ,(minX + 0.030615881085395813,minY                 ,maxZ - 0.031726663932204247)
    ,(minX + 0.0384651985950768,minY + 8.217990398406982e-06,maxZ - 0.026753226295113564)
    ,(minX + 0.0477495426312089,minY + 4.7869980335235596e-05,maxZ - 0.026370685547590256)
    ,(minX + 0.05598117969930172,minY + 0.00010830163955688477,maxZ - 0.03068153653293848)
    ,(minX + 0.06095444969832897,minY + 0.00017333775758743286,maxZ - 0.038530697114765644)
    ,(minX + 0.06133677065372467,minY + 0.0002255365252494812,minZ + 0.039201739244163036)
    ,(minX + 0.05702569708228111,minY + 0.00025093555450439453,minZ + 0.030970032326877117)
    ,(minX + 0.04917638096958399,minY + 0.00024271011352539062,minZ + 0.02599659003317356)
    ,(minX + 0.039892038563266397,minY + 0.00020306557416915894,minZ + 0.025614041835069656)
    ,(maxX - 0.012196376919746399,minY + 0.0031514912843704224,minZ + 0.03689247788861394)
    ,(maxX - 0.011049121618270874,minY + 0.0037728995084762573,minZ + 0.04000293998979032)
    ,(maxX - 0.010531991720199585,minY + 0.004111833870410919,maxZ - 0.041690999176353216)
    ,(maxX - 0.010783538222312927,minY + 0.0040774866938591,maxZ - 0.035582118667662144)
    ,(maxX - 0.011736378073692322,minY + 0.003679051995277405,maxZ - 0.030324016697704792)
    ,(maxX - 0.013135172426700592,minY + 0.003023289144039154,maxZ - 0.027325598523020744)
    ,(maxX - 0.013745412230491638,minY + 0.010863490402698517,minZ + 0.03701266320422292)
    ,(maxX - 0.012598156929016113,minY + 0.011484891176223755,minZ + 0.0401231253053993)
    ,(maxX - 0.012081027030944824,minY + 0.011823825538158417,maxZ - 0.041570812463760376)
    ,(maxX - 0.01233258843421936,minY + 0.011789467185735703,maxZ - 0.035461933352053165)
    ,(maxX - 0.013285413384437561,minY + 0.011391039937734604,maxZ - 0.030203829519450665)
    ,(maxX - 0.014684207737445831,minY + 0.010735277086496353,maxZ - 0.027205411344766617)
    ,(maxX - 0.000991135835647583,maxY - 0.01982143148779869,minZ + 0.03712343191727996)
    ,(maxX - 0.0034268200397491455,maxY - 0.018987802788615227,minZ + 0.03702782467007637)
    ,(maxX - 0.00027070939540863037,maxY - 0.018310068175196648,minZ + 0.040221322793513536)
    ,(maxX                 ,maxY - 0.017457325011491776,maxZ - 0.04147987486794591)
    ,(maxX - 0.00025157630443573,maxY - 0.01749167963862419,maxZ - 0.03537099435925484)
    ,(maxX - 0.000957980751991272,maxY - 0.018403928726911545,maxZ - 0.030105633661150932)
    ,(maxX - 0.001929953694343567,maxY - 0.019949644804000854,maxZ - 0.02709464356303215)
    ,(maxX - 0.0043656229972839355,maxY - 0.01911601796746254,maxZ - 0.027190251275897026)
    ,(maxX - 0.002706393599510193,maxY - 0.01747644878923893,minZ + 0.04012571508064866)
    ,(maxX - 0.0024356693029403687,maxY - 0.01662370003759861,maxZ - 0.04157548164948821)
    ,(maxX - 0.0026872456073760986,maxY - 0.016658056527376175,maxZ - 0.03546660114079714)
    ,(maxX - 0.0033936500549316406,maxY - 0.017570307478308678,maxZ - 0.030201241374015808)
    ,(minX + 0.04382078559137881,minY + 0.00012543797492980957,minZ + 0.04313003408606164)]
    
    # Faces
    myFaces = [(24, 0, 1),(24, 1, 2),(24, 2, 3),(24, 3, 4),(24, 4, 5)
    ,(24, 5, 6),(24, 6, 7),(24, 7, 8),(24, 8, 9),(24, 9, 10)
    ,(24, 10, 11),(11, 0, 24),(0, 12, 13, 1),(1, 13, 14, 2),(2, 14, 15, 3)
    ,(3, 15, 16, 4),(4, 16, 17, 5),(5, 17, 18, 6),(6, 18, 19, 7),(7, 19, 20, 8)
    ,(8, 20, 21, 9),(9, 21, 22, 10),(10, 22, 23, 11),(12, 0, 11, 23),(13, 12, 25, 26)
    ,(14, 13, 26, 27),(15, 14, 27, 28),(16, 15, 28, 29),(17, 16, 29, 30),(18, 17, 30, 31)
    ,(19, 18, 31, 32),(20, 19, 32, 33),(21, 20, 33, 34),(22, 21, 34, 35),(23, 22, 35, 36)
    ,(12, 23, 36, 25),(25, 49, 50, 26),(49, 37, 38, 50),(26, 50, 51, 27),(50, 38, 39, 51)
    ,(27, 51, 52, 28),(51, 39, 40, 52),(28, 52, 53, 29),(52, 40, 41, 53),(29, 53, 54, 30)
    ,(53, 41, 42, 54),(30, 54, 55, 31),(54, 42, 43, 55),(31, 55, 56, 32),(55, 43, 44, 56)
    ,(32, 56, 57, 33),(56, 44, 45, 57),(33, 57, 58, 34),(57, 45, 46, 58),(34, 58, 59, 35)
    ,(58, 46, 47, 59),(35, 59, 60, 36),(59, 47, 48, 60),(36, 60, 49, 25),(60, 48, 37, 49)
    ,(38, 37, 61, 62),(39, 38, 62, 63),(40, 39, 63, 64),(41, 40, 64, 65),(42, 41, 65, 66)
    ,(43, 42, 66, 67),(44, 43, 67, 68),(45, 44, 68, 69),(46, 45, 69, 70),(47, 46, 70, 71)
    ,(48, 47, 71, 72),(37, 48, 72, 61),(62, 61, 74, 73),(63, 62, 73, 75),(64, 63, 75, 76)
    ,(65, 64, 76, 77),(66, 65, 77, 78),(67, 66, 78, 79),(68, 67, 79, 80),(69, 68, 80, 81)
    ,(70, 69, 81, 82),(71, 70, 82, 83),(72, 71, 83, 84),(61, 72, 84, 74),(86, 85, 97, 98)
    ,(87, 86, 98, 99),(88, 87, 99, 100),(89, 88, 100, 101),(90, 89, 101, 102),(91, 90, 102, 103)
    ,(92, 91, 103, 104),(93, 92, 104, 105),(94, 93, 105, 106),(95, 94, 106, 107),(96, 95, 107, 108)
    ,(97, 85, 96, 108),(98, 97, 109, 110),(99, 98, 110, 111),(100, 99, 111, 112),(101, 100, 112, 113)
    ,(102, 101, 113, 114),(108, 107, 119, 120),(108, 120, 109, 97),(119, 107, 127, 121),(118, 119, 121, 122)
    ,(117, 118, 122, 123),(116, 117, 123, 124),(115, 116, 124, 125),(114, 115, 125, 126),(102, 114, 126, 132)
    ,(107, 106, 128, 127),(106, 105, 129, 128),(105, 104, 130, 129),(104, 103, 131, 130),(103, 102, 132, 131)
    ,(121, 127, 134, 133),(122, 121, 133, 135),(123, 122, 135, 136),(124, 123, 136, 137),(125, 124, 137, 138)
    ,(126, 125, 138, 139),(132, 126, 139, 140),(127, 128, 141, 134),(128, 129, 142, 141),(129, 130, 143, 142)
    ,(130, 131, 144, 143),(131, 132, 140, 144),(138, 144, 140, 139),(137, 143, 144, 138),(136, 142, 143, 137)
    ,(135, 141, 142, 136),(133, 134, 141, 135),(110, 109, 145),(111, 110, 145),(112, 111, 145)
    ,(113, 112, 145),(114, 113, 145),(115, 114, 145),(116, 115, 145),(117, 116, 145)
    ,(118, 117, 145),(119, 118, 145),(120, 119, 145),(109, 120, 145)]
    
    return (myVertex,myFaces)
#----------------------------------------------
# Handle model 02
#----------------------------------------------
def handle_model_02(self,context):
    #------------------------------------
    # Mesh data
    #------------------------------------
    minX = -0.04349547624588013
    maxX = 0.04352114722132683
    minY = -0.08959200233221054
    maxY = 0
    minZ = -0.04352371022105217
    maxZ = 0.04349301755428314
    
    # Vertex
    myVertex = [(minX + 0.013302795588970184,maxY - 0.002780601382255554,minZ + 0.010707870125770569)
    ,(minX + 0.0009496212005615234,maxY - 0.002942140679806471,minZ + 0.030204588547348976)
    ,(minX,maxY - 0.003071820829063654,maxZ - 0.033750676549971104)
    ,(minX + 0.010708402842283249,maxY - 0.0031348932534456253,maxZ - 0.013303784653544426)
    ,(minX + 0.03020550962537527,maxY - 0.003114458406344056,maxZ - 0.0009501762688159943)
    ,(maxX - 0.03374953381717205,maxY - 0.003015991533175111,maxZ)
    ,(maxX - 0.01330280676484108,maxY - 0.0028658765368163586,maxZ - 0.010707847774028778)
    ,(maxX - 0.0009496286511421204,maxY - 0.0027043374720960855,maxZ - 0.030204561538994312)
    ,(maxX,maxY - 0.0025746573228389025,minZ + 0.03375071194022894)
    ,(maxX - 0.010708380490541458,maxY - 0.002511584199965,minZ + 0.013303810730576515)
    ,(maxX - 0.03020548354834318,maxY - 0.0025320190470665693,minZ + 0.0009501948952674866)
    ,(minX + 0.03374955803155899,maxY - 0.0026304861530661583,minZ)
    ,(minX + 0.014472760260105133,maxY - 0.019589224830269814,minZ + 0.011804874986410141)
    ,(minX + 0.002567145973443985,maxY - 0.019744910299777985,minZ + 0.030595174990594387)
    ,(minX + 0.001651916652917862,maxY - 0.019869891926646233,maxZ - 0.034195657819509506)
    ,(minX + 0.011972300708293915,maxY - 0.019930677488446236,maxZ - 0.014489583671092987)
    ,(minX + 0.03076297417283058,maxY - 0.019910985603928566,maxZ - 0.0025835558772087097)
    ,(maxX - 0.034027633257210255,maxY - 0.019816085696220398,maxZ - 0.0016677752137184143)
    ,(maxX - 0.014321718364953995,maxY - 0.01967141032218933,maxZ - 0.011987630277872086)
    ,(maxX - 0.002416089177131653,maxY - 0.01951572299003601,maxZ - 0.030777926556766033)
    ,(maxX - 0.0015008561313152313,maxY - 0.019390743225812912,minZ + 0.03401290811598301)
    ,(maxX - 0.011821221560239792,maxY - 0.01932995393872261,minZ + 0.014306826516985893)
    ,(maxX - 0.03061189129948616,maxY - 0.01934964768588543,minZ + 0.002400781959295273)
    ,(minX + 0.03417872078716755,maxY - 0.019444547593593597,minZ + 0.001484982669353485)
    ,(minX + 0.043508310547622386,maxY - 0.005668943747878075,maxZ - 0.043508357635801076)
    ,(minX + 0.029034355655312538,maxY - 0.019612153992056847,minZ + 0.027617475017905235)
    ,(minX + 0.023084014654159546,maxY - 0.01968996599316597,minZ + 0.03700872650370002)
    ,(minX + 0.022626593708992004,maxY - 0.01975242979824543,maxZ - 0.03889966616407037)
    ,(minX + 0.027784643694758415,maxY - 0.019782811403274536,maxZ - 0.029050718992948532)
    ,(minX + 0.03717608004808426,maxY - 0.019772969186306,maxZ - 0.023100173100829124)
    ,(maxX - 0.03873214777559042,maxY - 0.019725536927580833,maxZ - 0.022642474621534348)
    ,(maxX - 0.02888327743858099,maxY - 0.019653232768177986,maxZ - 0.02780025824904442)
    ,(maxX - 0.022932931780815125,maxY - 0.019575420767068863,maxZ - 0.0371915097348392)
    ,(maxX - 0.022475499659776688,maxY - 0.019512956961989403,minZ + 0.03871688432991505)
    ,(maxX - 0.0276335496455431,maxY - 0.019482573494315147,minZ + 0.02886793203651905)
    ,(maxX - 0.03702498506754637,maxY - 0.019492419436573982,minZ + 0.022917380556464195)
    ,(minX + 0.038883245550096035,maxY - 0.0195398461073637,minZ + 0.022459672763943672)
    ,(minX + 0.029087782837450504,maxY - 0.03150090575218201,minZ + 0.027552824467420578)
    ,(minX + 0.023137442767620087,maxY - 0.03157871589064598,minZ + 0.036944076884537935)
    ,(minX + 0.022680018097162247,maxY - 0.03164118155837059,maxZ - 0.03896431624889374)
    ,(minX + 0.027838071808218956,maxY - 0.031671565026044846,maxZ - 0.029115368612110615)
    ,(minX + 0.0372295081615448,maxY - 0.03166172280907631,maxZ - 0.023164819926023483)
    ,(maxX - 0.03867871919646859,maxY - 0.03161429241299629,maxZ - 0.022707123309373856)
    ,(maxX - 0.028829848393797874,maxY - 0.03154198080301285,maxZ - 0.027864910662174225)
    ,(maxX - 0.022879503667354584,maxY - 0.031464170664548874,maxZ - 0.037256159354001284)
    ,(maxX - 0.022422071546316147,maxY - 0.03140170872211456,minZ + 0.038652234710752964)
    ,(maxX - 0.02758011966943741,maxY - 0.03137132152915001,minZ + 0.028803281486034393)
    ,(maxX - 0.03697155695408583,maxY - 0.031381167471408844,minZ + 0.022852730005979538)
    ,(minX + 0.038936673663556576,maxY - 0.03142859786748886,minZ + 0.022395022213459015)
    ,(minX + 0.029038896784186363,maxY - 0.020622700452804565,minZ + 0.027611978352069855)
    ,(minX + 0.02308855764567852,maxY - 0.02070051059126854,minZ + 0.0370032312348485)
    ,(minX + 0.02263113297522068,maxY - 0.020762978121638298,maxZ - 0.038905161898583174)
    ,(minX + 0.02778918668627739,maxY - 0.020793357864022255,maxZ - 0.029056214727461338)
    ,(minX + 0.037180622573941946,maxY - 0.02078351564705372,maxZ - 0.023105667904019356)
    ,(maxX - 0.03872760524973273,maxY - 0.020736083388328552,maxZ - 0.02264796942472458)
    ,(maxX - 0.028878736309707165,maxY - 0.020663777366280556,maxZ - 0.0278057549148798)
    ,(maxX - 0.02292838878929615,maxY - 0.020585965365171432,maxZ - 0.03719700500369072)
    ,(maxX - 0.022470960393548012,maxY - 0.020523501560091972,minZ + 0.0387113899923861)
    ,(maxX - 0.027629008516669273,maxY - 0.020493119955062866,minZ + 0.028862436302006245)
    ,(maxX - 0.03702044300734997,maxY - 0.020502964034676552,minZ + 0.022911883890628815)
    ,(minX + 0.03888778714463115,maxY - 0.02055039070546627,minZ + 0.02245417609810829)
    ,(minX + 0.03503026906400919,maxY - 0.0326739065349102,minZ + 0.03399384953081608)
    ,(minX + 0.03150810860097408,maxY - 0.032719966024160385,minZ + 0.03955277753993869)
    ,(minX + 0.03123734798282385,maxY - 0.03275693953037262,maxZ - 0.04088863683864474)
    ,(minX + 0.034290531650185585,maxY - 0.032774921506643295,maxZ - 0.035058788023889065)
    ,(minX + 0.039849569322541356,maxY - 0.0327690951526165,maxZ - 0.03153650462627411)
    ,(maxX - 0.04059170465916395,maxY - 0.03274102136492729,maxZ - 0.03126558102667332)
    ,(maxX - 0.03476190101355314,maxY - 0.032698217779397964,maxZ - 0.03431860730051994)
    ,(maxX - 0.031239738687872887,maxY - 0.03265216201543808,maxZ - 0.039877534145489335)
    ,(maxX - 0.03096897155046463,maxY - 0.032615188509225845,minZ + 0.040563880698755383)
    ,(maxX - 0.03402215428650379,maxY - 0.03259720280766487,minZ + 0.03473402839154005)
    ,(maxX - 0.03958118986338377,maxY - 0.032603029161691666,minZ + 0.03121174033731222)
    ,(minX + 0.04086008481681347,maxY - 0.032631102949380875,minZ + 0.030940811149775982)
    ,(minX + 0.026877090334892273,maxY - 0.04475956782698631,minZ + 0.02504805289208889)
    ,(minX + 0.020004114136099815,minY + 0.044742558151483536,minZ + 0.03589546587318182)
    ,(minX + 0.019475765526294708,minY + 0.044670410454273224,maxZ - 0.03829052206128836)
    ,(minX + 0.025433603674173355,minY + 0.04463531821966171,maxZ - 0.0269144456833601)
    ,(minX + 0.03628123179078102,minY + 0.04464668035507202,maxZ - 0.020041238516569138)
    ,(maxX - 0.0379045819863677,minY + 0.0447014644742012,maxZ - 0.01951257325708866)
    ,(maxX - 0.02652859501540661,minY + 0.044784992933273315,maxZ - 0.02547009475529194)
    ,(maxX - 0.01965562254190445,maxY - 0.04471714794635773,maxZ - 0.036317508202046156)
    ,(maxX - 0.019127257168293,maxY - 0.04464499279856682,minZ + 0.03786848206073046)
    ,(maxX - 0.02508508786559105,maxY - 0.04460989683866501,minZ + 0.026492400094866753)
    ,(maxX - 0.03593271458521485,maxY - 0.044621266424655914,minZ + 0.019619181752204895)
    ,(minX + 0.03825310105457902,maxY - 0.044676050543785095,minZ + 0.01909050904214382)
    ,(minX + 0.01721818558871746,minY + 0.00031135231256484985,minZ + 0.01437518559396267)
    ,(minX + 0.006362196058034897,minY + 0.00016936659812927246,minZ + 0.03150887507945299)
    ,(minX + 0.005527656525373459,minY + 5.542486906051636e-05,maxZ - 0.03524145483970642)
    ,(minX + 0.014938175678253174,minY,maxZ - 0.017272725701332092)
    ,(minX + 0.032072206027805805,minY + 1.7955899238586426e-05,maxZ - 0.006416358053684235)
    ,(maxX - 0.03467791061848402,minY + 0.00010447949171066284,maxZ - 0.0055813267827034)
    ,(maxX - 0.016709323972463608,minY + 0.00023641437292099,maxZ - 0.01499134860932827)
    ,(maxX - 0.005853328853845596,minY + 0.00037835538387298584,maxZ - 0.032125042751431465)
    ,(maxX - 0.0050187669694423676,minY + 0.0004923418164253235,minZ + 0.03462529182434082)
    ,(maxX - 0.014429278671741486,minY + 0.0005477666854858398,minZ + 0.016656557098031044)
    ,(maxX - 0.03156330715864897,minY + 0.0005298107862472534,minZ + 0.005800176411867142)
    ,(minX + 0.03518681041896343,minY + 0.000443287193775177,minZ + 0.0049651265144348145)
    ,(minX + 0.02942624967545271,minY + 0.0012636110186576843,minZ + 0.027632080018520355)
    ,(minX + 0.023563016206026077,minY + 0.0011869296431541443,minZ + 0.03688584640622139)
    ,(minX + 0.023112289607524872,minY + 0.0011253878474235535,maxZ - 0.039185164496302605)
    ,(minX + 0.028194833546876907,minY + 0.0010954588651657104,maxZ - 0.029480399563908577)
    ,(minX + 0.037448784336447716,minY + 0.0011051595211029053,maxZ - 0.023616963997483253)
    ,(maxX - 0.038622063118964434,minY + 0.0011518821120262146,maxZ - 0.023165971040725708)
    ,(maxX - 0.028917375952005386,minY + 0.001223146915435791,maxZ - 0.02824824769049883)
    ,(maxX - 0.02305414155125618,minY + 0.0012998059391975403,maxZ - 0.0375020164065063)
    ,(maxX - 0.02260340191423893,minY + 0.0013613700866699219,minZ + 0.03856899822130799)
    ,(maxX - 0.027685942128300667,minY + 0.001391299068927765,minZ + 0.028864230029284954)
    ,(maxX - 0.0369398919865489,minY + 0.001381605863571167,minZ + 0.023000789806246758)
    ,(minX + 0.03913095686584711,minY + 0.0013348758220672607,minZ + 0.022549785673618317)
    ,(minX + 0.03738117218017578,minY + 0.0037613436579704285,minZ + 0.03627043403685093)
    ,(minX + 0.03477128129452467,minY + 0.0037272050976753235,minZ + 0.04038954642601311)
    ,(minX + 0.034570650197565556,minY + 0.0036998093128204346,maxZ - 0.041754934238269925)
    ,(minX + 0.03683303436264396,minY + 0.0036864876747131348,maxZ - 0.03743506921455264)
    ,(minX + 0.040952228708192706,minY + 0.0036908015608787537,maxZ - 0.03482509031891823)
    ,(maxX - 0.0411921211052686,minY + 0.003711603581905365,maxZ - 0.03462434001266956)
    ,(maxX - 0.03687229100614786,minY + 0.0037433207035064697,maxZ - 0.03688660357147455)
    ,(maxX - 0.034262401051819324,minY + 0.003777444362640381,maxZ - 0.04100571759045124)
    ,(maxX - 0.03406176343560219,minY + 0.0038048475980758667,minZ + 0.0411387647036463)
    ,(maxX - 0.036324144806712866,minY + 0.0038181766867637634,minZ + 0.03681889921426773)
    ,(maxX - 0.04044333938509226,minY + 0.0038138628005981445,minZ + 0.03420891519635916)
    ,(minX + 0.04170101135969162,minY + 0.003793060779571533,minZ + 0.034008161164820194)
    ,(maxX - 0.043253868410829455,minY + 0.00480072945356369,minZ + 0.04320027763606049)
    ,(minX + 0.03971285093575716,maxY - 0.041327137500047684,maxZ - 0.031046375632286072)
    ,(maxX - 0.03359287604689598,maxY - 0.04114784672856331,minZ + 0.03433086443692446)
    ,(minX + 0.03072980046272278,maxY - 0.04131445661187172,maxZ - 0.040801193099468946)
    ,(minX + 0.031012218445539474,maxY - 0.04127589240670204,minZ + 0.03935709968209267)
    ,(minX + 0.04076687735505402,maxY - 0.04118320718407631,minZ + 0.030374319292604923)
    ,(minX + 0.034451283514499664,maxY - 0.03338594362139702,minZ + 0.033365121111273766)
    ,(minX + 0.030692334286868572,maxY - 0.03343509882688522,minZ + 0.039297766517847776)
    ,(minX + 0.03040337096899748,maxY - 0.03347455710172653,maxZ - 0.040701600490137935)
    ,(minX + 0.03366181440651417,maxY - 0.03349374979734421,maxZ - 0.03447982110083103)
    ,(minX + 0.03959457715973258,maxY - 0.033487528562545776,maxZ - 0.03072074055671692)
    ,(maxX - 0.040404647355899215,maxY - 0.033457569777965546,maxZ - 0.030431604012846947)
    ,(maxX - 0.03418291546404362,maxY - 0.03341188654303551,maxZ - 0.03368987888097763)
    ,(maxX - 0.030423964373767376,maxY - 0.0333627350628376,maxZ - 0.03962252289056778)
    ,(maxX - 0.030134993605315685,maxY - 0.03332327678799629,minZ + 0.04037684458307922)
    ,(maxX - 0.033393437042832375,maxY - 0.03330408036708832,minZ + 0.03415506146848202)
    ,(maxX - 0.03932619746774435,maxY - 0.03331030160188675,minZ + 0.030395975336432457)
    ,(minX + 0.040673027746379375,maxY - 0.03334026038646698,minZ + 0.030106833204627037)
    ,(minX + 0.030282274819910526,maxY - 0.005427400581538677,maxZ - 0.0011750981211662292)
    ,(minX + 0.013463903218507767,maxY - 0.005095209460705519,minZ + 0.0108589306473732)
    ,(minX + 0.010882444679737091,maxY - 0.005447734147310257,maxZ - 0.013467073440551758)
    ,(minX + 0.0011723600327968597,maxY - 0.005255943164229393,minZ + 0.030258373357355595)
    ,(minX + 0.0002274736762046814,maxY - 0.005384976044297218,maxZ - 0.033811951987445354)
    ,(maxX - 0.0134431142359972,maxY - 0.005180059932172298,maxZ - 0.010884080082178116)
    ,(maxX - 0.033787828870117664,maxY - 0.005329424981027842,maxZ - 0.00022966042160987854)
    ,(maxX - 0.0302614476531744,maxY - 0.004847868345677853,minZ + 0.0011499449610710144)
    ,(maxX - 0.00020667165517807007,maxY - 0.004890293348580599,minZ + 0.03378681745380163)
    ,(maxX - 0.0011515654623508453,maxY - 0.0050193266943097115,maxZ - 0.03028351627290249)
    ,(minX + 0.033808655105531216,maxY - 0.004945843946188688,minZ + 0.0002044886350631714)
    ,(maxX - 0.010861624032258987,maxY - 0.004827534779906273,minZ + 0.013441929593682289)
    ,(minX + 0.03468604106456041,maxY - 0.04122784733772278,minZ + 0.033558815717697144)
    ,(minX + 0.033914451487362385,maxY - 0.041333213448524475,maxZ - 0.03472032118588686)
    ,(maxX - 0.04044530005194247,maxY - 0.04129785671830177,maxZ - 0.03076378908008337)
    ,(maxX - 0.034364476799964905,maxY - 0.04125320911407471,maxZ - 0.03394827153533697)
    ,(maxX - 0.03069065511226654,maxY - 0.04120517522096634,maxZ - 0.03974655526690185)
    ,(maxX - 0.030408228747546673,maxY - 0.04116660729050636,minZ + 0.04041173937730491)
    ,(maxX - 0.03939127502962947,maxY - 0.0411539226770401,minZ + 0.030656912364065647)
    ,(minX + 0.03147818427532911,maxY - 0.033236272633075714,minZ + 0.03954096930101514)
    ,(minX + 0.031206720508635044,maxY - 0.03327333927154541,maxZ - 0.04088335996493697)
    ,(minX + 0.034267837181687355,maxY - 0.033291369676589966,maxZ - 0.03503836318850517)
    ,(minX + 0.03984131896868348,maxY - 0.03328552842140198,maxZ - 0.03150692768394947)
    ,(maxX - 0.040582869900390506,maxY - 0.0332573801279068,maxZ - 0.03123530000448227)
    ,(maxX - 0.03473791852593422,maxY - 0.033214468508958817,maxZ - 0.03429625928401947)
    ,(maxX - 0.031206604093313217,maxY - 0.03316829353570938,maxZ - 0.03986963024362922)
    ,(maxX - 0.030935133807361126,maxY - 0.03313122317194939,minZ + 0.040554699720814824)
    ,(maxX - 0.03399624954909086,maxY - 0.03311318904161453,minZ + 0.03470969945192337)
    ,(maxX - 0.03956972947344184,maxY - 0.03311903029680252,minZ + 0.031178259290754795)
    ,(minX + 0.04085446032695472,maxY - 0.0331471785902977,minZ + 0.030906626023352146)
    ,(minX + 0.035009496845304966,maxY - 0.03319009393453598,minZ + 0.03396759741008282)]
    
    # Faces
    myFaces = [(24, 0, 1),(24, 1, 2),(24, 2, 3),(24, 3, 4),(24, 4, 5)
    ,(24, 5, 6),(24, 6, 7),(24, 7, 8),(24, 8, 9),(24, 9, 10)
    ,(24, 10, 11),(11, 0, 24),(140, 12, 13, 142),(142, 13, 14, 143),(143, 14, 15, 141)
    ,(141, 15, 16, 139),(139, 16, 17, 145),(145, 17, 18, 144),(144, 18, 19, 148),(148, 19, 20, 147)
    ,(147, 20, 21, 150),(150, 21, 22, 146),(146, 22, 23, 149),(140, 0, 11, 149),(13, 12, 25, 26)
    ,(14, 13, 26, 27),(15, 14, 27, 28),(16, 15, 28, 29),(17, 16, 29, 30),(18, 17, 30, 31)
    ,(19, 18, 31, 32),(20, 19, 32, 33),(21, 20, 33, 34),(22, 21, 34, 35),(23, 22, 35, 36)
    ,(12, 23, 36, 25),(25, 49, 50, 26),(49, 37, 38, 50),(26, 50, 51, 27),(50, 38, 39, 51)
    ,(27, 51, 52, 28),(51, 39, 40, 52),(28, 52, 53, 29),(52, 40, 41, 53),(29, 53, 54, 30)
    ,(53, 41, 42, 54),(30, 54, 55, 31),(54, 42, 43, 55),(31, 55, 56, 32),(55, 43, 44, 56)
    ,(32, 56, 57, 33),(56, 44, 45, 57),(33, 57, 58, 34),(57, 45, 46, 58),(34, 58, 59, 35)
    ,(58, 46, 47, 59),(35, 59, 60, 36),(59, 47, 48, 60),(36, 60, 49, 25),(60, 48, 37, 49)
    ,(38, 37, 61, 62),(39, 38, 62, 63),(40, 39, 63, 64),(41, 40, 64, 65),(42, 41, 65, 66)
    ,(43, 42, 66, 67),(44, 43, 67, 68),(45, 44, 68, 69),(46, 45, 69, 70),(47, 46, 70, 71)
    ,(48, 47, 71, 72),(37, 48, 72, 61),(124, 125, 74, 75),(74, 73, 85, 86),(79, 78, 90, 91)
    ,(80, 79, 91, 92),(77, 76, 88, 89),(82, 81, 93, 94),(76, 75, 87, 88),(81, 80, 92, 93)
    ,(73, 84, 96, 85),(84, 83, 95, 96),(83, 82, 94, 95),(78, 77, 89, 90),(75, 74, 86, 87)
    ,(90, 89, 101, 102),(86, 85, 97, 98),(93, 92, 104, 105),(96, 95, 107, 108),(85, 96, 108, 97)
    ,(89, 88, 100, 101),(91, 90, 102, 103),(88, 87, 99, 100),(92, 91, 103, 104),(95, 94, 106, 107)
    ,(94, 93, 105, 106),(87, 86, 98, 99),(105, 104, 116, 117),(108, 107, 119, 120),(97, 108, 120, 109)
    ,(101, 100, 112, 113),(103, 102, 114, 115),(100, 99, 111, 112),(104, 103, 115, 116),(107, 106, 118, 119)
    ,(106, 105, 117, 118),(99, 98, 110, 111),(102, 101, 113, 114),(98, 97, 109, 110),(120, 119, 121)
    ,(109, 120, 121),(113, 112, 121),(115, 114, 121),(112, 111, 121),(116, 115, 121)
    ,(119, 118, 121),(118, 117, 121),(111, 110, 121),(114, 113, 121),(110, 109, 121)
    ,(117, 116, 121),(169, 158, 62, 61),(158, 159, 63, 62),(159, 160, 64, 63),(160, 161, 65, 64)
    ,(161, 162, 66, 65),(162, 163, 67, 66),(163, 164, 68, 67),(164, 165, 69, 68),(165, 166, 70, 69)
    ,(166, 167, 71, 70),(167, 168, 72, 71),(168, 169, 61, 72),(72, 138, 127, 61),(63, 129, 130, 64)
    ,(67, 133, 134, 68),(64, 130, 131, 65),(61, 127, 128, 62),(69, 135, 136, 70),(66, 132, 133, 67)
    ,(65, 131, 132, 66),(71, 137, 138, 72),(70, 136, 137, 71),(62, 128, 129, 63),(68, 134, 135, 69)
    ,(0, 140, 142, 1),(1, 142, 143, 2),(2, 143, 141, 3),(3, 141, 139, 4),(4, 139, 145, 5)
    ,(5, 145, 144, 6),(6, 144, 148, 7),(7, 148, 147, 8),(8, 147, 150, 9),(9, 150, 146, 10)
    ,(10, 146, 149, 11),(12, 140, 149, 23),(153, 154, 163, 162),(154, 155, 164, 163),(155, 156, 165, 164)
    ,(125, 151, 73, 74),(152, 124, 75, 76),(122, 152, 76, 77),(153, 122, 77, 78),(154, 153, 78, 79)
    ,(155, 154, 79, 80),(156, 155, 80, 81),(123, 156, 81, 82),(157, 123, 82, 83),(126, 157, 83, 84)
    ,(73, 151, 126, 84),(151, 125, 158, 169),(125, 124, 159, 158),(124, 152, 160, 159),(152, 122, 161, 160)
    ,(122, 153, 162, 161),(156, 123, 166, 165),(123, 157, 167, 166),(157, 126, 168, 167),(126, 151, 169, 168)]
    
    return (myVertex,myFaces)

#----------------------------------------------
# Handle model 03
#----------------------------------------------
def handle_model_03(self,context):
    #------------------------------------
    # Mesh data
    #------------------------------------
    minX = -0.04349547624588013
    maxX = 0.04352114722132683
    minY = -0.09871400892734528
    maxY = 0
    minZ = -0.04352371022105217
    maxZ = 0.04349301755428314
    
    # Vertex
    myVertex = [(minX + 0.013302795588970184,maxY - 0.002780601382255554,minZ + 0.010707870125770569)
    ,(minX + 0.0009496212005615234,maxY - 0.002942140679806471,minZ + 0.030204588547348976)
    ,(minX,maxY - 0.003071820829063654,maxZ - 0.033750676549971104)
    ,(minX + 0.010708402842283249,maxY - 0.0031348932534456253,maxZ - 0.013303784653544426)
    ,(minX + 0.03020550962537527,maxY - 0.003114458406344056,maxZ - 0.0009501762688159943)
    ,(maxX - 0.03374953381717205,maxY - 0.003015991533175111,maxZ)
    ,(maxX - 0.01330280676484108,maxY - 0.0028658765368163586,maxZ - 0.010707847774028778)
    ,(maxX - 0.0009496286511421204,maxY - 0.0027043374720960855,maxZ - 0.030204561538994312)
    ,(maxX,maxY - 0.0025746573228389025,minZ + 0.03375071194022894)
    ,(maxX - 0.010708380490541458,maxY - 0.002511584199965,minZ + 0.013303810730576515)
    ,(maxX - 0.03020548354834318,maxY - 0.0025320190470665693,minZ + 0.0009501948952674866)
    ,(minX + 0.03374955803155899,maxY - 0.0026304861530661583,minZ)
    ,(minX + 0.014472760260105133,maxY - 0.019589224830269814,minZ + 0.011804874986410141)
    ,(minX + 0.002567145973443985,maxY - 0.019744910299777985,minZ + 0.030595174990594387)
    ,(minX + 0.001651916652917862,maxY - 0.019869891926646233,maxZ - 0.034195657819509506)
    ,(minX + 0.011972300708293915,maxY - 0.019930677488446236,maxZ - 0.014489583671092987)
    ,(minX + 0.03076297417283058,maxY - 0.019910985603928566,maxZ - 0.0025835558772087097)
    ,(maxX - 0.034027633257210255,maxY - 0.019816085696220398,maxZ - 0.0016677752137184143)
    ,(maxX - 0.014321718364953995,maxY - 0.01967141032218933,maxZ - 0.011987630277872086)
    ,(maxX - 0.002416089177131653,maxY - 0.01951572299003601,maxZ - 0.030777926556766033)
    ,(maxX - 0.0015008561313152313,maxY - 0.019390743225812912,minZ + 0.03401290811598301)
    ,(maxX - 0.011821221560239792,maxY - 0.01932995393872261,minZ + 0.014306826516985893)
    ,(maxX - 0.03061189129948616,maxY - 0.01934964768588543,minZ + 0.002400781959295273)
    ,(minX + 0.03417872078716755,maxY - 0.019444547593593597,minZ + 0.001484982669353485)
    ,(minX + 0.043508310547622386,maxY - 0.005668943747878075,maxZ - 0.043508357635801076)
    ,(minX + 0.029034355655312538,maxY - 0.019612153992056847,minZ + 0.027617475017905235)
    ,(minX + 0.023084014654159546,maxY - 0.01968996599316597,minZ + 0.03700872650370002)
    ,(minX + 0.022626593708992004,maxY - 0.01975242979824543,maxZ - 0.03889966616407037)
    ,(minX + 0.027784643694758415,maxY - 0.019782811403274536,maxZ - 0.029050718992948532)
    ,(minX + 0.03717608004808426,maxY - 0.019772969186306,maxZ - 0.023100173100829124)
    ,(maxX - 0.03873214777559042,maxY - 0.019725536927580833,maxZ - 0.022642474621534348)
    ,(maxX - 0.02888327743858099,maxY - 0.019653232768177986,maxZ - 0.02780025824904442)
    ,(maxX - 0.022932931780815125,maxY - 0.019575420767068863,maxZ - 0.0371915097348392)
    ,(maxX - 0.022475499659776688,maxY - 0.019512956961989403,minZ + 0.03871688432991505)
    ,(maxX - 0.0276335496455431,maxY - 0.019482573494315147,minZ + 0.02886793203651905)
    ,(maxX - 0.03702498506754637,maxY - 0.019492419436573982,minZ + 0.022917380556464195)
    ,(minX + 0.038883245550096035,maxY - 0.0195398461073637,minZ + 0.022459672763943672)
    ,(minX + 0.029087782837450504,maxY - 0.03150090575218201,minZ + 0.027552824467420578)
    ,(minX + 0.023137442767620087,maxY - 0.03157871589064598,minZ + 0.036944076884537935)
    ,(minX + 0.022680018097162247,maxY - 0.03164118155837059,maxZ - 0.03896431624889374)
    ,(minX + 0.027838071808218956,maxY - 0.031671565026044846,maxZ - 0.029115368612110615)
    ,(minX + 0.0372295081615448,maxY - 0.03166172280907631,maxZ - 0.023164819926023483)
    ,(maxX - 0.03867871919646859,maxY - 0.03161429241299629,maxZ - 0.022707123309373856)
    ,(maxX - 0.028829848393797874,maxY - 0.03154198080301285,maxZ - 0.027864910662174225)
    ,(maxX - 0.022879503667354584,maxY - 0.031464170664548874,maxZ - 0.037256159354001284)
    ,(maxX - 0.022422071546316147,maxY - 0.03140170872211456,minZ + 0.038652234710752964)
    ,(maxX - 0.02758011966943741,maxY - 0.03137132152915001,minZ + 0.028803281486034393)
    ,(maxX - 0.03697155695408583,maxY - 0.031381167471408844,minZ + 0.022852730005979538)
    ,(minX + 0.038936673663556576,maxY - 0.03142859786748886,minZ + 0.022395022213459015)
    ,(minX + 0.029038896784186363,maxY - 0.020622700452804565,minZ + 0.027611978352069855)
    ,(minX + 0.02308855764567852,maxY - 0.02070051059126854,minZ + 0.0370032312348485)
    ,(minX + 0.02263113297522068,maxY - 0.020762978121638298,maxZ - 0.038905161898583174)
    ,(minX + 0.02778918668627739,maxY - 0.020793357864022255,maxZ - 0.029056214727461338)
    ,(minX + 0.037180622573941946,maxY - 0.02078351564705372,maxZ - 0.023105667904019356)
    ,(maxX - 0.03872760524973273,maxY - 0.020736083388328552,maxZ - 0.02264796942472458)
    ,(maxX - 0.028878736309707165,maxY - 0.020663777366280556,maxZ - 0.0278057549148798)
    ,(maxX - 0.02292838878929615,maxY - 0.020585965365171432,maxZ - 0.03719700500369072)
    ,(maxX - 0.022470960393548012,maxY - 0.020523501560091972,minZ + 0.0387113899923861)
    ,(maxX - 0.027629008516669273,maxY - 0.020493119955062866,minZ + 0.028862436302006245)
    ,(maxX - 0.03702044300734997,maxY - 0.020502964034676552,minZ + 0.022911883890628815)
    ,(minX + 0.03888778714463115,maxY - 0.02055039070546627,minZ + 0.02245417609810829)
    ,(minX + 0.03503026906400919,maxY - 0.0326739065349102,minZ + 0.03399384953081608)
    ,(minX + 0.03150810860097408,maxY - 0.032719966024160385,minZ + 0.03955277753993869)
    ,(minX + 0.03123734798282385,maxY - 0.03275693953037262,maxZ - 0.04088863683864474)
    ,(minX + 0.034290531650185585,maxY - 0.032774921506643295,maxZ - 0.035058788023889065)
    ,(minX + 0.039849569322541356,maxY - 0.0327690951526165,maxZ - 0.03153650462627411)
    ,(maxX - 0.04059170465916395,maxY - 0.03274102136492729,maxZ - 0.03126558102667332)
    ,(maxX - 0.03476190101355314,maxY - 0.032698217779397964,maxZ - 0.03431860730051994)
    ,(maxX - 0.031239738687872887,maxY - 0.03265216201543808,maxZ - 0.039877534145489335)
    ,(maxX - 0.03096897155046463,maxY - 0.032615188509225845,minZ + 0.040563880698755383)
    ,(maxX - 0.03402215428650379,maxY - 0.03259720280766487,minZ + 0.03473402839154005)
    ,(maxX - 0.03958118986338377,maxY - 0.032603029161691666,minZ + 0.03121174033731222)
    ,(minX + 0.04086008481681347,maxY - 0.032631102949380875,minZ + 0.030940811149775982)
    ,(minX + 0.026877090334892273,maxY - 0.04475956782698631,minZ + 0.02504805289208889)
    ,(minX + 0.020004114136099815,maxY - 0.044849444180727005,minZ + 0.03589546587318182)
    ,(minX + 0.019475765526294708,maxY - 0.04492159187793732,maxZ - 0.03829052206128836)
    ,(minX + 0.025433603674173355,maxY - 0.04495668411254883,maxZ - 0.0269144456833601)
    ,(minX + 0.03628123179078102,maxY - 0.04494532197713852,maxZ - 0.020041238516569138)
    ,(maxX - 0.0379045819863677,maxY - 0.04489053785800934,maxZ - 0.01951257325708866)
    ,(maxX - 0.02652859501540661,maxY - 0.044807009398937225,maxZ - 0.02547009475529194)
    ,(maxX - 0.01965562254190445,maxY - 0.04471714794635773,maxZ - 0.036317508202046156)
    ,(maxX - 0.019127257168293,maxY - 0.04464499279856682,minZ + 0.03786848206073046)
    ,(maxX - 0.02508508786559105,maxY - 0.04460989683866501,minZ + 0.026492400094866753)
    ,(maxX - 0.03593271458521485,maxY - 0.044621266424655914,minZ + 0.019619181752204895)
    ,(minX + 0.03825310105457902,maxY - 0.044676050543785095,minZ + 0.01909050904214382)
    ,(minX + 0.021551070734858513,minY + 0.00942724198102951,minZ + 0.01908031851053238)
    ,(minX + 0.01246710866689682,minY + 0.009308435022830963,minZ + 0.03341726865619421)
    ,(minX + 0.011768791824579239,minY + 0.009213089942932129,maxZ - 0.03664115583524108)
    ,(minX + 0.019643226638436317,minY + 0.009166710078716278,maxZ - 0.0216054730117321)
    ,(minX + 0.033980460837483406,minY + 0.009181737899780273,maxZ - 0.012521196156740189)
    ,(maxX - 0.036077769473195076,minY + 0.009254135191440582,maxZ - 0.011822465807199478)
    ,(maxX - 0.021042203530669212,minY + 0.0093645378947258,maxZ - 0.019696485251188278)
    ,(maxX - 0.011958237737417221,minY + 0.009483307600021362,maxZ - 0.03403343725949526)
    ,(maxX - 0.011259902268648148,minY + 0.009578689932823181,minZ + 0.03602499142289162)
    ,(maxX - 0.01913433149456978,minY + 0.009625062346458435,minZ + 0.020989302545785904)
    ,(maxX - 0.03347156383097172,minY + 0.009610041975975037,minZ + 0.011905014514923096)
    ,(minX + 0.03658666601404548,minY + 0.00953763723373413,minZ + 0.011206269264221191)
    ,(minX + 0.02942624967545271,minY + 0.001430809497833252,minZ + 0.027632080018520355)
    ,(minX + 0.023563016206026077,minY + 0.001354128122329712,minZ + 0.03688584640622139)
    ,(minX + 0.023112289607524872,minY + 0.001292586326599121,maxZ - 0.039185164496302605)
    ,(minX + 0.028194833546876907,minY + 0.001262657344341278,maxZ - 0.029480399563908577)
    ,(minX + 0.037448784336447716,minY + 0.001272358000278473,maxZ - 0.023616963997483253)
    ,(maxX - 0.038622063118964434,minY + 0.0013190805912017822,maxZ - 0.023165971040725708)
    ,(maxX - 0.028917375952005386,minY + 0.0013903453946113586,maxZ - 0.02824824769049883)
    ,(maxX - 0.02305414155125618,minY + 0.001467004418373108,maxZ - 0.0375020164065063)
    ,(maxX - 0.02260340191423893,minY + 0.0015285685658454895,minZ + 0.03856899822130799)
    ,(maxX - 0.027685942128300667,minY + 0.0015584975481033325,minZ + 0.028864230029284954)
    ,(maxX - 0.0369398919865489,minY + 0.0015488043427467346,minZ + 0.023000789806246758)
    ,(minX + 0.03913095686584711,minY + 0.0015020743012428284,minZ + 0.022549785673618317)
    ,(minX + 0.03738117218017578,minY + 0.001003175973892212,minZ + 0.03627043403685093)
    ,(minX + 0.03477128129452467,minY + 0.0009690374135971069,minZ + 0.04038954642601311)
    ,(minX + 0.034570650197565556,minY + 0.000941641628742218,maxZ - 0.041754934238269925)
    ,(minX + 0.03683303436264396,minY + 0.0009283199906349182,maxZ - 0.03743506921455264)
    ,(minX + 0.040952228708192706,minY + 0.0009326338768005371,maxZ - 0.03482509031891823)
    ,(maxX - 0.0411921211052686,minY + 0.0009534358978271484,maxZ - 0.03462434001266956)
    ,(maxX - 0.03687229100614786,minY + 0.0009851530194282532,maxZ - 0.03688660357147455)
    ,(maxX - 0.034262401051819324,minY + 0.0010192766785621643,maxZ - 0.04100571759045124)
    ,(maxX - 0.03406176343560219,minY + 0.0010466799139976501,minZ + 0.0411387647036463)
    ,(maxX - 0.036324144806712866,minY + 0.0010600090026855469,minZ + 0.03681889921426773)
    ,(maxX - 0.04044333938509226,minY + 0.001055695116519928,minZ + 0.03420891519635916)
    ,(minX + 0.04170101135969162,minY + 0.0010348930954933167,minZ + 0.034008161164820194)
    ,(maxX - 0.043253868410829455,minY,minZ + 0.04320027763606049)
    ,(minX + 0.03971285093575716,maxY - 0.041327137500047684,maxZ - 0.031046375632286072)
    ,(maxX - 0.03359287604689598,maxY - 0.04114784672856331,minZ + 0.03433086443692446)
    ,(minX + 0.03072980046272278,maxY - 0.04131445661187172,maxZ - 0.040801193099468946)
    ,(minX + 0.031012218445539474,maxY - 0.04127589240670204,minZ + 0.03935709968209267)
    ,(minX + 0.04076687735505402,maxY - 0.04118320718407631,minZ + 0.030374319292604923)
    ,(minX + 0.034451283514499664,maxY - 0.03338594362139702,minZ + 0.033365121111273766)
    ,(minX + 0.030692334286868572,maxY - 0.03343509882688522,minZ + 0.039297766517847776)
    ,(minX + 0.03040337096899748,maxY - 0.03347455710172653,maxZ - 0.040701600490137935)
    ,(minX + 0.03366181440651417,maxY - 0.03349374979734421,maxZ - 0.03447982110083103)
    ,(minX + 0.03959457715973258,maxY - 0.033487528562545776,maxZ - 0.03072074055671692)
    ,(maxX - 0.040404647355899215,maxY - 0.033457569777965546,maxZ - 0.030431604012846947)
    ,(maxX - 0.03418291546404362,maxY - 0.03341188654303551,maxZ - 0.03368987888097763)
    ,(maxX - 0.030423964373767376,maxY - 0.0333627350628376,maxZ - 0.03962252289056778)
    ,(maxX - 0.030134993605315685,maxY - 0.03332327678799629,minZ + 0.04037684458307922)
    ,(maxX - 0.033393437042832375,maxY - 0.03330408036708832,minZ + 0.03415506146848202)
    ,(maxX - 0.03932619746774435,maxY - 0.03331030160188675,minZ + 0.030395975336432457)
    ,(minX + 0.040673027746379375,maxY - 0.03334026038646698,minZ + 0.030106833204627037)
    ,(minX + 0.030282274819910526,maxY - 0.005427400581538677,maxZ - 0.0011750981211662292)
    ,(minX + 0.013463903218507767,maxY - 0.005095209460705519,minZ + 0.0108589306473732)
    ,(minX + 0.010882444679737091,maxY - 0.005447734147310257,maxZ - 0.013467073440551758)
    ,(minX + 0.0011723600327968597,maxY - 0.005255943164229393,minZ + 0.030258373357355595)
    ,(minX + 0.0002274736762046814,maxY - 0.005384976044297218,maxZ - 0.033811951987445354)
    ,(maxX - 0.0134431142359972,maxY - 0.005180059932172298,maxZ - 0.010884080082178116)
    ,(maxX - 0.033787828870117664,maxY - 0.005329424981027842,maxZ - 0.00022966042160987854)
    ,(maxX - 0.0302614476531744,maxY - 0.004847868345677853,minZ + 0.0011499449610710144)
    ,(maxX - 0.00020667165517807007,maxY - 0.004890293348580599,minZ + 0.03378681745380163)
    ,(maxX - 0.0011515654623508453,maxY - 0.0050193266943097115,maxZ - 0.03028351627290249)
    ,(minX + 0.033808655105531216,maxY - 0.004945843946188688,minZ + 0.0002044886350631714)
    ,(maxX - 0.010861624032258987,maxY - 0.004827534779906273,minZ + 0.013441929593682289)
    ,(minX + 0.03468604106456041,maxY - 0.04122784733772278,minZ + 0.033558815717697144)
    ,(minX + 0.033914451487362385,maxY - 0.041333213448524475,maxZ - 0.03472032118588686)
    ,(maxX - 0.04044530005194247,maxY - 0.04129785671830177,maxZ - 0.03076378908008337)
    ,(maxX - 0.034364476799964905,maxY - 0.04125320911407471,maxZ - 0.03394827153533697)
    ,(maxX - 0.03069065511226654,maxY - 0.04120517522096634,maxZ - 0.03974655526690185)
    ,(maxX - 0.030408228747546673,maxY - 0.04116660729050636,minZ + 0.04041173937730491)
    ,(maxX - 0.03939127502962947,maxY - 0.0411539226770401,minZ + 0.030656912364065647)
    ,(minX + 0.03147818427532911,maxY - 0.033236272633075714,minZ + 0.03954096930101514)
    ,(minX + 0.031206720508635044,maxY - 0.03327333927154541,maxZ - 0.04088335996493697)
    ,(minX + 0.034267837181687355,maxY - 0.033291369676589966,maxZ - 0.03503836318850517)
    ,(minX + 0.03984131896868348,maxY - 0.03328552842140198,maxZ - 0.03150692768394947)
    ,(maxX - 0.040582869900390506,maxY - 0.0332573801279068,maxZ - 0.03123530000448227)
    ,(maxX - 0.03473791852593422,maxY - 0.033214468508958817,maxZ - 0.03429625928401947)
    ,(maxX - 0.031206604093313217,maxY - 0.03316829353570938,maxZ - 0.03986963024362922)
    ,(maxX - 0.030935133807361126,maxY - 0.03313122317194939,minZ + 0.040554699720814824)
    ,(maxX - 0.03399624954909086,maxY - 0.03311318904161453,minZ + 0.03470969945192337)
    ,(maxX - 0.03956972947344184,maxY - 0.03311903029680252,minZ + 0.031178259290754795)
    ,(minX + 0.04085446032695472,maxY - 0.0331471785902977,minZ + 0.030906626023352146)
    ,(minX + 0.035009496845304966,maxY - 0.03319009393453598,minZ + 0.03396759741008282)
    ,(minX + 0.019410474225878716,minY + 0.020503833889961243,minZ + 0.016801605001091957)
    ,(minX + 0.009459223598241806,minY + 0.020373672246932983,minZ + 0.032507372088730335)
    ,(maxX - 0.03541257046163082,minY + 0.02031419426202774,maxZ - 0.008743710815906525)
    ,(maxX - 0.0189414881169796,minY + 0.02043512463569641,maxZ - 0.017369499430060387)
    ,(maxX - 0.008990231901407242,minY + 0.02056524157524109,maxZ - 0.03307527117431164)
    ,(minX + 0.017320478335022926,minY + 0.02021842449903488,maxZ - 0.01946074701845646)
    ,(minX + 0.03302655927836895,minY + 0.02023487538099289,maxZ - 0.009509153664112091)
    ,(maxX - 0.008225221186876297,minY + 0.02066972106695175,minZ + 0.0353640653192997)
    ,(maxX - 0.016851460561156273,minY + 0.020720526576042175,minZ + 0.018892847001552582)
    ,(minX + 0.008694231510162354,minY + 0.020269230008125305,maxZ - 0.03593196161091328)
    ,(minX + 0.035881591495126486,minY + 0.020624756813049316,minZ + 0.008175786584615707)
    ,(maxX - 0.032557537779212,minY + 0.020704075694084167,minZ + 0.008941244333982468)
    ,(minX + 0.008214566856622696,minY + 0.023270338773727417,minZ + 0.03213237784802914)
    ,(maxX - 0.018073920160531998,minY + 0.023333996534347534,maxZ - 0.016406163573265076)
    ,(maxX - 0.007764074951410294,minY + 0.023468807339668274,maxZ - 0.03267789073288441)
    ,(minX + 0.03263115230947733,minY + 0.023126527667045593,maxZ - 0.008262567222118378)
    ,(maxX - 0.015908580273389816,minY + 0.023629695177078247,minZ + 0.018027253448963165)
    ,(minX + 0.01852441392838955,minY + 0.023405179381370544,minZ + 0.015860654413700104)
    ,(maxX - 0.03513853810727596,minY + 0.023208707571029663,maxZ - 0.007469546049833298)
    ,(minX + 0.016359103843569756,minY + 0.02310948073863983,maxZ - 0.018572768196463585)
    ,(maxX - 0.006971497088670731,minY + 0.023577049374580383,minZ + 0.0350920120254159)
    ,(minX + 0.007422015070915222,minY + 0.023162126541137695,maxZ - 0.03563752118498087)
    ,(minX + 0.035589066334068775,minY + 0.023530468344688416,minZ + 0.00692400336265564)
    ,(maxX - 0.032180625945329666,minY + 0.023612648248672485,minZ + 0.0077170394361019135)
    ,(minX + 0.021761823445558548,minY + 0.020728543400764465,minZ + 0.019355909898877144)
    ,(minX + 0.012772375717759132,minY + 0.020610973238945007,minZ + 0.03354368917644024)
    ,(maxX - 0.03617278253659606,minY + 0.020557239651679993,maxZ - 0.012130718678236008)
    ,(maxX - 0.021293656900525093,minY + 0.020666487514972687,maxZ - 0.019922811537981033)
    ,(maxX - 0.012304211035370827,minY + 0.02078402042388916,maxZ - 0.03411059454083443)
    ,(minX + 0.019873831421136856,minY + 0.020470723509788513,maxZ - 0.021811936050653458)
    ,(minX + 0.034061891958117485,minY + 0.020485587418079376,maxZ - 0.01282217912375927)
    ,(maxX - 0.011613138020038605,minY + 0.020878411829471588,minZ + 0.0361242787912488)
    ,(maxX - 0.019405635073781013,minY + 0.02092430740594864,minZ + 0.02124503068625927)
    ,(minX + 0.012081325054168701,minY + 0.020516619086265564,maxZ - 0.03669118043035269)
    ,(minX + 0.03664098121225834,minY + 0.02083779126405716,minZ + 0.01156378909945488)
    ,(maxX - 0.03359369467943907,minY + 0.020909443497657776,minZ + 0.012255258858203888)
    ,(minX + 0.01420576497912407,minY + 0.023059040307998657,minZ + 0.03400459885597229)
    ,(maxX - 0.022325390949845314,minY + 0.023111969232559204,maxZ - 0.021023839712142944)
    ,(maxX - 0.013754449784755707,minY + 0.02322402596473694,maxZ - 0.034551107324659824)
    ,(minX + 0.034504144452512264,minY + 0.022939488291740417,maxZ - 0.014253776520490646)
    ,(maxX - 0.020525267347693443,minY + 0.023357778787612915,minZ + 0.02227850630879402)
    ,(minX + 0.022776709869503975,minY + 0.023171141743659973,minZ + 0.020477334037423134)
    ,(maxX - 0.036511816550046206,minY + 0.023007795214653015,maxZ - 0.013594510033726692)
    ,(minX + 0.020976610481739044,minY + 0.02292531728744507,maxZ - 0.02282501384615898)
    ,(maxX - 0.013095550239086151,minY + 0.02331402897834778,minZ + 0.03646504878997803)
    ,(minX + 0.013546885922551155,minY + 0.0229690819978714,maxZ - 0.037011553067713976)
    ,(minX + 0.03696316387504339,minY + 0.023275285959243774,minZ + 0.013047976419329643)
    ,(maxX - 0.03405279852449894,minY + 0.023343607783317566,minZ + 0.013707255944609642)]
    
    # Faces
    myFaces = [(24, 0, 1),(24, 1, 2),(24, 2, 3),(24, 3, 4),(24, 4, 5)
    ,(24, 5, 6),(24, 6, 7),(24, 7, 8),(24, 8, 9),(24, 9, 10)
    ,(24, 10, 11),(11, 0, 24),(140, 12, 13, 142),(142, 13, 14, 143),(143, 14, 15, 141)
    ,(141, 15, 16, 139),(139, 16, 17, 145),(145, 17, 18, 144),(144, 18, 19, 148),(148, 19, 20, 147)
    ,(147, 20, 21, 150),(150, 21, 22, 146),(146, 22, 23, 149),(140, 0, 11, 149),(13, 12, 25, 26)
    ,(14, 13, 26, 27),(15, 14, 27, 28),(16, 15, 28, 29),(17, 16, 29, 30),(18, 17, 30, 31)
    ,(19, 18, 31, 32),(20, 19, 32, 33),(21, 20, 33, 34),(22, 21, 34, 35),(23, 22, 35, 36)
    ,(12, 23, 36, 25),(25, 49, 50, 26),(49, 37, 38, 50),(26, 50, 51, 27),(50, 38, 39, 51)
    ,(27, 51, 52, 28),(51, 39, 40, 52),(28, 52, 53, 29),(52, 40, 41, 53),(29, 53, 54, 30)
    ,(53, 41, 42, 54),(30, 54, 55, 31),(54, 42, 43, 55),(31, 55, 56, 32),(55, 43, 44, 56)
    ,(32, 56, 57, 33),(56, 44, 45, 57),(33, 57, 58, 34),(57, 45, 46, 58),(34, 58, 59, 35)
    ,(58, 46, 47, 59),(35, 59, 60, 36),(59, 47, 48, 60),(36, 60, 49, 25),(60, 48, 37, 49)
    ,(38, 37, 61, 62),(39, 38, 62, 63),(40, 39, 63, 64),(41, 40, 64, 65),(42, 41, 65, 66)
    ,(43, 42, 66, 67),(44, 43, 67, 68),(45, 44, 68, 69),(46, 45, 69, 70),(47, 46, 70, 71)
    ,(48, 47, 71, 72),(37, 48, 72, 61),(124, 125, 74, 75),(171, 170, 85, 86),(173, 172, 90, 91)
    ,(174, 173, 91, 92),(176, 175, 88, 89),(178, 177, 93, 94),(175, 179, 87, 88),(177, 174, 92, 93)
    ,(170, 180, 96, 85),(180, 181, 95, 96),(181, 178, 94, 95),(172, 176, 89, 90),(179, 171, 86, 87)
    ,(90, 89, 101, 102),(86, 85, 97, 98),(93, 92, 104, 105),(96, 95, 107, 108),(85, 96, 108, 97)
    ,(89, 88, 100, 101),(91, 90, 102, 103),(88, 87, 99, 100),(92, 91, 103, 104),(95, 94, 106, 107)
    ,(94, 93, 105, 106),(87, 86, 98, 99),(105, 104, 116, 117),(108, 107, 119, 120),(97, 108, 120, 109)
    ,(101, 100, 112, 113),(103, 102, 114, 115),(100, 99, 111, 112),(104, 103, 115, 116),(107, 106, 118, 119)
    ,(106, 105, 117, 118),(99, 98, 110, 111),(102, 101, 113, 114),(98, 97, 109, 110),(120, 119, 121)
    ,(109, 120, 121),(113, 112, 121),(115, 114, 121),(112, 111, 121),(116, 115, 121)
    ,(119, 118, 121),(118, 117, 121),(111, 110, 121),(114, 113, 121),(110, 109, 121)
    ,(117, 116, 121),(169, 158, 62, 61),(158, 159, 63, 62),(159, 160, 64, 63),(160, 161, 65, 64)
    ,(161, 162, 66, 65),(162, 163, 67, 66),(163, 164, 68, 67),(164, 165, 69, 68),(165, 166, 70, 69)
    ,(166, 167, 71, 70),(167, 168, 72, 71),(168, 169, 61, 72),(72, 138, 127, 61),(63, 129, 130, 64)
    ,(67, 133, 134, 68),(64, 130, 131, 65),(61, 127, 128, 62),(69, 135, 136, 70),(66, 132, 133, 67)
    ,(65, 131, 132, 66),(71, 137, 138, 72),(70, 136, 137, 71),(62, 128, 129, 63),(68, 134, 135, 69)
    ,(0, 140, 142, 1),(1, 142, 143, 2),(2, 143, 141, 3),(3, 141, 139, 4),(4, 139, 145, 5)
    ,(5, 145, 144, 6),(6, 144, 148, 7),(7, 148, 147, 8),(8, 147, 150, 9),(9, 150, 146, 10)
    ,(10, 146, 149, 11),(12, 140, 149, 23),(153, 154, 163, 162),(154, 155, 164, 163),(155, 156, 165, 164)
    ,(125, 151, 73, 74),(152, 124, 75, 76),(122, 152, 76, 77),(153, 122, 77, 78),(154, 153, 78, 79)
    ,(155, 154, 79, 80),(156, 155, 80, 81),(123, 156, 81, 82),(157, 123, 82, 83),(126, 157, 83, 84)
    ,(73, 151, 126, 84),(151, 125, 158, 169),(125, 124, 159, 158),(124, 152, 160, 159),(152, 122, 161, 160)
    ,(122, 153, 162, 161),(156, 123, 166, 165),(123, 157, 167, 166),(157, 126, 168, 167),(126, 151, 169, 168)
    ,(185, 189, 213, 209),(192, 193, 217, 216),(172, 173, 197, 196),(174, 177, 201, 198),(171, 179, 203, 195)
    ,(184, 183, 207, 208),(187, 192, 216, 211),(170, 171, 195, 194),(179, 175, 199, 203),(176, 172, 196, 200)
    ,(183, 188, 212, 207),(190, 184, 208, 214),(74, 73, 187, 182),(79, 78, 188, 183),(80, 79, 183, 184)
    ,(77, 76, 189, 185),(82, 81, 190, 186),(76, 75, 191, 189),(81, 80, 184, 190),(73, 84, 192, 187)
    ,(84, 83, 193, 192),(83, 82, 186, 193),(78, 77, 185, 188),(75, 74, 182, 191),(206, 211, 194, 195)
    ,(207, 212, 196, 197),(208, 207, 197, 198),(209, 213, 199, 200),(210, 214, 201, 202),(213, 215, 203, 199)
    ,(214, 208, 198, 201),(211, 216, 204, 194),(216, 217, 205, 204),(217, 210, 202, 205),(212, 209, 200, 196)
    ,(215, 206, 195, 203),(180, 170, 194, 204),(173, 174, 198, 197),(193, 186, 210, 217),(186, 190, 214, 210)
    ,(181, 180, 204, 205),(175, 176, 200, 199),(188, 185, 209, 212),(189, 191, 215, 213),(182, 187, 211, 206)
    ,(178, 181, 205, 202),(177, 178, 202, 201),(191, 182, 206, 215)]

    return (myVertex,myFaces)    
    
#----------------------------------------------
# Handle model 04
#----------------------------------------------
def handle_model_04(self,context):
    #------------------------------------
    # Mesh data
    #------------------------------------
    minX = -0.04349547624588013
    maxX = 0.04352114722132683
    minY = -0.07034946978092194
    maxY = 0
    minZ = -0.12514087557792664
    maxZ = 0.12514087557792664
    
    # Vertex
    myVertex = [(minX + 0.013302795588970184,maxY - 0.002780601382255554,minZ + 0.010707870125770569)
    ,(minX + 0.0009496212005615234,maxY - 0.002942140679806471,minZ + 0.030204586684703827)
    ,(minX,maxY - 0.003071820829063654,minZ + 0.053266048431396484)
    ,(minX + 0.010708402842283249,maxY - 0.0031348932534456253,minZ + 0.07371294498443604)
    ,(minX + 0.03020550962537527,maxY - 0.003114458406344056,minZ + 0.08606655150651932)
    ,(maxX - 0.03374953381717205,maxY - 0.003015991533175111,minZ + 0.08701672777533531)
    ,(maxX - 0.01330280676484108,maxY - 0.0028658765368163586,minZ + 0.07630888000130653)
    ,(maxX - 0.0009496286511421204,maxY - 0.0027043374720960855,minZ + 0.056812167167663574)
    ,(maxX,maxY - 0.0025746573228389025,minZ + 0.033750712871551514)
    ,(maxX - 0.010708380490541458,maxY - 0.002511584199965,minZ + 0.013303808867931366)
    ,(maxX - 0.03020548354834318,maxY - 0.0025320190470665693,minZ + 0.0009501948952674866)
    ,(minX + 0.03374955803155899,maxY - 0.0026304861530661583,minZ)
    ,(minX + 0.014472760260105133,maxY - 0.019589224830269814,minZ + 0.01180487871170044)
    ,(minX + 0.002567145973443985,maxY - 0.019744910299777985,minZ + 0.03059517592191696)
    ,(minX + 0.001651916652917862,maxY - 0.019869891926646233,minZ + 0.052821069955825806)
    ,(minX + 0.011972300708293915,maxY - 0.019930677488446236,minZ + 0.07252714410424232)
    ,(minX + 0.03076297417283058,maxY - 0.019910985603928566,minZ + 0.0844331718981266)
    ,(maxX - 0.034027633257210255,maxY - 0.019816085696220398,minZ + 0.0853489525616169)
    ,(maxX - 0.014321718364953995,maxY - 0.01967141032218933,minZ + 0.07502909749746323)
    ,(maxX - 0.002416089177131653,maxY - 0.01951572299003601,minZ + 0.056238800287246704)
    ,(maxX - 0.0015008561313152313,maxY - 0.019390743225812912,minZ + 0.03401290625333786)
    ,(maxX - 0.011821221560239792,maxY - 0.01932995393872261,minZ + 0.014306828379631042)
    ,(maxX - 0.03061189129948616,maxY - 0.01934964768588543,minZ + 0.0024007856845855713)
    ,(minX + 0.03417872078716755,maxY - 0.019444547593593597,minZ + 0.001484982669353485)
    ,(minX + 0.043508310547622386,maxY - 0.005668943747878075,minZ + 0.043508365750312805)
    ,(minX + 0.029034355655312538,maxY - 0.019612153992056847,minZ + 0.027617476880550385)
    ,(minX + 0.023084014654159546,maxY - 0.01968996599316597,minZ + 0.037008725106716156)
    ,(minX + 0.022626593708992004,maxY - 0.01975242979824543,minZ + 0.048117056488990784)
    ,(minX + 0.027784643694758415,maxY - 0.019782811403274536,minZ + 0.05796600878238678)
    ,(minX + 0.03717608004808426,maxY - 0.019772969186306,minZ + 0.06391655653715134)
    ,(maxX - 0.03873214777559042,maxY - 0.019725536927580833,minZ + 0.06437425315380096)
    ,(maxX - 0.02888327743858099,maxY - 0.019653232768177986,minZ + 0.059216469526290894)
    ,(maxX - 0.022932931780815125,maxY - 0.019575420767068863,minZ + 0.04982522130012512)
    ,(maxX - 0.022475499659776688,maxY - 0.019512956961989403,minZ + 0.0387168824672699)
    ,(maxX - 0.0276335496455431,maxY - 0.019482573494315147,minZ + 0.0288679301738739)
    ,(maxX - 0.03702498506754637,maxY - 0.019492419436573982,minZ + 0.022917382419109344)
    ,(minX + 0.038883245550096035,maxY - 0.0195398461073637,minZ + 0.022459670901298523)
    ,(minX + 0.029087782837450504,maxY - 0.03150090575218201,minZ + 0.027552828192710876)
    ,(minX + 0.023137442767620087,maxY - 0.03157871589064598,minZ + 0.03694407641887665)
    ,(minX + 0.022680018097162247,maxY - 0.03164118155837059,minZ + 0.04805241525173187)
    ,(minX + 0.027838071808218956,maxY - 0.031671565026044846,minZ + 0.05790136009454727)
    ,(minX + 0.0372295081615448,maxY - 0.03166172280907631,minZ + 0.06385190784931183)
    ,(maxX - 0.03867871919646859,maxY - 0.03161429241299629,minZ + 0.06430960446596146)
    ,(maxX - 0.028829848393797874,maxY - 0.03154198080301285,minZ + 0.05915181338787079)
    ,(maxX - 0.022879503667354584,maxY - 0.031464170664548874,minZ + 0.04976056516170502)
    ,(maxX - 0.022422071546316147,maxY - 0.03140170872211456,minZ + 0.03865223377943039)
    ,(maxX - 0.02758011966943741,maxY - 0.03137132152915001,minZ + 0.028803281486034393)
    ,(maxX - 0.03697155695408583,maxY - 0.031381167471408844,minZ + 0.022852733731269836)
    ,(minX + 0.038936673663556576,maxY - 0.03142859786748886,minZ + 0.022395022213459015)
    ,(minX + 0.029038896784186363,maxY - 0.020622700452804565,minZ + 0.027611978352069855)
    ,(minX + 0.02308855764567852,maxY - 0.02070051059126854,minZ + 0.03700323402881622)
    ,(minX + 0.02263113297522068,maxY - 0.020762978121638298,minZ + 0.04811156541109085)
    ,(minX + 0.02778918668627739,maxY - 0.020793357864022255,minZ + 0.05796051025390625)
    ,(minX + 0.037180622573941946,maxY - 0.02078351564705372,minZ + 0.0639110580086708)
    ,(maxX - 0.03872760524973273,maxY - 0.020736083388328552,minZ + 0.06436875835061073)
    ,(maxX - 0.028878736309707165,maxY - 0.020663777366280556,minZ + 0.059210970997810364)
    ,(maxX - 0.02292838878929615,maxY - 0.020585965365171432,minZ + 0.04981972277164459)
    ,(maxX - 0.022470960393548012,maxY - 0.020523501560091972,minZ + 0.038711391389369965)
    ,(maxX - 0.027629008516669273,maxY - 0.020493119955062866,minZ + 0.02886243909597397)
    ,(maxX - 0.03702044300734997,maxY - 0.020502964034676552,minZ + 0.022911883890628815)
    ,(minX + 0.03888778714463115,maxY - 0.02055039070546627,minZ + 0.022454172372817993)
    ,(minX + 0.03503026906400919,maxY - 0.0326739065349102,minZ + 0.03399384766817093)
    ,(minX + 0.03150810860097408,maxY - 0.032719966024160385,minZ + 0.039552778005599976)
    ,(minX + 0.03123734798282385,maxY - 0.03275693953037262,minZ + 0.04612809419631958)
    ,(minX + 0.034290531650185585,maxY - 0.032774921506643295,minZ + 0.051957935094833374)
    ,(minX + 0.039849569322541356,maxY - 0.0327690951526165,minZ + 0.0554802268743515)
    ,(maxX - 0.04059170465916395,maxY - 0.03274102136492729,minZ + 0.055751144886016846)
    ,(maxX - 0.03476190101355314,maxY - 0.032698217779397964,minZ + 0.05269812047481537)
    ,(maxX - 0.031239738687872887,maxY - 0.03265216201543808,minZ + 0.04713919758796692)
    ,(maxX - 0.03096897155046463,maxY - 0.032615188509225845,minZ + 0.040563881397247314)
    ,(maxX - 0.03402215428650379,maxY - 0.03259720280766487,minZ + 0.03473402559757233)
    ,(maxX - 0.03958118986338377,maxY - 0.032603029161691666,minZ + 0.031211741268634796)
    ,(minX + 0.04086008481681347,maxY - 0.032631102949380875,minZ + 0.030940808355808258)
    ,(minX + 0.03971285093575716,minY + 0.029022332280874252,minZ + 0.05597035586833954)
    ,(maxX - 0.03359287604689598,minY + 0.029201623052358627,minZ + 0.034330859780311584)
    ,(minX + 0.03072980046272278,minY + 0.029035013169050217,minZ + 0.04621553421020508)
    ,(minX + 0.031012218445539474,minY + 0.029073577374219894,minZ + 0.03935709595680237)
    ,(minX + 0.04076687735505402,minY + 0.029166262596845627,minZ + 0.03037431836128235)
    ,(minX + 0.034451283514499664,maxY - 0.03338594362139702,minZ + 0.033365122973918915)
    ,(minX + 0.030692334286868572,maxY - 0.03343509882688522,minZ + 0.039297766983509064)
    ,(minX + 0.03040337096899748,maxY - 0.03347455710172653,minZ + 0.04631512612104416)
    ,(minX + 0.03366181440651417,maxY - 0.03349374979734421,minZ + 0.05253690481185913)
    ,(minX + 0.03959457715973258,maxY - 0.033487528562545776,minZ + 0.05629599094390869)
    ,(maxX - 0.040404647355899215,maxY - 0.033457569777965546,minZ + 0.056585125625133514)
    ,(maxX - 0.03418291546404362,maxY - 0.03341188654303551,minZ + 0.05332684516906738)
    ,(maxX - 0.030423964373767376,maxY - 0.0333627350628376,minZ + 0.047394201159477234)
    ,(maxX - 0.030134993605315685,maxY - 0.03332327678799629,minZ + 0.04037684202194214)
    ,(maxX - 0.033393437042832375,maxY - 0.03330408036708832,minZ + 0.03415506333112717)
    ,(maxX - 0.03932619746774435,maxY - 0.03331030160188675,minZ + 0.030395977199077606)
    ,(minX + 0.040673027746379375,maxY - 0.03334026038646698,minZ + 0.030106835067272186)
    ,(minX + 0.030282274819910526,maxY - 0.005427400581538677,minZ + 0.08584162965416908)
    ,(minX + 0.013463903218507767,maxY - 0.005095209460705519,minZ + 0.0108589306473732)
    ,(minX + 0.010882444679737091,maxY - 0.005447734147310257,minZ + 0.07354965433478355)
    ,(minX + 0.0011723600327968597,maxY - 0.005255943164229393,minZ + 0.03025837242603302)
    ,(minX + 0.0002274736762046814,maxY - 0.005384976044297218,minZ + 0.05320477485656738)
    ,(maxX - 0.0134431142359972,maxY - 0.005180059932172298,minZ + 0.0761326476931572)
    ,(maxX - 0.033787828870117664,maxY - 0.005329424981027842,minZ + 0.08678706735372543)
    ,(maxX - 0.0302614476531744,maxY - 0.004847868345677853,minZ + 0.0011499449610710144)
    ,(maxX - 0.00020667165517807007,maxY - 0.004890293348580599,minZ + 0.03378681838512421)
    ,(maxX - 0.0011515654623508453,maxY - 0.0050193266943097115,minZ + 0.05673321336507797)
    ,(minX + 0.033808655105531216,maxY - 0.004945843946188688,minZ + 0.0002044886350631714)
    ,(maxX - 0.010861624032258987,maxY - 0.004827534779906273,minZ + 0.01344192773103714)
    ,(minX + 0.03468604106456041,minY + 0.029121622443199158,minZ + 0.033558815717697144)
    ,(minX + 0.033914451487362385,minY + 0.02901625633239746,minZ + 0.05229640752077103)
    ,(maxX - 0.04044530005194247,minY + 0.029051613062620163,minZ + 0.056252941489219666)
    ,(maxX - 0.034364476799964905,minY + 0.02909626066684723,minZ + 0.053068459033966064)
    ,(maxX - 0.03069065511226654,minY + 0.029144294559955597,minZ + 0.04727017134428024)
    ,(maxX - 0.030408228747546673,minY + 0.029182862490415573,minZ + 0.04041174054145813)
    ,(maxX - 0.03939127502962947,minY + 0.029195547103881836,minZ + 0.030656911432743073)
    ,(minX + 0.03147818427532911,maxY - 0.033236272633075714,minZ + 0.03954096883535385)
    ,(minX + 0.031206720508635044,maxY - 0.03327333927154541,minZ + 0.0461333692073822)
    ,(minX + 0.034267837181687355,maxY - 0.033291369676589966,minZ + 0.05197836458683014)
    ,(minX + 0.03984131896868348,maxY - 0.03328552842140198,minZ + 0.05550979822874069)
    ,(maxX - 0.040582869900390506,maxY - 0.0332573801279068,minZ + 0.055781424045562744)
    ,(maxX - 0.03473791852593422,maxY - 0.033214468508958817,minZ + 0.05272047221660614)
    ,(maxX - 0.031206604093313217,maxY - 0.03316829353570938,minZ + 0.04714709520339966)
    ,(maxX - 0.030935133807361126,maxY - 0.03313122317194939,minZ + 0.040554702281951904)
    ,(maxX - 0.03399624954909086,maxY - 0.03311318904161453,minZ + 0.03470969945192337)
    ,(maxX - 0.03956972947344184,maxY - 0.03311903029680252,minZ + 0.03117825835943222)
    ,(minX + 0.04085446032695472,maxY - 0.0331471785902977,minZ + 0.03090662509202957)
    ,(minX + 0.035009496845304966,maxY - 0.03319009393453598,minZ + 0.033967599272727966)
    ,(maxX - 0.03939127502962947,minY + 0.0002205297350883484,minZ + 0.0343027338385582)
    ,(maxX - 0.030408228747546673,minY + 0.007109262049198151,minZ + 0.04120940715074539)
    ,(maxX - 0.03069065511226654,minY + 0.011931635439395905,minZ + 0.046086326241493225)
    ,(maxX - 0.034364476799964905,minY + 0.01599767804145813,minZ + 0.050220295786857605)
    ,(maxX - 0.04044530005194247,minY + 0.01821787655353546,minZ + 0.05250363051891327)
    ,(minX + 0.033914451487362385,minY + 0.015395186841487885,minZ + 0.04973094165325165)
    ,(minX + 0.03468604106456041,minY + 0.0022202134132385254,minZ + 0.03640696406364441)
    ,(minX + 0.04076687735505402,minY,minZ + 0.03412361443042755)
    ,(minX + 0.031012218445539474,minY + 0.006286241114139557,minZ + 0.040540941059589386)
    ,(minX + 0.03072980046272278,minY + 0.011108621954917908,minZ + 0.04541786015033722)
    ,(maxX - 0.03359287604689598,minY + 0.002822697162628174,minZ + 0.036896318197250366)
    ,(minX + 0.03971285093575716,minY + 0.01799735426902771,minZ + 0.05232451856136322)
    ,(minX + 0.0343002462759614,minY + 0.015705399215221405,maxZ - 0.10733164101839066)
    ,(minX + 0.030871009454131126,minY + 0.011495128273963928,maxZ - 0.10745517536997795)
    ,(minX + 0.030871009454131126,minY + 0.006645478308200836,maxZ - 0.1074824407696724)
    ,(minX + 0.0343002462759614,minY + 0.0024559199810028076,maxZ - 0.10740615427494049)
    ,(minX + 0.04023986402899027,minY + 4.902482032775879e-05,maxZ - 0.10724674165248871)
    ,(maxX - 0.03991828765720129,minY + 6.973743438720703e-05,maxZ - 0.10704692453145981)
    ,(maxX - 0.03397867642343044,minY + 0.0025124847888946533,maxZ - 0.10686022788286209)
    ,(maxX - 0.030549442395567894,minY + 0.00672275573015213,maxZ - 0.1067366972565651)
    ,(maxX - 0.030549442395567894,minY + 0.011572405695915222,maxZ - 0.10670943185687065)
    ,(maxX - 0.03397867642343044,minY + 0.015761971473693848,maxZ - 0.10678572952747345)
    ,(maxX - 0.03991828765720129,minY + 0.0181688591837883,maxZ - 0.10694513842463493)
    ,(minX + 0.04023986402899027,minY + 0.018148154020309448,maxZ - 0.10714496672153473)
    ,(minX + 0.013302795588970184,maxY - 0.002780601382255554,maxZ - 0.010707870125770569)
    ,(minX + 0.0009496212005615234,maxY - 0.002942140679806471,maxZ - 0.030204586684703827)
    ,(minX,maxY - 0.003071820829063654,maxZ - 0.053266048431396484)
    ,(minX + 0.010708402842283249,maxY - 0.0031348932534456253,maxZ - 0.07371294498443604)
    ,(minX + 0.03020550962537527,maxY - 0.003114458406344056,maxZ - 0.08606655150651932)
    ,(maxX - 0.03374953381717205,maxY - 0.003015991533175111,maxZ - 0.08701672777533531)
    ,(maxX - 0.01330280676484108,maxY - 0.0028658765368163586,maxZ - 0.07630888000130653)
    ,(maxX - 0.0009496286511421204,maxY - 0.0027043374720960855,maxZ - 0.056812167167663574)
    ,(maxX,maxY - 0.0025746573228389025,maxZ - 0.033750712871551514)
    ,(maxX - 0.010708380490541458,maxY - 0.002511584199965,maxZ - 0.013303808867931366)
    ,(maxX - 0.03020548354834318,maxY - 0.0025320190470665693,maxZ - 0.0009501948952674866)
    ,(minX + 0.03374955803155899,maxY - 0.0026304861530661583,maxZ)
    ,(minX + 0.014472760260105133,maxY - 0.019589224830269814,maxZ - 0.01180487871170044)
    ,(minX + 0.002567145973443985,maxY - 0.019744910299777985,maxZ - 0.03059517592191696)
    ,(minX + 0.001651916652917862,maxY - 0.019869891926646233,maxZ - 0.052821069955825806)
    ,(minX + 0.011972300708293915,maxY - 0.019930677488446236,maxZ - 0.07252714410424232)
    ,(minX + 0.03076297417283058,maxY - 0.019910985603928566,maxZ - 0.0844331718981266)
    ,(maxX - 0.034027633257210255,maxY - 0.019816085696220398,maxZ - 0.0853489525616169)
    ,(maxX - 0.014321718364953995,maxY - 0.01967141032218933,maxZ - 0.07502909749746323)
    ,(maxX - 0.002416089177131653,maxY - 0.01951572299003601,maxZ - 0.056238800287246704)
    ,(maxX - 0.0015008561313152313,maxY - 0.019390743225812912,maxZ - 0.03401290625333786)
    ,(maxX - 0.011821221560239792,maxY - 0.01932995393872261,maxZ - 0.014306828379631042)
    ,(maxX - 0.03061189129948616,maxY - 0.01934964768588543,maxZ - 0.0024007856845855713)
    ,(minX + 0.03417872078716755,maxY - 0.019444547593593597,maxZ - 0.001484982669353485)
    ,(minX + 0.043508310547622386,maxY - 0.005668943747878075,maxZ - 0.043508365750312805)
    ,(minX + 0.029034355655312538,maxY - 0.019612153992056847,maxZ - 0.027617476880550385)
    ,(minX + 0.023084014654159546,maxY - 0.01968996599316597,maxZ - 0.037008725106716156)
    ,(minX + 0.022626593708992004,maxY - 0.01975242979824543,maxZ - 0.048117056488990784)
    ,(minX + 0.027784643694758415,maxY - 0.019782811403274536,maxZ - 0.05796600878238678)
    ,(minX + 0.03717608004808426,maxY - 0.019772969186306,maxZ - 0.06391655653715134)
    ,(maxX - 0.03873214777559042,maxY - 0.019725536927580833,maxZ - 0.06437425315380096)
    ,(maxX - 0.02888327743858099,maxY - 0.019653232768177986,maxZ - 0.059216469526290894)
    ,(maxX - 0.022932931780815125,maxY - 0.019575420767068863,maxZ - 0.04982522130012512)
    ,(maxX - 0.022475499659776688,maxY - 0.019512956961989403,maxZ - 0.0387168824672699)
    ,(maxX - 0.0276335496455431,maxY - 0.019482573494315147,maxZ - 0.0288679301738739)
    ,(maxX - 0.03702498506754637,maxY - 0.019492419436573982,maxZ - 0.022917382419109344)
    ,(minX + 0.038883245550096035,maxY - 0.0195398461073637,maxZ - 0.022459670901298523)
    ,(minX + 0.029087782837450504,maxY - 0.03150090575218201,maxZ - 0.027552828192710876)
    ,(minX + 0.023137442767620087,maxY - 0.03157871589064598,maxZ - 0.03694407641887665)
    ,(minX + 0.022680018097162247,maxY - 0.03164118155837059,maxZ - 0.04805241525173187)
    ,(minX + 0.027838071808218956,maxY - 0.031671565026044846,maxZ - 0.05790136009454727)
    ,(minX + 0.0372295081615448,maxY - 0.03166172280907631,maxZ - 0.06385190784931183)
    ,(maxX - 0.03867871919646859,maxY - 0.03161429241299629,maxZ - 0.06430960446596146)
    ,(maxX - 0.028829848393797874,maxY - 0.03154198080301285,maxZ - 0.05915181338787079)
    ,(maxX - 0.022879503667354584,maxY - 0.031464170664548874,maxZ - 0.04976056516170502)
    ,(maxX - 0.022422071546316147,maxY - 0.03140170872211456,maxZ - 0.03865223377943039)
    ,(maxX - 0.02758011966943741,maxY - 0.03137132152915001,maxZ - 0.028803281486034393)
    ,(maxX - 0.03697155695408583,maxY - 0.031381167471408844,maxZ - 0.022852733731269836)
    ,(minX + 0.038936673663556576,maxY - 0.03142859786748886,maxZ - 0.022395022213459015)
    ,(minX + 0.029038896784186363,maxY - 0.020622700452804565,maxZ - 0.027611978352069855)
    ,(minX + 0.02308855764567852,maxY - 0.02070051059126854,maxZ - 0.03700323402881622)
    ,(minX + 0.02263113297522068,maxY - 0.020762978121638298,maxZ - 0.04811156541109085)
    ,(minX + 0.02778918668627739,maxY - 0.020793357864022255,maxZ - 0.05796051025390625)
    ,(minX + 0.037180622573941946,maxY - 0.02078351564705372,maxZ - 0.0639110580086708)
    ,(maxX - 0.03872760524973273,maxY - 0.020736083388328552,maxZ - 0.06436875835061073)
    ,(maxX - 0.028878736309707165,maxY - 0.020663777366280556,maxZ - 0.059210970997810364)
    ,(maxX - 0.02292838878929615,maxY - 0.020585965365171432,maxZ - 0.04981972277164459)
    ,(maxX - 0.022470960393548012,maxY - 0.020523501560091972,maxZ - 0.038711391389369965)
    ,(maxX - 0.027629008516669273,maxY - 0.020493119955062866,maxZ - 0.02886243909597397)
    ,(maxX - 0.03702044300734997,maxY - 0.020502964034676552,maxZ - 0.022911883890628815)
    ,(minX + 0.03888778714463115,maxY - 0.02055039070546627,maxZ - 0.022454172372817993)
    ,(minX + 0.03503026906400919,maxY - 0.0326739065349102,maxZ - 0.03399384766817093)
    ,(minX + 0.03150810860097408,maxY - 0.032719966024160385,maxZ - 0.039552778005599976)
    ,(minX + 0.03123734798282385,maxY - 0.03275693953037262,maxZ - 0.04612809419631958)
    ,(minX + 0.034290531650185585,maxY - 0.032774921506643295,maxZ - 0.051957935094833374)
    ,(minX + 0.039849569322541356,maxY - 0.0327690951526165,maxZ - 0.0554802268743515)
    ,(maxX - 0.04059170465916395,maxY - 0.03274102136492729,maxZ - 0.055751144886016846)
    ,(maxX - 0.03476190101355314,maxY - 0.032698217779397964,maxZ - 0.05269812047481537)
    ,(maxX - 0.031239738687872887,maxY - 0.03265216201543808,maxZ - 0.04713919758796692)
    ,(maxX - 0.03096897155046463,maxY - 0.032615188509225845,maxZ - 0.040563881397247314)
    ,(maxX - 0.03402215428650379,maxY - 0.03259720280766487,maxZ - 0.03473402559757233)
    ,(maxX - 0.03958118986338377,maxY - 0.032603029161691666,maxZ - 0.031211741268634796)
    ,(minX + 0.04086008481681347,maxY - 0.032631102949380875,maxZ - 0.030940808355808258)
    ,(minX + 0.03971285093575716,minY + 0.029022332280874252,maxZ - 0.05597035586833954)
    ,(maxX - 0.03359287604689598,minY + 0.029201623052358627,maxZ - 0.034330859780311584)
    ,(minX + 0.03072980046272278,minY + 0.029035013169050217,maxZ - 0.04621553421020508)
    ,(minX + 0.031012218445539474,minY + 0.029073577374219894,maxZ - 0.03935709595680237)
    ,(minX + 0.04076687735505402,minY + 0.029166262596845627,maxZ - 0.03037431836128235)
    ,(minX + 0.034451283514499664,maxY - 0.03338594362139702,maxZ - 0.033365122973918915)
    ,(minX + 0.030692334286868572,maxY - 0.03343509882688522,maxZ - 0.039297766983509064)
    ,(minX + 0.03040337096899748,maxY - 0.03347455710172653,maxZ - 0.04631512612104416)
    ,(minX + 0.03366181440651417,maxY - 0.03349374979734421,maxZ - 0.05253690481185913)
    ,(minX + 0.03959457715973258,maxY - 0.033487528562545776,maxZ - 0.05629599094390869)
    ,(maxX - 0.040404647355899215,maxY - 0.033457569777965546,maxZ - 0.056585125625133514)
    ,(maxX - 0.03418291546404362,maxY - 0.03341188654303551,maxZ - 0.05332684516906738)
    ,(maxX - 0.030423964373767376,maxY - 0.0333627350628376,maxZ - 0.047394201159477234)
    ,(maxX - 0.030134993605315685,maxY - 0.03332327678799629,maxZ - 0.04037684202194214)
    ,(maxX - 0.033393437042832375,maxY - 0.03330408036708832,maxZ - 0.03415506333112717)
    ,(maxX - 0.03932619746774435,maxY - 0.03331030160188675,maxZ - 0.030395977199077606)
    ,(minX + 0.040673027746379375,maxY - 0.03334026038646698,maxZ - 0.030106835067272186)
    ,(minX + 0.030282274819910526,maxY - 0.005427400581538677,maxZ - 0.08584162965416908)
    ,(minX + 0.013463903218507767,maxY - 0.005095209460705519,maxZ - 0.0108589306473732)
    ,(minX + 0.010882444679737091,maxY - 0.005447734147310257,maxZ - 0.07354965433478355)
    ,(minX + 0.0011723600327968597,maxY - 0.005255943164229393,maxZ - 0.03025837242603302)
    ,(minX + 0.0002274736762046814,maxY - 0.005384976044297218,maxZ - 0.05320477485656738)
    ,(maxX - 0.0134431142359972,maxY - 0.005180059932172298,maxZ - 0.0761326476931572)
    ,(maxX - 0.033787828870117664,maxY - 0.005329424981027842,maxZ - 0.08678706735372543)
    ,(maxX - 0.0302614476531744,maxY - 0.004847868345677853,maxZ - 0.0011499449610710144)
    ,(maxX - 0.00020667165517807007,maxY - 0.004890293348580599,maxZ - 0.03378681838512421)
    ,(maxX - 0.0011515654623508453,maxY - 0.0050193266943097115,maxZ - 0.05673321336507797)
    ,(minX + 0.033808655105531216,maxY - 0.004945843946188688,maxZ - 0.0002044886350631714)
    ,(maxX - 0.010861624032258987,maxY - 0.004827534779906273,maxZ - 0.01344192773103714)
    ,(minX + 0.03468604106456041,minY + 0.029121622443199158,maxZ - 0.033558815717697144)
    ,(minX + 0.033914451487362385,minY + 0.02901625633239746,maxZ - 0.05229640752077103)
    ,(maxX - 0.04044530005194247,minY + 0.029051613062620163,maxZ - 0.056252941489219666)
    ,(maxX - 0.034364476799964905,minY + 0.02909626066684723,maxZ - 0.053068459033966064)
    ,(maxX - 0.03069065511226654,minY + 0.029144294559955597,maxZ - 0.04727017134428024)
    ,(maxX - 0.030408228747546673,minY + 0.029182862490415573,maxZ - 0.04041174054145813)
    ,(maxX - 0.03939127502962947,minY + 0.029195547103881836,maxZ - 0.030656911432743073)
    ,(minX + 0.03147818427532911,maxY - 0.033236272633075714,maxZ - 0.03954096883535385)
    ,(minX + 0.031206720508635044,maxY - 0.03327333927154541,maxZ - 0.0461333692073822)
    ,(minX + 0.034267837181687355,maxY - 0.033291369676589966,maxZ - 0.05197836458683014)
    ,(minX + 0.03984131896868348,maxY - 0.03328552842140198,maxZ - 0.05550979822874069)
    ,(maxX - 0.040582869900390506,maxY - 0.0332573801279068,maxZ - 0.055781424045562744)
    ,(maxX - 0.03473791852593422,maxY - 0.033214468508958817,maxZ - 0.05272047221660614)
    ,(maxX - 0.031206604093313217,maxY - 0.03316829353570938,maxZ - 0.04714709520339966)
    ,(maxX - 0.030935133807361126,maxY - 0.03313122317194939,maxZ - 0.040554702281951904)
    ,(maxX - 0.03399624954909086,maxY - 0.03311318904161453,maxZ - 0.03470969945192337)
    ,(maxX - 0.03956972947344184,maxY - 0.03311903029680252,maxZ - 0.03117825835943222)
    ,(minX + 0.04085446032695472,maxY - 0.0331471785902977,maxZ - 0.03090662509202957)
    ,(minX + 0.035009496845304966,maxY - 0.03319009393453598,maxZ - 0.033967599272727966)
    ,(maxX - 0.03939127502962947,minY + 0.0002205297350883484,maxZ - 0.0343027338385582)
    ,(maxX - 0.030408228747546673,minY + 0.007109262049198151,maxZ - 0.04120940715074539)
    ,(maxX - 0.03069065511226654,minY + 0.011931635439395905,maxZ - 0.046086326241493225)
    ,(maxX - 0.034364476799964905,minY + 0.01599767804145813,maxZ - 0.050220295786857605)
    ,(maxX - 0.04044530005194247,minY + 0.01821787655353546,maxZ - 0.05250363051891327)
    ,(minX + 0.033914451487362385,minY + 0.015395186841487885,maxZ - 0.04973094165325165)
    ,(minX + 0.03468604106456041,minY + 0.0022202134132385254,maxZ - 0.03640696406364441)
    ,(minX + 0.04076687735505402,minY,maxZ - 0.03412361443042755)
    ,(minX + 0.031012218445539474,minY + 0.006286241114139557,maxZ - 0.040540941059589386)
    ,(minX + 0.03072980046272278,minY + 0.011108621954917908,maxZ - 0.04541786015033722)
    ,(maxX - 0.03359287604689598,minY + 0.002822697162628174,maxZ - 0.036896318197250366)
    ,(minX + 0.03971285093575716,minY + 0.01799735426902771,maxZ - 0.05232451856136322)
    ,(minX + 0.0343002462759614,minY + 0.015705399215221405,minZ + 0.10733164101839066)
    ,(minX + 0.030871009454131126,minY + 0.011495128273963928,minZ + 0.10745517536997795)
    ,(minX + 0.030871009454131126,minY + 0.006645478308200836,minZ + 0.1074824407696724)
    ,(minX + 0.0343002462759614,minY + 0.0024559199810028076,minZ + 0.10740615427494049)
    ,(minX + 0.04023986402899027,minY + 4.902482032775879e-05,minZ + 0.10724674165248871)
    ,(maxX - 0.03991828765720129,minY + 6.973743438720703e-05,minZ + 0.10704692453145981)
    ,(maxX - 0.03397867642343044,minY + 0.0025124847888946533,minZ + 0.10686022788286209)
    ,(maxX - 0.030549442395567894,minY + 0.00672275573015213,minZ + 0.1067366972565651)
    ,(maxX - 0.030549442395567894,minY + 0.011572405695915222,minZ + 0.10670943185687065)
    ,(maxX - 0.03397867642343044,minY + 0.015761971473693848,minZ + 0.10678572952747345)
    ,(maxX - 0.03991828765720129,minY + 0.0181688591837883,minZ + 0.10694513842463493)
    ,(minX + 0.04023986402899027,minY + 0.018148154020309448,minZ + 0.10714496672153473)]
    
    # Faces
    myFaces = [(24, 0, 1),(24, 1, 2),(24, 2, 3),(24, 3, 4),(24, 4, 5)
    ,(24, 5, 6),(24, 6, 7),(24, 7, 8),(24, 8, 9),(24, 9, 10)
    ,(24, 10, 11),(11, 0, 24),(91, 12, 13, 93),(93, 13, 14, 94),(94, 14, 15, 92)
    ,(92, 15, 16, 90),(90, 16, 17, 96),(96, 17, 18, 95),(95, 18, 19, 99),(99, 19, 20, 98)
    ,(98, 20, 21, 101),(101, 21, 22, 97),(97, 22, 23, 100),(91, 0, 11, 100),(13, 12, 25, 26)
    ,(14, 13, 26, 27),(15, 14, 27, 28),(16, 15, 28, 29),(17, 16, 29, 30),(18, 17, 30, 31)
    ,(19, 18, 31, 32),(20, 19, 32, 33),(21, 20, 33, 34),(22, 21, 34, 35),(23, 22, 35, 36)
    ,(12, 23, 36, 25),(25, 49, 50, 26),(49, 37, 38, 50),(26, 50, 51, 27),(50, 38, 39, 51)
    ,(27, 51, 52, 28),(51, 39, 40, 52),(28, 52, 53, 29),(52, 40, 41, 53),(29, 53, 54, 30)
    ,(53, 41, 42, 54),(30, 54, 55, 31),(54, 42, 43, 55),(31, 55, 56, 32),(55, 43, 44, 56)
    ,(32, 56, 57, 33),(56, 44, 45, 57),(33, 57, 58, 34),(57, 45, 46, 58),(34, 58, 59, 35)
    ,(58, 46, 47, 59),(35, 59, 60, 36),(59, 47, 48, 60),(36, 60, 49, 25),(60, 48, 37, 49)
    ,(38, 37, 61, 62),(39, 38, 62, 63),(40, 39, 63, 64),(41, 40, 64, 65),(42, 41, 65, 66)
    ,(43, 42, 66, 67),(44, 43, 67, 68),(45, 44, 68, 69),(46, 45, 69, 70),(47, 46, 70, 71)
    ,(48, 47, 71, 72),(37, 48, 72, 61),(120, 109, 62, 61),(109, 110, 63, 62),(110, 111, 64, 63)
    ,(111, 112, 65, 64),(112, 113, 66, 65),(113, 114, 67, 66),(114, 115, 68, 67),(115, 116, 69, 68)
    ,(116, 117, 70, 69),(117, 118, 71, 70),(118, 119, 72, 71),(119, 120, 61, 72),(72, 89, 78, 61)
    ,(63, 80, 81, 64),(67, 84, 85, 68),(64, 81, 82, 65),(61, 78, 79, 62),(69, 86, 87, 70)
    ,(66, 83, 84, 67),(65, 82, 83, 66),(71, 88, 89, 72),(70, 87, 88, 71),(62, 79, 80, 63)
    ,(68, 85, 86, 69),(0, 91, 93, 1),(1, 93, 94, 2),(2, 94, 92, 3),(3, 92, 90, 4)
    ,(4, 90, 96, 5),(5, 96, 95, 6),(6, 95, 99, 7),(7, 99, 98, 8),(8, 98, 101, 9)
    ,(9, 101, 97, 10),(10, 97, 100, 11),(12, 91, 100, 23),(104, 105, 114, 113),(105, 106, 115, 114)
    ,(106, 107, 116, 115),(102, 76, 109, 120),(76, 75, 110, 109),(75, 103, 111, 110),(103, 73, 112, 111)
    ,(73, 104, 113, 112),(107, 74, 117, 116),(74, 108, 118, 117),(108, 77, 119, 118),(77, 102, 120, 119)
    ,(74, 107, 122, 131),(107, 106, 123, 122),(104, 73, 132, 125),(106, 105, 124, 123),(75, 76, 129, 130)
    ,(73, 103, 126, 132),(105, 104, 125, 124),(102, 77, 128, 127),(103, 75, 130, 126),(77, 108, 121, 128)
    ,(76, 102, 127, 129),(108, 74, 131, 121),(126, 130, 134, 133),(130, 129, 135, 134),(129, 127, 136, 135)
    ,(127, 128, 137, 136),(128, 121, 138, 137),(121, 131, 139, 138),(131, 122, 140, 139),(122, 123, 141, 140)
    ,(123, 124, 142, 141),(124, 125, 143, 142),(125, 132, 144, 143),(132, 126, 133, 144),(169, 146, 145)
    ,(169, 147, 146),(169, 148, 147),(169, 149, 148),(169, 150, 149),(169, 151, 150)
    ,(169, 152, 151),(169, 153, 152),(169, 154, 153),(169, 155, 154),(169, 156, 155)
    ,(156, 169, 145),(236, 238, 158, 157),(238, 239, 159, 158),(239, 237, 160, 159),(237, 235, 161, 160)
    ,(235, 241, 162, 161),(241, 240, 163, 162),(240, 244, 164, 163),(244, 243, 165, 164),(243, 246, 166, 165)
    ,(246, 242, 167, 166),(242, 245, 168, 167),(236, 245, 156, 145),(158, 171, 170, 157),(159, 172, 171, 158)
    ,(160, 173, 172, 159),(161, 174, 173, 160),(162, 175, 174, 161),(163, 176, 175, 162),(164, 177, 176, 163)
    ,(165, 178, 177, 164),(166, 179, 178, 165),(167, 180, 179, 166),(168, 181, 180, 167),(157, 170, 181, 168)
    ,(170, 171, 195, 194),(194, 195, 183, 182),(171, 172, 196, 195),(195, 196, 184, 183),(172, 173, 197, 196)
    ,(196, 197, 185, 184),(173, 174, 198, 197),(197, 198, 186, 185),(174, 175, 199, 198),(198, 199, 187, 186)
    ,(175, 176, 200, 199),(199, 200, 188, 187),(176, 177, 201, 200),(200, 201, 189, 188),(177, 178, 202, 201)
    ,(201, 202, 190, 189),(178, 179, 203, 202),(202, 203, 191, 190),(179, 180, 204, 203),(203, 204, 192, 191)
    ,(180, 181, 205, 204),(204, 205, 193, 192),(181, 170, 194, 205),(205, 194, 182, 193),(183, 207, 206, 182)
    ,(184, 208, 207, 183),(185, 209, 208, 184),(186, 210, 209, 185),(187, 211, 210, 186),(188, 212, 211, 187)
    ,(189, 213, 212, 188),(190, 214, 213, 189),(191, 215, 214, 190),(192, 216, 215, 191),(193, 217, 216, 192)
    ,(182, 206, 217, 193),(265, 206, 207, 254),(254, 207, 208, 255),(255, 208, 209, 256),(256, 209, 210, 257)
    ,(257, 210, 211, 258),(258, 211, 212, 259),(259, 212, 213, 260),(260, 213, 214, 261),(261, 214, 215, 262)
    ,(262, 215, 216, 263),(263, 216, 217, 264),(264, 217, 206, 265),(217, 206, 223, 234),(208, 209, 226, 225)
    ,(212, 213, 230, 229),(209, 210, 227, 226),(206, 207, 224, 223),(214, 215, 232, 231),(211, 212, 229, 228)
    ,(210, 211, 228, 227),(216, 217, 234, 233),(215, 216, 233, 232),(207, 208, 225, 224),(213, 214, 231, 230)
    ,(145, 146, 238, 236),(146, 147, 239, 238),(147, 148, 237, 239),(148, 149, 235, 237),(149, 150, 241, 235)
    ,(150, 151, 240, 241),(151, 152, 244, 240),(152, 153, 243, 244),(153, 154, 246, 243),(154, 155, 242, 246)
    ,(155, 156, 245, 242),(157, 168, 245, 236),(249, 258, 259, 250),(250, 259, 260, 251),(251, 260, 261, 252)
    ,(247, 265, 254, 221),(221, 254, 255, 220),(220, 255, 256, 248),(248, 256, 257, 218),(218, 257, 258, 249)
    ,(252, 261, 262, 219),(219, 262, 263, 253),(253, 263, 264, 222),(222, 264, 265, 247),(219, 276, 267, 252)
    ,(252, 267, 268, 251),(249, 270, 277, 218),(251, 268, 269, 250),(220, 275, 274, 221),(218, 277, 271, 248)
    ,(250, 269, 270, 249),(247, 272, 273, 222),(248, 271, 275, 220),(222, 273, 266, 253),(221, 274, 272, 247)
    ,(253, 266, 276, 219),(271, 278, 279, 275),(275, 279, 280, 274),(274, 280, 281, 272),(272, 281, 282, 273)
    ,(273, 282, 283, 266),(266, 283, 284, 276),(276, 284, 285, 267),(267, 285, 286, 268),(268, 286, 287, 269)
    ,(269, 287, 288, 270),(270, 288, 289, 277),(277, 289, 278, 271)]    
        
    return (myVertex,myFaces)    
#------------------------------------------------------------------------------
# Create control box
#
# objName: Object name
# x: size x axis
# y: size y axis
# z: size z axis
# tube: True create a tube, False only sides
#------------------------------------------------------------------------------
def create_control_box(objName,x,y,z,tube=True):

    myVertex = [(-x/2, 0, 0.0)
                ,(-x/2, y, 0.0)
                ,(x/2, y, 0.0)
                ,(x/2, 0, 0.0)
                ,(-x/2, 0, z)
                ,(-x/2, y, z)
                ,(x/2, y, z)
                ,(x/2, 0, z)]
    
    if tube == True:
        myFaces = [(0,1,2,3),(0,1,5,4),(2,6,7,3),(5,6,7,4)]
    else:    
        myFaces = [(0,4,5,1),(2,6,7,3)]
        
    mesh = bpy.data.meshes.new(objName)
    myobject = bpy.data.objects.new(objName, mesh)
    
    myobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myobject)
    
    mesh.from_pydata(myVertex, [], myFaces)
    mesh.update(calc_edges=True)
   
    return myobject


#----------------------------------------------
# Code to run alone the script
#----------------------------------------------
if __name__ == "__main__":
    create_mesh(0)
    print("Executed")
