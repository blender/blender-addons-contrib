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
# File: books_maker.py
# Automatic generation of books
# Author: Antonio Vazquez (antonioya)
#
#----------------------------------------------------------
import bpy
import math
import random
import copy
import colorsys
from tools import *

#------------------------------------------------------------------
# Define UI class
# Books
#------------------------------------------------------------------
class BOOKS(bpy.types.Operator):
    bl_idname = "mesh.archimesh_books"
    bl_label = "Books"
    bl_description = "Books Generator"
    bl_category = 'Archimesh'
    bl_options = {'REGISTER', 'UNDO'}
    
    width= bpy.props.FloatProperty(name='Width',min=0.001,max= 1, default= 0.045,precision=3, description='Bounding book width')
    depth= bpy.props.FloatProperty(name='Depth',min=0.001,max= 1, default= 0.22,precision=3, description='Bounding book depth')
    height= bpy.props.FloatProperty(name='Height',min=0.001,max= 1, default= 0.30,precision=3, description='Bounding book height')
    num= bpy.props.IntProperty(name='Number of books',min=1,max= 100, default= 20, description='Number total of books')

    rX= bpy.props.FloatProperty(name='X',min=0.000,max= 0.999, default= 0,precision=3, description='Randomness for X axis')
    rY= bpy.props.FloatProperty(name='Y',min=0.000,max= 0.999, default= 0,precision=3, description='Randomness for Y axis')
    rZ= bpy.props.FloatProperty(name='Z',min=0.000,max= 0.999, default= 0,precision=3, description='Randomness for Z axis')

    rot= bpy.props.FloatProperty(name='Rotation',min=0.000,max= 1, default= 0,precision=3, description='Randomness for vertical position (0-> All straight)')
    afn= bpy.props.IntProperty(name='Affinity',min=0,max= 10, default= 5, description='Number of books with same rotation angle')

    # Materials        
    crt_mat = bpy.props.BoolProperty(name = "Create default Cycles materials",description="Create default materials for Cycles render.",default = True)
    hue= bpy.props.FloatProperty(name='H',min=0,max= 1, default= 0,precision=3, description='Color Hue')
    saturation= bpy.props.FloatProperty(name='S',min=0,max= 1, default= 0.4,precision=3, description='Color Saturation')
    value= bpy.props.FloatProperty(name='V',min=0,max= 1, default= 0.4,precision=3, description='Color Value')
    rC= bpy.props.FloatProperty(name='Randomness',min=0.000,max= 1, default= 0,precision=3, description='Randomness for color (only Hue)')

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
            box.label("Book size")
            row=box.row()
            row.prop(self,'width')
            row.prop(self,'depth')
            row.prop(self,'height')
            row=box.row()
            row.prop(self,'num',slider=True)

            box=layout.box()
            box.label("Randomness")
            row=box.row()
            row.prop(self,'rX',slider=True)
            row.prop(self,'rY',slider=True)
            row.prop(self,'rZ',slider=True)
            row=box.row()
            row.prop(self,'rot',slider=True)
            row.prop(self,'afn',slider=True)


            box=layout.box()
            box.prop(self,'crt_mat')
            if (self.crt_mat):
                row=box.row()
                row.prop(self,'hue',slider=True)
                row=box.row()
                row.prop(self,'saturation',slider=True)
                row=box.row()
                row.prop(self,'value',slider=True)
                row=box.row()
                row.prop(self,'rC',slider=True)
        else:
            row=layout.row()
            row.label("Warning: Operator does not work in local view mode", icon='ERROR')

    #-----------------------------------------------------
    # Execute
    #-----------------------------------------------------
    def execute(self, context):
        if (bpy.context.mode == "OBJECT"):
            # Create shelves    
            create_book_mesh(self,context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}

#------------------------------------------------------------------------------
# Generate mesh data
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def create_book_mesh(self,context):
    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    bpy.ops.object.select_all(False)
    generate_books(self,context)

    return
#------------------------------------------------------------------------------
# Generate books
# All custom values are passed using self container (self.myvariable)
#------------------------------------------------------------------------------
def generate_books(self,context):

    Boxes = []
    location = bpy.context.scene.cursor_location
    myLoc = copy.copy(location) # copy location to keep 3D cursor position
    
    # Create 
    lastX = myLoc.x
    oX = 0
    oY = 0
    oZ = 0
    oR = 0
    i = 0
    for x in range(self.num):
        # reset rotation
        if (i >= self.afn):
            i = 0
            oR = -1
                   
        myData = create_book("Book" + str(x)
                           ,self.width,self.depth,self.height
                           ,lastX,myLoc.y,myLoc.z
                           ,self.crt_mat
                           ,self.rX,self.rY,self.rZ,self.rot,oX,oY,oZ,oR
                           ,self.hue,self.saturation,self.value,self.rC)
        Boxes.extend([myData[0]])
        bookData = myData[1]
        
        # calculate rotation using previous book
        oR = bookData[3]
        i = i + 1
        oZ = 0
        
        # calculate x size after rotation
        if (i < self.afn):
            size = 0.0002 
        else:    
            size = 0.0003 + math.cos(math.radians(90 - bookData[3])) * bookData[2] # the height is the radius
            oZ = bookData[2]
            
        lastX = lastX + bookData[0] + size
        
    # refine units
    for box in Boxes:
        remove_doubles(box)
        set_normals(box)
        
    # deactivate others
    for o in bpy.data.objects:
        if (o.select == True):
            o.select = False
    
    Boxes[0].select = True        
    bpy.context.scene.objects.active = Boxes[0]
    
    return
#------------------------------------------------------------------------------
# Create books unit
#
# objName: Name for the new object
# thickness: wood thickness (sides)
# sX: Size in X axis
# sY: Size in Y axis
# sZ: Size in Z axis
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: Flag for creating materials
# frX: Random factor X
# frY: Random factor Y
# frZ: Random factor Z
# frR: Random factor Rotation
# oX: override x size
# oY: override y size
# oZ: override z size
# oR: override rotation
# hue: color hue
# saturation: color saturation
# value: color value
# frC: color randomness factor (only hue)
#------------------------------------------------------------------------------
def create_book(objName,sX,sY,sZ,pX,pY,pZ,mat,frX,frY,frZ,frR,oX,oY,oZ,oR,hue,saturation,value,frC):
    # gap Randomness
    rI = random.randint(10,150)
    gap = rI / 100000
    # Randomness X   
    if (oX == 0):
        rI = random.randint(0,int(frX * 1000))
        factor = rI / 1000
        sX = sX - (sX * factor)
        if (sX < (gap * 3)):
            sX = gap * 3
    else:
        sX = oX        

    # Randomness Y   
    if (oY == 0):
        rI = random.randint(0,int(frY * 1000))
        factor = rI / 1000
        sY = sY - (sY * factor)
        if (sY < (gap * 3)):
            sY = gap * 3
    else:
        sY = oY        

    # Randomness Z   
    if (oZ == 0):
        rI = random.randint(0,int(frZ * 1000))
        factor = rI / 1000
        sZ = sZ - (sZ * factor)
        if (sZ < (gap * 3)):
            sZ = gap * 3
    else:
        sZ = oZ        

    # Randomness rotation   
    rot = 0
    if (frR > 0 and oR != -1):
        if (oR == 0):
            rI = random.randint(0,int(frR * 1000))
            factor = rI / 1000
            rot = 30 * factor
        else:
            rot = oR    

    # Randomness color (only hue)   
    if (frC > 0):
        rC1 = random.randint(0,int(hue * 1000)) # 0 to hue
        rC2 = random.randint(int(hue * 1000),1000) # hue to maximum
        rC3 = random.randint(0,1000) # sign

        if (rC3 >= hue * 1000):
            hue = hue + ((rC2 * frC) / 1000)
        else:
            hue = hue -  ((rC1 * frC) / 1000)
                


    myVertex = []
    myFaces = []
    x = 0
    # Left side
    myVertex.extend([(x,-sY,0),(0,0,0),(x,0,sZ),(x,-sY,sZ)])
    myFaces.extend([(0,1,2,3)])

    myVertex.extend([(x + gap,-sY + gap,0),(x + gap,0,0),(x + gap,0,sZ),(x + gap,-sY + gap,sZ)])
    myFaces.extend([(4,5,6,7)])
    
    # Right side
    x = sX - gap
    myVertex.extend([(x,-sY + gap,0),(x,0,0),(x,0,sZ),(x,-sY + gap,sZ)])
    myFaces.extend([(8,9,10,11)])
    
    myVertex.extend([(x + gap,-sY,0),(x + gap,0,0),(x + gap,0,sZ),(x + gap,-sY,sZ)])
    myFaces.extend([(12,13,14,15)])
    
    myFaces.extend([(0,12,15,3),(4,8,11,7),(3,15,11,7),(0,12,8,4),(0,1,5,4),(8,9,13,12),(3,2,6,7)
                    ,(11,10,14,15),(1,2,6,5),(9,10,14,13)])
    
    # Top inside
    myVertex.extend([(gap,-sY + gap,sZ-gap),(gap, -gap,sZ-gap),(sX-gap, -gap,sZ-gap),(sX-gap,-sY + gap,sZ-gap)])
    myFaces.extend([(16,17,18,19)])
     
    # bottom inside and front face
    myVertex.extend([(gap,-sY + gap,gap),(gap, -gap,gap),(sX-gap, -gap,gap),(sX-gap,-sY + gap,gap)])
    myFaces.extend([(20,21,22,23),(17,18,22,21)])

    mymesh = bpy.data.meshes.new(objName)
    myBook = bpy.data.objects.new(objName, mymesh)
    
    myBook.location[0] = pX
    myBook.location[1] = pY
    myBook.location[2] = pZ + math.sin(math.radians(rot)) * sX 
    bpy.context.scene.objects.link(myBook)
    
    mymesh.from_pydata(myVertex, [], myFaces)
    mymesh.update(calc_edges=True)
    
    #---------------------------------
    # Materials and UV Maps
    #---------------------------------
    if (mat):
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        # External
        mat = create_diffuse_material(objName + "_material", True, rgb[0], rgb[1], rgb[2], rgb[0], rgb[1], rgb[2], 0.05)
        set_material(myBook, mat)
        # UV unwrap external
        select_faces(myBook, 0, True)
        select_faces(myBook, 3, False)
        select_faces(myBook, 4, False)
        unwrap_mesh(myBook,False)
        # Add Internal
        mat = create_diffuse_material(objName + "_side_material", True, 0.5, 0.5, 0.5, 0.5, 0.5, 0.3, 0.03)
        myBook.data.materials.append(mat)
        select_faces(myBook, 14, True)
        select_faces(myBook, 15, False)
        select_faces(myBook, 16, False)
        set_material_faces(myBook, 1)
        # UV unwrap
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        select_faces(myBook, 14, True)
        select_faces(myBook, 15, False)
        select_faces(myBook, 16, False)
        unwrap_mesh(myBook,False)
        
    #---------------------------------
    # Rotation on Y axis
    #---------------------------------
    myBook.rotation_euler = (0.0, math.radians(rot), 0.0) # radians
    
    # add some gap to the size between books
    return (myBook,(sX,sY,sZ,rot))

#----------------------------------------------
# Code to run alone the script
#----------------------------------------------
if __name__ == "__main__":
    create_mesh(0)
    print("Executed")
