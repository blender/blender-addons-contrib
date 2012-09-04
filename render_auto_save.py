bl_info = {
    "name": "Auto Save Render",
    "author": "tstscr",
    "version": (1, 0),
    "blender": (2, 6, 3),
    "location": "Rendertab -> Render Panel",
    "description": "Automatically save the image after rendering",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Render/Auto_Save",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=32491",
    "category": "Render"}
###########################################################################
import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.app.handlers import persistent
from os.path import dirname, exists, join
from bpy.path import basename
from os import mkdir, listdir
from re import findall


@persistent
def auto_save_render(scene):
    if not scene.save_after_render or not bpy.data.filepath:
        return
    rndr = scene.render
    original_format = rndr.image_settings.file_format

    format = rndr.image_settings.file_format = scene.auto_save_format
    if format == 'OPEN_EXR_MULTILAYER': extension = '.exr'
    if format == 'JPEG': extension = '.jpg'
    if format == 'PNG': extension = '.png'
    
    blendname = basename(bpy.data.filepath).rpartition('.')[0]
    filepath = dirname(bpy.data.filepath) + '/auto_saves'
    
    if not exists(filepath):
        mkdir(filepath)
        
    if scene.auto_save_subfolders:
        filepath = join(filepath, blendname)
        if not exists(filepath):
            mkdir(filepath)

    #imagefiles starting with the blendname
    files = [f for f in listdir(filepath) \
            if f.startswith(blendname) \
            and f.lower().endswith(('.png', '.jpg', '.jpeg', '.exr'))]
    
    highest = 0
    if files:
        for f in files:
            #find last numbers in the filename after the blendname
            suffix = findall('\d+', f.split(blendname)[-1])
            if suffix:
                if int(suffix[-1]) > highest:
                    highest = int(suffix[-1])
    
    save_name = join(filepath, blendname) + '_' + str(highest+1).zfill(3) + extension

    image = bpy.data.images['Render Result']
    if not image:
        print('Auto Save: Render Result not found. Image not saved')
        return
    
    print('Auto_Save:', save_name)
    image.save_render(save_name, scene=None)

    rndr.image_settings.file_format = original_format

###########################################################################
def auto_save_UI(self, context):
    layout = self.layout
    
    split=layout.split(percentage=0.66, align=True)
    row = split.row()
    row.prop(context.scene, 'save_after_render', text='Auto Save', toggle=False)
    row.prop(context.scene, 'auto_save_subfolders', toggle=False)
    #split=layout.split()
    row=split.row()
    row.prop(context.scene, 'auto_save_format', text='as', expand=False)
    
def register():
    bpy.types.Scene.save_after_render = BoolProperty(
                    name='Save after render',
                    default=True,
                    description='Automatically save rendered images into: //auto_save/')
    bpy.types.Scene.auto_save_format = EnumProperty(
                    name='Auto Save File Format',
                    description='File Format for the auto saves.',
                    items={
                    ('PNG', 'png', 'Save as png'),
                    ('JPEG', 'jpg', 'Save as jpg'),
                    ('OPEN_EXR_MULTILAYER', 'exr', 'Save as multilayer exr')},
                    default='PNG')
    bpy.types.Scene.auto_save_subfolders = BoolProperty(
                    name='subfolder',
                    default=False,
                    description='Save into individual subfolders per blend name')
    bpy.app.handlers.render_post.append(auto_save_render)
    bpy.types.RENDER_PT_render.append(auto_save_UI)
    
def unregister():
    del(bpy.types.Scene.save_after_render)
    del(bpy.types.Scene.auto_save_format)
    del(bpy.types.Scene.auto_save_subfolders)
    bpy.app.handlers.render_post.remove(auto_save_render)
    bpy.types.RENDER_PT_render.remove(auto_save_UI)

if __name__ == "__main__":
    register()