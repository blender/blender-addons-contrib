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
    "name": "XYZ Atomic Blender",
    "description": "Loading and manipulating atoms from XYZ files",
    "author": "Clemens Barth",
    "version": (0,5),
    "blender": (2,6),
    "api": 31236,
    "location": "File -> Import -> XYZ (.xyz), Panel: View 3D - Tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/"
                "Import-Export/XYZ#Loading_XYZ_filesp",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "index.php?func=detail&aid=29646&group_id=153&atid=468",
    "category": "Import-Export"
}


import bpy
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)



from . import import_xyz
ATOM_XYZ_ERROR = ""

# -----------------------------------------------------------------------------
#                                                                           GUI

# This is the panel, which can be used to prepare the scene.
# It is loaded after the file has been chosen via the menu 'File -> Import'
class CLASS_atom_xyz_prepare_panel(Panel):
    bl_label       = "XYZ - Atomic Blender"
    #bl_space_type  = "PROPERTIES"
    #bl_region_type = "WINDOW"
    #bl_context     = "physics"
    # This could be also an option ... :
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"

    @classmethod
    def poll(self, context):
        if import_xyz.ATOM_XYZ_FILEPATH == "":
            return False
        else:
            return True

    def draw(self, context):
        layout = self.layout
        scn    = bpy.context.scene

        row = layout.row()
        row.label(text="Outputs and custom data file")

        box = layout.box()
        row = box.row()
        row.label(text="Custom data file")
        row = box.row()
        col = row.column()
        col.prop(scn, "atom_xyz_datafile")
        col.operator("atom_xyz.datafile_apply")
        row = box.row()
        col = row.column(align=True)
        col.prop(scn, "atom_xyz_XYZ_file")
        row = box.row()
        # TODO, use lanel() instead
        row.prop(scn, "atom_xyz_number_atoms")
        row = box.row()
        row.operator("atom_xyz.button_distance")
        row.prop(scn, "atom_xyz_distance")

        row = layout.row()
        row.label(text="Choice of atom radii")
        box = layout.box()

        row = box.row()
        row.label(text="All changes concern:")
        row = box.row()
        row.prop(scn, "atom_xyz_radius_how")

        row = box.row()
        row.label(text="1. Change type of radii")
        row = box.row()
        row.prop(scn, "atom_xyz_radius_type")

        row = box.row()
        row.label(text="2. Change atom radii in pm")
        row = box.row()
        row.prop(scn, "atom_xyz_radius_pm_name")
        row = box.row()
        row.prop(scn, "atom_xyz_radius_pm")

        row = box.row()
        row.label(text="3. Change atom radii by scale")
        row = box.row()
        col = row.column()
        col.prop(scn, "atom_xyz_radius_all")
        col = row.column(align=True)
        col.operator( "atom_xyz.radius_all_bigger" )
        col.operator( "atom_xyz.radius_all_smaller" )

        if bpy.context.mode == 'EDIT_MESH':

            layout.separator()
            row = box.row()
            row.operator( "atom_xyz.separate_atom" )

        row = layout.row()
        row.label(text="Loading frames")

        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Frames")
        col = row.column()
        col.prop(scn, "atom_xyz_number_frames")
        row = box.row()
        col = row.column()
        col.label(text="Skip frames")
        col = row.column()
        col.prop(scn, "atom_xyz_skip_frames")
        row = box.row()
        col = row.column()
        col.label(text="Frames/key")
        col = row.column()
        col.prop(scn, "atom_xyz_images_per_key")        
        
        row = box.row()
        row.operator("atom_xyz.load_frames")
        row = box.row()
        row.operator("atom_xyz.delete_keys")
        row = box.row()
        row.operator( "atom_xyz.create_command")
        row = box.row()
        row.operator( "atom_xyz.render")


class CLASS_atom_xyz_IO(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scnn = bpy.context.scene
        import_xyz.DEF_atom_xyz_radius_type(
                scnn.atom_xyz_radius_type,
                scnn.atom_xyz_radius_how,
                )

    def Callback_radius_pm(self, context):
        scnn = bpy.context.scene
        import_xyz.DEF_atom_xyz_radius_pm(
                scnn.atom_xyz_radius_pm_name,
                scnn.atom_xyz_radius_pm,
                scnn.atom_xyz_radius_how,
                )

    # In the file dialog window
    scn = bpy.types.Scene
    scn.use_atom_xyz_cam = BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    scn.use_atom_xyz_lamp = BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    scn.use_atom_xyz_mesh = BoolProperty(
        name = "Mesh balls", default=False,
        description = "Do you want to use mesh balls instead of NURBS?")
    scn.atom_xyz_mesh_azimuth = IntProperty(
        name = "Azimuth", default=32, min=0,
        description = "Number of sectors (azimuth)")
    scn.atom_xyz_mesh_zenith = IntProperty(
        name = "Zenith", default=32, min=0,
        description = "Number of sectors (zenith)")
    scn.atom_xyz_scale_ballradius = FloatProperty(
        name = "Balls", default=1.0, min=0.0,
        description = "Scale factor for all atom radii")
    scn.atom_xyz_scale_distances = FloatProperty (
        name = "Distances", default=1.0, min=0.0,
        description = "Scale factor for all distances")
    scn.use_atom_xyz_center = BoolProperty(
        name = "Object to origin", default=False,
        description = "Shall the object first put into the global origin "
        "before applying the offsets on the left?")
    scn.atom_xyz_atomradius = EnumProperty(
        name="Type of radius",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radii"),
               ('1', "Atomic", "Use atomic radii"),
               ('2', "van der Waals", "Use van der Waals radii")),
               default='0',)

    # In the panel, first part
    scn.atom_xyz_datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    scn.atom_xyz_XYZ_file = StringProperty(
        name = "Path to file", default="",
        description = "Path of the XYZ file")
    # TODO, remove this property, its used for display only!
    scn.atom_xyz_number_atoms = StringProperty(name="",
        default="Number", description = "This output shows "
        "the number of atoms which have been loaded")
    scn.atom_xyz_distance = StringProperty(
        name="", default="Distance (A)",
        description="Distance of 2 objects in Angstrom")
    scn.atom_xyz_radius_how = EnumProperty(
        name="",
        description="Which objects shall be modified?",
        items=(('ALL_ACTIVE',"all active objects", "in the current layer"),
               ('ALL_IN_LAYER',"all"," in active layer(s)")),
               default='ALL_ACTIVE',)
    scn.atom_xyz_radius_type = EnumProperty(
        name="Type",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii")),
               default='0',update=Callback_radius_type)
    scn.atom_xyz_radius_pm_name = StringProperty(
        name="", default="Atom name",
        description="Put in the name of the atom (e.g. Hydrogen)")
    scn.atom_xyz_radius_pm = FloatProperty(
        name="", default=100.0, min=0.0,
        description="Put in the radius of the atom (in pm)",
        update=Callback_radius_pm)
    scn.atom_xyz_radius_all = FloatProperty(
        name="Scale", default = 1.05, min=1.0,
        description="Put in the scale factor")


    # In the panel, second part
    scn.atom_xyz_number_frames = StringProperty(
        name="", default="0",
        description="This is the total number of frames stored in the xyz file")
    scn.atom_xyz_skip_frames = IntProperty(
        name="", default=0, min=0,
        description="Number of frames you want to skip.")
    scn.atom_xyz_images_per_key = IntProperty(
        name="", default=1, min=0,
        description="Choose the number of images between 2 keys.")



# Button for creating a file that contains the command for rendering
class CLASS_atom_xyz_create_command(Operator):
    bl_idname = "atom_xyz.create_command"
    bl_label = "Create command"
    bl_description = "Create a shell command for rendering the scene"

    def execute(self, context):
        global ATOM_XYZ_ERROR
        import os
 
        scn = bpy.context.scene

        fstart = scn.frame_start
        fend = scn.frame_end
        file_blend = bpy.context.blend_data.filepath
        
        if file_blend == "":
            ATOM_XYZ_ERROR = "Save your scene first !"
            bpy.ops.atom_xyz.error_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}
            
        cameras = []    
        FOUND = False    
        for obj in bpy.context.scene.objects:  
            if obj.type == "CAMERA":
                cameras.append(obj)
                FOUND = True   
        if FOUND == False:
            ATOM_XYZ_ERROR = "No camera => no images !"
            bpy.ops.atom_xyz.error_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}      
        if bpy.context.scene.camera == None:
            bpy.context.scene.camera = cameras[0]
            
        KEYS_PRESENT = True
        for element in import_xyz.STRUCTURE:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = element
            element.select = True
            if element.data.shape_keys == None:
                KEYS_PRESENT = False
                break       
        if KEYS_PRESENT == False:
            ATOM_XYZ_ERROR = "No frames => no movie !"
            bpy.ops.atom_xyz.error_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}     
        
        bpy.ops.wm.save_mainfile()
        
        file_name = bpy.path.basename(file_blend)
        file_path = file_blend.replace(file_name,"")
        file_movie = bpy.path.display_name_from_filepath(file_blend)
        blender_exe = bpy.app.binary_path
                
        if os.name == "posix":
            execute = (blender_exe+" -b \'"+file_blend+"\' -x 1 -o //"+file_movie+
                  "_ -F AVIJPEG -s "+str(fstart)+" -e "+str(scn.frame_end)+" -a")
        else:
            execute = ("\""+blender_exe+"\" -b "+file_blend+" -x 1 -o //"+file_movie+
                  "_ -F AVIJPEG -s "+str(fstart)+" -e "+str(scn.frame_end)+" -a")

        if os.name == "posix":
            command_file = file_path + file_movie + ".sh"
        else:
            command_file = file_path + file_movie + ".txt"
        command_fp = open(command_file,"w")
           
        if os.name == "posix":        
            command_fp.write("#!/bin/sh\n")   
        command_fp.write("\n"+execute+"\n")     
        command_fp.close()

        return {'FINISHED'}


# Button for rendering the scene in a terminal
class CLASS_atom_xyz_render(Operator):
    bl_idname = "atom_xyz.render"
    bl_label = "Render"
    bl_description = "Render the scene"

    def execute(self, context):
        global ATOM_XYZ_ERROR
        import os
 
        scn = bpy.context.scene

        fstart = scn.frame_start
        fend = scn.frame_end
        file_blend = bpy.context.blend_data.filepath
        
        if file_blend == "":
            ATOM_XYZ_ERROR = "Save your scene first!"
            bpy.ops.atom_xyz.error_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}
            
        cameras = []    
        FOUND = False    
        for obj in bpy.context.scene.objects:  
            if obj.type == "CAMERA":
                cameras.append(obj)
                FOUND = True   
        if FOUND == False:
            ATOM_XYZ_ERROR = "No camera => no images !"
            bpy.ops.atom_xyz.error_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}      
        if bpy.context.scene.camera == None:
            bpy.context.scene.camera = cameras[0]
            
            
        KEYS_PRESENT = True
        for element in import_xyz.STRUCTURE:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = element
            element.select = True
            if element.data.shape_keys == None:
                KEYS_PRESENT = False
                break       
        if KEYS_PRESENT == False:
            ATOM_XYZ_ERROR = "No frames => no movie !"
            bpy.ops.atom_xyz.error_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}    
            
        bpy.ops.wm.save_mainfile()    
        
        file_name = bpy.path.basename(file_blend)
        file_path = file_blend.replace(file_name,"")
        file_movie = bpy.path.display_name_from_filepath(file_blend)
        blender_exe = bpy.app.binary_path
 
        if os.name == "posix":
            execute = (blender_exe+" -b \'"+file_blend+"\' -x 1 -o //"+file_movie+
                  "_ -F AVIJPEG -s "+str(fstart)+" -e "+str(scn.frame_end)+" -a")
            os_str = "xterm -e \"" + execute + "\" &"
        else:
            execute = ("\""+blender_exe+"\" -b "+file_blend+" -x 1 -o //"+file_movie+
                  "_ -F AVIJPEG -s "+str(fstart)+" -e "+str(scn.frame_end)+" -a")
            os_str = "C:\WINDOWS\system32\cmd.exe /C " + execute
            
        #print(os_str)    
        os.system(os_str)    
        
        return {'FINISHED'}


# Button deleting all shape keys of the structure
class CLASS_atom_xyz_delete_keys(Operator):
    bl_idname = "atom_xyz.delete_keys"
    bl_label = "Delete keys"
    bl_description = "Delete the shape keys"

    def execute(self, context):
    
        for element in import_xyz.STRUCTURE:
        
            if element.data.shape_keys == None:
                break
        
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = element
            element.select = True
        
            for key in element.data.shape_keys.key_blocks:
            
                bpy.ops.object.shape_key_remove()
        

        return {'FINISHED'}


# Button loading the shape keys
class CLASS_atom_xyz_load_frames(Operator):
    bl_idname = "atom_xyz.load_frames"
    bl_label = "Load frames"
    bl_description = "Load the frames"

    def execute(self, context):
        global ATOM_XYZ_ERROR
    
        scn = bpy.context.scene
        
        KEYS_PRESENT = False
        for element in import_xyz.STRUCTURE:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = element
            element.select = True
            if element.data.shape_keys != None:
                KEYS_PRESENT = True
                break
                
        if KEYS_PRESENT == True:
            ATOM_XYZ_ERROR = "Delete first the keys"
            bpy.ops.atom_xyz.error_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}
        
        
        import_xyz.DEF_atom_xyz_build_frames(scn.atom_xyz_images_per_key, scn.atom_xyz_skip_frames)

        return {'FINISHED'}



# Button loading a custom data file
class CLASS_atom_xyz_datafile_apply(Operator):
    bl_idname = "atom_xyz.datafile_apply"
    bl_label = "Apply"
    bl_description = "Use color and radii values stored in the custom file"

    def execute(self, context):
    
        scn = bpy.context.scene

        if scn.atom_xyz_datafile == "":
            return {'FINISHED'}

        import_xyz.DEF_atom_xyz_custom_datafile(scn.atom_xyz_datafile)

        # TODO, move this into 'import_xyz' and call the function
        for obj in bpy.context.selected_objects:
            if len(obj.children) != 0:
                child = obj.children[0]
                if child.type == "SURFACE" or child.type  == "MESH":
                    for element in import_xyz.ATOM_XYZ_ELEMENTS:
                        if element.name in obj.name:
                            child.scale = (element.radii[0],) * 3
                            child.active_material.diffuse_color = element.color
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    for element in import_xyz.ATOM_XYZ_ELEMENTS:
                        if element.name in obj.name:
                            obj.scale = (element.radii[0],) * 3
                            obj.active_material.diffuse_color = element.color

        return {'FINISHED'}


# Button for separating a single atom from a structure
class CLASS_atom_xyz_separate_atom(Operator):
    bl_idname = "atom_xyz.separate_atom"
    bl_label = "Separate atom"
    bl_description = "Separate the atom you have chosen"

    def execute(self, context):
        scn    = bpy.context.scene

        # Get first all important properties from the atom which the user
        # has chosen: location, color, scale
        obj = bpy.context.edit_object
        name = obj.name
        loc_obj_vec = obj.location
        scale = obj.children[0].scale
        material = obj.children[0].active_material

        # Separate the vertex from the main mesh and create a new mesh.
        bpy.ops.mesh.separate()
        new_object = bpy.context.scene.objects[0]
        # Keep in mind the coordinates <= We only need this
        loc_vec = new_object.data.vertices[0].co

        # And now, switch to the OBJECT mode such that we can ...
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # ... delete the new mesh including the separated vertex
        bpy.ops.object.select_all(action='DESELECT')
        new_object.select = True
        bpy.ops.object.delete()  # TODO, use scene.objects.unlink()

        # Create a new atom/vacancy at the position of the old atom
        current_layers=bpy.context.scene.layers

        if "Vacancy" not in name:
            if scn.use_atom_xyz_mesh == False:
                bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                    view_align=False, enter_editmode=False,
                                    location=loc_vec+loc_obj_vec,
                                    rotation=(0.0, 0.0, 0.0),
                                    layers=current_layers)
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(
                                segments=scn.atom_xyz_mesh_azimuth,
                                ring_count=scn.atom_xyz_mesh_zenith,
                                size=1, view_align=False, enter_editmode=False,
                                location=loc_vec+loc_obj_vec,
                                rotation=(0, 0, 0),
                                layers=current_layers)
        else:
            bpy.ops.mesh.primitive_cube_add(
                               view_align=False, enter_editmode=False,
                               location=loc_vec+loc_obj_vec,
                               rotation=(0.0, 0.0, 0.0),
                               layers=current_layers)

        new_atom = bpy.context.scene.objects.active
        # Scale, material and name it.
        new_atom.scale = scale
        new_atom.active_material = material
        new_atom.name = name + "_sep"

        # Switch back into the 'Edit mode' because we would like to seprate
        # other atoms may be (more convinient)
        new_atom.select = False
        obj.select = True
        bpy.context.scene.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        return {'FINISHED'}


# Button for measuring the distance of the active objects
class CLASS_atom_xyz_distance_button(Operator):
    bl_idname = "atom_xyz.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two objects"

    def execute(self, context):
        scn    = bpy.context.scene
        dist   = import_xyz.DEF_atom_xyz_distance()

        if dist != "N.A.":
           # The string length is cut, 3 digits after the first 3 digits
           # after the '.'. Append also "Angstrom".
           # Remember: 1 Angstrom = 10^(-10) m
           pos    = str.find(dist, ".")
           dist   = dist[:pos+4]
           dist   = dist + " A"

        # Put the distance into the string of the output field.
        scn.atom_xyz_distance = dist
        return {'FINISHED'}


# Button for increasing the radii of all atoms
class CLASS_atom_xyz_radius_all_bigger_button(Operator):
    bl_idname = "atom_xyz.radius_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene
        import_xyz.DEF_atom_xyz_radius_all(
                scn.atom_xyz_radius_all,
                scn.atom_xyz_radius_how,
                )
        return {'FINISHED'}


# Button for decreasing the radii of all atoms
class CLASS_atom_xyz_radius_all_smaller_button(Operator):
    bl_idname = "atom_xyz.radius_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene
        import_xyz.DEF_atom_xyz_radius_all(
                1.0/scn.atom_xyz_radius_all,
                scn.atom_xyz_radius_how,
                )
        return {'FINISHED'}



# This is the class for the file dialog.
class ImportXYZ(Operator, ImportHelper):
    bl_idname = "import_mesh.xyz"
    bl_label  = "Import XYZ (*.xyz)"

    filename_ext = ".xyz"
    filter_glob  = StringProperty(default="*.xyz", options={'HIDDEN'},)

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene

        row = layout.row()
        row.prop(scn, "use_atom_xyz_cam")
        row.prop(scn, "use_atom_xyz_lamp")
        row = layout.row()
        col = row.column()
        col.prop(scn, "use_atom_xyz_mesh")
        col = row.column(align=True)
        col.prop(scn, "atom_xyz_mesh_azimuth")
        col.prop(scn, "atom_xyz_mesh_zenith")

        row = layout.row()
        col = row.column()
        col.label(text="Scaling factors")
        col = row.column(align=True)
        col.prop(scn, "atom_xyz_scale_ballradius")
        col.prop(scn, "atom_xyz_scale_distances")

        row = layout.row()
        row.prop(scn, "use_atom_xyz_center")

        row = layout.row()
        row.prop(scn, "atom_xyz_atomradius")

    def execute(self, context):
        scn = bpy.context.scene
        
        import_xyz.ALL_FRAMES[:] = []
        import_xyz.NUMBER_FRAMES = 0
        import_xyz.ATOM_XYZ_ELEMENTS[:] = []
        import_xyz.ATOM_XYZ_FILEPATH = ""
        import_xyz.STRUCTURE[:] = []

        # This is in order to solve this strange 'relative path' thing.
        import_xyz.ATOM_XYZ_FILEPATH = bpy.path.abspath(self.filepath)

        scn.atom_xyz_XYZ_file = import_xyz.ATOM_XYZ_FILEPATH

        azimuth    = scn.atom_xyz_mesh_azimuth
        zenith     = scn.atom_xyz_mesh_zenith
        bradius    = scn.atom_xyz_scale_ballradius
        bdistance  = scn.atom_xyz_scale_distances
        radiustype = scn.atom_xyz_atomradius
        center     = scn.use_atom_xyz_center
        cam        = scn.use_atom_xyz_cam
        lamp       = scn.use_atom_xyz_lamp
        mesh       = scn.use_atom_xyz_mesh
        datafile   = scn.atom_xyz_datafile

        # Execute main routine
        atom_number = import_xyz.DEF_atom_xyz_main(
                mesh, azimuth, zenith, bradius,
                radiustype, bdistance, 
                center, cam, lamp, datafile)

        scn.atom_xyz_number_atoms = str(atom_number) + " atoms"
        scn.atom_xyz_number_frames = str(import_xyz.NUMBER_FRAMES)
        
        return {'FINISHED'}
        
   
class CLASS_atom_xyz_error_dialog(bpy.types.Operator):
    bl_idname = "atom_xyz.error_dialog"
    bl_label = "Attention !"
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="                          "+ATOM_XYZ_ERROR) 
    def execute(self, context):
        print("Atomic Blender - Error: "+ATOM_XYZ_ERROR+"\n")
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
        

# The entry into the menu 'file -> import'
def menu_func(self, context):
    self.layout.operator(ImportXYZ.bl_idname, text="XYZ (.xyz)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":

    register()
