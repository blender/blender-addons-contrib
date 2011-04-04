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
    "version": (0, 2, 6),
    "blender": (2, 5, 6),
    "api": 35816,
    "location": "3D window > Tool Shelf",
    "description": "Plot Papagayo's (or Jlipsync) voice file to frames and adds automatic blinking",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.5/Py/Scripts/Import-Export/Lipsync_Importer",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=24080&group_id=153&atid=468",
    "category": "Import-Export"}


import bpy, re
from bpy.props import *

mnulast = '1'

global phnmlst
phnmlst="rest"

# truning off relative path - it causes an error if it was true
if bpy.context.user_preferences.filepaths.use_relative_paths == True:
   bpy.context.user_preferences.filepaths.use_relative_paths = False

# add blinking
def blinker():
    
    scn = bpy.context.scene
    obj = bpy.context.object

    global blink, blinkphnm

    blink="off"
    blinkphnm=1983

    sk=len(obj.data.shape_keys.key_blocks)

    for x in range(sk):
        obj.active_shape_key_index = x
        if obj.active_shape_key.name=="blink": blink="on"; blinkphnm=x

    for y in range(scn['blinkNm']):

        blinkSpm=scn["blinkSp"]*y
        if blinkphnm!=1983: crtkey(blinkphnm, blinkSpm)


# mapping shape keys to phonemes vars.
def mapper():

    obj = bpy.context.object

    global AI, O, E, U, etc, L, WQ, MBP, FV, rest
    global AIphnm, Ophnm, Ephnm, Uphnm, etcphnm, Lphnm
    global WQphnm, MBPphnm, FVphnm, restphnm

    AI="off"; O="off"; E="off"; U="off"; etc="off"; L="off"
    WQ="off"; MBP="off"; FV="off"; rest="off"

    sk=len(obj.data.shape_keys.key_blocks)

    for x in range(sk):

        obj.active_shape_key_index = x

        if obj.active_shape_key.name=="AI": AI="on"; AIphnm=x
        elif obj.active_shape_key.name=="O": O="on"; Ophnm=x  
        elif obj.active_shape_key.name=="E": E="on"; Ephnm=x   
        elif obj.active_shape_key.name=="U": U="on"; Uphnm=x
        elif obj.active_shape_key.name=="etc": etc="on"; etcphnm=x
        elif obj.active_shape_key.name=="L": L="on"; Lphnm=x
        elif obj.active_shape_key.name=="WQ": WQ="on"; WQphnm=x
        elif obj.active_shape_key.name=="MBP": MBP="on"; MBPphnm=x
        elif obj.active_shape_key.name=="FV": FV="on"; FVphnm=x
        elif obj.active_shape_key.name=="rest": rest="on"; restphnm=x

    # calling file splitter
    splitter()


# reading imported file & creating keys
def splitter():
    
    scn = bpy.context.scene

    f=open(scn.fpath) # importing file
    f.readline() # reading the 1st line that we don"t need
    print("hhhh")
    for line in f:

        # removing new lines
        lsta = re.split("\n+", line)

        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])# making a list of a frame number & 
        frm = int(lst[0])

        # passing to create keys
        if lst[1]==("AI" or "A" or "I")and AI=="on": crtkey(AIphnm, frm)
        elif lst[1]=="O" and O=="on": crtkey(Ophnm, frm)
        elif lst[1]=="E" and E=="on": crtkey(Ephnm, frm)
        elif lst[1]=="U" and U=="on": crtkey(Uphnm, frm)
        elif lst[1]==("etc" or "C" or "D" or "G" or "K" or "N" or "R" or "S" or "TH" or "SH") and etc=="on": crtkey(etcphnm, frm)
        elif lst[1]=="L" and L=="on": crtkey(Lphnm, frm)
        elif lst[1]==("WQ" or "W" or "Q") and WQ=="on": crtkey(WQphnm, frm)
        elif lst[1]==("MBP" or "M" or "P" or "B") and MBP=="on": crtkey(MBPphnm, frm)
        elif lst[1]==("FV" or "F" or "V") and FV=="on": crtkey(FVphnm, frm)
        elif lst[1]==("rest" or "closed") and rest=="on": crtkey(restphnm, frm)  

# creating keys with offset and eases
def crtkey(phoneme, Skey):
    
    global phnmlst
    
    scn = bpy.context.scene
    obj = bpy.context.object

    objSK=obj.data.shape_keys
    obj.active_shape_key_index=phoneme

    offst=scn['offset']     # offset value
    skVlu=scn['skscale']    # shape key value
    frmIn=scn['easeIn']     # ease in value
    frmOut=scn['easeOut']   # ease out value
    hldIn=scn['holdGap']    # holding time value

    if bpy.context.scene['jlip'] == 1:
        
        if phnmlst!=phoneme:
            obj.active_shape_key.value=0.0
            objSK.key_blocks[phoneme].keyframe_insert("value",
                -1, offst+Skey-1, "Lipsync")
            
        obj.active_shape_key.value=skVlu
        objSK.key_blocks[phoneme].keyframe_insert("value", 
            -1, offst+Skey, "Lipsync")
                
        obj.active_shape_key.value=0.0
        objSK.key_blocks[phoneme].keyframe_insert("value", 
            -1, offst+Skey+1, "Lipsync")
        
        phnmlst=phoneme
        
    elif bpy.context.scene['jlip'] != 1:
        
        obj.active_shape_key.value=0.0
        objSK.key_blocks[phoneme].keyframe_insert("value",
            -1, offst+Skey-frmIn, "Lipsync")
    
        obj.active_shape_key.value=skVlu
        objSK.key_blocks[phoneme].keyframe_insert("value", 
            -1, offst+Skey, "Lipsync")
        
        obj.active_shape_key.value=skVlu
        objSK.key_blocks[phoneme].keyframe_insert("value", 
            -1, offst+Skey+hldIn, "Lipsync")
                
        obj.active_shape_key.value=0.0
        objSK.key_blocks[phoneme].keyframe_insert("value", 
        -1, offst+Skey+hldIn+frmOut, "Lipsync")

# clearing vars
def clear_properties():

    # can happen on reload
    if bpy.context.scene is None:
        return

    props = ["offset", "skscale", "easeIn", "easeOut", "blinkSp", "blinkNm", "holdGap", "jlip"]
    for p in props:
        if p in bpy.types.Scene.bl_rna.properties:
            exec("del bpy.types.Scene."+p)
        if p in bpy.context.scene:
            del bpy.context.scene[p]

# creating ui button to run things
class Lipsyncer(bpy.types.Operator):
    bl_idname = 'lipsync.go'
    bl_label = 'Start Processing'
    bl_description = 'Plots the voice file keys to timeline'

    def execute(self, context):

        scn = context.scene
        obj = context.object

        # testing if a mesh object with shape keys is selected
        if obj!=None and obj.type=="MESH":
            if obj.data.shape_keys!=None:
                if scn.fpath!='': mapper()
                else: print ("select a voice file")
            else: print("add shape keys PLEASE")
        else: print ("Object is not mesh or not selected ")
        return {'FINISHED'}

class Blinker_go(bpy.types.Operator):
    bl_idname = 'blink.go'
    bl_label = 'Start Processing'
    bl_description = 'Adds Random or Specifice blinks'

    def execute(self, context):
        
        scn = context.scene
        obj = context.object

        # testing if a mesh object with blink shape keys is selected
        if obj!=None and obj.type=="MESH":
            if obj.data.shape_keys!=None:
                blinker()
            else: print("add shape keys PLEASE")
        else: print ("Object is not mesh or not selected ")
        return {'FINISHED'}

class mnuSelect(bpy.types.Operator):
    bl_idname = 'view.operator'
    bl_label = 'Operator'
 
    # define possible operations
    modes = EnumProperty(items=(('1', 'Lipsyncer', '1'), ('2', 'Blinker', '2')))
 
    def execute(self, context):
 
        global mnulast
        
        # store the choosen selection
        mnulast = self.properties.modes 
        return {'FINISHED'}

# drawing the user interface
class LipSyncUI(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"
    bl_label = "LipSync Importer & Blinker"
    
    typ = bpy.types.Scene
    var = bpy.props

    typ.fpath = var.StringProperty(name="Import File ", description="Select your voice file", subtype="FILE_PATH", default="")
       
    typ.skscale = var.FloatProperty(description="Smoothing shape key values", min=0.1, max=1.0)
    typ.offset = var.IntProperty(description="Offset your frames")

    typ.easeIn = var.IntProperty(description="Smoothing In curve", min=1)
    typ.easeOut = var.IntProperty(description="Smoothing Out curve", min=1)
    typ.holdGap = var.IntProperty(description="Holding for slow keys", min=0)

    typ.blinkSp = var.IntProperty(description="Space between blinks", min=1)
    typ.blinkNm = var.IntProperty(description="Number of blinks", min=1)
    
    typ.jlip = var.BoolProperty(description="Enable Jlipsync file")

    def __init__(self):

        # intializing variables
        props = [("offset", 0), ("skscale", 0.8), ("easeIn", 3), ("easeOut", 3), ("blinkSp", 100), ("blinkNm", 10), ("holdGap", 0), ("jlip", 0)]
        for p, num in props:
            if not p in bpy.context.scene.keys():
                bpy.context.scene[p] = num

    def draw(self, context):
        
        obj = bpy.context.object
        
        global mnulast
        
        layout = self.layout
        col = layout.column()
        
        if obj != None:
            if obj.type == "MESH":
                split = col.split(align=True)
                split.label(text="Selected object is: ", icon="OBJECT_DATA")
                split.label(obj.name, icon="EDITMODE_HLT")
            elif obj.type!="MESH":
                layout.row().label(text="Object is not a Mesh", icon="OBJECT_DATA")
        else:
            layout.label(text="No object is selected", icon="OBJECT_DATA")

        layout = self.layout
        col = layout.column()
        
        col.label("Select Mode :")        
        
        if eval(mnulast)==1:
            col.operator_menu_enum('view.operator', 'modes', 'Lipsyncer')
            col.prop(context.scene, "fpath")
            col.prop(context.scene, "jlip", "Jlipsync Moho File")

        if eval(mnulast)==2:
            col.operator_menu_enum('view.operator', 'modes', 'Blinker')
            
        split = col.split(align=True)
        split.label("Key Value :")
        split.prop(context.scene, "skscale")

        split = col.split(align=True)
        split.label("Frame Offset :")
        split.prop(context.scene, "offset")
        
        if bpy.context.scene['jlip'] != 1:
            split = col.split(align=True)
            split.prop(context.scene, "easeIn", "Ease In")
            split.prop(context.scene, "holdGap", "Hold Gap")
            split.prop(context.scene, "easeOut", "Ease Out")

        if eval(mnulast)==1:
            col.operator('lipsync.go', text='Plote Keys PLEASE')

        if eval(mnulast)==2:
            col.prop(context.scene, "blinkSp", "Spacing")
            col.prop(context.scene, "blinkNm", "Times")
     
            col.operator('blink.go', text='Blink Keys PLEASE')

        col.separator()
        col.label("Version 0.26")
        col.label("Updated 30/03/2011")
        col.label("Yousef Harfoush")

# registering the script
def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

    clear_properties()

if __name__ == "__main__":
    register()