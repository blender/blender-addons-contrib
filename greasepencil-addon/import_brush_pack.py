import bpy
import re
import ssl
import urllib.request

def unzip(zip_path, extract_dir_path):
    '''Get a zip path and a directory path to extract to'''
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir_path)

def simple_dl_url(url, dest, fallback_url=None):
    ## need to import urlib.request or linux module does not found 'request' using urllib directly
    ## need to create an SSl context or linux fail returning unverified ssl
    # ssl._create_default_https_context = ssl._create_unverified_context

    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print('Error trying to download\n', e)
        if fallback_url:
            print('\nDownload page for manual install:', fallback_url)
        return e

def download_url(url, dest):
    '''download passed url to dest file (include filename)'''
    import shutil
    import time
    ssl._create_default_https_context = ssl._create_unverified_context
    start_time = time.time()
    
    try:
        with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        print('Error trying to download\n', e)
        return e

    print(f"Download time {time.time() - start_time:.2f}s",)


def get_brushes(blend_fp):
    cur_brushes = [b.name for b in bpy.data.brushes]
    with bpy.data.libraries.load(str(blend_fp), link=False) as (data_from, data_to):
        # load brushes starting with 'pp' prefix if there are not already there
        data_to.brushes = [b for b in data_from.brushes if b.startswith('pp_') and not b in cur_brushes]
    
    ## force fake user for the brushes
    for b in data_to.brushes:
        b.use_fake_user = True
    
    return len(data_to.brushes)

class GP_OT_install_brush_pack(bpy.types.Operator):
    bl_idname = "gp.import_brush_pack"
    bl_label = "Download and import texture brush pack"
    bl_description = "Download and import Grease Pencil brush pack from blender cloud"
    bl_options = {"REGISTER", "INTERNAL"}

    # @classmethod
    # def poll(cls, context):
    #     return True

    def execute(self, context):

        ## Compare current loaded brush with a hardcoded list of brush (not that usefull)
        # all_brushes = [b.name for b in bpy.data.brushes]
        # brushlist = ['pp_cloud_1', 'pp_grass_1', 'pp_grass_2', 'pp_leafs_1', 'pp_leafs_2', 'pp_oil_1', 'pp_oil_2', 'pp_rough_1', 'pp_sktch_1', 'pp_sktch_2', 'pp_sktch_3', 'pp_spray_1', 'pp_spray_2', 'pp_stone_1', 'pp_wet_1']
        # if all([name in all_brushes for name in brushlist]):
        #     self.report({'WARNING'}, 'Brushes already loaded')
        #     return {"CANCELLED"}

        from pathlib import Path
        import tempfile
        
        """ ## try to get DL link from page... seem encapsulated in a 'project container':
        page_url = 'https://cloud.blender.org/p/gallery/5f235cc297f8815e74ffb90b'
        print(page_url)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

        try:
            response = urllib.request.urlopen(page_url, context = ssl_context)
        except Exception as e:
            print('Error trying to check download page:', e)
            return {"CANCELLED"}

        data = response.read()
        body = data.decode("utf-8")
        matches = re.findall(r'<a title=\"Download File\" href=\"(http.*?)\"', body)
        if not matches :
            self.report({'ERROR'}, 'Url not found on webpage')
            return {"CANCELLED"}
        
        self.report({'INFO'}, '--'.join(matches))

        ## update dl_url string from match
        dl_url = matches[0]
        """

        ## URL seem to change everytime link is updated !
        dl_url = 'https://storage.googleapis.com/5649de716dcaf85da2faee95/_%2F1fc0d9422d724dd680f3240b07fb8017.zip?GoogleAccessId=956532172770-27ie9eb8e4u326l89p7b113gcb04cdgd%40developer.gserviceaccount.com&Expires=1600636870&Signature=I9XJeh9rjlLv2c76WUlWbgtO4v%2BkNj3TrRNlyB6sKIicpxDHyuy9wef0fwESf6Szl8YAiK6nq739RpgkR8IYolRHq5YkobI3MNFr52daC1m9B4Jem%2FXIcyvPWUGuh%2BD3u5OFkV6xcecb%2F3T3YXlzhGt%2FQFeuLWKv6S2lFOudfv5Vhii4aN6k0mT2%2BlUt2bRc5AbkzxIwNhg7%2FHO9%2FyDkHCdncQ7CZi874BMlC2hoF30PQSCEk9dtuZ0vafR90xt4lZ2G1fKk%2Fj0C2CH8Bxjl2M%2FBjhr26yMvccILUMmekMsq%2F%2BYA6fVfz8LxfA74sRmznHzi7QZLjjC0wuOW7ZPKbA%3D%3D'
        blendname = 'Daniel Martinez Lara (pepeland)_brush_pack_V2.blend'
        zipname = 'Daniel Martinez Lara (pepeland)_brush_pack_V2.zip'

        temp = tempfile.gettempdir()
        if not temp:
            self.report({'ERROR'}, 'no os temporary directory found to download brush pack (using python tempfile.gettempdir())')
            return {"CANCELLED"}
        
        temp = Path(temp)
        
        brushzip = temp / zipname
        blend_fp = Path(temp) / blendname
        
        '''### Part to load existing files instead of redownloading
        ## use blend if exists in tempdir
        if blend_fp.exists():
            bct = get_brushes(blend_fp)
            if bct:
                self.report({'INFO'}, f'{bct} brushes installed')
            return {"FINISHED"}

        ## unzip if zip already there and use blend
        if brushzip.exists():
            unzip(brushzip, temp)
            bct = get_brushes(blend_fp)
            if bct:
                self.report({'INFO'}, f'{bct} brushes installed')
            return {"FINISHED"}
        '''
        
        ## download, unzip, use blend
        # err = download_url(dl_url, str(brushzip))
        err = simple_dl_url(dl_url, str(brushzip), fallback_url='https://cloud.blender.org/p/gallery/5f235cc297f8815e74ffb90b')
        if err:
            self.report({'ERROR'}, 'Could not download brush pack. Check your internet connection. (see console for detail)')
            return {"CANCELLED"}

        unzip(brushzip, temp)
        bct = get_brushes(blend_fp)
        if bct:
            self.report({'INFO'}, f'{bct} brushes installed')
        else:
            self.report({'WARNING'}, 'Brushes already loaded')
        return {"FINISHED"}


def register():
    bpy.utils.register_class(GP_OT_install_brush_pack)

def unregister():
    bpy.utils.unregister_class(GP_OT_install_brush_pack)