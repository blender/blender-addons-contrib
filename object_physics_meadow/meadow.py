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

import bpy, os, cProfile, pstats, io
from mathutils import *

from object_physics_meadow import settings as _settings
from object_physics_meadow import patch, blob
from object_physics_meadow.duplimesh import project_on_ground
#from object_physics_meadow import dupliparticle
#from object_physics_meadow.pointcache import cache_filename
from object_physics_meadow.util import *

from object_physics_meadow.best_candidate import best_candidate_gen
from object_physics_meadow.hierarchical_dart_throw import hierarchical_dart_throw_gen

use_profiling = False

def make_samples(context, gridob, groundob):
    settings = _settings.get(context)
    
    mat = groundob.matrix_world
    gmin = mat * Vector(tuple(min(p[i] for p in groundob.bound_box) for i in range(3)))
    gmax = mat * Vector(tuple(max(p[i] for p in groundob.bound_box) for i in range(3)))
    
    # get a sample generator implementation
    #gen = best_candidate_gen(groundob.meadow.patch_radius, gmin[0], gmax[0], gmin[1], gmax[1])
    gen = hierarchical_dart_throw_gen(groundob.meadow.patch_radius, groundob.meadow.sampling_levels, gmin[0], gmax[0], gmin[1], gmax[1])
    
    loc2D = [p[0:2] for p in gen(groundob.meadow.seed, groundob.meadow.max_patches)]
    
    return loc2D

### Duplicators for later instancing ###
def make_blobs(context, gridob, groundob):
    # patches are linked to current blobs, clear to avoid confusing reset
    patch.patch_group_clear(context)
    
    if use_profiling:
        prof = cProfile.Profile()
        prof.enable()
    
    samples2D = make_samples(context, gridob, groundob)
    blob.make_blobs(context, gridob, groundob, samples2D, groundob.meadow.patch_radius)

    if use_profiling:
        prof.disable()

        s = io.StringIO()
        ps = pstats.Stats(prof, stream=s).sort_stats('tottime')
        ps.print_stats()
        print(s.getvalue())

def delete_blobs(context, groundob):
    if groundob:
        blob.object_free_blob_data(groundob)

    patch.patch_group_clear(context)
    blob.blob_group_clear(context)

### Patch copies for simulation ###
def make_patches(context, gridob, groundob):
    scene = context.scene

    if use_profiling:
        prof = cProfile.Profile()
        prof.enable()
    
    template_objects = [ob for ob in scene.objects if ob.meadow.type == 'TEMPLATE']
    patch.make_patches(context, groundob, gridob, template_objects)
    blob.setup_blob_duplis(context, groundob, 0.333 * groundob.meadow.patch_radius)

    if use_profiling:
        prof.disable()

        s = io.StringIO()
        ps = pstats.Stats(prof, stream=s).sort_stats('tottime')
        ps.print_stats()
        print(s.getvalue())
