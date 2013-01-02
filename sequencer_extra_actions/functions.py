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

import bpy
import os.path
import operator

from bpy.props import IntProperty
from bpy.props import FloatProperty
from bpy.props import EnumProperty
from bpy.props import BoolProperty
from bpy.props import StringProperty


imb_ext_image = [
    # IMG
    ".png", ".tga", ".bmp", ".jpg", ".jpeg", ".sgi", ".rgb",
    ".rgba", ".tif", ".tiff", ".tx", ".jp2", ".hdr", ".dds",
    ".dpx", ".cin", ".exr", ".rw2",
    # IMG QT
    ".gif", ".psd", ".pct", ".pict", ".pntg", ".qtif"]


imb_ext_movie = [
    ".avi", ".flc", ".mov", ".movie", ".mp4", ".m4v", ".m2v",
    ".m2t", ".m2ts", ".mts", ".mv", ".avs", ".wmv", ".ogv",
    ".dv", ".mpeg", ".mpg", ".mpg2", ".vob", ".mkv", ".flv",
    ".divx", ".xvid", ".mxf"]
    
movieextdict = [("1", ".avi", ""),
            ("2", ".flc", ""),
            ("3", ".mov", ""),
            ("4", ".movie", ""),
            ("5", ".mp4", ""),
            ("6", ".m4v", ""),
            ("7", ".m2v", ""),
            ("8", ".m2t", ""),
            ("9", ".m2ts", ""),
            ("10", ".mts", ""),
            ("11", ".mv", ""),
            ("12", ".avs", ""),
            ("13", ".wmv", ""),
            ("14", ".ogv", ""),
            ("15", ".dv", ""),
            ("16", ".mpeg", ""),
            ("17", ".mpg", ""),
            ("18", ".mpg2", ""),
            ("19", ".vob", ""),
            ("20", ".mkv", ""),
            ("21", ".flv", ""),
            ("22", ".divx", ""),
            ("23", ".xvid", ""),
            ("24", ".mxf", "")]


# Functions

def add_marker(text):
    scene = bpy.context.scene
    markers = scene.timeline_markers
    mark = markers.new(name=text)
    mark.frame = scene.frame_current


def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return None


def detect_strip_type(filepath):
    imb_ext_image = [
    # IMG
    ".png", ".tga", ".bmp", ".jpg", ".jpeg", ".sgi", ".rgb",
    ".rgba", ".tif", ".tiff", ".tx", ".jp2", ".hdr", ".dds",
    ".dpx", ".cin", ".exr",
    # IMG QT
    ".gif", ".psd", ".pct", ".pict", ".pntg", ".qtif"]

    imb_ext_movie = [
    ".avi", ".flc", ".mov", ".movie", ".mp4", ".m4v", ".m2v",
    ".m2t", ".m2ts", ".mts", ".mv", ".avs", ".wmv", ".ogv", ".ogg",
    ".dv", ".mpeg", ".mpg", ".mpg2", ".vob", ".mkv", ".flv",
    ".divx", ".xvid", ".mxf"]

    imb_ext_audio = [
    ".wav", ".ogg", ".oga", ".mp3", ".mp2", ".ac3", ".aac",
    ".flac", ".wma", ".eac3", ".aif", ".aiff", ".m4a"]

    extension = os.path.splitext(filepath)[1]
    extension = extension.lower()
    if extension in imb_ext_image:
        type = 'IMAGE'
    elif extension in imb_ext_movie:
        type = 'MOVIE'
    elif extension in imb_ext_audio:
        type = 'SOUND'
    else:
        type = None

    return type


def getpathfrombrowser():
    '''
    returns path from filebrowser
    '''
    scn = bpy.context.scene
    for a in bpy.context.window.screen.areas:
        if a.type == 'FILE_BROWSER':
            params = a.spaces[0].params
            break
    try:
        params
    except UnboundLocalError:
        #print("no browser")
        self.report({'ERROR_INVALID_INPUT'}, 'No visible File Browser')
        return {'CANCELLED'}
    path = params.directory
    return path


def getfilepathfrombrowser():
    '''
    returns path and file from filebrowser
    '''
    scn = bpy.context.scene
    for a in bpy.context.window.screen.areas:
        if a.type == 'FILE_BROWSER':
            params = a.spaces[0].params
            break
    try:
        params
    except UnboundLocalError:
        #print("no browser")
        self.report({'ERROR_INVALID_INPUT'}, 'No visible File Browser')
        return {'CANCELLED'}

    if params.filename == '':
        #print("no file selected")
        self.report({'ERROR_INVALID_INPUT'}, 'No file selected')
        return {'CANCELLED'}
    path = params.directory
    filename = params.filename
    return path, filename


def setpathinbrowser(path, file):
    '''
    set path and file in the filebrowser
    '''
    scn = bpy.context.scene
    for a in bpy.context.window.screen.areas:
        if a.type == 'FILE_BROWSER':
            params = a.spaces[0].params
            break
    try:
        params
    except UnboundLocalError:
        #print("no browser")
        self.report({'ERROR_INVALID_INPUT'}, 'No visible File Browser')
        return {'CANCELLED'}

    params.directory = path
    params.filename = file
    return path, params


def sortlist(filelist):
    '''
    given a list of tuplas (path, filename) returns a list sorted by filename
    '''
    filelist_sorted = sorted(filelist, key=operator.itemgetter(1))
    return filelist_sorted
    
# recursive load functions 

def loader(filelist):
    scn = bpy.context.scene
    if filelist:
        for i in filelist:
            setpathinbrowser(i[0], i[1])
            try:
                if scn.default_recursive_proxies:
                    bpy.ops.sequencerextra.placefromfilebrowserproxy(
                        proxy_suffix=scn.default_proxy_suffix,
                        proxy_extension=scn.default_proxy_extension,
                        proxy_path=scn.default_proxy_path,
                        build_25=scn.default_build_25,
                        build_50=scn.default_build_50,
                        build_75=scn.default_build_75,
                        build_100=scn.default_build_100)
                else:
                    bpy.ops.sequencerextra.placefromfilebrowser()
            except:
                print("Error loading file (recursive loader error): ", i[1])
                add_marker(i[1])
                #self.report({'ERROR_INVALID_INPUT'}, 'Error loading file ')
                #return {'CANCELLED'}
                pass

def onefolder():
    '''
    returns a list of MOVIE type files from folder selected in file browser
    '''
    filelist = []
    path, filename = getfilepathfrombrowser()
    extension = filename.rpartition(".")[2]
    #extension = scn.default_ext
    scn = bpy.context.scene

    if detect_strip_type(path + filename) == 'MOVIE':
        if scn.default_recursive_ext == True:
            for file in os.listdir(path):
                if file.rpartition(".")[2] == extension:
                    filelist.append((path, file))
        else:
            for file in os.listdir(path):
                filelist.append((path, file))
    return (filelist)

def recursive():
    '''
    returns a list of MOVIE type files recursively from file browser
    '''
    filelist = []
    path = getpathfrombrowser()
    scn = bpy.context.scene
    for i in movieextlist:
        if i[0] == scn.default_ext:
            extension = i[1].rpartition(".")[2]
    #pythonic way to magic:
    for root, dirs, files in os.walk(path):
        for f in files:
            if scn.default_recursive_ext == True:
                if f.rpartition(".")[2] == extension:
                    filelist.append((root, f))
            else:
                filelist.append((root, f))
    return filelist   



# jump to cut functions
def triminout(strip, sin, sout):
    start = strip.frame_start + strip.frame_offset_start
    end = start + strip.frame_final_duration
    if end > sin:
        if start < sin:
            strip.select_right_handle = False
            strip.select_left_handle = True
            bpy.ops.sequencer.snap(frame=sin)
            strip.select_left_handle = False
    if start < sout:
        if end > sout:
            strip.select_left_handle = False
            strip.select_right_handle = True
            bpy.ops.sequencer.snap(frame=sout)
            strip.select_right_handle = False
    return {'FINISHED'}


#------------ random edit functions...

def randompartition(lst,n,rand):
    division = len(lst) / float(n)
    lista = []
    for i in range(n):	lista.append(division)
    var=0
    for i in range(n-1):
        lista[i]+= random.randint(-int(rand*division),int(rand*division))
        var+=lista[i]
    if lista[n-1] != len(lst)-var:
        lista[n-1] = len(lst)-var
    random.shuffle(lista)
    division = len(lst) / float(n)
    count = 0
    newlist=[]
    for i in range(n):
        print(lst[count : int(lista[i]-1)+count])
        newlist.append([lst[count : int(lista[i]-1)+count]])
        count += int(lista[i]) 
    return newlist


