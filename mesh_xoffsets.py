'''
BEGIN GPL LICENSE BLOCK

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

END GPL LICENSE BLOCK

#============================================================================

mesh_xoffsets.py (alpha version 007b)

Install instructions (if downloaded separately from Blender):
1) Save the mesh_xoffsets.py file to your computer.
2) In Blender, go to File > User Preferences > Add-ons
3) Press Install From File and select the mesh_xoffsets.py file you
    just downloaded.
4) Enable the Add-On by clicking on the box to the left of Add-On's name

#============================================================================

todo:
  [?] rewrite/refactor code to optimize for modal operation
  [?] make sure point removal state resets are correct (tryAdd)
  [X] fix: when btn clicked, dialog will not appear until after mouse moved
  [X] fix: when new meas input, transform not applied until after mouse moved
  [ ] prevent selection of non-visible vertices
  [ ] fix bug: obj is not subscriptable error if perspective is changed after 
        launching addon, disabling perspective change for now
  [ ] better measurement input panel
  [ ] add hotkey reference info into 3D View ?

#============================================================================
'''

bl_info = {
    "name": "Exact Offsets",
    "author": "nBurn",
    "version": (0, 0, 7),
    "blender": (2, 7, 7),
    "location": "View3D",
    "description": "Tool for precisely setting distance, scale, and rotation of mesh geometry",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Mesh/Exact_Offsets",
    "category": "Mesh"
}

import bpy
import bgl
import blf
import bmesh
from copy import deepcopy
from math import fmod, sqrt, degrees, radians
from mathutils import Vector, geometry, Quaternion, Euler
from mathutils.geometry import intersect_line_line_2d
from bpy_extras.view3d_utils import location_3d_to_region_2d
#__import__('code').interact(local=dict(globals(), **locals()))

print("Exact Offsets loaded")

(
    XO_CLICK_CHECK,
    XO_CHECK_POPUP_INFO,
    XO_DO_TRANSFORM,
    XO_GET_0_OR_180,
    XO_MOVE,
    XO_SCALE,
    XO_ROTATE,
) = range(7)

currMeasStor = 0.0
newMeasStor = None
popUpActive = False
RegRv3d = ()


def getRegRv3d():
    global RegRv3d
    region = bpy.context.region
    rv3d = []
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            rv3d = area.spaces[0].region_3d
            break
    RegRv3d = (region, rv3d)


class Colr:
    red   = 1.0, 0.0, 0.0, 0.5
    green = 0.0, 1.0, 0.0, 0.5
    blue  = 0.0, 0.0, 1.0, 0.5
    white = 1.0, 1.0, 1.0, 1.0
    grey  = 1.0, 1.0, 1.0, 0.4


# Class to stores selection info for scene and/or edited mesh
# Generates a list of mesh objects in the scene and lists of selected mesh
# and non-mesh objects and selected vertices (if in Edit Mode). These lists
# are used to speed up mesh object iteration and for restoring the selected
# objects after transforms.
class SceneSelectionInfo:
    def __init__(self):
        self.selNMObjs = []  # selected non-mesh objects
        self.MshObjs = []
        self.selMshObjs = []
        self.selMshVts = []
        self.activeObj = None
        self.obj = bpy.context.scene.objects  # short hand, for internal use

    # Checks if there was changes to the selected objects or verts. It is
    # assumed no objects added or removed while the addon is running. This
    # should not be run while the snap point is active / existing.
    def update(self, EdType):
        tmp = []
        if EdType == "OBJECT":
            if self.obj.active.type == 'MESH':
                self.activeObj = self.obj.active
            else:
                self.obj.active = self.obj[ self.MshObjs[0] ]
                self.activeObj = self.obj.active
            for i in self.MshObjs:
                if self.obj[i].select:
                    tmp.append(i)
            self.selMshObjs = tmp.copy()
            #print("self.selMshObjs", self.selMshObjs)  # debug

        elif EdType == "EDIT_MESH":
            bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
            if hasattr(bm.verts, "ensure_lookup_table"):
                bm.verts.ensure_lookup_table()
            for ind in range(len(bm.verts)):
                if bm.verts[ind].select == True:
                    tmp.append(ind)
            self.selMshVts = tmp.copy()

    def restoreSelected(self, EdType):
        if EdType == "OBJECT":
            self.obj.active = self.activeObj
            for ind in self.selMshObjs:
                self.obj[ind].select = True
        elif EdType == "EDIT_MESH":
            bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
            if hasattr(bm.verts, "ensure_lookup_table"):
                bm.verts.ensure_lookup_table()
            for ind in self.selMshVts:
                bm.verts[ind].select = True

    # for generating MshObjs and selNMObjs info when addon first run
    def startRun(self, EdType):
        for i in range(len(self.obj)):
            if self.obj[i].type == 'MESH':
                self.MshObjs.append(i)
            elif self.obj[i].select:
                self.selNMObjs.append(i)
        self.update(EdType)


# vertex storage class, stores reference point info
class VertObj:
    def __init__(self, objInd=-1, vertInd=-1, co3D=(), co2D=(), dist2D=4000, refInd=-1):
        self.objInd = objInd
        self.vertInd = vertInd
        self.co3D = co3D
        self.co2D = co2D
        self.dist2D = dist2D
        self.refInd = refInd
        self.obj = bpy.context.scene.objects  # short hand, for internal use

    # Have to use deepcopy for co's as tuples are the default init
    # value and tuples don't have a ".copy()" method.
    def copy(self):  # returns independent copy of VertObj
        return VertObj(self.objInd, self.vertInd, deepcopy(self.co3D),
                deepcopy(self.co2D), self.dist2D, self.refInd)

    def set2D(self):
        global RegRv3d
        region, rv3d = RegRv3d[0], RegRv3d[1]
        self.co2D = location_3d_to_region_2d(region, rv3d, self.co3D)

    def update3D(self):
        tmpCoLocal = self.obj[self.objInd].data.vertices[self.vertInd].co
        self.co3D = self.obj[self.objInd].matrix_world * tmpCoLocal


# Stores the reference points and ref pt related info.
class ReferencePoints:
    def __init__(self):
        self.cnt = 0  # count
        self.rpLs = [(),(),()]  # ref pt list
        self.lpLs = [(),(),()]  # lock pt list
        self.axLock = ''  # axis lock
        self.colrLs = Colr.red, Colr.green

    def update_colrLs(self):
        if self.cnt < 3:
            self.colrLs = Colr.red, Colr.green
        else:  # self.cnt > 2
            self.colrLs = Colr.red, Colr.blue, Colr.green

    def removePt(self, remInd):
        # hackery or smart, you decide...
        if remInd != self.cnt - 1:
            ind = [0, 1, 2][:self.cnt]
            ind.remove(remInd)
            for i in range(len(ind)):
                self.rpLs[i] = self.rpLs[ind[i]].copy()
                self.rpLs[i].refInd = i
        self.cnt -= 1

    def tryAdd(self, found_pt):
        if self.cnt > 0:
            for rp in range(self.cnt):
                if self.rpLs[rp].co3D == found_pt.co3D:
                    self.axLock = ''
                    self.removePt(self.rpLs[rp].refInd)
                    self.lpLs = self.rpLs
                    #print("ref pt removed:", rp, "cnt:", self.cnt)  # debug
                    self.update_colrLs()
                    return
        # if duplicate not found and cnt not max, add found_pt to rpLs
        if self.cnt < 3:
            self.rpLs[self.cnt] = found_pt.copy()
            self.rpLs[self.cnt].refInd = self.cnt
            ''' Begin Debug 
            ptFndStr = str(self.rpLs[self.cnt].co3D)
            ptFndStr = ptFndStr.replace("<Vector ", "Vector(")
            ptFndStr = ptFndStr.replace(">", ")")
            print("Ref_pt_" + str(self.cnt) + ' =', ptFndStr)
            #print("ref pt added:", self.cnt, "cnt:", self.cnt+1) 
            End Debug ''' 
            self.cnt += 1
        self.update_colrLs()
        return


# Stores rotation info for passing data from draw_callback_px to
# external functions. Not as bad as hiding arguments in passed
# variables, but still seems hackish...
class RotationData:
    def __init__(self):
        self.newAngR = 0.0
        self.newAngD = 0.0
        self.angDiffD = 0.0
        self.angDiffR = 0.0
        self.axisLk = ''
        self.pivNorm = []  # pivot normal
        #self.angleEq_0_180 = False
        #self.obj = bpy.context.scene.objects[self.objInd] # short hand


# === Linear Equations ===

def getMidpoint(ptA, ptB):
    return ptA.lerp(ptB, 0.5)


def get_dist(ptA, ptB):
    return (ptA - ptB).length


# For making sure rise over run doesn't get flipped.
def slope_check(pt1, pt2):
    cmp_ls = []
    for i in range(len(pt1)):
        cmp_ls.append(floatsAlmEq(pt1[i], pt2[i]) or pt1[i] > pt2[i])
    return cmp_ls


# Finds 3D location that shares same slope of line connecting Anchor and
# Free or that is on axis line going through Anchor.
def get_new_3D_co(self, lock, rpLs, oldDis, newDis):
    ptA, ptF = rpLs[0].co3D, rpLs[1].co3D
    if lock == '':
        if newDis == 0:
            return ptA
        origSlope = slope_check(ptA, ptF)
        scale = newDis / oldDis
        ptN_1 = ptA.lerp(ptF,  scale)
        ptN_2 = ptA.lerp(ptF, -scale)
        ptN_1_slp = slope_check(ptA, ptN_1)
        ptN_2_slp = slope_check(ptA, ptN_2)
        if origSlope == ptN_1_slp:
            #print("ptN_1 !")  # debug
            if newDis > 0:
                return ptN_1
            else:
                # for negative distances
                return ptN_2
        elif origSlope == ptN_2_slp:
            #print("ptN_2 !")  # debug
            if newDis > 0:
                return ptN_2
            else:
                return ptN_1
        else:  # neither slope matches
            self.report({'ERROR'}, 'Slope mismatch. Cannot calculate new point.')
            return None
    elif lock == 'X':
        if ptF[0] > ptA[0]: return Vector([ ptA[0] + newDis, ptF[1], ptF[2] ])
        else: return Vector([ ptA[0] - newDis, ptF[1], ptF[2] ])
    elif lock == 'Y':
        if ptF[1] > ptA[1]: return Vector([ ptF[0], ptA[1] + newDis, ptF[2] ])
        else: return Vector([ ptF[0], ptA[1] - newDis, ptF[2] ])
    elif lock == 'Z':
        if ptF[2] > ptA[2]: return Vector([ ptF[0], ptF[1], ptA[2] + newDis ])
        else: return Vector([ ptF[0], ptF[1], ptA[2] - newDis ])
    else:  # neither slope matches
        self.report({'ERROR'}, "Slope mismatch. Can't calculate new point.")
        return None


# Floating point math fun! Since equality tests on floats are a crap shoot,
# instead check if floats are almost equal (is the first float within a
# certain tolerance amount of the second).
# Note, this function may fail in certain circumstances depending on the
# number of significant figures. If comparisons become problematic, you can
# try a different power of ten for the "tol" value (eg 0.01 or 0.00001)
# todo: replace this with Python 3.5's math.isclose() ?
# do recent versions of Blender support math.isclose()?
def floatsAlmEq(flt_A, flt_B):
    tol = 0.0001
    return flt_A > (flt_B - tol) and flt_A < (flt_B + tol)


# Aco, Bco, and Cco are Vector based 3D coordinates
# coordinates must share a common center "pivot" point (Bco)
def getLineAngle3D(Aco, Bco, Cco):
    algnAco = Aco - Bco
    algnCco = Cco - Bco
    return algnAco.angle(algnCco)


# Checks if the 3 coordinates arguments (pt1, pt2, pt3) will create
# an angle with a measurement matching the value in the argument
# expAngMeas (expected angle measurement).
def angleMatch3D(pt1, pt2, pt3, expAngMeas):
    angMeas = getLineAngle3D(pt1, pt2, pt3)
    '''
    print("pt1", pt1)  # debug
    print("pt2", pt2)  # debug
    print("pt3", pt3)  # debug
    print("expAng ", expAngMeas)  # debug
    print("angMeas ", angMeas)  # debug
    '''
    return floatsAlmEq(angMeas, expAngMeas)


# Calculates rotation around axis or face normal at Pivot's location.
# Takes two 3D coordinate Vectors (PivC and movCo), rotation angle in
# radians (angleDiffRad), and rotation data storage object (rotDat).
# Aligns movCo to world origin (0, 0, 0) and rotates aligned
# movCo (movAligned) around axis stored in rotDat. After rotation,
# removes world-origin alignment.
def getRotatedPoint(PivC, angleDiffRad, rotDat, movCo):
    axisLk = rotDat.axisLk
    movAligned = movCo - PivC
    rotVal = []
    if   axisLk == '':  # arbitrary axis / spherical rotations
        rotVal = Quaternion(rotDat.pivNorm, angleDiffRad)
    elif axisLk == 'X':
        rotVal = Euler((angleDiffRad, 0.0, 0.0), 'XYZ')
    elif axisLk == 'Y':
        rotVal = Euler((0.0, angleDiffRad, 0.0), 'XYZ')
    elif axisLk == 'Z':
        rotVal = Euler((0.0, 0.0, angleDiffRad), 'XYZ')
    movAligned.rotate(rotVal)
    return movAligned + PivC


# Takes a refPts (ReferencePoints class) argument and modifies its member
# variable lpLs (lock pt list). The lpLs variable is assigned a modified list
# of 3D coordinates (if an axis lock was provided), the contents of the
# refPts' rpLs var (if no axis lock was provided), or an empty list (if there
# wasn't enough refPts or there was a problem creating the modified list).
# todo : move inside ReferencePoints class ?
def setLockPts(refPts):
    if refPts.cnt < 2:
        refPts.lpLs = []
    elif refPts.axLock == '':
        refPts.lpLs = refPts.rpLs
    else:
        refPts.lpLs = []
        new0, new1 = VertObj(), VertObj()
        ptls = [refPts.rpLs[i].co3D for i in range(refPts.cnt)]  # shorthand
        # finds 3D midpoint between 2 supplied coordinates
        # axis determines which coordinates are assigned midpoint values
        # if X, Anchor is [AncX, MidY, MidZ] and Free is [FreeX, MidY, MidZ]
        if refPts.cnt == 2:  # translate
            mid3D = getMidpoint(ptls[0], ptls[1])
            if refPts.axLock == 'X':
                new0.co3D = Vector([ ptls[0][0], mid3D[1], mid3D[2] ])
                new1.co3D = Vector([ ptls[1][0], mid3D[1], mid3D[2] ])
            elif refPts.axLock == 'Y':
                new0.co3D = Vector([ mid3D[0], ptls[0][1], mid3D[2] ])
                new1.co3D = Vector([ mid3D[0], ptls[1][1], mid3D[2] ])
            elif refPts.axLock == 'Z':
                new0.co3D = Vector([ mid3D[0], mid3D[1], ptls[0][2] ])
                new1.co3D = Vector([ mid3D[0], mid3D[1], ptls[1][2] ])
            if new0.co3D != new1.co3D:
                refPts.lpLs = [new0, new1]

        # axis determines which of the Free's coordinates are assigned
        # to Anchor and Pivot coordinates eg:
        # if X, Anchor is [FreeX, AncY, AncZ] and Pivot is [FreeX, PivY, PivZ]
        elif refPts.cnt == 3:  # rotate
            movCo = refPts.rpLs[2].co3D.copy()
            if refPts.axLock == 'X':
                new0.co3D = Vector([ movCo[0], ptls[0][1], ptls[0][2] ])
                new1.co3D = Vector([ movCo[0], ptls[1][1], ptls[1][2] ])
            elif refPts.axLock == 'Y':
                new0.co3D = Vector([ ptls[0][0], movCo[1], ptls[0][2] ])
                new1.co3D = Vector([ ptls[1][0], movCo[1], ptls[1][2] ])
            elif refPts.axLock == 'Z':
                new0.co3D = Vector([ ptls[0][0], ptls[0][1], movCo[2] ])
                new1.co3D = Vector([ ptls[1][0], ptls[1][1], movCo[2] ])
            if new0.co3D != new1.co3D and \
            new0.co3D != movCo and \
            new1.co3D != movCo:
                new2 = VertObj(-1, -1, movCo, [], -1, -1)
                refPts.lpLs = [new0, new1, new2]

        if refPts.lpLs != []:
            for itm in refPts.lpLs: itm.set2D()


# Finds out whether positive rotDat.newAngR or negative rotDat.newAngR
# will result in the desired rotation angle.
def findCorrectRot(refPts, rotDat):
    angDiffRad, newAngRad = rotDat.angDiffR, rotDat.newAngR
    PivPt, movePt = refPts.rpLs[1].co3D, refPts.rpLs[2].co3D
    tmpCoP = getRotatedPoint(PivPt, angDiffRad, rotDat, movePt)
    tmpCoN = getRotatedPoint(PivPt,-angDiffRad, rotDat, movePt)
    #print("tmpCoP", tmpCoP, "\ntmpCoN", tmpCoN)  # debug
    setLockPts(refPts)
    lockPts = refPts.lpLs
    # is below check needed? is lockPts tested before findCorrectRot called?
    # will be needed for a selection move?
    if lockPts == []:
        print("lockPts == [] CHECK IS NEEDED!")
        refPts.axLock = ''
        return ()
    else:
        if angleMatch3D(lockPts[0].co3D, lockPts[1].co3D, tmpCoP, newAngRad):
            #print("matched positive tmpCo")  # debug
            return tmpCoP, angDiffRad
        else:
            #print("matched negative tmpCo")  # debug
            return tmpCoN, -angDiffRad


# === Point finding code ===


# Returns the closest vertex found to the supplied 2D location.
# Returns None if no vertex found.
def find_closest_vert(loc, meshIndLs):
    global RegRv3d
    region, rv3d = RegRv3d[0], RegRv3d[1]
    objs = bpy.context.scene.objects  # shorthand
    closest = VertObj()
    for ind in meshIndLs:
        meshObj = objs[ind]
        if len(meshObj.data.vertices) > 0:
            for i, v in enumerate(meshObj.data.vertices):
                co3D = meshObj.matrix_world * v.co
                co2D = location_3d_to_region_2d(region, rv3d, co3D)
                dist2D = get_dist(loc, co2D)
                if closest.dist2D > dist2D:
                    closest = VertObj(ind, i, co3D, co2D, dist2D)
    if closest.dist2D < 40:
        return closest
    else:
        return None


# === 3D View mouse location and button code ===
# Functions outside_loop() and point_inside_loop() for creating the measure
# change "button" in the 3D View taken from patmo141's Virtual Button script:
# https://blenderartists.org/forum/showthread.php?259085

def outside_loop(loopCoords):
    xs = [v[0] for v in loopCoords]
    ys = [v[1] for v in loopCoords]
    maxx = max(xs)
    maxy = max(ys)
    bound = (1.1*maxx, 1.1*maxy)
    return bound


def point_inside_loop(loopCoords, mousLoc):
    nverts = len(loopCoords)
    # vectorize our two item tuple
    out = Vector(outside_loop(loopCoords))
    vecMous = Vector(mousLoc)
    intersections = 0
    for i in range(0, nverts):
        a = Vector(loopCoords[i-1])
        b = Vector(loopCoords[i])
        if intersect_line_line_2d(vecMous, out, a, b):
            intersections += 1
    inside = False
    if fmod(intersections, 2):
        inside = True
    return inside


# === GL drawing code ===


def draw_logo(text, pt_co):
    pt_color = [1.0, 1.0, 0.5, 0.6]  # pale yellow
    font_id = 0
    bgl.glColor4f(*pt_color)
    blf.position(font_id, pt_co[0], pt_co[1], 0)
    blf.size(font_id, 32, 32)
    blf.draw(font_id, text)
    w, h = blf.dimensions(font_id, text)
    return [w, h]


def get_btn_coor(origin, rWidth, rHeight, xOffset, yOffset):
    coBL = (origin[0]-xOffset), (origin[1]-yOffset)
    coTL = (origin[0]-xOffset), (origin[1]+rHeight+yOffset)
    coTR = (origin[0]+rWidth+xOffset), (origin[1]+rHeight+yOffset)
    coBR = (origin[0]+rWidth+xOffset), (origin[1]-yOffset)
    return [coBL, coTL, coTR, coBR]


def draw_font_at_pt(text, pt_co, pt_color):
    font_id = 0
    bgl.glColor4f(*pt_color)
    blf.position(font_id, pt_co[0], pt_co[1], 0)
    blf.size(font_id, 32, 72)
    blf.draw(font_id, text)
    w, h = blf.dimensions(font_id, text)
    return [w, h]


def draw_pt_2D(pt_co, pt_color, sz=8):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glPointSize(sz)
    bgl.glColor4f(*pt_color)
    bgl.glBegin(bgl.GL_POINTS)
    bgl.glVertex2f(*pt_co)
    bgl.glEnd()
    return


def draw_line_2D(pt_co_1, pt_co_2, pt_color):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glPointSize(7)
    bgl.glColor4f(*pt_color)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*pt_co_1)
    bgl.glVertex2f(*pt_co_2)
    bgl.glEnd()
    return


def draw_box(box_co, color):
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for coord in box_co:
        bgl.glVertex2f(coord[0], coord[1])
    bgl.glVertex2f(box_co[0][0], box_co[0][1])
    bgl.glEnd()
    return


def draw_meas_btn(text, co2D, mouseLoc, colorOff, colorOn):
    color = colorOff
    offSet = 5
    font_id = 0
    blf.size(font_id, 24, 72)
    w, h = blf.dimensions(font_id, text)
    textCoor = (co2D[0] - w/2, (co2D[1] + 5*offSet))
    btnCo = get_btn_coor(textCoor, w, h, offSet, offSet)

    bgl.glColor4f(*color)
    blf.position(font_id, textCoor[0], textCoor[1], 0.0)
    blf.draw(font_id, text)
    if point_inside_loop(btnCo, mouseLoc):
        color = colorOn

    draw_box(btnCo, color)
    return btnCo


# Draw User Interface
def drawUI(self):
    global currMeasStor
    refPts, measBtnAct = self.refPts, self.measBtnAct
    if refPts.cnt == 1:
        refPts.rpLs[0].set2D()
        draw_pt_2D(refPts.rpLs[0].co2D, refPts.colrLs[0])
    else:
        midP = []
        if refPts.cnt < 3:
            midP = VertObj(-1, -1, getMidpoint(refPts.rpLs[0].co3D,
                    refPts.rpLs[1].co3D))
        else:
            midP = VertObj( -1, -1, refPts.lpLs[1].co3D.copy() )

        lastPt = []
        if refPts.axLock == '':
            for i in range(refPts.cnt):
                refPts.rpLs[i].set2D()
                draw_pt_2D(refPts.rpLs[i].co2D, refPts.colrLs[i])
                if lastPt != []:
                    draw_line_2D(lastPt, refPts.rpLs[i].co2D, refPts.colrLs[0])
                lastPt = refPts.rpLs[i].co2D
        else:
            if   refPts.axLock == 'X':
                draw_font_at_pt(refPts.axLock, [80, 36], Colr.red)
            elif refPts.axLock == 'Y':
                draw_font_at_pt(refPts.axLock, [80, 36], Colr.green)
            elif refPts.axLock == 'Z':
                draw_font_at_pt(refPts.axLock, [80, 36], Colr.blue)
            for i in range(refPts.cnt):
                refPts.rpLs[i].set2D()
                draw_pt_2D(refPts.rpLs[i].co2D, refPts.colrLs[i])
                refPts.lpLs[i].set2D()
                draw_pt_2D(refPts.lpLs[i].co2D, refPts.colrLs[i])
                if lastPt != []:
                    draw_line_2D(lastPt, refPts.lpLs[i].co2D, refPts.colrLs[0])
                lastPt = refPts.lpLs[i].co2D

        if measBtnAct:
            midP.set2D()
            MeasStr = format(currMeasStor, '.2f')
            self.measBtnCo = draw_meas_btn(MeasStr, midP.co2D,
                        self.mouseLoc, Colr.white, Colr.red)


# Refreshes mesh drawing in 3D view and updates mesh coordinate
# data so refPts are drawn at correct locations.
# Using editmode_toggle to do this seems hackish, but editmode_toggle seems
# to be the only thing that updates both drawing and coordinate info.
def EditModeRefresh(edType):
    if edType == "EDIT_MESH":
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()


# Takes the Editor Mode (mode), newCo (Vector), and freeObj (VertObj) as
# arguments. Calculates difference between the 3D locations in newCo and
# freeObj to determine the translation to apply to the selected geometry.
def do_translation(mode, newCo, freeObj):
    objs = bpy.context.scene.objects  # shorthand
    #print("coChg", coChg)  # debug
    if mode == "OBJECT":
        coChg = -(freeObj.co3D - newCo)  # coChg = coordinate change
        bpy.ops.transform.translate(value=(coChg[0], coChg[1], coChg[2]))
    elif mode == "EDIT_MESH":
        tLoc = objs[freeObj.objInd].data.vertices[freeObj.vertInd].co
        oldCo = bpy.context.edit_object.matrix_world * tLoc
        coChg = -(oldCo - newCo)
        bpy.ops.transform.translate(value=(coChg[0], coChg[1], coChg[2]))


# Performs a scale transformation using the provided sFac (scale factor)
# argument. The scale factor is the result from dividing the user input
# measure (newMeasStor) by the distance between the Anchor and Free
# (currMeasStor). After the object is scaled, it is then translated so the
# Anchor point returns to its "pre-scaled" location.
# takes: refPts (ReferencePoints), sFac (float)
def do_scale(refPts, sFac):
    # store Anchor location for use after scale
    anchCo = refPts.rpLs[0].co3D.copy()
    axMultip, cnstrBlVals = (), ()
    if   refPts.axLock ==  '':
        axMultip, cnstrBlVals = (sFac, sFac, sFac), (True, True, True)
    elif refPts.axLock == 'X':
        axMultip, cnstrBlVals = (sFac, 1, 1), (True, False, False)
    elif refPts.axLock == 'Y':
        axMultip, cnstrBlVals = (1, sFac, 1), (False, True, False)
    elif refPts.axLock == 'Z':
        axMultip, cnstrBlVals = (1, 1, sFac), (False, False, True)
    bpy.ops.transform.resize(value=axMultip, constraint_axis=cnstrBlVals)
    refPts.rpLs[0].update3D()
    # move scaled object so Anchor returns to where it was located
    # before scale was applied
    do_translation("OBJECT", anchCo, refPts.rpLs[0])


# Takes 2D Pivot Point (piv) for piv to temp lines, 2 possible rotation
# coordinates to choose between (rPco, rNco), 2 rotation angles used to
# obtain the coordinates (rPangR, rNangR), 2D mouse location (mouseLoc) for
# determining which rotation coordinate is closest to the cursor, and boolean
# indicating whether the left mouse button was clicked (Lclick).
# Returns New 3D Location chosen by user
# rPco == rotation Positive coordinate, rNco == rot Negative coor
# todo : redo way args passed to choose_0_or_180 ?
def choose_0_or_180(piv, rPco, rPangR, rNco, rNangR, mouseLoc, Lclick):
    global RegRv3d
    region, rv3d = RegRv3d[0], RegRv3d[1]
    rPco_2D = location_3d_to_region_2d(region, rv3d, rPco)
    rNco_2D = location_3d_to_region_2d(region, rv3d, rNco)
    piv2D = location_3d_to_region_2d(region, rv3d, piv.co3D)
    ms_co1_dis = get_dist(rPco_2D, mouseLoc)
    ms_co2_dis = get_dist(rNco_2D, mouseLoc)
    # draw both buttons and wait for Lmouse click input
    if   ms_co1_dis < ms_co2_dis:
        draw_line_2D(piv2D, rPco_2D, Colr.green)
        draw_pt_2D(rPco_2D, Colr.green, 14)
        draw_pt_2D(rNco_2D, Colr.grey)
        if Lclick:
            #print("Chose coor rPco!")  # debug
            return rPco, rPangR
    elif ms_co2_dis < ms_co1_dis:
        draw_line_2D(piv2D, rNco_2D, Colr.green)
        draw_pt_2D(rNco_2D, Colr.green, 14)
        draw_pt_2D(rPco_2D, Colr.grey)
        if Lclick:
            #print("Chose coor rNco!")  # debug
            return rNco, rNangR
    else:
        draw_pt_2D(rPco_2D, Colr.grey)
        draw_pt_2D(rNco_2D, Colr.grey)
    return None, None


# Reduces the provided rotation amount (newMsStor) to an "equivalent" value
# less than or equal to 180 degrees. Calculates the angle offset from
# currMsStor to achieve a newMsStor value. Finally, copies axis lock info
# from refPts to rDat.
def prep_rotation_info(refPts, rDat, currMsStor, newMsStor):
    #print("curr angle", currMsStor)  # debug
    #print("new angle", newMsStor)  # debug

    # workaround for angles over 360 degrees and negative angles
    if newMsStor > 360 or newMsStor < 0:
        newMsStor = newMsStor % 360
    rDat.angDiffD = newMsStor - currMsStor
    # fix for angles over 180 degrees
    if newMsStor > 180:
        rDat.newAngR = radians(180 - (newMsStor % 180))
    else:
        rDat.newAngR = radians(newMsStor)
    rDat.angDiffR = radians(rDat.angDiffD)
    rDat.axisLk = refPts.axLock


# Takes: self, newFreeCo (Vector) as args. Uses newFreeCo to calculate
# the rotation value and then does a rotation on the selected objects or
# vertices using the obtained value.
def do_rotate(EdType, newFreeCo, refPts, rDat):
    #print("angDiffRad", rDat.angDiffR," angDiffReg", degrees(rDat.angDiffR))  # debug
    Free = refPts.rpLs[2]
    axisLock = refPts.axLock
    objs = bpy.context.scene.objects  # shorthand

    opsAxLock = ()
    if   axisLock == 'X': opsAxLock = 1, 0, 0
    elif axisLock == 'Y': opsAxLock = 0, 1, 0
    elif axisLock == 'Z': opsAxLock = 0, 0, 1
    elif axisLock ==  '': opsAxLock = rDat.pivNorm

    if EdType == "OBJECT":
        bpy.ops.transform.rotate(value=rDat.angDiffR, axis=opsAxLock,
                constraint_axis=(False, False, False))
        Free.update3D()
        coChg = -(Free.co3D - newFreeCo)  # coChg = coordinate change
        bpy.ops.transform.translate(value=(coChg[0], coChg[1], coChg[2]))

    elif EdType == "EDIT_MESH":
        bpy.ops.transform.rotate(value=rDat.angDiffR, axis=opsAxLock,
                constraint_axis=(False, False, False))
        EditModeRefresh(EdType)
        Free.update3D()
        tLoc = objs[Free.objInd].data.vertices[Free.vertInd].co
        oldCo = bpy.context.edit_object.matrix_world * tLoc
        coChg = -(oldCo - newFreeCo)
        bpy.ops.transform.translate(value=(coChg[0], coChg[1], coChg[2]))


# == pop-up dialog code ==
# todo: update with newer menu code if it can ever be made to work
class ChangeInputPanel(bpy.types.Operator):
    bl_idname = "object.ms_input_dialog_op"
    bl_label = "Measurement Input Panel"
    bl_options = {'INTERNAL'}

    float_new_meas = bpy.props.FloatProperty(name="Measurement")

    def execute(self, context):
        global popUpActive, newMeasStor  #, currMeasStor
        #print("currMeasStor:", currMeasStor)  # debug
        newMeasStor = self.float_new_meas
        #print("newMeasStor:", newMeasStor)  # debug
        popUpActive = False
        return {'FINISHED'}

    def invoke(self, context, event):
        global currMeasStor
        self.float_new_meas = currMeasStor
        return context.window_manager.invoke_props_dialog(self)

    def cancel(self, context):  # testing
        global popUpActive
        #print("Cancelled Pop-Up")  # debug
        popUpActive = False

class DialogPanel(bpy.types.Panel):
    def draw(self, context):
        self.layout.operator("object.ms_input_dialog_op")


# Updates lock points and changes currMeasStor to use measure based on
# lock points instead of refPts (for axis constrained transformations).
def updateLockPts(self, refPts):
    global currMeasStor
    setLockPts(refPts)
    if refPts.lpLs == []:
        self.report({'ERROR'}, refPts.axLock+' axis lock creates identical points')
        refPts.lpLs = refPts.rpLs
        refPts.axLock = ''
    # update Measurement in currMeasStor
    LkPts = refPts.lpLs
    if refPts.cnt < 2:
        currMeasStor = 0.0
    elif refPts.cnt == 2:
        currMeasStor = get_dist(LkPts[0].co3D, LkPts[1].co3D)
    elif refPts.cnt == 3:
        lineAngR = getLineAngle3D(LkPts[0].co3D, LkPts[1].co3D, LkPts[2].co3D)
        currMeasStor = degrees(lineAngR)


# See if key was pressed that would require updating the axis lock info.
# If one was, update the lock points to use new info.
def axisKeyCheck(self):
    if self.refPts.cnt < 2:
        self.keyC = self.keyX = self.keyY = self.keyZ = False
    else:
        axis = self.refPts.axLock
        changeLock = False
        if self.keyC:
            if axis != '':
                axis = ''
                changeLock = True
            self.keyC = False
        elif self.keyX:
            if axis != 'X':
                axis = 'X'
                changeLock = True
            self.keyX = False
        elif self.keyY:
            if axis != 'Y':
                axis = 'Y'
                changeLock = True
            self.keyY = False
        elif self.keyZ:
            if axis != 'Z':
                axis = 'Z'
                changeLock = True
            self.keyZ = False
        if changeLock:
            self.refPts.axLock = axis
            updateLockPts(self, self.refPts)


# Adjusts settings so procClick can run again for next possible transform
def resetSettings(self):
    global newMeasStor
    newMeasStor = None
    self.LmouseLoc = [-5000, -5000]
    self.LmouseClick = False
    EditModeRefresh(self.currEdType)
    for ob in range(self.refPts.cnt):
        self.refPts.rpLs[ob].update3D()
        self.refPts.rpLs[ob].set2D()
    if self.refPts.cnt < 2:
        self.measBtnAct = False
    else:
        updateLockPts(self, self.refPts)
        self.measBtnAct = True
    self.AddOnMode = XO_CLICK_CHECK
    setLockPts(self.refPts)

    # restore selected items (except Anchor)
    # needed so update selection will work correctly
    self.sel_backup.restoreSelected(self.currEdType)

    # make sure last transform didn't cause points to overlap
    PtA = self.refPts.rpLs[0].co3D
    PtB = self.refPts.rpLs[self.refPts.cnt - 1].co3D
    if floatsAlmEq(PtA[0], PtB[0]): 
        if floatsAlmEq(PtA[1], PtB[1]):
            if floatsAlmEq(PtA[2], PtB[2]):
                self.report({'ERROR'}, 'Free and Anchor share same location.')
                self.refPts = ReferencePoints()  # reset ref pt data


# Can a transformation be performed?
def canTransf(self):
    global popUpActive, currMeasStor
    success = False
    if self.refPts.cnt == 2:
        # activate scale mode if Anchor and Free attached to same object
        self.transfMode = XO_MOVE
        if self.currEdType == "OBJECT":
            if self.refPts.rpLs[0].objInd == self.refPts.rpLs[1].objInd:
                self.transfMode = XO_SCALE
                success = True
            else:
                success = True
        elif self.currEdType == "EDIT_MESH" and \
        bpy.context.scene.objects[self.refPts.rpLs[1].objInd].mode != 'EDIT':
            self.report({'ERROR'}, 'Free must be in active mesh in Edit Mode.')
        else:
            success = True
    elif self.refPts.cnt == 3:
        self.transfMode = XO_ROTATE
        if self.currEdType == "OBJECT" and \
        self.refPts.rpLs[0].objInd == self.refPts.rpLs[2].objInd:
            self.report({'ERROR'}, "Free & Anchor can't be on same object for rotations.")
        elif self.currEdType == "EDIT_MESH" and \
        bpy.context.scene.objects[self.refPts.rpLs[2].objInd].mode != 'EDIT':
            self.report({'ERROR'}, "Free must be in active mesh in Edit Mode.")
        elif self.refPts.axLock != '':
            success = True
        # if not flat angle and no axis lock set, begin preparations for
        # arbitrary axis / spherical rotation
        elif floatsAlmEq(currMeasStor, 0.0) == False and \
        floatsAlmEq(currMeasStor, 180.0) == False:
            AncC = self.refPts.rpLs[0].co3D
            PivC = self.refPts.rpLs[1].co3D
            FreC = self.refPts.rpLs[2].co3D
            self.rDat.pivNorm = geometry.normal(AncC, PivC, FreC)
            success = True
        else:
            # would need complex angle processing workaround to get
            # spherical rotations working with flat angles. todo item?
            # blocking execution for now.
            self.report({'INFO'}, "Need axis lock for O and 180 degree angles.")
    return success


# Handles left mouse clicks, sets and removes reference points, and
# activates the pop-up dialog if the "meas button" is clicked.
def procClick(self):
    global popUpActive
    axisKeyCheck(self)
    if self.LmouseClick:
        self.LmouseClick = False
        if self.measBtnAct and point_inside_loop(self.measBtnCo, self.LmouseLoc):
            if canTransf(self):
                # refresh the viewport and update the selection list just in
                # case we are coming here from an earlier resetSettings call
                # and the selection was changed after that
                EditModeRefresh(self.currEdType)
                self.sel_backup.update(self.currEdType)
                # operation will continue on in background
                # after "ms_input_dialog_op" is called
                # need to have popup loop running and waiting for input
                self.measBtnAct = False
                popUpActive = True
                self.AddOnMode = XO_CHECK_POPUP_INFO
                drawUI(self)
                bpy.ops.object.ms_input_dialog_op('INVOKE_DEFAULT')
            else:
                resetSettings(self)
        else:
            found_pt = find_closest_vert(self.LmouseLoc, self.sel_backup.MshObjs)
            if found_pt != None:
                self.refPts.tryAdd(found_pt)
                setLockPts(self.refPts)
                if self.refPts.cnt < 2:
                    self.measBtnAct = False
                else:
                    updateLockPts(self, self.refPts)
                    self.measBtnAct = True


# Generates a list of which selected mesh objects or selected vertices will
# remain selected based on the editor type, the transform mode, and whether
# the Free was part of the selected geometry. Mesh objects or vertices are
# then selected or unselected to match the contents of the generated list.
def prepareSelected(selBak, refPts, EdType, transfMode):
    objs = bpy.context.scene.objects  # shorthand
    anch = refPts.rpLs[0]
    free = refPts.rpLs[refPts.cnt - 1]
    freeInSel = False
    selectedLs = None

    if EdType == "OBJECT":
        selectedLs = selBak.selMshObjs.copy()
        freeInd = free.objInd
        # If Scale Mode, auto-fail freeInSel as Scale only runs on Free Obj
        if transfMode == XO_SCALE:
            freeInSel = False
        else:
            # See if Free's Obj was selected
            if objs[anch.objInd].select:
                selectedLs.remove(anch.objInd)
            if objs[freeInd].select:
                freeInSel = True
        # Unselect everything in case a non-mesh obj was selected
        bpy.ops.object.select_all(action='DESELECT')
        if freeInSel == False:
            selectedLs = [freeInd]
        # Reselect just the mesh objects contained in selectedLs 
        for ind in selectedLs:
            objs[ind].select = True

    elif EdType == "EDIT_MESH":
        selectedLs = selBak.selMshVts.copy()
        freeInd = free.vertInd
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        if hasattr(bm.verts, "ensure_lookup_table"):
            bm.verts.ensure_lookup_table()
        # The 'EDIT' mode check below is not needed as this was
        # already verified in can_transf()
        #if objs[free.objInd].mode == 'EDIT':
        if bm.verts[freeInd].select:
            freeInSel = True
            # Make sure the anchor isn't selected. If it is, "unselect" it.
            # Note that it's not possible to just unselect a single vert
            # without also unselecting ALL edges and faces that vert was
            # a part of. As there does not seem to be any simple method to
            # find and unselect those edges and faces, instead unselect
            # everything and then reselect all the verts that were
            # originally selected, one-by-one, except the the vert that is
            # being "unselected".
            if objs[anch.objInd].mode == 'EDIT':
                if bm.verts[anch.vertInd].select:
                    selectedLs.remove(anch.vertInd)
                    if freeInSel == True:
                        bpy.ops.mesh.select_all(action='DESELECT')
                        for ind in selectedLs:
                            bm.verts[ind].select = True
        # If the Free is not selected the transform will be on the Free only.
        # Unselect everything else and make so only the Free is selected.
        else:
            selectedLs = [freeInd]
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.verts[freeInd].select = True
        EditModeRefresh(EdType)


def doTransform(self):
    global currMeasStor, newMeasStor
    rpLs, axLock = self.refPts.rpLs, self.refPts.axLock
    currEd = self.currEdType

    # Onto Transformations...

    if self.transfMode == XO_GET_0_OR_180:
        self.newFreeCo, self.rDat.angDiffR = choose_0_or_180(rpLs[1],
                *self.modal_buff, self.mouseLoc, self.LmouseClick)
        if self.LmouseClick:
            self.LmouseClick = False
            if self.newFreeCo != ():
                do_rotate(currEd, self.newFreeCo, self.refPts, self.rDat)
            resetSettings(self)

    elif self.transfMode == XO_MOVE:
        newCoor = get_new_3D_co(self, axLock, rpLs, currMeasStor, newMeasStor)
        if newCoor != None:
            #print('newCoor', newCoor)  #, self.refPts.rpLs[1] )  # debug
            do_translation(currEd, newCoor, rpLs[1])
        resetSettings(self)

    elif self.transfMode == XO_SCALE:
        scale_factor = newMeasStor / currMeasStor
        do_scale(self.refPts, scale_factor)
        resetSettings(self)

    elif self.transfMode == XO_ROTATE:
        # for "normal" (non 0_or_180) rotations
        if self.newFreeCo != ():
            do_rotate(currEd, self.newFreeCo, self.refPts, self.rDat)
        resetSettings(self)


def checkPopUpInput(self):
    global popUpActive, currMeasStor, newMeasStor
    if popUpActive == False:
        if newMeasStor != None:
            if self.transfMode == XO_SCALE and newMeasStor < 0:
                self.report({'ERROR'}, 'Scale input cannot be negative.')
                resetSettings(self)
            else:
                prepareSelected(self.sel_backup, self.refPts,
                        self.currEdType, self.transfMode)
                self.AddOnMode = XO_DO_TRANSFORM
                if self.transfMode == XO_ROTATE:
                    prep_rotation_info(self.refPts, self.rDat, currMeasStor, newMeasStor)
                    if floatsAlmEq(currMeasStor, 0.0) or floatsAlmEq(currMeasStor, 180.0):
                        rotDat, angDiffRad = self.rDat, self.rDat.angDiffR
                        Piv, Mov = self.refPts.rpLs[1].co3D, self.refPts.rpLs[2].co3D
                        tmpCoP = getRotatedPoint(Piv, angDiffRad, rotDat, Mov)
                        tmpCoN = getRotatedPoint(Piv, -angDiffRad, rotDat, Mov)
                        self.modal_buff = (tmpCoP, angDiffRad, tmpCoN, -angDiffRad)
                        self.transfMode = XO_GET_0_OR_180
                        doTransform(self)
                    else:
                        self.newFreeCo, self.rDat.angDiffR = \
                                findCorrectRot(self.refPts, self.rDat)
                        doTransform(self)
                else:  # transfMode == XO_MOVE
                    doTransform(self)
        else:
            resetSettings(self)


def exit_addon(self):
    for i in self.sel_backup.selNMObjs:
        self.sel_backup.obj[i].select = True
    #print("\n\n\n  Add-On Exited!\n")  # debug


def draw_callback_px(self, context):
    draw_logo(  "Exact", [10, 92])
    draw_logo("Offsets", [10, 78])
    getRegRv3d()

    if self.AddOnMode == XO_CLICK_CHECK:
        procClick(self)

    elif self.AddOnMode == XO_CHECK_POPUP_INFO:
        checkPopUpInput(self)

    elif self.AddOnMode == XO_DO_TRANSFORM:
        doTransform(self)

    self.LmouseClick = False
    if self.refPts.cnt > 0:
        drawUI(self)


class Xoffsets(bpy.types.Operator):
    """Select vertices with the mouse"""
    bl_idname = "view3d.xoffsets_main"
    bl_label = "Exact Offsets"

    # Only launch Add-On when active object is a MESH and Blender
    # is in OBJECT mode or EDIT_MESH mode.
    @classmethod
    def poll(self, context):
        if context.mode == 'OBJECT' or context.mode == 'EDIT_MESH':
            if bpy.context.scene.objects.active != None:
                return bpy.context.scene.objects.active.type == 'MESH'
        else:
            return False

    def modal(self, context, event):
        context.area.tag_redraw()
        self.currEdType = context.mode

        if event.type in {'A', 'MIDDLEMOUSE', 'WHEELUPMOUSE',
        'WHEELDOWNMOUSE', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4',
        'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'TAB'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouseLoc = Vector((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'RIGHTMOUSE':
            if self.LmousePressed:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                exit_addon(self)
                return {'CANCELLED'}
            else:
                return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE':
            self.LmousePressed = event.value == 'PRESS'

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.LmouseClick = True
            self.LmouseLoc = Vector((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'C' and event.value == 'PRESS':
            #print("Pressed C!\n")  # debug
            self.keyC = True

        if event.type == 'X' and event.value == 'PRESS':
            #print("Pressed X!\n")  # debug
            self.keyX = True

        if event.type == 'Y' and event.value == 'PRESS':
            #print("Pressed Y!\n")  # debug
            self.keyY = True

        if event.type == 'Z' and event.value == 'PRESS':
            #print("Pressed Z!\n")  # debug
            self.keyZ = True

        if event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            exit_addon(self)
            return {'CANCELLED'}

        if self.exitCheck:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            exit_addon(self)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                    draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.currEdType = context.mode  # current Blender Editor Type
            self.transfMode = ""  # transform mode
            self.AddOnMode = XO_CLICK_CHECK  # transform mode
            self.rDat = RotationData()
            self.newFreeCo = ()  # new Free Coordinates
            self.refPts = ReferencePoints()
            self.sel_Stor = []  # selection storage
            self.sel_backup = SceneSelectionInfo()
            self.measBtnCo = []
            self.measBtnAct = False  # measure button active
            self.modal_buff = []
            self.mouseLoc = Vector((event.mouse_region_x, event.mouse_region_y))
            self.LmousePressed = False
            self.LmouseClick = False
            self.LmouseLoc = []
            self.keyC = False
            self.keyX = False
            self.keyY = False
            self.keyZ = False
            self.exitCheck = False

            #print("Exact Offsets started!")  # debug
            self.sel_backup.startRun(self.currEdType)
            EditModeRefresh(self.currEdType)  # refresh the viewport
            context.window_manager.modal_handler_add(self)
            getRegRv3d()

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(Xoffsets)
    bpy.utils.register_class(ChangeInputPanel)

def unregister():
    bpy.utils.unregister_class(Xoffsets)
    bpy.utils.unregister_class(ChangeInputPanel)

if __name__ == "__main__":
    register()
