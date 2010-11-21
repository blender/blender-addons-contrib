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

bl_addon_info = {
    "name": "LipSync Importer",
    "author": "Yousef Harfoush - bat3a ;)",
    "version": (0,2,0),
    "blender": (2, 5, 4),
    "api": 32077,
    "location": "3D window > Tool Shelf",
    "description": "Plot Papagayo's voice file to frames",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import/Export"}


import bpy, re

# intializing variables
obj = bpy.context.object
scn = bpy.context.scene
typ = bpy.types.Scene
var = bpy.props

scn['offset']=0
scn['skscale']=0.8    
scn['easeIn']=3
scn['easeOut']=3

# truning off relative path - it causes an error if it was true
if bpy.context.user_preferences.filepaths.use_relative_paths == True:
   bpy.context.user_preferences.filepaths.use_relative_paths = False

# mapping shape keys to phonemes vars.
def mapper():
    
    global AI, O, E, U, etc, L, WQ, MBP, FV, rest
    global AIphnm, Ophnm, Ephnm, Uphnm, etcphnm, Lphnm
    global WQphnm, MBPphnm, FVphnm, restphnm
    
    AI="off"; O="off"; E="off"; U="off"; etc="off"; L="off"
    WQ="off"; MBP="off"; FV="off"; rest="off"
      
    sk=len(obj.data.shape_keys.keys)
    
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
    spltr()


# reading imported file & creating keys
def spltr():
    
    f=open(scn.fpath) # importing file
    f.readline() # reading the 1st line that we don"t need
    
    for line in f:
        
        # removing new lines
        lsta = re.split("\n+", line)
        
        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])
        frm = int(lst[0])
        
        # creating keys
        if lst[1]=="AI" and AI=="on": crtkey(AIphnm, frm)
        elif lst[1]=="O" and O=="on": crtkey(Ophnm, frm)
        elif lst[1]=="E" and E=="on": crtkey(Ephnm, frm)
        elif lst[1]=="U" and U=="on": crtkey(Uphnm, frm)
        elif lst[1]=="etc" and etc=="on": crtkey(etcphnm, frm)
        elif lst[1]=="L" and L=="on": crtkey(Lphnm, frm)
        elif lst[1]=="WQ" and WQ=="on": crtkey(WQphnm, frm)
        elif lst[1]=="MBP" and MBP=="on": crtkey(MBPphnm, frm)
        elif lst[1]=="FV" and FV=="on": crtkey(FVphnm, frm)
        elif lst[1]=="rest" and rest=="on": crtkey(restphnm, frm)

# creating keys with offset and eases
def crtkey(phoneme, Skey):
    
    objSK=obj.data.shape_keys
    obj.active_shape_key_index=phoneme
    
    offst=scn['offset']        # offset value
    skVlu=scn['skscale']       # shape key value
    frmIn=scn['easeIn']        # ease in value
    frmOut=scn['easeOut']      # ease out value
        
    obj.active_shape_key.value=0.0
    objSK.keys[phoneme].keyframe_insert("value",
        -1, offst+Skey-frmIn, "Lipsync")

    obj.active_shape_key.value=skVlu
    objSK.keys[phoneme].keyframe_insert("value", 
        -1, offst+Skey, "Lipsync")
    
    obj.active_shape_key.value=0.0
    objSK.keys[phoneme].keyframe_insert("value", 
        -1, offst+Skey+frmOut, "Lipsync")


# creating ui button to running things
class LipSync_go(bpy.types.Operator):
    bl_idname = 'LipSync_go'
    bl_label = 'Start Processing'
    bl_description = 'Plots the voice file keys to timeline'
    
    def execute(self, context):
        
        # testing if a mesh object with shape keys is selected
        if obj!=None and obj.type=="MESH":
            if obj.data.shape_keys!=None:
                if scn.fpath!='': mapper()
                else: print ("select a voice file")
            else: print("add shape keys PLEASE")
        else: print ("Object is not mesh or not selected ")
        return {'FINISHED'}

# drawing the user intreface
class LipSync_viewer(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"
    bl_label = "LipSync Importer"
    
    def draw(self, context):
        
        typ.fpath = var.StringProperty(name="Import File ", description="Select your voice file", subtype="FILE_PATH", default="")
        typ.skscale = var.FloatProperty(description="Smoothing shape key values", min=0.1, max=1.0)
        typ.offset = var.IntProperty(description="Offset your frames")
        typ.easeIn = var.IntProperty(description="Smoothing In curve", min=1)
        typ.easeOut = var.IntProperty(description="Smoothing Out curve", min=1)
        
        layout = self.layout
        
        if obj != None:
            if obj.type == "MESH":
                col = layout.column()
                split = col.split(align=True)
                split.label(text="Selected object is: ", icon="OBJECT_DATA")
                split.label(obj.name, icon="EDITMODE_HLT")
            elif obj.type!="MESH":
                layout.row().label(text="Object is not a Mesh", icon="OBJECT_DATA")
        else:
            layout.label(text="No object is selected", icon="OBJECT_DATA")    
        
        layout.prop(context.scene, "fpath")

        col = layout.column()
        split = col.split(align=True)
        split.label("Shape Key Value :")
        split.prop(context.scene, "skscale")
        
        col = layout.column()
        split = col.split(align=True)
        split.label("Frame Offset :")
        split.prop(context.scene, "offset")

        col = layout.column()
        split = col.split(align=True)
        split.prop(context.scene, "easeIn", "Ease In")
        split.prop(context.scene, "easeOut", "Ease Out")
        
        
        col = layout.column()
        col.separator()
        col.operator('LipSync_go', text='Plote Keys PLEASE')
        
        col.separator()
        col.label("Version 0.21 Updated 27/9/2010")
        col.label("Yousef Harfoush")

# registering the script
def register():
    pass
def unregister():
    pass
if __name__ == "__main__":
   register()