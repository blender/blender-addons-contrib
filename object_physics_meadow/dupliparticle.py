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
from mathutils import *

from object_physics_meadow.pointcache import OCacheFrame, ParticleTimes, BoidData

def write_cache(cachedir, filename, locations):
    totpoint = len(locations)
    indices = [i for i in range(totpoint)]
    velocities = [(0.0, 0.0, 0.0) for i in range(totpoint)]
    q = Quaternion()
    q.identity()
    rotations = [q[:] for i in range(totpoint)]
    angvels = [(0.0, 0.0, 0.0) for i in range(totpoint)]
    sizes = [1.0 for i in range(totpoint)]
    times = [ParticleTimes(1.0, 1000000.0, 1000001.0) for i in range(totpoint)]
    boids = [BoidData(1.0, (0.0, 0.0, 0.0), 0, 0) for i in range(totpoint)]
    
    cache = OCacheFrame(filename, 'PARTICLES', totpoint)
    cache.set_data('INDEX', indices)
    cache.set_data('LOCATION', locations)
    cache.set_data('VELOCITY', velocities)
    cache.set_data('ROTATION', rotations)
    cache.set_data('AVELOCITY', angvels)
    cache.set_data('SIZE', sizes)
    cache.set_data('TIMES', times)
    cache.set_data('BOIDS', boids)
    
    cache.write(cachedir)

#def create_particle_duplis(pset):
#    
