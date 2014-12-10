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

def tri_signed_area(v1, v2, v3, i, j):
    return 0.5 * ((v1[i] - v2[i]) * (v2[j] - v3[j]) + (v1[j] - v2[j]) * (v3[i] - v2[i]))

# get the 2 dominant axis values, 0==X, 1==Y, 2==Z
def axis_dominant(axis):
    xn = fabs(axis[0])
    yn = fabs(axis[1])
    zn = fabs(axis[2])
    if zn >= xn and zn >= yn:
        return 0, 1
    elif yn >= xn and yn >= zn:
        return 0, 2
    else:
        return 1, 2

def barycentric_weights(v1, v2, v3, co, n):
    i, j = axis_dominant(n)
    
    w = (tri_signed_area(v2, v3, co, i, j),
         tri_signed_area(v3, v1, co, i, j),
         tri_signed_area(v1, v2, co, i, j))
    wtot = w[0] + w[1] + w[2]
    
    if fabs(wtot) > sys.float_info.epsilon:
        inv_w = 1.0 / wtot
        return True, tuple(x*inv_w for x in w)
    else:
        return False, tuple(1.0/3.0 for x in w)

def interp_weights_face(verts, co):
    w = (0.0, 0.0, 0.0, 0.0)
    
    # OpenGL seems to split this way, so we do too
    if len(verts) > 3:
        n = (verts[0] - verts[2]).cross(verts[1] - verts[3])
        
        ok, w3 = barycentric_weights(verts[0], verts[1], verts[3], co, n)
        w = (w3[0], w3[1], 0.0, w3[2])
        idx = (0, 1, 3)
        
        if not ok or w[0] < 0.0:
            # if w[1] is negative, co is on the other side of the v1-v3 edge,
            # so we interpolate using the other triangle
            ok, w3 = barycentric_weights(verts[1], verts[2], verts[3], co, n)
            w = (0.0, w3[0], w3[1], w3[2])
            idx = (1, 2, 3)
        
    else:
        n = (verts[0] - verts[2]).cross(verts[1] - verts[2])
        
        ok, w3 = barycentric_weights(verts[0], verts[1], verts[2], co, n)
        w = (w3[0], w3[1], w3[2], 0.0)
        idx = (0, 1, 2)
    
    return w, idx


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
