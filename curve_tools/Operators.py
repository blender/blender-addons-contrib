import time
import threading

import bpy
from bpy.props import *
from bpy_extras import object_utils

from . import Properties
from . import Curves
from . import CurveIntersections
from . import Util
from . import Surfaces



class OperatorSelectionInfo(bpy.types.Operator):
    bl_idname = "curvetools2.operatorselectioninfo"
    bl_label = "Selection Info"
    bl_description = "Maintains a list of selected objects in the order they were selected"


    @classmethod
    def poll(cls, context):
        selectedObjectNames = Properties.CurveTools2SelectedObject.GetSelectedObjectNames()
        selectedBlenderObjectNames = Properties.CurveTools2SelectedObject.GetSelectedBlenderObjectNames()

        sleepTime = 0.02

        lock = threading.Lock()
        lock_holder = threading.Thread(target = Properties.CurveTools2SelectedObject.UpdateThreadTarget, args=(lock, sleepTime, selectedObjectNames, selectedBlenderObjectNames), name='OperatorSelectionInfoThread')
        # lock_holder = threading.Thread(target = Properties.CurveTools2SelectedObject.UpdateThreadTarget2, args=(lock, sleepTime, selectedObjectNames, selectedBlenderObjectNames, context), name='OperatorSelectionInfoThread')
        lock_holder.setDaemon(True)
        lock_holder.start()

        return True


    def execute(self, context):
        nrSelectedObjects = bpy.context.scene.curvetools.NrSelectedObjects

        self.report({'INFO'}, "Selection Info: nrSelectedObjects: %d" % nrSelectedObjects)

        selectedObjects = bpy.context.scene.curvetools.SelectedObjects
        selectedObjectValues = selectedObjects.values()
        for i, selectedObject in enumerate(selectedObjectValues):
            print("--", "selected object %d of %d: %s" % (i + 1, nrSelectedObjects, selectedObject.name))

        return {'FINISHED'}



# 1 CURVE SELECTED
# ################
class OperatorCurveInfo(bpy.types.Operator):
    bl_idname = "curvetools2.operatorcurveinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)

        nrSplines = len(curve.splines)
        nrSegments = 0
        nrEmptySplines = 0
        for spline in curve.splines:
            nrSegments += spline.nrSegments
            if spline.nrSegments < 1: nrEmptySplines += 1


        self.report({'INFO'}, "nrSplines: %d; nrSegments: %d; nrEmptySplines: %d" % (nrSplines, nrSegments, nrEmptySplines))

        return {'FINISHED'}



class OperatorCurveLength(bpy.types.Operator):
    bl_idname = "curvetools2.operatorcurvelength"
    bl_label = "Length"
    bl_description = "Calculates the length of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)

        context.scene.curvetools.CurveLength = curve.length

        return {'FINISHED'}



class OperatorSplinesInfo(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the splines of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)
        nrSplines = len(curve.splines)

        print("")
        print("OperatorSplinesInfo:", "nrSplines:", nrSplines)

        nrEmptySplines = 0
        for iSpline, spline in enumerate(curve.splines):
            print("--", "spline %d of %d: nrSegments: %d" % (iSpline + 1, nrSplines, spline.nrSegments))

            if spline.nrSegments < 1:
                nrEmptySplines += 1
                print("--", "--", "## WARNING: spline has no segments and will therefor be ignored in any further calculations")


        self.report({'INFO'}, "nrSplines: %d; nrEmptySplines: %d" % (nrSplines, nrEmptySplines) + " -- more info: see console")

        return {'FINISHED'}



class OperatorSegmentsInfo(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsegmentsinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the segments of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)
        nrSplines = len(curve.splines)
        nrSegments = 0

        print("")
        print("OperatorSegmentsInfo:", "nrSplines:", nrSplines)

        nrEmptySplines = 0
        for iSpline, spline in enumerate(curve.splines):
            nrSegmentsSpline = spline.nrSegments
            print("--", "spline %d of %d: nrSegments: %d" % (iSpline + 1, nrSplines, nrSegmentsSpline))

            if nrSegmentsSpline < 1:
                nrEmptySplines += 1
                print("--", "--", "## WARNING: spline has no segments and will therefor be ignored in any further calculations")
                continue

            for iSegment, segment in enumerate(spline.segments):
                print("--", "--", "segment %d of %d coefficients:" % (iSegment + 1, nrSegmentsSpline))
                print("--", "--", "--", "C0: %.6f, %.6f, %.6f" % (segment.coeff0.x, segment.coeff0.y, segment.coeff0.z))

            nrSegments += nrSegmentsSpline

        self.report({'INFO'}, "nrSplines: %d; nrSegments: %d; nrEmptySplines: %d" % (nrSplines, nrSegments, nrEmptySplines))

        return {'FINISHED'}



class OperatorOriginToSpline0Start(bpy.types.Operator):
    bl_idname = "curvetools2.operatororigintospline0start"
    bl_label = "OriginToSpline0Start"
    bl_description = "Sets the origin of the active/selected curve to the starting point of the (first) spline. Nice for curve modifiers."


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        blCurve = context.active_object
        blSpline = blCurve.data.splines[0]
        newOrigin = blCurve.matrix_world @ blSpline.bezier_points[0].co

        origOrigin = bpy.context.scene.cursor.location.copy()
        print("--", "origOrigin: %.6f, %.6f, %.6f" % (origOrigin.x, origOrigin.y, origOrigin.z))
        print("--", "newOrigin: %.6f, %.6f, %.6f" % (newOrigin.x, newOrigin.y, newOrigin.z))

        bpy.context.scene.cursor.location = newOrigin
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.cursor.location = origOrigin

        self.report({'INFO'}, "TODO: OperatorOriginToSpline0Start")

        return {'FINISHED'}



# 2 CURVES SELECTED
# #################
class OperatorIntersectCurves(bpy.types.Operator):
    bl_idname = "curvetools2.operatorintersectcurves"
    bl_label = "Intersect"
    bl_description = "Intersects selected curves"


    @classmethod
    def poll(cls, context):
        return Util.Selected2Curves()


    def execute(self, context):
        print("### TODO: OperatorIntersectCurves.execute()")

        algo = context.scene.curvetools.IntersectCurvesAlgorithm
        print("-- algo:", algo)


        mode = context.scene.curvetools.IntersectCurvesMode
        print("-- mode:", mode)
        # if mode == 'Split':
            # self.report({'WARNING'}, "'Split' mode is not implemented yet -- <<STOPPING>>")
            # return {'CANCELLED'}

        affect = context.scene.curvetools.IntersectCurvesAffect
        print("-- affect:", affect)


        curveIntersector = CurveIntersections.CurvesIntersector.FromSelection()
        rvIntersectionNrs = curveIntersector.CalcAndApplyIntersections()

        self.report({'INFO'}, "Active curve points: %d; other curve points: %d" % (rvIntersectionNrs[0], rvIntersectionNrs[1]))

        return {'FINISHED'}



class OperatorLoftCurves(bpy.types.Operator):
    bl_idname = "curvetools2.operatorloftcurves"
    bl_label = "Loft"
    bl_description = "Lofts selected curves"


    @classmethod
    def poll(cls, context):
        return Util.Selected2Curves()


    def execute(self, context):
        #print("### TODO: OperatorLoftCurves.execute()")

        loftedSurface = Surfaces.LoftedSurface.FromSelection()
        loftedSurface.AddToScene()

        self.report({'INFO'}, "OperatorLoftCurves.execute()")

        return {'FINISHED'}



class OperatorSweepCurves(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsweepcurves"
    bl_label = "Sweep"
    bl_description = "Sweeps the active curve along to other curve (rail)"


    @classmethod
    def poll(cls, context):
        return Util.Selected2Curves()


    def execute(self, context):
        #print("### TODO: OperatorSweepCurves.execute()")

        sweptSurface = Surfaces.SweptSurface.FromSelection()
        sweptSurface.AddToScene()

        self.report({'INFO'}, "OperatorSweepCurves.execute()")

        return {'FINISHED'}



# 3 CURVES SELECTED
# #################
class OperatorBirail(bpy.types.Operator):
    bl_idname = "curvetools2.operatorbirail"
    bl_label = "Birail"
    bl_description = "Generates a birailed surface from 3 selected curves -- in order: rail1, rail2 and profile"


    @classmethod
    def poll(cls, context):
        return Util.Selected3Curves()


    def execute(self, context):
        birailedSurface = Surfaces.BirailedSurface.FromSelection()
        birailedSurface.AddToScene()

        self.report({'INFO'}, "OperatorBirail.execute()")

        return {'FINISHED'}



# 1 OR MORE CURVES SELECTED
# #########################
class OperatorSplinesSetResolution(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinessetresolution"
    bl_label = "SplinesSetResolution"
    bl_description = "Sets the resolution of all splines"


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        splRes = context.scene.curvetools.SplineResolution
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            for spline in blCurve.data.splines:
                spline.resolution_u = splRes

        return {'FINISHED'}



class OperatorSplinesRemoveZeroSegment(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesremovezerosegment"
    bl_label = "SplinesRemoveZeroSegment"
    bl_description = "Removes splines with no segments -- they seem to creep up, sometimes.."


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = Curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            splinesToRemove = []
            for spline in curve.splines:
                if len(spline.segments) < 1: splinesToRemove.append(spline)
            nrRemovedSplines = len(splinesToRemove)

            for spline in splinesToRemove: curve.splines.remove(spline)

            if nrRemovedSplines > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Removed %d of %d splines" % (nrRemovedSplines, nrSplines))

        return {'FINISHED'}



class OperatorSplinesRemoveShort(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesremoveshort"
    bl_label = "SplinesRemoveShort"
    bl_description = "Removes splines with a length smaller than the threshold"


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        threshold = context.scene.curvetools.SplineRemoveLength
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = Curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            nrRemovedSplines = curve.RemoveShortSplines(threshold)
            if nrRemovedSplines > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Removed %d of %d splines" % (nrRemovedSplines, nrSplines))

        return {'FINISHED'}



class OperatorSplinesJoinNeighbouring(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesjoinneighbouring"
    bl_label = "SplinesJoinNeighbouring"
    bl_description = "Joins neighbouring splines within a distance smaller than the threshold"


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = Curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            threshold = context.scene.curvetools.SplineJoinDistance
            startEnd = context.scene.curvetools.SplineJoinStartEnd
            mode = context.scene.curvetools.SplineJoinMode

            nrJoins = curve.JoinNeighbouringSplines(startEnd, threshold, mode)
            if nrJoins > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Applied %d joins on %d splines; resulting nrSplines: %d" % (nrJoins, nrSplines, curve.nrSplines))

        return {'FINISHED'}


class ConvertBezierRectangleToSurface(bpy.types.Operator):
    bl_idname = "curvetools2.convert_bezier_rectangle_to_surface"
    bl_label = "Convert Bezier Rectangle To Surface"
    bl_description = "Convert Bezier Rectangle To Surface"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()

    def execute(self, context):
        # main function
        active_object = context.active_object
        splines = active_object.data.splines
        surfacedata = bpy.data.curves.new('Surface', type='SURFACE')
        surfaceobject = object_utils.object_data_add(context, surfacedata)
        surfaceobject.matrix_world = active_object.matrix_world
        surfaceobject.rotation_euler = active_object.rotation_euler
        surfacedata.dimensions = '3D'
        
        n = 0
        pp = []
        for s in splines:
            for p in s.bezier_points:
                pp.append(p)
                n += 1
        
        # 1
        surfacespline1 = surfacedata.splines.new(type='NURBS')
        surfacespline1.use_endpoint_u = True
        surfacespline1.use_endpoint_v = True
        surfacespline1.points.add(3)
        surfacespline1.points[0].co = [pp[0].co.x, pp[0].co.y, pp[0].co.z, 1]
        surfacespline1.points[1].co = [pp[0].handle_left.x, pp[0].handle_left.y, pp[0].handle_left.z, 1]
        surfacespline1.points[2].co = [pp[3].handle_right.x, pp[3].handle_right.y, pp[3].handle_right.z, 1]
        surfacespline1.points[3].co = [pp[3].co.x, pp[3].co.y, pp[3].co.z, 1]
        
        # 2
        surfacespline2 = surfacedata.splines.new(type='NURBS')
        surfacespline2.use_endpoint_u = True
        surfacespline2.use_endpoint_v = True
        surfacespline2.points.add(3)
        surfacespline2.points[0].co = [pp[0].handle_right.x, pp[0].handle_right.y, pp[0].handle_right.z, 1]
        surfacespline2.points[1].co = [(pp[0].handle_right.x + pp[3].handle_left.x)/2,
                                       (pp[0].handle_right.y + pp[3].handle_left.y)/2,
                                       (pp[0].handle_right.z + pp[3].handle_left.z)/2, 1]
        surfacespline2.points[2].co = [(pp[3].handle_left.x + pp[0].handle_right.x)/2,
                                       (pp[3].handle_left.y + pp[0].handle_right.y)/2,
                                       (pp[3].handle_left.z + pp[0].handle_right.z)/2, 1]
        surfacespline2.points[3].co = [pp[3].handle_left.x, pp[3].handle_left.y, pp[3].handle_left.z, 1]

        # 3
        surfacespline3 = surfacedata.splines.new(type='NURBS')
        surfacespline3.use_endpoint_u = True
        surfacespline3.use_endpoint_v = True
        surfacespline3.points.add(3)
        surfacespline3.points[0].co = [pp[1].handle_left.x, pp[1].handle_left.y, pp[1].handle_left.z, 1]
        surfacespline3.points[1].co = [(pp[1].handle_left.x + pp[2].handle_right.x)/2,
                                       (pp[1].handle_left.y + pp[2].handle_right.y)/2,
                                       (pp[1].handle_left.z + pp[2].handle_right.z)/2, 1]
        surfacespline3.points[2].co = [(pp[2].handle_right.x + pp[1].handle_left.x)/2,
                                       (pp[2].handle_right.y + pp[1].handle_left.y)/2,
                                       (pp[2].handle_right.z + pp[1].handle_left.z)/2, 1]
        surfacespline3.points[3].co = [pp[2].handle_right.x, pp[2].handle_right.y, pp[2].handle_right.z, 1]

        # 4
        surfacespline4 = surfacedata.splines.new(type='NURBS')
        surfacespline4.use_endpoint_u = True
        surfacespline4.use_endpoint_v = True
        surfacespline4.points.add(3)
        surfacespline4.points[0].co = [pp[1].co.x, pp[1].co.y, pp[1].co.z, 1]
        surfacespline4.points[1].co = [pp[1].handle_right.x, pp[1].handle_right.y, pp[1].handle_right.z, 1]
        surfacespline4.points[2].co = [pp[2].handle_left.x, pp[2].handle_left.y, pp[2].handle_left.z, 1]
        surfacespline4.points[3].co = [pp[2].co.x, pp[2].co.y, pp[2].co.z, 1]
        
        splines = surfaceobject.data.splines
        for s in splines:
            for p in s.points:
                p.select = True

        bpy.context.view_layer.objects.active = surfaceobject
        bpy.ops.object.mode_set(mode = 'EDIT') 
        bpy.ops.curve.make_segment()
        splines = surfaceobject.data.splines
        for s in splines:
            s.order_u = 4
            s.order_v = 4
            s.resolution_u = 4
            s.resolution_v = 4

        return {'FINISHED'}

