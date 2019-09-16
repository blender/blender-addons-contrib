import bpy
import bgl
import math
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from .shader import Dashed_Shader_3D
from . properties import Sun

dashedLineShader = gpu.types.GPUShader(Dashed_Shader_3D.vertex_shader, Dashed_Shader_3D.fragment_shader)

class NorthClass:

    def __init__(self):
        self.handler = None
        self.isActive = False

    def refresh_screen(self):
        #bpy.context.scene.cursor.location.x += 0.0
        bpy.context.area.tag_redraw()

    def activate(self, context):

        if context.area.type == 'PROPERTIES':
            self.handler = bpy.types.SpaceView3D.draw_handler_add(
                               DrawNorth_callback,
                               #(self, context), 'WINDOW', 'POST_PIXEL')  # why changed?
                               (self, context), 'WINDOW', 'POST_VIEW')
            self.isActive = True
            self.refresh_screen()
            return True
        return False

    def deactivate(self):
        if self.handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
            self.handler = None
        self.isActive = False
        self.refresh_screen()
        #if Sun.SP:  # why removed?
        Sun.SP.ShowNorth = False  # indent?
        Sun.ShowNorth = False


North = NorthClass()


def DrawNorth_callback(self, context):

    if not Sun.SP.ShowNorth and North.isActive:
        North.deactivate()
        return

    # ------------------------------------------------------------------
    # Set up the compass needle using the current north offset angle
    # less 90 degrees.  This forces the unit circle to begin at the
    # 12 O'clock instead of 3 O'clock position.
    # ------------------------------------------------------------------
    #color = (0.2, 0.6, 1.0, 0.7)
    color = (0.2, 0.6, 1.0, 1)
    radius = 100
    angle = -(Sun.NorthOffset - math.pi / 2)
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius

    #p1, p2 = (0, 0, 0), (x, y, 0)   # Start & end of needle
    # much removed / changed from original below
    bgl.glEnable(bgl.GL_MULTISAMPLE)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glEnable(bgl.GL_BLEND)

    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glDepthMask(False)

    bgl.glLineWidth(2)


    p1 = (0, 0, 0)
    p2 = (x/20 , y/20, 0)
    coords = [p1, p2]   # Start & end of needle
    arclengths = [0,(Vector(p1)-Vector(p2)).length]
    batch = batch_for_shader(dashedLineShader, 'LINES', {"pos": coords,"arcLength":arclengths})

    dashedLineShader.bind()
    dashedLineShader.uniform_float("finalColor", color)
    dashedLineShader.uniform_float("u_Scale", 10)
    batch.draw(dashedLineShader)
