
bl_info = {
    "name": "Shading Menu: Key: 'Z' & 'Shift Z'",
    "description": "Shading Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "'Z' & 'Shift Z'",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"
}

import bpy
from ..utils import AddonPreferences, SpaceProperty
from bpy.types import Menu, Header
from bpy.types import Menu, Header
from bpy.props import IntProperty, FloatProperty, BoolProperty

# Pie Shading - Z


class PieShadingView(Menu):
    bl_idname = "pie.shadingview"
    bl_label = "Pie Shading"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.prop(context.space_data, "viewport_shade", expand=True)

        if context.active_object:
            if(context.mode == 'EDIT_MESH'):
                pie.operator("MESH_OT_faces_shade_smooth")
                pie.operator("MESH_OT_faces_shade_flat")
            else:
                pie.operator("OBJECT_OT_shade_smooth")
                pie.operator("OBJECT_OT_shade_flat")

# Pie Object Shading- Shift + Z
class PieObjectShading(Menu):
    bl_idname = "pie.objectshading"
    bl_label = "Pie Shading Object"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        view = context.space_data
        obj = context.object
        mesh = context.active_object.data
        fx_settings = view.fx_settings

        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("scene.togglegridaxis", text="Show/Hide Grid", icon="MESH_GRID")
        # 6 - RIGHT
        pie.operator("wire.selectedall", text="Wire", icon='WIRE')
        # 2 - BOTTOM
        box = pie.split().column()
        row = box.row(align=True)

        if view.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'}:
            row = box.row(align=True)
            row.prop(fx_settings, "use_dof")
            row = box.row(align=True)
            row.prop(fx_settings, "use_ssao", text="AO")
            if fx_settings.use_ssao:
                ssao_settings = fx_settings.ssao
                row = box.row(align=True)
                row.prop(ssao_settings, "factor")
                row = box.row(align=True)
                row.prop(ssao_settings, "distance_max")
                row = box.row(align=True)
                row.prop(ssao_settings, "attenuation")
                row = box.row(align=True)
                row.prop(ssao_settings, "samples")
                row = box.row(align=True)
                row.prop(ssao_settings, "color")
        # 8 - TOP
        box = pie.split().column()
        row = box.row(align=True)
        row.prop(obj, "show_x_ray", text="X-Ray")
        row = box.row(align=True)
        row.prop(view, "show_occlude_wire", text="Hidden Wire")
        row = box.row(align=True)
        row.prop(view, "show_backface_culling", text="Backface Culling")
        # 7 - TOP - LEFT
        box = pie.split().column()
        row = box.row(align=True)
        row.prop(mesh, "show_normal_face", text="Show Normals Faces", icon='FACESEL')
        row = box.row()
        row.menu("meshdisplay.overlays", text="Mesh display", icon='OBJECT_DATAMODE')
        # 9 - TOP - RIGHT
        box = pie.split().column()
        row = box.row(align=True)
        row.prop(mesh, "show_double_sided", text="Double sided")
        row = box.row(align=True)
        row.prop(mesh, "use_auto_smooth")
        if mesh.use_auto_smooth:
            row = box.row(align=True)
            row.prop(mesh, "auto_smooth_angle", text="Angle")
        # 1 - BOTTOM - LEFT
        box = pie.split().column()
        row = box.row(align=True)
        box.prop(view, "show_only_render")
        row = box.row(align=True)
        box.prop(view, "show_world")
        row = box.row(align=True)
        box.prop(view, "show_outline_selected")

        # 3 - BOTTOM - RIGHT
        box = pie.split().column()
        row = box.row(align=True)
        row.menu("object.material_list_menu", icon='MATERIAL_DATA')
        row = box.row(align=True)
        row.prop(view, "use_matcap", text="Matcaps")
        if view.use_matcap:
            row = box.row(align=True)
            row.menu("meshdisplay.matcaps", text="Choose Matcaps", icon='MATCAP_02')

# Overlays
class MeshDisplayMatcaps(bpy.types.Menu):
    bl_idname = "meshdisplay.matcaps"
    bl_label = "Mesh Display Matcaps"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        layout.template_icon_view(view, "matcap_icon")

class MeshDisplayOverlays(bpy.types.Menu):
    bl_idname = "meshdisplay.overlays"
    bl_label = "Mesh Display Overlays"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        mesh = context.active_object.data
        scene = context.scene

        split = layout.split()

        col = split.column()
        col.label(text="Overlays:")
        col.prop(mesh, "show_faces", text="Faces")
        col.prop(mesh, "show_edges", text="Edges")
        col.prop(mesh, "show_edge_crease", text="Creases")
        col.prop(mesh, "show_edge_seams", text="Seams")
        layout.prop(mesh, "show_weight")
        col.prop(mesh, "show_edge_sharp", text="Sharp")
        col.prop(mesh, "show_edge_bevel_weight", text="Bevel")
        col.prop(mesh, "show_freestyle_edge_marks", text="Edge Marks")
        col.prop(mesh, "show_freestyle_face_marks", text="Face Marks")

# Wire on selected objects
class WireSelectedAll(bpy.types.Operator):
    bl_idname = "wire.selectedall"
    bl_label = "Wire Selected All"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        for obj in bpy.data.objects:
            if bpy.context.selected_objects:
                if obj.select:
                    if obj.show_wire:
                        obj.show_all_edges = False
                        obj.show_wire = False
                    else:
                        obj.show_all_edges = True
                        obj.show_wire = True
            elif not bpy.context.selected_objects:
                if obj.show_wire:
                    obj.show_all_edges = False
                    obj.show_wire = False
                else:
                    obj.show_all_edges = True
                    obj.show_wire = True
        return {'FINISHED'}

# Grid show/hide with axes
class ToggleGridAxis(bpy.types.Operator):
    bl_idname = "scene.togglegridaxis"
    bl_label = "Toggle Grid and Axis in 3D view"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.space_data.show_axis_y = not bpy.context.space_data.show_axis_y
        bpy.context.space_data.show_axis_x = not bpy.context.space_data.show_axis_x
        bpy.context.space_data.show_floor = not bpy.context.space_data.show_floor
        return {'FINISHED'}

class ShadingVariable(bpy.types.Operator):
    bl_idname = "object.shadingvariable"
    bl_label = "Shading Variable"
    bl_options = {'REGISTER', 'UNDO'}
    variable = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.context.space_data.viewport_shade = self.variable
        return {'FINISHED'}


class ShadingSmooth(bpy.types.Operator):
    bl_idname = "shading.smooth"
    bl_label = "Shading Smooth"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.object.mode == "OBJECT":
            bpy.ops.object.shade_smooth()

        elif bpy.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class ShadingFlat(bpy.types.Operator):
    bl_idname = "shading.flat"
    bl_label = "Shading Flat"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.object.mode == "OBJECT":
            bpy.ops.object.shade_flat()

        elif bpy.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_flat()
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

# Pie Material
class MaterialListMenu(bpy.types.Menu):  # menu appel� par le pie
    bl_idname = "object.material_list_menu"
    bl_label = "Material_list"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        if len(bpy.data.materials):  # "len" retourne le nombre d'occurence donc, si il y a des materiaux dans les datas:
            for mat in bpy.data.materials:
                name = mat.name
                try:
                    icon_val = layout.icon(mat)  # r�cup�re l'icon du materiau
                except:
                    icon_val = 1
                    print("WARNING [Mat Panel]: Could not get icon value for %s" % name)

                op = col.operator("object.apply_material", text=name, icon_value=icon_val)  # op�rateur qui apparait dans le menu pour chaque mat�riau pr�sent dans les datas materials
                op.mat_to_assign = name  # on "stock" le nom du mat�riau dans la variable "mat_to_assign" declar�e dans la class op�rateur "ApplyMaterial"
        else:
            layout.label("No data materials")


class ApplyMaterial(bpy.types.Operator):
    bl_idname = "object.apply_material"
    bl_label = "Apply material"

    mat_to_assign = bpy.props.StringProperty(default="")

    def execute(self, context):

        if context.object.mode == 'EDIT':
            obj = context.object
            bm = bmesh.from_edit_mesh(obj.data)

            selected_face = [f for f in bm.faces if f.select]  # si des faces sont s�lectionn�es, elles sont stock�es dans la liste "selected_faces"

            mat_name = [mat.name for mat in bpy.context.object.material_slots if len(bpy.context.object.material_slots)]  # pour tout les material_slots, on stock les noms des mat de chaque slots dans la liste "mat_name"

            if self.mat_to_assign in mat_name:  # on test si le nom du mat s�lectionn� dans le menu est pr�sent dans la liste "mat_name" (donc, si un des slots poss�de le materiau du m�me nom). Si oui:
                context.object.active_material_index = mat_name.index(self.mat_to_assign)  # on definit le slot portant le nom du comme comme �tant le slot actif
                bpy.ops.object.material_slot_assign()  # on assigne le mat�riau � la s�lection
            else:  # sinon
                bpy.ops.object.material_slot_add()  # on ajout un slot
                bpy.context.object.active_material = bpy.data.materials[self.mat_to_assign]  # on lui assigne le materiau choisi
                bpy.ops.object.material_slot_assign()  # on assigne le mat�riau � la s�lection

            return {'FINISHED'}

        elif context.object.mode == 'OBJECT':

            obj_list = [obj.name for obj in context.selected_objects]

            for obj in obj_list:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[obj].select = True
                bpy.context.scene.objects.active = bpy.data.objects[obj]
                bpy.context.object.active_material_index = 0

                if self.mat_to_assign == bpy.data.materials:
                    bpy.context.active_object.active_material = bpy.data.materials[mat_name]

                else:
                    if not len(bpy.context.object.material_slots):
                        bpy.ops.object.material_slot_add()

                    bpy.context.active_object.active_material = bpy.data.materials[self.mat_to_assign]

            for obj in obj_list:
                bpy.data.objects[obj].select = True

            return {'FINISHED'}

classes = [
    PieShadingView,
    PieObjectShading,
    MeshDisplayMatcaps,
    MeshDisplayOverlays,
    WireSelectedAll,
    ToggleGridAxis,
    ShadingVariable,
    ShadingSmooth,
    ShadingFlat,
    MaterialListMenu,
    ApplyMaterial,
    ]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Shading
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'Z', 'PRESS')
        kmi.properties.name = "pie.shadingview"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

        # Object shading
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'Z', 'PRESS', shift=True)
        kmi.properties.name = "pie.objectshading"
#        kmi.active = True
        addon_keymaps.append((km, kmi))

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View Generic']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.shadingview":
                    km.keymap_items.remove(kmi)

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View Generic']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.objectshading":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
