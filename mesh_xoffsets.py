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

mesh_xoffsets.py (alpha version 005)

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
    "version": (0, 0, 5),
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
from math import fmod, sqrt, degrees, radians
from mathutils import Vector, geometry, Quaternion, Euler
from mathutils.geometry import intersect_line_line_2d
from bpy_extras.view3d_utils import location_3d_to_region_2d
#import code
#code.interact(local=locals())
#__import__('code').interact(local=dict(globals(), **locals()))

print("Exact Offsets loaded")

(    SET_REF_PTS,
    GET_TRANSF_MODE,
    CHECK_POPUP_INFO,
    DO_TRANSFORM,
    GET_0_OR_180,
    MOVE,
    SCALE,
    ROTATE,
) = range(8)

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


# vertex storage class, stores reference point info
class vertObj:
    def __init__(self, objInd=-1, vertInd=-1, co3D=[], co2D=[], dist2D=-1, refInd=-1):
        self.objInd = objInd
        self.vertInd = vertInd
        self.co3D = co3D
        self.co2D = co2D
        self.dist2D = dist2D
        self.refInd = refInd
        self.obj = bpy.context.scene.objects # short hand, for internal use

    def copy(self): # return independent copy of vertObj
        return vertObj( self.objInd, self.vertInd, self.co3D.copy(), [*self.co2D], self.dist2D, self.refInd )

    def set2D(self):
        global RegRv3d
        region, rv3d = RegRv3d[0], RegRv3d[1]
        self.co2D = location_3d_to_region_2d(region, rv3d, self.co3D)

    def update3D(self):
        tmpCoLocal = self.obj[self.objInd].data.vertices[self.vertInd].co
        self.co3D = self.obj[self.objInd].matrix_world * tmpCoLocal


# stores info for the reference points info
class referencePoints():
    def __init__(self, count=0, rLs=[(),(),()], mLs=[(),(),()], axisLock='', col_ls=[]):
        self.cnt = count
        self.rLs = rLs
        self.mLs = mLs
        self.axLock = axisLock
        self.col_ls = col_ls
        self.colorRed   = [1.0, 0.0, 0.0, 0.5]
        self.colorGreen = [0.0, 1.0, 0.0, 0.5]
        self.colorBlue  = [0.0, 0.0, 1.0, 0.5]

    def update_col_ls(self):
        if self.cnt < 3:
            self.col_ls = [self.colorRed,self.colorGreen]
        else: # self.cnt > 2
            self.col_ls = [self.colorRed,self.colorBlue,self.colorGreen]

    def removePt(self,remInd):
        # hackery or smart, you decide...
        if remInd != self.cnt - 1:
            ind = [0,1,2][:self.cnt]
            ind.remove(remInd)
            for i in range(len(ind)):
                self.rLs[i] = self.rLs[ind[i]].copy()
                self.rLs[i].refInd = i
        self.cnt -= 1

    def tryAdd(self,found_pt):
        if self.cnt > 0:
            for rp in range(self.cnt):
                if self.rLs[rp].co3D == found_pt.co3D:
                    self.axLock = ''
                    self.removePt( self.rLs[rp].refInd )
                    self.mLs = self.rLs
                    #print("ref pt removed:",rp,"cnt:",self.cnt) # debug
                    self.update_col_ls()
                    return
        if self.cnt < 3:
            self.rLs[self.cnt] = found_pt
            self.rLs[self.cnt].refInd = self.cnt
            ''' Begin Debug 
            ptFndStr = str(self.rLs[self.cnt].co3D)
            ptFndStr = ptFndStr.replace("<Vector ","Vector(")
            ptFndStr = ptFndStr.replace(">",")")
            print("Ref_pt_" + str(self.cnt) +' =',ptFndStr)
            #print("ref pt added:",self.cnt,"cnt:",self.cnt+1) 
            End Debug ''' 
            self.cnt += 1
        self.update_col_ls()
        return


# stores rotation info
# for passing data from draw_callback_px to external functions
# not as bad as hiding arguments in passed variables, but still seems hackish
class rotationData:
    def __init__(self):
        self.newAngR = 0.0
        self.newAngD = 0.0
        self.angDiffD = 0.0
        self.angDiffR = 0.0
        self.axisLk = ''
        self.pivNorm = [] # pivot normal
        #self.angleEq_0_180 = False
        #self.obj = bpy.context.scene.objects[self.objInd] # short hand


### linear equations ### 

#def getMidpoint2D(x1,y1,x2,y2):
#    return ( (x1+x2)/2 , (y1+y2)/2 )


def getMidpoint3D(ptA, ptB):
    x1,y1,z1 = ptA[0],ptA[1],ptA[2]
    x2,y2,z2 = ptB[0],ptB[1],ptB[2]
    return Vector([ (x1+x2)/2 , (y1+y2)/2 , (z1+z2)/2 ])


def get_dist_2D(ptA, ptB):
    x1,y1 = ptA[0],ptA[1]
    x2,y2 = ptB[0],ptB[1]
    return sqrt( abs( ((x2-x1)**2) + ((y2-y1)**2) ) )


def get_dist_3D(ptA, ptB):
    x1,y1,z1 = ptA[0],ptA[1],ptA[2]
    x2,y2,z2 = ptB[0],ptB[1],ptB[2]
    res = sqrt( abs( ((x2-x1)**2) + ((y2-y1)**2) + ((z2-z1)**2) ) )
    return res


def get_slope_3D(self, ptA, ptB):
    dist3D = get_dist_3D( ptA, ptB )
    x1,y1,z1 = ptA[0],ptA[1],ptA[2]
    x2,y2,z2 = ptB[0],ptB[1],ptB[2]
    if dist3D == 0:
        self.report({'ERROR'}, 'Distance between points cannot be zero.')
        return
    xSlope = (x1 - x2) / dist3D
    ySlope = (y1 - y2) / dist3D
    zSlope = (z1 - z2) / dist3D
    return ( xSlope, ySlope, zSlope )


def get_new_pt_3D(xyz,slope3D,dis3D):
    #newX = (x1 +- ( dis3D * slopeX ) )
    x1,y1,z1 = xyz[0], xyz[1], xyz[2]
    slopeX,slopeY,slopeZ = slope3D[0],slope3D[1],slope3D[2]
    newX = x1 + ( dis3D * slopeX )
    newY = y1 + ( dis3D * slopeY )
    newZ = z1 + ( dis3D * slopeZ )
    return Vector([newX,newY,newZ])


# for making sure rise over run doesn't get flipped
def slope_check(pt1,pt2):
    cmp = ( pt1[0] >= pt2[0], pt1[1] >= pt2[1], pt1[2] >= pt2[2] )
    return cmp


# todo: split into 2 functions ?
# finds 3D location that shares same slope of line connecting Anchor and
# Free or is on axis line going through Anchor
def get_new_3D_coor(self,lock, ptA, ptF, newDis):
    ptN_1, ptN_2 = (), ()
    if lock == '':
        if newDis == 0:
            return ptA
        origSlope = slope_check(ptA, ptF)
        slope3D = get_slope_3D(self, ptF, ptA )
        ptN_1 = get_new_pt_3D( ptA, slope3D, newDis )
        ptN_2 = get_new_pt_3D( ptA, slope3D, -newDis )
        ptN_1_slp = slope_check( ptA, ptN_1 )
        ptN_2_slp = slope_check( ptA, ptN_2 )
        if   origSlope == ptN_1_slp:
            if newDis > 0:
                return ptN_1
            else:
            # for negative distances
                return ptN_2
        elif origSlope == ptN_2_slp:
            if newDis > 0:
                return ptN_2
            else:
                return ptN_1
        else: # neither slope matches
            self.report({'ERROR'}, 'Slope mismatch. Cannot calculate new point.')
            return []
    elif lock == 'X':
        if ptF[0] > ptA[0]: return Vector([ ptA[0] + newDis, ptF[1], ptF[2] ])
        else: return Vector([ ptA[0] - newDis, ptF[1], ptF[2] ])
    elif lock == 'Y':
        if ptF[1] > ptA[1]: return Vector([ ptF[0], ptA[1] + newDis, ptF[2] ])
        else: return Vector([ ptF[0], ptA[1] - newDis, ptF[2] ])
    elif lock == 'Z':
        if ptF[2] > ptA[2]: return Vector([ ptF[0], ptF[1], ptA[2] + newDis ])
        else: return Vector([ ptF[0], ptF[1], ptA[2] - newDis ])
    else: # neither slope matches
        self.report({'ERROR'}, "Slope mismatch. Can't calculate new point.")
        return []


# Floating point math fun!  Since equality tests on floats are a crap shoot,
# instead check if floats are almost equal (is the first float within a
# certain tolerance amount of the second).
# Note, this function may fail in certain circumstances depending on the
# number of significant figures. If comparisons become problematic, you can
# try a different power of ten for the "tol" value (eg 0.01 or 0.00001)
# todo: replace this with Python 3.5's math.isclose() ?
# do recent versions of Blender support math.isclose()?
def AreFloatsEq(flt_A,flt_B):
    tol = 0.0001
    return flt_A > (flt_B - tol) and flt_A < (flt_B + tol)


# Aco, Bco, and Cco are Vector based 3D coordinates
# coordinates must share a common center "pivot" point (Bco)
def getLineAngle3D(Aco, Bco, Cco):
    # todo, more testing on Vector's built-in angle measure method
    algnAco = Aco - Bco
    algnCco = Cco - Bco
    return algnAco.angle(algnCco)


# checks if 3 coordinates create an angle that matches the expected angle
def angleMatch3D(pt1,pt2,pt3,expAng):
    angMeas = getLineAngle3D(pt1,pt2,pt3)
    #print("pt1",pt1) # debug
    #print("pt2",pt2) # debug
    #print("pt3",pt3) # debug
    #print( "expAng ",expAng ) # debug
    #print( "angMeas ",angMeas ) # debug
    return AreFloatsEq(angMeas,expAng)


# Calculates rotation around axis or face normal at Pivot's location.
# Takes two 3D coordinate Vectors (PivC and movCo), rotation angle in
# radians (angleDiffRad), and rotation data storage object (rotDat).
# Aligns movCo to world origin (0, 0, 0) and rotates aligned
# movCo (movAligned) around axis stored in rotDat. After rotation,
# removes world-origin alignment.
def getRotatedPoint(PivC,angleDiffRad,rotDat,movCo):
    axisLk = rotDat.axisLk
    movAligned = movCo - PivC
    rotVal = []
    if   axisLk == '': # arbitrary axis / spherical rotations
        rotVal = Quaternion(rotDat.pivNorm, angleDiffRad)
    elif axisLk == 'X':
        rotVal = Euler((angleDiffRad,0.0,0.0), 'XYZ')
    elif axisLk == 'Y':
        rotVal = Euler((0.0,angleDiffRad,0.0), 'XYZ')
    elif axisLk == 'Z':
        rotVal = Euler((0.0,0.0,angleDiffRad), 'XYZ')
    movAligned.rotate(rotVal)
    return movAligned + PivC


# takes axis (str), list of 3D coordinates, and amount of 3D coordinates (int)
# returns modified list of 3D coordinates or empty tuple if problem
# returns supplied list of 3D coordinates if no axis lock
# todo : send transfMode instead of refCount ?
# todo : move inside referencePoints class ?
def setLockPts(axis, rPts, refCount):
    if refCount < 2:
        return []
    if axis == '':
        return rPts
    else:
        NewPtLs = [ vertObj(), vertObj() ]
        rPts2 = [rPts[i].co3D for i in range(refCount)] # shorthand
        if refCount == 2:  # translate
        # finds 3D midpoint between 2 supplied coordinates
        # axis determines which coordinates are assigned midpoint values
        # if X, Anchor is [AncX,MidY,MidZ] and Free is [FreeX,MidY,MidZ]
            mid3D = getMidpoint3D( rPts2[0], rPts2[1] )
            if axis == 'X':
                NewPtLs[0].co3D = Vector([ rPts2[0][0], mid3D[1], mid3D[2] ])
                NewPtLs[1].co3D = Vector([ rPts2[1][0], mid3D[1], mid3D[2] ])
            elif axis == 'Y':
                NewPtLs[0].co3D = Vector([ mid3D[0], rPts2[0][1], mid3D[2] ])
                NewPtLs[1].co3D = Vector([ mid3D[0], rPts2[1][1], mid3D[2] ])
            elif axis == 'Z':
                NewPtLs[0].co3D = Vector([ mid3D[0], mid3D[1], rPts2[0][2] ])
                NewPtLs[1].co3D = Vector([ mid3D[0], mid3D[1], rPts2[1][2] ])
            if NewPtLs[0].co3D == NewPtLs[1].co3D:
                # axis lock creates identical points, return empty list
                return []

        elif refCount == 3:  # rotate
        # axis determines which of the Free's coordinates are assigned
        # to Anchor and Pivot coordinates eg:
        # if X, Anchor is [FreeX,AncY,AncZ] and Pivot is [FreeX,PivY,PivZ]
            movCo = rPts[2].co3D.copy()
            if axis == 'X':
                NewPtLs[0].co3D = Vector([ movCo[0], rPts2[0][1], rPts2[0][2] ])
                NewPtLs[1].co3D = Vector([ movCo[0], rPts2[1][1], rPts2[1][2] ])
            elif axis == 'Y':
                NewPtLs[0].co3D = Vector([ rPts2[0][0], movCo[1], rPts2[0][2] ])
                NewPtLs[1].co3D = Vector([ rPts2[1][0], movCo[1], rPts2[1][2] ])
            elif axis == 'Z':
                NewPtLs[0].co3D = Vector([ rPts2[0][0], rPts2[0][1], movCo[2] ])
                NewPtLs[1].co3D = Vector([ rPts2[1][0], rPts2[1][1], movCo[2] ])
            if NewPtLs[0].co3D == NewPtLs[1].co3D or \
            NewPtLs[0].co3D == movCo or \
            NewPtLs[1].co3D == movCo:
                # axis lock creates identical points, return empty list
                return []
            else:
                NewPtLs.append( vertObj( -1,-1,movCo,[],-1,-1 ) )

        for itm in NewPtLs: itm.set2D()
        return NewPtLs


# Finds out whether positive rotDat.newAngR or negative rotDat.newAngR
# will result in desired rotation angle.
# todo : move self.refPts.rLs to passed args ?
def findCorrectRot(self, rotDat):
    refPts2 = self.refPts.rLs
    angDiffRad,newAngleRad = rotDat.angDiffR,rotDat.newAngR
    PivPt, movePt = refPts2[1].co3D, refPts2[2].co3D
    tmpCoP = getRotatedPoint(PivPt, angDiffRad,rotDat,movePt)
    tmpCoN = getRotatedPoint(PivPt,-angDiffRad,rotDat,movePt)
    #print("tmpCoP",tmpCoP,"\ntmpCoN",tmpCoN) # debug
    self.refPts.mLs = setLockPts(self.refPts.axLock, refPts2, self.refPts.cnt)
    lockPts = self.refPts.mLs
    # is below check needed? is lockPts tested before findCorrectRot called?
    # will be needed for a selection move?
    if lockPts == []:
        print("lockPts == [] CHECK IS NEEDED!")
        self.refPts.mLs = refPts2
        self.refPts.axLock = ''
        return ()
    else:
        if angleMatch3D(lockPts[0].co3D,lockPts[1].co3D,tmpCoP,newAngleRad):
            #print("matched positive tmpCo") # debug
            return tmpCoP, angDiffRad
        else:
            #print("matched negative tmpCo") # debug
            return tmpCoN, -angDiffRad


## point finding code ##

def find_closest_vert(obInd,loc,meshObj):
    meshDat = meshObj.data
    closVert = vertObj()
    for i, v in enumerate(meshDat.vertices):
        tmpOb = vertObj(obInd, i)
        tmpOb.co3D = meshObj.matrix_world * v.co # global instead of local
        tmpOb.set2D()
        tmpOb.dist2D = get_dist_2D( loc, tmpOb.co2D )
        if closVert.dist2D != -1:
            if closVert.dist2D > tmpOb.dist2D:
                closVert = tmpOb
        else:
            closVert = tmpOb
    return closVert


def find_all(co_find):
    closest = vertObj()
    indexLs = []
    objLen = len(bpy.context.scene.objects)
    for i in range(objLen):
        if bpy.context.scene.objects[i].type == 'MESH':
            indexLs.append(i)
    for iNum in indexLs:
        meshC = bpy.context.scene.objects[iNum]
        tempOb = find_closest_vert(iNum, co_find, meshC)
        if closest.dist2D == -1:
            closest = tempOb
        else:
            if tempOb.dist2D < closest.dist2D:
                closest = tempOb
    if closest.dist2D < 40:
        return closest
    else:
        return []


### GL drawing code ### 

def draw_font_at_pt(text, pt_co, pt_color):
    font_id = 0
    bgl.glColor4f(*pt_color) # grey
    blf.position(font_id, pt_co[0], pt_co[1], 0)
    blf.size(font_id, 32, 72)
    blf.draw(font_id, text)
    w, h = blf.dimensions(font_id, text)
    return [w, h]


def draw_pt_2D(pt_co, pt_color,sz=8):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glPointSize(sz)
    bgl.glColor4f(*pt_color)
    bgl.glBegin(bgl.GL_POINTS)
    bgl.glVertex2f(*pt_co)
    bgl.glEnd()
    return


def draw_line_2D (pt_co_1, pt_co_2, pt_color):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glPointSize(7)
    bgl.glColor4f(*pt_color)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f( *pt_co_1 )
    bgl.glVertex2f( *pt_co_2 )
    bgl.glEnd()
    return


def draw_box(boxCo, color):
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for coord in boxCo:
        bgl.glVertex2f( coord[0], coord[1] )
    bgl.glVertex2f( boxCo[0][0], boxCo[0][1] )
    bgl.glEnd()
    return


# == 3D View mouse location and button code ==
# Functions outside_loop() and point_inside_loop() for creating the measure
# change "button" in the 3D View taken from patmo141's Vitual Button script:
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
    #vectorize our two item tuple
    out = Vector(outside_loop(loopCoords))
    vecMous = Vector(mousLoc)
    intersections = 0
    for i in range(0,nverts):
        a = Vector(loopCoords[i-1])
        b = Vector(loopCoords[i])
        if intersect_line_line_2d(vecMous,out,a,b):
            intersections += 1
    inside = False
    if fmod(intersections,2):
        inside = True
    return inside


def get_box_coor(origin,rWidth,rHeight,xOffset,yOffset):
    coBL = (origin[0]-xOffset), (origin[1]-yOffset)
    coTL = (origin[0]-xOffset), (origin[1]+rHeight+yOffset)
    coTR = (origin[0]+rWidth+xOffset), (origin[1]+rHeight+yOffset)
    coBR = (origin[0]+rWidth+xOffset), (origin[1]-yOffset)
    return [coBL, coTL, coTR, coBR]


def sceneRefresh(edType):
    if bpy.context.scene.objects.active.type != 'MESH':
        for i in bpy.context.scene.objects:
            if i.type == 'MESH':
                bpy.context.scene.objects.active = i
                break
    if bpy.context.scene.objects.active.type == 'MESH':
        sObjs = bpy.context.scene.objects
        scn_selected = []
        if edType != "EDIT_MESH":
            scn_selected = [o for o in range(len(sObjs)) if sObjs[o].select]
            bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        if scn_selected != []:
            for i in scn_selected: sObjs[i].select = True


# takes vertObj type and 3D coordinate list as arguments, 
# calculates difference between their 3D locations
# to determine translation to apply to object in vertObj arg
def do_translation( mode,newCo,freeObj,selectLs=[],freeInSel=False ):
    coorChange, oldCo = [0,0,0], [0,0,0]
    if mode == "OBJECT":  # get Free's global coordinates
        oldCo = freeObj.co3D
    elif mode == "EDIT_MESH":  # get Free's local coordinates
        oldCo = bpy.context.scene.objects[freeObj.objInd].data.vertices[freeObj.vertInd].co
    for i in range(3):
        if oldCo[i] != newCo[i]:
            coorChange[i] = - ( oldCo[i] - newCo[i] )
        else:
            coorChange[i] = 0
    #print("coorChange",coorChange) # debug
    if mode == "OBJECT":
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects[freeObj.objInd].select = True
        bpy.ops.transform.translate(value=(coorChange[0], coorChange[1], coorChange[2]))
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        return Vector([ *coorChange ])
    elif mode == "EDIT_MESH":
        bm = bmesh.from_edit_mesh( bpy.context.edit_object.data )
        activMW = bpy.context.edit_object.matrix_world
        if hasattr(bm.verts, "ensure_lookup_table"):
            bm.verts.ensure_lookup_table()
        for v2 in selectLs:
            bm.verts[v2].co.x += coorChange[0]
            bm.verts[v2].co.y += coorChange[1]
            bm.verts[v2].co.z += coorChange[2]

        newVertLoc = activMW * bm.verts[freeObj.vertInd].co
        bmesh.update_edit_mesh( bpy.context.scene.objects[freeObj.objInd].data )
        sceneRefresh( mode )
        return newVertLoc


# Performs scale using the result from dividing the user input measure
# (newMeasStor) by the distance between the anchor and free as the
# scale_factor. Then translates scaled object so the Anchor point 
# returns to its pre-scale location
# takes: self, scale_factor (float, sel_backup (list)
# returns: null
def do_scale(self, scale_factor, sel_backup):
    #print("scale!!!!")
    anchNum = self.refPts.rLs[0].objInd
    # store Anchor location for use after scale
    anchCo = self.refPts.rLs[0].co3D
    # todo: check on axis locks for scales to make sure they work right
    # todo: what happens if scale_factor is zero?
    scaleLkMult, cnstrBlVals = (), ()
    if   self.refPts.axLock ==  '':
        scaleLkMult, cnstrBlVals = (scale_factor,scale_factor,scale_factor), (True,True,True)
    elif self.refPts.axLock == 'X':
        scaleLkMult, cnstrBlVals = (scale_factor,1,1), (True,False,False)
    elif self.refPts.axLock == 'Y':
        scaleLkMult, cnstrBlVals = (1,scale_factor,1), (False,True,False)
    elif self.refPts.axLock == 'Z':
        scaleLkMult, cnstrBlVals = (1,1,scale_factor), (False,False,True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects[anchNum].select = True
    bpy.ops.transform.resize(value=scaleLkMult, constraint_axis=cnstrBlVals)
    bpy.ops.object.select_all(action='DESELECT')
    self.refPts.rLs[0].update3D()
    # move scaled object so Anchor returns to where it was located
    # before scale was applied
    do_translation( "OBJECT", anchCo, self.refPts.rLs[0] )
    for obI in range(self.refPts.cnt):
        self.refPts.rLs[obI].update3D()
        self.refPts.rLs[obI].set2D()
    # restore selected items (except Anchor)
    for ind in sel_backup:
        bpy.context.scene.objects[ind].select = True
    resetSettings(self)


# Takes 2D Pivot Point (piv) for piv to temp lines, 2 possible rotation
# coordinates to choose from (rPco,rNco), 2 rotation angles (rPangR,rNangR),
# 2D mouse location for determining which rotation coordinate is closest to
# cursor, and boolean indicating whether left mouse was clicked (Lclick).
# Returns New 3D Location chosen by user
# rPco == rotation Positive coordinate,  rNco == rot Negative coor
# todo : make rPco_2D,rNco_2D vertObj types ?
def choose_0_or_180(piv,rPco,rPangR,rNco,rNangR,mouseLoc,Lclick):
    global RegRv3d  # RegRv3d = (region, rv3d)
    colorGrey = [1.0, 1.0, 1.0, 0.4]
    colorGreen = [0.0, 1.0, 0.0, 0.5]
    region, rv3d = RegRv3d[0], RegRv3d[1]
    rPco_2D = location_3d_to_region_2d(region, rv3d, rPco)
    rNco_2D = location_3d_to_region_2d(region, rv3d, rNco)
    piv2D = location_3d_to_region_2d(region, rv3d, piv.co3D)
    ms_co1_dis = get_dist_2D(rPco_2D, mouseLoc)
    ms_co2_dis = get_dist_2D(rNco_2D, mouseLoc)
    # draw both buttons and wait for Lmouse click input
    if   ms_co1_dis < ms_co2_dis:
        draw_line_2D(piv2D, rPco_2D, colorGreen)
        draw_pt_2D(rPco_2D, colorGreen, 14)
        draw_pt_2D(rNco_2D, colorGrey)
        if Lclick:
            #print("Chose coor rPco!")
            return rPco, rPangR
    elif ms_co2_dis < ms_co1_dis:
        draw_line_2D(piv2D, rNco_2D, colorGreen)
        draw_pt_2D(rNco_2D, colorGreen, 14)
        draw_pt_2D(rPco_2D, colorGrey)
        if Lclick:
            #print("Chose coor rNco!")
            return rNco, rNangR
    else:
        draw_pt_2D(rPco_2D, colorGrey)
        draw_pt_2D(rNco_2D, colorGrey)
    return None, None


# reduces input rotation amount (newMeasStor) to "equivalent" value less
# than or equal to 180 degrees
def find_rotate_amnt(self, currMeasStor):
    global newMeasStor
    #print("curr angle",currMeasStor)
    #print("new angle",newMeasStor)

    # workaround for negative rotation angles
    while newMeasStor < 0:
        newMeasStor = newMeasStor + 360
    # fix for angles over 180 degrees
    if newMeasStor > 360:
        newMeasStor = newMeasStor % 360
    self.rDat.angDiffD = newMeasStor - currMeasStor
    if newMeasStor > 180:
        self.rDat.newAngR = radians(180 - (newMeasStor % 180))
    else:
        self.rDat.newAngR = radians(newMeasStor)
    self.rDat.angDiffR = radians(self.rDat.angDiffD)
    self.rDat.axisLk = self.refPts.axLock


# Takes: newFreeCoor (float), freeInSel (bool), selectedLs (list),
#   sel_backup (list)
# Uses values to calculate rotation value, then performs rotation
def do_rotate(self, newFreeCoor,freeInSel,selectedLs,sel_backup):
    #print("angRadChng",self.rDat.angDiffR," angDegChng",degrees(self.rDat.angDiffR)) # debug
    freeNum = self.refPts.rLs[2].objInd
    freeVerIn = self.refPts.rLs[2].vertInd
    axisLock = self.refPts.axLock

    if newFreeCoor != ():
    # todo: shouldn't above check be before do_rotate ?
    # eg: if newFreeCoor != (): do_rotate(); else self.AddOnMode = SET_REF_PTS

        pivC = self.refPts.rLs[1].co3D
        if self.currEdType == "OBJECT":
            opsAxLock = ()
            if   axisLock == 'X': opsAxLock = (1, 0, 0)
            elif axisLock == 'Y': opsAxLock = (0, 1, 0)
            elif axisLock == 'Z': opsAxLock = (0, 0, 1)
            elif axisLock ==  '': opsAxLock = self.rDat.pivNorm

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects[freeNum].select = True
            bpy.ops.transform.rotate(value=self.rDat.angDiffR, axis=opsAxLock, constraint_axis=(False, False, False))

            bpy.ops.object.select_all(action='DESELECT')
            self.refPts.rLs[2].update3D()
            # Free is rotated first
            do_translation( "OBJECT", newFreeCoor, self.refPts.rLs[2] )

            # Code below isn't pretty, but works for now...
            # Basically it takes object numbers stored in selectedLs and uses
            # them to create vertObj objects, but using selected object's
            # origins as "Free vertex" values instead of actual Free vertex.
            # Then it rotates these "Free vertex" values around Anchor by
            # radian value stored in self.rDat.angDiffR
            # todo: clean this up along with the rest of the selectedLs code
            if freeInSel:
                for ob in selectedLs:
                    newOb = vertObj( ob, -1, Vector([*bpy.context.scene.objects[ob].location]) )
                    lockPts = setLockPts(axisLock,[self.refPts.rLs[0],self.refPts.rLs[1],newOb], self.refPts.cnt) # todo
                    if (lockPts != []):
                        glbCo = lockPts[2].co3D
                        tmpCo = getRotatedPoint(pivC,self.rDat.angDiffR,self.rDat,glbCo)
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.scene.objects[ob].select = True
                        bpy.ops.transform.rotate(value=self.rDat.angDiffR, axis=opsAxLock, constraint_axis=(False, False, False))

                        bpy.ops.object.select_all(action='DESELECT')
                        newOb.co3D = Vector([ *bpy.context.scene.objects[ob].location ])
                        do_translation( "OBJECT", tmpCo, newOb )
            # restore selected items (except Anchor)
            for ind in sel_backup:
                bpy.context.scene.objects[ind].select = True

        elif self.currEdType == "EDIT_MESH":
            bm = bmesh.from_edit_mesh( bpy.context.edit_object.data )
            activMW = bpy.context.edit_object.matrix_world
            inverMW = bpy.context.edit_object.matrix_world.inverted()
            bm.verts[freeVerIn].co = inverMW * Vector( newFreeCoor )
            # if Free was in a selection, rotate the rest of the selection
            if freeInSel:
                newPt = vertObj()
                for v2 in selectedLs:
                    newPt.co3D = activMW * bm.verts[v2].co
                    lockPts = setLockPts( self.refPts.axLock,[self.refPts.rLs[0],self.refPts.rLs[1],newPt], self.refPts.cnt)
                    if (lockPts != []):
                        glbCo = lockPts[2].co3D
                        # can't just send rDat because of findCorrectRot()
                        tmpCo = getRotatedPoint(pivC,self.rDat.angDiffR,self.rDat,glbCo)
                        bm.verts[v2].co = inverMW * tmpCo

            bmesh.update_edit_mesh( bpy.context.scene.objects[freeNum].data )  # refresh data?

    # update 3D View and coordinates
    sceneRefresh( self.currEdType )

    for obI in range(self.refPts.cnt):
        self.refPts.rLs[obI].update3D()
        self.refPts.rLs[obI].set2D()


'''
# for testing / debug purposes, may use later for UI elements
# finds 0 and 180 degree reference points
def draw_pts_0_180(self,ptLs,axisLock,Color):
    AncC = ptLs[0].co3D
    PivC = ptLs[1].co3D
    FreC = ptLs[2].co3D
    region = bpy.context.region
    rv3d = []
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D": 
            rv3d = area.spaces[0].region_3d
            break
    A2P_dis = get_dist_3D( AncC, PivC )
    P2F_dis = get_dist_3D( PivC, FreC )
    dis180 = A2P_dis + P2F_dis
    co180 = get_new_3D_coor(self,'',AncC, PivC, dis180)
    co000 = get_new_3D_coor(self,'',PivC, AncC, P2F_dis)
    co180_2d, co000_2d = [], []

    if axisLock == '':
        co180_2d = location_3d_to_region_2d(region, rv3d, [ co180[0],co180[1],co180[2] ])
        co000_2d = location_3d_to_region_2d(region, rv3d, [ co000[0],co000[1],co000[2] ])
    elif axisLock == 'X':
        co180_2d = location_3d_to_region_2d(region, rv3d, [ FreC[0],co180[1],co180[2] ])
        co000_2d = location_3d_to_region_2d(region, rv3d, [ FreC[0],co000[1],co000[2] ])
    elif axisLock == 'Y':
        co180_2d = location_3d_to_region_2d(region, rv3d, [ co180[0],FreC[1],co180[2] ])
        co000_2d = location_3d_to_region_2d(region, rv3d, [ co000[0],FreC[1],co000[2] ])
    elif axisLock == 'Z':
        co180_2d = location_3d_to_region_2d(region, rv3d, [ co180[0],co180[1],FreC[2] ])
        co000_2d = location_3d_to_region_2d(region, rv3d, [ co000[0],co000[1],FreC[2] ])
    draw_pt_2D( co180_2d, Color )
    draw_pt_2D( co000_2d, Color )
'''


def draw_btn(text, co2D, mouseLoc, colorOff, colorOn):
    color = colorOff
    offSet = 5
    font_id = 0
    blf.size(font_id, 32, 72)
    w, h = blf.dimensions(font_id, text)
    textCoor = (co2D[0] - w/2, (co2D[1] + 5*offSet))
    boxCo = get_box_coor(textCoor, w, h, offSet, offSet)

    bgl.glColor4f(*color)
    blf.position(font_id, textCoor[0], textCoor[1], 0.0)
    blf.draw(font_id, text)
    if point_inside_loop(boxCo,mouseLoc):
        color = colorOn

    draw_box(boxCo, color)
    return boxCo


def drawAllPts(self):
    global currMeasStor
    refPts,btnDrawn,lockPts = self.refPts,self.btnDrawn,self.refPts.mLs
    if refPts.cnt == 1:
        refPts.rLs[0].set2D()
        draw_pt_2D(refPts.rLs[0].co2D, refPts.col_ls[0])
    else:
        midP = []
        if refPts.cnt < 3:
            midP = vertObj( -1,-1,getMidpoint3D( refPts.rLs[0].co3D, refPts.rLs[1].co3D ))
        else:
            midP = vertObj( -1,-1,lockPts[1].co3D.copy() )

        lastPt = []
        if refPts.axLock == '':
            for i in range( refPts.cnt ):
                refPts.rLs[i].set2D()
                draw_pt_2D(refPts.rLs[i].co2D, refPts.col_ls[i])
                if lastPt != []:
                    draw_line_2D(lastPt, refPts.rLs[i].co2D, refPts.col_ls[0])
                lastPt = refPts.rLs[i].co2D
        else:
            if   refPts.axLock == 'X':
                draw_font_at_pt ( refPts.axLock, [70,70], refPts.colorRed )
            elif refPts.axLock == 'Y':
                draw_font_at_pt ( refPts.axLock, [70,70], refPts.colorGreen )
            elif refPts.axLock == 'Z':
                draw_font_at_pt ( refPts.axLock, [70,70], refPts.colorBlue )
            for i in range( refPts.cnt ):
                refPts.rLs[i].set2D()
                draw_pt_2D(refPts.rLs[i].co2D, refPts.col_ls[i])
                refPts.mLs[i].set2D()
                draw_pt_2D(refPts.mLs[i].co2D, refPts.col_ls[i])
                if lastPt != []:
                    draw_line_2D(lastPt, refPts.mLs[i].co2D, refPts.col_ls[0])
                lastPt = refPts.mLs[i].co2D

        if btnDrawn:
            colorWhite = [1.0, 1.0, 1.0, 1.0]
            midP.set2D()
            MeasStr = format(currMeasStor, '.2f')
            self.boxCo = draw_btn(MeasStr, midP.co2D, self.mouseLoc,colorWhite,refPts.col_ls[0])


# == pop-up dialog code ==
# todo: update with newer menu code if it can ever be made to work
class changeInputPanel(bpy.types.Operator):
    bl_idname = "object.ms_input_dialog_op"
    bl_label = "Measurement Input Panel"
    bl_options = {'INTERNAL'}

    float_new_meas = bpy.props.FloatProperty(name="Measurement")

    def execute(self, context):
        global popUpActive, newMeasStor #, currMeasStor
        #print("currMeasStor:",currMeasStor) # debug
        newMeasStor = self.float_new_meas
        #print("newMeasStor:",newMeasStor) # debug
        popUpActive = False
        return {'FINISHED'}

    def invoke(self, context, event):
        global currMeasStor
        self.float_new_meas = currMeasStor
        return context.window_manager.invoke_props_dialog(self)

    def cancel(self, context): # testing
        global popUpActive
        #print("Cancelled Pop-Up")
        popUpActive = False
        #newMeasStor = None

class DialogPanel(bpy.types.Panel):
    def draw(self, context):
        self.layout.operator("object.ms_input_dialog_op")


# updates lock points and changes measure to use lockpoints
# instead of refPts (for axis restrained transformations)
def updateLockPts(self, axis):
    global currMeasStor
    self.refPts.mLs = setLockPts(axis, self.refPts.rLs, self.refPts.cnt)
    if self.refPts.mLs == []:
        self.report({'ERROR'}, axis+' axis lock creates identical points')
        self.refPts.mLs = self.refPts.rLs
        self.refPts.axLock = ''
    # update Measurement in currMeasStor
    LkPts = self.refPts.mLs
    if self.refPts.cnt < 2:
        currMeasStor = 0.0
    elif self.refPts.cnt == 2:
        currMeasStor = get_dist_3D(LkPts[0].co3D, LkPts[1].co3D)
    elif self.refPts.cnt == 3:
        lineAngR = getLineAngle3D(LkPts[0].co3D, LkPts[1].co3D, LkPts[2].co3D)
        currMeasStor = degrees(lineAngR)


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
            updateLockPts(self, axis)


# adjust settings so procClick can run again for next possible transform
def resetSettings(self):
    self.LmouseLoc = [-5000,-5000]
    self.LmouseClick = False
    if self.refPts.cnt < 2:
        self.btnDrawn = False
    else:
        updateLockPts(self, self.refPts.axLock)
        self.btnDrawn = True
    sceneRefresh(self.currEdType)
    self.AddOnMode = SET_REF_PTS
    self.refPts.mLs = setLockPts(self.refPts.axLock,self.refPts.rLs,self.refPts.cnt)

    # make sure last transform didn't cause points to overlap
    PtA = self.refPts.rLs[0].co3D
    PtB = []
    if self.refPts.cnt == 2:
        PtB = self.refPts.rLs[1].co3D
    elif self.refPts.cnt == 3:
        PtB = self.refPts.rLs[2].co3D
    if AreFloatsEq(PtA[0],PtB[0]): 
        if AreFloatsEq(PtA[1],PtB[1]):
            if AreFloatsEq(PtA[2],PtB[2]):
                self.report({'ERROR'}, 'Free and Anchor share same location.')
                self.exitCheck = True


def procClick(self):
# handles left mouse clicks. sets and removes reference points and
# activates the pop-up dialog if the "button" is clicked
    global popUpActive
    axisKeyCheck(self)

    if self.LmouseClick:
        self.LmouseClick = False
        if self.btnDrawn and point_inside_loop(self.boxCo,self.LmouseLoc):
            self.btnDrawn = False
            if canTransf(self):
                # operation will continue on in background after "ms_input_dialog_op" is called
                # need to have popup loop running and waiting for input
                popUpActive = True
                self.AddOnMode = CHECK_POPUP_INFO
                drawAllPts(self)
                bpy.ops.object.ms_input_dialog_op('INVOKE_DEFAULT')
            else:
                resetSettings(self)
        else:
            found_pt = find_all( self.LmouseLoc )
            if found_pt != []:
                self.refPts.tryAdd(found_pt)
                self.refPts.mLs = setLockPts(self.refPts.axLock,self.refPts.rLs,self.refPts.cnt)

                if self.refPts.cnt < 2:
                    self.btnDrawn = False
                else:
                    updateLockPts(self, self.refPts.axLock)
                    self.btnDrawn = True


def getSelected(refPts, currEdType):
    # First generate list of selected geometry to see if Free was selected
    # for determining whether to run multi-selection transforms and for
    # restoring selected items after object mode transforms.
    # Does not add Free to selected list in object mode and does not add
    # Anchor to selected list in either mode.
    freeInSel = False
    selectedLs = []
    sel_backup = []
    Anchor = refPts.rLs[0]
    Free = []
    if refPts.cnt == 2:
        Free = refPts.rLs[1]
    elif refPts.cnt == 3:
        Free = refPts.rLs[2]

    if currEdType == "OBJECT":
        objLen = len(bpy.context.scene.objects)
        for i in range(objLen):
            if bpy.context.scene.objects[i].select:
                sel_backup.append(i)
            if bpy.context.scene.objects[i].type == 'MESH':
                if bpy.context.scene.objects[i].select:
                    if i == Free.objInd:
                        freeInSel = True
                        #print("freeInSel", freeInSel) # debug
                    elif i != Anchor.objInd:
                        selectedLs.append(i)

    elif currEdType == "EDIT_MESH":
        bm = bmesh.from_edit_mesh( bpy.context.edit_object.data )
        activMW = bpy.context.edit_object.matrix_world
        vertCnt = len(bm.verts)
        for v1 in range(vertCnt):
            if bm.verts[v1].select:
                # todo: add float compare safeguard?
                # compare refPts using vert index instead of coordinates?
                vGlbCo = activMW * bm.verts[v1].co
                if vGlbCo != Anchor.co3D:
                    if vGlbCo == Free.co3D:
                        freeInSel = True
                        #print("freeInSel", freeInSel) # debug
                    selectedLs.append(v1)

    if freeInSel == False:
        if currEdType == "OBJECT":
            selectedLs = [ Free.objInd ]
        elif currEdType == "EDIT_MESH":
            selectedLs = [ Free.vertInd ]
    #print("selectedLs",selectedLs) # debug
    return (freeInSel, selectedLs, sel_backup)


def canTransf(self):
# can a transformation be performed?
    global popUpActive, currMeasStor
    success = False
    if self.refPts.cnt == 2:
        # activate scale mode if Anchor and Free attached to same object
        self.transfMode = MOVE
        if self.currEdType == "OBJECT":
            if self.refPts.rLs[0].objInd == self.refPts.rLs[1].objInd:
                self.transfMode = SCALE
                success = True
            else:
                success = True
        elif self.currEdType == "EDIT_MESH" and \
        bpy.context.scene.objects[self.refPts.rLs[1].objInd].mode != 'EDIT':
            self.report({'ERROR'}, 'Free must be in active mesh in Edit Mode.')
        else:
            success = True
    elif self.refPts.cnt == 3:
        self.transfMode = ROTATE
        if self.currEdType == "OBJECT" and \
        self.refPts.rLs[0].objInd == self.refPts.rLs[2].objInd:
            self.report({'ERROR'}, "Free & Anchor can't be on same object for rotations.")
        elif self.currEdType == "EDIT_MESH" and \
        bpy.context.scene.objects[self.refPts.rLs[2].objInd].mode != 'EDIT':
            self.report({'ERROR'}, "Free must be in active mesh in Edit Mode.")
        elif self.refPts.axLock != '':
            success = True
        # not flat angle and no axis lock set
        elif AreFloatsEq(currMeasStor, 0.0) == False and \
        AreFloatsEq(currMeasStor, 180.0) == False:
            AncC = self.refPts.rLs[0].co3D
            PivC = self.refPts.rLs[1].co3D
            FreC = self.refPts.rLs[2].co3D
            self.rDat.pivNorm = geometry.normal(AncC,PivC,FreC)
            success = True
        else:
            # would need complex angle processing workaround to get
            # spherical rotations working with flat angles. todo item?
            # blocking execution for now.
            self.report({'INFO'}, "Need axis lock for O and 180 degree angles.")
    return success


def checkPopUpInfo(self):
    global popUpActive, newMeasStor, currMeasStor
    if popUpActive == False:
        if newMeasStor != None:
            if self.transfMode == SCALE and newMeasStor < 0:
                self.report({'ERROR'}, 'Scale input cannot be negative.')
                resetSettings(self)
            else:
                self.sel_Stor = getSelected(self.refPts, self.currEdType)
                freeInSel = self.sel_Stor[0]
                self.AddOnMode = DO_TRANSFORM
                if self.transfMode == ROTATE:
                    if freeInSel:
                        if self.currEdType == "EDIT_MESH":
                            self.sel_Stor[1].remove(self.refPts.rLs[2].vertInd)
                    find_rotate_amnt(self, currMeasStor)
                    if AreFloatsEq(currMeasStor, 0.0) or AreFloatsEq(currMeasStor, 180.0):        
                        rotDat, angDiffRad = self.rDat, self.rDat.angDiffR
                        Piv, Mov = self.refPts.rLs[1].co3D, self.refPts.rLs[2].co3D
                        tmpCoP = getRotatedPoint(Piv, angDiffRad,rotDat,Mov)
                        tmpCoN = getRotatedPoint(Piv,-angDiffRad,rotDat,Mov)
                        self.modal_buff = (tmpCoP, angDiffRad, tmpCoN, -angDiffRad)
                        self.transfMode = GET_0_OR_180
                        doTransform(self)
                    else:
                        self.newFreeCoor, self.rDat.angDiffR = findCorrectRot(self, self.rDat)
                        doTransform(self)
                else:
                    doTransform(self)
                
        else:
            #print( "resetSettings(self)" )
            resetSettings(self)


def doTransform(self):
    #print("doTransform") # debug
    global currMeasStor, newMeasStor
    freeInSel,selectedLs,sel_backup = self.sel_Stor[0],self.sel_Stor[1],self.sel_Stor[2]
    rPts,axLock = self.refPts.rLs, self.refPts.axLock

    # Onto Transformations...

    if self.transfMode == GET_0_OR_180:
        self.newFreeCoor, self.rDat.angDiffR = choose_0_or_180(self.refPts.rLs[1], *self.modal_buff,self.mouseLoc,self.LmouseClick)
        if self.LmouseClick:
            self.LmouseClick = False
            if self.newFreeCoor != ():
                do_rotate(self,self.newFreeCoor,freeInSel,selectedLs,sel_backup)
            resetSettings(self)
            
    elif self.transfMode == MOVE:
        newCoor = get_new_3D_coor(self,axLock,rPts[0].co3D,rPts[1].co3D,newMeasStor)
        #print('newCoor',newCoor) #, self.refPts.rLs[1] ) # debug
        if self.currEdType == "OBJECT":

            # translate Free object and get store the translation change info
            chngCo = do_translation( "OBJECT", newCoor, rPts[1] )
            tmpCoLocal = bpy.context.scene.objects[rPts[1].objInd].data.vertices[rPts[1].vertInd].co
            tmpGlob = bpy.context.scene.objects[rPts[1].objInd].matrix_world * tmpCoLocal
            self.refPts.rLs[1].co3D = tmpGlob
            self.refPts.rLs[1].set2D()

            # If more than 1 mesh object was selected and Free was
            # in selection set, translate other selected objects.
            # Use list returned from do_translation operation on
            # Free (chngCo) to do translations
            if freeInSel:
                for ob in selectedLs:
                    coorChange = [0,0,0]
                    newOb = vertObj(ob, -1, Vector([*bpy.context.scene.objects[ob].location]))
                    for i in range(3):
                        coorChange[i] = newOb.co3D[i] + chngCo[i]
                    do_translation( "OBJECT", coorChange, newOb )
            # restore selected items (except Anchor)
            for ind in sel_backup:
                bpy.context.scene.objects[ind].select = True

        elif self.currEdType == "EDIT_MESH":
            inverMW = bpy.context.edit_object.matrix_world.inverted()
            locCo = inverMW * Vector(newCoor)
            newVertLoc = do_translation( "EDIT_MESH", locCo, rPts[1],selectedLs,freeInSel )
            self.refPts.rLs[1].co3D = newVertLoc
            self.refPts.rLs[1].set2D()

        resetSettings(self)

    elif self.transfMode == SCALE:
        scale_factor = newMeasStor / currMeasStor
        do_scale (self, scale_factor, sel_backup)

    elif self.transfMode == ROTATE:
        # gets run for "normal" / non 0_or_180 rotations
        if self.newFreeCoor != ():
            do_rotate(self,self.newFreeCoor,freeInSel,selectedLs,sel_backup)
        resetSettings(self)


def draw_callback_px(self, context):
    getRegRv3d()
    
    if self.AddOnMode == SET_REF_PTS:
        procClick(self)

    elif self.AddOnMode == CHECK_POPUP_INFO:
        checkPopUpInfo(self)
        #print( "window_manager 1st", bpy.context.window_manager.operators[0].name ) # debug
        #print( "window_manager las", bpy.context.window_manager.operators[-1].name ) # debug

    elif self.AddOnMode == DO_TRANSFORM:
        doTransform(self)

    self.LmouseClick = False
    if self.refPts.cnt > 0:
        drawAllPts(self)


class xOffsets(bpy.types.Operator):
    """Select vertices with the mouse"""
    bl_idname = "view3d.xoffsets_main"
    bl_label = "Exact Offsets"

    # Only launch Add-On when active object is a MESH and Blender
    # is in OBJECT mode or EDIT_MESH mode.
    @classmethod
    def poll(self, context):
        if context.mode == 'OBJECT' or context.mode == 'EDIT_MESH':
            return bpy.context.scene.objects.active.type == 'MESH'
        else:
            return False

    def modal(self, context, event):
        context.area.tag_redraw()
        self.currEdType = context.mode

        if event.type in {'A', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'TAB'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouseLoc = (event.mouse_region_x, event.mouse_region_y)

        if event.type == 'RIGHTMOUSE':
            if self.LmousePressed:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'CANCELLED'}
            else:
                return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE':
            self.LmousePressed = event.value == 'PRESS'

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.LmouseClick = True
            self.LmouseLoc = (event.mouse_region_x, event.mouse_region_y)

        if event.type == 'C' and event.value == 'PRESS':
            #print("Pressed C!\n") # debug
            self.keyC = True

        if event.type == 'X' and event.value == 'PRESS':
            #print("Pressed X!\n") # debug
            self.keyX = True

        if event.type == 'Y' and event.value == 'PRESS':
            #print("Pressed Y!\n") # debug
            self.keyY = True

        if event.type == 'Z' and event.value == 'PRESS':
            #print("Pressed Z!\n") # debug
            self.keyZ = True

        if event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            #print("\n\n\n  Game Over!\n") # debug
            return {'CANCELLED'}

        if self.exitCheck:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.currEdType = ""  # current Blender Editor Type
            self.transfMode = ""  # transform mode
            self.AddOnMode = SET_REF_PTS  # transform mode
            self.rDat = rotationData()
            self.newFreeCoor = ()
            self.refPts = referencePoints()
            self.sel_Stor = []
            self.boxCo = []
            self.btnDrawn = False
            self.modal_buff = []
            self.mouseLoc = (-5000,-5000)
            self.LmouseClick = False
            self.LmouseLoc = []
            self.keyC = False
            self.keyX = False
            self.keyY = False
            self.keyZ = False
            self.exitCheck = False

            #print("Exact Offsets started!") # debug
            # refresh the viewport
            sceneRefresh(context.mode)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(xOffsets)
    bpy.utils.register_class(changeInputPanel)

def unregister():
    bpy.utils.unregister_class(xOffsets)
    bpy.utils.unregister_class(changeInputPanel)

if __name__ == "__main__":
    register()
