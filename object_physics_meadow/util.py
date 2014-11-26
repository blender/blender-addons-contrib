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

import bpy, time

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

class Profiling():
    def __init__(self, name):
        self.name = name
        self.total = 0.0
        self.count = 0
        self.last = 0.0
    
    def reset(self):
        self.total = 0.0
        self.count = 0
        self.last = 0.0
    
    @property
    def average(self):
        return self.total / float(self.count) if self.count > 0 else 0.0
    
    def __enter__(self):
        self.start_time = time.time()
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.last = time.time() - self.start_time
        self.total += self.last
        self.count += 1
        
    def as_string(self, show_total=True, show_count=True, show_average=True, show_last=False):
        precision = 6
        factor = 10 ** precision
        time_str = lambda t: "{}:{}".format(time.strftime("%M:%S", time.gmtime(t)), str(int(t * float(factor)) % factor).rjust(precision, '0'))
        result = "{}:\n".format(self.name)
        if show_total:
            result += "\ttotal = {}\n".format(time_str(self.total))
        if show_count:
            result += "\tcount = {}\n".format(self.count)
        if show_average:
            result += "\taverage = {}\n".format(time_str(self.average))
        if show_last:
            result += "\tlast = {}\n".format(time_str(self.last))
        return result
