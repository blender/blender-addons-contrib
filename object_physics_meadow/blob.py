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
from itertools import accumulate
import random

from object_physics_meadow import settings as _settings
from object_physics_meadow import duplimesh
from object_physics_meadow.duplimesh import project_on_ground
from object_physics_meadow.util import *

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
    
    if not blob_group:
        return
    
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
    pass # TODO

#-----------------------------------------------------------------------

# 8-class qualitative Brewer color scheme for high-contrast colors
# http://colorbrewer2.org/
color_schemes = [
    (228, 26, 28),
    (55, 126, 184),
    (77, 175, 74),
    (152, 78, 163),
    (255, 127, 0),
    (255, 255, 51),
    (166, 86, 40),
    (247, 129, 191),
    ]

def select_color(index):
    base = color_schemes[hash(str(index)) % len(color_schemes)]
    return (base[0]/255.0, base[1]/255.0, base[2]/255.0, 1.0)

def get_blob_material(context):
    materials = context.blend_data.materials
    if _blob_object_name in materials:
        return materials[_blob_object_name]
    
    # setup new blob material
    ma = materials.new(_blob_object_name)
    ma.use_object_color = True
    # make the material stand out a bit more using emission
    ma.emit = 1.0
    return ma

# assign sample to a blob, based on distance weighting
def assign_blob(blobtree, loc, nor):
    num_nearest = 4 # number of blobs to consider
    
    nearest = blobtree.find_n(loc, num_nearest)
    
    totn = len(nearest)
    if totn == 0:
        return -1
    if totn == 1:
        return nearest[0][1]
    totdist = fsum(dist for co, index, dist in nearest)
    if totdist == 0.0:
        return -1
    
    norm = 1.0 / (float(totn-1) * totdist)
    accum = list(accumulate(((totdist - dist) * norm) ** 8 for co, index, dist in nearest))
    
    u = random.uniform(0.0, accum[-1])
    for a, (co, index, dist) in zip(accum, nearest):
        if u < a:
            return index
    return -1

def make_blob_object(context, index, loc, samples, display_radius):
    settings = _settings.get(context)
    
    obmat = Matrix.Translation(loc)
    
    mesh = duplimesh.make_dupli_mesh(_blob_object_name, obmat, samples, display_radius)
    mesh.materials.append(get_blob_material(context))
    
    ob = object_utils.object_data_add(bpy.context, mesh, operator=None).object
    # assign the index for mapping
    ob.meadow.blob_index = index
    # objects get put at the cursor location by object_utils
    ob.matrix_world = obmat
    
    blob_apply_settings(ob, settings)
    
    # assign color and material settings
    ob.color = select_color(index)
    ob.show_wire_color = True # XXX this is debatable, could make it an option
    
    return ob

class Blob():
    def __init__(self, loc, nor, face_index):
        self.loc = loc
        self.nor = nor
        self.face_index = face_index
        self.samples = []

blobs = []

def make_blobs(context, gridob, groundob, samples, display_radius):
    global blobs
    
    blob_group_clear(context)
    blobs = []
    
    blobtree = KDTree(len(gridob.data.vertices))
    for i, v in enumerate(gridob.data.vertices):
        # note: only using 2D coordinates, otherwise weights get distorted by z offset
        blobtree.insert((v.co[0], v.co[1], 0.0), i)
    blobtree.balance()
    
    for v in gridob.data.vertices:
        ok, loc, nor, face_index = project_on_ground(groundob, v.co)
        blobs.append(Blob(loc, nor, face_index) if ok else None)
    
    for loc, nor, face_index in samples:
        # note: use only 2D coordinates for weighting, z component should be 0
        index = assign_blob(blobtree, (loc[0], loc[1], 0.0), nor)
        if index >= 0:
            blob = blobs[index]
            if blob:
                blob.samples.append((loc, nor, face_index))
    
    # preliminary display object
    # XXX this could be removed eventually, but it's helpful as visual feedback to the user
    # before creating the actual duplicator blob meshes
    for index, blob in enumerate(blobs):
        if blob:
            samples = [(loc, nor) for loc, nor, _ in blob.samples]
            ob = make_blob_object(context, index, blob.loc, samples, display_radius)
            # put it in the blob group
            blob_group_assign(context, ob)

#-----------------------------------------------------------------------

from object_physics_meadow.patch import patch_objects, patch_group_assign

# select one patch object for each sample based on vertex groups
def assign_sample_patches(vgroups, blob):
    vgroup_samples = { name : [] for name in vgroups }
    
    for loc, nor, face_index in blob.samples:
        # XXX testing
        vgroup_samples[vgroups[-1]].append((loc, nor))
    
    return vgroup_samples

def setup_blob_duplis(context, display_radius):
    global blobs
    
    patches = [ob for ob in patch_objects(context) if blobs[ob.meadow.blob_index] is not None]
    
    vgroups = [""] + list(set(ob.meadow.density_vgroup_name for ob in patches))
    for blob_index, blob in enumerate(blobs):
        if blob is None:
            continue
        
        vgroup_samples = assign_sample_patches(vgroups, blob)
        
        for ob in patches:
            if ob.meadow.blob_index != blob_index:
                continue
            
            samples = vgroup_samples.get(ob.meadow.density_vgroup_name, [])
            if not samples:
                continue
            
            if ob.meadow.use_as_dupli:
                # make a duplicator for the patch object
                dob = make_blob_object(context, blob_index, blob.loc, samples, display_radius)
                # put the duplicator in the patch group,
                # so it gets removed together with patch copies
                patch_group_assign(context, dob)
                
                dob.dupli_type = 'FACES'
                
                ob.parent = dob
                # make sure duplis are placed at the sample locations
                if ob.meadow.use_centered:
                    # XXX centering is needed for particle instance modifier (this might be a bug!)
                    ob.matrix_world = Matrix.Identity(4)
                else:
                    ob.matrix_world = dob.matrix_world
            else:
                # move to the blob center
                ob.matrix_world = dob.matrix_world
