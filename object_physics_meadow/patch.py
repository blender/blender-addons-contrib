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
from bpy_extras import object_utils

from object_physics_meadow import settings as _settings
from object_physics_meadow.util import *
from object_physics_meadow import progress

#-----------------------------------------------------------------------

def patch_objects(context):
    settings = _settings.get(context)
    patch_group = settings.patch_group(context)
    # ignore objects with invalid blob index
    return [ob for ob in patch_group.objects if ob.meadow.blob_index >= 0]

def patch_group_clear(context):
    settings = _settings.get(context)
    patch_group = settings.patch_group(context)
    
    if patch_group:
        delete_objects(context, patch_group.objects)

def patch_group_assign(context, patchob, test=False):
    settings = _settings.get(context)
    patch_group = settings.patch_group(context)
    
    if test and patchob in patch_group.objects.values():
        return
    
    patch_group.objects.link(patchob)
    # NOTE: unsetting the type is important, otherwise gathering templates
    # a second time will include deleted objects!
    patchob.meadow.type = 'NONE'

def patch_group_remove(context, patchob):
    settings = _settings.get(context)
    patch_group = settings.patch_group(context)
    
    patch_group.objects.unlink(patchob)

#-----------------------------------------------------------------------

# XXX WARNING: using the duplicate operator is _horribly_ slow!
# fortunately we can use a trick and create dupli instances first,
# then use "make duplicates real" once to generate actual object copies
"""
def duplicate_patch_object(context, varob):
    scene = context.scene
    
    scene.objects.active = varob
    for ob in scene.objects:
        ob.select = (ob == varob)
    
    bpy.ops.object.duplicate('EXEC_DEFAULT', mode='INIT')
    
    # find new patch duplicate among selected
    patchob = None
    for ob in scene.objects:
        if ob.select and ob != varob:
            patchob = ob
            break
    return patchob

def make_patch_variant(context, varob, obmat):
    patchob = duplicate_patch_object(context, varob)
    if patchob:
        patchob.matrix_world = obmat

def make_patches(context, patch_mats, variant_objects):
    scene = context.scene
    
    # store active/selected state to restore it afterward
    curact = scene.objects.active
    cursel = { ob : ob.select for ob in scene.objects }
    
    for obmat in patch_mats:
        for varob in variant_objects:
            make_patch_variant(context, varob, obmat)
    
    # restore active/selected state
    scene.objects.active = curact
    for ob in scene.objects:
        ob.select = cursel.get(ob, False)
"""

def make_copies(scene, gridob, childob):
    # setup the template as dupli child of the grid
    childmat = childob.matrix_basis
    childob.parent = gridob
    gridob.dupli_type = 'VERTS'
    
    # select duplicator object
    select_single_object(gridob)
    
    # do it!
    bpy.ops.object.duplicates_make_real(use_base_parent=False, use_hierarchy=False)
    
    # collect new copies
    duplicates = [ob for ob in scene.objects if ob.select and ob != gridob]
    
    # un-parent again
    childob.parent = None
    childob.matrix_basis = childmat
    gridob.dupli_type = 'NONE'
    
    return duplicates

def make_patches(context, groundob, gridob, template_objects):
    scene = context.scene
    gridmat = gridob.matrix_world
    
    patch_group_clear(context)
    
    temp_copies = {}
    for tempob in template_objects:
        # create patch copies
        copies = make_copies(scene, gridob, tempob)
        
        # customize copies
        for ob, (index, vert) in zip(copies, enumerate(gridob.data.vertices)):
            # put it in the patch group
            patch_group_assign(context, ob)
            # assign the index for mapping
            ob.meadow.blob_index = index
            # use ground object as parent to keep the outliner clean
            set_object_parent(ob, groundob)
            # apply layers
            if groundob.meadow.use_layers:
                ob.layers = groundob.meadow.layers

            # apply transform
            vertmat = Matrix.Translation(vert.co)
            duplimat = gridmat * vertmat
            ob.matrix_world = duplimat
            
            # optional visibility override
            if ob.meadow.hide:
                ob.hide = True

            # XXX WARNING: having lots of objects in the scene slows down
            # the make-duplis-real operator to an absolute crawl!!
            # Therefore we unlink all copies here until the copying
            # of other objects is done
            scene.objects.unlink(ob)
        
        temp_copies[tempob] = copies
    
    # copying is done, re-link stuff to the scene
    for tempob, copies in temp_copies.items():
        for ob in copies:
            # construct a unique name (scene.objects.link otherwise can raise an exception)
            ob.name = "{}__{}__".format(tempob.name, str(ob.meadow.blob_index))
            
            scene.objects.link(ob)
    
    # recreate dependencies between patch objects on the copies
    # note: let copying finish first, otherwise might miss dependencies to objects that are copied later
    for copies in temp_copies.values():
        for index, copyob in enumerate(copies):
            for data, prop in object_relations(copyob):
                relob = getattr(data, prop, None)
                relcopies = temp_copies.get(relob, None)
                if relcopies:
                    setattr(data, prop, relcopies[index])
