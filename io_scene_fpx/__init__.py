# ##### BEGIN GPL LICENSE BLOCK #####
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

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2013 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


bl_info = {
    'name': "Future Pinball FPx format (.fpm/.fpl/.fpt)",
    'description': "Import Future Pinball Model, Library and Table files",
    'author': "Alexander Nussbaumer",
    'version': (0, 0, 0, '2013-08-24'),
    'blender': (2, 68, 0),
    'location': "File > Import",
    'warning': "",
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/"\
            "Py/Scripts/Import-Export/FuturePinball_FPx",
    'tracker_url': "https://projects.blender.org/tracker/index.php?func=detail&aid=36215",
    'category': "Import-Export",
    }


# To support reload properly, try to access a package var,
# if it's there, reload everything
if 'bpy' in locals():
    import imp
    if 'io_scene_fpx.fpx_ui' in locals():
        imp.reload(io_scene_fpx.fpx_ui)
else:
    from io_scene_fpx.fpx_ui import (
            FpmImportOperator,
            FplImportOperator,
            FptImportOperator,
            )


#import blender stuff
from bpy.utils import (
        register_module,
        unregister_module,
        )
from bpy.types import (
        INFO_MT_file_export,
        INFO_MT_file_import,
        )


###############################################################################
# registration
def register():
    ####################
    # F8 - key
    import imp
    imp.reload(fpx_ui)
    # F8 - key
    ####################

    fpx_ui.register()

    register_module(__name__)
    INFO_MT_file_import.append(FpmImportOperator.menu_func)
    INFO_MT_file_import.append(FplImportOperator.menu_func)
    INFO_MT_file_import.append(FptImportOperator.menu_func)


def unregister():
    fpx_ui.unregister()

    unregister_module(__name__)
    INFO_MT_file_import.remove(FpmImportOperator.menu_func)
    INFO_MT_file_import.remove(FplImportOperator.menu_func)
    INFO_MT_file_import.remove(FptImportOperator.menu_func)


###############################################################################
# global entry point
if (__name__ == "__main__"):
    register()

###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
