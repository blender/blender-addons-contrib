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
# File: curtain_maker.py
# Automatic generation of curtains
# Author: Antonio Vazquez (antonioya)
#
#----------------------------------------------------------
import bpy
import colorsys
import copy
import math
from tools import *

#------------------------------------------------------------------
# Define UI class
# Japanese curtains
#------------------------------------------------------------------
class JAPAN(bpy.types.Operator):
    bl_idname = "mesh.archimesh_japan"
    bl_label = "Japanese curtains"
    bl_description = "Japanese curtains Generator"
    bl_category = 'Archimesh'
    bl_options = {'REGISTER', 'UNDO'}
    
    width= bpy.props.FloatProperty(name='Width',min=0.30,max= 4, default= 1,precision=3, description='Total width')
    height= bpy.props.FloatProperty(name='Height',min=0.20,max= 50, default= 1.8,precision=3, description='Total height')
    num= bpy.props.IntProperty(name='Rails',min=2,max= 5, default= 2, description='Number total of rails')
    palnum= bpy.props.IntProperty(name='Panels',min=1,max= 2, default= 1, description='Panels by rail')
    
    open01 = bpy.props.FloatProperty(name='Position 01', min=0, max= 1, default= 0,precision=3, description='Position of the panel')
    open02 = bpy.props.FloatProperty(name='Position 02', min=0, max= 1, default= 0,precision=3, description='Position of the panel')
    open03 = bpy.props.FloatProperty(name='Position 03', min=0, max= 1, default= 0,precision=3, description='Position of the panel')
    open04 = bpy.props.FloatProperty(name='Position 04', min=0, max= 1, default= 0,precision=3, description='Position of the panel')
    open05 = bpy.props.FloatProperty(name='Position 05', min=0, max= 1, default= 0,precision=3, description='Position of the panel')

    # Materials        
    crt_mat = bpy.props.BoolProperty(name = "Create default Cycles materials",description="Create default materials for Cycles render.",default = True)

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
            row.prop(self,'width')
            row.prop(self,'height')
            row=box.row()
            row.prop(self,'num')
            row.prop(self,'palnum')
            
            if (self.num >= 1):
                row=box.row()
                row.prop(self,'open01',slider=True)
            if (self.num >= 2):
                row=box.row()
                row.prop(self,'open02',slider=True)
            if (self.num >= 3):
                row=box.row()
                row.prop(self,'open03',slider=True)
            if (self.num >= 4):
                row=box.row()
                row.prop(self,'open04',slider=True)
            if (self.num >= 5):
                row=box.row()
                row.prop(self,'open05',slider=True)

            box=layout.box()
            box.prop(self,'crt_mat')
            if (self.crt_mat):
                box.label("* Remember to verify fabric texture folder")
        else:
            row=layout.row()
            row.label("Warning: Operator does not work in local view mode", icon='ERROR')

    #-----------------------------------------------------
    # Execute
    #-----------------------------------------------------
    def execute(self, context):
        if (bpy.context.mode == "OBJECT"):
            create_japan_mesh(self,context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}

#------------------------------------------------------------------------------
# Generate mesh data
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_japan_mesh(self,context):
    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    bpy.ops.object.select_all(False)
    # Create units
    generate_japan(self,context)

    return
#------------------------------------------------------------------
# Define UI class
# Roller curtains
#------------------------------------------------------------------
class ROLLER(bpy.types.Operator):
    bl_idname = "mesh.archimesh_roller"
    bl_label = "Roller curtains"
    bl_description = "Roller_curtains Generator"
    bl_category = 'Archimesh'
    bl_options = {'REGISTER', 'UNDO'}
    
    width= bpy.props.FloatProperty(name='Width',min=0.30,max= 4, default= 1,precision=3, description='Total width')
    height= bpy.props.FloatProperty(name='Height',min=0.01,max= 50, default= 1.7,precision=3, description='Total height')

    # Materials        
    crt_mat = bpy.props.BoolProperty(name = "Create default Cycles materials",description="Create default materials for Cycles render.",default = True)

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
            row.prop(self,'width')
            row.prop(self,'height')

            box=layout.box()
            box.prop(self,'crt_mat')
            if (self.crt_mat):
                box.label("* Remember to verify fabric texture folder")
        else:
            row=layout.row()
            row.label("Warning: Operator does not work in local view mode", icon='ERROR')

    #-----------------------------------------------------
    # Execute
    #-----------------------------------------------------
    def execute(self, context):
        if (bpy.context.mode == "OBJECT"):
            create_roller_mesh(self,context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}

#------------------------------------------------------------------
# Define UI class
# Venetian curtains
#------------------------------------------------------------------
class VENETIAN(bpy.types.Operator):
    bl_idname = "mesh.archimesh_venetian"
    bl_label = "Venetian blind"
    bl_description = "Venetian blind Generator"
    bl_category = 'Archimesh'
    bl_options = {'REGISTER', 'UNDO'}
    
    width= bpy.props.FloatProperty(name='Width',min=0.30,max= 4, default= 1,precision=3, description='Total width')
    height= bpy.props.FloatProperty(name='Height',min=0.20,max= 10, default= 1.7,precision=3, description='Total height')
    depth= bpy.props.FloatProperty(name='Slat depth',min=0.02,max= 0.30, default= 0.04,precision=3, description='Slat depth')
    angle= bpy.props.FloatProperty(name='Angle',min=0,max= 85, default= 0,precision=1, description='Angle of the slats')
    ratio= bpy.props.IntProperty(name='Extend',min=0,max= 100, default= 100, description='% of extension (100 full extend)')

    # Materials        
    crt_mat = bpy.props.BoolProperty(name = "Create default Cycles materials",description="Create default materials for Cycles render.",default = True)
    hue= bpy.props.FloatProperty(name='H',min=0,max= 1, default= 0.658,precision=3, description='Color Hue')
    saturation= bpy.props.FloatProperty(name='S',min=0,max= 1, default= 0.620,precision=3, description='Color Saturation')
    value= bpy.props.FloatProperty(name='V',min=0,max= 1, default= 0.655,precision=3, description='Color Value')

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
            row.prop(self,'width')
            row.prop(self,'height')
            row.prop(self,'depth')
            row=box.row()
            row.prop(self,'angle',slider=True)
            row.prop(self,'ratio',slider=True)

            box=layout.box()
            box.prop(self,'crt_mat')
            if (self.crt_mat):
                row=box.row()
                row.prop(self,'hue',slider=True)
                row=box.row()
                row.prop(self,'saturation',slider=True)
                row=box.row()
                row.prop(self,'value',slider=True)
        else:
            row=layout.row()
            row.label("Warning: Operator does not work in local view mode", icon='ERROR')

    #-----------------------------------------------------
    # Execute
    #-----------------------------------------------------
    def execute(self, context):
        if (bpy.context.mode == "OBJECT"):
            create_venetian_mesh(self,context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}

#------------------------------------------------------------------------------
# Generate mesh data
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_venetian_mesh(self,context):
    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    bpy.ops.object.select_all(False)
    generate_venetian(self,context)

    return
#------------------------------------------------------------------------------
# Generate mesh data
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_roller_mesh(self,context):
    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    bpy.ops.object.select_all(False)
    generate_roller(self,context)

    return
#------------------------------------------------------------------------------
# Generate japanese curtains
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def generate_japan(self,context):

    Support = []
    Panel = []

    location = bpy.context.scene.cursor_location
    myLoc = copy.copy(location) # copy location to keep 3D cursor position

    #------------------ 
    # Rail
    #------------------ 
    myRail = create_japan_rail("Rail"
                       ,self.width - 0.02,self.num
                       ,myLoc.x,myLoc.y,myLoc.z
                       ,self.crt_mat)
    # refine
    remove_doubles(myRail)
    set_normals(myRail)
     
    #--------------------------------------------------------------------------------
    # Supports
    #--------------------------------------------------------------------------------
    width = (self.width / self.num) / self.palnum
    # left
    posX = 0.01 + 0.01
    posY = 0.006 
    posZ = 0.006
    for x in range(self.num):
        mySup = create_japan_support("Support_" + str(x) + ".L"
                       ,width - 0.02 # subtract 2 cm
                       ,0,0,0
                       ,self.crt_mat)
        Support.extend([mySup])
        mySup.parent = myRail
        
        if (x == 0): f = self.open01
        if (x == 1): f = self.open02
        if (x == 2): f = self.open03
        if (x == 3): f = self.open04
        if (x == 4): f = self.open05
              
        if (self.palnum == 1):
            maxPos = ((self.width / self.palnum) - width - 0.02) * f
        else:    
            maxPos = ((self.width / self.palnum) - width) * f
 
        mySup.location.x = posX + maxPos
        mySup.location.y = -posY
        mySup.location.z = posZ
        
        posY = posY + 0.015
    # Right
    if (self.palnum > 1):
        posX = self.width - width #+ 0.01
        posY = 0.006 
        posZ = 0.006 
        for x in range(self.num):
            mySup = create_japan_support("Support_" + str(x) + ".R"
                           ,width - 0.02 # subtract 2 cm
                           ,0,0,0
                           ,self.crt_mat)
            Support.extend([mySup])
            mySup.parent = myRail
        
            if (x == 0): f = self.open01
            if (x == 1): f = self.open02
            if (x == 2): f = self.open03
            if (x == 3): f = self.open04
            if (x == 4): f = self.open05
                  
            maxPos = ((self.width / self.palnum) - width) * f
 
            mySup.location.x = posX - maxPos
            mySup.location.y = -posY
            mySup.location.z = posZ
            
            posY = posY + 0.015
    #--------------------------------------------------------------------------------
    # Panels
    #--------------------------------------------------------------------------------
    width = ((self.width / self.num) / self.palnum) + 0.01
    posX = -0.01
    posY = -0.006 
    posZ = -0.008
    x = 1
    fabricMat = None
    if (self.crt_mat):
        fabricMat = create_fabric_material("Fabric_material", False, 0.653, 0.485, 0.265, 0.653, 0.485, 0.265)

    for sup in Support:
        myPanel = create_japan_panel("Panel_" + str(x)
                       ,width,self.height
                       ,0,0,0
                       ,self.crt_mat,fabricMat)
        Panel.extend([myPanel])
        myPanel.parent = sup
        myPanel.location.x = posX 
        myPanel.location.y = posY
        myPanel.location.z = posZ
        x = x + 1
    #------------------------
    # Strings        
    #------------------------
    x = myRail.location.x
    y = myRail.location.y
    z = myRail.location.z
    
    long = -1
    if (self.height < 1):
        long = -self.height
     
    myP = [((0,0,0),(- 0.25, 0, 0),(0.0, 0, 0))
          ,((0,0,long),(- 0.01, 0, long),(0.25, 0, long))] # double element
    myCurve1 = create_bezier("String_1", myP,(x,y,z))
    myCurve1.parent = myRail
    myCurve1.location.x = self.width 
    myCurve1.location.y = -0.004    
    myCurve1.location.z = 0.005    
 
    myCurve2 = create_bezier("String_2", myP,(x,y,z))
    myCurve2.parent = myRail
    myCurve2.location.x = self.width
    myCurve2.location.y = -0.01    
    myCurve2.location.z = 0.005    
     
    if (self.crt_mat):
        mat = create_diffuse_material("String_material", False, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.01)
        set_material(myCurve1, mat)
        set_material(myCurve2, mat)
    
    
    # refine
    for obj in Support:
        remove_doubles(obj)
        set_normals(obj)
    

    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    
    myRail.select = True        
    bpy.context.scene.objects.active = myRail
    
    return
#------------------------------------------------------------------------------
# Create japan rail
#
# objName: Name for the new object
# sX: Size in X axis
# ways: Number of ways
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: Flag for creating materials
#------------------------------------------------------------------------------
def create_japan_rail(objName,sX,ways,pX,pY,pZ,mat):
    myVertex = []
    myFaces = []
    
    waysize= 0.005 # gap
    sZ = 0.0145
    size = 0.005
    sizeint = 0.01
    tap = 0.01
    sY = (size * 2) + (waysize * ways) + (sizeint * (ways - 1))
    v = 0
    # left extension
    myVertex.extend([(0,0,0),(0,0,sZ),(0,-sY,sZ),(0,-sY,0),(tap,0,0),(tap,0,sZ),(tap,-sY,sZ),(tap,-sY,0)])
    myFaces.extend([(0,1,2,3),(4,5,6,7),(0,1,5,4),(3,2,6,7),(2,1,5,6),(3,0,4,7)])
    v = v + 8
    # Center
    myVertex.extend([(tap,-size,size),(tap,-size,0),(tap,0,0),(tap,0,sZ),(tap,-sY,sZ),(tap,-sY,0),(tap,-sY + size,0),(tap,-sY + size,sZ - 0.002)])
    myVertex.extend([(sX+tap,-size,size),(sX+tap,-size,0),(sX+tap,0,0),(sX+tap,0,sZ),(sX+tap,-sY,sZ),(sX+tap,-sY,0),(sX+tap,-sY + size,0),(sX+tap,-sY + size,sZ-0.002)])
    myFaces.extend([(v,v+8,v+9,v+1),(v+1,v+9,v+10,v+2),(v+2,v+10,v+11,v+3),(v+3,v+11,v+12,v+4)
                    ,(v+4,v+12,v+13,v+5),(v+5,v+13,v+14,v+6),(v+7,v+15,v+14,v+6)])
    v = v + 16
    # Right extension
    myVertex.extend([(sX+tap,0,0),(sX+tap,0,sZ),(sX+tap,-sY,sZ),(sX+tap,-sY,0),(sX+tap+tap,0,0),(sX+tap+tap,0,sZ),(sX+tap+tap,-sY,sZ),(sX+tap+tap,-sY,0)])
    myFaces.extend([(v,v+1,v+2,v+3),(v+4,v+5,v+6,v+7),(v,v+1,v+5,v+4),(v+3,v+2,v+6,v+7),(v+2,v+1,v+5,v+6),(v+3,v,v+4,v+7)])
    v = v + 8
    
    # Internal
    space = waysize + size
    if (ways > 1):
        for x in range(ways - 1):
            myVertex.extend([(tap,-space,sZ),(tap,-space ,0),(tap,-space - sizeint,0),(tap,-space-sizeint,size)])
            myVertex.extend([(sX+tap,-space,sZ),(sX+tap,-space ,0),(sX+tap,-space - sizeint,0),(sX+tap,-space-sizeint,size)])
            myFaces.extend([(v,v + 4,v + 5, v + 1),(v+1,v+5,v+6,v+2),(v+2,v+6,v+7,v+3)])
            v = v + 8
            space = space + waysize + sizeint
    

    mymesh = bpy.data.meshes.new(objName)
    myObject = bpy.data.objects.new(objName, mymesh)
    
    myObject.location[0] = pX
    myObject.location[1] = pY
    myObject.location[2] = pZ 
    bpy.context.scene.objects.link(myObject)
    
    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)
    
    #---------------------------------
    # Materials
    #---------------------------------
    if (mat):
        # External
        mat = create_diffuse_material(objName + "_material", False, 0.8, 0.8, 0.8, 0.6, 0.6, 0.6, 0.15)
        set_material(myObject, mat)
    
    return (myObject)

#------------------------------------------------------------------------------
# Create japan support
#
# objName: Name for the new object
# sX: Size in X axis
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: Flag for creating materials
#------------------------------------------------------------------------------
def create_japan_support(objName,sX,pX,pY,pZ,mat):
    myVertex = []
    myFaces = []
    
    waysize= 0.008
    sZ = 0.015
    sY = 0.006

    myVertex.extend([(0,0,0),(0,0,-sZ),(0,-sY,-sZ),(0,-sY,-waysize),(0,-0.003,-waysize),(0,-0.003,0)])
    myVertex.extend([(sX,0,0),(sX,0,-sZ),(sX,-sY,-sZ),(sX,-sY,- waysize),(sX,-0.003,-waysize),(sX,-0.003,0)])
    myFaces.extend([(0,1,7,6),(2,3,9,8),(1,7,8,2),(3,4,10,9),(4,5,11,10),(0,6,11,5),(0,1,2,3,4,5),(6,7,8,9,10,11)])

    mymesh = bpy.data.meshes.new(objName)
    myObject = bpy.data.objects.new(objName, mymesh)
    
    myObject.location[0] = pX
    myObject.location[1] = pY
    myObject.location[2] = pZ 
    bpy.context.scene.objects.link(myObject)
    
    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)
    
    #---------------------------------
    # Materials
    #---------------------------------
    if (mat):
        # External
        mat = create_diffuse_material(objName + "_material", False, 0.8, 0.8, 0.8, 0.6, 0.6, 0.6, 0.15)
        set_material(myObject, mat)
    
    return (myObject)

#------------------------------------------------------------------------------
# Create japan panel
#
# objName: Name for the new object
# sX: Size in X axis
# sZ: Size in Z axis
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: Flag for creating materials
# fabricMat: Fabric material
#------------------------------------------------------------------------------
def create_japan_panel(objName,sX,sZ,pX,pY,pZ,mat,fabricMat):
    myVertex = []
    myFaces = []
    
    myVertex.extend([(0,0,0),(0,0,-sZ),(sX,0,-sZ),(sX,0,0)])
    myFaces.extend([(0,1,2,3)])

    mymesh = bpy.data.meshes.new(objName)
    myObject = bpy.data.objects.new(objName, mymesh)
    
    myObject.location[0] = pX
    myObject.location[1] = pY
    myObject.location[2] = pZ 
    bpy.context.scene.objects.link(myObject)
    
    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)
    
    #---------------------------------
    # Materials
    #---------------------------------
    if (mat):
        unwrap_mesh(myObject,True)
        # remap UV to use all texture
        for uv_loop in myObject.data.uv_layers.active.data:
            myVector = uv_loop.uv
            if (myVector.x > 0.0001):
                myVector.x = 1
                   
        set_material(myObject, fabricMat)
    return (myObject)

#------------------------------------------------------------------------------
# Create bezier curve
#------------------------------------------------------------------------------
def create_bezier(objName, points, origin,depth=0.001,fill='FULL'):    
    curvedata = bpy.data.curves.new(name=objName, type='CURVE')   
    curvedata.dimensions = '3D'    
    curvedata.fill_mode = fill
    curvedata.bevel_resolution=5
    curvedata.bevel_depth= depth
    
    myObject = bpy.data.objects.new(objName, curvedata)    
    myObject.location = origin
    
    bpy.context.scene.objects.link(myObject)    
    
    polyline = curvedata.splines.new('BEZIER')    
    polyline.bezier_points.add(len(points)-1)    
 
 
    for idx, (knot, h1, h2) in enumerate(points):
        point = polyline.bezier_points[idx]
        point.co = knot
        point.handle_left = h1
        point.handle_right = h2
        point.handle_left_type = 'FREE'
        point.handle_right_type = 'FREE'

    return myObject 

#------------------------------------------------------------------------------
# Generate Roller curtains
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def generate_roller(self,context):

    location = bpy.context.scene.cursor_location
    myLoc = copy.copy(location) # copy location to keep 3D cursor position

    #------------------ 
    # Roller Top
    #------------------ 
    fabricsolid= None
    if (self.crt_mat):
        fabricsolid = create_diffuse_material("Fabric_solid_material", False, 0.653, 0.485, 0.265)
    
    myRoller = create_roller_rail("Roller"
                       ,self.width
                       ,0.035
                       ,myLoc.x,myLoc.y,myLoc.z
                       ,self.crt_mat,fabricsolid)
    # refine
    remove_doubles(myRoller)
    set_normals(myRoller)
     
    #--------------------------------------------------------------------------------
    # Sides
    #--------------------------------------------------------------------------------
    plastic = None
    if (self.crt_mat):
        plastic = create_diffuse_material("Plastic_roller_material", False, 0.653, 0.485, 0.265, 0.653, 0.485, 0.265,0.2)

    mySide_L =  create_roller_sides(myRoller,"L"
                       ,0.026,0,0
                       ,self.crt_mat,plastic)
    # refine
    remove_doubles(mySide_L)
    set_normals(mySide_L)
    
    mySide_R =  create_roller_sides(myRoller,"R"
                       ,self.width - 0.026,0,0
                       ,self.crt_mat,plastic)
    # refine
    remove_doubles(mySide_R)
    set_normals(mySide_R)
    
    
    #--------------------------------------------------------------------------------
    # Panel
    #--------------------------------------------------------------------------------
    fabricMat = None
    if (self.crt_mat):
        fabricMat = create_fabric_material("Fabric_translucent_material", False, 0.653, 0.485, 0.265, 0.653, 0.485, 0.265)

    myPanel = create_japan_panel("Panel"
                   ,self.width,self.height
                   ,0,0,0
                   ,self.crt_mat,fabricMat)
    myPanel.parent = myRoller
    myPanel.location.x = 0 
    myPanel.location.y = 0.035
    myPanel.location.z = 0
    #------------------ 
    # Roller Bottom
    #------------------ 
    myBottom = create_roller_rail("Roller_bottom"
                       ,self.width
                       ,0.001
                       ,0,0,-self.height
                       ,self.crt_mat,plastic)
    myBottom.parent = myPanel
    # refine
    remove_doubles(myRoller)
    set_normals(myRoller)
    
    #------------------------
    # Strings        
    #------------------------
    myP = [((0.0000, -0.0328, -0.0000), (0.0000, -0.0403, -0.3327), (0.0000, -0.0293, 0.1528))
            ,((0.0000, 0.0000, 0.3900), (0.0000, -0.0264, 0.3900), (-0.0000, 0.0226, 0.3900))
            ,((-0.0000, 0.0212, 0.0000), (-0.0000, 0.0189, 0.1525), (-0.0000, 0.0260, -0.3326))
            ,((-0.0000, -0.0000, -0.8518), (-0.0000, 0.0369, -0.8391), (0.0000, -0.0373, -0.8646))] # double element
    myCurve = create_bezier("String",myP,(0,0,0))
    set_curve_cycle(myCurve)
    myCurve.parent = myRoller
    myCurve.location.x = self.width + 0.015 
    myCurve.location.y = 0    
    myCurve.location.z = -0.38    
    if (self.crt_mat):
        mat = create_diffuse_material("String_material", False, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.01)
        set_material(myCurve, mat)
    

    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    
    myRoller.select = True        
    bpy.context.scene.objects.active = myRoller
    
    return
#------------------------------------------------------------------------------
# Create roller
#
# objName: Object name
# width: Total width of roller
# radio: Roll radio
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: create default cycles material
# mymaterial: plastic material or fabric
#------------------------------------------------------------------------------
def create_roller_rail(objName,width,radio,pX,pY,pZ,mat,mymaterial):
         
    myVertex = []
    myFaces = []
    pies = 16
    seg = 0
    
    # Add right circle
    for i in range(pies):
        x = math.cos(math.radians(seg)) * radio
        y = math.sin(math.radians(seg)) * radio
        myPoint = [(0.0,x,y)]
        myVertex.extend(myPoint)
        seg = seg + (360 / pies)
    # Add left circle
    seg = 0
    for i in range(pies):
        x = math.cos(math.radians(seg)) * radio
        y = math.sin(math.radians(seg)) * radio
        myPoint = [(width,x,y)]
        myVertex.extend(myPoint)
        seg = seg + (360 / pies)
    #------------------------------------- 
    # Faces
    #------------------------------------- 
    t = 1       
    for n in range(0,pies):        
        t = t + 1
        if (t > pies): 
            t = 1
            myFace = [(n,n - pies + 1,n + 1,n + pies)]
            myFaces.extend(myFace)
        else:
            myFace = [(n,n+1,n + pies + 1,n + pies)]
            myFaces.extend(myFace)

    
    mymesh = bpy.data.meshes.new(objName)
    myRoll = bpy.data.objects.new(objName, mymesh)
    bpy.context.scene.objects.link(myRoll)
    
    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)
    # Position
    myRoll.location.x = pX        
    myRoll.location.y = pY       
    myRoll.location.z = pZ        
    
    # Materials
    if (mat):
        set_material(myRoll, mymaterial)

    # Smooth
    set_smooth(myRoll)
   
    return myRoll
#------------------------------------------------------------------------------
# Create roller sides
# 
# myRoller: Roller to add sides
# side: Side of the cap R/L
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: create default cycles material
# plastic: plastic material
#------------------------------------------------------------------------------
def create_roller_sides(myRoller,side,pX,pY,pZ,mat,plastic):
    # Retry mesh data
    myData = roller_side()

    # move data
    myVertex = myData[0]
    myFaces = myData[1]
    
    mymesh = bpy.data.meshes.new("Side." + side)
    mySide = bpy.data.objects.new("Side." + side, mymesh)
    bpy.context.scene.objects.link(mySide)
    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)
    # Position
    mySide.location.x = pX        
    mySide.location.y = pY       
    mySide.location.z = pZ        
    # rotate
    if (side == "L"):
        mySide.rotation_euler = (0,0, math.radians(180))
    # parent
    mySide.parent = myRoller
    
    # Materials
    if (mat):
        set_material(mySide, plastic)

    # Smooth
    set_smooth(mySide)
    set_modifier_subsurf(mySide)

    return mySide

#----------------------------------------------
# Roller side data
#----------------------------------------------
def roller_side():
    #------------------------------------
    # Mesh data
    #------------------------------------
    minX = -7.54842304218073e-08
    maxX = 0.05209559202194214
    minY = -0.04486268758773804
    maxY = 0.04486268758773804
    minZ = -0.04486268758773804
    maxZ = 0.08202265202999115
    
    # Vertex
    myVertex = [(maxX - 0.004684023559093475,maxY,minZ + 0.04486270064847542)
    ,(maxX - 0.004684023559093475,maxY - 0.0034149661660194397,minZ + 0.027694489806890488)
    ,(maxX - 0.004684023559093475,maxY - 0.013139978051185608,minZ + 0.013139985501766205)
    ,(maxX - 0.004684023559093475,maxY - 0.02769448049366474,minZ + 0.0034149736166000366)
    ,(maxX - 0.004684023559093475,minY + 0.044862685327428764,minZ)
    ,(maxX - 0.004684023559093475,minY + 0.027694476768374443,minZ + 0.0034149736166000366)
    ,(maxX - 0.004684023559093475,minY + 0.013139978051185608,minZ + 0.013139985501766205)
    ,(maxX - 0.004684023559093475,minY + 0.0034149661660194397,minZ + 0.02769448794424534)
    ,(maxX - 0.004684023559093475,minY,minZ + 0.04486269387439812)
    ,(maxX - 0.004684023559093475,minY + 0.0034149624407291412,minZ + 0.06203090213239193)
    ,(maxX - 0.004684023559093475,minY + 0.013139966875314713,maxZ - 0.050299935042858124)
    ,(maxX - 0.004684023559093475,minY + 0.027694474905729294,maxZ - 0.04057491198182106)
    ,(maxX - 0.004684023559093475,maxY - 0.027694473043084145,maxZ - 0.04057491570711136)
    ,(maxX - 0.004684023559093475,maxY - 0.013139966875314713,maxZ - 0.05029993876814842)
    ,(maxX - 0.004684023559093475,maxY - 0.0034149587154388428,minZ + 0.062030890956521034)
    ,(maxX - 0.0046574510633945465,minY + 0.028278490528464317,minZ + 0.0048249028623104095)
    ,(maxX - 0.0046574510633945465,minY + 0.014219092205166817,minZ + 0.014219097793102264)
    ,(maxX - 0.0046574510633945465,minY + 0.004824899137020111,minZ + 0.028278499841690063)
    ,(maxX - 0.003122705966234207,maxY,minZ + 0.04486270064847542)
    ,(maxX - 0.003122705966234207,maxY - 0.0034149661660194397,minZ + 0.027694489806890488)
    ,(maxX - 0.003122705966234207,maxY - 0.013139978051185608,minZ + 0.013139985501766205)
    ,(maxX - 0.003122705966234207,maxY - 0.02769448049366474,minZ + 0.0034149736166000366)
    ,(maxX - 0.003149278461933136,maxY - 0.04486268735455812,maxZ - 0.03868604078888893)
    ,(maxX - 0.003149278461933136,maxY - 0.02827848680317402,maxZ - 0.04198484495282173)
    ,(maxX - 0.003149278461933136,maxY - 0.014219081029295921,maxZ - 0.05137905105948448)
    ,(maxX - 0.003149278461933136,maxY - 0.004824887961149216,minZ + 0.06144687905907631)
    ,(maxX - 0.02118653617799282,minY + 0.027694474905729294,maxZ - 0.04057491570711136)
    ,(maxX - 0.02118653617799282,minY + 0.013139966875314713,maxZ - 0.050299935042858124)
    ,(maxX - 0.02118653617799282,minY + 0.0034149624407291412,minZ + 0.06203090213239193)
    ,(maxX - 0.02118653617799282,minY,minZ + 0.04486269262849252)
    ,(maxX - 0.003122705966234207,minY,minZ + 0.04486269387439812)
    ,(maxX - 0.003122705966234207,minY + 0.0034149624407291412,minZ + 0.06203090213239193)
    ,(maxX - 0.003122705966234207,minY + 0.013139966875314713,maxZ - 0.050299935042858124)
    ,(maxX - 0.003122705966234207,minY + 0.027694474905729294,maxZ - 0.04057491198182106)
    ,(maxX - 0.02118653617799282,maxY - 0.02769448049366474,minZ + 0.0034149661660194397)
    ,(maxX - 0.02118653617799282,maxY - 0.013139978051185608,minZ + 0.013139981776475906)
    ,(maxX - 0.02118653617799282,maxY - 0.0034149661660194397,minZ + 0.02769448794424534)
    ,(maxX - 0.02118653617799282,maxY,minZ + 0.044862699402576034)
    ,(maxX - 0.020517520606517792,minY + 0.01146744191646576,minZ + 0.03102993033826351)
    ,(maxX - 0.020517520606517792,minY + 0.01930307224392891,minZ + 0.019303075969219208)
    ,(maxX - 0.020517520606517792,minY + 0.031029919162392616,minZ + 0.01146744191646576)
    ,(maxX - 0.020517520606517792,minY + 0.04486268576937835,minZ + 0.008715935051441193)
    ,(maxX - 0.003122705966234207,maxY - 0.013139966875314713,maxZ - 0.02605174481868744)
    ,(maxX,minY + 0.013139966875314713,maxZ - 0.026319395750761032)
    ,(maxX,minY + 0.027694474905729294,maxZ - 0.026230186223983765)
    ,(maxX,maxY - 0.013139966875314713,maxZ - 0.02605174481868744)
    ,(maxX - 0.0046574510633945465,minY + 0.0015261024236679077,minZ + 0.04486269394558251)
    ,(maxX - 0.0046574510633945465,minY + 0.004824895411729813,minZ + 0.061446888372302055)
    ,(maxX - 0.0046574510633945465,minY + 0.014219081029295921,maxZ - 0.05137904919683933)
    ,(maxX - 0.0046574510633945465,minY + 0.02827848680317402,maxZ - 0.04198484495282173)
    ,(maxX,maxY - 0.027694473043084145,maxZ - 0.026230186223983765)
    ,(maxX,maxY - 0.04486268735205459,maxZ - 0.02629481628537178)
    ,(maxX - 0.003122705966234207,maxY - 0.027694473043084145,maxZ - 0.04057491570711136)
    ,(maxX - 0.003122705966234207,maxY - 0.013139966875314713,maxZ - 0.05029993876814842)
    ,(maxX - 0.003122705966234207,maxY - 0.0034149587154388428,minZ + 0.062030890956521034)
    ,(maxX - 0.003149278461933136,maxY - 0.0015261024236679077,minZ + 0.044862700489230356)
    ,(maxX - 0.003149278461933136,maxY - 0.004824899137020111,minZ + 0.028278501704335213)
    ,(maxX - 0.003149278461933136,maxY - 0.014219092205166817,minZ + 0.014219097793102264)
    ,(maxX - 0.003149278461933136,maxY - 0.028278492391109467,minZ + 0.0048249028623104095)
    ,(maxX - 0.003149278461933136,minY + 0.0015261024236679077,minZ + 0.04486269394558251)
    ,(maxX - 0.003149278461933136,minY + 0.004824895411729813,minZ + 0.061446888372302055)
    ,(maxX - 0.003149278461933136,minY + 0.014219081029295921,maxZ - 0.05137904919683933)
    ,(maxX - 0.003149278461933136,minY + 0.02827848680317402,maxZ - 0.04198484495282173)
    ,(maxX - 0.02118653617799282,maxY - 0.0034149587154388428,minZ + 0.062030889093875885)
    ,(maxX - 0.02118653617799282,maxY - 0.013139966875314713,maxZ - 0.05029993876814842)
    ,(maxX - 0.02118653617799282,maxY - 0.027694473043084145,maxZ - 0.04057491570711136)
    ,(maxX - 0.02118653617799282,maxY - 0.04486268735205459,maxZ - 0.03715994209051132)
    ,(maxX - 0.020517520606517792,maxY - 0.011467430740594864,minZ + 0.058695447631180286)
    ,(maxX - 0.020517520606517792,maxY - 0.019303061068058014,maxZ - 0.05646303482353687)
    ,(maxX - 0.020517520606517792,maxY - 0.031029915437102318,maxZ - 0.04862739145755768)
    ,(maxX - 0.020517520606517792,maxY - 0.044862687395027134,maxZ - 0.045875877141952515)
    ,(maxX,minY + 0.0034149661660194397,minZ + 0.02769448794424534)
    ,(maxX,minY + 0.013139978051185608,minZ + 0.013139985501766205)
    ,(maxX,minY + 0.027694476768374443,minZ + 0.0034149736166000366)
    ,(maxX,minY + 0.044862685327428764,minZ)
    ,(maxX - 0.02118653617799282,minY + 0.0034149661660194397,minZ + 0.02769448794424534)
    ,(maxX - 0.02118653617799282,minY + 0.013139978051185608,minZ + 0.013139981776475906)
    ,(maxX - 0.02118653617799282,minY + 0.027694476768374443,minZ + 0.0034149661660194397)
    ,(maxX - 0.02118653617799282,minY + 0.044862685327428764,minZ)
    ,(maxX - 0.020517520606517792,maxY - 0.031029922887682915,minZ + 0.01146744191646576)
    ,(maxX - 0.020517520606517792,maxY - 0.01930307224392891,minZ + 0.019303075969219208)
    ,(maxX - 0.020517520606517792,maxY - 0.01146744191646576,minZ + 0.03102993033826351)
    ,(maxX - 0.020517520606517792,maxY - 0.008715927600860596,minZ + 0.04486269835125789)
    ,(maxX - 0.0046574510633945465,maxY - 0.04486268735455812,maxZ - 0.03868604078888893)
    ,(maxX - 0.0046574510633945465,maxY - 0.02827848680317402,maxZ - 0.04198484495282173)
    ,(maxX - 0.0046574510633945465,maxY - 0.014219081029295921,maxZ - 0.05137905105948448)
    ,(maxX - 0.0046574510633945465,maxY - 0.004824887961149216,minZ + 0.06144687905907631)
    ,(maxX - 0.0046574510633945465,maxY - 0.0015261024236679077,minZ + 0.044862700489230356)
    ,(maxX - 0.0046574510633945465,maxY - 0.004824899137020111,minZ + 0.028278501704335213)
    ,(maxX - 0.0046574510633945465,maxY - 0.014219092205166817,minZ + 0.014219097793102264)
    ,(maxX - 0.0046574510633945465,maxY - 0.028278492391109467,minZ + 0.0048249028623104095)
    ,(maxX - 0.003149278461933136,minY + 0.004824899137020111,minZ + 0.028278499841690063)
    ,(maxX - 0.003149278461933136,minY + 0.014219092205166817,minZ + 0.014219097793102264)
    ,(maxX - 0.003149278461933136,minY + 0.028278490528464317,minZ + 0.0048249028623104095)
    ,(maxX,minY,minZ + 0.04486269387439812)
    ,(maxX,minY + 0.0034149624407291412,minZ + 0.06203090213239193)
    ,(maxX,minY + 0.013139966875314713,maxZ - 0.050299935042858124)
    ,(maxX,minY + 0.027694474905729294,maxZ - 0.04057491198182106)
    ,(maxX - 0.020517520606517792,minY + 0.031029917299747467,maxZ - 0.04862739145755768)
    ,(maxX - 0.020517520606517792,minY + 0.019303061068058014,maxZ - 0.056463029235601425)
    ,(maxX - 0.020517520606517792,minY + 0.011467434465885162,minZ + 0.05869545880705118)
    ,(maxX - 0.020517520606517792,minY + 0.008715927600860596,minZ + 0.04486269289324163)
    ,(maxX - 0.003122705966234207,minY + 0.0034149661660194397,minZ + 0.02769448794424534)
    ,(maxX - 0.003122705966234207,minY + 0.013139978051185608,minZ + 0.013139985501766205)
    ,(maxX - 0.003122705966234207,minY + 0.027694476768374443,minZ + 0.0034149736166000366)
    ,(maxX - 0.003122705966234207,minY + 0.044862685327428764,minZ)
    ,(maxX,maxY - 0.02769448049366474,minZ + 0.0034149736166000366)
    ,(maxX,maxY - 0.013139978051185608,minZ + 0.013139985501766205)
    ,(maxX,maxY - 0.0034149661660194397,minZ + 0.027694489806890488)
    ,(maxX,maxY,minZ + 0.04486270064847542)
    ,(maxX,maxY - 0.0034149587154388428,minZ + 0.062030890956521034)
    ,(maxX,maxY - 0.013139966875314713,maxZ - 0.05029993876814842)
    ,(maxX,maxY - 0.027694473043084145,maxZ - 0.04057491570711136)
    ,(maxX,maxY - 0.04486268735205459,maxZ - 0.03715994209051132)
    ,(maxX - 0.003122705966234207,maxY - 0.027694473043084145,maxZ - 0.026230186223983765)
    ,(maxX - 0.003122705966234207,maxY - 0.04486268735205459,maxZ - 0.02629481628537178)
    ,(maxX - 0.003122705966234207,minY + 0.027694474905729294,maxZ - 0.026230186223983765)
    ,(maxX - 0.003122705966234207,minY + 0.013139966875314713,maxZ - 0.026319395750761032)
    ,(maxX - 0.003122705966234207,minY + 0.013139966875314713,maxZ - 0.0018796995282173157)
    ,(maxX - 0.01466318964958191,minY + 0.013139966875314713,maxZ - 0.0018796995282173157)
    ,(maxX,minY + 0.027694474905729294,maxZ - 0.0017904937267303467)
    ,(maxX,maxY - 0.013139966875314713,maxZ - 0.001612052321434021)
    ,(maxX - 0.009187713265419006,maxY - 0.013139966875314713,maxZ - 0.02605174481868744)
    ,(maxX - 0.009187713265419006,maxY - 0.027694473043084145,maxZ - 0.026230186223983765)
    ,(maxX - 0.009187713265419006,maxY - 0.04486268735205459,maxZ - 0.02629481628537178)
    ,(maxX - 0.009187713265419006,minY + 0.027694474905729294,maxZ - 0.026230186223983765)
    ,(maxX - 0.009187713265419006,minY + 0.013139966875314713,maxZ - 0.026319395750761032)
    ,(maxX - 0.003122705966234207,maxY - 0.013139966875314713,maxZ - 0.001612052321434021)
    ,(maxX - 0.01466318964958191,minY + 0.027694474905729294,maxZ - 0.0017904937267303467)
    ,(maxX,minY + 0.022660084068775177,minZ + 0.03566607739776373)
    ,(maxX,minY + 0.02786955051124096,minZ + 0.027869559824466705)
    ,(maxX,minY + 0.03566606715321541,minZ + 0.022660093382000923)
    ,(maxX,minY + 0.04486268649608238,minZ + 0.020830770954489708)
    ,(maxX,minY + 0.02083076350390911,minZ + 0.044862694725740226)
    ,(maxX,minY + 0.022660082206130028,minZ + 0.05405931267887354)
    ,(maxX,minY + 0.02786954492330551,minZ + 0.061855828389525414)
    ,(maxX,minY + 0.035666066221892834,maxZ - 0.059820037335157394)
    ,(maxX,maxY - 0.03566606715321541,minZ + 0.022660093382000923)
    ,(maxX,maxY - 0.02786955051124096,minZ + 0.027869559824466705)
    ,(maxX,maxY - 0.022660084068775177,minZ + 0.035666078329086304)
    ,(maxX,maxY - 0.02083076350390911,minZ + 0.044862698354463326)
    ,(maxX,maxY - 0.02266007848083973,minZ + 0.05405930709093809)
    ,(maxX,maxY - 0.02786954492330551,minZ + 0.061855828389525414)
    ,(maxX,maxY - 0.035666064359247684,maxZ - 0.059820037335157394)
    ,(maxX,maxY - 0.04486268734234705,maxZ - 0.05799071677029133)
    ,(maxX,minY + 0.04486268733843682,minZ + 0.04486269544876009)
    ,(maxX - 0.009557131677865982,maxY - 0.04486268735205459,maxZ - 0.02464577928185463)
    ,(maxX - 0.009557131677865982,minY + 0.027694474905729294,maxZ - 0.024581149220466614)
    ,(maxX - 0.009557131677865982,maxY - 0.013139966875314713,maxZ - 0.024402707815170288)
    ,(maxX - 0.009557131677865982,minY + 0.013139966875314713,maxZ - 0.02467035874724388)
    ,(maxX - 0.009557131677865982,maxY - 0.027694473043084145,maxZ - 0.024581149220466614)
    ,(maxX - 0.015024378895759583,minY + 0.027694474905729294,maxZ - 0.00017844140529632568)
    ,(maxX - 0.015024378895759583,minY + 0.013139966875314713,maxZ - 0.0002676546573638916)
    ,(maxX - 0.015024378895759583,maxY - 0.04486268735205459,maxZ - 0.0002430751919746399)
    ,(maxX - 0.015024378895759583,maxY - 0.027694473043084145,maxZ - 0.00017844140529632568)
    ,(maxX - 0.015024378895759583,maxY - 0.013139966875314713,maxZ)
    ,(maxX,minY + 0.013139966875314713,maxZ - 0.0018796995282173157)
    ,(maxX - 0.01466318964958191,maxY - 0.04486268735205459,maxZ - 0.001855120062828064)
    ,(maxX,maxY - 0.04486268735205459,maxZ - 0.001855120062828064)
    ,(maxX - 0.01466318964958191,maxY - 0.027694473043084145,maxZ - 0.0017904937267303467)
    ,(maxX - 0.01466318964958191,maxY - 0.013139966875314713,maxZ - 0.001612052321434021)
    ,(maxX,maxY - 0.027694473043084145,maxZ - 0.0017904937267303467)
    ,(maxX - 0.020517520606517792,minY + 0.014739999547600746,minZ + 0.03238546848297119)
    ,(maxX - 0.020517520606517792,minY + 0.021807780489325523,minZ + 0.02180778607726097)
    ,(maxX - 0.020517520606517792,minY + 0.03238545823842287,minZ + 0.014740003272891045)
    ,(maxX - 0.020517520606517792,minY + 0.044862685933359736,minZ + 0.012258127331733704)
    ,(maxX - 0.020517520606517792,maxY - 0.014739990234375,minZ + 0.05733991041779518)
    ,(maxX - 0.020517520606517792,maxY - 0.021807771176099777,maxZ - 0.05896773934364319)
    ,(maxX - 0.020517520606517792,maxY - 0.03238545451313257,maxZ - 0.051899950951337814)
    ,(maxX - 0.020517520606517792,maxY - 0.044862687428120204,maxZ - 0.049418069422245026)
    ,(maxX - 0.020517520606517792,maxY - 0.03238546196371317,minZ + 0.014740003272891045)
    ,(maxX - 0.020517520606517792,maxY - 0.021807780489325523,minZ + 0.02180778607726097)
    ,(maxX - 0.020517520606517792,maxY - 0.014739999547600746,minZ + 0.03238546848297119)
    ,(maxX - 0.020517520606517792,maxY - 0.012258119881153107,minZ + 0.04486269794694575)
    ,(maxX - 0.020517520606517792,minY + 0.03238545544445515,maxZ - 0.051899950951337814)
    ,(maxX - 0.020517520606517792,minY + 0.021807771176099777,maxZ - 0.05896773561835289)
    ,(maxX - 0.020517520606517792,minY + 0.014739995822310448,minZ + 0.05733991973102093)
    ,(maxX - 0.020517520606517792,minY + 0.012258119881153107,minZ + 0.04486269302378876)
    ,(minX,minY + 0.014739999547600746,minZ + 0.03238546848297119)
    ,(minX,minY + 0.021807780489325523,minZ + 0.02180778607726097)
    ,(minX,minY + 0.03238545823842287,minZ + 0.014740003272891045)
    ,(minX,minY + 0.044862685933359736,minZ + 0.012258127331733704)
    ,(minX,maxY - 0.014739990234375,minZ + 0.05733991041779518)
    ,(minX,maxY - 0.021807771176099777,maxZ - 0.05896773934364319)
    ,(minX,maxY - 0.03238545451313257,maxZ - 0.051899950951337814)
    ,(minX,maxY - 0.044862687428120204,maxZ - 0.049418069422245026)
    ,(minX,maxY - 0.03238546196371317,minZ + 0.014740003272891045)
    ,(minX,maxY - 0.021807780489325523,minZ + 0.02180778607726097)
    ,(minX,maxY - 0.014739999547600746,minZ + 0.03238546848297119)
    ,(minX,maxY - 0.012258119881153107,minZ + 0.04486269794694575)
    ,(minX,minY + 0.03238545544445515,maxZ - 0.051899950951337814)
    ,(minX,minY + 0.021807771176099777,maxZ - 0.05896773561835289)
    ,(minX,minY + 0.014739995822310448,minZ + 0.05733991973102093)
    ,(minX,minY + 0.012258119881153107,minZ + 0.04486269302378876)]
    
    # Faces
    myFaces = [(37, 0, 1, 36),(36, 1, 2, 35),(35, 2, 3, 34),(34, 3, 4, 78),(78, 4, 5, 77)
    ,(77, 5, 6, 76),(76, 6, 7, 75),(75, 7, 8, 29),(29, 8, 9, 28),(28, 9, 10, 27)
    ,(27, 10, 11, 26),(65, 12, 13, 64),(8, 7, 17, 46),(63, 14, 0, 37),(64, 13, 14, 63)
    ,(34, 78, 41, 79),(64, 63, 67, 68),(76, 75, 38, 39),(65, 64, 68, 69),(27, 26, 98, 99)
    ,(78, 77, 40, 41),(28, 27, 99, 100),(35, 34, 79, 80),(63, 37, 82, 67),(29, 28, 100, 101)
    ,(26, 66, 70, 98),(36, 35, 80, 81),(66, 65, 69, 70),(77, 76, 39, 40),(37, 36, 81, 82)
    ,(75, 29, 101, 38),(19, 18, 109, 108),(31, 32, 61, 60),(2, 1, 88, 89),(103, 102, 91, 92)
    ,(7, 6, 16, 17),(54, 18, 55, 25),(32, 33, 62, 61),(18, 19, 56, 55),(6, 5, 15, 16)
    ,(11, 10, 48, 49),(52, 53, 24, 23),(0, 14, 86, 87),(94, 71, 129, 133),(97, 113, 51, 44)
    ,(33, 32, 117, 116),(18, 54, 110, 109),(32, 31, 95, 96),(96, 97, 44, 43),(102, 103, 72, 71)
    ,(53, 52, 114, 42),(21, 20, 107, 106),(103, 104, 73, 72),(31, 30, 94, 95),(20, 19, 108, 107)
    ,(30, 102, 71, 94),(105, 21, 106, 74),(54, 53, 111, 110),(104, 105, 74, 73),(47, 46, 59, 60)
    ,(90, 89, 57, 58),(87, 86, 25, 55),(48, 47, 60, 61),(49, 48, 61, 62),(83, 49, 62, 22)
    ,(16, 15, 93, 92),(88, 87, 55, 56),(84, 83, 22, 23),(17, 16, 92, 91),(85, 84, 23, 24)
    ,(46, 17, 91, 59),(89, 88, 56, 57),(86, 85, 24, 25),(104, 103, 92, 93),(3, 2, 89, 90)
    ,(20, 21, 58, 57),(13, 12, 84, 85),(9, 8, 46, 47),(102, 30, 59, 91),(30, 31, 60, 59)
    ,(19, 20, 57, 56),(14, 13, 85, 86),(53, 54, 25, 24),(10, 9, 47, 48),(1, 0, 87, 88)
    ,(111, 53, 42, 45),(112, 111, 45, 50),(32, 96, 43, 117),(113, 112, 50, 51),(115, 116, 125, 124)
    ,(42, 114, 123, 122),(116, 117, 126, 125),(114, 115, 124, 123),(112, 113, 144, 143),(95, 94, 133, 134)
    ,(110, 111, 142, 141),(96, 95, 134, 135),(74, 106, 137, 132),(97, 96, 135, 136),(73, 74, 132, 131)
    ,(107, 108, 139, 138),(113, 97, 136, 144),(72, 73, 131, 130),(108, 109, 140, 139),(109, 110, 141, 140)
    ,(71, 72, 130, 129),(106, 107, 138, 137),(111, 112, 143, 142),(135, 134, 145),(137, 138, 145)
    ,(142, 143, 145),(136, 135, 145),(131, 132, 145),(143, 144, 145),(144, 136, 145)
    ,(130, 131, 145),(141, 142, 145),(129, 130, 145),(132, 137, 145),(133, 129, 145)
    ,(138, 139, 145),(134, 133, 145),(139, 140, 145),(140, 141, 145),(26, 11, 83, 66)
    ,(66, 83, 12, 65),(12, 83, 84),(22, 52, 23),(83, 11, 49),(21, 105, 58)
    ,(4, 90, 58, 105),(15, 4, 105, 93),(33, 22, 62),(4, 3, 90),(105, 104, 93)
    ,(5, 4, 15),(52, 22, 115, 114),(22, 33, 116, 115),(124, 125, 147, 146),(122, 123, 150, 148)
    ,(125, 126, 149, 147),(123, 124, 146, 150),(157, 128, 151, 153),(159, 157, 153, 154),(160, 159, 154, 155)
    ,(128, 119, 152, 151),(146, 147, 128, 157),(150, 146, 157, 159),(148, 150, 159, 160),(147, 149, 119, 128)
    ,(69, 68, 167, 168),(101, 100, 176, 177),(39, 38, 162, 163),(100, 99, 175, 176),(41, 40, 164, 165)
    ,(80, 79, 170, 171),(82, 81, 172, 173),(67, 82, 173, 166),(70, 69, 168, 169),(38, 101, 177, 162)
    ,(98, 70, 169, 174),(40, 39, 163, 164),(79, 41, 165, 170),(99, 98, 174, 175),(81, 80, 171, 172)
    ,(68, 67, 166, 167),(169, 168, 184, 185),(170, 165, 181, 186),(172, 171, 187, 188),(162, 177, 193, 178)
    ,(164, 163, 179, 180),(167, 166, 182, 183),(174, 169, 185, 190),(168, 167, 183, 184),(175, 174, 190, 191)
    ,(171, 170, 186, 187),(173, 172, 188, 189),(163, 162, 178, 179),(165, 164, 180, 181),(177, 176, 192, 193)
    ,(166, 173, 189, 182),(176, 175, 191, 192),(51, 50, 161, 158),(127, 160, 155),(156, 120, 151, 152)
    ,(155, 154, 161, 121),(161, 154, 153, 158),(42, 122, 148),(117, 149, 126),(127, 42, 148, 160)
    ,(118, 152, 119),(158, 153, 151, 120),(50, 45, 121, 161),(117, 118, 119, 149),(43, 44, 120, 156)
    ,(44, 51, 158, 120),(117, 43, 156, 118),(45, 42, 127, 121)]
   
                
    return (myVertex,myFaces)    
#--------------------------------------------------------------------
# Set curve cycle
#
# myObject: Curve obejct
#--------------------------------------------------------------------
def set_curve_cycle(myObject):
    bpy.context.scene.objects.active = myObject
# go edit mode
    bpy.ops.object.mode_set(mode='EDIT')
# select all faces
    bpy.ops.curve.select_all(action='SELECT')
# St cyclic
    bpy.ops.curve.cyclic_toggle(direction='CYCLIC_U')
# go object mode again
    bpy.ops.object.editmode_toggle()
#------------------------------------------------------------------------------
# Generate Venetian curtains
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def generate_venetian(self,context):

    location = bpy.context.scene.cursor_location
    myLoc = copy.copy(location) # copy location to keep 3D cursor position

    if (self.crt_mat):
        rgb = colorsys.hsv_to_rgb(self.hue, self.saturation, self.value)
        plastic = create_diffuse_material("Plastic_venetian_material", True, rgb[0], rgb[1], rgb[2], rgb[0], rgb[1], rgb[2],0.2)

    #------------------ 
    # Top
    #------------------ 
    myTop = create_venetian_base("Venetian_top",self.width + 0.002,self.depth + 0.002,-0.06)
    myTop.location.x = myLoc.x
    myTop.location.y = myLoc.y
    myTop.location.z = myLoc.z

    # materials
    if (self.crt_mat):
        set_material(myTop, plastic)
     
    #--------------------------------------------------------------------------------
    # segments
    #--------------------------------------------------------------------------------
    margin = self.depth
    myData = create_slat_mesh("Venetian_slats",self.width,self.depth,self.height - 0.06,self.angle,self.ratio)
    mySlats = myData[0]
    mySlats.parent = myTop
    mySlats.location.x = 0
    mySlats.location.y = 0
    mySlats.location.z = -margin - 0.04
    
    myPoints = myData[1]
    angleUsed = myData[2]
    # refine
    remove_doubles(mySlats)
    set_normals(mySlats)
    set_smooth(mySlats)
    
    if (self.crt_mat):
        set_material(mySlats, plastic)
    #------------------------
    # Strings (Middle)       
    #------------------------
    myP = [((0, 0, myPoints[0] + margin), (0, 0, 0), (0, 0, 0))
            ,((0, 0, myPoints[len(myPoints) - 1]), (0, 0, 0), (0, 0, 0))]
    
    myCurveL = create_bezier("String.L",myP,(0,0,0))
    myCurveL.parent = mySlats
    myCurveC = create_bezier("String.C",myP,(0,0,0))
    myCurveC.parent = mySlats
    myCurveR = create_bezier("String.R",myP,(0,0,0))
    myCurveR.parent = mySlats
    
    if (self.width < 0.60):
        sep = 0.058
    else:
        sep = 0.148
        
    myCurveL.location.x = (self.width/2) - sep
    myCurveL.location.y = 0    
    myCurveL.location.z = 0
        
    myCurveC.location.x = 0
    myCurveC.location.y = 0    
    myCurveC.location.z = 0
        
    myCurveR.location.x = -(self.width/2) + sep
    myCurveR.location.y = 0    
    myCurveR.location.z = 0
        
    if (self.crt_mat):
        mat = create_diffuse_material("String_material", False, 0.674, 0.617, 0.496, 0.1, 0.1, 0.1, 0.01)
        set_material(myCurveL, mat)
        set_material(myCurveC, mat)
        set_material(myCurveR, mat)
    #------------------------
    # Strings (Front)       
    #------------------------
    myP = [((0, 0, margin) , (0, 0, 0), (0, 0, 0))
            ,((0, 0, myPoints[len(myPoints) - 1] - 0.003 - math.sin(math.radians(angleUsed)) * self.depth/2), (0, 0, 0), (0, 0, 0))]
    
    myCurveLf = create_bezier("String.f.L",myP,(0,0,0),0.001,'FRONT')
    myCurveLf.parent = mySlats
    myCurveCf = create_bezier("String.f.C",myP,(0,0,0),0.001,'FRONT')
    myCurveCf.parent = mySlats
    myCurveRf = create_bezier("String.f.R",myP,(0,0,0),0.001,'FRONT')
    myCurveRf.parent = mySlats
    
    if (self.width < 0.60):
        sep = 0.058
    else:
        sep = 0.148
        
    myCurveLf.location.x = (self.width/2) - sep
    myCurveLf.location.y = ((-self.depth/2) * math.cos(math.radians(self.angle))) - 0.001
    myCurveLf.location.z = 0
        
    myCurveCf.location.x = 0
    myCurveCf.location.y = ((-self.depth/2) * math.cos(math.radians(self.angle))) - 0.001    
    myCurveCf.location.z = 0
        
    myCurveRf.location.x = -(self.width/2) + sep
    myCurveRf.location.y = ((-self.depth/2) * math.cos(math.radians(self.angle))) - 0.001    
    myCurveRf.location.z = 0
        
    if (self.crt_mat):
        set_material(myCurveLf, mat)
        set_material(myCurveCf, mat)
        set_material(myCurveRf, mat)
    
    #------------------------
    # Strings (Back)       
    #------------------------
    myP = [((0, 0, margin) , (0, 0, 0), (0, 0, 0))
           ,((0, 0, myPoints[len(myPoints) - 1] - 0.003 + math.sin(math.radians(angleUsed)) * self.depth/2), (0, 0, 0), (0, 0, 0))]
    
    myCurveLb = create_bezier("String.b.L",myP,(0,0,0),0.001,'BACK')
    myCurveLb.parent = mySlats
    myCurveCb = create_bezier("String.b.C",myP,(0,0,0),0.001,'BACK')
    myCurveCb.parent = mySlats
    myCurveRb = create_bezier("String.b.R",myP,(0,0,0),0.001,'BACK')
    myCurveRb.parent = mySlats
    
    if (self.width < 0.60):
        sep = 0.058
    else:
        sep = 0.148
        
    myCurveLb.location.x = (self.width/2) - sep
    myCurveLb.location.y = ((self.depth/2) * math.cos(math.radians(self.angle))) + 0.001
    myCurveLb.location.z = 0
        
    myCurveCb.location.x = 0
    myCurveCb.location.y = ((self.depth/2) * math.cos(math.radians(self.angle))) + 0.001    
    myCurveCb.location.z = 0
        
    myCurveRb.location.x = -(self.width/2) + sep
    myCurveRb.location.y = ((self.depth/2) * math.cos(math.radians(self.angle))) + 0.001    
    myCurveRb.location.z = 0
        
    if (self.crt_mat):
        set_material(myCurveLb, mat)
        set_material(myCurveCb, mat)
        set_material(myCurveRb, mat)
    
    #------------------ 
    # Bottom
    #------------------ 
    myBase = create_venetian_base("Venetian_base",self.width + 0.002,self.depth + 0.002,-0.006)
    myBase.parent = mySlats
    myBase.location.x = 0
    myBase.location.y = 0
    myBase.location.z = myPoints[len(myPoints) - 1]
    myBase.rotation_euler = (math.radians(angleUsed),0,0)

    # materials
    if (self.crt_mat):
        set_material(myBase, plastic)
    #------------------ 
    # Stick
    #------------------ 
    myStick = get_venetian_stick("Venetian_stick",self.height * 0.6)
    myStick.parent = myTop
    myStick.location.x = -self.width / 2 + 0.03
    myStick.location.y = -self.depth/2 - 0.003
    myStick.location.z = -0.03
    # materials
    if (self.crt_mat):
        matstick = create_diffuse_material("Stick_material", False, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.04)
        set_material(myBase, matstick)
    
    #------------------ 
    # Strings up/down
    #------------------ 
    myString = get_venetian_strings("Venetian_updown",self.height * 0.75)
    myString.parent = myTop
    myString.location.x = self.width / 2 - 0.03
    myString.location.y = -self.depth/2 - 0.003
    myString.location.z = -0.03
    
    if (self.crt_mat):
        set_material(myString, mat)

    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    
#     myRoller.select = True        
#     bpy.context.scene.objects.active = myRoller
    
    return
#------------------------------------------------------------
# Create venetian slats
#
# width: total width of the slat
# depth: depth of the slat
# height: Total height (extended)
# ratio: factor of extension 0-collapsed 100-extended
# angle: angle
#------------------------------------------------------------
def create_slat_mesh(objName,width,depth,height,angle,ratio):
    # Vertex
    v = 0
    gap = 0.001
    angleUsed = 0
    myVertex = []
    myFaces = []
    myPoints = []
    # Calculate total slats
    separation = (depth * 0.75) # posZ is % of depth
    numSlats = int(height / separation)
    collapsedSlats = numSlats -  int((height * ((100-ratio)/100))/separation)
    #--------------------------------
    # Generate slats
    #--------------------------------
    posZ = 0    
    for x in range(numSlats):
        # if the slat is collapsed, the angle is 0
        if (x < collapsedSlats):
            angleUsed = angle
        elif ( x == collapsedSlats):
            angleUsed = angle/2
        else:
            angleUsed = 0        
         
        myData = get_slat_data(v,angleUsed,width,depth,posZ) 
        myPoints.extend([posZ]) # saves all Z points
        myVertex.extend(myData[0])
        myFaces.extend(myData[1])
        v = myData[2]
        if (x < collapsedSlats):
            posZ = posZ - separation
        else:
            posZ = posZ - gap     
        # Transition to horizontal
        if (angleUsed == angle/2):
            sinHeight = math.sin(math.radians(angle/2)) * depth/2
            posZ = posZ - sinHeight


    mesh = bpy.data.meshes.new(objName)
    myObject = bpy.data.objects.new(objName, mesh)
    
    myObject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myObject)
    
    mesh.from_pydata(myVertex, [], myFaces)
    mesh.update(calc_edges=True)

    return (myObject,myPoints,angleUsed)
#------------------------------------------------------------
# Generate slat data for venetian slat mesh
#
# v: last vertex index
# angle: angle
# width: total width of the slat
# depth: depth of the slat
# posZ: position in Z axis
#------------------------------------------------------------
def get_slat_data(v,angle,width,depth,posZ):
    #------------------------------------
    # Mesh data
    #------------------------------------
    maxX = width/2
    minY = -depth/2
    maxY = depth/2
    maxZ = 0.0028
    gap = 0.0025
    radio = 0.00195
    sinV = math.sin(math.atan(maxZ/(maxY-gap)))
    cos = math.cos(math.radians(angle))
    sin = math.sin(math.radians(angle))
    
    if (width < 0.60):
        sep = 0.06
    else:
        sep = 0.15
    
    sep2 = sep - 0.005
    
    # Vertex
    myVertex = []
      
    myVertex.extend([(maxX - 0.0017,(minY + 0.00195) * cos,posZ + (-maxZ + (radio * sinV)) + ((minY + 0.00195) * sin)) 
    ,(maxX - 0.0017,(maxY - 0.00195) * cos,posZ + (-maxZ + (radio * sinV)) + ((maxY - 0.00195) * sin)) 
    ,(maxX - 0.0045,minY * cos,posZ + -maxZ + (minY * sin))
    ,(maxX - 0.0045,maxY * cos,posZ + -maxZ + (maxY * sin))
    ,(maxX,-gap * cos,posZ + (-gap*sin))
    ,(maxX,gap * cos,posZ + (gap*sin))
    ,(maxX - 0.0045,-gap * cos,posZ + (-gap*sin))
    ,(maxX - 0.0045,gap* cos,posZ + (gap*sin))
    ,(0.001172,minY*cos,posZ + -maxZ + (minY * sin))
    ,(0.001172,maxY*cos,posZ + -maxZ + (maxY * sin))
    ,(0.001172,-gap*cos,posZ + (-gap*sin))
    ,(0.001172,gap*cos,posZ + (gap*sin))
    ,(maxX - sep,minY*cos,posZ + -maxZ + (minY * sin))
    ,(maxX - sep,maxY*cos,posZ + -maxZ + (maxY * sin))
    ,(maxX - sep,-gap*cos,posZ + (-gap*sin)) 
    ,(maxX - sep,gap*cos,posZ + (gap*sin)) 
    ,(maxX - sep2,minY*cos,posZ + -maxZ + (minY * sin))
    ,(maxX - sep2,maxY*cos,posZ + -maxZ + (maxY * sin))
    ,(maxX - sep2,-gap*cos,posZ + (-gap*sin)) 
    ,(maxX - sep2,gap*cos,posZ + (gap*sin))]) 
   
    myVertex.extend([(-maxX + 0.0017,(minY + 0.00195) * cos,posZ + (-maxZ + (radio * sinV)) + ((minY + 0.00195) * sin)) 
    ,(-maxX + 0.0017,(maxY - 0.00195) * cos,posZ + (-maxZ + (radio * sinV)) + ((maxY - 0.00195) * sin)) 
    ,(-maxX + 0.0045,minY * cos,posZ + -maxZ + (minY * sin))
    ,(-maxX + 0.0045,maxY * cos,posZ + -maxZ + (maxY * sin))
    ,(-maxX,-gap * cos,posZ + (-gap*sin))
    ,(-maxX,gap * cos,posZ + (gap*sin))
    ,(-maxX + 0.0045,-gap * cos,posZ + (-gap*sin))
    ,(-maxX + 0.0045,gap* cos,posZ + (gap*sin))
    ,(-0.001172,minY*cos,posZ + -maxZ + (minY * sin))
    ,(-0.001172,maxY*cos,posZ + -maxZ + (maxY * sin))
    ,(-0.001172,-gap*cos,posZ + (-gap*sin))
    ,(-0.001172,gap*cos,posZ + (gap*sin))
    ,(-maxX + sep,minY*cos,posZ + -maxZ + (minY * sin))
    ,(-maxX + sep,maxY*cos,posZ + -maxZ + (maxY * sin))
    ,(-maxX + sep,-gap*cos,posZ + (-gap*sin)) 
    ,(-maxX + sep,gap*cos,posZ + (gap*sin)) 
    ,(-maxX + sep2,minY*cos,posZ + -maxZ + (minY * sin))
    ,(-maxX + sep2,maxY*cos,posZ + -maxZ + (maxY * sin))
    ,(-maxX + sep2,-gap*cos,posZ + (-gap*sin)) 
    ,(-maxX + sep2,gap*cos,posZ + (gap*sin))]) 

    # Faces
    myFaces = [(v+7,v+5,v+1,v+3),(v+19,v+7,v+3,v+17),(v+2,v+0,v+4,v+6),(v+6,v+4,v+5,v+7),(v+16,v+2,v+6,v+18)
    ,(v+18,v+6,v+7,v+19),(v+11,v+15,v+13,v+9),(v+8,v+12,v+14,v+10),(v+10,v+14,v+15,v+11),(v+15,v+19,v+17,v+13)
    ,(v+12,v+16,v+18,v+14),(v+39,v+35,v+33,v+37),(v+34,v+38,v+36,v+32),(v+27,v+25,v+21,v+23),(v+27,v+26,v+24,v+25)
    ,(v+24,v+26,v+22,v+20),(v+39,v+37,v+23,v+27),(v+39,v+27,v+26,v+38),(v+38,v+26,v+22,v+36),(v+30,v+34,v+32,v+28)
    ,(v+34,v+30,v+31,v+35),(v+35,v+31,v+29,v+33),(v+11,v+9,v+29,v+31),(v+8,v+10,v+30,v+28)]
                    
    v = v + len(myVertex)
    
    return (myVertex,myFaces,v)
#------------------------------------------------------------------------------
# Create rectangular base
#
# objName: Object name
# x: size x axis
# y: size y axis
# z: size z axis
#------------------------------------------------------------------------------
def create_venetian_base(objName,x,y,z):

    myVertex = [(-x/2, -y/2, 0.0)
                ,(-x/2, y/2, 0.0)
                ,(x/2, y/2, 0.0)
                ,(x/2, -y/2, 0.0)
                ,(-x/2, -y/2, z)
                ,(-x/2, y/2, z)
                ,(x/2, y/2, z)
                ,(x/2, -y/2, z)]
    
    myFaces = [(0,1,2,3),(0,1,5,4),(1,2,6,5),(2,6,7,3),(5,6,7,4),(0,4,7,3)]
    
    mesh = bpy.data.meshes.new(objName)
    myobject = bpy.data.objects.new(objName, mesh)
    
    myobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myobject)
    
    mesh.from_pydata(myVertex, [], myFaces)
    mesh.update(calc_edges=True)
   
    return myobject

#------------------------------------------------------------
# Generate stick for venetian 
#
# objName: Object name
# height: height
#------------------------------------------------------------
def get_venetian_stick(objName,height):
    #------------------------------------
    # Mesh data
    #------------------------------------
    minX = -0.005686083808541298
    maxX = 0.005686083808541298
    minY = 0.0 # locked
    lockY = -0.015877623111009598
    maxY = 0
    #minZ = -0.2236524224281311
    minZ = -height
    maxZ = 0
    
    # Vertex
    myVertex = [(minX + 0.0031912513077259064,-0.012805024161934853,maxZ - 0.02722930908203125)
    ,(minX + 0.0030460257548838854,-0.007894348353147507,maxZ - 0.008386015892028809)
    ,(minX + 0.003936204360798001,-0.014603500254452229,maxZ - 0.02722930908203125)
    ,(minX + 0.003812092007137835,-0.006685533560812473,maxZ - 0.009785711765289307)
    ,(maxX - 0.005637487949570641,-0.01534845307469368,maxZ - 0.02722930908203125)
    ,(minX + 0.005661540681103361,-0.006184821017086506,maxZ - 0.010365545749664307)
    ,(maxX - 0.0038390127010643482,-0.014603500254452229,maxZ - 0.02722930908203125)
    ,(maxX - 0.0038611787604168057,-0.006685533560812473,maxZ - 0.009785711765289307)
    ,(maxX - 0.0030940594151616096,-0.012805024161934853,maxZ - 0.02722930908203125)
    ,(maxX - 0.0030951115768402815,-0.007894348353147507,maxZ - 0.008386015892028809)
    ,(maxX - 0.0038390120025724173,-0.011006549000740051,maxZ - 0.02722930908203125)
    ,(maxX - 0.0038611781783401966,-0.009103144519031048,maxZ - 0.0069863200187683105)
    ,(maxX - 0.005637487425701693,-0.010261595249176025,maxZ - 0.02722930908203125)
    ,(minX + 0.005661541004883475,-0.00960385799407959,maxZ - 0.0064064860343933105)
    ,(minX + 0.003936204593628645,-0.011006549000740051,maxZ - 0.02722930908203125)
    ,(minX + 0.003812092822045088,-0.009103145450353622,maxZ - 0.0069863200187683105)
    ,(minX + 0.004708557506091893,-0.0009992714039981365,maxZ - 0.002431390807032585)
    ,(minX + 0.004987679829355329,-0.0009992715204134583,maxZ - 0.0031052385456860065)
    ,(minX + 0.005661541195877362,-0.0009992715204134583,maxZ - 0.0033843691926449537)
    ,(maxX - 0.00503676530206576,-0.0009992715204134583,maxZ - 0.0031052385456860065)
    ,(maxX - 0.004757642629556358,-0.0009992716368287802,maxZ - 0.002431390807032585)
    ,(maxX - 0.005036764952819794,-0.0009992715204134583,maxZ - 0.0017575474921613932)
    ,(minX + 0.005661541457811836,-0.0009992715204134583,maxZ - 0.0014784171944484115)
    ,(minX + 0.004987680295016617,-0.0009992715204134583,maxZ - 0.0017575474921613932)
    ,(minX + 0.0038341645849868655,-0.010904508642852306,maxZ - 0.015928268432617188)
    ,(maxX - 0.005637487367494032,-0.01011728961020708,maxZ - 0.015928268432617188)
    ,(maxX - 0.003736971877515316,-0.010904508642852306,maxZ - 0.015928268432617188)
    ,(maxX - 0.002949752612039447,-0.012805024161934853,maxZ - 0.015928268432617188)
    ,(maxX - 0.0037369721103459597,-0.014705540612339973,maxZ - 0.015928268432617188)
    ,(maxX - 0.00563748789136298,-0.015492759644985199,maxZ - 0.015928268432617188)
    ,(minX + 0.0038341644685715437,-0.014705540612339973,maxZ - 0.015928268432617188)
    ,(minX + 0.003046944970265031,-0.012805024161934853,maxZ - 0.015928268432617188)
    ,(minX + 0.0043586865067481995,-0.012638782151043415,maxZ - 0.013130486011505127)
    ,(minX + 0.004740283475257456,-0.0120366420596838,maxZ - 0.013827741146087646)
    ,(minX + 0.0056615397916175425,-0.011787224560976028,maxZ - 0.014116525650024414)
    ,(maxX - 0.004789371509104967,-0.0120366420596838,maxZ - 0.013827741146087646)
    ,(maxX - 0.0044077744241803885,-0.012638782151043415,maxZ - 0.013130486011505127)
    ,(maxX - 0.0047893712762743235,-0.013240913860499859,maxZ - 0.012433230876922607)
    ,(minX + 0.005661539897118928,-0.01349033135920763,maxZ - 0.01214444637298584)
    ,(minX + 0.004740283824503422,-0.013240914791822433,maxZ - 0.012433230876922607)
    ,(minX + 0.005661537383275572,-0.012638770043849945,maxZ - 0.017504926770925522)
    ,(maxX - 0.0039202586049214005,-0.010174507275223732,maxZ - 0.015622403472661972)
    ,(maxX - 0.0028137227054685354,-0.013580016791820526,maxZ - 0.015622403472661972)
    ,(minX + 0.005661537154082907,-0.015684761106967926,maxZ - 0.015622403472661972)
    ,(minX + 0.0027646280359476805,-0.013580016791820526,maxZ - 0.015622403472661972)
    ,(minX + 0.003871166962198913,-0.010174507275223732,maxZ - 0.015622403472661972)
    ,(maxX - 0.0028137224726378918,-0.011697524227201939,maxZ - 0.01257637981325388)
    ,(maxX - 0.003920258954167366,-0.015103034675121307,maxZ - 0.01257637981325388)
    ,(minX + 0.0038711666129529476,-0.015103034675121307,maxZ - 0.01257637981325388)
    ,(minX + 0.002764628268778324,-0.011697524227201939,maxZ - 0.01257637981325388)
    ,(minX + 0.0056615376142872265,-0.00959277804940939,maxZ - 0.01257637981325388)
    ,(minX + 0.005661537383275572,-0.012638770043849945,maxZ - 0.010693902149796486)
    ,(maxX - 0.004007883137091994,-0.013192017562687397,maxZ - 0.016996320337057114)
    ,(maxX - 0.004658283665776253,-0.011190323159098625,maxZ - 0.016996320337057114)
    ,(maxX - 0.002955520059913397,-0.011743564158678055,maxZ - 0.015889829024672508)
    ,(minX + 0.00566153760337329,-0.009741866029798985,maxZ - 0.015889829024672508)
    ,(minX + 0.0046091912081465125,-0.011190323159098625,maxZ - 0.016996320337057114)
    ,(minX + 0.005661537248670356,-0.014429156668484211,maxZ - 0.016996320337057114)
    ,(maxX - 0.004007878364063799,-0.014982416294515133,maxZ - 0.015889829024672508)
    ,(minX + 0.003958789980970323,-0.013192017562687397,maxZ - 0.016996320337057114)
    ,(minX + 0.00395878404378891,-0.014982416294515133,maxZ - 0.015889829024672508)
    ,(minX + 0.002906427951529622,-0.011743564158678055,maxZ - 0.015889829024672508)
    ,(maxX - 0.004658278776332736,-0.009399918839335442,maxZ - 0.014099414460361004)
    ,(minX + 0.004609186435118318,-0.009399918839335442,maxZ - 0.014099414460361004)
    ,(maxX - 0.0023051041644066572,-0.012638770043849945,maxZ - 0.014099414460361004)
    ,(maxX - 0.0029555035289376974,-0.010637051425874233,maxZ - 0.014099414460361004)
    ,(maxX - 0.004658279241994023,-0.015877623111009598,maxZ - 0.014099414460361004)
    ,(maxX - 0.0029555039945989847,-0.014640489593148232,maxZ - 0.014099414460361004)
    ,(minX + 0.0029064100235700607,-0.014640489593148232,maxZ - 0.014099414460361004)
    ,(minX + 0.00460918596945703,-0.015877623111009598,maxZ - 0.014099414460361004)
    ,(minX + 0.002906410489231348,-0.010637051425874233,maxZ - 0.014099414460361004)
    ,(minX + 0.0022560113575309515,-0.012638770043849945,maxZ - 0.014099414460361004)
    ,(maxX - 0.004007878014817834,-0.010295123793184757,maxZ - 0.012308954261243343)
    ,(maxX - 0.002955520059913397,-0.013533977791666985,maxZ - 0.012308954261243343)
    ,(minX + 0.005661537164996844,-0.015535674057900906,maxZ - 0.012308954261243343)
    ,(minX + 0.0029064277186989784,-0.013533977791666985,maxZ - 0.012308954261243343)
    ,(minX + 0.003958784393034875,-0.010295123793184757,maxZ - 0.012308954261243343)
    ,(maxX - 0.004007883137091994,-0.012085524387657642,maxZ - 0.011202462017536163)
    ,(minX + 0.0056615375196997775,-0.01084838341921568,maxZ - 0.011202462017536163)
    ,(maxX - 0.004658283898606896,-0.01408721785992384,maxZ - 0.011202462017536163)
    ,(minX + 0.004609190975315869,-0.01408721785992384,maxZ - 0.011202462017536163)
    ,(minX + 0.003958789980970323,-0.012085524387657642,maxZ - 0.011202462017536163)
    ,(minX + 0.003936204593628645,-0.011006549000740051,minZ)
    ,(maxX - 0.005637487425701693,-0.010261595249176025,minZ)
    ,(maxX - 0.0038390120025724173,-0.011006549000740051,minZ)
    ,(maxX - 0.0030940594151616096,-0.012805024161934853,minZ)
    ,(maxX - 0.0038390127010643482,-0.014603500254452229,minZ)
    ,(maxX - 0.005637487949570641,-0.01534845307469368,minZ)
    ,(minX + 0.003936204360798001,-0.014603500254452229,minZ)
    ,(minX + 0.0031912513077259064,-0.012805024161934853,minZ)
    ,(minX,-0.001379312016069889,maxZ - 0.005334946792572737)
    ,(minX,-4.6566128730773926e-09,maxZ - 0.005334946792572737)
    ,(maxX,-4.6566128730773926e-09,maxZ - 0.005334946792572737)
    ,(maxX,-0.001379312016069889,maxZ - 0.005334946792572737)
    ,(minX,-0.001379312016069889,maxZ - 1.5133991837501526e-08)
    ,(minX,-4.6566128730773926e-09,maxZ - 1.5133991837501526e-08)
    ,(maxX,-4.6566128730773926e-09,maxZ - 1.5133991837501526e-08)
    ,(maxX,-0.001379312016069889,maxZ - 1.5133991837501526e-08)
    ,(minX + 0.0009754756465554237,-0.001379312016069889,maxZ - 0.00447732862085104)
    ,(minX + 0.0009754756465554237,-0.001379312016069889,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0009754756465554237,-0.001379312016069889,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0009754756465554237,-0.001379312016069889,maxZ - 0.00447732862085104)
    ,(minX + 0.0009754756465554237,-0.0007799165323376656,maxZ - 0.00447732862085104)
    ,(minX + 0.0009754756465554237,-0.0007799165323376656,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0009754756465554237,-0.0007799165323376656,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0009754756465554237,-0.0007799165323376656,maxZ - 0.00447732862085104)]
    
    # Faces
    myFaces = [(1, 15, 23, 16),(17, 16, 23, 22, 21, 20, 19, 18),(15, 13, 22, 23),(13, 11, 21, 22),(11, 9, 20, 21)
    ,(9, 7, 19, 20),(7, 5, 18, 19),(5, 3, 17, 18),(3, 1, 16, 17),(0, 31, 24, 14)
    ,(14, 24, 25, 12),(12, 25, 26, 10),(10, 26, 27, 8),(8, 27, 28, 6),(6, 28, 29, 4)
    ,(2, 30, 31, 0),(4, 29, 30, 2),(15, 1, 32, 39),(13, 15, 39, 38),(11, 13, 38, 37)
    ,(9, 11, 37, 36),(7, 9, 36, 35),(5, 7, 35, 34),(3, 5, 34, 33),(1, 3, 33, 32)
    ,(40, 53, 52),(41, 53, 55),(40, 52, 57),(40, 57, 59),(40, 59, 56)
    ,(41, 55, 62),(42, 54, 64),(43, 58, 66),(44, 60, 68),(45, 61, 70)
    ,(41, 62, 65),(42, 64, 67),(43, 66, 69),(44, 68, 71),(45, 70, 63)
    ,(46, 72, 77),(47, 73, 79),(48, 74, 80),(49, 75, 81),(50, 76, 78)
    ,(52, 54, 42),(52, 53, 54),(53, 41, 54),(55, 56, 45),(55, 53, 56)
    ,(53, 40, 56),(57, 58, 43),(57, 52, 58),(52, 42, 58),(59, 60, 44)
    ,(59, 57, 60),(57, 43, 60),(56, 61, 45),(56, 59, 61),(59, 44, 61)
    ,(62, 63, 50),(62, 55, 63),(55, 45, 63),(64, 65, 46),(64, 54, 65)
    ,(54, 41, 65),(66, 67, 47),(66, 58, 67),(58, 42, 67),(68, 69, 48)
    ,(68, 60, 69),(60, 43, 69),(70, 71, 49),(70, 61, 71),(61, 44, 71)
    ,(65, 72, 46),(65, 62, 72),(62, 50, 72),(67, 73, 47),(67, 64, 73)
    ,(64, 46, 73),(69, 74, 48),(69, 66, 74),(66, 47, 74),(71, 75, 49)
    ,(71, 68, 75),(68, 48, 75),(63, 76, 50),(63, 70, 76),(70, 49, 76)
    ,(77, 78, 51),(77, 72, 78),(72, 50, 78),(79, 77, 51),(79, 73, 77)
    ,(73, 46, 77),(80, 79, 51),(80, 74, 79),(74, 47, 79),(81, 80, 51)
    ,(81, 75, 80),(75, 48, 80),(78, 81, 51),(78, 76, 81),(76, 49, 81)
    ,(87, 4, 2, 88),(88, 2, 0, 89),(86, 6, 4, 87),(85, 8, 6, 86),(84, 10, 8, 85)
    ,(83, 12, 10, 84),(82, 14, 12, 83),(89, 0, 14, 82),(94, 95, 91, 90),(95, 96, 92, 91)
    ,(96, 97, 93, 92),(98, 101, 105, 102),(90, 91, 92, 93),(97, 96, 95, 94),(98, 99, 94, 90)
    ,(100, 101, 93, 97),(99, 100, 97, 94),(101, 98, 90, 93),(104, 103, 102, 105),(100, 99, 103, 104)
    ,(101, 100, 104, 105),(99, 98, 102, 103)]
    
    mesh = bpy.data.meshes.new(objName)
    myObject = bpy.data.objects.new(objName, mesh)
    
    myObject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myObject)
    
    mesh.from_pydata(myVertex, [], myFaces)
    mesh.update(calc_edges=True)

    return (myObject)

#------------------------------------------------------------
# Generate strings for venetian 
#
# objName: Object name
# height: height
#------------------------------------------------------------
def get_venetian_strings(objName,height):
    #------------------------------------
    # Mesh data
    #------------------------------------
    minX = -0.006897219456732273
    maxX = 0.006897197104990482
    maxY = 1.57160684466362e-08
    minZ = -height
    maxZ = 0
    
    # Vertex
    myVertex = [(maxX - 0.004941887455061078,-0.005041633266955614,minZ + 3.1925737857818604e-05)
    ,(maxX - 0.005070153623819351,-0.004731120076030493,minZ + 4.9524009227752686e-05)
    ,(maxX - 0.005380495102144778,-0.004602177534252405,minZ + 5.389750003814697e-05)
    ,(maxX - 0.005691118887625635,-0.00473033869639039,minZ + 4.2498111724853516e-05)
    ,(maxX - 0.005820065038278699,-0.005040528252720833,minZ + 2.1979212760925293e-05)
    ,(maxX - 0.005691798985935748,-0.005351040977984667,minZ + 4.380941390991211e-06)
    ,(maxX - 0.005381457391194999,-0.0054799835197627544,minZ)
    ,(maxX - 0.005070833722129464,-0.005351822357624769,minZ + 1.1406838893890381e-05)
    ,(maxX - 0.005004765349440277,-0.005394590552896261,minZ + 0.029493853449821472)
    ,(maxX - 0.005133012658916414,-0.005083992145955563,minZ + 0.02950144186615944)
    ,(maxX - 0.005443348782137036,-0.004955026786774397,minZ + 0.029502809047698975)
    ,(maxX - 0.005753983394242823,-0.005083239171653986,minZ + 0.02949715033173561)
    ,(maxX - 0.0058829509653151035,-0.005393524654209614,minZ + 0.02948778122663498)
    ,(maxX - 0.005754703655838966,-0.005704122595489025,minZ + 0.029480192810297012)
    ,(maxX - 0.005444367183372378,-0.005833088420331478,minZ + 0.029478825628757477)
    ,(maxX - 0.005133732687681913,-0.005704876501113176,minZ + 0.02948448434472084)
    ,(maxX - 0.005029367166571319,-0.005440863780677319,maxZ - 0.029401594772934914)
    ,(maxX - 0.005157589330337942,-0.005130413919687271,maxZ - 0.029417745769023895)
    ,(maxX - 0.005467916373163462,-0.005001509562134743,maxZ - 0.029425399377942085)
    ,(maxX - 0.005778562976047397,-0.0051296609453856945,maxZ - 0.029420070350170135)
    ,(maxX - 0.005907556158490479,-0.00543979974463582,maxZ - 0.029404880478978157)
    ,(maxX - 0.005779333529062569,-0.005750249605625868,maxZ - 0.029388729482889175)
    ,(maxX - 0.005469006602652371,-0.005879154894500971,maxZ - 0.029381075873970985)
    ,(maxX - 0.005158359999768436,-0.0057510025799274445,maxZ - 0.029386404901742935)
    ,(maxX - 0.00503770902287215,-0.005161902867257595,maxZ - 0.015295670367777348)
    ,(maxX - 0.00516585458535701,-0.004854197148233652,maxZ - 0.015373632311820984)
    ,(maxX - 0.005476148682646453,-0.00472648162394762,maxZ - 0.01540757529437542)
    ,(maxX - 0.0057868254370987415,-0.004853568039834499,maxZ - 0.015377615578472614)
    ,(maxX - 0.005915894289501011,-0.005161012522876263,maxZ - 0.015301303938031197)
    ,(maxX - 0.0057877483777701855,-0.005468717776238918,maxZ - 0.015223342925310135)
    ,(maxX - 0.005477453931234777,-0.005596434231847525,maxZ - 0.01518939808011055)
    ,(maxX - 0.005166777293197811,-0.005469346884638071,maxZ - 0.01521935872733593)
    ,(maxX - 0.0050518905045464635,-0.004537198692560196,maxZ - 0.007016266230493784)
    ,(maxX - 0.0051788275595754385,-0.004260011948645115,maxZ - 0.007274628151208162)
    ,(maxX - 0.005488568218424916,-0.004146246705204248,maxZ - 0.007390326354652643)
    ,(maxX - 0.005799670936539769,-0.004262544680386782,maxZ - 0.007295588497072458)
    ,(maxX - 0.005929895443841815,-0.004540780559182167,maxZ - 0.007045908365398645)
    ,(maxX - 0.0058029580395668745,-0.004817967768758535,maxZ - 0.006787544582039118)
    ,(maxX - 0.005493217264302075,-0.004931733012199402,maxZ - 0.006671848241239786)
    ,(maxX - 0.005182114546187222,-0.004815434105694294,maxZ - 0.006766586098819971)
    ,(maxX - 0.005094519350677729,-0.0035386907402426004,maxZ - 0.003334574867039919)
    ,(maxX - 0.005213141208514571,-0.0034136706963181496,maxZ - 0.0038649537600576878)
    ,(maxX - 0.005518985213711858,-0.003371135564520955,maxZ - 0.004107045475393534)
    ,(maxX - 0.0058328923769295216,-0.0034360019490122795,maxZ - 0.003919033799320459)
    ,(maxX - 0.005970980157144368,-0.003570271423086524,maxZ - 0.003411055076867342)
    ,(maxX - 0.005852358415722847,-0.003695291467010975,maxZ - 0.002880676183849573)
    ,(maxX - 0.005546514177694917,-0.0037378265988081694,maxZ - 0.002638584468513727)
    ,(maxX - 0.005232607247307897,-0.003672960214316845,maxZ - 0.0028265961445868015)
    ,(maxX - 0.005944175529293716,-0.0036394987255334854,maxZ - 0.003126396331936121)
    ,(maxX - 0.005875613423995674,-0.00560829509049654,maxZ - 0.02939625270664692)
    ,(maxX - 0.005034194211475551,-0.005343204364180565,maxZ - 0.021542727947235107)
    ,(maxX - 0.005612890352495015,-0.00580073706805706,minZ + 0.029478538781404495)
    ,(maxX - 0.0052128632087260485,-0.005448057781904936,minZ + 3.8817524909973145e-06)
    ,(maxX - 0.005320212687365711,-0.004174317233264446,maxZ - 0.007358333561569452)
    ,(maxX - 0.005857669049873948,-0.005254213232547045,minZ + 0.01586836576461792)
    ,(maxX - 0.005270682042464614,-0.002958775730803609,maxZ - 0.0018540903693065047)
    ,(maxX - 0.004973854636773467,-0.004873105324804783,minZ + 4.190206527709961e-05)
    ,(maxX - 0.005896858056075871,-0.0043898820877075195,maxZ - 0.007182727102190256)
    ,(maxX - 0.005644757067784667,-0.004758160561323166,maxZ - 0.015400669537484646)
    ,(maxX - 0.0050204748986288905,-0.0054572150111198425,maxZ - 0.03902619704604149)
    ,(maxX - 0.005107744364067912,-0.004944739863276482,minZ + 0.01588994264602661)
    ,(maxX - 0.005821454804390669,-0.004324669484049082,maxZ - 0.004334418568760157)
    ,(maxX - 0.0058509946102276444,-0.00556210009381175,minZ + 0.029483404010534286)
    ,(maxX - 0.004974223440513015,-0.005210080184042454,minZ + 2.121180295944214e-05)
    ,(maxX - 0.005512951058335602,-0.004414208233356476,maxZ - 0.004156060982495546)
    ,(maxX - 0.005657264497131109,-0.004175691865384579,maxZ - 0.007369710598140955)
    ,(maxX - 0.005083143012598157,-0.004386562388390303,maxZ - 0.007155258674174547)
    ,(maxX - 0.005898642586544156,-0.004691417329013348,maxZ - 0.006906915921717882)
    ,(maxX - 0.005482866894453764,-0.005316956900060177,maxZ - 0.010308705270290375)
    ,(maxX - 0.005200946354307234,-0.004315671045333147,maxZ - 0.004297847393900156)
    ,(maxX - 0.005883492063730955,-0.004994065500795841,maxZ - 0.015342974103987217)
    ,(maxX - 0.0055490892846137285,-0.004634103272110224,minZ + 5.002319812774658e-05)
    ,(maxX - 0.005586991785094142,-0.002982017118483782,maxZ - 0.0016202632104977965)
    ,(maxX - 0.005500998347997665,-0.0037720794789493084,maxZ - 0.005249096546322107)
    ,(maxX - 0.0056365174241364,-0.005033436696976423,maxZ - 0.029424406588077545)
    ,(maxX - 0.0051623902982100844,-0.0050335354171693325,maxZ - 0.021582692861557007)
    ,(maxX - 0.005850603571161628,-0.005225026980042458,minZ + 0.029492609202861786)
    ,(maxX - 0.005787728703580797,-0.0048720804043114185,minZ + 3.269314765930176e-05)
    ,(maxX - 0.005192494718357921,-0.003861617762595415,maxZ - 0.005070738960057497)
    ,(maxX - 0.005163213470950723,-0.005652572028338909,maxZ - 0.021503763273358345)
    ,(maxX - 0.005460095009766519,-0.005895696114748716,maxZ - 0.039026711136102676)
    ,(maxX - 0.005661572678945959,-0.004903662484139204,maxZ - 0.006703841034322977)
    ,(maxX - 0.005856060888618231,-0.002980045508593321,maxZ - 0.003230756614357233)
    ,(maxX - 0.005036721588112414,-0.005226014647632837,minZ + 0.029498230665922165)
    ,(maxX - 0.005933607462793589,-0.0034987321123480797,maxZ - 0.0036901147104799747)
    ,(maxX - 0.005068209487944841,-0.0040867808274924755,maxZ - 0.004676718730479479)
    ,(maxX - 0.005645966622978449,-0.005564413033425808,maxZ - 0.015198467299342155)
    ,(maxX - 0.005149454576894641,-0.005767486989498138,maxZ - 0.03902563825249672)
    ,(maxX - 0.0050617282977327704,-0.005609281826764345,maxZ - 0.029393207281827927)
    ,(maxX - 0.005539751029573381,-0.0029568036552518606,maxZ - 0.0034645837731659412)
    ,(maxX - 0.005688222707249224,-0.003390622790902853,maxZ - 0.00406796345487237)
    ,(maxX - 0.005419071996584535,-0.005693721119314432,minZ + 0.0158514603972435)
    ,(maxX - 0.005788097972981632,-0.005209055729210377,minZ + 1.1995434761047363e-05)
    ,(maxX - 0.005069609847851098,-0.004994889721274376,maxZ - 0.015337754040956497)
    ,(maxX - 0.005299395183101296,-0.0050338455475866795,maxZ - 0.029423145577311516)
    ,(maxX - 0.005729411728680134,-0.005564768332988024,minZ + 0.015854761004447937)
    ,(maxX - 0.005889465333893895,-0.002997873816639185,maxZ - 0.0019266236340627074)
    ,(maxX - 0.00523727759718895,-0.002940947189927101,maxZ - 0.0031582233496010303)
    ,(maxX - 0.005883992882445455,-0.0053280252031981945,maxZ - 0.015259221196174622)
    ,(maxX - 0.005637527909129858,-0.0058468179777264595,maxZ - 0.029383329674601555)
    ,(maxX - 0.0060009173466823995,-0.002997057046741247,maxZ - 0.0025937133468687534)
    ,(maxX - 0.00581300281919539,-0.0038706157356500626,maxZ - 0.005107311997562647)
    ,(maxX - 0.005784186767414212,-0.005651846993714571,maxZ - 0.02150617726147175)
    ,(maxX - 0.005061309668235481,-0.005272367969155312,maxZ - 0.02941022254526615)
    ,(maxX - 0.00535176380071789,-0.0033784990664571524,maxZ - 0.004038602579385042)
    ,(maxX - 0.005131891928613186,-0.0036102300509810448,maxZ - 0.0030555170960724354)
    ,(maxX - 0.0059457405004650354,-0.004099506419152021,maxZ - 0.004728438798338175)
    ,(maxX - 0.005791432806290686,-0.004595593549311161,maxZ - 0.010660232976078987)
    ,(maxX - 0.005473870667628944,-0.005780417006462812,maxZ - 0.021488623693585396)
    ,(maxX - 0.005108443321660161,-0.005565532948821783,minZ + 0.01586039364337921)
    ,(maxX - 0.005042683565989137,-0.00489416578784585,maxZ - 0.01050524227321148)
    ,(maxX - 0.0053004054352641106,-0.005847226828336716,maxZ - 0.029382066801190376)
    ,(maxX - 0.005324521102011204,-0.004902287386357784,maxZ - 0.006692463997751474)
    ,(maxX - 0.0053076359909027815,-0.00475850235670805,maxZ - 0.015398506075143814)
    ,(maxX - 0.005770427291281521,-0.005766738206148148,maxZ - 0.03902877867221832)
    ,(maxX - 0.005377276800572872,-0.0037183398380875587,maxZ - 0.0026776683516800404)
    ,(maxX - 0.005898662726394832,-0.005456155631691217,maxZ - 0.03903063386678696)
    ,(maxX - 0.005084927543066442,-0.004688097629696131,maxZ - 0.006879445631057024)
    ,(maxX - 0.005037112743593752,-0.0055630882270634174,minZ + 0.029489029198884964)
    ,(maxX - 0.0050701110158115625,-0.0053288498893380165,maxZ - 0.015254000201821327)
    ,(maxX - 0.005418083746917546,-0.004815786611288786,minZ + 0.01589323580265045)
    ,(maxX - 0.005308845662511885,-0.0055647543631494045,maxZ - 0.015196305699646473)
    ,(maxX - 0.0054806380067020655,-0.0044716945849359035,maxZ - 0.010715048760175705)
    ,(maxX - 0.005459042498841882,-0.005017674993723631,maxZ - 0.03903011977672577)
    ,(maxX - 0.00571373593993485,-0.0037304633297026157,maxZ - 0.0027070273645222187)
    ,(maxX - 0.005125825526192784,-0.0029417641926556826,maxZ - 0.002491133753210306)
    ,(maxX - 0.005783363711088896,-0.005032809916883707,maxZ - 0.02158510498702526)
    ,(maxX - 0.005121324211359024,-0.003469463437795639,maxZ - 0.00361923361197114)
    ,(maxX - 0.005170495598576963,-0.0045953672379255295,maxZ - 0.010650848969817162)
    ,(maxX - 0.005611946457065642,-0.004986968822777271,minZ + 0.02950076386332512)
    ,(maxX - 0.005769683048129082,-0.005145883187651634,maxZ - 0.03903118893504143)
    ,(maxX - 0.004979487042874098,-0.005255294498056173,minZ + 0.01587633788585663)
    ,(maxX - 0.005172071512788534,-0.005193057470023632,maxZ - 0.010363521054387093)
    ,(maxX - 0.005793009069748223,-0.005193284247070551,maxZ - 0.010372905060648918)
    ,(maxX - 0.005875195027329028,-0.005271381698548794,maxZ - 0.029413267970085144)
    ,(maxX - 0.005472706281580031,-0.004904965870082378,maxZ - 0.02160024456679821)
    ,(maxX - 0.0052757697412744164,-0.0058011459186673164,minZ + 0.029480870813131332)
    ,(maxX - 0.0057287130039185286,-0.004943975247442722,minZ + 0.01588430255651474)
    ,(maxX - 0.0051487102173268795,-0.0051466329023242,maxZ - 0.03902805224061012)
    ,(maxX - 0.005920821567997336,-0.004894486162811518,maxZ - 0.0105185117572546)
    ,(maxX - 0.005912382970564067,-0.005342178046703339,maxZ - 0.021546142175793648)
    ,(maxX - 0.005211971350945532,-0.004634527489542961,minZ + 5.383789539337158e-05)
    ,(maxX - 0.005274825729429722,-0.004987378139048815,minZ + 0.029503092169761658)
    ,(maxX - 0.005549981025978923,-0.0054476335644721985,minZ + 6.705522537231445e-08)
    ,(maxX - 0.005011449102312326,-0.005086742807179689,minZ + 0.01588405668735504)
    ,(maxX - 0.005249560461379588,-0.004848137032240629,minZ + 0.01589324325323105)
    ,(maxX - 0.005586679908446968,-0.004847722128033638,minZ + 0.015890181064605713)
    ,(maxX - 0.005825327709317207,-0.005085740704089403,minZ + 0.01587667316198349)
    ,(maxX - 0.005825707106851041,-0.005422765389084816,minZ + 0.015860632061958313)
    ,(maxX - 0.005587595398537815,-0.005661370232701302,minZ + 0.0158514603972435)
    ,(maxX - 0.005250476184301078,-0.005661786068230867,minZ + 0.015854522585868835)
    ,(maxX - 0.005011828150600195,-0.005423767026513815,minZ + 0.01586802303791046)
    ,(maxX - 0.0050524246180430055,-0.00528864748775959,maxZ - 0.03902701288461685)
    ,(maxX - 0.005290519911795855,-0.005050024017691612,maxZ - 0.03902914375066757)
    ,(maxX - 0.005627641920000315,-0.005049617029726505,maxZ - 0.03903084620833397)
    ,(maxX - 0.005866308696568012,-0.005287665408104658,maxZ - 0.03903112933039665)
    ,(maxX - 0.005866712890565395,-0.005624723620712757,maxZ - 0.039029818028211594)
    ,(maxX - 0.005628617363981903,-0.005863346625119448,maxZ - 0.03902768716216087)
    ,(maxX - 0.0052914953557774425,-0.005863754078745842,maxZ - 0.03902598097920418)
    ,(maxX - 0.005052828579209745,-0.005625705700367689,maxZ - 0.03902570158243179)
    ,(maxX - 0.005066122743301094,-0.005175130441784859,maxZ - 0.02156427875161171)
    ,(maxX - 0.005304188118316233,-0.004937214311212301,maxZ - 0.021595504134893417)
    ,(maxX - 0.0056413100101053715,-0.004936820361763239,maxZ - 0.021596813574433327)
    ,(maxX - 0.005880007753148675,-0.005174180027097464,maxZ - 0.021567441523075104)
    ,(maxX - 0.005880454205907881,-0.005510250572115183,maxZ - 0.021524591371417046)
    ,(maxX - 0.0056423889473080635,-0.005748167168349028,maxZ - 0.021493365988135338)
    ,(maxX - 0.005305267055518925,-0.005748561583459377,maxZ - 0.02149205468595028)
    ,(maxX - 0.005066569661721587,-0.005511201918125153,maxZ - 0.02152142859995365)
    ,(maxX - 0.005074405577033758,-0.004731936380267143,maxZ - 0.010583722963929176)
    ,(maxX - 0.005312168272212148,-0.004502579569816589,maxZ - 0.01069762371480465)
    ,(maxX - 0.005649270839057863,-0.004502702970057726,maxZ - 0.010702718049287796)
    ,(maxX - 0.0058882435550913215,-0.004732233472168446,maxZ - 0.010596020147204399)
    ,(maxX - 0.005889098974876106,-0.0050567155703902245,maxZ - 0.010440031066536903)
    ,(maxX - 0.005651336396113038,-0.005286071915179491,maxZ - 0.010326128453016281)
    ,(maxX - 0.005314233829267323,-0.005285948980599642,maxZ - 0.010321034118533134)
    ,(maxX - 0.0050752609968185425,-0.005056418012827635,maxZ - 0.01042773388326168)
    ,(maxX - 0.005098042776808143,-0.003963995724916458,maxZ - 0.004888410214334726)
    ,(maxX - 0.005333001143299043,-0.0037931459955871105,maxZ - 0.005199151579290628)
    ,(maxX - 0.005669870879501104,-0.003798031248152256,maxZ - 0.0052190073765814304)
    ,(maxX - 0.005911318236030638,-0.003975789062678814,maxZ - 0.004936345387250185)
    ,(maxX - 0.005915906862355769,-0.004222291521728039,maxZ - 0.004516747314482927)
    ,(maxX - 0.0056809482630342245,-0.004393140785396099,maxZ - 0.004206005949527025)
    ,(maxX - 0.0053440784104168415,-0.004388255998492241,maxZ - 0.0041861520148813725)
    ,(maxX - 0.005102631403133273,-0.004210498183965683,maxZ - 0.004468812141567469)
    ,(maxX - 0.005148796364665031,-0.0029389490373432636,maxZ - 0.002848892007023096)
    ,(maxX - 0.005373513558879495,-0.0029471139423549175,maxZ - 0.0033773710019886494)
    ,(maxX - 0.005709447083063424,-0.0029683399479836226,maxZ - 0.003416749183088541)
    ,(maxX - 0.005959811387583613,-0.002990193199366331,maxZ - 0.002943959552794695)
    ,(maxX - 0.0059779464500024915,-0.002999872202053666,maxZ - 0.0022359550930559635)
    ,(maxX - 0.005753229022957385,-0.0029917070642113686,maxZ - 0.0017074759816750884)
    ,(maxX - 0.005417295498773456,-0.0029704810585826635,maxZ - 0.0016680978005751967)
    ,(maxX - 0.0051669314270839095,-0.002948627807199955,maxZ - 0.0021408875472843647)
    ,(minX + 0.006793352426029742,-0.005108049139380455,minZ + 0.00023909658193588257)
    ,(minX + 0.0066346460953354836,-0.004723844584077597,minZ + 0.00025669485330581665)
    ,(minX + 0.006250653299503028,-0.004564301110804081,minZ + 0.00026106834411621094)
    ,(minX + 0.00586631172336638,-0.0047228774055838585,minZ + 0.0002496689558029175)
    ,(minX + 0.005706763477064669,-0.005106681492179632,minZ + 0.00022915005683898926)
    ,(minX + 0.005865469924174249,-0.005490886978805065,minZ + 0.00021155178546905518)
    ,(minX + 0.006249462720006704,-0.005650430452078581,minZ + 0.00020717084407806396)
    ,(minX + 0.006633804412558675,-0.005491853225976229,minZ + 0.00021857768297195435)
    ,(minX + 0.006715552299283445,-0.005544771905988455,minZ + 0.029701028019189835)
    ,(minX + 0.00655686913523823,-0.005160461645573378,minZ + 0.0297086164355278)
    ,(minX + 0.006172882916871458,-0.005000889301300049,minZ + 0.029709983617067337)
    ,(minX + 0.005788527661934495,-0.0051595289260149,minZ + 0.029704324901103973)
    ,(minX + 0.005628953338600695,-0.005543452687561512,minZ + 0.02969495579600334)
    ,(minX + 0.005787636619061232,-0.005927762482315302,minZ + 0.029687367379665375)
    ,(minX + 0.0061716228374280035,-0.006087335292249918,minZ + 0.02968600019812584)
    ,(minX + 0.006555978092364967,-0.005928694736212492,minZ + 0.029691658914089203)
    ,(minX + 0.006685112020932138,-0.005602027289569378,maxZ - 0.0291944220662117)
    ,(minX + 0.006526459823362529,-0.005217899568378925,maxZ - 0.029210573062300682)
    ,(minX + 0.0061424848972819746,-0.005058403126895428,maxZ - 0.029218226671218872)
    ,(minX + 0.005758114974014461,-0.00521696824580431,maxZ - 0.029212897643446922)
    ,(minX + 0.005598508752882481,-0.005600709468126297,maxZ - 0.029197707772254944)
    ,(minX + 0.005757161183282733,-0.005984836723655462,maxZ - 0.029181556776165962)
    ,(minX + 0.006141135876532644,-0.0061443340964615345,maxZ - 0.029173903167247772)
    ,(minX + 0.006525505916215479,-0.005985768511891365,maxZ - 0.029179232195019722)
    ,(minX + 0.00667479052208364,-0.005256861448287964,maxZ - 0.015088497661054134)
    ,(minX + 0.006516232970170677,-0.0048761311918497086,maxZ - 0.01516645960509777)
    ,(minX + 0.006132298905868083,-0.0047181048430502415,maxZ - 0.015200402587652206)
    ,(minX + 0.005747891729697585,-0.004875352140516043,maxZ - 0.015170442871749401)
    ,(minX + 0.005588191794231534,-0.005255760159343481,maxZ - 0.015094131231307983)
    ,(minX + 0.005746749578975141,-0.005636490881443024,maxZ - 0.015016170218586922)
    ,(minX + 0.006130683759693056,-0.005794517230242491,maxZ - 0.014982225373387337)
    ,(minX + 0.006515091052278876,-0.005637269467115402,maxZ - 0.015012186020612717)
    ,(minX + 0.006657243531662971,-0.004483901429921389,maxZ - 0.0068090930581092834)
    ,(minX + 0.0065001812763512135,-0.004140931181609631,maxZ - 0.007067454978823662)
    ,(minX + 0.006116931792348623,-0.004000166896730661,maxZ - 0.007183153182268143)
    ,(minX + 0.005731997545808554,-0.004144065547734499,maxZ - 0.007088415324687958)
    ,(minX + 0.005570868030190468,-0.004488333128392696,maxZ - 0.006838735193014145)
    ,(minX + 0.005727930460125208,-0.004831302911043167,maxZ - 0.006580371409654617)
    ,(minX + 0.006111179769504815,-0.004972067661583424,maxZ - 0.006464675068855286)
    ,(minX + 0.006496114016044885,-0.004828169010579586,maxZ - 0.006559412926435471)
    ,(minX + 0.006604497611988336,-0.0032484245020896196,maxZ - 0.0031274016946554184)
    ,(minX + 0.006457724317442626,-0.003093734150752425,maxZ - 0.0036577805876731873)
    ,(minX + 0.006079296523239464,-0.003041104646399617,maxZ - 0.003899872303009033)
    ,(minX + 0.005690891877748072,-0.003121365327388048,maxZ - 0.003711860626935959)
    ,(minX + 0.0055200329516083,-0.003287500236183405,maxZ - 0.0032038819044828415)
    ,(minX + 0.005666806362569332,-0.003442190121859312,maxZ - 0.0026735030114650726)
    ,(minX + 0.006045234156772494,-0.0034948198590427637,maxZ - 0.0024314112961292267)
    ,(minX + 0.006433638744056225,-0.0034145594108849764,maxZ - 0.002619422972202301)
    ,(minX + 0.005553199094720185,-0.003373156301677227,maxZ - 0.0029192231595516205)
    ,(minX + 0.005638031987473369,-0.005809193942695856,maxZ - 0.029189079999923706)
    ,(minX + 0.006679139332845807,-0.005481190048158169,maxZ - 0.021335555240511894)
    ,(minX + 0.005963105417322367,-0.0060473051853477955,minZ + 0.029685713350772858)
    ,(minX + 0.0064580682083033025,-0.005610927473753691,minZ + 0.00021105259656906128)
    ,(minX + 0.006325242109596729,-0.004034899175167084,maxZ - 0.007151160389184952)
    ,(minX + 0.005660235299728811,-0.0053710793145000935,minZ + 0.016075536608695984)
    ,(minX + 0.00638652773341164,-0.002530882600694895,maxZ - 0.001646917313337326)
    ,(minX + 0.006753799156285822,-0.004899526014924049,minZ + 0.0002490729093551636)
    ,(minX + 0.005611745989881456,-0.004301622975617647,maxZ - 0.006975553929805756)
    ,(minX + 0.005923676071688533,-0.004757302813231945,maxZ - 0.015193496830761433)
    ,(minX + 0.006696114782243967,-0.00562225840985775,maxZ - 0.038819022476673126)
    ,(minX + 0.006588134099729359,-0.004988160915672779,minZ + 0.016097113490104675)
    ,(minX + 0.0057050439063459635,-0.004220933653414249,maxZ - 0.004127245396375656)
    ,(minX + 0.005668493686243892,-0.005752034951001406,minZ + 0.02969057857990265)
    ,(minX + 0.006753342226147652,-0.005316472612321377,minZ + 0.0002283826470375061)
    ,(minX + 0.00608676258707419,-0.0043317219242453575,maxZ - 0.003948887810111046)
    ,(minX + 0.005908200400881469,-0.004036600701510906,maxZ - 0.0071625374257564545)
    ,(minX + 0.006618573679588735,-0.004297514911741018,maxZ - 0.006948085501790047)
    ,(minX + 0.005609537824057043,-0.004674719180911779,maxZ - 0.006699742749333382)
    ,(minX + 0.0061239866190589964,-0.005448713432997465,maxZ - 0.010101532563567162)
    ,(minX + 0.006472813023719937,-0.004209799692034721,maxZ - 0.0040906742215156555)
    ,(minX + 0.00562828395050019,-0.005049192346632481,maxZ - 0.015135801397264004)
    ,(minX + 0.006042047869414091,-0.004603803623467684,minZ + 0.00025719404220581055)
    ,(minX + 0.005995150306262076,-0.002559639746323228,maxZ - 0.0014130901545286179)
    ,(minX + 0.006101552047766745,-0.0035372015554457903,maxZ - 0.005041923373937607)
    ,(minX + 0.005933871027082205,-0.005097907967865467,maxZ - 0.029217233881354332)
    ,(minX + 0.006520519149489701,-0.005098029971122742,maxZ - 0.021375520154833794)
    ,(minX + 0.005668977275490761,-0.005334966816008091,minZ + 0.02969978377223015)
    ,(minX + 0.005746773676946759,-0.004898258484899998,minZ + 0.00023986399173736572)
    ,(minX + 0.006483270728494972,-0.0036479895934462547,maxZ - 0.0048635657876729965)
    ,(minX + 0.006519501097500324,-0.005863978061825037,maxZ - 0.021296590566635132)
    ,(minX + 0.00615216267760843,-0.006164800841361284,maxZ - 0.038819536566734314)
    ,(minX + 0.00590286951046437,-0.004937335848808289,maxZ - 0.0064966678619384766)
    ,(minX + 0.005662225186824799,-0.0025571994483470917,maxZ - 0.0030235834419727325)
    ,(minX + 0.00667601206805557,-0.0053361887112259865,minZ + 0.029705405235290527)
    ,(minX + 0.005566274747252464,-0.0031989826820790768,maxZ - 0.0034829415380954742)
    ,(minX + 0.006637051934376359,-0.0039265891537070274,maxZ - 0.004469545558094978)
    ,(minX + 0.005922179203480482,-0.005754896439611912,maxZ - 0.014991294592618942)
    ,(minX + 0.006536525208503008,-0.006006165407598019,maxZ - 0.03881846368312836)
    ,(minX + 0.006645070854574442,-0.005810413975268602,maxZ - 0.029186034575104713)
    ,(minX + 0.006053602788597345,-0.0025284423027187586,maxZ - 0.0032574106007814407)
    ,(minX + 0.005869895336218178,-0.0030652163550257683,maxZ - 0.0038607902824878693)
    ,(minX + 0.0062029213877394795,-0.005914892535656691,minZ + 0.016058631241321564)
    ,(minX + 0.005746316979639232,-0.005315205082297325,minZ + 0.00021916627883911133)
    ,(minX + 0.006635318568442017,-0.005050212610512972,maxZ - 0.015130581334233284)
    ,(minX + 0.006350999989081174,-0.005098414141684771,maxZ - 0.029215972870588303)
    ,(minX + 0.005818931153044105,-0.00575533602386713,minZ + 0.016061931848526)
    ,(minX + 0.005620893090963364,-0.002579259453341365,maxZ - 0.0017194505780935287)
    ,(minX + 0.0064278600621037185,-0.0025088228285312653,maxZ - 0.00295105017721653)
    ,(minX + 0.005627664038911462,-0.00546240946277976,maxZ - 0.015052048489451408)
    ,(minX + 0.005932620842941105,-0.006104323081672192,maxZ - 0.02917615696787834)
    ,(minX + 0.0054829909931868315,-0.0025782485026866198,maxZ - 0.002386540174484253)
    ,(minX + 0.005715501611120999,-0.003659122856333852,maxZ - 0.004900138825178146)
    ,(minX + 0.005751156946644187,-0.005863080266863108,maxZ - 0.021299004554748535)
    ,(minX + 0.006645588902756572,-0.005393543280661106,maxZ - 0.029203049838542938)
    ,(minX + 0.006286203453782946,-0.0030502157751470804,maxZ - 0.0038314294070005417)
    ,(minX + 0.00655825569992885,-0.0033369415905326605,maxZ - 0.002848343923687935)
    ,(minX + 0.005551262525841594,-0.003942334558814764,maxZ - 0.004521265625953674)
    ,(minX + 0.0057421906385570765,-0.004556154832243919,maxZ - 0.010453060269355774)
    ,(minX + 0.00613511772826314,-0.006022163201123476,maxZ - 0.021281450986862183)
    ,(minX + 0.0065872694831341505,-0.005756282713264227,minZ + 0.016067564487457275)
    ,(minX + 0.006668635527603328,-0.0049255844205617905,maxZ - 0.010298069566488266)
    ,(minX + 0.006349750037770718,-0.006104828789830208,maxZ - 0.029174894094467163)
    ,(minX + 0.006319911277387291,-0.0049356333911418915,maxZ - 0.006485290825366974)
    ,(minX + 0.0063408034620806575,-0.004757725168019533,maxZ - 0.015191333368420601)
    ,(minX + 0.00576818163972348,-0.006005238275974989,maxZ - 0.03882160410284996)
    ,(minX + 0.0062546354020014405,-0.0034707081504166126,maxZ - 0.00247049517929554)
    ,(minX + 0.00560951279476285,-0.005620947107672691,maxZ - 0.038823459297418594)
    ,(minX + 0.006616365630179644,-0.004670611582696438,maxZ - 0.0066722724586725235)
    ,(minX + 0.0066755281295627356,-0.005753257777541876,minZ + 0.029696203768253326)
    ,(minX + 0.006634698482230306,-0.005463429726660252,maxZ - 0.015046827495098114)
    ,(minX + 0.006204143981449306,-0.004828604869544506,minZ + 0.016100406646728516)
    ,(minX + 0.006339306535664946,-0.005755319260060787,maxZ - 0.01498913299292326)
    ,(minX + 0.006126744614448398,-0.004402851220220327,maxZ - 0.010507876053452492)
    ,(minX + 0.006153465015813708,-0.005078405141830444,maxZ - 0.03882294520735741)
    ,(minX + 0.005838327226229012,-0.003485708963125944,maxZ - 0.002499854192137718)
    ,(minX + 0.00656576210167259,-0.0025098335463553667,maxZ - 0.0022839605808258057)
    ,(minX + 0.005752174882218242,-0.005097132176160812,maxZ - 0.021377932280302048)
    ,(minX + 0.006571331556187943,-0.003162768203765154,maxZ - 0.0034120604395866394)
    ,(minX + 0.006510490493383259,-0.00455587450414896,maxZ - 0.010443676263093948)
    ,(minX + 0.005964273179415613,-0.005040412303060293,minZ + 0.02970793843269348)
    ,(minX + 0.005769102484919131,-0.005237040109932423,maxZ - 0.038824014365673065)
    ,(minX + 0.006746829953044653,-0.005372417625039816,minZ + 0.016083508729934692)
    ,(minX + 0.0065085404785349965,-0.0052954102866351604,maxZ - 0.01015634834766388)
    ,(minX + 0.005740240449085832,-0.005295691080391407,maxZ - 0.010165732353925705)
    ,(minX + 0.0056385500356554985,-0.005392322316765785,maxZ - 0.02920609526336193)
    ,(minX + 0.006136558135040104,-0.004938947968184948,maxZ - 0.021393071860074997)
    ,(minX + 0.006380232633091509,-0.006047811824828386,minZ + 0.029688045382499695)
    ,(minX + 0.005819795769639313,-0.0049872142262756824,minZ + 0.016091473400592804)
    ,(minX + 0.006537446053698659,-0.00523796770721674,maxZ - 0.03882087767124176)
    ,(minX + 0.005582095473073423,-0.004925980698317289,maxZ - 0.010311339050531387)
    ,(minX + 0.005592536414042115,-0.005479920189827681,maxZ - 0.021338969469070435)
    ,(minX + 0.0064591713598929346,-0.00460432842373848,minZ + 0.00026100873947143555)
    ,(minX + 0.006381400395184755,-0.005040918942540884,minZ + 0.02971026673913002)
    ,(minX + 0.006040944659616798,-0.005610402673482895,minZ + 0.00020723789930343628)
    ,(minX + 0.006707282620482147,-0.005163864698261023,minZ + 0.016091227531433105)
    ,(minX + 0.006412662158254534,-0.004868632182478905,minZ + 0.016100414097309113)
    ,(minX + 0.005995536455884576,-0.004868118558079004,minZ + 0.016097351908683777)
    ,(minX + 0.0057002517860382795,-0.005162625107914209,minZ + 0.016083844006061554)
    ,(minX + 0.005699782632291317,-0.005579632706940174,minZ + 0.016067802906036377)
    ,(minX + 0.0059944032109342515,-0.005874865222722292,minZ + 0.016058631241321564)
    ,(minX + 0.00641152891330421,-0.005875378847122192,minZ + 0.0160616934299469)
    ,(minX + 0.0067068132339045405,-0.005580872762948275,minZ + 0.016075193881988525)
    ,(minX + 0.006656582350842655,-0.00541368592530489,maxZ - 0.03881983831524849)
    ,(minX + 0.00636198150459677,-0.005118431523442268,maxZ - 0.03882196918129921)
    ,(minX + 0.005944853066466749,-0.005117928143590689,maxZ - 0.03882367163896561)
    ,(minX + 0.005649544997140765,-0.005412471015006304,maxZ - 0.03882395476102829)
    ,(minX + 0.005649045226164162,-0.005829520057886839,maxZ - 0.03882264345884323)
    ,(minX + 0.005943646072410047,-0.006124773994088173,maxZ - 0.03882051259279251)
    ,(minX + 0.00636077462695539,-0.00612527783960104,maxZ - 0.038818806409835815)
    ,(minX + 0.00665608246345073,-0.005830735433846712,maxZ - 0.03881852701306343)
    ,(minX + 0.006639633560553193,-0.005273229442536831,maxZ - 0.021357106044888496)
    ,(minX + 0.006345069617964327,-0.004978850018233061,maxZ - 0.021388331428170204)
    ,(minX + 0.00592794077238068,-0.00497836247086525,maxZ - 0.021389640867710114)
    ,(minX + 0.005632595275528729,-0.005272052250802517,maxZ - 0.02136026881635189)
    ,(minX + 0.005632042535580695,-0.0056878807954490185,maxZ - 0.021317418664693832)
    ,(minX + 0.005926606128923595,-0.005982260685414076,maxZ - 0.021286193281412125)
    ,(minX + 0.0063437349162995815,-0.005982748232781887,maxZ - 0.021284881979227066)
    ,(minX + 0.006639080471359193,-0.0056890579871833324,maxZ - 0.021314255893230438)
    ,(minX + 0.006629384937696159,-0.004724854603409767,maxZ - 0.010376550257205963)
    ,(minX + 0.006335195794235915,-0.004441066179424524,maxZ - 0.010490451008081436)
    ,(minX + 0.0059180911630392075,-0.004441218450665474,maxZ - 0.010495545342564583)
    ,(minX + 0.005622404860332608,-0.004725221544504166,maxZ - 0.010388847440481186)
    ,(minX + 0.005621346062980592,-0.005126711446791887,maxZ - 0.01023285835981369)
    ,(minX + 0.0059155350318178535,-0.005410499405115843,maxZ - 0.010118955746293068)
    ,(minX + 0.0063326399540528655,-0.005410346668213606,maxZ - 0.010113861411809921)
    ,(minX + 0.006628326023928821,-0.005126343574374914,maxZ - 0.010220561176538467)
    ,(minX + 0.006600138149224222,-0.0037746636662632227,maxZ - 0.004681237041950226)
    ,(minX + 0.006309418939054012,-0.0035632678773254156,maxZ - 0.004991978406906128)
    ,(minX + 0.005892602261155844,-0.0035693119280040264,maxZ - 0.00501183420419693)
    ,(minX + 0.005593853886239231,-0.0037892560940235853,maxZ - 0.0047291722148656845)
    ,(minX + 0.005588176427409053,-0.004094259347766638,maxZ - 0.004309574142098427)
    ,(minX + 0.005878895753994584,-0.004305655136704445,maxZ - 0.003998832777142525)
    ,(minX + 0.006295712431892753,-0.00429961085319519,maxZ - 0.003978978842496872)
    ,(minX + 0.006594460690394044,-0.004079666920006275,maxZ - 0.004261638969182968)
    ,(minX + 0.006537339504575357,-0.002506350167095661,maxZ - 0.0026417188346385956)
    ,(minX + 0.006259291782043874,-0.0025164526887238026,maxZ - 0.003170197829604149)
    ,(minX + 0.005843633785843849,-0.0025427164509892464,maxZ - 0.0032095760107040405)
    ,(minX + 0.005533852614462376,-0.0025697555392980576,maxZ - 0.0027367863804101944)
    ,(minX + 0.005511413444764912,-0.0025817318819463253,maxZ - 0.002028781920671463)
    ,(minX + 0.005789461429230869,-0.0025716288946568966,maxZ - 0.0015003029257059097)
    ,(minX + 0.006205119309015572,-0.0025453658308833838,maxZ - 0.001460924744606018)
    ,(minX + 0.0065149005386047065,-0.0025183262769132853,maxZ - 0.0019337143748998642)
    ,(minX,-0.0013792915269732475,maxZ - 0.005334946792572737)
    ,(minX + 4.656612873077393e-10,maxY,maxZ - 0.005334946792572737)
    ,(maxX,maxY - 4.423782229423523e-09,maxZ - 0.005334946792572737)
    ,(maxX,-0.0013792961835861206,maxZ - 0.005334946792572737)
    ,(minX,-0.0013792915269732475,maxZ - 1.5133991837501526e-08)
    ,(minX + 4.656612873077393e-10,maxY,maxZ - 1.5133991837501526e-08)
    ,(maxX,maxY - 4.423782229423523e-09,maxZ - 1.5133991837501526e-08)
    ,(maxX,-0.0013792961835861206,maxZ - 1.5133991837501526e-08)
    ,(minX + 0.0011832499876618385,-0.0013792921090498567,maxZ - 0.00447732862085104)
    ,(minX + 0.0011832499876618385,-0.0013792921090498567,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0011832499876618385,-0.0013792957179248333,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0011832499876618385,-0.0013792957179248333,maxZ - 0.00447732862085104)
    ,(minX + 0.0011832504533231258,-0.0007798965089023113,maxZ - 0.00447732862085104)
    ,(minX + 0.0011832504533231258,-0.0007798965089023113,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0011832495220005512,-0.0007799001759849489,maxZ - 0.0008576327236369252)
    ,(maxX - 0.0011832495220005512,-0.0007799001759849489,maxZ - 0.00447732862085104)
    ,(minX + 0.004529597237706184,-0.0007973873289301991,maxZ - 0.0044512152671813965)
    ,(minX + 0.004529597237706184,-0.0007973873289301991,maxZ - 0.0008894965285435319)
    ,(minX + 0.004144799197092652,-0.001563245547004044,maxZ - 0.0044512152671813965)
    ,(minX + 0.004144799197092652,-0.001563245547004044,maxZ - 0.0008894965285435319)
    ,(minX + 0.0032158144749701023,-0.0018804739229381084,maxZ - 0.0044512152671813965)
    ,(minX + 0.0032158144749701023,-0.0018804739229381084,maxZ - 0.0008894965285435319)
    ,(minX + 0.0022868295200169086,-0.0015632447320967913,maxZ - 0.0044512152671813965)
    ,(minX + 0.0022868295200169086,-0.0015632447320967913,maxZ - 0.0008894965285435319)
    ,(minX + 0.0019020326435565948,-0.0007973865140229464,maxZ - 0.0044512152671813965)
    ,(minX + 0.0019020326435565948,-0.0007973865140229464,maxZ - 0.0008894965285435319)
    ,(maxX - 0.001917288638651371,-0.0007973890169523656,maxZ - 0.0044512152671813965)
    ,(maxX - 0.001917288638651371,-0.0007973890169523656,maxZ - 0.0008894965285435319)
    ,(maxX - 0.0023020864464342594,-0.0015632474096491933,maxZ - 0.0044512152671813965)
    ,(maxX - 0.0023020864464342594,-0.0015632474096491933,maxZ - 0.0008894965285435319)
    ,(maxX - 0.0032310718670487404,-0.0018804756691679358,maxZ - 0.0044512152671813965)
    ,(maxX - 0.0032310718670487404,-0.0018804756691679358,maxZ - 0.0008894965285435319)
    ,(maxX - 0.00416005658917129,-0.0015632465947419405,maxZ - 0.0044512152671813965)
    ,(maxX - 0.00416005658917129,-0.0015632465947419405,maxZ - 0.0008894965285435319)
    ,(maxX - 0.0045448546297848225,-0.0007973880274221301,maxZ - 0.0044512152671813965)
    ,(maxX - 0.0045448546297848225,-0.0007973880274221301,maxZ - 0.0008894965285435319)]
    
    # Faces
    myFaces = [(0, 56, 144, 131),(0, 131, 151, 63),(1, 141, 145, 60),(1, 60, 144, 56),(2, 71, 146, 120)
    ,(2, 120, 145, 141),(3, 77, 147, 137),(3, 137, 146, 71),(4, 92, 148, 54),(4, 54, 147, 77)
    ,(5, 143, 149, 95),(5, 95, 148, 92),(6, 52, 150, 91),(6, 91, 149, 143),(7, 63, 151, 109)
    ,(7, 109, 150, 52),(8, 131, 144, 83),(8, 83, 152, 59),(8, 59, 159, 118),(8, 118, 151, 131)
    ,(9, 60, 145, 142),(9, 142, 153, 138),(9, 138, 152, 83),(9, 83, 144, 60),(10, 120, 146, 129)
    ,(10, 129, 154, 123),(10, 123, 153, 142),(10, 142, 145, 120),(11, 137, 147, 76),(11, 76, 155, 130)
    ,(11, 130, 154, 129),(11, 129, 146, 137),(12, 54, 148, 62),(12, 62, 156, 116),(12, 116, 155, 76)
    ,(12, 76, 147, 54),(13, 95, 149, 51),(13, 51, 157, 114),(13, 114, 156, 62),(13, 62, 148, 95)
    ,(14, 91, 150, 136),(14, 136, 158, 80),(14, 80, 157, 51),(14, 51, 149, 91),(15, 109, 151, 118)
    ,(15, 118, 159, 87),(15, 87, 158, 136),(15, 136, 150, 109),(16, 59, 152, 103),(16, 103, 160, 50)
    ,(16, 50, 167, 88),(16, 88, 159, 59),(17, 138, 153, 94),(17, 94, 161, 75),(17, 75, 160, 103)
    ,(17, 103, 152, 138),(18, 123, 154, 74),(18, 74, 162, 135),(18, 135, 161, 94),(18, 94, 153, 123)
    ,(19, 130, 155, 134),(19, 134, 163, 126),(19, 126, 162, 74),(19, 74, 154, 130),(20, 116, 156, 49)
    ,(20, 49, 164, 140),(20, 140, 163, 134),(20, 134, 155, 116),(21, 114, 157, 99),(21, 99, 165, 102)
    ,(21, 102, 164, 49),(21, 49, 156, 114),(22, 80, 158, 111),(22, 111, 166, 108),(22, 108, 165, 99)
    ,(22, 99, 157, 80),(23, 87, 159, 88),(23, 88, 167, 79),(23, 79, 166, 111),(23, 111, 158, 87)
    ,(24, 50, 160, 93),(24, 93, 168, 110),(24, 110, 175, 119),(24, 119, 167, 50),(25, 75, 161, 113)
    ,(25, 113, 169, 128),(25, 128, 168, 93),(25, 93, 160, 75),(26, 135, 162, 58),(26, 58, 170, 122)
    ,(26, 122, 169, 113),(26, 113, 161, 135),(27, 126, 163, 70),(27, 70, 171, 107),(27, 107, 170, 58)
    ,(27, 58, 162, 126),(28, 140, 164, 98),(28, 98, 172, 139),(28, 139, 171, 70),(28, 70, 163, 140)
    ,(29, 102, 165, 86),(29, 86, 173, 133),(29, 133, 172, 98),(29, 98, 164, 102),(30, 108, 166, 121)
    ,(30, 121, 174, 68),(30, 68, 173, 86),(30, 86, 165, 108),(31, 79, 167, 119),(31, 119, 175, 132)
    ,(31, 132, 174, 121),(31, 121, 166, 79),(32, 110, 168, 66),(32, 66, 176, 85),(32, 85, 183, 117)
    ,(32, 117, 175, 110),(33, 128, 169, 53),(33, 53, 177, 78),(33, 78, 176, 66),(33, 66, 168, 128)
    ,(34, 122, 170, 65),(34, 65, 178, 73),(34, 73, 177, 53),(34, 53, 169, 122),(35, 107, 171, 57)
    ,(35, 57, 179, 101),(35, 101, 178, 65),(35, 65, 170, 107),(36, 139, 172, 67),(36, 67, 180, 106)
    ,(36, 106, 179, 57),(36, 57, 171, 139),(37, 133, 173, 81),(37, 81, 181, 61),(37, 61, 180, 67)
    ,(37, 67, 172, 133),(38, 68, 174, 112),(38, 112, 182, 64),(38, 64, 181, 81),(38, 81, 173, 68)
    ,(39, 132, 175, 117),(39, 117, 183, 69),(39, 69, 182, 112),(39, 112, 174, 132),(40, 85, 176, 127)
    ,(40, 127, 184, 125),(40, 125, 191, 105),(40, 105, 183, 85),(41, 78, 177, 104),(41, 104, 185, 97)
    ,(41, 97, 184, 127),(41, 127, 176, 78),(42, 73, 178, 90),(42, 90, 186, 89),(42, 89, 185, 104)
    ,(42, 104, 177, 73),(43, 101, 179, 84),(43, 84, 187, 82),(43, 82, 186, 90),(43, 90, 178, 101)
    ,(44, 106, 180, 48),(44, 48, 188, 100),(44, 100, 187, 84),(44, 84, 179, 106),(45, 61, 181, 124)
    ,(45, 124, 189, 96),(45, 96, 188, 48),(45, 48, 180, 61),(46, 64, 182, 115),(46, 115, 190, 72)
    ,(46, 72, 189, 124),(46, 124, 181, 64),(47, 69, 183, 105),(47, 105, 191, 55),(47, 55, 190, 115)
    ,(47, 115, 182, 69),(192, 248, 336, 323),(192, 323, 343, 255),(193, 333, 337, 252),(193, 252, 336, 248)
    ,(194, 263, 338, 312),(194, 312, 337, 333),(195, 269, 339, 329),(195, 329, 338, 263),(196, 284, 340, 246)
    ,(196, 246, 339, 269),(197, 335, 341, 287),(197, 287, 340, 284),(198, 244, 342, 283),(198, 283, 341, 335)
    ,(199, 255, 343, 301),(199, 301, 342, 244),(200, 323, 336, 275),(200, 275, 344, 251),(200, 251, 351, 310)
    ,(200, 310, 343, 323),(201, 252, 337, 334),(201, 334, 345, 330),(201, 330, 344, 275),(201, 275, 336, 252)
    ,(202, 312, 338, 321),(202, 321, 346, 315),(202, 315, 345, 334),(202, 334, 337, 312),(203, 329, 339, 268)
    ,(203, 268, 347, 322),(203, 322, 346, 321),(203, 321, 338, 329),(204, 246, 340, 254),(204, 254, 348, 308)
    ,(204, 308, 347, 268),(204, 268, 339, 246),(205, 287, 341, 243),(205, 243, 349, 306),(205, 306, 348, 254)
    ,(205, 254, 340, 287),(206, 283, 342, 328),(206, 328, 350, 272),(206, 272, 349, 243),(206, 243, 341, 283)
    ,(207, 301, 343, 310),(207, 310, 351, 279),(207, 279, 350, 328),(207, 328, 342, 301),(208, 251, 344, 295)
    ,(208, 295, 352, 242),(208, 242, 359, 280),(208, 280, 351, 251),(209, 330, 345, 286),(209, 286, 353, 267)
    ,(209, 267, 352, 295),(209, 295, 344, 330),(210, 315, 346, 266),(210, 266, 354, 327),(210, 327, 353, 286)
    ,(210, 286, 345, 315),(211, 322, 347, 326),(211, 326, 355, 318),(211, 318, 354, 266),(211, 266, 346, 322)
    ,(212, 308, 348, 241),(212, 241, 356, 332),(212, 332, 355, 326),(212, 326, 347, 308),(213, 306, 349, 291)
    ,(213, 291, 357, 294),(213, 294, 356, 241),(213, 241, 348, 306),(214, 272, 350, 303),(214, 303, 358, 300)
    ,(214, 300, 357, 291),(214, 291, 349, 272),(215, 279, 351, 280),(215, 280, 359, 271),(215, 271, 358, 303)
    ,(215, 303, 350, 279),(216, 242, 352, 285),(216, 285, 360, 302),(216, 302, 367, 311),(216, 311, 359, 242)
    ,(217, 267, 353, 305),(217, 305, 361, 320),(217, 320, 360, 285),(217, 285, 352, 267),(218, 327, 354, 250)
    ,(218, 250, 362, 314),(218, 314, 361, 305),(218, 305, 353, 327),(219, 318, 355, 262),(219, 262, 363, 299)
    ,(219, 299, 362, 250),(219, 250, 354, 318),(220, 332, 356, 290),(220, 290, 364, 331),(220, 331, 363, 262)
    ,(220, 262, 355, 332),(221, 294, 357, 278),(221, 278, 365, 325),(221, 325, 364, 290),(221, 290, 356, 294)
    ,(222, 300, 358, 313),(222, 313, 366, 260),(222, 260, 365, 278),(222, 278, 357, 300),(223, 271, 359, 311)
    ,(223, 311, 367, 324),(223, 324, 366, 313),(223, 313, 358, 271),(224, 302, 360, 258),(224, 258, 368, 277)
    ,(224, 277, 375, 309),(224, 309, 367, 302),(225, 320, 361, 245),(225, 245, 369, 270),(225, 270, 368, 258)
    ,(225, 258, 360, 320),(226, 314, 362, 257),(226, 257, 370, 265),(226, 265, 369, 245),(226, 245, 361, 314)
    ,(227, 299, 363, 249),(227, 249, 371, 293),(227, 293, 370, 257),(227, 257, 362, 299),(228, 331, 364, 259)
    ,(228, 259, 372, 298),(228, 298, 371, 249),(228, 249, 363, 331),(229, 325, 365, 273),(229, 273, 373, 253)
    ,(229, 253, 372, 259),(229, 259, 364, 325),(230, 260, 366, 304),(230, 304, 374, 256),(230, 256, 373, 273)
    ,(230, 273, 365, 260),(231, 324, 367, 309),(231, 309, 375, 261),(231, 261, 374, 304),(231, 304, 366, 324)
    ,(232, 277, 368, 319),(232, 319, 376, 317),(232, 317, 383, 297),(232, 297, 375, 277),(233, 270, 369, 296)
    ,(233, 296, 377, 289),(233, 289, 376, 319),(233, 319, 368, 270),(234, 265, 370, 282),(234, 282, 378, 281)
    ,(234, 281, 377, 296),(234, 296, 369, 265),(235, 293, 371, 276),(235, 276, 379, 274),(235, 274, 378, 282)
    ,(235, 282, 370, 293),(236, 298, 372, 240),(236, 240, 380, 292),(236, 292, 379, 276),(236, 276, 371, 298)
    ,(237, 253, 373, 316),(237, 316, 381, 288),(237, 288, 380, 240),(237, 240, 372, 253),(238, 256, 374, 307)
    ,(238, 307, 382, 264),(238, 264, 381, 316),(238, 316, 373, 256),(239, 261, 375, 297),(239, 297, 383, 247)
    ,(239, 247, 382, 307),(239, 307, 374, 261),(388, 389, 385, 384),(389, 390, 386, 385),(390, 391, 387, 386)
    ,(392, 395, 399, 396),(384, 385, 386, 387),(391, 390, 389, 388),(392, 393, 388, 384),(394, 395, 387, 391)
    ,(393, 394, 391, 388),(395, 392, 384, 387),(398, 397, 396, 399),(394, 393, 397, 398),(395, 394, 398, 399)
    ,(393, 392, 396, 397),(400, 401, 403, 402),(402, 403, 405, 404),(404, 405, 407, 406),(406, 407, 409, 408)
    ,(410, 411, 413, 412),(412, 413, 415, 414),(414, 415, 417, 416),(416, 417, 419, 418)]

    mesh = bpy.data.meshes.new(objName)
    myObject = bpy.data.objects.new(objName, mesh)
    
    myObject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(myObject)
    
    mesh.from_pydata(myVertex, [], myFaces)
    mesh.update(calc_edges=True)

    return (myObject)


#----------------------------------------------
# Code to run alone the script
#----------------------------------------------
if __name__ == "__main__":
    create_japan_mesh(0)
    print("Executed")
