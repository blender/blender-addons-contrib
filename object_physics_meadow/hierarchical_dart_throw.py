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

import random, time
import bpy
from math import *

from object_physics_meadow.util import *

# Implements Poisson Disk sampling according to
# "Poisson Disk Point Sets by Hierarchical Dart Throwing"
# (White, Cline, Egbert)

class GridCell():
    __slots__ = ('i', 'j', 'k')
    
    def __init__(self, i, j, k):
        self.i = i
        self.j = j
        self.k = k

class GridLevel():
    __slots__ = ('index', 'size', 'weight', 'cells', 'debug')
    
    def __init__(self, index, size):
        self.index = index
        self.size = size
        self.weight = size * size # 2D
        self.cells = []
        self.debug = None

    def activate(self, i, j, k):
        cell = GridCell(i, j, k)
        self.cells.append(cell)
        
        x0, x1, y0, y1, _, _ = self.cell_corners(cell)
        if self.debug:
            self.debug.add_grid_cell(x0, x1, y0, y1)
        
        return cell

    def deactivate(self, index):
        c = self.cells[index]
        self.cells[index] = self.cells.pop()
        return c

    def cell_corners(self, cell):
        x0 = float(cell.i)
        y0 = float(cell.j)
        z0 = float(cell.k)
        s = self.size
        return x0 * s, (x0 + 1.0) * s, y0 * s, (y0 + 1.0) * s, z0 * s, (z0 + 1.0) * s

    def sample(self, x0, x1, y0, y1, z0, z1):
        x = random.uniform(x0, x1)
        y = random.uniform(y0, y1)
        z = random.uniform(z0, z1)
        return (x, y, z)

def base_grid_size(radius, gridmin, gridmax):
    width = gridmax[0] - gridmin[0]
    height = gridmax[1] - gridmin[1]
    
    # base cell size
    b0 = max(h / ceil(h * sqrt(2.0) / radius) for h in (width, height))
    
    imin = ifloor(gridmin[0] / b0)
    imax = ifloor(gridmax[0] / b0) + 1
    jmin = ifloor(gridmin[1] / b0)
    jmax = ifloor(gridmax[1] / b0) + 1
    
    return b0, imin, imax, jmin, jmax

def pop_cell(levels):
    totweight = fsum(len(level.cells) * level.weight for level in levels)
    u = random.uniform(0.0, totweight)
    
    for level in levels:
        level_totweight = len(level.cells) * level.weight
        if u < level_totweight:
            cell_index = int(u / level.weight)
            cell = level.deactivate(cell_index)
            return level, cell
        else:
            u -= level_totweight
    return None, None

class PointCell():
    __slots__ = ('points')
    
    def __init__(self):
        self.points = []

class PointGrid():
    def __init__(self, radius, b0, gridmin, gridmax):
        width = gridmax[0] - gridmin[0]
        height = gridmax[1] - gridmin[1]
        
        self.amin = ifloor(gridmin[0] / radius) - 1
        self.bmin = ifloor(gridmin[1] / radius) - 1
        self.na = ifloor(gridmax[0] / radius) + 2 - self.amin
        self.nb = ifloor(gridmax[1] / radius) + 2 - self.bmin
        
        self.size = radius
        self.invsize = 1.0 / radius
        
        # factor to get point grid index from cell grid index
        self.cell_grid_factor = b0 / radius
        
        # note: row-major, so we can address it with cells[i][j]
        self.cells = tuple(tuple(PointCell() for j in range(self.nb)) for i in range(self.na))

    def insert(self, point):
        s = self.invsize
        a = ifloor(point[0] * s) - self.amin
        b = ifloor(point[1] * s) - self.bmin
        cell = self.cells[a][b]
        assert(len(cell.points) <= 3)
        cell.points.append(point)

    def neighbors(self, level, cell_i, cell_j):
        # multiplier between cell grid and base grid
        grid_factor = self.cell_grid_factor / (2 ** level.index)
        
        ca = ifloor(cell_i * grid_factor)
        cb = ifloor(cell_j * grid_factor)
        amin = max(ca - self.amin - 1, 0)
        amax = min(ca - self.amin + 2, self.na)
        bmin = max(cb - self.bmin - 1, 0)
        bmax = min(cb - self.bmin + 2, self.nb)
        for a in range(amin, amax):
            for b in range(bmin, bmax):
                for p in self.cells[a][b].points:
                    yield p

def is_covered(radius2, b0, pgrid, level, cell_i, cell_j, x0, x1, y0, y1):
    cx = 0.5*(x0 + x1)
    cy = 0.5*(y0 + y1)
    for point in pgrid.neighbors(level, cell_i, cell_j):
        # distance test according to section 3.2 of the paper
        dx = fabs(point[0] - cx) + 0.5*b0
        dy = fabs(point[1] - cy) + 0.5*b0
        d2 = dx*dx + dy*dy
        if d2 <= radius2:
            return True
    return False

def test_disk(radius2, pgrid, point, level, cell_i, cell_j):
    for npoint in pgrid.neighbors(level, cell_i, cell_j):
        dx = point[0] - npoint[0]
        dy = point[1] - npoint[1]
        d2 = dx*dx + dy*dy
        if d2 < radius2:
            return False
    return True

def split_cell(radius2, b0, pgrid, child_level, cell, x0, x1, y0, y1, z0, z1):
    s = child_level.size
    ck = cell.k # 2D case
    for cj, cy0, cy1 in zip(range(cell.j*2, cell.j*2 + 2), (y0, y0+s), (y0+s, y1)):
        for ci, cx0, cx1 in zip(range(cell.i*2, cell.i*2 + 2), (x0, x0+s), (x0+s, x1)):
            if not is_covered(radius2, b0, pgrid, child_level, ci, cj, cx0, cx1, cy0, cy1):
                child_cell = child_level.activate(ci, cj, ck)

def hierarchical_dart_throw_gen(radius, max_levels, xmin, xmax, ymin, ymax, debug=None):
    radius2 = radius * radius
    gridmin = (xmin, ymin)
    gridmax = (xmax, ymax)
    b0, imin, imax, jmin, jmax = base_grid_size(radius, gridmin, gridmax)
    ni = imax - imin
    nj = jmax - jmin
    nk = 1 # for 2D grid

    base_level = GridLevel(0, b0)
    levels = [base_level] + [GridLevel(i, base_level.size / (2**i)) for i in range(1, max_levels)]
    epsilon = levels[-1].weight * 0.5
    for level in levels:
        level.debug = debug
    
    for j in range(jmin, jmax):
        for i in range(imin, imax):
            base_level.activate(i, j, 0)
    
    pgrid = PointGrid(radius, b0, gridmin, gridmax)
    
    def gen(seed, num):
        random.seed(seed)
        
        for i in range(num):
            if not any(level.cells for level in levels):
                break
            
            level, cell = pop_cell(levels)
            if level:
                x0, x1, y0, y1, z0, z1 = level.cell_corners(cell)
                
                # test coverage
                if not is_covered(radius2, b0, pgrid, level, cell.i, cell.j, x0, x1, y0, y1):
                    point = level.sample(x0, x1, y0, y1, z0, z1)
                    if test_disk(radius2, pgrid, point, level, cell.i, cell.j):
                        yield point
                        pgrid.insert(point)
                        if debug:
                            debug.add_sample(point)
                    else:
                        if level.index < max_levels - 1:
                            split_cell(radius2, b0, pgrid, levels[level.index+1], cell, x0, x1, y0, y1, z0, z1)
            else:
                break
    
    return gen

#-----------------------------------------------------------------------

class MeshDebug:
    def __init__(self, drawsize = 0.1):
        self.verts = []
        self.edges = []
        self.drawsize = drawsize
    
    def add_grid_cell(self, x0, x1, y0, y1):
        N = len(self.verts)
        self.verts += [(x0, y0, 0.0), (x1, y0, 0.0), (x1, y1, 0.0), (x0, y1, 0.0)]
        self.edges += [(N+0, N+1), (N+1, N+2), (N+2, N+3), (N+3, N+0)]
    
    def add_sample(self, sample):
        #verts += (sample[0], sample[1], 0.0)
        u = self.drawsize * 0.5
        N = len(self.verts)
        self.verts += [(sample[0]-u, sample[1]-u, 0.0), (sample[0]+u, sample[1]+u, 0.0), (sample[0]-u, sample[1]+u, 0.0), (sample[0]+u, sample[1]-u, 0.0)]
        self.edges += [(N+0, N+1), (N+2, N+3)]
    
    def to_object(self, context):
        from bpy_extras import object_utils
        
        name = "PoissonSamplesDebug"
        
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, self.edges, [])
        mesh.update()
        
        ob = object_utils.object_data_add(context, mesh, operator=None).object
        return ob
