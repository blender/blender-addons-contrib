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
# File: room_maker.py
# Automatic generation of rooms
# Author: Antonio Vazquez (antonioya) and Eduardo Gutierrez
#
#----------------------------------------------------------
import bpy
import math
import os
import datetime
import time
from tools import *
from bpy_extras.io_utils import ExportHelper, ImportHelper

#----------------------------------------------------------
#    Export menu UI
#----------------------------------------------------------
 
class EXPORT_ROOM(bpy.types.Operator, ExportHelper):
    bl_idname = "io_export.roomdata"
    bl_description = 'Export Room data (.dat)'
    bl_category = 'Archimesh'
    bl_label = "Export"
 
    # From ExportHelper. Filter filenames.
    filename_ext = ".dat"
    filter_glob = bpy.props.StringProperty(default="*.dat", options={'HIDDEN'})
 
    filepath = bpy.props.StringProperty(
        name="File Path", 
        description="File path used for exporting room data file", 
        maxlen= 1024, default= "")
 

#----------------------------------------------------------
# Execute
#----------------------------------------------------------
    def execute(self, context):
        print("Exporting:", self.properties.filepath)
        try:
            myObj = bpy.context.active_object
            myData = myObj.RoomGenerator[0]
            
            #-------------------------------
            # extract path and filename 
            #-------------------------------
            (filepath, filename) = os.path.split(self.properties.filepath)
            print('Exporting %s' % filename)
            #-------------------------------
            # Open output file
            #-------------------------------
            realpath = os.path.realpath(os.path.expanduser(self.properties.filepath))
            fOut = open(realpath, 'w')
                
            st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            fOut.write("# Archimesh room export data\n")
            fOut.write("# " + st +"\n")
            fOut.write("#======================================================\n")
    
            fOut.write("name=" + myObj.name + "\n")
            fOut.write("height=" + str(round(myData.room_height,3)) + "\n")
            fOut.write("thickness=" + str(round(myData.wall_width,3)) + "\n")
            fOut.write("inverse=" + str(myData.inverse) + "\n")
            fOut.write("ceiling=" + str(myData.ceiling) + "\n")
            fOut.write("floor=" + str(myData.floor) + "\n")
            fOut.write("close=" + str(myData.merge) + "\n")
    
            # Walls
            fOut.write("#\n# Walls\n#\n")
            fOut.write("walls=" + str(myData.wall_num) + "\n")
            i = 0
            for w in myData.walls:
                if i < myData.wall_num:
                    i = i + 1
                    fOut.write("w=" + str(round(w.w,3)))
                    if w.a == True: # advance
                        fOut.write(",a=" + str(w.a) + ",")
                        fOut.write("r=" + str(round(w.r,1)) + ",")
                        fOut.write("h=" + str(w.h) + ",")
                        fOut.write("m=" + str(round(w.m,3)) + ",")
                        fOut.write("f=" + str(round(w.f,3)) + ",")
                        fOut.write("c=" + str(w.curved) + ",")
                        fOut.write("cf=" + str(round(w.curve_factor,1)) + ",")
                        fOut.write("cd=" + str(round(w.curve_arc_deg,1)) + ",")
                        fOut.write("cs=" + str(w.curve_steps) + "\n")
                    else:
                        fOut.write("\n")
                    
            # Baseboard
            fOut.write("#\n# Baseboard\n#\n")
            fOut.write("baseboard=" + str(myData.baseboard) + "\n")
            fOut.write("baseh=" + str(round(myData.base_height,3)) + "\n")
            fOut.write("baset=" + str(round(myData.base_width,3)) + "\n")
            # Materials
            fOut.write("#\n# Materials\n#\n")
            fOut.write("materials=" + str(myData.crt_mat) + "\n")
            
            
            fOut.close()
            self.report({'INFO'}, realpath + "successfully exported")
        except:
            self.report({'ERROR'}, "Unable to export room data")

 
        return {'FINISHED'}
#----------------------------------------------------------
# Invoke
#----------------------------------------------------------
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#----------------------------------------------------------
#    Import menu UI
#----------------------------------------------------------
 
class IMPORT_ROOM(bpy.types.Operator, ImportHelper):
    bl_idname = "io_import.roomdata"
    bl_description = 'Import Room data (.dat)'
    bl_category = 'Archimesh'
    bl_label = "Import"
 
    # From Helper. Filter filenames.
    filename_ext = ".dat"
    filter_glob = bpy.props.StringProperty(default="*.dat", options={'HIDDEN'})
 
    filepath = bpy.props.StringProperty(
        name="File Path", 
        description="File path used for exporting room data file", 
        maxlen= 1024, default= "")
    
#----------------------------------------------------------
# Execute
#----------------------------------------------------------
    def execute(self, context):
        print("Importing:", self.properties.filepath)
        try:
            realpath = os.path.realpath(os.path.expanduser(self.properties.filepath))
            fInput = open(realpath)
            line = fInput.readline()   
            
            myObj = bpy.context.active_object
            myData = myObj.RoomGenerator[0]
            #----------------------------------         
            # Loop all records from file
            #----------------------------------
            idx = 0 # index of each wall
            while line:
                if line[:1] != '#':
                    if "name=" in line.lower():
                        myObj.name = line[5:-1]
                        
                    elif "height=" in line.lower():
                        myData.room_height = float(line[7:-1])
                           
                    elif "thickness=" in line.lower():
                        myData.wall_width = float(line[10:-1])
                        
                    elif "inverse=" in line.lower():
                        if line[8:-4].upper() == "T":
                            myData.inverse = True
                        else:
                            myData.inverse = False
                             
                    elif "ceiling=" in line.lower():
                        if line[8:-4].upper() == "T":
                            myData.ceiling = True
                        else:
                            myData.ceiling = False
                        
                    elif "floor=" in line.lower():
                        if line[6:-4].upper() == "T":
                            myData.floor = True
                        else:
                            myData.floor = False
                        
                    elif "close=" in line.lower():
                        if line[6:-4].upper() == "T":
                            myData.merge = True
                        else:
                            myData.merge = False
        
                    elif "walls=" in line.lower():
                        myData.wall_num = int(line[6:-1])
     
                    #---------------------
                    # Walls Data
                    #---------------------
                    elif "w=" in line.lower() and idx < myData.wall_num:
                        # get all pieces
                        buf = line[:-1] + ","
                        s = buf.split(",")
                        for e in s:
                            param = e.lower()
                            if "w=" in param:
                                myData.walls[idx].w = float(e[2:])
                            elif "a=" in param:
                                if "true" == param[2:]:
                                    myData.walls[idx].a = True
                                else:
                                    myData.walls[idx].a = False
                            elif "r=" in param:
                                myData.walls[idx].r = float(e[2:])
                            elif "h=" in param:
                                myData.walls[idx].h = e[2:]
                            elif "m=" in param:
                                myData.walls[idx].m = float(e[2:])
                            elif "f=" == param[0:2]:
                                myData.walls[idx].f = float(e[2:])
                            elif "c=" in param:
                                if "true" == param[2:]:
                                    myData.walls[idx].curved = True
                                else:
                                    myData.walls[idx].curved = False
                            elif "cf=" in param:
                                myData.walls[idx].curve_factor = float(e[3:])
                            elif "cd=" in param:
                                myData.walls[idx].curve_arc_deg = float(e[3:])
                            elif "cs=" in param:
                                myData.walls[idx].curve_steps = int(e[3:])
                        idx = idx + 1
    
                    elif "materials=" in line.lower():
                        if line[10:-4].upper() == "T":
                            myData.crt_mat = True
                        else:
                            myData.crt_mat = False
                       
                line = fInput.readline()
                
            fInput.close()
            self.report({'INFO'}, realpath + "successfully imported")
        except:
            self.report({'ERROR'}, "Unable to import room data")
 
        return {'FINISHED'}
#----------------------------------------------------------
# Invoke
#----------------------------------------------------------
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#------------------------------------------------------------------
# Define operator class to create rooms
#------------------------------------------------------------------
class ROOM(bpy.types.Operator):
    bl_idname = "mesh.archimesh_room"
    bl_label = "Room"
    bl_description = "Generate room with walls, baseboard, floor and ceiling."
    bl_category = 'Archimesh'
    bl_options = {'REGISTER', 'UNDO'}

    #-----------------------------------------------------
    # Draw (create UI interface)
    #-----------------------------------------------------
    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row.label("Use Properties panel (N) to define parms", icon='INFO')
        row = layout.row(align=False)
        row.operator("io_import.roomdata", text="Import",icon='COPYDOWN')
        
    #-----------------------------------------------------
    # Execute
    #-----------------------------------------------------
    def execute(self, context):
        if (bpy.context.mode == "OBJECT"):
            create_room(self,context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}

#------------------------------------------------------------------------------
# Create main object for the room. The other objects of room will be children of this.
#------------------------------------------------------------------------------
def create_room(self,context):
    # deselect all objects
    for o in bpy.data.objects:
        o.select = False

    # we create main object and mesh for walls
    RoomMesh = bpy.data.meshes.new("Room")
    RoomObject = bpy.data.objects.new("Room", RoomMesh)
    RoomObject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(RoomObject)
    RoomObject.RoomGenerator.add()
    RoomObject.RoomGenerator[0].walls.add()

    # we shape the walls and create other objects as children of 'RoomObject'.
    shape_walls_and_create_children(RoomObject)

    # we select, and activate, main object for the room.
    RoomObject.select = True
    bpy.context.scene.objects.active = RoomObject

#-----------------------------------------------------
# Verify if solidify exist
#-----------------------------------------------------
def isSolidify(myObject):
    flag = False
    for mod in myObject.modifiers:
            if mod.type == 'SOLIDIFY':
                flag = True
                break
    return flag        

#------------------------------------------------------------------------------
# Update wall mesh and children objects (baseboard, floor and ceiling).
#------------------------------------------------------------------------------
def update_room(self,context):
    # When we update, the active object is the main object of the room.
    o=bpy.context.active_object
    # Now we deselect that room object to not delete it.
    o.select=False
    # Remove walls (mesh of room/active object),
    o.data.user_clear()
    bpy.data.meshes.remove(o.data)
    # and we create a new mesh for the walls:
    RoomMesh = bpy.data.meshes.new("Room")
    o.data = RoomMesh
    o.data.use_fake_user = True
    # deselect all objects
    for obj in bpy.data.objects:
        obj.select = False
    # Remove children created by this addon:
    for child in o.children:
        try:
            if child["archimesh.room_object"] == True:
                try:
                    # remove child relationship
                    for grandchild in child.children:
                            grandchild.parent = None
                    # remove modifiers
                    for mod in child.modifiers:
                        bpy.ops.object.modifier_remove(mod)
                except:
                    x = 1 # dummy    
                # clear data
                child.data.user_clear()
                bpy.data.meshes.remove(child.data)
                child.select=True
                bpy.ops.object.delete()
        except:    
            x = 1 # dummy    
    # Finally we create all that again (except main object),
    shape_walls_and_create_children(o,True)
    # and select, and activate, the main object of the room.
    o.select = True
    bpy.context.scene.objects.active = o

#-----------------------------------------------------
# Move Solidify to Top
#-----------------------------------------------------
def moveToTopSolidify(myObject):
    mymod = None
    for mod in myObject.modifiers:
        if mod.type == 'SOLIDIFY':
            mymod = mod
            
    if mymod != None:
        while myObject.modifiers[0] != mymod: 
            bpy.ops.object.modifier_move_up(modifier=mymod.name)            

#------------------------------------------------------------------------------
# Generate walls, baseboard, floor, ceiling and materials.
# For walls, it only shapes mesh and creates modifier solidify (the modifier, only the first time).
# And, for the others, it creates object and mesh.
#------------------------------------------------------------------------------
def shape_walls_and_create_children(myRoom,update=False):
    rp = myRoom.RoomGenerator[0] # "rp" means "room properties".
    # Create the walls (only mesh, because the object is 'myRoom', created before).
    create_walls(rp,myRoom.data,get_BlendUnits(rp.room_height))
    # Mark Seams
    select_vertices(myRoom,[0,1])   
    mark_seam(myRoom) 
    # Unwrap
    unwrap_mesh(myRoom)
    
    remove_doubles(myRoom)
    set_normals(myRoom,not rp.inverse) # inside/outside

    if (rp.wall_width > 0.0):
        if (False == update or isSolidify(myRoom) == False):
            set_modifier_solidify(myRoom,get_BlendUnits(rp.wall_width))
        else:
            for mod in myRoom.modifiers:
                if (mod.type == 'SOLIDIFY'):
                    mod.thickness = rp.wall_width
        # Move to Top SOLIDIFY            
        moveToTopSolidify(myRoom)
                    
    else: # clear not used SOLIDIFY
        for mod in myRoom.modifiers:
            if (mod.type == 'SOLIDIFY'):
                myRoom.modifiers.remove(mod)
                        
        
    # Create baseboard
    if (rp.baseboard):
        BaseboardMesh = bpy.data.meshes.new("Baseboard")
        myBase = bpy.data.objects.new("Baseboard", BaseboardMesh)
        myBase.location = (0,0,0)
        bpy.context.scene.objects.link(myBase)
        myBase.parent = myRoom
        myBase.select = True
        myBase["archimesh.room_object"] = True
        myBase["archimesh.room_baseboard"] = True
        
        create_walls(rp,BaseboardMesh,get_BlendUnits(rp.base_height),True)
        set_normals(myBase,rp.inverse) # inside/outside room
        if (rp.base_width > 0.0):
            set_modifier_solidify(myBase,get_BlendUnits(rp.base_width))
            # Move to Top SOLIDIFY            
            moveToTopSolidify(myBase)
        # Mark Seams
        select_vertices(myBase,[0,1])   
        mark_seam(myBase) 
        # Unwrap
        unwrap_mesh(myBase)
        
    # Create floor
    if (rp.floor):
        myFloor = create_floor(rp,"Floor",myRoom)
        myFloor["archimesh.room_object"] = True
        myFloor.parent = myRoom    
        # Unwrap
        unwrap_mesh(myFloor)

    # Create ceiling
    if (rp.ceiling):
        myCeiling = create_floor(rp,"Ceiling",myRoom)
        myCeiling["archimesh.room_object"] = True
        myCeiling.parent = myRoom    
        # Unwrap
        unwrap_mesh(myCeiling)

    # Create materials        
    if (rp.crt_mat):
        # Wall material (two faces)
        mat = create_diffuse_material("Wall_material",False,0.765, 0.650, 0.588,0.8,0.621,0.570,0.1,True)
        set_material(myRoom,mat)

        # Baseboard material
        if (rp.baseboard):
            mat = create_diffuse_material("Baseboard_material",False,0.8, 0.8, 0.8)
            set_material(myBase,mat)

        # Ceiling material
        if (rp.ceiling):
            mat = create_diffuse_material("Ceiling_material",False,0.95, 0.95, 0.95)
            set_material(myCeiling,mat)

        # Floor material    
        if (rp.floor):
            mat = create_brick_material("Floor_material",False,0.711, 0.668, 0.668,0.8,0.636,0.315)
            set_material(myFloor,mat)


#------------------------------------------------------------------------------
# Create walls or baseboard (indicated with baseboard parameter).
# Some custom values are passed using the rp ("room properties" group) parameter (rp.myvariable).
#------------------------------------------------------------------------------
def create_walls(rp,mymesh,height,baseboard=False):
    myVertex = [(0.0,0.0,height),(0.0,0.0,0.0)]
    myFaces = []
    lastFace = 0
    lastX = lastY = 0

    # Iterate the walls
    for i in range(0,rp.wall_num):
        if (0 == i):
            prv = False
        else:
            prv = rp.walls[i-1].a and not rp.walls[i-1].curved
            
        myDat = make_wall(prv,rp.walls[i],baseboard,lastFace,
                          lastX,lastY,height,myVertex,myFaces)
        lastX = myDat[0]
        lastY = myDat[1]
        lastFace = myDat[2]

    # Close room
    if (rp.merge == True):
        if (baseboard == False):
            if (rp.walls[rp.wall_num-1].a != True):
                myFaces.extend([(0,1,lastFace + 1, lastFace)])
            else:   
                if (rp.walls[rp.wall_num-1].curved == True):
                    myFaces.extend([(0,1,lastFace + 1, lastFace)])
                else:   
                    myFaces.extend([(0,1,lastFace, lastFace + 1)])
        else:
            myFaces.extend([(0,1,lastFace + 1, lastFace)])


    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)


#------------------------------------------------------------------------------
# Make a Wall
#   prv: If previous wall has 'curved' activate.
#   lastFace: Number of faces of all before walls.
#   lastX: X position of the end of the last wall.
#   lastY: Y position of the end of the last wall.
#   height: Height of the last wall, without peak.
#------------------------------------------------------------------------------
def make_wall(prv,wall,baseboard,lastFace,lastX,lastY,height,myVertex,myFaces):
    #   size: Length of the wall.
    #   over: Height of the peak from "height".
    #   factor: Displacement of the peak (between -1 and 1; 0 is the middle of the wall).
    advanced = wall.a	
    size = wall.w
    over = wall.m	
    factor = wall.f
    angle = wall.r	
    hide = wall.h

    # if angle negative, calculate real
    # use add because the angle is negative 
    if (angle < 0):
        angle = 360 + angle
    # Verify Units    
    size = get_BlendUnits(size)
    over = get_BlendUnits(over)
    
    # Calculate size using angle
    sizeX = math.cos(math.radians(angle)) * size
    sizeY = math.sin(math.radians(angle)) * size
    
    # Create faces
    if (False == advanced or True == baseboard):
        # Cases of this first option: Baseboard or wall without peak and without curve.
        if (True == baseboard and True == advanced and True == wall.curved):
            (myVertex, myFaces, sizeX, sizeY, lastFace) = make_curved_wall(myVertex, myFaces, size, angle,
                                                             lastX, lastY, height, lastFace,
                                                             wall.curve_factor, int(wall.curve_arc_deg),
                                                             int(wall.curve_arc_deg/wall.curve_steps),
                                                             hide, baseboard)
        else:
            myVertex.extend([(lastX + sizeX,lastY + sizeY,height),
                             (lastX + sizeX,lastY + sizeY,0.0)])
            if (check_visibility(hide,baseboard)):
                if (prv == False or baseboard == True):
                    # Previous no advance or advance with curve
                    myFaces.extend([(lastFace,lastFace + 2,lastFace + 3,lastFace + 1)])
                else:
                    # Previous advance without curve
                    myFaces.extend([(lastFace,lastFace + 1,lastFace + 2,lastFace + 3)])
            lastFace = lastFace + 2
    else:
        # Case of this second option: Wall with advanced features (orientation, visibility and peak or curve).
        # Orientation and visibility options ('angle' and 'hide' variables) are only visible in panel
        # with advanced features, but are taken in account in any case.
        if (True == wall.curved):
            # Wall with curve and without peak.
            (myVertex, myFaces, sizeX, sizeY, lastFace) = make_curved_wall(myVertex, myFaces, size, angle,
                                                             lastX, lastY, height, lastFace,
                                                             wall.curve_factor, int(wall.curve_arc_deg),
                                                             int(wall.curve_arc_deg/wall.curve_steps),
                                                             hide, baseboard)
        else:
            # Wall with peak and without curve.
            mid = size / 2 + ((size / 2) * factor)
            midX = math.cos(math.radians(angle)) * mid
            midY = math.sin(math.radians(angle)) * mid
            # first face
            myVertex.extend([(lastX + midX,lastY + midY,height + over)
                             ,(lastX + midX,lastY + midY,0.0)])
            if (check_visibility(hide,baseboard)):
                if (math.fabs(factor) != 1):
                    if (prv == False):
                        # Previous no advance or advance with curve
                        myFaces.extend([(lastFace,lastFace + 2,lastFace + 3,lastFace + 1)])
                    else:
                        # Previous advance without curve
                        myFaces.extend([(lastFace,lastFace + 1,lastFace + 2,lastFace + 3)])
            # second face
            myVertex.extend([(lastX + sizeX,lastY + sizeY,0.0)
                             ,(lastX + sizeX,lastY + sizeY,height)])
            if (check_visibility(hide,baseboard)):
                if (math.fabs(factor) != 1):
                    myFaces.extend([(lastFace + 2,lastFace + 3,lastFace + 4,lastFace+ 5)])
                else:   
                    if (prv == False):
                        myFaces.extend([(lastFace, lastFace + 5, lastFace + 4, lastFace + 1),
                                        (lastFace, lastFace + 2, lastFace + 5)])
                    else:
                        myFaces.extend([(lastFace, lastFace + 4, lastFace + 5, lastFace + 1),
                                        (lastFace + 1, lastFace + 2, lastFace + 5)])
            
            lastFace = lastFace + 4
        
    lastX = lastX + sizeX
    lastY = lastY + sizeY
        
    return (lastX,lastY,lastFace)


#------------------------------------------------------------------------------
# Verify visibility of walls
#------------------------------------------------------------------------------
def check_visibility(h,base):
    # Visible
    if h == '0':
        return True
    # Wall
    if h == '2':
        if base == True:
            return False
        else:
            return True
    # Baseboard
    if h == '1':
        if base == True:
            return True
        else:
            return False
    # Hidden
    if h == '3':
        return False


#------------------------------------------------------------------------------
# Create a curved wall.
#------------------------------------------------------------------------------
def make_curved_wall(myVertex, myFaces, size, wall_angle, lastX, lastY, height,
                     lastFace, curve_factor, arc_angle, step_angle, hide, baseboard):
    # Calculate size using angle
    sizeX = math.cos(math.radians(wall_angle)) * size
    sizeY = math.sin(math.radians(wall_angle)) * size

    for step in range(0,arc_angle+step_angle,step_angle):
        curveX = sizeX/2 - math.cos(math.radians(step+wall_angle)) * size/2
        curveY = sizeY/2 - math.sin(math.radians(step+wall_angle)) * size/2
        curveY = curveY * curve_factor
        myVertex.extend([(lastX + curveX, lastY + curveY, height),
                         (lastX + curveX, lastY + curveY, 0.0)])
        if (check_visibility(hide,baseboard)):
            myFaces.extend([(lastFace,lastFace + 2,lastFace + 3,lastFace + 1)])
        lastFace = lastFace + 2
    return (myVertex, myFaces, curveX, curveY, lastFace)


#------------------------------------------------------------------------------
# Create floor or ceiling (create object and mesh)
# Parameters:
#   rm: "room properties" group
#   typ: Name of new object and mesh ('Floor' or 'Ceiling')
#   myRoom: Main object for the room
#------------------------------------------------------------------------------
def create_floor(rp,typ,myRoom):
    bpy.context.scene.objects.active = myRoom

    myVertex = []
    myFaces = []
    verts = []

    obverts = bpy.context.active_object.data.vertices
    for vertex in obverts:
        verts.append(tuple(vertex.co))
    # Loop only selected
    i = 0 
    for e in verts:
        if (typ == "Floor"):
            if (e[2] == 0.0):
                myVertex.extend([(e[0],e[1],e[2])])
                i = i + 1    
        else: # ceiling
            if (round(e[2],5) == round(get_BlendUnits(rp.room_height),5)):
                myVertex.extend([(e[0],e[1],e[2])])    
                i = i + 1

    # Create faces
    fa = []
    for f in range(0,i):
        fa.extend([f])

    myFaces.extend([fa])

    mymesh = bpy.data.meshes.new(typ)
    myobject = bpy.data.objects.new(typ, mymesh)

    myobject.location = (0,0,0)
    bpy.context.scene.objects.link(myobject)

    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)

    return myobject


#------------------------------------------------------------------
# Define property group class to create, or modify, room walls.
#------------------------------------------------------------------
class WallProperties(bpy.types.PropertyGroup):
    w = bpy.props.FloatProperty(name='Length',min=-150,max=150,default=1,precision=3,description='Length of the wall (negative to reverse direction)',update=update_room)

    a = bpy.props.BoolProperty(name="Advance",description="Define advance parameters of the wall",default=False,update=update_room)

    curved = bpy.props.BoolProperty(name="Curved",description="Enable curved wall parameters",default=False,update=update_room)
    curve_factor = bpy.props.FloatProperty(name='Factor',min=-5,max=5,default=1,precision=1,description='Curvature variation.',update=update_room)
    curve_arc_deg = bpy.props.FloatProperty(name='Degrees',min=0,max=359,default=180,precision=1,description='Degrees of the curve arc',update=update_room)
    curve_steps = bpy.props.IntProperty(name='Steps',min=2,max= 50,default=18,description='Curve steps',update=update_room)
    
    m = bpy.props.FloatProperty(name='Peak',min=0,max= 50,default=0,precision=3,description='Middle height variation',update=update_room)
    f = bpy.props.FloatProperty(name='Factor',min=-1,max= 1,default=0,precision=3,description='Middle displacement',update=update_room)
    r = bpy.props.FloatProperty(name='Angle',min=-180,max=180,default=0,precision=1,description='Wall Angle (-180 to +180)',update=update_room)

    h = bpy.props.EnumProperty(items = (('0',"Visible",""),('1',"Baseboard",""),('2',"Wall",""),('3',"Hidden","")),
                                 name="",description="Wall visibility",update=update_room)

bpy.utils.register_class(WallProperties)


#------------------------------------------------------------------
# Add a new room wall.
# First add a parameter group for that new wall, and then update the room.
#------------------------------------------------------------------
def add_room_wall(self,context):
    rp=context.object.RoomGenerator[0]
    for cont in range(len(rp.walls)-1,rp.wall_num):
        rp.walls.add()
        # by default, we alternate the direction of the walls.
        if (1 == cont % 2):
            rp.walls[cont].r = 90
    update_room(self,context)

#------------------------------------------------------------------
# Define property group class to create or modify a rooms.
#------------------------------------------------------------------
class RoomProperties(bpy.types.PropertyGroup):
    room_height = bpy.props.FloatProperty(name='Height',min=0.001,max=50,default= 2.4,precision=3,description='Room height',update=update_room)
    wall_width = bpy.props.FloatProperty(name='Thickness',min=0.000,max=10,default= 0.0,precision=3,description='Thickness of the walls',update=update_room)
    inverse = bpy.props.BoolProperty(name="Inverse",description="Inverse normals to outside.",default=False,update=update_room)
    crt_mat = bpy.props.BoolProperty(name="Create default Cycles materials",description="Create default materials for Cycles render.",default = True,update=update_room)

    wall_num = bpy.props.IntProperty(name='Number of Walls',min=1,max=50,default=1,description='Number total of walls in the room',update=add_room_wall)
    
    baseboard = bpy.props.BoolProperty(name="Baseboard",description="Create a baseboard automatically.",default=True,update=update_room)

    base_width = bpy.props.FloatProperty(name='Width',min=0.001,max= 10,default=0.015,precision=3,description='Baseboard width',update=update_room)
    base_height = bpy.props.FloatProperty(name='Height',min=0.05,max= 20,default=0.12,precision=3,description='Baseboard height',update=update_room)
    
    ceiling = bpy.props.BoolProperty(name="Ceiling",description="Create a ceiling.",default = False,update=update_room)
    floor = bpy.props.BoolProperty(name="Floor",description="Create a floor automatically.",default=False,update=update_room)

    merge = bpy.props.BoolProperty(name="Close walls",description="Close walls to create a full closed room.",default=False,update=update_room)

    walls = bpy.props.CollectionProperty(type=WallProperties)

bpy.utils.register_class(RoomProperties)
bpy.types.Object.RoomGenerator=bpy.props.CollectionProperty(type=RoomProperties)


#-----------------------------------------------------
# Add wall parameters to the panel.
#-----------------------------------------------------
def add_wall(idx,box,wall):
    box.label("Wall " + str(idx))
    row = box.row()
    row.prop(wall, 'w')
    row.prop(wall, 'a')
    #row.prop(wall, 'curved')
    if wall.a == True:
        srow = box.row()
        srow.prop(wall, 'r')
        srow.prop(wall, 'h')
        
        srow = box.row()
        srow.prop(wall, 'curved')
        
        if wall.curved == False:
            srow.prop(wall, 'm')
            srow.prop(wall, 'f')
            
        if wall.curved == True:
            srow.prop(wall, 'curve_factor')
            srow.prop(wall, 'curve_arc_deg')
            srow.prop(wall, 'curve_steps')


#------------------------------------------------------------------
# Define panel class to modify rooms.
#------------------------------------------------------------------
class RoomGeneratorPanel(bpy.types.Panel):
    bl_idname      ="OBJECT_PT_room_generator"
    bl_label       ="Room Generator"
    bl_space_type  ='VIEW_3D'
    bl_region_type ='UI'
    bl_category = 'Archimesh'

    #-----------------------------------------------------
    # Draw (create UI interface)
    #-----------------------------------------------------
    def draw(self, context):
        o = context.object
        # If the selected object didn't be created with the group 'RoomGenerator', this panel is not created.
        try:
            if ('RoomGenerator' not in o):
                return
        except:
            return
            
        layout = self.layout
        if (bpy.context.mode == 'EDIT_MESH'):
            layout.label('Warning: Operator does not work in edit mode.', icon='ERROR')
        else:
            room = o.RoomGenerator[0]
            row = layout.row()
            row.prop(room,'room_height')
            row.prop(room,'wall_width')
            row.prop(room,'inverse')

            row = layout.row()
            row.prop(room,'ceiling')
            row.prop(room,'floor')
            if room.wall_num > 1:
                row.prop(room,'merge')

            # Wall number
            row = layout.row()
            row.prop(room,'wall_num')

            # Add menu for walls
            if room.wall_num > 0:
                for wall_index in range(0,room.wall_num):
                    box = layout.box()
                    add_wall(wall_index + 1,box,room.walls[wall_index])

            box = layout.box()
            box.prop(room,'baseboard')
            if (room.baseboard == True):
                row = box.row()
                row.prop(room,'base_width')
                row.prop(room,'base_height')

            box = layout.box()
            box.prop(room,'crt_mat')
#----------------------------------------------
# Code to run alone the script
#----------------------------------------------
if __name__ == "__main__":
    print("Executed")
