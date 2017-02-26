from bpy.props import *
from .Utils.core import *


class DyntopoMenuOperator(bpy.types.Operator):
    bl_label = "Dyntopo Menu Operator"
    bl_idname = "view3d.dyntopo_operator"

    @classmethod
    def poll(self, context):
        if get_mode() == sculpt:
            return True
        else:
            return False

    def modal(self, context, event):
        current_time = time.time()

        # if key has been held for more than 0.3 seconds call the menu
        if event.value == 'RELEASE' and current_time > self.start_time + 0.3:
            bpy.ops.wm.call_menu(name=DynTopoMenu.bl_idname)

            return {'FINISHED'}

        # else toggle manipulator mode on/off
        elif event.value == 'RELEASE' and current_time < self.start_time + 0.3:
            bpy.ops.view3d.dyntopo_warn_operator()

            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.start_time = time.time()
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class DyntopoWarnOperator(bpy.types.Operator):
    bl_label = "Dyntopo Warn Operator"
    bl_idname = "view3d.dyntopo_warn_operator"

    def execute(self, context):
        if not context.object.use_dynamic_topology_sculpting:
            if context.active_object.data.vertex_colors.active:
                bpy.ops.wm.call_menu(name=DynWarnMenu.bl_idname)
            elif context.active_object.data.uv_layers.active:
                bpy.ops.wm.call_menu(name=DynWarnMenu.bl_idname)
            elif context.active_object.data.shape_keys:
                bpy.ops.wm.call_menu(name=DynWarnMenu.bl_idname)
            elif context.active_object.data.has_custom_normals:
                bpy.ops.wm.call_menu(name=DynWarnMenu.bl_idname)
            elif context.active_object.vertex_groups.active:
                bpy.ops.wm.call_menu(name=DynWarnMenu.bl_idname)
            else:
                bpy.ops.sculpt.dynamic_topology_toggle()
        else:
            bpy.ops.sculpt.dynamic_topology_toggle()

        return {'FINISHED'}


class DynTopoMenu(bpy.types.Menu):
    bl_label = "Dyntopo"
    bl_idname = "view3d.dyntopo"

    @classmethod
    def poll(self, context):
        if get_mode() == sculpt:
            return True
        else:
            return False

    def draw(self, context):
        menu = Menu(self)

        if context.object.use_dynamic_topology_sculpting:
            menu.add_item().operator("sculpt.dynamic_topology_toggle", "Disable Dynamic Topology")

            menu.add_item().separator()

            menu.add_item().menu(DynDetailMenu.bl_idname)
            menu.add_item().menu(DetailMethodMenu.bl_idname)

            menu.add_item().separator()

            menu.add_item().operator("sculpt.optimize")
            if bpy.context.tool_settings.sculpt.detail_type_method == 'CONSTANT':
                menu.add_item().operator("sculpt.detail_flood_fill")

            menu.add_item().menu(SymmetrizeMenu.bl_idname)
            menu.add_item().prop(context.tool_settings.sculpt, "use_smooth_shading", toggle=True)

        else:
            menu.add_item().operator("view3d.dyntopo_warn_operator", "Enable Dynamic Topology")


class DynWarnMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "view3d.warn_dyntopo"

    @classmethod
    def poll(self, context):
        if get_mode() == sculpt:
            return True
        else:
            return False

    def draw(self, context):
        menu = Menu(self)

        menu.add_item().label("Warning!", icon='ERROR')
        menu.add_item().separator()
        menu.add_item().label("Vertex Data Detected!", icon='INFO')
        menu.add_item().label("Dyntopo will not preserve vertex colors, UVs, or other custom data")
        menu.add_item().separator()
        menu.add_item().operator("sculpt.dynamic_topology_toggle", "OK")


class DynDetailMenu(bpy.types.Menu):
    bl_label = "Detail Size"
    bl_idname = "view3d.dyn_detail"

    def init(self):
        settings = [["40", 40], ["30", 30], ["20", 20],
                    ["10", 10], ["5", 5], ["1", 1]]

        if bpy.context.tool_settings.sculpt.detail_type_method == 'RELATIVE':
            datapath = "tool_settings.sculpt.detail_size"
            slider_setting = "detail_size"

        else:
            datapath = "tool_settings.sculpt.constant_detail"
            slider_setting = "constant_detail"

        return settings, datapath, slider_setting

    def draw(self, context):
        settings, datapath, slider_setting = self.init()
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(context.tool_settings.sculpt, slider_setting, slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1], datapath,
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class DetailMethodMenu(bpy.types.Menu):
    bl_label = "Detail Method"
    bl_idname = "view3d.detail_method_menu"

    def draw(self, context):
        menu = Menu(self)
        refine_path = "tool_settings.sculpt.detail_refine_method"
        type_path = "tool_settings.sculpt.detail_type_method"

        refine_items = [["Subdivide Edges", 'SUBDIVIDE'],
                        ["Collapse Edges", 'COLLAPSE'],
                        ["Subdivide Collapse", 'SUBDIVIDE_COLLAPSE']]

        type_items = [["Relative Detail", 'RELATIVE'],
                      ["Constant Detail", 'CONSTANT']]

        menu.add_item().label("Refine")
        menu.add_item().separator()

        # add the refine menu items
        for item in refine_items:
            menuprop(menu.add_item(), item[0], item[1], refine_path, disable=True,
                     icon='RADIOBUT_OFF', disable_icon='RADIOBUT_ON')

        menu.add_item().label("")

        menu.add_item().label("Type")
        menu.add_item().separator()

        # add the type menu items
        for item in type_items:
            menuprop(menu.add_item(), item[0], item[1], type_path, disable=True,
                     icon='RADIOBUT_OFF', disable_icon='RADIOBUT_ON')


class SymmetrizeMenu(bpy.types.Menu):
    bl_label = "Symmetrize"
    bl_idname = "view3d.symmetrize_menu"

    def draw(self, context):
        menu = Menu(self)
        path = "tool_settings.sculpt.symmetrize_direction"
        items = [["-X to +X", 'NEGATIVE_X'],
                 ["+X to -X", 'POSITIVE_X'],
                 ["-Y to +Y", 'NEGATIVE_Y'],
                 ["+Y to -Y", 'POSITIVE_Y'],
                 ["-Z to +Z", 'NEGATIVE_Z'],
                 ["+Z to -Z", 'POSITIVE_Z']]

        # add the the symmetrize operator to the menu
        menu.add_item().operator("sculpt.symmetrize")
        menu.add_item().separator()

        # add the rest of the menu items
        for item in items:
            menuprop(menu.add_item(), item[0], item[1], path, disable=True,
                     icon='RADIOBUT_OFF', disable_icon='RADIOBUT_ON')


### ------------ New hotkeys and registration ------------ ###
def register():
    pass

def unregister():
    pass 
if __name__ == "__main__":
    register()

