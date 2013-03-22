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

bl_info = {
    'name': "Nodes Efficiency Tools",
    'author': "Bartek Skorupa",
    'version': (2, 0.12),
    'blender': (2, 6, 6),
    'location': "Node Editor Properties Panel (Ctrl-SPACE)",
    'description': "Nodes Efficiency Tools",
    'warning': "", 
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Nodes_Efficiency_Tools",
    'tracker_url': "http://projects.blender.org/tracker/?func=detail&atid=468&aid=33543&group_id=153",
    'category': "Node",
    }

import bpy
from bpy.props import EnumProperty, StringProperty, BoolProperty, FloatProperty

#################
# rl_outputs:
# list of outputs of Input Render Layer
# with attributes determinig if pass is used,
# and MultiLayer EXR outputs names and corresponding render engines
#
# rl_outputs entry = (render_pass, rl_output_name, exr_output_name, in_internal, in_cycles)
rl_outputs = (
    ('use_pass_ambient_occlusion', 'AO', 'AO', True, True),
    ('use_pass_color', 'Color', 'Color',True, False),
    ('use_pass_combined', 'Image', 'Combined', True, True),
    ('use_pass_diffuse', 'Diffuse', 'Diffuse', True, False),
    ('use_pass_diffuse_color', 'Diffuse Color', 'DiffCol', False, True),
    ('use_pass_diffuse_direct', 'Diffuse Direct', 'DiffDir', False, True),
    ('use_pass_diffuse_indirect', 'Diffuse Indirect', 'DiffInd', False, True),
    ('use_pass_emit', 'Emit', 'Emit', True, False),
    ('use_pass_environment', 'Environment', 'Env', True, False),
    ('use_pass_glossy_color', 'Glossy Color', 'GlossCol', False, True),
    ('use_pass_glossy_direct', 'Glossy Direct', 'GlossDir', False, True),
    ('use_pass_glossy_indirect', 'Glossy Indirect', 'GlossInd', False, True),
    ('use_pass_indirect', 'Indirect', 'Indirect', True, False),
    ('use_pass_material_index', 'IndexMA', 'IndexMA', True, True),
    ('use_pass_mist', 'Mist', 'Mist', True, False),
    ('use_pass_normal', 'Normal', 'Normal', True, True),
    ('use_pass_object_index', 'IndexOB', 'IndexOB', True, True),
    ('use_pass_reflection', 'Reflect', 'Reflect', True, False),
    ('use_pass_refraction', 'Refract', 'Refract', True, False),
    ('use_pass_shadow', 'Shadow', 'Shadow', True, True),
    ('use_pass_specular', 'Specular', 'Spec', True, False),
    ('use_pass_transmission_color', 'Transmission Color', 'TransCol', False, True),
    ('use_pass_transmission_direct', 'Transmission Direct', 'TransDir', False, True),
    ('use_pass_transmission_indirect', 'Transmission Indirect', 'TransInd', False, True),
    ('use_pass_uv', 'UV', 'UV', True, True),
    ('use_pass_vector', 'Speed', 'Vector', True, True),
    ('use_pass_z', 'Z', 'Depth', True, True),
    )

# list of blend types of "Mix" nodes
blend_types = (
    'MIX', 'ADD', 'MULTIPLY', 'SUBTRACT', 'SCREEN',
    'DIVIDE', 'DIFFERENCE', 'DARKEN', 'LIGHTEN', 'OVERLAY',
    'DODGE', 'BURN', 'HUE', 'SATURATION', 'VALUE',
    'COLOR', 'SOFT_LIGHT', 'LINEAR_LIGHT',
    )
# list of operations of "Math" nodes
operations = (
    'ADD', 'MULTIPLY', 'SUBTRACT', 'DIVIDE', 'SINE',
    'COSINE', 'TANGENT', 'ARCSINE', 'ARCCOSINE', 'ARCTANGENT',
    'POWER', 'LOGARITHM', 'MINIMUM', 'MAXIMUM', 'ROUND',
    'LESS_THAN', 'GREATER_THAN',
    )
# list of mixing shaders
merge_shaders = ('MIX', 'ADD')

def set_convenience_variables(context):
    global nodes
    global links

    space = context.space_data
    tree = space.node_tree
    nodes = tree.nodes
    links = tree.links
    active = nodes.active
    context_active = context.active_node
    # check if we are working on regular node tree or node group is currently edited.
    # if group is edited - active node of space_tree is the group
    # if context.active_node != space active node - it means that the group is being edited.
    # in such case we set "nodes" to be nodes of this group, "links" to be links of this group
    # if context.active_node == space.active_node it means that we are not currently editing group
    is_main_tree = True
    if active:
        is_main_tree = context_active == active
    if not is_main_tree:  # if group is currently edited
        tree = active.node_tree
        nodes = tree.nodes
        links = tree.links
    
    return


class MergeNodes(bpy.types.Operator):
    bl_idname = "node.merge_nodes"
    bl_label = "Merge Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: "BlendType/ShaderKind/MathOperation and Node Kind" separated with space
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        tree_type = context.space_data.node_tree.type
        if tree_type == 'COMPOSITING':
            node_type = 'CompositorNode'
        elif tree_type == 'SHADER':
            node_type = 'ShaderNode'
        set_convenience_variables(context)
        option_split = self.option.split( )
        mode = option_split[0]
        node_kind = option_split[1]  # kinds: 'AUTO', 'SHADER', 'MIX', 'MATH'
        selected_mix = []  # entry = [index, loc]
        selected_shader = []  # entry = [index, loc]
        selected_math = []  # entry = [index, loc]
        
        for i, node in enumerate(nodes):
            if node.select and node.outputs:
                if node_kind == 'AUTO':
                    for (type, the_list, dst) in (
                        ('SHADER', merge_shaders, selected_shader),
                        ('RGBA', blend_types, selected_mix),
                        ('VALUE', operations, selected_math),
                        ):
                        output_type = node.outputs[0].type
                        valid_mode = mode in the_list
                        # When mode is 'MIX' use mix node for both 'RGBA' and 'VALUE' output types.
                        # Cheat that output type is 'RGBA',
                        # and that 'MIX' exists in math operations list.
                        # This way when selected_mix list is analyzed:
                        # Node data will be appended even though it doesn't meet requirements.
                        if output_type != 'SHADER' and mode == 'MIX':
                            output_type = 'RGBA'
                            valid_mode = True
                        if output_type == type and valid_mode:
                            dst.append([i, node.location.x, node.location.y])
                else:
                    for (kind, the_list, dst) in (
                        ('MIX', blend_types, selected_mix),
                        ('SHADER', merge_shaders, selected_shader),
                        ('MATH', operations, selected_math),
                        ):
                        if node_kind == kind and mode in the_list:
                            dst.append([i, node.location.x, node.location.y])
        # When nodes with output kinds 'RGBA' and 'VALUE' are selected at the same time
        # use only 'Mix' nodes for merging.
        # For that we add selected_math list to selected_mix list and clear selected_math.
        if selected_mix and selected_math and node_kind == 'AUTO':
            selected_mix += selected_math
            selected_math = []
        
        for the_list in [selected_mix, selected_shader, selected_math]:
            if the_list:
                count_before = len(nodes)
                # sort list by loc_x - reversed
                the_list.sort(key = lambda k: k[1], reverse = True)
                # get maximum loc_x
                loc_x = the_list[0][1] + 350.0
                the_list.sort(key = lambda k: k[2], reverse = True)
                loc_y = the_list[len(the_list) - 1][2]
                offset_y = 40.0
                if the_list == selected_shader:
                    offset_y = 150.0
                the_range = len(the_list)-1
                do_hide = True
                if len(the_list) == 1:
                    the_range = 1
                    do_hide = False
                for i in range(the_range):
                    if the_list == selected_mix:
                        add_type = node_type + 'MixRGB'
                        add = nodes.new(add_type)
                        add.blend_type = mode
                        add.show_preview = False
                        add.hide = do_hide
                        first = 1
                        second = 2
                        add.width_hidden = 100.0
                    elif the_list == selected_math:
                        add_type = node_type + 'Math'
                        add = nodes.new(add_type)
                        add.operation = mode
                        add.hide = do_hide
                        first = 0
                        second = 1
                        add.width_hidden = 100.0
                    elif the_list == selected_shader:
                        if mode == 'MIX':
                            add_type = node_type + 'MixShader'
                            add = nodes.new(add_type)
                            first = 1
                            second = 2
                            add.width_hidden = 100.0
                        elif mode == 'ADD':
                            add_type = node_type + 'AddShader'
                            add = nodes.new(add_type)
                            first = 0
                            second = 1
                            add.width_hidden = 100.0
                    add.location.x = loc_x
                    add.location.y = loc_y
                    loc_y += offset_y
                    add.select = True
                count_adds = i + 1
                count_after = len(nodes)
                index = count_after - 1
                # add link from "first" selected and "first" add node
                links.new(nodes[the_list[0][0]].outputs[0], nodes[count_after - 1].inputs[first])
                # add links between added ADD nodes and between selected and ADD nodes
                for i in range(count_adds):
                    if i < count_adds - 1:
                        links.new(nodes[index-1].inputs[first], nodes[index].outputs[0])
                    if len(the_list) > 1:
                        links.new(nodes[index].inputs[second], nodes[the_list[i+1][0]].outputs[0])
                    index -= 1
                # set "last" of added nodes as active    
                nodes.active = nodes[count_before]
                for [i, x, y] in the_list:
                    nodes[i].select = False
                    
        return {'FINISHED'}


class BatchChangeNodes(bpy.types.Operator):
    bl_idname = "node.batch_change"
    bl_label = "Batch Change Blend Type and Math Operation"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Mix Blend Type and Math Operation separated with space.
    option = StringProperty()
        
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        navs = ('CURRENT', 'NEXT', 'PREV')
        option_split = self.option.split( )
        blend_type = option_split[0]
        operation = option_split[1]
        for node in context.selected_nodes:
            if node.type == 'MIX_RGB':
                if not blend_type in navs:
                    node.blend_type = blend_type
                else:
                    if blend_type == 'NEXT':
                        index = blend_types.index(node.blend_type)
                        if index == len(blend_types) - 1:
                            node.blend_type = blend_types[0]
                        else:
                            node.blend_type = blend_types[index + 1]

                    if blend_type == 'PREV':
                        index = blend_types.index(node.blend_type)
                        if index == 0:
                            node.blend_type = blend_types[len(blend_types) - 1]
                        else:
                            node.blend_type = blend_types[index - 1]
                                                        
            if node.type == 'MATH':
                if not operation in navs:
                    node.operation = operation
                else:
                    if operation == 'NEXT':
                        index = operations.index(node.operation)
                        if index == len(operations) - 1:
                            node.operation = operations[0]
                        else:
                            node.operation = operations[index + 1]

                    if operation == 'PREV':
                        index = operations.index(node.operation)
                        if index == 0:
                            node.operation = operations[len(operations) - 1]
                        else:
                            node.operation = operations[index - 1]

        return {'FINISHED'}


class ChangeMixFactor(bpy.types.Operator):
    bl_idname = "node.factor"
    bl_label = "Change Factors of Mix Nodes and Mix Shader Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: Change factor.
    # If option is 1.0 or 0.0 - set to 1.0 or 0.0
    # Else - change factor by option value.
    option = FloatProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        option = self.option
        selected = []  # entry = index
        for si, node in enumerate(nodes):
            if node.select:
                if node.type in {'MIX_RGB', 'MIX_SHADER'}:
                    selected.append(si)
                
        for si in selected:
            fac = nodes[si].inputs[0]
            nodes[si].hide = False
            if option in {0.0, 1.0}:
                fac.default_value = option
            else:
                fac.default_value += option
        
        return {'FINISHED'}


class NodesCopySettings(bpy.types.Operator):
    bl_idname = "node.copy_settings"
    bl_label = "Copy Settings of Active Node to Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if (space.type == 'NODE_EDITOR' and
                space.node_tree is not None and
                context.active_node is not None and
                context.active_node.type is not 'FRAME'
                ):
            valid = True
        return valid
    
    def execute(self, context):
        set_convenience_variables(context)
        selected = [n for n in nodes if n.select]
        reselect = []  # duplicated nodes will be selected after execution
        active = nodes.active
        if active.select:
            reselect.append(active)
        
        for node in selected:
            if node.type == active.type and node != active:
                # duplicate active, relink links as in 'node', append copy to 'reselect', delete node
                bpy.ops.node.select_all(action = 'DESELECT')
                nodes.active = active
                active.select = True
                bpy.ops.node.duplicate()
                copied = nodes.active
                # Copied active should however inherit some properties from 'node'
                attributes = (
                    'hide', 'show_preview', 'mute', 'label',
                    'use_custom_color', 'color', 'width', 'width_hidden',
                    )
                for attr in attributes:
                    setattr(copied, attr, getattr(node, attr))
                # Handle scenario when 'node' is in frame. 'copied' is in same frame then.
                if copied.parent:
                    bpy.ops.node.parent_clear()
                locx = node.location.x
                locy = node.location.y
                # get absolute node location
                parent = node.parent
                while parent:
                    locx += parent.location.x
                    locy += parent.location.y
                    parent = parent.parent
                copied.location = [locx, locy]
                # reconnect links from node to copied
                for i, input in enumerate(node.inputs):
                    if input.links:
                        link = input.links[0]
                        links.new(link.from_socket, copied.inputs[i])
                for out, output in enumerate(node.outputs):
                    if output.links:
                        out_links = output.links
                        for link in out_links:
                            links.new(copied.outputs[out], link.to_socket)
                bpy.ops.node.select_all(action = 'DESELECT')
                node.select = True
                bpy.ops.node.delete()
                reselect.append(copied)
            else:  # If selected wasn't copied, need to reselect it afterwards.
                reselect.append(node)
        # clean up
        bpy.ops.node.select_all(action = 'DESELECT')
        for node in reselect:
            node.select = True
        nodes.active = active
        
        return {'FINISHED'}


class NodesCopyLabel(bpy.types.Operator):
    bl_idname = "node.copy_label"
    bl_label = "Copy Label"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: 'from active', 'from node', 'from socket'
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        option = self.option
        active = nodes.active
        if option == 'from active':
            if active:
                src_label = active.label
                for node in [n for n in nodes if n.select and nodes.active != n]:
                    node.label = src_label
        elif option == 'from node':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_node
                        node.label = src.label
                        break
        elif option == 'from socket':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_socket
                        node.label = src.name
                        break
        
        return {'FINISHED'}


class NodesClearLabel(bpy.types.Operator):
    bl_idname = "node.clear_label"
    bl_label = "Clear Label"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: 'confirmed', 'not confirmed'
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        for node in [n for n in nodes if n.select]:
            node.label = ''
        
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.option == 'confirmed':
            return self.execute(context)
        else:
            return context.window_manager.invoke_confirm(self, event)


class NodesAddTextureSetup(bpy.types.Operator):
    bl_idname = "node.add_texture"
    bl_label = "Add Texture Node to Active Node Input"
    bl_options = {'REGISTER', 'UNDO'}
    
    # placeholder
    option = StringProperty()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None:
                valid = True
        return valid
    
    def execute(self, context):
        set_convenience_variables(context)
        active = nodes.active
        valid = False
        if active:
            if active.select:
                if active.type in (
                    'BSDF_ANISOTROPIC',
                    'BSDF_DIFFUSE',
                    'BSDF_GLOSSY',
                    'BSDF_GLASS',
                    'BSDF_REFRACTION',
                    'BSDF_TRANSLUCENT',
                    'BSDF_TRANSPARENT',
                    'BSDF_VELVET',
                    'EMISSION',
                    'AMBIENT_OCCLUSION',
                    ):
                    if not active.inputs[0].is_linked:
                        valid = True
        if valid:
            locx = active.location.x
            locy = active.location.y
            tex = nodes.new('ShaderNodeTexImage')
            tex.location = [locx - 200.0, locy + 28.0]
            map = nodes.new('ShaderNodeMapping')
            map.location = [locx - 490.0, locy + 80.0]
            coord = nodes.new('ShaderNodeTexCoord')
            coord.location = [locx - 700, locy + 40.0]
            active.select = False
            nodes.active = tex
            
            links.new(tex.outputs[0], active.inputs[0])
            links.new(map.outputs[0], tex.inputs[0])
            links.new(coord.outputs[2], map.inputs[0])
            
        return {'FINISHED'}


class NodesAddReroutes(bpy.types.Operator):
    bl_idname = "node.add_reroutes"
    bl_label = "Add Reroutes to Outputs"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: 'all', 'loose'
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        tree_type = context.space_data.node_tree.type
        if tree_type == 'COMPOSITING':
            node_type = 'CompositorNode'
        elif tree_type == 'SHADER':
            node_type = 'ShaderNode'
        option = self.option
        set_convenience_variables(context)
        # output valid when option is 'all' or when 'loose' output has no links
        valid = False
        post_select = []  # nodes to be selected after execution
        # create reroutes and recreate links
        for node in [n for n in nodes if n.select]:
            if node.outputs:
                x = node.location.x
                y = node.location.y
                width = node.width
                # unhide 'REROUTE' nodes to avoid issues with location.y
                if node.type == 'REROUTE':
                    node.hide = False
                # When node is hidden - width_hidden not usable.
                # Hack needed to calculate real width
                if node.hide:
                    bpy.ops.node.select_all(action = 'DESELECT')
                    helper = nodes.new('NodeReroute')
                    helper.select = True
                    node.select = True
                    # resize node and helper to zero. Then check locations to calculate width
                    bpy.ops.transform.resize(value = (0.0, 0.0, 0.0))
                    width = 2.0 * (helper.location.x - node.location.x)
                    # restore node location
                    node.location = [x,y]
                    # delete helper
                    node.select = False
                    # only helper is selected now
                    bpy.ops.node.delete()
                x = node.location.x + width + 20.0
                if node.type != 'REROUTE':
                    y -= 35.0
                y_offset = -21.0
                loc = [x, y]
            reroutes_count = 0  # will be used when aligning reroutes added to hidden nodes
            for out_i, output in enumerate(node.outputs):
                pass_used = False  # initial value to be analyzed if 'R_LAYERS'
                # if node is not 'R_LAYERS' - "pass_used" not needed, so set it to True
                if node.type != 'R_LAYERS':
                    pass_used = True
                else:  # if 'R_LAYERS' check if output represent used render pass
                    node_scene = node.scene
                    node_layer = node.layer
                    # If output - "Alpha" is analyzed - assume it's used. Not represented in passes.
                    if output.name == 'Alpha':
                        pass_used = True
                    else:
                        # check entries in global 'rl_outputs' variable
                        for [render_pass, out_name, exr_name, in_internal, in_cycles] in rl_outputs:
                            if output.name == out_name:
                                pass_used = getattr(node_scene.render.layers[node_layer], render_pass)
                                break
                if pass_used:
                    valid = option == 'all' or (option == 'loose' and not output.links)
                    # Add reroutes only if valid, but offset location in all cases.
                    if valid:
                        n = nodes.new('NodeReroute')
                        nodes.active = n
                        for link in output.links:
                            links.new(n.outputs[0], link.to_socket)
                        links.new(output, n.inputs[0])
                        n.location = loc
                        post_select.append(n)
                    reroutes_count += 1
                    y += y_offset 
                    loc = [x, y]
            # disselect the node so that after execution of script only newly created nodes are selected
            node.select = False
            # nicer reroutes distribution along y when node.hide
            if node.hide:
                y_translate = reroutes_count * y_offset / 2.0 - y_offset - 35.0
                for reroute in [r for r in nodes if r.select]:
                    reroute.location.y -= y_translate
            for node in post_select:
                node.select = True
        
        return {'FINISHED'}
    

class NodesSwap(bpy.types.Operator):
    bl_idname = "node.swap_nodes"
    bl_label = "Swap Reroutes and Switches"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: 'CompositorNodeSwitch', 'NodeReroute', 'NodeMixRGB', 'NodeMath', 'CompositorNodeAlphaOver'
    # 'CompositorNodeSwitch' - change selected reroutes to switches
    # 'NodeReroute' - change selected switches to reroutes
    # 'NodeMixRGB' - change selected switches to MixRGB (prefix 'Compositor' or 'Shader' will be added
    # 'NodeMath' - change selected switches to Math (prefix 'Compositor' or 'Shader' will be added
    # 'CompositorNodeAlphaOver'
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        tree_type = context.space_data.tree_type
        if tree_type == 'CompositorNodeTree':
            prefix = 'Compositor'
        elif tree_type == 'ShaderNodeTree':
            prefix = 'Shader'
        option = self.option
        selected = [n for n in nodes if n.select]
        reselect = []
        mode = None  # will be used to set proper operation or blend type in new Math or Mix nodes.
        if option == 'CompositorNodeSwitch':
            replace_types = ('REROUTE', 'MIX_RGB', 'MATH', 'ALPHAOVER')
            new_type = option
        elif option == 'NodeReroute':
            replace_types = ('SWITCH')
            new_type = option
        elif option == 'NodeMixRGB':
            replace_types = ('REROUTE', 'SWITCH', 'MATH', 'ALPHAOVER')
            new_type = prefix + option
        elif option == 'NodeMath':
            replace_types = ('REROUTE', 'SWITCH', 'MIX_RGB', 'ALPHAOVER')
            new_type = prefix + option
        elif option == 'CompositorNodeAlphaOver':
            replace_types = ('REROUTE', 'SWITCH', 'MATH', 'MIX_RGB')
            new_type = option
        for node in selected:
            if node.type in replace_types:
                hide = node.hide
                if node.type == 'REROUTE':
                    hide = True
                new_node = nodes.new(new_type)
                # if swap Mix to Math of vice-verca - try to set blend type or operation accordingly
                if new_node.type == 'MIX_RGB':
                    if node.type == 'MATH':
                        if node.operation in blend_types:
                            new_node.blend_type = node.operation
                elif new_node.type == 'MATH':
                    if node.type == 'MIX_RGB':
                        if node.blend_type in operations:
                            new_node.operation = node.blend_type
                old_inputs_count = len(node.inputs)
                new_inputs_count = len(new_node.inputs)
                if new_inputs_count == 1:
                    replace = [[0, 0]]  # old input 0 (first of the entry) will be replaced by new input 0.
                elif new_inputs_count == 2:
                    if old_inputs_count == 1:
                        replace = [[0, 0]]
                    elif old_inputs_count == 2:
                        replace = [[0, 0], [1, 1]]
                    elif old_inputs_count == 3:
                        replace = [[1, 0], [2, 1]]
                elif new_inputs_count == 3:
                    if old_inputs_count == 1:
                        replace = [[0, 1]]
                    elif old_inputs_count == 2:
                        replace = [[0, 1], [1, 2]]
                    elif old_inputs_count == 3:
                        replace = [[0, 0], [1, 1], [2, 2]]
                for [old, new] in replace:
                    if node.inputs[old].links:
                        in_link = node.inputs[old].links[0]
                        links.new(in_link.from_socket, new_node.inputs[new])
                for out_link in node.outputs[0].links:
                    links.new(new_node.outputs[0], out_link.to_socket)
                new_node.location = node.location
                new_node.label = node.label
                new_node.hide = hide
                new_node.mute = node.mute
                new_node.show_preview = node.show_preview
                new_node.width_hidden = node.width_hidden
                nodes.active = new_node
                reselect.append(new_node)
                bpy.ops.node.select_all(action = "DESELECT")
                node.select = True
                bpy.ops.node.delete()
            else:
                reselect.append(node)
        for node in reselect:
            node.select = True
            
        return {'FINISHED'}


class NodesLinkActiveToSelected(bpy.types.Operator):
    bl_idname = "node.link_active_to_selected"
    bl_label = "Link Active Node to Selected"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: 'bool bool bool' - replace, use node's name, use outputs' names
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None and context.active_node is not None:
                if context.active_node.select:
                    valid = True
        return valid
    
    def execute(self, context):
        set_convenience_variables(context)
        option_split = self.option.split( )
        replace = eval(option_split[0])
        use_node_name = eval(option_split[1])
        use_outputs_names = eval(option_split[2])
        active = nodes.active
        selected = [node for node in nodes if node.select and node != active]
        outputs = []  # Only usable outputs of active nodes will be stored here.
        for out in active.outputs:
            if active.type != 'R_LAYERS':
                outputs.append(out)
            else:
                # 'R_LAYERS' node type needs special handling.
                # outputs of 'R_LAYERS' are callable even if not seen in UI.
                # Only outputs that represent used passes should be taken into account
                # Check if pass represented by output is used.
                # global 'rl_outputs' list will be used for that
                for [render_pass, out_name, exr_name, in_internal, in_cycles] in rl_outputs:
                    pass_used = False  # initial value. Will be set to True if pass is used
                    if out.name == 'Alpha':
                        # Alpha output is always present. Doesn't have representation in render pass. Assume it's used.
                        pass_used = True
                    elif out.name == out_name:
                        # example 'render_pass' entry: 'use_pass_uv' Check if True in scene render layers
                        pass_used = getattr(active.scene.render.layers[active.layer], render_pass)
                        break
                if pass_used:
                    outputs.append(out)
        doit = True  # Will be changed to False when links successfully added to previous output.
        for out in outputs:
            if doit:
                for node in selected:
                    dst_name = node.name  # Will be compared with src_name if needed.
                    # When node has label - use it as dst_name
                    if node.label:
                        dst_name = node.label
                    valid = True  # Initial value. Will be changed to False if names don't match.
                    src_name = dst_name  # If names not used - this asignment will keep valid = True.
                    if use_node_name:
                        # Set src_name to source node name or label
                        src_name = active.name
                        if active.label:
                            src_name = active.label
                    elif use_outputs_names:
                        # Set src_name to name of output currently analyzed.
                        src_name = out.name
                    if src_name != dst_name:
                        valid = False
                    if valid:
                        for input in node.inputs:
                            if input.type == out.type or node.type == 'REROUTE':
                                if replace or not input.is_linked:
                                    links.new(out, input)
                                    if not use_node_name and not use_outputs_names:
                                        doit = False
                                    break
        
        return {'FINISHED'}


class AlignNodes(bpy.types.Operator):
    bl_idname = "node.align_nodes"
    bl_label = "Align nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: 'Vertically', 'Horizontally'
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        selected = []  # entry = [index, loc.x, loc.y, width, height]
        frames_reselect = []  # entry = frame node. will be used to reselect all selected frames
        active = nodes.active
        for i, node in enumerate(nodes):
            if node.select:
                if node.type == 'FRAME':
                    node.select = False
                    frames_reselect.append(i)
                else:
                    locx = node.location.x
                    locy = node.location.y
                    parent = node.parent
                    while parent != None:
                        locx += parent.location.x
                        locy += parent.location.y
                        parent = parent.parent
                    selected.append([i, locx, locy])
        count = len(selected)
        # add reroute node then scale all to 0.0 and calculate widths and heights of nodes
        if count > 1:  # aligning makes sense only if at least 2 nodes are selected
            helper = nodes.new('NodeReroute')
            helper.select = True
            bpy.ops.transform.resize(value = (0.0, 0.0, 0.0))
            # store helper's location for further calculations
            zero_x = helper.location.x
            zero_y = helper.location.y
            nodes.remove(helper)
            # helper is deleted but its location is stored
            # helper's width and height are 0.0.
            # Check loc of other nodes in relation to helper to calculate their dimensions
            # and append them to entries of "selected"
            total_w = 0.0  # total width of all nodes. Will be calculated later.
            total_h = 0.0  # total height of all nodes. Will be calculated later
            for j, [i, x, y] in enumerate(selected):
                locx = nodes[i].location.x
                locy = nodes[i].location.y
                # take node's parent (frame) into account. Get absolute location
                parent = nodes[i].parent
                while parent != None:
                        locx += parent.location.x
                        locy += parent.location.y
                        parent = parent.parent
                width = abs((zero_x - locx) * 2.0)
                height = abs((zero_y - locy) * 2.0)
                selected[j].append(width)  # complete selected's entry for nodes[i]
                selected[j].append(height)  # complete selected's entry for nodes[i]
                total_w += width  # add nodes[i] width to total width of all nodes
                total_h += height  # add nodes[i] height to total height of all nodes
            selected_sorted_x = sorted(selected, key = lambda k: (k[1], -k[2]))
            selected_sorted_y = sorted(selected, key = lambda k: (-k[2], k[1]))
            min_x = selected_sorted_x[0][1]  # min loc.x
            min_x_loc_y = selected_sorted_x[0][2]  # loc y of node with min loc x
            min_x_w = selected_sorted_x[0][3]  # width of node with max loc x
            max_x = selected_sorted_x[count - 1][1]  # max loc.x
            max_x_loc_y = selected_sorted_x[count - 1][2]  # loc y of node with max loc.x
            max_x_w = selected_sorted_x[count - 1][3]  #  width of node with max loc.x
            min_y = selected_sorted_y[0][2]  # min loc.y
            min_y_loc_x = selected_sorted_y[0][1]  # loc.x of node with min loc.y
            min_y_h = selected_sorted_y[0][4]  # height of node with min loc.y
            min_y_w = selected_sorted_y[0][3]  # width of node with min loc.y
            max_y = selected_sorted_y[count - 1][2]  # max loc.y
            max_y_loc_x = selected_sorted_y[count - 1][1]  # loc x of node with max loc.y
            max_y_w = selected_sorted_y[count - 1][3]  # width of node with max loc.y
            max_y_h = selected_sorted_y[count - 1][4]  # height of node with max loc.y
            
            if self.option == 'Vertically':
                loc_x = min_x
                #loc_y = (max_x_loc_y + min_x_loc_y) / 2.0
                loc_y = (max_y - max_y_h / 2.0 + min_y - min_y_h / 2.0) / 2.0
                offset_x = (max_x - min_x - total_w + max_x_w) / (count - 1)
                for [i, x, y, w, h] in selected_sorted_x:
                    nodes[i].location.x = loc_x
                    nodes[i].location.y = loc_y + h / 2.0
                    parent = nodes[i].parent
                    while parent != None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_x += offset_x + w
            else:  # if align Horizontally
                #loc_x = (max_y_loc_x + max_y_w / 2.0 + min_y_loc_x + min_y_w / 2.0) / 2.0
                loc_x = (max_x + max_x_w / 2.0 + min_x + min_x_w / 2.0) / 2.0
                loc_y = min_y
                offset_y = (max_y - min_y + total_h - min_y_h) / (count - 1)
                for [i, x, y, w, h] in selected_sorted_y:
                    nodes[i].location.x = loc_x - w / 2.0
                    nodes[i].location.y = loc_y
                    parent = nodes[i].parent
                    while parent != None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_y += offset_y - h
    
            # reselect selected frames
            for i in frames_reselect:
                nodes[i].select = True
            # restore active node
            nodes.active = active
        
        return {'FINISHED'}


class SelectParentChildren(bpy.types.Operator):
    bl_idname = "node.select_parent_child"
    bl_label = "Select Parent or Children"
    bl_options = {'REGISTER', 'UNDO'}
    
    # option: 'Parent', 'Children'
    option = StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        option = self.option
        selected = [node for node in nodes if node.select]
        if option == 'Parent':
            for sel in selected:
                parent = sel.parent
                if parent:
                    parent.select = True
        else:
            for sel in selected:
                children = [node for node in nodes if node.parent == sel]
                for kid in children:
                    kid.select = True
        
        return {'FINISHED'}


#############################################################
#  P A N E L S
#############################################################

class EfficiencyToolsPanel(bpy.types.Panel):
    bl_idname = "NODE_PT_efficiency_tools"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Efficiency Tools (Ctrl-SPACE)"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout

        box = layout.box()
        box.menu(MergeNodesMenu.bl_idname)
        if type == 'ShaderNodeTree':
            box.operator(NodesAddTextureSetup.bl_idname, text = 'Add Image Texture (Ctrl T)')
        box.menu(BatchChangeNodesMenu.bl_idname, text = 'Batch Change...')
        box.menu(NodeAlignMenu.bl_idname, text = "Align Nodes (Shift =)")
        box.menu(CopyToSelectedMenu.bl_idname, text = 'Copy to Selected (Shift-C)')
        box.operator(NodesClearLabel.bl_idname).option = 'confirmed'
        box.menu(AddReroutesMenu.bl_idname, text = 'Add Reroutes')
        box.menu(NodesSwapMenu.bl_idname, text = 'Swap Nodes')
        box.menu(LinkActiveToSelectedMenu.bl_idname, text = 'Link Active To Selected')


#############################################################
#  M E N U S
#############################################################

class EfficiencyToolsMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_node_tools_menu"
    bl_label = "Efficiency Tools"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        layout.menu(MergeNodesMenu.bl_idname, text = 'Merge Selected Nodes')
        if type == 'ShaderNodeTree':
            layout.operator(NodesAddTextureSetup.bl_idname, text = 'Add Image Texture with coordinates')
        layout.menu(BatchChangeNodesMenu.bl_idname, text = 'Batch Change')
        layout.menu(NodeAlignMenu.bl_idname, text="Align Nodes")
        layout.menu(CopyToSelectedMenu.bl_idname, text = 'Copy to Selected')
        layout.operator(NodesClearLabel.bl_idname).option = 'confirmed'
        layout.menu(AddReroutesMenu.bl_idname, text = 'Add Reroutes')
        layout.menu(NodesSwapMenu.bl_idname, text = 'Swap Nodes')
        layout.menu(LinkActiveToSelectedMenu.bl_idname, text = 'Link Active To Selected')


class MergeNodesMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_merge_nodes_menu"
    bl_label = "Merge Selected Nodes"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(MergeShadersMenu.bl_idname, text = 'Use Shaders')
        layout.menu(MergeMixMenu.bl_idname, text="Use Mix Nodes")
        layout.menu(MergeMathMenu.bl_idname, text="Use Math Nodes")


class MergeShadersMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_merge_shaders_menu"
    bl_label = "Merge Selected Nodes using Shaders"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        for type in merge_shaders:
            option = type + ' SHADER'
            layout.operator(MergeNodes.bl_idname, text = type).option = option


class MergeMixMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_merge_mix_menu"
    bl_label = "Merge Selected Nodes using Mix"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        for type in blend_types:
            option = type + ' MIX'
            layout.operator(MergeNodes.bl_idname, text = type).option = option        


class MergeMathMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_merge_math_menu"
    bl_label = "Merge Selected Nodes using Math"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        for type in operations:
            option = type + ' MATH'
            layout.operator(MergeNodes.bl_idname, text = type).option = option


class BatchChangeNodesMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_batch_change_nodes_menu"
    bl_label = "Batch Change Selected Nodes"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.menu(BatchChangeBlendTypeMenu.bl_idname)
        layout.menu(BatchChangeOperationMenu.bl_idname)
                                  

class BatchChangeBlendTypeMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_batch_change_blend_type_menu"
    bl_label = "Batch Change Blend Type"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        for blend_type in blend_types:
            option = blend_type + ' CURRENT'
            layout.operator(BatchChangeNodes.bl_idname, text = blend_type).option = option


class BatchChangeOperationMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_batch_change_operation_menu"
    bl_label = "Batch Change Math Operation"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        for operation in operations:
            option = 'CURRENT ' + operation
            layout.operator(BatchChangeNodes.bl_idname, text = operation).option = option
                                  

class CopyToSelectedMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_copy_node_properties_menu"
    bl_label = "Copy to Selected"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesCopySettings.bl_idname, text = 'Settings from Active')
        layout.menu(CopyLabelMenu.bl_idname)


class CopyLabelMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_copy_label_menu"
    bl_label = "Copy Label"
    
    def draw(self, context):
        layout = self.layout
        layout.operator(NodesCopyLabel.bl_idname, text = 'from Active Node\'s Label').option = 'from active'
        layout.operator(NodesCopyLabel.bl_idname, text = 'from Linked Node\'s Label').option = 'from node'
        layout.operator(NodesCopyLabel.bl_idname, text = 'from Linked Output\'s Name').option = 'from socket'


class AddReroutesMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_add_reroutes_menu"
    bl_label = "Add Reroutes"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesAddReroutes.bl_idname, text = 'to All Outputs').option = 'all'
        layout.operator(NodesAddReroutes.bl_idname, text = 'to Loose Outputs').option = 'loose'


class NodesSwapMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_swap_menu"
    bl_label = "Swap Nodes"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'CompositorNodeTree':
            layout.operator(NodesSwap.bl_idname, text = "Change to Switches").option = 'CompositorNodeSwitch'
            layout.operator(NodesSwap.bl_idname, text = "Change to Reroutes").option = 'NodeReroute'
        layout.operator(NodesSwap.bl_idname, text = "Change to Mix Nodes").option = 'NodeMixRGB'
        if type == 'CompositorNodeTree':
            layout.operator(NodesSwap.bl_idname, text = "Change to Alpha Over").option = 'CompositorNodeAlphaOver'
        layout.operator(NodesSwap.bl_idname, text = "Change to Math Nodes").option = 'NodeMath'


class LinkActiveToSelectedMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_link_active_to_selected_menu"
    bl_label = "Link Active to Selected"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.menu(LinkStandardMenu.bl_idname)
        layout.menu(LinkUseNamesMenu.bl_idname)


class LinkStandardMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_link_standard_menu"
    bl_label = "To All Selected"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links (Shift-F)").option = 'False False False'
        layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links (Ctrl-Shift-F)").option = 'True False False'



class LinkUseNamesMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_link_use_names_menu"
    bl_label = "Use Names/Labels..."

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.menu(LinkUseNodeNameMenu.bl_idname, text="Use Node Name/Label")
        layout.menu(LinkUseOutputsNamesMenu.bl_idname, text="Use Outputs Names")


class LinkUseNodeNameMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_link_use_node_name_menu"
    bl_label = "Use Node Name/Label"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links").option = 'True True False'
        layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links").option = 'False True False'


class LinkUseOutputsNamesMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_link_use_outputs_names_menu"
    bl_label = "Use Outputs Names"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links").option = 'True False True'
        layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links").option = 'False False True'


class NodeAlignMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_node_align_menu"
    bl_label = "Align Nodes"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        for opt in {'Horizontally', 'Vartically'}:
            layout.operator(AlignNodes.bl_idname, text=opt).option = opt


#############################################################
#  MENU ITEMS
#############################################################

def select_parent_children_buttons(self, context):
    layout = self.layout
    layout.operator(SelectParentChildren.bl_idname, text = 'Select frame\'s members (children)').option = "Children"
    layout.operator(SelectParentChildren.bl_idname, text = 'Select parent frame').option = "Parent"

#############################################################
#  REGISTER/UNREGISTER CLASSES AND KEYMAP ITEMS
#############################################################

addon_keymaps = []
# kmi_defs_operators entry: (operator, key, option_value, Ctrl, Shift, Alt)
kmi_defs_operators = (
    # MERGE NODES
    # MergeNodes with Ctrl (AUTO).
    (MergeNodes.bl_idname, 'NUMPAD_0', 'MIX AUTO', True, False, False),
    (MergeNodes.bl_idname, 'ZERO', 'MIX AUTO', True, False, False),
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', 'ADD AUTO', True, False, False),
    (MergeNodes.bl_idname, 'EQUAL', 'ADD AUTO', True, False, False),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'MULTIPLY AUTO', True, False, False),
    (MergeNodes.bl_idname, 'EIGHT', 'MULTIPLY AUTO', True, False, False),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', 'SUBTRACT AUTO', True, False, False),
    (MergeNodes.bl_idname, 'MINUS', 'SUBTRACT AUTO', True, False, False),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', 'DIVIDE AUTO', True, False, False),
    (MergeNodes.bl_idname, 'SLASH', 'DIVIDE AUTO', True, False, False),
    (MergeNodes.bl_idname, 'COMMA', 'LESS_THAN MATH', True, False, False),
    (MergeNodes.bl_idname, 'PERIOD', 'GREATER_THAN MATH', True, False, False),
    # MergeNodes with Ctrl Alt (MIX)
    (MergeNodes.bl_idname, 'NUMPAD_0', 'MIX MIX', True, False, True),
    (MergeNodes.bl_idname, 'ZERO', 'MIX MIX', True, False, True),
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', 'ADD MIX', True, False, True),
    (MergeNodes.bl_idname, 'EQUAL', 'ADD MIX', True, False, True),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'MULTIPLY MIX', True, False, True),
    (MergeNodes.bl_idname, 'EIGHT', 'MULTIPLY MIX', True, False, True),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', 'SUBTRACT MIX', True, False, True),
    (MergeNodes.bl_idname, 'MINUS', 'SUBTRACT MIX', True, False, True),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', 'DIVIDE MIX', True, False, True),
    (MergeNodes.bl_idname, 'SLASH', 'DIVIDE MIX', True, False, True),
    # MergeNodes with Ctrl Shift (MATH)
    (MergeNodes.bl_idname, 'NUMPAD_0', 'MIX MATH', True, True, False),
    (MergeNodes.bl_idname, 'ZERO', 'MIX MATH', True, True, False),
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', 'ADD MATH', True, True, False),
    (MergeNodes.bl_idname, 'EQUAL', 'ADD MATH', True, True, False),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'MULTIPLY MATH', True, True, False),
    (MergeNodes.bl_idname, 'EIGHT', 'MULTIPLY MATH', True, True, False),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', 'SUBTRACT MATH', True, True, False),
    (MergeNodes.bl_idname, 'MINUS', 'SUBTRACT MATH', True, True, False),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', 'DIVIDE MATH', True, True, False),
    (MergeNodes.bl_idname, 'SLASH', 'DIVIDE MATH', True, True, False),
    (MergeNodes.bl_idname, 'COMMA', 'LESS_THAN MATH', True, True, False),
    (MergeNodes.bl_idname, 'PERIOD', 'GREATER_THAN MATH', True, True, False),
    # BATCH CHANGE NODES
    # BatchChangeNodes with Alt
    (BatchChangeNodes.bl_idname, 'NUMPAD_0', 'MIX CURRENT', False, False, True),
    (BatchChangeNodes.bl_idname, 'ZERO', 'MIX CURRENT', False, False, True),
    (BatchChangeNodes.bl_idname, 'NUMPAD_PLUS', 'ADD ADD', False, False, True),
    (BatchChangeNodes.bl_idname, 'EQUAL', 'ADD ADD', False, False, True),
    (BatchChangeNodes.bl_idname, 'NUMPAD_ASTERIX', 'MULTIPLY MULTIPLY', False, False, True),
    (BatchChangeNodes.bl_idname, 'EIGHT', 'MULTIPLY MULTIPLY', False, False, True),
    (BatchChangeNodes.bl_idname, 'NUMPAD_MINUS', 'SUBTRACT SUBTRACT', False, False, True),
    (BatchChangeNodes.bl_idname, 'MINUS', 'SUBTRACT SUBTRACT', False, False, True),
    (BatchChangeNodes.bl_idname, 'NUMPAD_SLASH', 'DIVIDE DIVIDE', False, False, True),
    (BatchChangeNodes.bl_idname, 'SLASH', 'DIVIDE DIVIDE', False, False, True),
    (BatchChangeNodes.bl_idname, 'COMMA', 'CURRENT LESS_THAN', False, False, True),
    (BatchChangeNodes.bl_idname, 'PERIOD', 'CURRENT GREATER_THAN', False, False, True),
    (BatchChangeNodes.bl_idname, 'DOWN_ARROW', 'NEXT NEXT', False, False, True),
    (BatchChangeNodes.bl_idname, 'UP_ARROW', 'PREV PREV', False, False, True),
    # CHANGE MIX FACTOR
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', -0.1, False, False, True),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', 0.1,  False, False, True),
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', -0.01, False, True, True),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', 0.01, False, True, True),
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', 0.0, True, True, True),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', 1.0, True, True, True),
    (ChangeMixFactor.bl_idname, 'NUMPAD_0', 0.0, True, True, True),
    (ChangeMixFactor.bl_idname, 'ZERO', 0.0, True, True, True),
    (ChangeMixFactor.bl_idname, 'NUMPAD_1', 1.0, True, True, True),
    (ChangeMixFactor.bl_idname, 'ONE', 1.0, True, True, True),
    # CLEAR LABEL (Alt L)
    (NodesClearLabel.bl_idname, 'L', 'not confirmed', False, False, True),
    # ADD TEXTURE SETUP (Ctrl T)
    (NodesAddTextureSetup.bl_idname, 'T', '', True, False, False),
    # SELECT PARENT/CHILDREN
    # Select Children
    (SelectParentChildren.bl_idname, 'RIGHT_BRACKET', 'Children', False, False, False),
    # Select Parent
    (SelectParentChildren.bl_idname, 'LEFT_BRACKET', 'Parent', False, False, False),
    # LINK ACTIVE TO SELECTED
    # Don't use names, replace links (Ctrl Shift F)
    (NodesLinkActiveToSelected.bl_idname, 'F', 'True False False', True, True, False),
    # Don't use names, don't replace links (Shift F)
    (NodesLinkActiveToSelected.bl_idname, 'F', 'False False False', False, True, False),
    )

# kmi_defs_menus entry: (key, CTRL, SHIFT, ALT, menu_name)
kmi_defs_menus = (
    ('SPACE', True, False, False, EfficiencyToolsMenu.bl_idname),  # (Ctrl Space) - Main Menu
    ('SLASH', False, False, False, AddReroutesMenu.bl_idname),  # (Slash) - Add Reroutes Menu
    ('NUMPAD_SLASH', False, False, False, AddReroutesMenu.bl_idname),  # (Numpad Slash) - Add Reroutes Menu
    ('EQUAL', False, True, False, NodeAlignMenu.bl_idname),  # (Shift =) - Align Nodes Menu
    ('F', False, False, True, LinkUseNamesMenu.bl_idname),  # (Alt F) - Link Active To Selected using names/labels
    ('C', False, True, False, CopyToSelectedMenu.bl_idname),  # (Shift C) - Copy To Selected Menu
    ('S', False, True, False, NodesSwapMenu.bl_idname),  # (Shift S) - Swap Nodes Menu
    )

def register():
    bpy.utils.register_module(__name__)
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type = "NODE_EDITOR")
    
    # keymap items for operators
    for (operator, key, opt, CTRL, SHIFT, ALT) in kmi_defs_operators:
        kmi = km.keymap_items.new(operator, key, 'PRESS', ctrl = CTRL, shift = SHIFT, alt = ALT)
        kmi.properties.option = opt
        addon_keymaps.append((km, kmi))
    
    # keymap items for menus
    for (key, CTRL, SHIFT, ALT, menu_name) in kmi_defs_menus:
        kmi = km.keymap_items.new('wm.call_menu', key, 'PRESS', ctrl = CTRL, shift = SHIFT, alt = ALT)
        kmi.properties.name = menu_name
        addon_keymaps.append((km, kmi))
    
    # menu items
    bpy.types.NODE_MT_select.append(select_parent_children_buttons)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
    