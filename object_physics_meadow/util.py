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
from math import *

def ifloor(x):
    return int(x) if x >= 0.0 else int(x) - 1

class ObjectSelection():
    def __enter__(self):
        scene = bpy.context.scene
        # store active/selected state to restore it after operator execution
        self.curact = scene.objects.active
        self.cursel = { ob : ob.select for ob in scene.objects }
        
        return (self.curact, self.cursel)
    
    def __exit__(self, exc_type, exc_value, traceback):
        scene = bpy.context.scene
        # restore active/selected state
        scene.objects.active = self.curact
        for ob in scene.objects:
            ob.select = self.cursel.get(ob, False)

def select_single_object(ob):
    scene = bpy.context.scene
    
    scene.objects.active = ob
    for tob in scene.objects:
        tob.select = (tob == ob)

#-----------------------------------------------------------------------

# supported relation types between patch objects
# yields (data, property) pairs to object pointer properties
def object_relations(ob):
    for md in ob.modifiers:
        if md.type == 'PARTICLE_INSTANCE':
            yield md, "object"

def delete_objects(context, objects):
    scene = context.scene
    
    obset = set(objects)
    
    while obset:
        ob = obset.pop()
        
        #remove from groups
        for g in bpy.data.groups:
            if ob in g.objects.values():
                g.objects.unlink(ob)
        
        # unlink from other objects
        for relob in bpy.data.objects:
            for data, prop in object_relations(relob):
                if getattr(data, prop, None) == ob:
                    setattr(data, prop, None)
        
        # unlink from scenes
        for scene in bpy.data.scenes:
            if ob in scene.objects.values():
                scene.objects.unlink(ob)
        
        # note: this can fail if something still references the object
        # we try to unlink own pointers above, but users might add own
        if ob.users == 0:
            bpy.data.objects.remove(ob)
        else:
            print("Warning: could not remove object %r" % ob.name)

#-----------------------------------------------------------------------

# set the object parent without modifying world space transform
def set_object_parent(ob, parent):
    mat = ob.matrix_world
    ob.parent = parent
    ob.matrix_world = mat
