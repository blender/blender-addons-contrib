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
# Contributed to by: meta-androcto, pitiwazou, chromoly, italic #

import bpy
from math import *
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty, PointerProperty, StringProperty, CollectionProperty
from bpy.types import PropertyGroup

import inspect

from . import pie_modes_menu
from . import pie_views_numpad_menu
from . import pie_sculpt_menu
from . import pie_origin_cursor
from . import pie_manipulator_menu
from . import pie_snap_menu
from . import pie_orientation_menu
from . import pie_shading_menu
from . import pie_pivot_point_menu
from . import pie_proportional_menu
from . import pie_align_menu
from . import pie_delete_menu
from . import pie_apply_transform_menu
from . import pie_select_menu
from . import pie_animation_menu
from . import pie_save_open_menu
from . import pie_editor_switch_menu

bl_info = {
    'name': '3D Viewport Pie Menu',
    'author': 'meta-androcto, pitiwazou',
    'version': (1, 1, 3),
    'blender': (2, 7, 7),
    'location': '',
    'description': 'Pie Menu Activate',
    'warning': '',
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
    "Scripts/3D_interaction/viewport_pies",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    'category': 'User Interface'
    }


sub_modules = [
    pie_modes_menu,
    pie_views_numpad_menu,
    pie_sculpt_menu,
    pie_origin_cursor,
    pie_manipulator_menu,
    pie_snap_menu,
    pie_orientation_menu,
    pie_shading_menu,
    pie_pivot_point_menu,
    pie_proportional_menu,
    pie_align_menu,
    pie_delete_menu,
    pie_apply_transform_menu,
    pie_select_menu,
    pie_animation_menu,
    pie_save_open_menu,
    pie_editor_switch_menu,
    ]


sub_modules.sort(
    key=lambda mod: (mod.bl_info['category'], mod.bl_info['name']))


def _get_pref_class(mod):
    for obj in vars(mod).values():
        if inspect.isclass(obj) and issubclass(obj, bpy.types.PropertyGroup):
            if hasattr(obj, 'bl_idname') and obj.bl_idname == mod.__name__:
                return obj


def get_addon_preferences(name=''):
    """Acquisition and registration"""
    addons = bpy.context.user_preferences.addons
    if __name__ not in addons:  # wm.read_factory_settings()
        return None
    prefs = addons[__name__].preferences
    if name:
        if not hasattr(prefs, name):
            for mod in sub_modules:
                if mod.__name__.split('.')[-1] == name:
                    cls = _get_pref_class(mod)
                    if cls:
                        prop = bpy.props.PointerProperty(type=cls)
                        setattr(UIToolsPreferences, name, prop)
                        bpy.utils.unregister_class(UIToolsPreferences)
                        bpy.utils.register_class(UIToolsPreferences)
        return getattr(prefs, name, None)
    else:
        return prefs


def register_submodule(mod):
    if not hasattr(mod, '__addon_enabled__'):
        mod.__addon_enabled__ = False
    if not mod.__addon_enabled__:
        mod.register()
        mod.__addon_enabled__ = True


def unregister_submodule(mod):
    if mod.__addon_enabled__:
        mod.unregister()
        mod.__addon_enabled__ = False

        prefs = get_addon_preferences()
        name = mod.__name__.split('.')[-1]
        if hasattr(UIToolsPreferences, name):
            delattr(UIToolsPreferences, name)
            if prefs:
                bpy.utils.unregister_class(UIToolsPreferences)
                bpy.utils.register_class(UIToolsPreferences)
                if name in prefs:
                    del prefs[name]


def test_platform():
    return (platform.platform().split('-')[0].lower()
            not in {'darwin', 'windows'})


class UIToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    align_box_draw = bpy.props.BoolProperty(
        name='Box Draw',
        description='If applied patch: patch/ui_layout_box.patch',
        default=False)

    def draw(self, context):
        layout = self.layout
        """:type: bpy.types.UILayout"""

        for mod in sub_modules:
            mod_name = mod.__name__.split('.')[-1]
            info = mod.bl_info
            column = layout.column(align=self.align_box_draw)
            box = column.box()

            # first stage
            expand = getattr(self, 'show_expanded_' + mod_name)
            icon = 'TRIA_DOWN' if expand else 'TRIA_RIGHT'
            col = box.column()
            row = col.row()
            sub = row.row()
            sub.context_pointer_set('addon_prefs', self)
            sub.alignment = 'LEFT'
            op = sub.operator('wm.context_toggle', text='', icon=icon,
                              emboss=False)
            op.data_path = 'addon_prefs.show_expanded_' + mod_name
            sub.label('{}: {}'.format(info['category'], info['name']))
            sub = row.row()
            sub.alignment = 'RIGHT'
            if info.get('warning'):
                sub.label('', icon='ERROR')
            sub.prop(self, 'use_' + mod_name, text='')

            # The second stage
            if expand:
                if info.get('description'):
                    split = col.row().split(percentage=0.15)
                    split.label('Description:')
                    split.label(info['description'])
                if info.get('location'):
                    split = col.row().split(percentage=0.15)
                    split.label('Location:')
                    split.label(info['location'])
                if info.get('author') and info.get('author') != 'chromoly':
                    split = col.row().split(percentage=0.15)
                    split.label('Author:')
                    split.label(info['author'])
                if info.get('version'):
                    split = col.row().split(percentage=0.15)
                    split.label('Version:')
                    split.label('.'.join(str(x) for x in info['version']),
                                translate=False)
                if info.get('warning'):
                    split = col.row().split(percentage=0.15)
                    split.label('Warning:')
                    split.label('  ' + info['warning'], icon='ERROR')

                tot_row = int(bool(info.get('wiki_url')))
                if tot_row:
                    split = col.row().split(percentage=0.15)
                    split.label(text='Internet:')
                    if info.get('wiki_url'):
                        op = split.operator('wm.url_open',
                                            text='Documentation', icon='HELP')
                        op.url = info.get('wiki_url')
                    for i in range(4 - tot_row):
                        split.separator()

                # Details and settings
                if getattr(self, 'use_' + mod_name):
                    prefs = get_addon_preferences(mod_name)
                    if prefs and hasattr(prefs, 'draw'):
                        if self.align_box_draw:
                            box = column.box()
                        else:
                            box = box.column()

                        prefs.layout = box
                        try:
                            prefs.draw(context)
                        except:
                            traceback.print_exc()
                            box.label(text='Error (see console)', icon='ERROR')
                        del prefs.layout

        row = layout.row()
        sub = row.row()
        sub.alignment = 'RIGHT'
        sub.prop(self, 'align_box_draw')


for mod in sub_modules:
    info = mod.bl_info
    mod_name = mod.__name__.split('.')[-1]

    def gen_update(mod):
        def update(self, context):
            if getattr(self, 'use_' + mod.__name__.split('.')[-1]):
                if not mod.__addon_enabled__:
                    register_submodule(mod)
            else:
                if mod.__addon_enabled__:
                    unregister_submodule(mod)
        return update

    prop = bpy.props.BoolProperty(
        name=info['name'],
        description=info.get('description', ''),
        update=gen_update(mod),
    )
    setattr(UIToolsPreferences, 'use_' + mod_name, prop)
    prop = bpy.props.BoolProperty()
    setattr(UIToolsPreferences, 'show_expanded_' + mod_name, prop)

classes = [
    UIToolsPreferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    prefs = get_addon_preferences()
    for mod in sub_modules:
        if not hasattr(mod, '__addon_enabled__'):
            mod.__addon_enabled__ = False
        name = mod.__name__.split('.')[-1]
        if getattr(prefs, 'use_' + name):
            register_submodule(mod)


def unregister():
    for mod in sub_modules:
        if mod.__addon_enabled__:
            unregister_submodule(mod)

    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
