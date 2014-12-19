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

import bpy, time, sys
from mathutils import *

from object_physics_meadow import settings as _settings, patch
from object_physics_meadow.util import *
from object_physics_meadow import progress

#-----------------------------------------------------------------------

sim_modifier_types = { 'CLOTH', 'DYNAMIC_PAINT', 'FLUID_SIMULATION', 'PARTICLE_SYSTEM', 'SMOKE', 'SOFT_BODY' }

# yield (modifier, pointcache) tuples of an object's simulations
def object_sims(ob):
    for md in ob.modifiers:
        
        if md.type == 'CLOTH':
            yield (md, md.point_cache)
        
        elif md.type == 'DYNAMIC_PAINT':
            if md.canvas_settings:
                for surf in md.canvas_settings.canvas_surfaces:
                    yield (md, surf,point_cache)

        elif md.type == 'PARTICLE_SYSTEM':
            yield (md, md.particle_system.point_cache)

        elif md.type == 'SMOKE':
            if md.smoke_type == 'DOMAIN':
                yield (md, md.domain_settings.point_cache)

        elif md.type == 'SOFT_BODY':
            yield (md, md.point_cache)

# XXX HACK! depsgraph doesn't work and there is no proper way
# of forcing a cache reset after freeing a bake ...
# this function just attempts to set some variable so the cache is tagged 'outdated'
def object_mod_clear_cache(md):
    if md.type == 'CLOTH':
        md.settings.mass = md.settings.mass
    
    elif md.type == 'DYNAMIC_PAINT':
        if md.canvas_settings:
            for surf in md.canvas_settings.canvas_surfaces:
                surf.use_dissolve = surf.use_dissolve

    elif md.type == 'PARTICLE_SYSTEM':
        md.particle_system.invert_vertex_group_density = md.particle_system.invert_vertex_group_density

    elif md.type == 'SMOKE':
        if md.smoke_type == 'DOMAIN':
            md.domain_settings.strength = md.domain_settings.strength

    elif md.type == 'SOFT_BODY':
        md.settings.mass = md.settings.mass


# stores the enabled state of sim objects to allow toggling for bakes
class BakeSimContext():
    def __enter__(self):
        scene = bpy.context.scene

        # frame is modified during baking
        self.curframe = scene.frame_current
        
        self.mod_toggles = {}
        for ob in scene.objects:
            for md in ob.modifiers:
                if md.type in sim_modifier_types:
                    self.mod_toggles[(ob, md)] = (md.show_viewport, md.show_render)
        
        return self.mod_toggles
    
    def __exit__(self, exc_type, exc_value, traceback):
        scene = bpy.context.scene
        
        for ob in scene.objects:
            for md in ob.modifiers:
                if md.type in sim_modifier_types:
                    if (ob, md) in self.mod_toggles:
                        toggle = self.mod_toggles[(ob, md)]
                        # XXX noop settings still invalidates point caches, avoid that
                        if md.show_viewport != toggle[0]:
                            md.show_viewport = toggle[0]
                        if md.show_render != toggle[1]:
                            md.show_render = toggle[1]

        # restore frame
        scene.frame_set(self.curframe)

def bake_all(context):
    context_override = context.copy() # context override for the 'point_cache' argument
    scene = context.scene
    settings = _settings.get(context)

    patches = patch.patch_objects(context)
    nonpatches = set(scene.objects) - set(patches)
    
    # XXX this could disable necessary external influences,
    # so for now rely on the user to disable unnecessary stuff
    # should not be a big issue in practice ...
    """
    # disable all non-patch objects to avoid possible simulation overhead
    for ob in nonpatches:
        for md in ob.modifiers:
            if md.type in sim_modifier_types:
                md.show_viewport = False
                md.show_render = False
    """
    
    for ob in patches:
        for md, ptcache in object_sims(ob):
            # convenience feature: copy the frame range from the scene to the patch objects
            # the per-cache frame range will probably be dropped anyway at some point
            ptcache.frame_start = scene.frame_start
            ptcache.frame_end = scene.frame_end

            # reset unbaked cache data just to be sure (depsgraph is not reliable enough ...)
            object_mod_clear_cache(md)

    # walk through frames, this creates (unbaked) cache frames
    totframes = scene.frame_end - scene.frame_start + 1 # note: +1 because the end frame is included
    with progress.ProgressContext("Calculate Physics", scene.frame_start, scene.frame_end):
        for cfra in range(scene.frame_start, scene.frame_end+1):
            progress.progress_set(cfra)
            scene.frame_set(cfra)
            scene.update()

    # make cached data "baked" so it doesn't get destroyed
    for ob in patches:
        for md, ptcache in object_sims(ob):
            if not ptcache.is_baked:
                select_single_object(ob)
                context_override["point_cache"] = ptcache
                bpy.ops.ptcache.bake_from_cache(context_override)

def scene_bake_all(context):
    with BakeSimContext():
        bake_all(context)

def free_all(context):
    context_override = context.copy() # context override for the 'point_cache' argument
    patches = patch.patch_objects(context)

    for ob in patches:
        for md, ptcache in object_sims(ob):
            if ptcache.is_baked:
                select_single_object(ob)
                context_override["point_cache"] = ptcache
                bpy.ops.ptcache.free_bake(context_override)
            object_mod_clear_cache(md)

def scene_free_all(context):
    with BakeSimContext():
        free_all(context)
