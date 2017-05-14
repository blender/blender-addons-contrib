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
    "name": "A.N.T. Displace",
    "author": "Jimmy Hazevoet",
    "version": (0, 1, 6),
    "blender": (2, 77, 0),
    "location": "View3D > Tool Shelf",
    "description": "Another Noise Tool: Displace vertices of selected mesh",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Add_Mesh/ANT_Landscape",
    "category": "Mesh",
}

"""
# -------------------------------------------------------------
- UPDATE: A.N.T. Displace - Version 0,1,6 (5/2017)
# -------------------------------------------------------------
                - NEW:
                -
                - Displace vertices of selected mesh
                - Use Blender internal texture data block - texture nodes
                - Use vertex group weight of active group
                - Slope map, z normal to vertex group weight,
                    and optional select vertices on flat area's
                - Use Blender internal texture data block - texture nodes
                - Noise variations (from old A.N.T. Blender-2.49 addon)
                - Variable X, Y, Z noise Size and Offset
                - Plateau and Sealevel renamed to Maximum and Minimum 
                -
# -------------------------------------------------------------
# Another Noise Tool: Vert Displace Version
# -------------------------------------------------------------
MESH OPTIONS:
Mesh update:     Turn this on for interactive mesh refresh.
Vertex Group:    Slope map, z normal value to vertex group weight,
                    and select vertices on flat area's

NOISE OPTIONS: ( Many of these options are the same as in blender textures. )
X_Offset:        Noise x offset in blender units (make tiled terrain)
Y_Offset:        Noise y offset in blender units
Random seed:     Use this to randomise the origin of the noise function.
Noise size:      Size of the noise.
Noise type:      Available noise types: multiFractal, ridgedMFractal, fBm, hybridMFractal, heteroTerrain,
                 Turbulence, Distorted Noise, Marble, Shattered_hTerrain, Strata_hTerrain, Planet_noise
Noise basis:     Blender, Perlin, NewPerlin, Voronoi_F1, Voronoi_F2, Voronoi_F3, Voronoi_F4, Voronoi_F2-F1,
                 Voronoi Crackle, Cellnoise
Distortion:      Distortion amount.
Hard:            Hard/Soft turbulence noise.
Depth:           Noise depth, number of frequencies in the fBm.
Dimension:       Musgrave: Fractal dimension of the roughest areas.
Lacunarity:      Musgrave: Gap between successive frequencies.
Offset:          Musgrave: Raises the terrain from sea level.
Gain:            Musgrave: Scale factor.
Marble Bias:     Sin, Tri, Saw
Marble Sharpnes: Soft, Sharp, Sharper
Marble Shape:    Shape of the marble function: Default, Ring, Swirl, Bumps, Wave, X, Y

TERRAIN OPTIONS:
Height:          Scale terrain height.
Invert:          Invert terrain height.
Offset:          Terrain height offset.
Seabed:          Flattens terrain at seabed level.
Plateau:         Flattens terrain at plateau level.
Strata:          Strata amount, number of strata / terrace layers.
Strata type:     Strata types, Smooth, Sharp-sub, Sharp-add, Quantize
Vertex Group:    Use vertex group weight
"""

# ------------------------------------------------------------
# import modules
import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        StringProperty,
        FloatVectorProperty,
        )
from mathutils import Vector
from mathutils.noise import (
        seed_set,
        turbulence,
        turbulence_vector,
        fractal,
        hybrid_multi_fractal,
        multi_fractal,
        ridged_multi_fractal,
        hetero_terrain,
        random_unit_vector,
        variable_lacunarity,
        )
from math import (
        floor, sqrt,
        sin, cos, pi,
        )

# ------------------------------------------------------------
# some functions for marble_noise
def sin_bias(a):
    return 0.5 + 0.5 * sin(a)


def cos_bias(a):
    return 0.5 + 0.5 * cos(a)


def tri_bias(a):
    b = 2 * pi
    a = 1 - 2 * abs(floor((a * (1 / b)) + 0.5) - (a * (1 / b)))
    return a


def saw_bias(a):
    b = 2 * pi
    n = int(a / b)
    a -= n * b
    if a < 0:
        a += b
    return a / b


def soft(a):
    return a


def sharp(a):
    return a**0.5


def sharper(a):
    return sharp(sharp(a))


def shapes(x, y, shape=0):
    p = pi
    if shape is 1:
        # ring
        x = x * p
        y = y * p
        s = cos(x**2 + y**2) / (x**2 + y**2 + 0.5)
    elif shape is 2:
        # swirl
        x = x * p
        y = y * p
        s = ((x * sin(x * x + y * y) + y * cos(x * x + y * y)) / (x**2 + y**2 + 0.5))
    elif shape is 3:
        # bumps
        x = x * p
        y = y * p
        s = ((cos(x * p) + cos(y * p)) - 0.5)
    elif shape is 4:
        # wave
        x = x * p * 2
        y = y * p * 2
        s = sin(x + sin(y))
    elif shape is 5:
        # y grad.
        s = (y * p)
    elif shape is 6:
        # x grad.
        s = (x * p)
    else:
        # marble default
        s = ((x + y) * 5)
    return s


# marble_noise
def marble_noise(x, y, z, origin, size, shape, bias, sharpnes, turb, depth, hard, basis, amp, freq):

    s = shapes(x, y, shape)
    x += origin[0]
    y += origin[1]
    z += origin[2]
    value = s + turb * turbulence_vector((x, y, z), depth, hard, basis)[2]

    if bias is 1:
        value = cos_bias(value)
    if bias is 2:
        value = tri_bias(value)
    elif bias is 3:
        value = saw_bias(value)
    else:
        value = sin_bias(value)

    if sharpnes is 1:
        value = 1.0 - sharp(value)
    elif sharpnes is 2:
        value = 1.0 - sharper(value)
    elif sharpnes is 3:
        value = soft(value)
    elif sharpnes is 4:
        value = sharp(value)
    elif sharpnes is 5:
        value = sharper(value)
    else:
        value = 1.0 - soft(value)

    return value

# ------------------------------------------------------------
# custom noise types

# vl_noise_turbulence: 
def vlnTurbMode(coords, distort, basis, vlbasis, hardnoise):
    # hard noise
    if hardnoise:
        return (abs(-variable_lacunarity(coords, distort, basis, vlbasis)))
    # soft noise
    else:
        return variable_lacunarity(coords, distort, basis, vlbasis)


def vl_noise_turbulence(coords, distort, depth, basis, vlbasis, hardnoise, amp, freq):
    x, y, z = coords
    value = vlnTurbMode(coords, distort, basis, vlbasis, hardnoise)
    i=0
    for i in range(depth):
        i+=1
        value += vlnTurbMode((x * (freq * i), y * (freq * i), z * (freq * i)), distort, basis, vlbasis, hardnoise) * (amp * 0.5 / i)
    return value


## duo_multiFractal:
def double_multiFractal(coords, H, lacunarity, octaves, offset, gain, basis, vlbasis):
    x, y, z = coords
    n1 = multi_fractal((x * 1.5 + 1, y * 1.5 + 1, z * 1.5 + 1), 1.0, 1.0, 1.0, basis) * (offset * 0.5)
    n2 = multi_fractal((x - 1, y - 1, z - 1), H, lacunarity, octaves, vlbasis) * (gain * 0.5)
    return (n1 * n1 + n2 * n2) * 0.5


## distorted_heteroTerrain:
def distorted_heteroTerrain(coords, H, lacunarity, octaves, offset, distort, basis, vlbasis):
    x, y, z = coords
    h1 = (hetero_terrain((x, y, z), 1.0, 2.0, 1.0, 1.0, basis) * 0.5)
    d =  h1 * distort * 2
    h2 = (hetero_terrain((x + d, y + d, z + d), H, lacunarity, octaves, offset, vlbasis) * 0.25)
    return (h1 * h1 + h2 * h2) * 0.5


## SlickRock:
def slick_rock(coords, H, lacunarity, octaves, offset, gain, distort, basis, vlbasis):
    x, y, z = coords
    n = multi_fractal((x,y,z), 1.0, 2.0, 2.0, basis) * distort * 0.5
    r = ridged_multi_fractal((x + n, y + n, z + n), H, lacunarity, octaves, offset + 0.1, gain * 2, vlbasis)
    return (n + (n * r)) * 0.5


## vlhTerrain
def vl_hTerrain(coords, H, lacunarity, octaves, offset, basis, vlbasis, distort):
    x, y, z = coords
    ht = hetero_terrain((x, y, z), H, lacunarity, octaves, offset, basis ) * 0.25
    vl = ht * variable_lacunarity((x, y, z), distort, basis, vlbasis) * 0.5 + 0.5
    return vl * ht


# another turbulence
def ant_turbulence(coords, depth, hardnoise, nbasis, amp, freq, distortion):
    x, y, z = coords
    tv = turbulence_vector((x+1, y+2, z+3), depth, hardnoise, nbasis, amp, freq)
    d = (distortion * tv[0]) * 0.25
    return (d + ((tv[0] - tv[1]) * (tv[2])**2))


# shattered_hterrain:
def shattered_hterrain(coords, H, lacunarity, octaves, offset, distort, basis):
    x, y, z = coords
    d = (turbulence_vector(coords, 6, 0, 0)[0] * 0.5 + 0.5) * distort * 0.5
    t1 = (turbulence_vector((x + d, y + d, z + d), 0, 0, 7)[0] + 0.5)
    t2 = (hetero_terrain((x * 2, y * 2, z * 2), H, lacunarity, octaves, offset, basis) * 0.5)
    return ((t1 * t2) + t2 * 0.5) * 0.5


# strata_hterrain
def strata_hterrain(coords, H, lacunarity, octaves, offset, distort, basis):
    x, y, z = coords
    value = hetero_terrain((x, y, z), H, lacunarity, octaves, offset, basis) * 0.5
    steps = (sin(value * (distort * 5) * pi) * (0.1 / (distort * 5) * pi))
    return (value * (1.0 - 0.5) + steps * 0.5)


# planet_noise by Farsthary: https://farsthary.com/2010/11/24/new-planet-procedural-texture/
def planet_noise(coords, oct=6, hard=0, noisebasis=1, nabla=0.001):
    x, y, z = coords
    d = 0.001
    offset = nabla * 1000
    x = turbulence((x, y, z), oct, hard, noisebasis)
    y = turbulence((x + offset, y, z), oct, hard, noisebasis)
    z = turbulence((x, y + offset, z), oct, hard, noisebasis)
    xdy = x - turbulence((x, y + d, z), oct, hard, noisebasis)
    xdz = x - turbulence((x, y, z + d), oct, hard, noisebasis)
    ydx = y - turbulence((x + d, y, z), oct, hard, noisebasis)
    ydz = y - turbulence((x, y, z + d), oct, hard, noisebasis)
    zdx = z - turbulence((x + d, y, z), oct, hard, noisebasis)
    zdy = z - turbulence((x, y + d, z), oct, hard, noisebasis)
    return (zdy - ydz), (zdx - xdz), (ydx - xdy)


# ------------------------------------------------------------
# noise_gen
def noise_gen(coords, props):

    rseed = props[0]
    nsize = props[1]
    ntype = props[2]
    nbasis = int(props[3][0])
    vlbasis = int(props[4][0])
    distortion = props[5]
    hardnoise = int(props[6])
    depth = props[7]
    dimension = props[8]
    lacunarity = props[9]
    offset = props[10]
    gain = props[11]
    marblebias = int(props[12][0])
    marblesharpnes = int(props[13][0])
    marbleshape = int(props[14][0])
    invert = props[15]
    height = props[16]
    heightoffset = props[17]
    minimum = props[18]
    maximum = props[19]
    strata = props[20]
    stratatype = props[21]
    x_offset = props[22]
    y_offset = props[23]
    z_offset = props[24]
    size_x = props[25]
    size_y = props[26]
    size_z = props[27]
    amp = props[28]
    freq = props[29]
    texture_name = props[30]

    x, y, z = coords
    # origin
    if rseed is 0:
        origin = x_offset, y_offset, z_offset
        origin_x = x_offset
        origin_y = y_offset
        origin_z = z_offset
        o_range = 1.0
    else:
        # randomise origin
        o_range = 10000.0
        seed_set(rseed)
        origin = random_unit_vector()
        ox = (origin[0] * o_range)
        oy = (origin[1] * o_range)
        oz = (origin[2] * o_range)
        origin_x = (ox - (ox / 2)) + x_offset
        origin_y = (oy - (oy / 2)) + y_offset
        origin_z = (oz - (oz / 2)) + z_offset

    ncoords = (x / (nsize * size_x) + origin_x, y / (nsize * size_y) + origin_y, z / (nsize * size_z) + origin_z)

    # noise type's
    if ntype == 'multi_fractal':
        value = multi_fractal(ncoords, dimension, lacunarity, depth, nbasis) * 0.5

    elif ntype == 'ridged_multi_fractal':
        value = ridged_multi_fractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis) * 0.5

    elif ntype == 'hybrid_multi_fractal':
        value = hybrid_multi_fractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis) * 0.5

    elif ntype == 'hetero_terrain':
        value = hetero_terrain(ncoords, dimension, lacunarity, depth, offset, nbasis) * 0.25

    elif ntype == 'fractal':
        value = fractal(ncoords, dimension, lacunarity, depth, nbasis)

    elif ntype == 'turbulence_vector':
        value = turbulence_vector(ncoords, depth, hardnoise, nbasis, amp, freq)[0]

    elif ntype == 'variable_lacunarity':
        value = variable_lacunarity(ncoords, distortion, nbasis, vlbasis)

    elif ntype == 'marble_noise':
        value = marble_noise(
                        (ncoords[0] - origin_x + x_offset),
                        (ncoords[1] - origin_y + y_offset), 
                        (ncoords[2] - origin_z),
                        (origin[0] + x_offset, origin[1] + y_offset, 0), nsize,
                        marbleshape, marblebias, marblesharpnes,
                        distortion, depth, hardnoise, nbasis, amp, freq
                        )
    elif ntype == 'shattered_hterrain':
        value = shattered_hterrain(ncoords, dimension, lacunarity, depth, offset, distortion, nbasis)

    elif ntype == 'strata_hterrain':
        value = strata_hterrain(ncoords, dimension, lacunarity, depth, offset, distortion, nbasis)

    elif ntype == 'ant_turbulence':
        value = ant_turbulence(ncoords, depth, hardnoise, nbasis, amp, freq, distortion)

    elif ntype == 'vl_noise_turbulence':
        value = vl_noise_turbulence(ncoords, distortion, depth, nbasis, vlbasis, hardnoise, amp, freq)

    elif ntype == 'vl_hTerrain':
        value = vl_hTerrain(ncoords, dimension, lacunarity, depth, offset, nbasis, vlbasis, distortion)

    elif ntype == 'distorted_heteroTerrain':
        value = distorted_heteroTerrain(ncoords, dimension, lacunarity, depth, offset, distortion, nbasis, vlbasis)

    elif ntype == 'double_multiFractal':
        value = double_multiFractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis, vlbasis)

    elif ntype == 'slick_rock':
        value = slick_rock(ncoords,dimension, lacunarity, depth, offset, gain, distortion, nbasis, vlbasis)

    elif ntype == 'planet_noise':
        value = planet_noise(ncoords, depth, hardnoise, nbasis)[2] * 0.5 + 0.5

    elif ntype == 'blender_texture':
        if texture_name in bpy.data.textures:
            value = bpy.data.textures[texture_name].evaluate(ncoords)[3]
        else:
            value = 0.0
    else:
        value = 0.0

    # adjust height
    if invert:
        value = -value
        value = value * height + heightoffset
    else:
        value = value * height + heightoffset

    # strata / terrace / layers
    if stratatype != '0':
        strata = strata / height

    if stratatype == '1':
        strata *= 2
        steps = (sin(value * strata * pi) * (0.1 / strata * pi))
        value = (value * 0.5 + steps * 0.5) * 2.0

    elif stratatype == '2':
        steps = -abs(sin(value * strata * pi) * (0.1 / strata * pi))
        value = (value * 0.5 + steps * 0.5) * 2.0

    elif stratatype == '3':
        steps = abs(sin(value * strata * pi) * (0.1 / strata * pi))
        value = (value * 0.5 + steps * 0.5) * 2.0

    elif stratatype == '4':
        value = int( value * strata ) * 1.0 / strata

    elif stratatype == '5':
        steps = (int( value * strata ) * 1.0 / strata)
        value = (value * (1.0 - 0.5) + steps * 0.5)

    # clamp height min max
    if (value < minimum):
        value = minimum
    if (value > maximum):
        value = maximum

    return value


# ------------------------------------------------------------
# Z normal value to vertex group (Slope map)
class ANTSlopeVGroup(bpy.types.Operator):
    bl_idname = "mesh.ant_slope_vgroup"
    bl_label = "Slope Map"
    bl_description = "Slope map - z normal value to vertex group weight"
    #bl_options = {'REGISTER'} 

    z_method = EnumProperty(
            name="Method:",
            default='SLOPE_Z',
            items=[
                ('SLOPE_Z', "Slope Z", "Slope for planar mesh"),
                ('SLOPE_XYZ', "Slope XYZ", "Slope for spherical mesh")
                ])
    group_name = StringProperty(
            name="Vertex Group Name:",
            default="Slope",
            description="Name"
            )
    select_flat = BoolProperty(
            name="Vert Select:",
            default=True,
            description="Select vertices on flat surface"
            )
    select_range = FloatProperty(
            name="Vert Select Range:",
            default=0.0,
            min=0.0,
            max=1.0,
            description="Increase to select more vertices"
            )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


    def execute(self, context):
        message = "Popup Values: %d, %f, %s, %s" % \
            (self.select_flat, self.select_range, self.group_name, self.z_method)
        self.report({'INFO'}, message)

        ob = bpy.context.active_object

        if self.select_flat:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.context.tool_settings.mesh_select_mode = [True, False, False]
            bpy.ops.object.mode_set(mode='OBJECT')

        vertex_group = ob.vertex_groups.active
        if vertex_group is None or vertex_group.name is not self.group_name:
            bpy.ops.object.vertex_group_add()
            vertex_group = ob.vertex_groups.active
        else:
            vertex_group = ob.vertex_groups.active

        for v in ob.data.vertices:
            if self.z_method == 'SLOPE_XYZ':
                z = (v.co.normalized() * v.normal.normalized()) * 2 - 1
            else:
                z = v.normal[2]

            vertex_group.add([v.index], z, 'REPLACE')
            if self.select_flat:
                if z >= (1.0 - self.select_range):
                    v.select = True

        vertex_group.name = self.group_name

        return {'FINISHED'}


# ------------------------------------------------------------
# Do vert displacement
class do_displace(bpy.types.Operator):
    bl_idname = "mesh.ant_displace"
    bl_label = "Displace"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    bl_description = "Displace mesh vertices - make landscape"

    # properties
    random_seed = IntProperty(
            name="Random Seed",
            min=0,
            default=0,
            description="Randomize noise origin"
            )
    x_offset = FloatProperty(
            name="Offset X",
            default=0.0,
            description="Noise X Offset"
            )
    y_offset = FloatProperty(
            name="Offset Y",
            default=0.0,
            description="Noise Y Offset"
            )
    z_offset = FloatProperty(
            name="Offset Z",
            default=0.0,
            description="Noise Z Offset"
            )
    noise_size = FloatProperty(
            name="Noise Size",
            min=0.01,
            max=1000.0,
            default=0.25,
            description="Noise size"
            )
    noise_size_x = FloatProperty(
            name="Size X",
            min=0.01,
            max=1000.0,
            default=1.0,
            description="Noise x size"
            )
    noise_size_y = FloatProperty(
            name="Size Y",
            min=0.01,
            max=1000.0,
            default=1.0,
            description="Noise y size"
            )
    noise_size_z = FloatProperty(
            name="Size Z",
            min=0.01,
            max=1000.0,
            default=1.0,
            description="Noise Z size"
            )
    NoiseTypes = [
            ('multi_fractal', "Multi Fractal", "Blender: Multi Fractal algorithm"),
            ('ridged_multi_fractal', "Ridged MFractal", "Blender: Ridged Multi Fractal"),
            ('hybrid_multi_fractal', "Hybrid MFractal", "Blender: Hybrid Multi Fractal"),
            ('hetero_terrain', "Hetero Terrain", "Blender: Hetero Terrain"),
            ('fractal', "fBm Fractal", "Blender: fBm - Fractional Browninian motion"),
            ('turbulence_vector', "Turbulence", "Blender: Turbulence Vector"),
            ('variable_lacunarity', "Distorted Noise", "Blender: Distorted Noise"),
            ('marble_noise', "Marble", "A.N.T.: Marble Noise"),
            ('shattered_hterrain', "Shattered hTerrain", "A.N.T.: Shattered hTerrain"),
            ('strata_hterrain', "Strata hTerrain", "A.N.T: Strata hTerrain"),
            ('ant_turbulence', "Another Turbulence", "A.N.T: Turbulence variation"),
            ('vl_noise_turbulence', "vlNoise turbulence", "A.N.T: vlNoise turbulence"),
            ('vl_hTerrain', "vlNoise hTerrain", "A.N.T: vlNoise hTerrain"),
            ('distorted_heteroTerrain', "Distorted hTerrain", "A.N.T distorted hTerrain"),
            ('double_multiFractal', "Double MultiFractal", "A.N.T: double multiFractal"),
            ('slick_rock', "Slick Rock", "A.N.T: slick rock"),
            ('planet_noise', "Planet Noise", "Planet Noise by: Farsthary"),
            ('blender_texture', "Blender Texture - Texture Nodes", "Blender Internal Texture Data Block")
            ]
    noise_type = EnumProperty(
            name="Type",
            description="Noise type",
            default='hetero_terrain',
            items=NoiseTypes
            )
    BasisTypes = [
            ("0", "Blender", "Blender default noise"),
            ("1", "Perlin", "Perlin noise"),
            ("2", "New Perlin", "New Perlin noise"),
            ("3", "Voronoi F1", "Voronoi F1"),
            ("4", "Voronoi F2", "Voronoi F2"),
            ("5", "Voronoi F3", "Voronoi F3"),
            ("6", "Voronoi F4", "Voronoi F4"),
            ("7", "Voronoi F2-F1", "Voronoi F2-F1"),
            ("8", "Voronoi Crackle", "Voronoi Crackle"),
            ("9", "Cell Noise", "Cell noise")
            ]
    basis_type = EnumProperty(
            name="Basis",
            description="Noise basis algorithms",
            default="0",
            items=BasisTypes
            )
    vl_basis_type = EnumProperty(
            name="VLBasis",
            description="VLNoise basis algorithms",
            default="0",
            items=BasisTypes
            )
    distortion = FloatProperty(
            name="Distortion",
            min=0.01,
            max=100.0,
            default=1.0,
            description="Distortion amount"
            )
    hardTypes = [
            ("0", "Soft", "Soft Noise"),
            ("1", "Hard", "Hard noise")
            ]
    hard_noise = EnumProperty(
            name="Soft Hard",
            description="Soft Noise, Hard noise",
            default="0",
            items=hardTypes
            )
    noise_depth = IntProperty(
            name="Depth",
            min=0,
            max=16,
            default=8,
            description="Noise Depth - number of frequencies in the fBm"
            )
    amplitude = FloatProperty(
            name="Amp",
            min=0.01,
            max=1.0,
            default=0.5,
            description="Amplitude"
            )
    frequency = FloatProperty(
            name="Freq",
            min=0.01,
            max=5.0,
            default=2.0,
            description="Frequency"
            )
    dimension = FloatProperty(
            name="Dimension",
            min=0.01,
            max=2.0,
            default=1.0,
            description="H - fractal dimension of the roughest areas"
            )
    lacunarity = FloatProperty(
            name="Lacunarity",
            min=0.01,
            max=6.0,
            default=2.0,
            description="Lacunarity - gap between successive frequencies"
            )
    moffset = FloatProperty(
            name="Offset",
            min=0.01,
            max=6.0,
            default=1.0,
            description="Offset - raises the terrain from sea level"
            )
    gain = FloatProperty(
            name="Gain",
            min=0.01,
            max=6.0,
            default=1.0,
            description="Gain - scale factor"
            )
    BiasTypes = [
            ("0", "Sin", "Sin"),
            ("1", "Cos", "Cos"),
            ("2", "Tri", "Tri"),
            ("3", "Saw", "Saw")
            ]
    marble_bias = EnumProperty(
            name="Bias",
            description="Marble bias",
            default="0",
            items=BiasTypes
            )
    SharpTypes = [
            ("0", "Soft", "Soft"),
            ("1", "Sharp", "Sharp"),
            ("2", "Sharper", "Sharper"),
            ("3", "Soft inv.", "Soft"),
            ("4", "Sharp inv.", "Sharp"),
            ("5", "Sharper inv.", "Sharper")
            ]
    marble_sharp = EnumProperty(
            name="Sharp",
            description="Marble sharpness",
            default="0",
            items=SharpTypes
            )
    ShapeTypes = [
            ("0", "Default", "Default"),
            ("1", "Ring", "Ring"),
            ("2", "Swirl", "Swirl"),
            ("3", "Bump", "Bump"),
            ("4", "Wave", "Wave"),
            ("5", "Y", "Y"),
            ("6", "X", "X")
            ]
    marble_shape = EnumProperty(
            name="Shape",
            description="Marble shape",
            default="0",
            items=ShapeTypes
            )
    height = FloatProperty(
            name="Height",
            min=-10000.0,
            max=10000.0,
            default=0.25,
            description="Noise intensity scale"
            )
    invert = BoolProperty(
            name="Invert",
            default=False,
            )
    offset = FloatProperty(
            name="Offset",
            min=-10000.0,
            max=10000.0,
            default=0.0,
            description="Height offset"
            )
    maximum = FloatProperty(
            name="Maximum",
            min=-10000.0,
            max=10000.0,
            default=1.0,
            description="Maximum"
            )
    minimum = FloatProperty(
            name="Minimum",
            min=-10000.0,
            max=10000.0,
            default=-1.0,
            description="Minimum"
            )
    strata = FloatProperty(
            name="Amount",
            min=0.01,
            max=1000.0,
            default=5.0,
            description="Strata layers / terraces"
            )
    StrataTypes = [
            ("0", "None", "No strata"),
            ("1", "Smooth", "Smooth transitions"),
            ("2", "Sharp -", "Sharp substract transitions"),
            ("3", "Sharp +", "Sharp add transitions"),
            ("4", "Quantize", "Quantize"),
            ("5", "Quantize Mix", "Quantize mixed with noise")
            ]
    strata_type = EnumProperty(
            name="Strata",
            description="Strata types",
            default="0",
            items=StrataTypes
            )
    use_vgroup = BoolProperty(
            name="Vertex Group Weight",
            default=False,
            description="Use active vertex group weight"
            )
    show_noise_settings = BoolProperty(
            name="Noise Settings",
            default=True,
            description="Show noise settings"
            )
    show_terrain_settings = BoolProperty(
            name="Displace Settings",
            default=True,
            description="Show displace settings"
            )
    refresh = BoolProperty(
            name="Refresh",
            description="Refresh",
            default=False
            )
    auto_refresh = BoolProperty(
            name="Auto",
            description="Automatic refresh",
            default=True
            )
    texture_name = StringProperty(
        name="Texture",
        default=""
        )

    def draw(self, context):
        sce = context.scene
        layout = self.layout

        box = layout.box()
        row = box.row(align=True)
        if self.auto_refresh is False:
            self.refresh = False
        elif self.auto_refresh is True:
            self.refresh = True
        split = row.split(align=True)
        split.prop(self, 'auto_refresh', toggle=True, icon_only=True, icon='AUTO')
        split.prop(self, 'refresh', toggle=True, icon_only=True, icon='FILE_REFRESH')
        split.operator('mesh.ant_slope_vgroup', text="", icon='GROUP_VERTEX')

        box = layout.box()
        box.prop(self, "show_noise_settings", toggle=True)
        if self.show_noise_settings:
            box.prop(self, "noise_type")
            if self.noise_type == "blender_texture":
                box.prop_search(self, "texture_name", bpy.data, "textures")
            else:
                box.prop(self, "basis_type")

            col = box.column(align=True)
            col.prop(self, "random_seed")
            col = box.column(align=True)
            col.prop(self, "x_offset")
            col.prop(self, "y_offset")
            col.prop(self, "z_offset")
            col.prop(self, "noise_size_x")
            col.prop(self, "noise_size_y")
            col.prop(self, "noise_size_z")
            col = box.column(align=True)
            col.prop(self, "noise_size")

            col = box.column(align=True)
            if self.noise_type == "multi_fractal":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
            elif self.noise_type == "ridged_multi_fractal":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
                col.prop(self, "gain")
            elif self.noise_type == "hybrid_multi_fractal":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
                col.prop(self, "gain")
            elif self.noise_type == "hetero_terrain":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
            elif self.noise_type == "fractal":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
            elif self.noise_type == "turbulence_vector":
                col.prop(self, "noise_depth")
                col.prop(self, "amplitude")
                col.prop(self, "frequency")
                col.separator()
                row = col.row(align=True)
                row.prop(self, "hard_noise", expand=True)
            elif self.noise_type == "variable_lacunarity":
                box.prop(self, "vl_basis_type")
                box.prop(self, "distortion")
            elif self.noise_type == "marble_noise":
                box.prop(self, "marble_shape")
                box.prop(self, "marble_bias")
                box.prop(self, "marble_sharp")
                col = box.column(align=True)
                col.prop(self, "distortion")
                col.prop(self, "noise_depth")
                col.separator()
                row = col.row(align=True)
                row.prop(self, "hard_noise", expand=True)
            elif self.noise_type == "shattered_hterrain":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
                col.prop(self, "distortion")
            elif self.noise_type == "strata_hterrain":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
                col.prop(self, "distortion", text="Strata")
            elif self.noise_type == "ant_turbulence":
                col.prop(self, "noise_depth")
                col.prop(self, "amplitude")
                col.prop(self, "frequency")
                col.prop(self, "distortion")
                col.separator()
                row = col.row(align=True)
                row.prop(self, "hard_noise", expand=True)
            elif self.noise_type == "vl_noise_turbulence":
                col.prop(self, "noise_depth")
                col.prop(self, "amplitude")
                col.prop(self, "frequency")
                col.prop(self, "distortion")
                col.separator()
                col.prop(self, "vl_basis_type")
                col.separator()
                row = col.row(align=True)
                row.prop(self, "hard_noise", expand=True)
            elif self.noise_type == "vl_hTerrain":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
                col.prop(self, "distortion")
                col.separator()
                col.prop(self, "vl_basis_type")
            elif self.noise_type == "distorted_heteroTerrain":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
                col.prop(self, "distortion")
                col.separator()
                col.prop(self, "vl_basis_type")
            elif self.noise_type == "double_multiFractal":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "moffset")
                col.prop(self, "gain")
                col.separator()
                col.prop(self, "vl_basis_type")
            elif self.noise_type == "slick_rock":
                col.prop(self, "noise_depth")
                col.prop(self, "dimension")
                col.prop(self, "lacunarity")
                col.prop(self, "gain")
                col.prop(self, "moffset")
                col.prop(self, "distortion")
                col.separator()
                col.prop(self, "vl_basis_type")
            elif self.noise_type == "planet_noise":
                col.prop(self, "noise_depth")
                col.separator()
                row = col.row(align=True)
                row.prop(self, "hard_noise", expand=True)

        box = layout.box()
        box.prop(self, "show_terrain_settings", toggle=True)
        if self.show_terrain_settings:
            col = box.column(align=True)
            row = col.row(align=True).split(0.9, align=True)
            row.prop(self, "height")
            row.prop(self, "invert", toggle=True, text="", icon='ARROW_LEFTRIGHT')
            col.prop(self, "offset")
            col.prop(self, "maximum")
            col.prop(self, "minimum")
            col = box.column(align=True)
            col.prop(self, "use_vgroup", toggle=True)
            col = box.column(align=False)
            col.prop(self, "strata_type")
            if self.strata_type is not "0":
                col = box.column(align=False)
                col.prop(self, "strata")

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'MESH')


    def invoke(self, context, event):
        self.refresh = True
        return self.execute(context)


    def execute(self, context):
        if not self.refresh:
            return {'PASS_THROUGH'}

        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        # settings
        props = [
            self.random_seed,
            self.noise_size,
            self.noise_type,
            self.basis_type,
            self.vl_basis_type,
            self.distortion,
            self.hard_noise,
            self.noise_depth,
            self.dimension,
            self.lacunarity,
            self.moffset,
            self.gain,
            self.marble_bias,
            self.marble_sharp,
            self.marble_shape,
            self.invert,
            self.height,
            self.offset,
            self.minimum,
            self.maximum,
            self.strata,
            self.strata_type,
            self.x_offset,
            self.y_offset,
            self.z_offset,
            self.noise_size_x,
            self.noise_size_y,
            self.noise_size_z,
            self.amplitude,
            self.frequency,
            self.texture_name
            ]

        # do displace
        obj = context.object
        mesh = obj.data

        if not self.use_vgroup:
            for v in mesh.vertices:
                v.co += v.normal * noise_gen(v.co, props)
        else:
            vertex_group = obj.vertex_groups.active 
            if vertex_group:
                index = 0
                for v in mesh.vertices:
                    v.co += vertex_group.weight(index) * v.normal * noise_gen(v.co, props)
                    index += 1

        mesh.update()

        if bpy.ops.object.shade_smooth == True:
            bpy.ops.object.shade_smooth()



        if self.auto_refresh is False:
            self.refresh = False

        # restore pre operator undo state
        context.user_preferences.edit.use_global_undo = undo


        return {'FINISHED'}

# ------------------------------------------------------------
# ------------------------------------------------------------
class panel_func_ant_displace(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "TOOLS"
    bl_label = "Displace mesh"
    bl_category = "Tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator(do_displace.bl_idname, text="A.N.T. Displace", icon="MOD_DISPLACE")


# ------------------------------------------------------------
# Register:
def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(panel_func_ant_displace)
    #bpy.utils.register_class(ANTSlopeVGroup)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(panel_func_ant_displace)
    #bpy.utils.unregister_class(ANTSlopeVGroup)


if __name__ == "__main__":
 register()