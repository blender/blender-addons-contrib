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

import bpy, os
from mathutils import *

from meadow import settings as _settings
from meadow import patch, blob
from meadow.duplimesh import project_on_ground
#from meadow import dupliparticle
#from meadow.pointcache import cache_filename

from meadow.best_candidate import best_candidate_gen
from meadow.hierarchical_dart_throw import hierarchical_dart_throw_gen, MeshDebug

def make_samples(context, groundob):
    settings = _settings.get(context)
    
    xmin = min(p[0] for p in groundob.bound_box)
    xmax = max(p[0] for p in groundob.bound_box)
    ymin = min(p[1] for p in groundob.bound_box)
    ymax = max(p[1] for p in groundob.bound_box)
    zmin = min(p[2] for p in groundob.bound_box)
    zmax = max(p[2] for p in groundob.bound_box)
    
    debug = MeshDebug(drawsize=0.1)
    # get a sample generator implementation
    #gen = best_candidate_gen(settings.patch_radius, xmin, xmax, ymin, ymax)
    gen = hierarchical_dart_throw_gen(settings.patch_radius, 4, xmin, xmax, ymin, ymax, debug)
    
    loc2D = [(p[0], p[1]) for p in gen(settings.seed, settings.max_patches)]
    debug.to_object(context)
    
    # project samples onto the ground object
    samples = []
    for loc in loc2D:
        ok, loc, nor = project_on_ground(groundob, loc)
        if ok:
            samples.append((loc, nor))
    
    return samples

def generate_meadow(context, gridob, groundob):
    settings = _settings.get(context)
    scene = context.scene
    template_objects = [ob for ob in scene.objects if ob.meadow.type == 'TEMPLATE']
    
    ### Patch copies for simulation ###
    
    patch.make_patches(context, gridob, template_objects)
    
    ### Samples ###
    
    samples = make_samples(context, groundob)
    
    ### Duplicators for instancing ###
    
    blob.make_blobs(context, gridob, groundob, samples)

    blob.setup_blob_duplis(context)
