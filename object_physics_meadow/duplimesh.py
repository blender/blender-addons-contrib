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

import bpy, sys
from math import *
from mathutils import *

def project_on_ground(groundob, co):
    groundmat4 = groundob.matrix_world
    inv_groundmat4 = groundmat4.inverted()
    groundmat3 = groundmat4.to_3x3()
    
    zmin = min(p[2] for p in groundob.bound_box) - 1.0
    zmax = max(p[2] for p in groundob.bound_box) + 1.0
    
    obco = inv_groundmat4 * Vector(co[0:3] + (1.0,)) # co expected to be in world space
    ray_start = (obco[0], obco[1], zmax)
    ray_end = (obco[0], obco[1], zmin)
    
    hit, nor, index = groundob.ray_cast(ray_start, ray_end)
    if index >= 0:
        return True, groundmat4 * hit, groundmat3 * nor, index
    else:
        return False, co, (0.0, 0.0, 1.0), -1


def make_dupli_mesh(name, obmat, samples, scale):
    scalemat = Matrix()
    scalemat[0][0] = scalemat[1][1] = scalemat[2][2] = scale
    scalemat[3][3] = 1.0
    
    invobmat = obmat.inverted()
    
    def make_verts():
        verts = []
        for i, (loc, rot) in enumerate(samples):
            mat = Matrix.Translation(loc) * invobmat * rot * scalemat
            verts.append(mat * Vector((-0.86603, -0.5, 0.0)))
            verts.append(mat * Vector(( 0.86603, -0.5, 0.0)))
            verts.append(mat * Vector(( 0.0,      1.0, 0.0)))
        return i, verts
    
    def edges(tot):
        for i in range(tot):
            yield (i*3 + 0, i*3 + 1)
            yield (i*3 + 1, i*3 + 2)
            yield (i*3 + 2, i*3 + 0)
    
    def faces(tot):
        for i in range(tot):
            yield (i*3 + 0, i*3 + 1, i*3 + 2)
    
    tot, verts = make_verts()
    mesh = bpy.data.meshes.new(name)
    # XXX edges somehow are broken, but can be calculated automatically
    #mesh.from_pydata(verts, [e for e in edges(tot)], [f for f in faces(tot)])
    mesh.from_pydata(verts, [], [f for f in faces(tot)])
    mesh.update()
    return mesh
