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
    'version': (2, 0.06),
    'blender': (2, 6, 5),
    'location': "Node Editor Properties Panel (Ctrl-SPACE)",
    'description': "Nodes Efficiency Tools",
    'warning': "", 
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Nodes_Efficiency_Tools",
    'tracker_url': "http://projects.blender.org/tracker/?func=detail&atid=468&aid=33543&group_id=153",
    'category': "Node",
    }

import bpy
from bpy.props import EnumProperty, StringProperty

#################
# rl_outputs:
# list of outputs of Input Render Layer
# with attributes determinig if pass is used,
# and MultiLayer EXR outputs names and corresponding render engines
#
# rl_outputs entry = [render_pass, rl_output_name, exr_output_name, in_internal, in_cycles]
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
    space_tree = space.node_tree
    tree = space_tree
    nodes = tree.nodes
    links = tree.links
    active = nodes.active
    selected = [node for node in nodes if node.select]
    context_active = context.active_node
    context_selected = context.selected_nodes
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
    
    combo = StringProperty(
        name = "Combo",
        description = "BlendType/ShaderKind/MathOperation and Node Kind",
        )
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        combo_split = self.combo.split( )
        mode = combo_split[0]
        node_kind = combo_split[1]  # kinds: 'AUTO', 'SHADER', 'MIX', 'MATH'
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
                        if node.outputs[0].type == type and mode in the_list:
                            dst.append([i, node.location.x, node.location.y])
                else:
                    for (kind, the_list, dst) in (
                        ('MIX', blend_types, selected_mix),
                        ('SHADER', merge_shaders, selected_shader),
                        ('MATH', operations, selected_math),
                        ):
                        if node_kind == kind and mode in the_list:
                            dst.append([i, node.location.x, node.location.y])
                    

        for the_list in [selected_mix, selected_shader, selected_math]:
            if len(the_list) > 1:
                count_before = len(nodes)
                # sort list by loc_x - reversed
                the_list.sort(key = lambda k: k[1], reverse = True)
                # get maximum loc_x
                loc_x = the_list[0][1] + 300.0
                the_list.sort(key = lambda k: k[2], reverse = True)
                loc_y = the_list[len(the_list) - 1][2]
                offset_y = 40.0
                if the_list == selected_shader:
                    offset_y = 150.0
                add_nodes = []
                for i in range(len(the_list)-1):
                    if the_list == selected_mix:
                        add = nodes.new('MIX_RGB')
                        add.blend_type = mode
                        add.show_preview = False
                        add.hide = True
                        first = 1
                        second = 2
                        if hasattr(add, 'width_hidden'):
                            add.width_hidden = 100.0
                    elif the_list == selected_math:
                        add = nodes.new('MATH')
                        add.operation = mode
                        add.hide = True
                        first = 0
                        second = 1
                        if hasattr(add, 'width_hidden'):
                            add.width_hidden = 100.0
                    elif the_list == selected_shader:
                        if mode == 'MIX':
                            add = nodes.new('MIX_SHADER')
                            first = 1
                            second = 2
                            if hasattr(add, 'width_hidden'):
                                add.width_hidden = 100.0
                        elif mode == 'ADD':
                            add = nodes.new('ADD_SHADER')
                            first = 0
                            second = 1
                            if hasattr(add, 'width_hidden'):
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
    
    combo = StringProperty(
        name = "Combo",
        description = "Mix Blend Type and Math Operation"
        )
        
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        navs = ('CURRENT', 'NEXT', 'PREV')
        combo_split = self.combo.split( )
        blend_type = combo_split[0]
        operation = combo_split[1]
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
    
    change = StringProperty(
        name = "Fac_Change",
        description = "Factor Change",
        )
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        change = float(self.change)
        selected = []  # entry = index
        for si, node in enumerate(nodes):
            if node.select:
                if node.type in {'MIX_RGB', 'MIX_SHADER'}:
                    selected.append(si)
                
        for si in selected:
            fac = nodes[si].inputs[0]
            nodes[si].hide = False
            if change in {0.0, 1.0}:
                fac.default_value = change
            else:
                fac.default_value += change
        
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
        n_index = len(nodes)  # get index of new node when added
        active = nodes.active
        selected_i = []  # entry = node index
        selected_same_type_i = []  # entry = node index
        reconnects = []  #entry = [old index, new index]
        old_links = []
        new_links = []
        
        for si, node in enumerate(nodes):
            if node.select:
                selected_i.append(si)  # will be used to restore selection
                if active.type == node.type and node != active:
                    selected_same_type_i.append(si)
        
        for si in selected_same_type_i:
            bpy.ops.node.select_all(action = 'DESELECT')
            nodes.active = active
            active.select = True
            bpy.ops.node.duplicate()
            copied = nodes.active
            copied.hide = nodes[si].hide
            copied.show_preview = nodes[si].show_preview
            copied.mute = nodes[si].mute
            copied.label = nodes[si].label
            copied.use_custom_color = nodes[si].use_custom_color
            copied.color = nodes[si].color
            if copied.parent:
                bpy.ops.node.parent_clear()
            locx = nodes[si].location.x
            locy = nodes[si].location.y
            # get absolute nodes[si] location
            parent = nodes[si].parent
            while parent:
                locx += parent.location.x
                locy += parent.location.y
                parent = parent.parent
            copied.location = [locx, locy]
            reconnects.append([si, n_index])
            n_index += 1

        for li, link in enumerate(links):
            from_node = None
            from_socket = None
            to_node = None
            to_socket = None
            for ni in selected_same_type_i:
                if link.from_node == nodes[ni]:
                    from_node = ni
                    for oi, output in enumerate(nodes[ni].outputs):
                        if link.from_socket == output:
                            from_socket = oi
                            break
                    for nj in range (len(nodes)):
                        if link.to_node == nodes[nj]:
                            to_node = nj
                            for ii, input in enumerate(nodes[nj].inputs):
                                if link.to_socket == input:
                                    to_socket = ii
                    entry = [from_node, from_socket, to_node, to_socket]
                    if entry not in old_links:
                        old_links.append(entry)
                elif link.to_node == nodes[ni]:
                    to_node = ni
                    for ii, input in enumerate(nodes[ni].inputs):
                        if link.to_socket == input:
                            to_socket = ii
                            break
                    for nj in range (len(nodes)):
                        if link.from_node == nodes[nj]:
                            from_node = nj
                            for oi, output in enumerate(nodes[nj].outputs):
                                if link.from_socket == output:
                                    from_socket = oi
                    entry = [from_node, from_socket, to_node, to_socket]
                    if entry not in old_links:
                        old_links.append(entry)
        
        for i, [fn, fs, tn, ts] in enumerate(old_links):
            for [old_i, new_i] in reconnects:
                if fn == old_i:
                    fn = new_i
                if tn == old_i:
                    tn = new_i
            new_links.append([fn, fs, tn, ts])
        
        for [fn, fs, tn, ts] in new_links:
            links.new(nodes[fn].outputs[fs], nodes[tn].inputs[ts])
                       
        # clean up
        bpy.ops.node.select_all(action = 'DESELECT')
        for i in selected_same_type_i:
            nodes[i].select = True
        bpy.ops.node.delete()
        for i in selected_i:
            nodes[i].select = True
        nodes.active = active
        
        return {'FINISHED'}


class NodesCopyLabel(bpy.types.Operator):
    bl_idname = "node.copy_label"
    bl_label = "Copy Label of Active Node to Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None and context.active_node is not None
    
    def execute(self, context):
        set_convenience_variables(context)
        selected = []
        active = nodes.active
        for si, node in enumerate(nodes):
            if node.select and node != active:
                selected.append(si)
        src_label = active.label
        for si in selected:
            nodes[si].label = src_label
        
        return {'FINISHED'}


class NodesAddTextureSetup(bpy.types.Operator):
    bl_idname = "node.add_texture"
    bl_label = "Add Texture Node to Active Node Input"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'SHADER' and space.node_tree is not None:
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
            tex = nodes.new('TEX_IMAGE')
            tex.location = [locx - 200.0, locy + 28.0]
            map = nodes.new('MAPPING')
            map.location = [locx - 490.0, locy + 80.0]
            coord = nodes.new('TEX_COORD')
            coord.location = [locx - 700, locy + 40.0]
            active.select = False
            nodes.active = tex
            
            links.new(tex.outputs[0], active.inputs[0])
            links.new(map.outputs[0], tex.inputs[0])
            links.new(coord.outputs[2], map.inputs[0])
            
        return {'FINISHED'}


class AddSwitchesToNodesOutputs(bpy.types.Operator):
    bl_idname = "node.switches_to_outputs"
    bl_label = "Add Switches to Links"
    bl_options = {'REGISTER', 'UNDO'}
    
    name_options = ['Nodes names', 'Outputs names', 'Nodes and Outputs names']
    naming = []
    for n in name_options:
        naming.append((n, n, n))
    
    naming = EnumProperty(
        name = "naming",
        description = "Name nodes using...",
        items = naming
        )
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'COMPOSITING' and space.node_tree is not None:
                valid = True
        return valid
    
    def execute(self, context):
        set_convenience_variables(context)
        n_index = len(nodes) - 1  # get index of last node in nodes' list before script execution
        selected_i = []  # entry = node index
        new_links = []  # entry = [to node index, input index, from node index, output index]
        reconnects = []  # entry [old from node index, old from output index, new node index] - used to reconnect links
        
        # append selected nodes' indexes to selected_i
        for node_i, node in enumerate(nodes):
            if node.select:
                selected_i.append(node_i)
        
        # create new nodes and append entries for new links - from selected to new nodes
        for si in selected_i:
            node = nodes[si]
            name = node.name
            # if node has label - use it instead of its name
            if node.label:
                name = node.label
            x = node.location.x + 400.0
            y = node.location.y
            y_offset = -50.0
            loc = [x, y]
            # if analyzed node's output is linked - add node and "connect" to output
            for out_i, output in enumerate(node.outputs):
                pass_used = False  # initial value to be analyzed if 'R_LAYERS'
                # if node is not 'R_LAYERS' - "is_pass_used" not needed, so set it to True
                if node.type != 'R_LAYERS':
                    pass_used = True
                else:  # if 'R_LAYERS' check if output represent used render pass
                    node_scene = node.scene
                    node_layer = node.layer
                    # If output - "Alpha" is analyzed - assume it's used. Not represented in passes.
                    if output.name == 'Alpha':
                        pass_used = True
                    else:
                        for [render_pass, out_name, exr_name, in_internal, in_cycles] in rl_outputs:
                            if output.name == out_name:
                                pass_used = getattr(node_scene.render.layers[node_layer], render_pass)
                                break
                if pass_used:
                    n = nodes.new('SWITCH')
                    n.hide = True
                    if self.naming == 'Nodes names':
                        n.label = name
                    elif self.naming == 'Outputs names':
                        n.label = output.name
                    else:
                        n.label = name + '_' + output.name
                    if hasattr(n, 'width_hidden'):
                        n.width_hidden = 100.0
                    n.location = loc
                    y += y_offset 
                    loc = [x, y]
                    n_index += 1  # new node appeared. It's given the index of previous last index plus 1
                    to_node = n_index
                    to_input = 0  # new node has only one input, so index of 0 will be used
                    from_node = node.name  # get name of nodes[si]
                    from_output = out_i
                    # append entry to new_links. new links will be made afterwards in one loop
                    new_links.append([to_node, to_input, from_node, from_output])
                    # append entries to "reconnects" so that in next "for si" loop proper connections can be made
                    reconnects.append([si, from_output, n_index])
            # disselect the node so that after execution of script only newly created nodes are selected
            node.select = False
        
        # create entries for new links - from new nodes to old inputs
        # analyze all for every link. len(links) is rather greater than len(selected_i),
        # so less entries is required this way
        for link in links:
            for si in selected_i:
                if link.from_node == nodes[si]:
                    # if link "li" is linked from node "si" create new entry for new_links
                    new_link = []
                    to_node = link.to_node
                    to_node_name = to_node.name
                    # analyze "to_node" inputs
                    for in_i, input in enumerate(to_node.inputs):
                        if input == link.to_socket:
                            # create first 2 of 4 entries in "new_link"
                            # when creating links - nodes' indexes can be used, but names as well
                            new_link.append(to_node_name)
                            new_link.append(in_i)
                    # analyze nodes[si] outputs if they are part of link "li"
                    for out_i, output in enumerate(nodes[si].outputs):
                        if link.from_socket == nodes[si].outputs[out_i]:
                            # if so: check "new_nodes" entries and create last 2 of 4 entries in "new_link"
                            for [old_node_i, old_out_i, new_node_i] in reconnects:
                                if old_node_i == si:
                                    if out_i == old_out_i:
                                        new_link.append(new_node_i)
                                        # new nodes have only one output, so index 0 will always be correct
                                        new_link.append(0)
                    # append newly created entry to "new_links" list
                    new_links.append(new_link)
        
        # create all new links:
        # From linked outs of selected nodes to newly created nodes (created in first loop when new nodes were added)
        # From new nodes to old inputs (created in 2nd loop when links were analyzed and selected nodes for each link)
        for [to_node, to_input, from_node, from_output] in new_links:
            links.new(nodes[to_node].inputs[to_input], nodes[from_node].outputs[from_output])
        
        nodes.active = nodes[n_index]  # make the last of newly created nodes active
        return {'FINISHED'}


class NodesLinkActiveToSelected(bpy.types.Operator):
    bl_idname = "node.link_active_to_selected"
    bl_label = "Link Active Node to Selected"
    bl_options = {'REGISTER', 'UNDO'}
    
    options = []
    options_list = ['Nodes Names', 'Nodes Location', 'First Output Only',]
    for opt in options_list:
        options.append((opt, opt, opt))
    
    option = EnumProperty(
        name = "option",
        description = "Option",
        items = options
        )
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'COMPOSITING' and space.node_tree is not None and context.active_node is not None:
                valid = True
        return valid
    
    def execute(self, context):
        set_convenience_variables(context)
        option = self.option
        active = nodes.active
        selected = []  # entry = [node index, node locacion.x, node.location.y]
        for i, node in enumerate(nodes):
            is_selected = node.select
            is_not_active = node != active
            has_inputs = len(node.inputs) > 0
            is_valid = is_selected and is_not_active and has_inputs
            if is_valid:
                selected.append([i, node.location.x, node.location.y])
        selected.sort(key = lambda k: (-k[2], k[1]))
        if active:
            if active.select:
                outputs = []
                for i, out in enumerate(active.outputs):
                    if active.type != 'R_LAYERS':
                        outputs.append(i)
                    else:
                        for [render_pass, out_name, exr_name, in_internal, in_cycles] in rl_outputs:
                            pass_used = False
                            if out.name == 'Alpha':
                                pass_used = True
                            elif out.name == out_name:
                                pass_used = getattr(node.scene.render.layers[node.layer], render_pass)
                                break
                        if pass_used:
                            outputs.append(i)
                if len(outputs) > 0:
                    if option == 'Nodes Names':
                        for i, out in enumerate(outputs):
                            for [ni, x, y] in selected:
                                name = nodes[ni].name
                                l = len(nodes[ni].inputs)
                                if nodes[ni].label:
                                    name = nodes[ni].label
                                for [render_pass, out_name, exr_name, in_internal, in_cycles] in rl_outputs:
                                    if name in {out_name, exr_name}:
                                        names = [out_name, exr_name]
                                        break
                                    else:
                                        names = [name]
                                if len(outputs) > 1:
                                    if active.outputs[out].name in names:
                                        out_type = active.outputs[out].type
                                        input_i = 0
                                        if (nodes[ni].inputs[0].type != out_type and l > 1):
                                            for ii in range (1, l):
                                                if nodes[ni].inputs[ii].type == out_type:
                                                    input_i = ii
                                                    break
                                        links.new(active.outputs[out], nodes[ni].inputs[input_i])
                                else:
                                    a_name = active.name
                                    if active.label:
                                        a_name = active.label
                                    if a_name in names:
                                        out_type = active.outputs[0].type
                                        input_i = 0
                                        if (nodes[ni].inputs[0].type != out_type and l > 1):
                                            for ii in range (1, l):
                                                if nodes[ni].inputs[ii].type == out_type:
                                                    input_i = ii
                                                    break
                                        links.new(active.outputs[0], nodes[ni].inputs[input_i])
                    elif option == 'Nodes Location':
                        for i, out in enumerate(outputs):
                            if i < len(selected):
                                out_type = active.outputs[out].type
                                l = len(nodes[selected[i][0]].inputs)
                                input_i = 0
                                if (nodes[selected[i][0]].inputs[0].type != out_type and l > 1):
                                    for ii in range (1, l):
                                        if nodes[selected[i][0]].inputs[ii].type == out_type:
                                            input_i = ii
                                            break
                                links.new(active.outputs[out], nodes[selected[i][0]].inputs[input_i])
                    elif option == 'First Output Only':
                        out_type = active.outputs[0].type
                        for [ni, x, y] in selected:
                            l = len(nodes[ni].inputs)
                            input_i = 0
                            if (nodes[ni].inputs[0].type != out_type and l > 1):
                                for ii in range (1, l):
                                    if nodes[ni].inputs[ii].type == out_type:
                                        input_i = ii
                                        break
                            links.new(active.outputs[0], nodes[ni].inputs[input_i])

        return {'FINISHED'}            


class AlignNodes(bpy.types.Operator):
    bl_idname = "node.align_nodes"
    bl_label = "Align nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    axes = []
    axes_list = ['Vertically', 'Horizontally']
    for axis in axes_list:
        axes.append((axis, axis, axis))
    
    align_axis = EnumProperty(
        name = "align_axis",
        description = "Align Axis",
        items = axes
        )
    
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
            helper = nodes.new('REROUTE')
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
            
            if self.align_axis == 'Vertically':
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
    
    option = StringProperty(
        name = "option",
        description = "Parent/Children",
        )
    
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
        if type == 'SHADER':
            box.operator(NodesAddTextureSetup.bl_idname, text = 'Add Image Texture (Ctrl T)')
        box.menu(BatchChangeNodesMenu.bl_idname, text = 'Batch Change...')
        box.operator_menu_enum(AlignNodes.bl_idname, "align_axis", text = "Align Nodes (Shift =)")
        box.menu(CopyNodePropertiesMenu.bl_idname, text = 'Copy Active to Selected (Shift-C)')
        if type == 'COMPOSITING':
            box = layout.box()
            box.label('Add Switches to Outputs (Ctrl /):')
            row = box.row()
            row.operator_menu_enum(AddSwitchesToNodesOutputs.bl_idname, "naming", text = 'Base Names on')
            
            box = layout.box()
            box.label('Link Active to Selected (Shift F)')
            box.operator_menu_enum(NodesLinkActiveToSelected.bl_idname, "option", text = "Basing on")


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
        if type == 'SHADER':
            layout.operator(NodesAddTextureSetup.bl_idname, text = 'Add Image Texture with coordinates')
        layout.menu(BatchChangeNodesMenu.bl_idname, text = 'Batch Change')
        layout.operator_menu_enum(
            AlignNodes.bl_idname,
            property="align_axis",
            text="Align Nodes",
            )
        layout.menu(CopyNodePropertiesMenu.bl_idname, text = 'Copy Active to Selected       Shift C')
        if type == 'COMPOSITING':
            layout.operator_menu_enum(
                AddSwitchesToNodesOutputs.bl_idname,
                property = "naming",
                text = 'Add Switches to Outputs. Names base:',
                )
            layout.operator_menu_enum(
                NodesLinkActiveToSelected.bl_idname,
                property = "option",
                text = "Link Active to Selected basing on",
                )


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
        if type == 'SHADER':
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
            combo = type + ' SHADER'
            layout.operator(MergeNodes.bl_idname, text = type).combo = combo


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
            combo = type + ' MIX'
            layout.operator(MergeNodes.bl_idname, text = type).combo = combo        


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
            combo = type + ' MATH'
            layout.operator(MergeNodes.bl_idname, text = type).combo = combo


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
            combo = blend_type + ' CURRENT'
            layout.operator(BatchChangeNodes.bl_idname, text = blend_type).combo = combo


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
            combo = 'CURRENT ' + operation
            layout.operator(BatchChangeNodes.bl_idname, text = operation).combo = combo
                                  

class CopyNodePropertiesMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_copy_node_properties_menu"
    bl_label = "Copy Active Node's Properties to Selected"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesCopySettings.bl_idname, text = 'Copy Settings')
        layout.operator(NodesCopyLabel.bl_idname, text = 'Copy Label')


class LinkActiveToSelectedMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_link_active_to_selected_menu"
    bl_label = "Link Active To Selected"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None

    def draw(self, context):
        layout = self.layout
        layout.operator_menu_enum(
            NodesLinkActiveToSelected.bl_idname,
            property="option",
            text="Basing on...",
            )


class NodeAlignMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_node_align_menu"
    bl_label = "Align Nodes"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.operator_menu_enum(
            AlignNodes.bl_idname,
            property="align_axis",
            text="Direction...",
            )


class SwitchesToOutputsMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_switches_to_outputs_menu"
    bl_label = "Add Switches to Outputs"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None
    
    def draw(self, context):
        layout = self.layout
        layout.operator_menu_enum(
            AddSwitchesToNodesOutputs.bl_idname,
            property="naming",
            text="Name Switches using...",
            )

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

def register():
    bpy.utils.register_module(__name__)
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type = "NODE_EDITOR")

    kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS', ctrl = True)
    kmi.properties.name = EfficiencyToolsMenu.bl_idname
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_0', 'PRESS', ctrl = True)
    kmi.properties.combo = 'MIX AUTO'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', ctrl = True)
    kmi.properties.combo = 'ADD AUTO'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl = True)
    kmi.properties.combo = 'MULTIPLY AUTO'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', ctrl = True)
    kmi.properties.combo = 'SUBTRACT AUTO'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', ctrl = True)
    kmi.properties.combo = 'DIVIDE AUTO'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_0', 'PRESS', ctrl = True, alt = True)
    kmi.properties.combo = 'MIX MIX'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', ctrl = True, alt = True)
    kmi.properties.combo = 'ADD MIX'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl = True, alt = True)
    kmi.properties.combo = 'MULTIPLY MIX'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', ctrl = True, alt = True)
    kmi.properties.combo = 'SUBTRACT MIX'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', ctrl = True, alt = True)
    kmi.properties.combo = 'DIVIDE MIX'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', ctrl = True, shift = True)
    kmi.properties.combo = 'ADD MATH'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl = True, shift = True)
    kmi.properties.combo = 'MULTIPLY MATH'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', ctrl = True, shift = True)
    kmi.properties.combo = 'SUBTRACT MATH'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', ctrl = True, shift = True)
    kmi.properties.combo = 'DIVIDE MATH'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'COMMA', 'PRESS', ctrl = True, shift = True)
    kmi.properties.combo = 'LESS_THAN MATH'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(MergeNodes.bl_idname, 'PERIOD', 'PRESS', ctrl = True, shift = True)
    kmi.properties.combo = 'GREATER_THAN MATH'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'NUMPAD_0', 'PRESS', alt = True)
    kmi.properties.combo = 'MIX CURRENT'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', alt = True)
    kmi.properties.combo = 'ADD ADD'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', alt = True)
    kmi.properties.combo = 'MULTIPLY MULTIPLY'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', alt = True)
    kmi.properties.combo = 'SUBTRACT SUBTRACT'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', alt = True)
    kmi.properties.combo = 'DIVIDE DIVIDE'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'DOWN_ARROW', 'PRESS', alt = True)
    kmi.properties.combo = 'NEXT NEXT'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'UP_ARROW', 'PRESS', alt = True)
    kmi.properties.combo = 'PREV PREV'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'COMMA', 'PRESS', alt = True)
    kmi.properties.combo = 'CURRENT LESS_THAN'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(BatchChangeNodes.bl_idname, 'PERIOD', 'PRESS', alt = True)
    kmi.properties.combo = 'CURRENT GREATER_THAN'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS', alt = True)
    kmi.properties.change = '-0.1'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS', alt = True)
    kmi.properties.change = '0.1'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS', alt = True, shift = True)
    kmi.properties.change = '-0.01'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS', alt = True, shift = True)
    kmi.properties.change = '0.01'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS', ctrl = True, alt = True, shift = True)
    kmi.properties.change = '0.0'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS', ctrl = True, alt = True, shift = True)
    kmi.properties.change = '1.0'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'NUMPAD_0', 'PRESS', ctrl = True, alt = True, shift = True)
    kmi.properties.change = '0.0'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(ChangeMixFactor.bl_idname, 'NUMPAD_1', 'PRESS', ctrl = True, alt = True, shift = True)
    kmi.properties.change = '1.0'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('wm.call_menu', 'SLASH', 'PRESS', ctrl = True)
    kmi.properties.name = SwitchesToOutputsMenu.bl_idname
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('wm.call_menu', 'EQUAL', 'PRESS', shift = True)
    kmi.properties.name = NodeAlignMenu.bl_idname
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('wm.call_menu', 'F', 'PRESS', shift = True)
    kmi.properties.name = LinkActiveToSelectedMenu.bl_idname
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('wm.call_menu', 'C', 'PRESS', shift = True)
    kmi.properties.name = CopyNodePropertiesMenu.bl_idname
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new('wm.call_menu', 'C', 'PRESS', ctrl = True, shift = True)
    kmi.properties.name = CopyNodePropertiesMenu.bl_idname
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(NodesAddTextureSetup.bl_idname, 'T', 'PRESS', ctrl = True)
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(SelectParentChildren.bl_idname, 'RIGHT_BRACKET', 'PRESS')
    kmi.properties.option = 'Children'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new(SelectParentChildren.bl_idname, 'LEFT_BRACKET', 'PRESS')
    kmi.properties.option = 'Parent'
    addon_keymaps.append((km, kmi))
    
    bpy.types.NODE_MT_select.append(select_parent_children_buttons)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()