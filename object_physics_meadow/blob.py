### BEGIN GPL LICENSE BLOCK #####
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

# <pep8 compliant>

import bpy
from bpy_extras import object_utils
from math import *
from mathutils import *
from mathutils.kdtree import KDTree

from meadow import settings as _settings
from meadow import duplimesh
from meadow.duplimesh import project_on_ground
from meadow.util import *

_blob_object_name = "__MeadowBlob__"

def blob_objects(context):
    settings = _settings.get(context)
    blob_group = settings.blob_group(context)
    # ignore objects with invalid blob index
    return [ob for ob in blob_group.objects if ob.meadow.blob_index >= 0]

def blob_group_clear(context):
    settings = _settings.get(context)
    blob_group = settings.blob_group(context)
    scene = context.scene
    
    # local list copy to avoid messing up the iterator
    objects = [ob for ob in blob_group.objects]
    
    for ob in objects:
        scene.objects.unlink(ob)
        blob_group.objects.unlink(ob)
        
        # note: this can fail if something still references the object
        # we try to unlink own pointers above, but users might add own
        if ob.users == 0:
            bpy.data.objects.remove(ob)
        else:
            print("Warning: could not remove object %r" % ob.name)

def blob_group_assign(context, blobob):
    settings = _settings.get(context)
    blob_group = settings.blob_group(context)
    
    blob_group.objects.link(blobob)
    # NOTE: unsetting the type is important, otherwise gathering templates
    # a second time will include deleted objects!
    blobob.meadow.type = 'NONE'

def blob_group_remove(context, blobob):
    settings = _settings.get(context)
    blob_group = settings.blob_group(context)
    
    blob_group.objects.unlink(blobob)

def blob_apply_settings(ob, settings):
    ob.draw_type = settings.dupli_draw_type
    
    particle_draw_method = 'NONE' if settings.dupli_draw_type in {'BOUNDS'} else 'RENDER'
    for psys in ob.particle_systems:
        psys.settings.draw_method = particle_draw_method

#-----------------------------------------------------------------------

# assign sample to a blob, based on distance weighting
def assign_blob(blobtree, loc, nor):
    num_nearest = 4 # number of blobs to consider
    
    nearest = blobtree.find_n(loc, num_nearest)
    if nearest:
        return nearest[0][1]
    
    return -1

def make_blob_object(context, index, loc, samples):
    settings = _settings.get(context)
    
    obmat = Matrix.Translation(loc)
    
    mesh = duplimesh.make_dupli_mesh(_blob_object_name, obmat, samples)
    ob = object_utils.object_data_add(bpy.context, mesh, operator=None).object
    
    # put it in the blob group
    blob_group_assign(context, ob)
    # assign the index for mapping
    ob.meadow.blob_index = index
    
    # objects get put at the cursor location by object_utils
    ob.matrix_world = obmat
    
    blob_apply_settings(ob, settings)

    return ob

def make_blobs(context, gridob, groundob, samples):
    blob_group_clear(context)
    
    blobtree = KDTree(len(gridob.data.vertices))
    for i, v in enumerate(gridob.data.vertices):
        blobtree.insert(v.co, i)
    blobtree.balance()
    
    blob_list = []
    for v in gridob.data.vertices:
        ok, loc, nor = project_on_ground(groundob, v.co)
        blob_list.append((loc, []))
    
    for loc, nor in samples:
        index = assign_blob(blobtree, loc, nor)
        if index >= 0:
            blob_list[index][1].append((loc, nor))
    
    for index, (loc, samples) in enumerate(blob_list):
        make_blob_object(context, index, loc, samples)

#-----------------------------------------------------------------------

from meadow.patch import patch_objects

def setup_blob_duplis(context):
    # build patch map for lookup
    patches = {}
    for ob in patch_objects(context):
        index = ob.meadow.blob_index
        
        if index not in patches:
            patches[index] = []
        patches[index].append(ob)
    
    # now make each blob a duplicator for the patches
    for ob in blob_objects(context):
        index = ob.meadow.blob_index
        
        if index in patches:
            for pob in patches[index]:
                if pob.meadow.use_as_dupli:
                    pob.parent = ob
                    # make sure duplis are placed at the sample locations
                    pob.matrix_world = Matrix.Identity(4)
                else:
                    # move to the blob center
                    pob.matrix_world = ob.matrix_world
            ob.dupli_type = 'FACES'
