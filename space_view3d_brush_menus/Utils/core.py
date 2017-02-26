import bpy
import time
import sys
import os
import re

object_mode = 'OBJECT'
edit = 'EDIT'
sculpt = 'SCULPT'
vertex_paint = 'VERTEX_PAINT'
weight_paint = 'WEIGHT_PAINT'
texture_paint = 'TEXTURE_PAINT'
particle_edit = 'PARTICLE_EDIT'
pose = 'POSE'

a_props = []


class Menu():

    def __init__(self, menu):
        self.layout = menu.layout
        self.items = {}
        self.current_item = None

    def add_item(self, ui_type="row", parent=None, **kwargs):
        # set the parent layout
        if parent:
            layout = parent
        else:
            layout = self.layout

        # create and return a ui layout
        if ui_type == "row":
            self.current_item = self.items[len(self.items) + 1] = layout.row(**kwargs)

            return self.current_item

        elif ui_type == "column":
            self.current_item = self.items[len(self.items) + 1] = layout.column(**kwargs)

            return self.current_item

        elif ui_type == "column_flow":
            self.current_item = self.items[len(self.items) + 1] = layout.column_flow(**kwargs)

            return self.current_item

        elif ui_type == "box":
            self.current_item = self.items[len(self.items) + 1] = layout.box(**kwargs)

            return self.current_item

        elif ui_type == "split":
            self.current_item = self.items[len(self.items) + 1] = layout.split(**kwargs)

            return self.current_item

        else:
            print("Unknown Type")


def get_mode():
    return bpy.context.object.mode


def menuprop(item, name, value, data_path, icon='NONE',
             disable=False, disable_icon=None,
             custom_disable_exp=None,
             method=None, path=False):

    # disable the ui
    if disable:
        disabled = False

        # used if you need a custom expression to disable the ui
        if custom_disable_exp:
            if custom_disable_exp[0] == custom_disable_exp[1]:
                item.enabled = False
                disabled = True

        # check if the ui should be disabled for numbers
        elif isinstance(eval("bpy.context.{}".format(data_path)), float):
            if round(eval("bpy.context.{}".format(data_path)), 2) == value:
                item.enabled = False
                disabled = True

        # check if the ui should be disabled for anything else
        else:
            if eval("bpy.context.{}".format(data_path)) == value:
                item.enabled = False
                disabled = True

        # change the icon to the disable_icon if the ui has been disabled
        if disable_icon and disabled:
            icon = disable_icon

    # creates the menu item
    prop = item.operator("wm.context_set_value", text=name, icon=icon)

    # sets what the menu item changes
    if path:
        prop.value = value
        value = eval(value)

    elif type(value) == str:
        prop.value = "'{}'".format(value)

    else:
        prop.value = '{}'.format(value)

    # sets the path to what is changed
    prop.data_path = data_path


def set_prop(prop_type, path, **kwargs):
    kwstring = ""

    # turn **kwargs into a string that can be used with exec
    for k, v in kwargs.items():
        if type(v) is str:
            v = '"{}"'.format(v)

        kwstring += "{0}={1}, ".format(k, v)

    kwstring = kwstring[:-2]

    # create the property
    exec("{0} = bpy.props.{1}({2})".format(path, prop_type, kwstring))

    # add the path to a list of property paths
    a_props.append(path)

    return eval(path)


def del_props():
    for prop in a_props:
        exec("del {}".format(prop))

    a_props.clear()

