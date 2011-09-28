# Converts a formated string to a float tuple:
#   IN - '(0.5, 0.2)' -> CONVERT -> OUT - (0.5, 0.2)
def toTuple(stringIn):  
    sTemp = str(stringIn)[1:len(str(stringIn)) - 1].split(', ')
    fTemp = []
    for i in sTemp:
        fTemp.append(float(i))
    return tuple(fTemp)

# Converts a formated string to a float tuple:
#   IN - '[0.5, 0.2]' -> CONVERT -> OUT - [0.5, 0.2]
def toList(stringIn):  
    sTemp = str(stringIn)[1:len(str(stringIn)) - 1].split(', ')
    fTemp = []
    for i in sTemp:
        fTemp.append(float(i))
    return fTemp

# Converts each item of a list into a float:
def toFloats(inList):
    outList = []
    for i in inList:
        outList.append(float(i))
    return outList

# Converts each item of a list into an integer:
def toInts(inList):
    outList = []
    for i in inList:
        outList.append(int(i))
    return outList

# Sets all faces smooth.  Done this way since I can't
# find a simple way without using bpy.ops:
def smooth(mesh):
    for i in mesh.faces:
        i.use_smooth = True
    return mesh
