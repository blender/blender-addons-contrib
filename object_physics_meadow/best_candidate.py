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

from math import *
from mathutils import *
from mathutils.kdtree import KDTree
import random

# simple uniform distribution for testing
def uniform_2D(num, seed, xmin, xmax, ymin, ymax, radius):
    for i in range(num):
        yield (random.uniform(xmin, xmax), random.uniform(ymin, ymax))

# Mitchell's best candidate algorithm
def best_candidate_gen(radius, xmin, xmax, ymin, ymax):
    def best_candidate(k, tree):
        best_dist = radius * 2.0
        best = None
        
        for i in range(k):
            candidate = (random.uniform(xmin, xmax), random.uniform(ymin, ymax))
            
            npoint, nindex, ndist = tree.find((candidate[0], candidate[1], 0.0))
            if not nindex:
                return (random.uniform(xmin, xmax), random.uniform(ymin, ymax))
            
            if ndist > best_dist:
                best_dist = ndist
                best = candidate
        
        return best
    
    num_candidates = 10
    
    def gen(seed, num):
        random.seed(seed)
        
        data = []
        tree = KDTree(0)
        tree.balance()
        for i in range(num):
            best = best_candidate(num_candidates, tree)
            if not best:
                break
            yield best
            
            data.append((best[0], best[1], 0.0))
            tree = KDTree(len(data))
            for i, p in enumerate(data):
                tree.insert(p, i)
            tree.balance()

    return gen
