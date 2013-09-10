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
This script uses the concept of support edges, or the inserting of new edges parallel to the selected edges.


Documentation

First go to User Preferences->Addons and enable the ParEdge addon in the Mesh category.
Go to EditMode, select a closed edge path without corners (an edgeloop or part of an edgeloop)and invoke 
the addon (button in the Mesh Tool panel).  Enter a distance (positive or negative) with the slider in 
the Mesh Tools panel or leftclick-drag from left to right to
interactively choose the parallel distance.  Select "Both Sides" on the panel to insert edges on both sides.
Select "Endpoint quads" if you want to have edgepath endpoints "capped".
Press the right mouse button to cancel operation or ENTER to accept changes.  
The tool will remember the last set distance and the "Both Sides" setting for the next ParEdge operation.

If you wish to hotkey ParEdge:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.paredge'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "ParEdge",
	"author": "Gert De Roost",
	"version": (0, 4, 5),
	"blender": (2, 6, 3),
	"location": "View3D > Tools",
	"description": "Inserting of parallel edges",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}

if "bpy" in locals():
    import imp


import bpy
import bmesh
import math



parchange = 0
started = 0


bpy.types.Scene.Distance = bpy.props.FloatProperty(
		name = "Distance", 
		description = "Enter distance",
		default = 0,
		min = -1,
		max = 1)

bpy.types.Scene.Both = bpy.props.BoolProperty(
		name = "Both sides", 
		description = "Insert on both sides",
		default = False)

bpy.types.Scene.Cap = bpy.props.BoolProperty(
		name = "Endpoint quads", 
		description = "Create endpoint quads",
		default = False)




class ParEdge(bpy.types.Operator):
	bl_idname = "mesh.paredge"
	bl_label = "ParEdge"
	bl_description = "Inserting of parallel edges"
	bl_options = {"REGISTER", "UNDO"}
	
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):
		
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False

		do_paredge(self)
		
		context.window_manager.modal_handler_add(self)
		self._handle = bpy.types.SpaceView3D.draw_handler_add(redraw,(), 'WINDOW', 'POST_PIXEL')
		
		return {'RUNNING_MODAL'}

	def modal(self, context, event):
		
		global bm, bmundo, mesh
		global started, mbns, basex, basev, dist
		global dist, olddist, distset, oldboth, negsubd, possubd
		global dissverts1, dissedges1, railverts1, railedges1
		global dissverts2, dissedges2, railverts2, railedges2

		scn = bpy.context.scene
		
		if event.type == "RIGHTMOUSE" or wrongsel or stop:
			# right mousebutton cancels
			started = 0
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			bm.free()
			bpy.ops.object.editmode_toggle()
			bmundo.to_mesh(mesh)
			bpy.ops.object.editmode_toggle()
			return {'CANCELLED'}
		elif event.type in ["LEFTMOUSE"]:
			if event.mouse_region_x < 0:
				# this for splitting up mouse func between panel and 3d view
				return {"PASS_THROUGH"}
			if event.value == "PRESS":
				basex = event.mouse_region_x
				basev = dist
				mbns = 1
			if event.value == "RELEASE":
				mbns = 0
			return {"RUNNING_MODAL"}
		elif event.type in ["MIDDLEMOUSE", "WHEELDOWNMOUSE", "WHEELUPMOUSE"]:
			return {"PASS_THROUGH"}
		elif event.type == "RET":
			# Consolidate changes if SPACEBAR pressed.
			# Free the bmesh.
			if event.mouse_region_x < 0:
				return {"PASS_THROUGH"}
			started = 0
			bpy.ops.mesh.select_all(action="DESELECT")
			for posn in range(len(vertlist)):
				if capped:
					for e in capsellist:
						if e == None:
							continue
						e.select = 1
						e.verts[0].select = 1
						e.verts[1].select = 1
				# select only the inserted verts/edges
				if negsubd[posn]:
					for vert in dissverts1[posn]:
						vert.select = 1
					for edge in dissedges1[posn]:
						edge.select = 1
				if possubd[posn]:
					for vert in dissverts2[posn]:
						vert.select = 1
					for edge in dissedges2[posn]:
						edge.select = 1
				# if user resetted to zero: remove inserted edges
				if dist == 0:
					if negsubd[posn]:
						bpy.ops.mesh.select_all(action="DESELECT")
						for vert in dissverts1[posn]:
							vert.select = 1
						for edge in dissedges1[posn]:
							edge.select = 1
						bpy.ops.mesh.dissolve_limited()
						mesh.calc_tessface()
						negsubd[posn] = 0
						possubd[posn] = 0
					if possubd[posn]:
						bpy.ops.mesh.select_all(action="DESELECT")
						for vert in dissverts2[posn]:
							vert.select = 1
						for edge in dissedges2[posn]:
							edge.select = 1
						bpy.ops.mesh.dissolve_limited()
						mesh.calc_tessface()
						negsubd[posn] = 0
						possubd[posn] = 0
					for vert in vertlist[posn]:
						vert.select = 1
					for edge in edgelist[posn]:
						edge.select = 1
					mesh.update()
			bm.free()
			bpy.ops.object.editmode_toggle()
			bmundo.free()
			bpy.ops.object.editmode_toggle()
			bpy.context.user_preferences.edit.use_global_undo = self.save_global_undo
			return {'FINISHED'}
		elif event.type == "MOUSEMOVE":
			# do some edgecreating
			adapt(self, event)
			return {'PASS_THROUGH'}
			
		return {'RUNNING_MODAL'}


def panel_func(self, context):
	
	global parchange
	
	scn = bpy.context.scene
	self.layout.label(text="ParEdge:")
	self.layout.operator("mesh.paredge", text="Insert Edges")
	if started:
		self.layout.prop(scn, 'Distance')
		self.layout.prop(scn, 'Both')
		if scn.Both:
			self.layout.prop(scn, 'Cap')
		parchange = 1
		region.tag_redraw()


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_class(ParEdge)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()


def adapt(self, event):
	
	global bm, bmundo, mesh
	global started, mbns, basex, basev, dist
	global dist, olddist, distset, oldboth, negsubd, possubd
	global dissverts1, dissedges1, railverts1, railedges1
	global dissverts2, dissedges2, railverts2, railedges2
	global caplist, oldcap, capped, capsellist
	
	def removecaps():
		capped = 0
		for posn in range(len(vertlist)):
			for [e1, e2, v1, v2, fj, fo1, fo2] in caplist[posn]:
				if e1 == None:
					continue
				print (posn, caplist[posn])
				bmesh.utils.face_split(fj, v1, v2)
				templ = []
				for f in e1.link_faces:
					templ.append(f)
				bmesh.utils.face_join(templ)
				templ = []
				for f in e2.link_faces:
					templ.append(f)
				bmesh.utils.face_join(templ)
		mesh.calc_tessface()


	scn = bpy.context.scene
	
	if mbns == 0 and parchange == 0:
		if scn.Cap != oldcap:
			if dist != 0:
				mbns = 2
			if scn.Cap == True:
				capped = 0
			else:
				removecaps()
			oldcap = scn.Cap
		if scn.Both != oldboth:
			if dist != 0:
				# enter edge-building through the backdoor to instantaneously show both inserts 
				mbns = 2
			if scn.Both == True:
				# if just set
				for posn in range(len(vertlist)):
					if negsubd[posn]:
						possubd[posn] = 0
					if possubd[posn]:
						negsubd[posn] = 0
			else:
				if capped:
					capped = 0
					removecaps()
				# if just unset: remove one side of edges
				if dist < 0:
					for posn in range(len(vertlist)):
						bpy.ops.mesh.select_all(action="DESELECT")
						for vert in dissverts2[posn]:
							vert.select = 1
						for edge in dissedges2[posn]:
							edge.select = 1
						bpy.ops.mesh.dissolve_limited()
						mesh.calc_tessface()
						for vert in dissverts1[posn]:
							vert.select = 1
						for edge in dissedges1[posn]:
							edge.select = 1
						possubd[posn] = 0
						railedges2[posn] = []
						railverts2[posn] = []
						dissverts2[posn] = []
						dissedges2[posn] = []
				if dist >= 0:
					for posn in range(len(vertlist)):
						if railedges1[posn] != []:
							bpy.ops.mesh.select_all(action="DESELECT")
							for vert in dissverts1[posn]:
								vert.select = 1
							for edge in dissedges1[posn]:
								edge.select = 1
							bpy.ops.mesh.dissolve_limited()
							mesh.calc_tessface()													
							for vert in dissverts2[posn]:
								vert.select = 1
							for edge in dissedges2[posn]:
								edge.select = 1
							negsubd[posn] = 0
							railedges1[posn] = []
							railverts1[posn] = []
							dissverts1[posn] = []
							dissedges1[posn] = []
				for vert in vertlist[posn]:
					vert.select = 1
				for edge in edgelist[posn]:
					edge.select = 1
		oldboth = scn.Both
#		if distset:
#			if scn.Distance != dist:
#				scn.Distance = dist
#				return {'PASS_THROUGH'}
#			distset = 0
		dist = scn.Distance
		if dist != olddist:
			mbns = 2
		olddist = dist
	else:
		if mbns != 2:
			if event != None:
				# do mouse handling left-right
				mx = event.mouse_region_x
				mean = max(-1*meanmin, meanmax)
				dist = basev + ((mx - basex) / 200) * mean
				scn.Distance = dist
				distset = 1
		else:
			mbns = 0
#			return
		# dont do anything if zero - removing edges will be handled once exiting with ENTER
		if scn.Distance == 0:
			return
		
		#negative side handling
		if dist < 0 or scn.Both == True:
			for posn in range(len(vertlist)):
				if not(negsubd[posn]):
					if scn.Both == False:
						# if just switched sides: remove positive side
						if possubd[posn] == 1:
							bpy.ops.mesh.select_all(action="DESELECT")
							for vert in dissverts2[posn]:
								vert.select = 1
							for edge in dissedges2[posn]:
								edge.select = 1
							bpy.ops.mesh.dissolve_limited()
							railedges2[posn] = []
							railverts2[posn] = []
							dissverts2[posn] = []
							dissedges2[posn] = []
						possubd[posn] = 0
					railedges1[posn] = []
					railverts1[posn] = []
					dissverts1[posn] = []
					dissedges1[posn] = []
			
			for posn in range(len(vertlist)):
				if not(negsubd[posn]):
					negsubd[posn] = 1
					# if just switched sides: look for slide constellations
					for vert in vertlist[posn]:
						if vertlist[posn].index(vert) == len(vertlist[posn]) - 1:
							break
						for loop in vert.link_loops:
							if loop.link_loop_next.vert == vertlist[posn][vertlist[posn].index(vert) + 1]:
								railverts1[posn].append(loop.link_loop_prev.vert)
								e = loop.link_loop_prev.edge
								railedges1[posn].append(e)
								if vertlist[posn].index(vert) == len(vertlist[posn]) - 2:
									railverts1[posn].append(loop.link_loop_next.link_loop_next.vert)
									e = loop.link_loop_next.edge        
									railedges1[posn].append(e)							
					if railedges1[posn] != []:
						# insert parallel edges
						prev = None
						popout = 0
						for idx in range(len(railedges1[posn])):
							if popout:
								break
							edge = railedges1[posn][idx]
							if idx == len(railedges1[posn]) - 2 and railverts1[posn][0] == railverts1[posn][len(railverts1[posn]) - 1]:
								# this handles closed edgeloops
								vert = startvert
								railedges1[posn].pop(len(railedges1[posn]) - 1)
								railverts1[posn].pop(len(railverts1[posn]) - 1)
								popout = 1
							else:
								dummy, vert = bmesh.utils.edge_split(edge, vertlist[posn][railedges1[posn].index(edge)], 0.5)
							if idx == 0:
								startvert = vert 
							dissverts1[posn].append(vert)
							if not(prev == None):
								for f in edge.link_faces:
									if prevedge in f.edges:
										bmesh.utils.face_split(f, vert, prev)
										bmesh.utils.face_split(f, prev, vert)
										bm.faces.remove(f)
										for e in vert.link_edges:
											if prev in e.verts:
												dissedges1[posn].append(e)
							prev = vert
							prevedge = edge
						mesh.calc_tessface()

			# select inserted edges/verts
			for posn in range(len(vertlist)):
				for v in dissverts1[posn]:
					v.select = 1
				for e in dissedges1[posn]:
					e.select = 1

		# do distance shifting
		for posn in range(len(vertlist)):
			if railedges1[posn] != []:
				for v in vertlist[posn]:
					pv = dissverts1[posn][vertlist[posn].index(v)]
					rv = railverts1[posn][vertlist[posn].index(v)]
					sv = bmundo.verts[v.index]
					vec = rv.co - sv.co
					vec.length = abs(dist)
					pv.co = sv.co + vec


		#positive side handling
		if dist > 0 or scn.Both == True:
			for posn in range(len(vertlist)):
				if not(possubd[posn]):
					if scn.Both == False:
						# if just switched sides: remove positive side
						if negsubd[posn] == 1:
							bpy.ops.mesh.select_all(action="DESELECT")
							for vert in dissverts1[posn]:
								vert.select = 1
							for edge in dissedges1[posn]:
								edge.select = 1
							bpy.ops.mesh.dissolve_limited()
							railedges1[posn] = []
							railverts1[posn] = []
							dissverts1[posn] = []
							dissedges1[posn] = []
						negsubd[posn] = 0
					railedges2[posn] = []
					railverts2[posn] = []
					dissverts2[posn] = []
					dissedges2[posn] = []
			for posn in range(len(vertlist)):
				if not(possubd[posn]):
					# if just switched sides: look for slide constellations
					for vert in vertlist[posn]:
						if vertlist[posn].index(vert) == len(vertlist[posn]) - 1:
							break
						for loop in vert.link_loops:
							if loop.link_loop_prev.vert == vertlist[posn][vertlist[posn].index(vert) + 1]:
								railverts2[posn].append(loop.link_loop_next.vert)
								e = loop.edge
								railedges2[posn].append(e)
								if vertlist[posn].index(vert) == len(vertlist[posn]) - 2:
									railverts2[posn].append(loop.link_loop_prev.link_loop_prev.vert)
									e = loop.link_loop_prev.link_loop_prev.edge
									railedges2[posn].append(e)
			for posn in range(len(vertlist)):
				if not(possubd[posn]):
					possubd[posn] = 1
					if railedges2[posn] != []:
						# insert parallel edges
						prev = None
						popout = 0
						for idx in range(len(railedges2[posn])):
							if popout:
								break
							edge = railedges2[posn][idx]
							if idx == len(railedges2[posn]) - 2 and railverts2[posn][0] == railverts2[posn][len(railverts2[posn]) - 1]:
								# this handles closed edgeloops
								vert = startvert
								railedges2[posn].pop(len(railedges2[posn]) - 1)
								railverts2[posn].pop(len(railverts2[posn]) - 1)
								popout = 1
							else:
								dummy, vert = bmesh.utils.edge_split(edge, vertlist[posn][railedges2[posn].index(edge)], 0.5)
							if idx == 0:
								startvert = vert 
							dissverts2[posn].append(vert)
							if not(prev == None):
								for f in edge.link_faces:
									if prevedge in f.edges:
										bmesh.utils.face_split(f, vert, prev)
										bmesh.utils.face_split(f, prev, vert)
										bm.faces.remove(f)
										for e in vert.link_edges:
											if prev in e.verts:
												dissedges2[posn].append(e)
							prev = vert
							prevedge = edge
						mesh.calc_tessface()
					

			# select inserted edges/verts
			for posn in range(len(vertlist)):
				for v in dissverts2[posn]:
					v.select = 1
				for e in dissedges2[posn]:
					e.select = 1

		# do distance shifting
		for posn in range(len(vertlist)):
			if railedges2[posn] != []:
				for v in vertlist[posn]:
					pv = dissverts2[posn][vertlist[posn].index(v)]
					rv = railverts2[posn][vertlist[posn].index(v)]
					sv = bmundo.verts[v.index]
					vec = rv.co - sv.co
					vec.length = abs(dist)
					pv.co = sv.co + vec
		
		# create cap
		if not(capped):
			capsellist = []
			for posn in range(len(vertlist)):
				if scn.Both and scn.Cap:
					capped = 1
					
					def capendpoint(i):
						capedges = []
						es1 = None
						es2 = None
						vert = vertlist[posn][i]
						for e in vert.link_edges:
							v = e.other_vert(vert)
							if not(v in vertlist[posn]) and not(v in dissverts1[posn]) and not(v in dissverts2[posn]):
								capedges.append(e)
						if len(capedges) == 1:
							e = capedges[0]
							for f in e.link_faces:
								v2 = e.other_vert(vert)
								v2.select = 1
								if dissverts1[posn][i] in f.verts:
									f1, l1 = bmesh.utils.face_split(f, v2, dissverts1[posn][i])
									if e in f.edges:
										fj1 = f
										fo1 = f1
									else:
										fj1 = f1
										fo1 = f
									for es in v2.link_edges:
										if es.other_vert(v2) == dissverts1[posn][i]:
											es.select = 1
											es1 = es
								elif dissverts2[posn][i] in f.verts:
									f2, l1 = bmesh.utils.face_split(f, v2, dissverts2[posn][i])
									if e in f.edges:
										fj2 = f
										fo2 = f2
									else:
										fj2 = f2
										fo2 = f
									for es in v2.link_edges:
										if es.other_vert(v2) == dissverts2[posn][i]:
											es.select = 1
											es2 = es
							f3 = bmesh.utils.face_join((fj1, fj2))
						if es1 == None:
							caplist[posn].append((None, None, None, None, None, None, None))
						else:
							caplist[posn].append((es1, es2, vert, v2, f3, fo1, fo2))
						capsellist.append(es1)
						capsellist.append(es2)
							
					caplist[posn] = []
					capendpoint(0)
					capendpoint(-1)
			mesh.calc_tessface()

		# select original verts/edges
		for posn in range(len(vertlist)):
			for edge in edgelist[posn]:
				edge.select = 1
			for vert in vertlist[posn]:
				vert.select = 1
				
	bmesh.update_edit_mesh(mesh, destructive=True)
	mesh.update()
	



def do_paredge(self):

	global started, wrongsel, stop
	global dist, olddist, distset, oldboth, mbns, negsubd, possubd
	global bm, bmundo, mesh, region, scn
	global vertlist, edgelist, facelist, sellist2
	global meanmin, meanmax
	global dissverts1, dissedges1, railverts1, railedges1
	global dissverts2, dissedges2, railverts2, railedges2
	global caplist, capped, oldcap

	oldcap = 0
	capped = 0
	stop = 0
	dist = 0
	olddist = 0
	oldboth = 0
	wrongsel = 0
	mbns = 0
	negsubd = []
	possubd = []
	distset = 0
	railedges1 = []
	railedges2 = []
	railverts1 = []
	railverts2 = []
	dissedges1 = []
	dissedges2 = []
	dissverts1 = []
	dissverts2 = []
	caplist = []
	singledir = []
	firstvert = []

	if eval(str(bpy.app.build_revision)[2:7]) >= 47779:
		bpy.ops.mesh.sort_elements(elements={"VERT"})
	else:
		bpy.ops.mesh.vertices_sort()
	context = bpy.context
	scn = context.scene
	region = context.region  
	area = context.area
	selobj = bpy.context.active_object
	mesh = selobj.data
	bm = bmesh.from_edit_mesh(mesh)
	bmundo = bm.copy()
	started = 1

	sellist = []
	sellist2 = []
	edgelist = []
	vertlist = []
	for v in bm.verts:
		if v.select:
			sellist.append(v)
			sellist2.append(v)
	if len(sellist) <= 1:
		wrongsel = 1
		return
	# find first two connected verts: v and nxv
	# they consitute edge e
	
	# vertlist: make ordered list of selected vert-string
	# edgelist: make ordered list of selected edges-string
	p = 0
	while len(sellist) > 0:
		# as long as verts in selection list, keep creating new connected vert/edgelists
		v = sellist[0]
		railedges1.append([])
		railedges2.append([])
		railverts1.append([])
		railverts2.append([])
		dissedges1.append([])
		dissedges2.append([])
		dissverts1.append([])
		dissverts2.append([])
		caplist.append([])
		vertlist.append([])
		edgelist.append([])
		possubd.append(0)
		negsubd.append(0)
		singledir.append(None)
		firstvert.append(None)
		for e in v.link_edges:
			if e.select:
				vertlist[p].append(v)
				edgelist[p].append(e)
				nxv = e.other_vert(v)
				vertlist[p].append(nxv)
				break
		sellist.pop(sellist.index(v))
		try:
			sellist.pop(sellist.index(nxv))
		except:
			pass

		# add in front of lists	
		while len(sellist) > 0:
			facelist = []
			invlist = []
			found = 0
			l = len(vertlist[p])
			for f in vertlist[p][0].link_faces:
				if not(vertlist[p][1] in f.verts):
					facelist.append(f)
				else:
					invlist.append(f)
			# must be edgeloop(slice)
			if len(facelist) == 2:
				for fe in facelist[0].edges:
					if fe in facelist[1].edges:
						if fe.select:
							found = 1
							break
			elif len(facelist) == 1:
				for fe in vertlist[p][0].link_edges:
					if fe in facelist[0].edges:
						nt = 0
						for invf in invlist:
							if fe in invf.edges:
								nt = 1
						if not(nt):
							found = 1
							break
			if found:
				if fe.select:
					for fv in fe.verts:
						if fv != vertlist[p][0]:
							break
					vertlist[p].insert(0, fv)
					edgelist[p].insert(0, fe)
					sellist.pop(sellist.index(fv))
					continue
			break
		
		#store first vert for closedness checking
		firstvert[p] = vertlist[p][0]
		sellist.append(firstvert[p])

		# add to end of lists
		while len(sellist) > 0:
			facelist = []
			invlist = []
			found = 0
			l = len(vertlist[p])
			for f in vertlist[p][l - 1].link_faces:
				if not(vertlist[p][l - 2] in f.verts):
					facelist.append(f)
				else:
					invlist.append(f)
			# must be edgeloop(slice)
			if len(facelist) == 2:
				for fe in facelist[0].edges:
					if fe in facelist[1].edges:
						if fe.select:
							found = 1
							break
			elif len(facelist) == 1:
				found = 0
				for fe in vertlist[p][l - 1].link_edges:
					if fe in facelist[0].edges:
						nt = 0
						for invf in invlist:
							if fe in invf.edges:
								nt = 1
						if not(nt):
							found = 1
							break
			if found:
				if fe.select:
					for fv in fe.verts:
						if fv != vertlist[p][l - 1]:
							break
					vertlist[p].append(fv)
					edgelist[p].append(fe)
					sellist.pop(sellist.index(fv))
					continue
			break
		# handle closed/open selections
		if vertlist[p][len(vertlist[p]) - 1] == firstvert[p]:
			for edge in firstvert[p].link_edges:
				if edge.other_vert(firstvert[p]) == vertlist[p][len(vertlist[p]) - 2]:
					edgelist[p].append(edge)
					break
					vertlist[p].append(firstvert[p])
		else:
			sellist.pop(sellist.index(firstvert[p]))
		# next selected edgeloopslice
		p += 1


	# orient edge and vertlists parallel - reverse if necessary

	singledir[0] = edgelist[0][0].verts[0]		
	
	for i in range(len(edgelist) - 1):
		bpy.ops.mesh.select_all(action="DESELECT")
		# get first vert and edge for two adjacent slices
		for v in edgelist[i][0].verts:
			if len(edgelist[i]) == 1:
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
		bpy.ops.mesh.select_vertex_path(type='TOPOLOGICAL')
		
		for e in bm.edges:
			if e.verts[0].select and e.verts[1].select:
				e.select = 1
		
		# correct selected path when not connected neatly to vert from left or right(cant know direction)
		def correctsel(e1, v1, lst):
			found = 0
			# check situation where left/right connection is on some other slicevert than first
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
							if len(templ) < 2:
								v1.select = 0
								e1.select = 0
								v1 = e1.other_vert(v1)
								return e1, v1, "reverse"
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
				if len(templ) < 2:
					break
				for edge in v1.link_edges:
					if edge in templ[0].edges and edge in templ[1].edges:
						if edge.other_vert(v1).select:
							v1.select = 0
							edge.select = 0
							v1 = edge.other_vert(v1)
							e1 = edge
							found = 0
			return e1, v1, "normal"
							
		e1, v1, state1 = correctsel(e1, v1, edgelist[i])
		if state1 == "reverse":
			# special trick - mail me
			for j in range(i + 1):
				edgelist[j].reverse()
				vertlist[j].reverse()
		e2, v2, state2 = correctsel(e2, v2, edgelist[i+1])					
		if state2 == "reverse":
			# special trick - mail me
			edgelist[i+1].reverse()
			vertlist[i+1].reverse()

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
														vertlist[i+1].reverse()
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
														vertlist[i+1].reverse()
													break
											brk = 1
											break
									if brk == 1:
										break
							break
					break
#		if i == 50:
#			stop = 1
#			return

	bpy.ops.mesh.select_all(action="DESELECT")
	for posn in range(len(vertlist)):
		for v in vertlist[posn]:
			v.select = 1
		for e in edgelist[posn]:
			e.select = 1





	# try to guess min and max values for distance slider - can always use mouse to override
	co1 = vertlist[0][0].co
	co2 = vertlist[0][len(vertlist[0]) - 1].co				
	meanmin = (co1 - co2).length * -2
	meanmax = -meanmin
	if meanmax == 0:
		meanmax = meanmin = 1

	bpy.types.Scene.Distance = bpy.props.FloatProperty(
			name = "Distance", 
			description = "Enter distance",
			default = 0,
			min = meanmin,
			max = meanmax)
	
	
def redraw():
	
	global parchange
	
	if not(bpy.context.mode == "EDIT_MESH"):
		return
	
	# if parameter changes, reinsert/move edges
	if parchange:
		parchange = 0
		adapt(scn, None)

