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

__bpydoc__ = """\
This addon enables you to snakelike "grow" an edgeloop selection with arrow keys.


Documentation

First go to User Preferences->Addons and enable the EdgeGrow addon in the Mesh category.
Invoke it (button in the Mesh Tools panel).
Go to EditMode, select one or more edges or connected edge-snakes (you can grow several at the same time, a bmesh mesh has a certain
spin direction to it, so in most general non-complex situations multiple edges will grow together
in the desired direction).  Use the left and right arrow keys to grow / ungrow the edgeloop in any direction.
The addon will show the edges you can grow next in light blue, with the active edge(will be selected 
when using arrow keys) highlighted in red.  Use up and down arrow keys to activate the other light blue
edges, this way you can route your edge-snake in every possible direction; defsult is the middle one.
You can grow multiple slices at the same time.

If you wish to hotkey EdgeGrow:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.edgetune'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "EdgeGrow",
	"author": "Gert De Roost",
	"version": (0, 3, 2),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Growing edgeloops with arrowkeys",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}

if "bpy" in locals():
    import imp


import bpy
from bpy_extras import *
import bmesh
from bgl import *
from mathutils import *
import time




class EdgeGrow(bpy.types.Operator):
	bl_idname = "mesh.edgegrow"
	bl_label = "EdgeGrow"
	bl_description = "Growing edgeloops with arrowkeys"
	bl_options = {"REGISTER", "UNDO"}
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		do_edgegrow(self)
		
		context.window_manager.modal_handler_add(self)
		if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
			self._handle = bpy.types.SpaceView3D.draw_handler_add(redraw, (), 'WINDOW', 'POST_PIXEL')
		else:
			self._handle = context.region.callback_add(redraw, (), 'POST_PIXEL')
		
		return {'RUNNING_MODAL'}

	def modal(self, context, event):
		
		global bm, mesh
		global viewchange, state, activedir, check
		global edgelist, cursor, counter, posn

		scn = bpy.context.scene
		
		if event.type in ["MIDDLEMOUSE"]:
			# recalculate transformation matrix
			viewchange = 1
			return {"PASS_THROUGH"}
		elif event.type in ["WHEELDOWNMOUSE", "WHEELUPMOUSE"]:
			# recalculate transformation matrix
			viewchange = 1
			return {"PASS_THROUGH"}
		elif event.type == "RET" or stop:
			# Consolidate changes if ENTER pressed.
			# Free the bmesh.
			bm.free()
			if eval(str(bpy.app.build_revision)[2:7]) >= 53207:
				bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
			else:
				context.region.callback_remove(self._handle)
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			return {'FINISHED'}
		elif event.type == "LEFT_ARROW":
			# reinit: when user returns to begin position: display cursor edges on both sides
			# start: add to beginning of lists
			# end: add to end of lists
			# init: first initialization state: cursor on both sides
			# set cursor to correct edge
			for posn in range(len(edgelist)):
				if event.value == "PRESS":
					if state[posn] == "reinit":
						check[posn] = 0
						if oldstate[posn] == "start":
							if activedir[posn] == "left":
								state[posn] = "start"
							else:
								state[posn] = "end"
								if cursor[posn] == startcur[posn]:
									cursor[posn] = endcur[posn]
								else:
									cursor[posn] = startcur[posn]
						else:
							if activedir[posn] == "left":
								state[posn] = "end"
							else:
								state[posn] = "start"
								if cursor[posn] == startcur[posn]:
									cursor[posn] = endcur[posn]
								else:
									cursor[posn] = startcur[posn]
						activedir[posn] = "left"						
					if state[posn] == "init":			
						activedir[posn] = "left"
						check[posn] = 1
						state[posn] = "start"
						cursor[posn] = startcur[posn]
							
					# activedir: left or right absolute -> movement in x direction (when in init state)
					if activedir[posn] == "left":
						addedge()
					else:
						removeedge()
			return {'RUNNING_MODAL'}
		elif event.type == "RIGHT_ARROW":
			# check LEFT_ARROW
			if event.value == "PRESS":
				for posn in range(len(edgelist)):
					if state[posn] == "reinit":
						check[posn] = 0
						if oldstate[posn] == "start":
							if activedir[posn] == "right":
								state[posn] = "start"
								if cursor[posn] == startcur[posn]:
									cursor[posn] = startcur[posn]
								else:
									cursor[posn] = endcur[posn]
							else:
								state[posn] = "end"
								if cursor[posn] == startcur[posn]:
									cursor[posn] = endcur[posn]
								else:
									cursor[posn] = startcur[posn]
						else:
							if activedir[posn] == "right":
								state[posn] = "end"
								if cursor[posn] == startcur[posn]:
									cursor[posn] = startcur[posn]
								else:
									cursor[posn] = endcur[posn]
							else:
								state[posn] = "start"
								if cursor[posn] == startcur[posn]:
									cursor[posn] = endcur[posn]
								else:
									cursor[posn] = startcur[posn]
						activedir[posn] = "right"
					if state[posn] == "init":
						activedir[posn] = "right"
						check[posn] = 1
						state[posn] = "end"
						cursor[posn] = endcur[posn]
					if activedir[posn] == "right":
						addedge()
					else:
						removeedge()
			return {'RUNNING_MODAL'}
		elif event.type == "UP_ARROW":
			# next cursor possibility
			if event.value == "PRESS":
				counter += 1
				mesh.update()
			return {'RUNNING_MODAL'}
		elif event.type == "DOWN_ARROW":
			# previous cursor possibility
			if event.value == "PRESS":
				counter -= 1
				mesh.update()
			return {'RUNNING_MODAL'}
		
		return {'RUNNING_MODAL'}

def addedge():
	
	global edgelist, mesh, change
	
	# add edge to edgelist
	change = 1
	if state[posn] == "start":
		edgelist[posn].insert(0, cursor[posn])
	if state[posn] == "end":
		edgelist[posn].append(cursor[posn])
	cursor[posn].verts[0].select = 1
	cursor[posn].verts[1].select = 1
	cursor[posn].select = 1 
	mesh.update()

def removeedge():
	
	global edgelist, mesh, cursor, change
	
	# removve edge from edgelist
	change = 1
	if state[posn] == "start":
		for vert in edgelist[posn][0].verts:
			if vert in cursor[posn].verts:
				vert.select = 0
		cursor[posn] = edgelist[posn][0]
		edgelist[posn].pop(0)
	if state[posn] == "end":
		for vert in edgelist[posn][len(edgelist[posn]) - 1].verts:
			if vert in cursor[posn].verts:
				vert.select = 0
		cursor[posn] = edgelist[posn][len(edgelist[posn]) - 1]
		edgelist[posn].pop(len(edgelist[posn]) - 1)
	cursor[posn].select = 0
	mesh.update()




def panel_func(self, context):
	scn = bpy.context.scene
	self.layout.label(text="EdgeGrow:")
	self.layout.operator("mesh.edgegrow", text="Grow Edges")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_class(EdgeGrow)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()






def getscreencoords(vector):
	
	# calculate screen coords for given Vector
	
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d	
	pvector = vector * matrix
	pvector = pvector + selobj.location
	svector = view3d_utils.location_3d_to_region_2d(region, rv3d, pvector)
	if svector == None:
		return [0, 0 ,0]
	else:
		return [svector[0], svector[1], pvector[2]]



def addstart(vert):
	
	global selset, edgelist

	# recursive: adds to initial edgelist at start
	for e in vert.link_edges:
		if e in selset:
			selset.discard(e)
			v = e.other_vert(vert)
			edgelist[posn].insert(0, e)
			addstart(v)
			break

def addend(vert):
	
	global selset, edgelist

	# recursive: adds to initial edgelist at end
	for e in vert.link_edges:
		if e in selset:
			selset.discard(e)
			v = e.other_vert(vert)
			edgelist[posn].append(e)
			addend(v)
			break


def do_edgegrow(self):

	global bm, mesh, selobj, actedge
	global selset, edgelist, posn, startlen
	global viewchange, check, change, stop
	global state, oldstate, cursor, startcur, endcur, activedir, singledir
	
	viewchange = 0
	change = 1
	stop = 0

	context = bpy.context
	region = context.region  
	area = context.area
	selobj = bpy.context.active_object
	mesh = selobj.data
	bm = bmesh.from_edit_mesh(mesh)
	actedge = bm.select_history.active
	# get transf matrix
	adapt()

	# vsellist, essellist: remember selection for reselecting later
	selset = set([])
	vsellist = []
	esellist = []
	for edge in bm.edges:
		if edge.select:
			selset.add(edge)
			esellist.append(edge)		
	for vert in bm.verts:
		if vert.select:
			vsellist.append(vert)		

	state = []
	oldstate = []
	cursor = []
	startcur = []
	endcur = []
	check = []
	activedir = []
	posn = 0
	singledir = {}
	singledir[0] = None
	startlen = []
	edgelist = []
	while len(selset) > 0:
		# initialize next edgesnake
		state.append("init")
		oldstate.append("init")
		cursor.append(None)
		startcur.append(None)
		endcur.append(None)
		check.append(0)
		activedir.append("")
		
		edgelist.append([])
		elem = selset.pop()
		vert = elem.verts[0]
		selset.add(elem)
		# add to start and end of arbitrary start vert
		addstart(vert)
		addend(vert)
		startlen.append(len(edgelist[posn]))
		posn += 1
	if len(edgelist) == 1:
		if len(edgelist[0]) == 1:
			# must store leftmost vert as startingvert when only one edge selected
			x1, y, z = getscreencoords(edgelist[0][0].verts[0].co)
			x2, y, z = getscreencoords(edgelist[0][0].verts[1].co)
			if x1 < x2:
				singledir[0] = edgelist[0][0].verts[0]
			else:
				singledir[0] = edgelist[0][0].verts[1]
	
	# orient first edgesnake from left(start) to right(end)
	x1, y, z = getscreencoords(edgelist[0][0].verts[0].co)
	x2, y, z = getscreencoords(edgelist[0][len(edgelist[0]) - 1].verts[0].co)
	if x1 > x2:
		edgelist[0].reverse()				
		
	
	# 
	# orient edge and vertlists parallel - reverse if necessary
	for i in range(len(edgelist) - 1):
		bpy.ops.mesh.select_all(action="DESELECT")
		# get first vert and edge for two adjacent snakes
		for v in edgelist[i][0].verts:
			if len(edgelist[i]) == 1:
				if i == 0:
					x1, y, z = getscreencoords(v.co)
					x2, y, z = getscreencoords(edgelist[i][0].other_vert(v).co)
					if x1 < x2:
						singledir[0] = v
					else:
						singledir[0] = edgelist[i][0].other_vert(v)
				vt = singledir[i]	
				vt.select = 1
				bm.select_history.add(vt)
				v1 = vt
				e1 = edgelist[i][0]
				break
			elif not(v in edgelist[i][1].verts):
				v.select = 1
				bm.select_history.add(v)
				v1 = v
				e1 = edgelist[i][0]
		for v in edgelist[i+1][0].verts:
			if len(edgelist[i+1]) == 1:
				v.select = 1
				bm.select_history.add(v)
				v2 = v
				e2 = edgelist[i+1][0]
				break
			elif not(v in edgelist[i+1][1].verts):
				v.select = 1
				bm.select_history.add(v)
				v2 = v
				e2 = edgelist[i+1][0]
		singledir[i+1] = v2
		bm.select_history.validate()
		# get path between startverts for checking orientation
		bpy.ops.mesh.shortest_path_select()
		
		for e in bm.edges:
			if e.verts[0].select and e.verts[1].select:
				e.select = 1
		
		# correct selected path when not connected neatly to vert from left or right(cant know direction)
		def correctsel(e1, v1, lst):
			found = 0
			while not(found):
				found = 1
				for edge in e1.other_vert(v1).link_edges:
					if edge.select and edge != e1:
						if lst.index(e1) < len(lst) - 1:
							v1.select = 0
							e1.select = 0
							v1 = e1.other_vert(v1)
							e1 = lst[lst.index(e1) + 1]
						else:
							templ = list(e1.other_vert(v1).link_faces)
							for f in e1.link_faces:
								templ.pop(templ.index(f))
							for edge in e1.other_vert(v1).link_edges:
								if edge in templ[0].edges and edge in templ[1].edges:
									v1.select = 0
									e1.select = 0
									v1 = e1.other_vert(v1)
									e1 = edge
						found = 0
									
			# check situation where left/right connection is on vert thats outside slice
			found = 0
			while not(found):
				templ = list(v1.link_faces)
				for f in e1.link_faces:
					templ.pop(templ.index(f))
				found = 1
				for edge in v1.link_edges:
					if edge in templ[0].edges and edge in templ[1].edges:
						if edge.other_vert(v1).select:
							v1.select = 0
							edge.select = 0
							v1 = edge.other_vert(v1)
							e1 = edge
							found = 0
			return e1, v1
							
		e1, v1 = correctsel(e1, v1, edgelist[i])
		e2, v2 = correctsel(e2, v2, edgelist[i+1])					
		
		# do all the checking to see if the checked lists must be reversed
		brk = 0
		for face1 in e1.link_faces:
			for edge1 in face1.edges:
				if edge1.select:
					for loop1 in face1.loops:
						if loop1.vert == v1:
							if loop1.edge == e1:
								turn = loop1
							elif loop1.link_loop_next.edge == e1:
								turn = loop1.link_loop_next
							else:
								turn = loop1.link_loop_prev
							# check if turning in one direction
							if turn.link_loop_next.edge.select:
								for face2 in e2.link_faces:
									for edge2 in face2.edges:
										if edge2.select:
											for loop2 in face2.loops:
												if loop2.vert == v2:
													if loop2.edge == e2:
														turn = loop2
													elif loop2.link_loop_next.edge == e2:
														turn = loop2.link_loop_next
													else:
														turn = loop2.link_loop_prev
													if turn.link_loop_next.edge.select:
														singledir[i+1] = e2.other_vert(v2)
														edgelist[i+1].reverse()
													break
											brk = 1
											break
									if brk == 1:
										break
							# and the other
							elif loop1.link_loop_prev.edge.select:
								for face2 in e2.link_faces:
									for edge2 in face2.edges:
										if edge2.select:
											for loop2 in face2.loops:
												if loop2.vert == v2:
													if loop2.edge == e2:
														turn = loop2
													elif loop2.link_loop_next.edge == e2:
														turn = loop2.link_loop_next
													else:
														turn = loop2.link_loop_prev
													if turn.link_loop_prev.edge.select:
														singledir[i+1] = e2.other_vert(v2)
														edgelist[i+1].reverse()
													break
											brk = 1
											break
									if brk == 1:
										break
							break
					break
					
	for posn in range(len(edgelist)):
		if edgelist[posn][0] == actedge:
			for posn in range(len(edgelist)):
				edgelist[posn].reverse()
					
	bpy.ops.mesh.select_all(action="DESELECT")
	for v in vsellist:
		v.select = 1
	for e in esellist:
		e.select = 1


	region.tag_redraw()



def adapt():
	
	global matrix
	global bm, mesh, selobj
	global mbns, viewchange
	global selobj
	
	# Rotating / panning / zooming 3D view is handled here.
	# Get matrix.
	if selobj.rotation_mode == "AXIS_ANGLE":
		# when roataion mode is axisangle
		angle, x, y, z =  selobj.rotation_axis_angle
		matrix = Matrix.Rotation(-angle, 4, Vector((x, y, z)))
	elif selobj.rotation_mode == "QUATERNION":
		# when rotation on object is quaternion
		w, x, y, z = selobj.rotation_quaternion
		x = -x
		y = -y
		z = -z
		quat = Quaternion([w, x, y, z])
		matrix = quat.to_matrix()
		matrix.resize_4x4()
	else:
		# when rotation of object is euler
		ax, ay, az = selobj.rotation_euler
		mat_rotX = Matrix.Rotation(-ax, 4, 'X')
		mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
		mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
	if selobj.rotation_mode == "XYZ":
		matrix = mat_rotX * mat_rotY * mat_rotZ
	elif selobj.rotation_mode == "XZY":
		matrix = mat_rotX * mat_rotZ * mat_rotY
	elif selobj.rotation_mode == "YXZ":
		matrix = mat_rotY * mat_rotX * mat_rotZ
	elif selobj.rotation_mode == "YZX":
		matrix = mat_rotY * mat_rotZ * mat_rotX
	elif selobj.rotation_mode == "ZXY":
		matrix = mat_rotZ * mat_rotX * mat_rotY
	elif selobj.rotation_mode == "ZYX":
		matrix = mat_rotZ * mat_rotY * mat_rotX

	# handle object scaling
	sx, sy, sz = selobj.scale
	mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
	mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
	mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
	matrix = mat_scX * mat_scY * mat_scZ * matrix


def getedge(vert, edge):
	
	global sortlist, startedge
	
	# get the next edge in list of edges rotating from/around vert at seelection end (for cursor choice)
	for loop in vert.link_loops:
		if loop.edge == edge:
			edge = loop.link_loop_prev.edge
			if edge == startedge:
				break
			sortlist.append(edge)
			getedge(vert, edge)
			break

def drawedges(vert, edge):
	
	global sortlist, startedge, tempcur, change, counter
	
	# get sorted list of possible cursor choices
	sortlist = []
	startedge = edge
	getedge(vert, edge)
	if len(vert.link_edges) - len(sortlist) > 1:
		for e in vert.link_edges:
			if e != startedge:
				if not(e in sortlist):
					sortlist.append(e)
	# calculate new cursor position in sortlist if changed			
	if change:
		if len(sortlist) == 2 and (len(sortlist[0].link_faces) == 1 or len(sortlist[1].link_faces) == 1):
			for f in startedge.link_faces:
				for e in sortlist:
					tel = 0
					if e.verts[0] in f.verts:
						tel += 1
						vfound = e.verts[1]
					if e.verts[1] in f.verts:
						tel += 1
						vfound = e.verts[0]
					if tel == 1:
						break
			for e in sortlist:
				if vfound in e.verts:
					cnt = sortlist.index(e)
		else:
			# standard middle edge is cursor
			cnt = int((len(sortlist) - 1) / 2)
		counter = cnt
	else:
		# do revert to start when past end and other way around
		if counter >= len(sortlist):
			cnt = counter - (int(counter / len(sortlist)) * len(sortlist))
		elif counter < 0:
			cnt = counter
			while cnt < 0:
				cnt += len(sortlist)
		else:
			cnt = counter
	# draw cursor possibilities in blue, current in red
	for edge in sortlist:
		if sortlist.index(edge) == cnt:
			tempcur = edge
			glColor3f(1.0, 0, 0)
		else:
			glColor3f(0.2, 0.2, 1.0)
		glBegin(GL_LINES)
		x, y, dummy = getscreencoords(edge.verts[0].co)
		glVertex2f(x, y)
		x, y, dummy = getscreencoords(edge.verts[1].co)
		glVertex2f(x, y)
		glEnd()
			
def setcursors(v):
	
	global startcur, endcur, posn
	
	# what it says
	if oldstate[posn] == "start":
		if v in cursor[posn].verts:
			startcur[posn] = tempcur
		else:
			endcur[posn] = tempcur
	elif oldstate[posn] == "end":
		if v in cursor[posn].verts:
			endcur[posn] = tempcur
		else:
			startcur[posn] = tempcur


def redraw():
	
	global viewchange, edgelist, state, oldstate, check
	global cursor, startcur, endcur, tempcur, change, posn
	
	# user changes view
	if viewchange:
		viewchange = 0
		adapt()
	
	# reinit if returning to initial state
	for lst in edgelist:
		posn = edgelist.index(lst)
		oldstate[posn] = state[posn]
		if len(lst) == startlen[posn]:
			if check[posn]:
				state[posn] = "reinit"
		else:
			check[posn] = 1
	
	for lst in edgelist:
		posn = edgelist.index(lst)
		
		if state[posn] == "init" or state[posn] == "reinit":
			if len(lst) == 1:
				# if snake is one edge, use singledir vert for orientation
				v = lst[0].verts[0]
				drawedges(v, lst[0])
				setcursors(v)
				if oldstate[posn] == "init":
					if singledir[posn] == v:
						startcur[posn] = tempcur
					else:
						endcur[posn] = tempcur
				v = lst[0].verts[1]
				drawedges(v, lst[0])
				setcursors(v)
				if oldstate[posn] == "init":
					if singledir[posn] == v:
						startcur[posn] = tempcur
					else:
						endcur[posn] = tempcur
			else:
				# draw and set start and end cursors
				edge = lst[0]
				edge.select = 0
				for vert in edge.verts:
					if not(vert in lst[1].verts):
						drawedges(vert, edge)
						startcur[posn] = tempcur
				edge = lst[len(lst) - 1]
				edge.select = 0
				for vert in edge.verts:
					if not(vert in lst[len(lst) - 2].verts):
						drawedges(vert, edge)
						endcur[posn] = tempcur
		elif state[posn] == "start":
			# draw and set cursor at start
			edge = lst[0]
			for vert in edge.verts:
				if not(vert in lst[1].verts):
					drawedges(vert, edge)
					cursor[posn] = tempcur
		elif state[posn] == "end":
			# draw and set cursor at end
			edge = lst[len(lst) - 1]
			for vert in edge.verts:
				if not(vert in lst[len(lst) - 2].verts):
					drawedges(vert, edge)
					cursor[posn] = tempcur
		for e in edgelist[posn]:
			e.verts[0].select = 1
			e.verts[1].select = 1
			e.select = 1
			
	change = 0
	


