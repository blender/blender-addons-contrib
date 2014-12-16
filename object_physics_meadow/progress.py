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

show_progress_bar = True
show_stdout = False

_progress_context = None

def _get_time_string(x):
    if x >= 0.0:
        return time.strftime("%H:%M:%S", time.gmtime(x)) + ".%02d" % (int(x * 100.0) % 100)
    else:
        return "??:??:??.??"

class ProgressContext():
    def __init__(self, name, pmin, pmax):
        self.name = name
        self.pmin = pmin
        self.pmax = pmax
        self.tot = pmax - pmin
        self.norm = 1.0 / float(self.tot) if self.tot > 0 else 0.0

        self.pcur = pmin
        self.perc_show = -2.0 # last displayed percentage, init to make sure we show the first time

        self.duration = 0.0
        self.start_time = 0.0

    def __enter__(self):
        global _progress_context, show_progress_bar, show_stdout

        assert(_progress_context is None)
        _progress_context = self
        
        self.start_time = time.time()

        if show_progress_bar:
            wm = bpy.context.window_manager
            # always use 0..100 percentage on the progress counter,
            # it does not display large numbers well
            wm.progress_begin(0, 100)

    def __exit__(self, exc_type, exc_value, traceback):
        global _progress_context, show_progress_bar, show_stdout

        if show_progress_bar:
            wm = bpy.context.window_manager
            wm.progress_end()

        if show_stdout:
            # make a final report
            done = self.pcur - self.pmin
            sys.stdout.write("\r>> {}: {}/{}, {}".format(self.name,
                                                                str(done).rjust(len(str(self.tot))), str(self.tot),
                                                                _get_time_string(self.duration)))
            # clean newline
            sys.stdout.write("\n")
            sys.stdout.flush()

        assert(_progress_context is self)
        _progress_context = None

    def estimate_total_duration(self):
        done = self.pcur - self.pmin
        if done > 0:
            return self.duration * self.tot / done
        else:
            return -1.0

    def set_progress(self, value, message):
        global _progress_context, show_progress_bar, show_stdout

        self.pcur = value
        done = value - self.pmin
        perc = 100.0 * done * self.norm

        # only write to progress indicator or stdout if the percentage actually changed
        # avoids overhead for very frequent updates
        if perc > self.perc_show + 1.0:
            self.perc_show = perc
            perc = min(max(perc, 0), 100)

            self.duration = time.time() - self.start_time

            if show_progress_bar:
                wm = bpy.context.window_manager
                wm.progress_update(perc)

            if show_stdout:
                bar = 50
                filled = int(bar * done * self.norm)

                eta = self.estimate_total_duration()

                sys.stdout.write("\r>> {}: {}/{} [{}{}] {}/{} | {}".format(self.name,
                                                                           str(done).rjust(len(str(self.tot))), str(self.tot),
                                                                           '.' * filled, ' ' * (bar - filled),
                                                                           _get_time_string(self.duration), _get_time_string(eta),
                                                                           message))
                sys.stdout.flush()

def progress_set(value, message=""):
    global _progress_context
    
    if not _progress_context:
        return
    _progress_context.set_progress(value, message)

def progress_add(value, message=""):
    global _progress_context

    if not _progress_context:
        return
    _progress_context.set_progress(_progress_context.pcur + value, message)
