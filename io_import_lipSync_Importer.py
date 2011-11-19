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
    "name": "LipSync Importer & Blinker",
    "author": "Yousef Harfoush - bat3a ;)",
    "version": (0, 4, 0),
    "blender": (2, 5, 9),
    "api": 39900,
    "location": "3D window > Tool Shelf",
    "description": "Plot Moho (Papagayo, Jlipsync, Yolo) file to frames and adds automatic blinking",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.5/Py/Scripts/Import-Export/Lipsync_Importer",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=24080&group_id=153&atid=468",
    "category": "Import-Export"}


import bpy, re
from random import random
from bpy.props import *
from bpy.props import IntProperty, FloatProperty, StringProperty

global phnmlst
phnmlst="nothing"

# truning off relative path - it causes an error if it was true
if bpy.context.user_preferences.filepaths.use_relative_paths == True:
    bpy.context.user_preferences.filepaths.use_relative_paths = False

# add blinking
def blinker():
    
    scn = bpy.context.scene
    obj = bpy.context.object

    global blink, blinkphnm

    blink="off"
    blinkphnm=-1

    sk=len(obj.data.shape_keys.key_blocks)

    # searching for blink shapekey index
    for x in range(sk):
        obj.active_shape_key_index = x
        if obj.active_shape_key.name=="blink": blink="on"; blinkphnm=x

    if blinkphnm!=-1:
       
        if scn.remnuTypes.enumBlinks == '0':
            modifier = 0
        elif scn.remnuTypes.enumBlinks == '1':
            modifier = scn.blinkMod
        
        #creating keys with blinkNm count
        for y in range(scn.blinkNm):
            
            blinkfrm = y * scn.blinkSp + int(random()*modifier)
             
            crtkey(blinkphnm, blinkfrm)


# reading imported file & creating keys
def lipsyncer():
    
    obj = bpy.context.object
    scn = bpy.context.scene
    
    f=open(scn.fpath) # importing file
    f.readline() # reading the 1st line that we don"t need
    
    for line in f:

        # removing new lines
        lsta = re.split("\n+", line)

        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])# making a list of a frame number & 
        frm = int(lst[0])
        
        sk=len(obj.data.shape_keys.key_blocks)
        for x in range(sk):
            obj.active_shape_key_index = x
            oask=obj.active_shape_key.name
            if lst[1]==oask: crtkey(x, frm)

# retargetting?? ------WIP
def retargeter():
    
    scn = bpy.context.scene

    f=open(scn.fpath) # importing file
    f.readline() # reading the 1st line that we don"t need
    
    for line in f:
        # removing new lines
        lsta = re.split("\n+", line)
        
        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])# making a list of a frame number & 
        frm = int(lst[0])
        
        sk=len(obj.data.shape_keys.key_blocks)
        
        for x in range(sk):
            obj.active_shape_key_index = x
            oask=obj.active_shape_key.name
            if lst[1]==oask: crtkey(x, frm)
                    
# creating keys with offset and eases for a phonem @ the Skframe
def crtkey(phoneme, Skframe):
    
    global phnmlst
    
    scn = bpy.context.scene
    obj = bpy.context.object
    objSK=obj.data.shape_keys
    
    #setting the active shape key to phonem
    obj.active_shape_key_index=phoneme

    offst = scn.offset     # offset value
    skVlu = scn.skscale    # shape key value
    
    #in case of Papagayo format
    if scn.remnuTypes.enumFiles == '0' :
        frmIn = scn.easeIn     # ease in value
        frmOut = scn.easeOut   # ease out value
        hldIn = scn.holdGap    # holding time value
        
    #in case of Jlipsync format or Yolo
    elif scn.remnuTypes.enumFiles == '1' :
        frmIn = 1
        frmOut = 1
        hldIn = 0

    # inserting the In key only when phonem change or when blinking
    if phnmlst!=phoneme or eval(scn.mnuFunc) == 1:
        obj.active_shape_key.value=0.0
        objSK.key_blocks[phoneme].keyframe_insert("value",
            -1, offst+Skframe-frmIn, "Lipsync")
            
    obj.active_shape_key.value=skVlu
    objSK.key_blocks[phoneme].keyframe_insert("value", 
        -1, offst+Skframe, "Lipsync")
    
    obj.active_shape_key.value=skVlu
    objSK.key_blocks[phoneme].keyframe_insert("value", 
        -1, offst+Skframe+hldIn, "Lipsync")
            
    obj.active_shape_key.value=0.0
    objSK.key_blocks[phoneme].keyframe_insert("value", 
    -1, offst+Skframe+hldIn+frmOut, "Lipsync")
    
    phnmlst=phoneme
      
# lipsyncer operation start
class btn_lipsyncer(bpy.types.Operator):
    bl_idname = 'lipsync.go'
    bl_label = 'Start Processing'
    bl_description = 'Plots the voice file keys to timeline'

    def execute(self, context):

        scn = context.scene
        obj = context.object

        # testing if a mesh object with shape keys is selected
        if obj!=None and obj.type=="MESH":
            if obj.data.shape_keys!=None:
                if scn.fpath!='': lipsyncer()
                else: print ("select a Moho file")
            else: print("add shape keys PLEASE")
        else: print ("Object is not mesh or not selected ")
        return {'FINISHED'}

# blinker operation start
class btn_blinker(bpy.types.Operator):
    bl_idname = 'blink.go'
    bl_label = 'Start Processing'
    bl_description = 'Adds random or specifice blinks'

    def execute(self, context):
        
        scn = context.scene
        obj = context.object

        # testing if a mesh object with blink shape keys is selected
        if obj!=None and obj.type=="MESH":
            if obj.data.shape_keys!=None: blinker()
            else: print("add shape keys PLEASE")
        else: print ("Object is not mesh or not selected ")
        return {'FINISHED'}

# retargetting operation start
class btn_retarget(bpy.types.Operator):
    bl_idname = 'retarget.go'
    bl_label = 'Start Processing'
    bl_description = 'Refresh Shape Keys List'

    def execute(self, context):
        
        obj = context.object

        # testing if a mesh object with blink shape keys is selected
        if obj!=None and obj.type=="MESH":
            if obj.data.shape_keys!=None: retargeter()
            else: print("add shape keys PLEASE")
        else: print ("Object is not mesh or not selected ")
        return {'FINISHED'}

# getting props from current shape keys
class btn_refresh(bpy.types.Operator):
    bl_idname = 'refresh.go'
    bl_label = 'Start Processing'
    bl_description = 'Refresh Shape Keys List'

    def execute(self, context):
        
        scn = context.scene
        obj = context.object

        # testing if a mesh object with blink shape keys is selected
        if obj!=None and obj.type=="MESH":
            if obj.data.shape_keys!=None:
                
                obj = bpy.context.object
                typ = bpy.types.Scene
                sk = len(obj.data.shape_keys.key_blocks)
                
                for x in range(sk):
                    obj.active_shape_key_index=x
                    exec("typ.sk"+str(x)+"=StringProperty(name="+"obj.active_shape_key.name"+")")
                    
            else: print("add shape keys PLEASE")
        else: print ("Object is not mesh or not selected ")
        return {'FINISHED'}

#defining custom enumeratos
class mnuTypes(bpy.types.PropertyGroup):

    enumFiles = EnumProperty( items =(  ('0', 'Papagayo', ''), 
                                        ('1', 'Jlipsync Or Yolo', '')
                                        #,('2', 'Retarget', '')
                                        ),
                                        name = 'test',
                                        default = '0' )

    enumBlinks = EnumProperty( items =( ('0', 'Specific', ''),
                                        ('1', 'Random','')),
                                        name = 'test',
                                        default = '0' )
                        
# drawing the user interface
class LipSyncUI(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"
    bl_label = "LipSync Importer & Blinker"
    
    typ = bpy.types.Scene
    scn = bpy.context.scene
    
    typ.mnuFunc = EnumProperty(name="Select Mode ", description="Select function",
                                   items=(('0', 'Lipsyncer', ''), ('1', 'Blinker', '')), default='0')
        
    typ.fpath = StringProperty(name="Import File ", description="Select your voice file", subtype="FILE_PATH")
    typ.skscale = FloatProperty(description="Smoothing shape key values", min=0.1, max=1.0, default=0.8)
    typ.offset = IntProperty(description="Offset your frames", default=0)

    typ.easeIn = IntProperty(description="Smoothing In curve", min=1, default=3)
    typ.easeOut = IntProperty(description="Smoothing Out curve", min=1, default=3)
    typ.holdGap = IntProperty(description="Holding for slow keys", min=0, default=0)

    typ.blinkSp = IntProperty(description="Space between blinks", min=1, default=100)
    typ.blinkNm = IntProperty(description="Number of blinks", min=1, default=10)
    
    typ.blinkMod = IntProperty(description="Randomzing blinks keyframe placment", min=1, default=10)
    
    
    def draw(self, context):
        
        obj = bpy.context.object
        scn = bpy.context.scene
        
        layout = self.layout
        col = layout.column()

        #showing the current object type
        if obj != None:
            if obj.type == "MESH":
                split = col.split(align=True)
                split.label(text="The active object is: ", icon="OBJECT_DATA")
                split.label(obj.name, icon="EDITMODE_HLT")
            elif obj.type!="MESH":
                col.label(text="The active object is not a Mesh !", icon="OBJECT_DATA")
        else:
            layout.label(text="No object is selected", icon="OBJECT_DATA")
            
        col.prop(context.scene, "mnuFunc")
        col.separator()
        
        # the lipsyncer panel
        if bpy.context.scene.mnuFunc == '0':

            col.row().prop(context.scene.remnuTypes, 'enumFiles', text = ' ', expand = True)
            
            # Papagayo panel
            if scn.remnuTypes.enumFiles == '0':
                col.prop(context.scene, "fpath")
                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label("Frame Offset :")
                split.prop(context.scene, "offset")
                split = col.split(align=True)
                split.prop(context.scene, "easeIn", "Ease In")
                split.prop(context.scene, "holdGap", "Hold Gap")
                split.prop(context.scene, "easeOut", "Ease Out")
                
                col.operator('lipsync.go', text='Plot Keys PLEASE')

            # Jlipsync & Yolo panel
            elif scn.remnuTypes.enumFiles == '1':
                col.prop(context.scene, "fpath")
                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label("Frame Offset :")
                split.prop(context.scene, "offset")
                
                col.operator('lipsync.go', text='Plot Keys PLEASE')

#            # Retarget panel
#            elif scn.remnuTypes.enumFiles == '2':
#                col.prop(context.scene, "fpath")
#                split = col.split(align=True)
#                split.label("Key Value :")
#                split.prop(context.scene, "skscale")
#                split = col.split(align=True)
#                split.label("Frame Offset :")
#                split.prop(context.scene, "offset")
#                split = col.split(align=True)
#                split.prop(context.scene, "easeIn", "Ease In")
#                split.prop(context.scene, "holdGap", "Hold Gap")
#                split.prop(context.scene, "easeOut", "Ease Out")
#                
#                col.operator('refresh.go', text='Refresh Shape Key List')
#                
#                split = col.split(align=True)
#                split.label("Current shape keys:")
#                split.label("Mapping to custom keys:")
#    
#                obj = bpy.context.object
#                sk=len(obj.data.shape_keys.key_blocks)
#                
#                for x in range(sk):
#                    split = col.split(align=True)
#                    split.prop(context.scene, "sk"+str(x))
#                
#                col.operator('retarget.go', text='Plot Keys PLEASE')
          
        # the blinker panel
        elif bpy.context.scene.mnuFunc == '1':
            
            col.row().prop(context.scene.remnuTypes, 'enumBlinks', text = ' ', expand = True)
            
            # specific panel
            if scn.remnuTypes.enumBlinks == '0':
                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label("Frame Offset :")
                split.prop(context.scene, "offset")
                split = col.split(align=True)
                split.prop(context.scene, "easeIn", "Ease In")
                split.prop(context.scene, "holdGap", "Hold Gap")
                split.prop(context.scene, "easeOut", "Ease Out")
                col.prop(context.scene, "blinkSp", "Spacing")
                col.prop(context.scene, "blinkNm", "Times")
                col.operator('blink.go', text='Blink Keys PLEASE')
            
            # Random panel
            elif scn.remnuTypes.enumBlinks == '1':
                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label("Frame Start :")
                split.prop(context.scene, "offset")
                split = col.split(align=True)
                split.prop(context.scene, "easeIn", "Ease In")
                split.prop(context.scene, "holdGap", "Hold Gap")
                split.prop(context.scene, "easeOut", "Ease Out")
                split = col.split(align=True)
                split.prop(context.scene, "blinkSp", "Spacing")
                split.prop(context.scene, "blinkMod", "Random Modifier")
                col.prop(context.scene, "blinkNm", "Times")
                col.operator('blink.go', text='Blink Keys PLEASE')
                
        col.separator()
        col.label("Version 0.4 By Yousef Harfoush" )
        col.label("Updated 04/09/2011")

# clearing vars
def clear_properties():

    # can happen on reload
    if bpy.context.scene is None:
        return

    props = ["offset", "skscale", "easeIn", "easeOut", "blinkSp", "blinkNm", "holdGap", "blinkMod"]
    for p in props:
        if p in bpy.types.Scene.bl_rna.properties:
            exec("del bpy.types.Scene."+p)
        if p in bpy.context.scene:
            del bpy.context.scene[p]

# registering the script
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.remnuTypes = PointerProperty(type = mnuTypes)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.context.scene.remnuTypes

    clear_properties()

if __name__ == "__main__":
    register()
