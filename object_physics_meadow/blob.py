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
from mathutils.interpolate import poly_3d_calc
from itertools import accumulate
import random

from object_physics_meadow import settings as _settings
from object_physics_meadow import duplimesh
from object_physics_meadow.duplimesh import project_on_ground
from object_physics_meadow.util import *

_blob_object_name = "__MeadowBlob__"
_blob_object_parent_name = "__MeadowBlobParent__"

def blob_objects(context):
    settings = _settings.get(context)
    blob_group = settings.blob_group(context)
    # ignore objects with invalid blob index
    return [ob for ob in blob_group.objects if ob.meadow.blob_index >= 0]

def blob_group_clear(context):
    settings = _settings.get(context)
    blob_group = settings.blob_group(context)
    
    if blob_group:
        delete_objects(context, blob_group.objects)

def blob_group_assign(context, blobob, test=False):
    settings = _settings.get(context)
    blob_group = settings.blob_group(context)
    
    if test and blobob in blob_group.objects.values():
        return
    
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

def get_blob_parent(context, obmat):
    ob = context.blend_data.objects.get(_blob_object_parent_name, None)
    if not ob:
        ob = object_utils.object_data_add(bpy.context, None, name=_blob_object_parent_name).object
    # put it in the blob group
    blob_group_assign(context, ob, test=True)
    
    ob.matrix_world = obmat
    
    return ob

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
    def __init__(self, loc, nor, poly_index):
        self.loc = loc
        self.nor = nor
        self.poly_index = poly_index
        self.samples = []
    
    def add_sample(self, loc, nor, poly, verts, weights):
        self.samples.append((loc, nor, poly, verts, weights))
    
    # note: Vector instances cannot be pickled directly,
    # therefore define own pickle methods here
    def __getstate__(self):
        return self.loc[:], self.nor[:], self.poly_index, [(sloc[:], snor[:], spoly, sverts, sweights) for sloc, snor, spoly, sverts, sweights in self.samples]
    
    def __setstate__(self, state):
        self.loc = Vector(state[0])
        self.nor = Vector(state[1])
        self.poly_index = state[2]
        self.samples = [(Vector(sloc), Vector(snor), spoly, sverts, sweights) for sloc, snor, spoly, sverts, sweights in state[3]]

# store blobs list in ID datablock as customdata
def blobs_to_customprops(data, blobs):
    import pickle, array
    B = pickle.dumps(blobs)
    pad = (4 - len(B)) % 4
    A = array.array('i', B + b'\x00' * pad)
    data['blobs'] = A.tolist()

# load blobs list from ID datablock customdata
def blobs_from_customprops(data):
    import pickle, array
    A = array.array('i', data['blobs'])
    blobs = pickle.loads(A.tobytes())
    return blobs


def make_blobs(context, gridob, groundob, samples2D, display_radius):
    blob_group_clear(context)
    blobs = []
    
    blobtree = KDTree(len(gridob.data.vertices))
    for i, v in enumerate(gridob.data.vertices):
        co = gridob.matrix_world * v.co
        # note: only using 2D coordinates, otherwise weights get distorted by z offset
        blobtree.insert((co[0], co[1], 0.0), i)
    blobtree.balance()
    
    for v in gridob.data.vertices:
        co = gridob.matrix_world * v.co
        ok, loc, nor, poly_index = project_on_ground(groundob, co)
        blobs.append(Blob(loc, nor, poly_index) if ok else None)
    
    mpolys = groundob.data.polygons
    mverts = groundob.data.vertices
    for xy in samples2D:
        # note: use only 2D coordinates for weighting, z component should be 0
        index = assign_blob(blobtree, (xy[0], xy[1], 0.0), nor)
        if index < 0:
            continue
        blob = blobs[index]
        if blob is None:
            continue
        
        # project samples onto the ground object
        ok, sloc, snor, spoly = project_on_ground(groundob, xy[0:2]+(0,))
        if not ok:
            continue
        
        # calculate barycentric vertex weights on the poly
        poly = mpolys[spoly]
        sverts = list(poly.vertices)
        sweights = poly_3d_calc(tuple(mverts[i].co for i in sverts), sloc)

        blob.add_sample(sloc, snor, spoly, sverts, sweights)

    # common parent empty for blobs
    blob_parent = get_blob_parent(context, groundob.matrix_world)
    
    # preliminary display object
    # XXX this could be removed eventually, but it's helpful as visual feedback to the user
    # before creating the actual duplicator blob meshes
    for index, blob in enumerate(blobs):
        if blob:
            samples = [(loc, nor) for loc, nor, _, _, _ in blob.samples]
            ob = make_blob_object(context, index, blob.loc, samples, display_radius)
            # put it in the blob group
            blob_group_assign(context, ob)
            # use parent to keep the outliner clean
            set_object_parent(ob, blob_parent)
    
    blobs_to_customprops(groundob.meadow, blobs)

#-----------------------------------------------------------------------

from object_physics_meadow.patch import patch_objects, patch_group_assign

# select one patch object for each sample based on vertex groups
def assign_sample_patches(groundob, blob, patches):
    vgroups = groundob.vertex_groups
    mverts = groundob.data.vertices
    
    used_vgroup_names = set(ob.meadow.density_vgroup_name for ob in patches)
    
    vgroup_samples = { vg.name : [] for vg in vgroups }
    vgroup_samples[""] = [] # samples for unassigned patches
    for sloc, snor, spoly, sverts, sweights in blob.samples:
        verts = [mverts[i] for i in sverts]
        # accumulate weights for each vertex group by interpolating the poly
        weights = [ 0.0 for vg in vgroups ]
        for v, fac in zip(verts, sweights):
            for vg in v.groups:
                weights[vg.group] += vg.weight * fac
        
        def select_vgroup():
            if not weights:
                return None
            used_vgroups = [(vg, w) for vg, w in zip(vgroups, weights) if vg.name in used_vgroup_names]
            
            totweight = sum(w for vg, w in used_vgroups)
            # using 1.0 as the minimum total weight means we select
            # the default "non-group" in uncovered areas:
            # there is a 1.0-totweight chance of selecting no vgroup at all
            u = random.uniform(0.0, max(totweight, 1.0))
            for vg, w in used_vgroups:
                if u < w:
                    return vg
                u -= w
            return None
        
        vg = select_vgroup()
        if vg:
            vgroup_samples[vg.name].append((sloc, snor))
        else:
            vgroup_samples[""].append((sloc, snor))
    
    return vgroup_samples

def setup_blob_duplis(context, groundob, display_radius):
    blobs = blobs_from_customprops(groundob.meadow)

    patches = [ob for ob in patch_objects(context) if blobs[ob.meadow.blob_index] is not None]
    
    # common parent empty for blobs
    blob_parent = get_blob_parent(context, groundob.matrix_world)
    
    del_patches = set() # patches to delete, keep this separate for iterator validity
    for blob_index, blob in enumerate(blobs):
        if blob is None:
            continue
        
        vgroup_samples = assign_sample_patches(groundob, blob, patches)
        
        for ob in patches:
            if ob.meadow.blob_index != blob_index:
                continue
            
            samples = vgroup_samples.get(ob.meadow.density_vgroup_name, [])
            if not samples:
                del_patches.add(ob)
                continue
            
            if ob.meadow.use_as_dupli:
                # make a duplicator for the patch object
                dob = make_blob_object(context, blob_index, blob.loc, samples, display_radius)
                # put the duplicator in the patch group,
                # so it gets removed together with patch copies
                patch_group_assign(context, dob)
                # use parent to keep the outliner clean
                set_object_parent(dob, blob_parent)
                set_object_parent(ob, dob)
                
                dob.dupli_type = 'FACES'
                
                # make sure duplis are placed at the sample locations
                if ob.meadow.use_centered:
                    # XXX centering is needed for particle instance modifier (this might be a bug!)
                    ob.matrix_world = Matrix.Identity(4)
                else:
                    ob.matrix_world = dob.matrix_world
            else:
                # use parent to keep the outliner clean
                set_object_parent(ob, blob_parent)
                # move to the blob center
                ob.matrix_world = Matrix.Translation(blob.loc)
        
    # delete unused patch objects
    delete_objects(context, del_patches)
