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

# stores the enabled state of sim objects to allow toggling for bakes
class BakeSimContext():
    def __enter__(self):
        scene = bpy.context.scene
        
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
                        md.show_viewport = toggle[0]
                        md.show_render = toggle[1]

def enable_single_sim_psys(context, sim_ob, sim_psys):
    scene = context.scene
    for ob in scene.objects:
        for md in ob.modifiers:
            if md.type not in sim_modifier_types:
                continue
            
            enable = (md.type == 'PARTICLE_SYSTEM' and md.particle_system == sim_psys)
            
            md.show_viewport = enable
            md.show_render = enable

def bake_psys(context, ob, psys):
    cache = psys.point_cache
    context_override = context.copy()
    context_override["point_cache"] = cache
    
    select_single_object(ob)
    curpsys = ob.particle_systems.active
    ob.particle_systems.active = psys
    
    if cache.is_baked:
        bpy.ops.ptcache.free_bake(context_override)
    
    # make sure only the active psys is enabled
    enable_single_sim_psys(context, ob, psys)
    
    bpy.ops.ptcache.bake(context_override, bake=True)
    
    # restore
    ob.particle_systems.active = curpsys

def count_bakeable(context):
    num = 0
    for ob in patch.patch_objects(context):
        for psys in ob.particle_systems:
            num += 1
    return num

def bake_all(context):
    settings = _settings.get(context)
    wm = context.window_manager
    
    total_time = 0.0
    avg_time = 0.0
    
    total = count_bakeable(context)
    
    with progress.ProgressContext("Bake Blob", 0, total):
        for ob in patch.patch_objects(context):
            for psys in ob.particle_systems:
                progress.progress_add(1)
                bake_psys(context, ob, psys)

def scene_bake_all(context):
    settings = _settings.get(context)
    wm = context.window_manager
    
    # we disable all sim modifiers selectively to make sure only one sim has to be calculated at a time
    with BakeSimContext():
        scene = context.scene
        curframe = scene.frame_current
        
        # XXX have to set this because bake operator only bakes up to the last frame ...
        scene.frame_current = scene.frame_end
        
        bake_all(context)
        
        scene.frame_set(curframe)
