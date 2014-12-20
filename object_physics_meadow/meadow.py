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
from math import *
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

# estimate an upper bound on sample number based on optimal circle packing
def estimate_max_samples(context, groundob, precision=3):
    radius = groundob.meadow.sample_distance
    area_circle = pi * radius*radius
    
    mat = groundob.matrix_world
    bbmin = mat * Vector(tuple(min(p[i] for p in groundob.bound_box) for i in range(3)))
    bbmax = mat * Vector(tuple(max(p[i] for p in groundob.bound_box) for i in range(3)))
    area_bounds = (bbmax[0] - bbmin[0]) * (bbmax[1] - bbmin[1])
    # optimal circle packing area ratio is pi/(2*sqrt(3)) ~= 0.9069
    # http://en.wikipedia.org/wiki/Circle_packing
    area_max = area_bounds * pi / (2.0*sqrt(3.0))

    num = area_max / area_circle
    # round to precision
    num = int(round_sigfigs(num + 0.5, precision))

    groundob.meadow.max_samples = num

def make_samples(context, gridob, groundob):
    settings = _settings.get(context)
    
    mat = groundob.matrix_world
    bbmin = mat * Vector(tuple(min(p[i] for p in groundob.bound_box) for i in range(3)))
    bbmax = mat * Vector(tuple(max(p[i] for p in groundob.bound_box) for i in range(3)))
    
    # get a sample generator implementation
    #gen = best_candidate_gen(groundob.meadow.sample_distance, bbmin[0], bbmax[0], bbmin[1], bbmax[1])
    gen = hierarchical_dart_throw_gen(groundob.meadow.sample_distance, groundob.meadow.sampling_levels, bbmin[0], bbmax[0], bbmin[1], bbmax[1])
    
    loc2D = [p[0:2] for p in gen(groundob.meadow.seed, groundob.meadow.max_samples)]
    
    return loc2D

### Duplicators for later instancing ###
def make_blobs(context, gridob, groundob):
    # patches are linked to current blobs, clear to avoid confusing reset
    patch.patch_group_clear(context)
    
    if use_profiling:
        prof = cProfile.Profile()
        prof.enable()
    
    samples2D = make_samples(context, gridob, groundob)
    blob.make_blobs(context, gridob, groundob, samples2D, groundob.meadow.sample_distance)

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
    # XXX use a tiny radius here to hide duplicator faces in the viewport as much as possible
    # this is not ideal, but we can't easily separate duplicator visibility and dupli visibility:
    # hiding the duplicator would also hide the duplis!
    blob.setup_blob_duplis(context, groundob, 0.0001)

    if use_profiling:
        prof.disable()

        s = io.StringIO()
        ps = pstats.Stats(prof, stream=s).sort_stats('tottime')
        ps.print_stats()
        print(s.getvalue())
