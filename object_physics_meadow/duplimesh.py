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

def project_on_ground(groundob, co):
    groundmat4 = groundob.matrix_world
    groundmat3 = groundmat4.to_3x3()
    
    zmin = min(p[2] for p in groundob.bound_box) - 1.0
    zmax = max(p[2] for p in groundob.bound_box) + 1.0
    
    ray_start = (co[0], co[1], zmax)
    ray_end = (co[0], co[1], zmin)
    
    hit, nor, index = groundob.ray_cast(ray_start, ray_end)
    if index >= 0:
        return True, groundmat4 * hit, groundmat3 * nor
    else:
        return False, co, (0.0, 0.0, 1.0)


def make_dupli_mesh(name, obmat, samples, scale):
    tot = len(samples)
    scalemat = Matrix()
    scalemat[0][0] = scalemat[1][1] = scalemat[2][2] = scale
    scalemat[3][3] = 1.0
    
    invobmat = obmat.inverted()
    
    def verts():
        for loc, nor in samples:
            mat = Matrix.Translation(loc) * invobmat * scalemat
            yield ( mat * Vector((-0.86603, -0.5, 0.0)) )[:]
            yield ( mat * Vector(( 0.86603, -0.5, 0.0)) )[:]
            yield ( mat * Vector(( 0.0,      1.0, 0.0)) )[:]
    
    def edges():
        for i in range(tot):
            yield (i*3 + 0, i*3 + 1)
            yield (i*3 + 1, i*3 + 2)
            yield (i*3 + 2, i*3 + 0)
    
    def faces():
        for i in range(tot):
            yield (i*3 + 0, i*3 + 1, i*3 + 2)
    
    mesh = bpy.data.meshes.new(name)
    # XXX edges somehow are broken, but can be calculated automatically
    #mesh.from_pydata([v for v in verts()], [e for e in edges()], [f for f in faces()])
    mesh.from_pydata([v for v in verts()], [], [f for f in faces()])
    mesh.update()
    return mesh
