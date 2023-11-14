# SPDX-FileCopyrightText: 2023 Sebastian Schrand
#
# SPDX-License-Identifier: GPL-2.0-or-later


#--- LICENSE ---
# GNU GPL
# Import is based on using information from olefile IO sourcecode
# and the FreeCAD Autodesk 3DS Max importer ImportMAX
#
# olefile (formerly OleFileIO_PL) is copyright (c) 2005-2018 Philippe Lagadec
# (https://www.decalage.info)
#
# ImportMAX is copyright (c) 2017-2022 Jens M. Plonka
# (https://www.github.com/jmplonka/Importer3D)


bl_info = {
    "name": "Import Autodesk MAX (.max)",
    "author": "Sebastian Sille, Philippe Lagadec, Jens M. Plonka",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "File > Import",
    "description": "Import 3DSMAX meshes & materials",
    "warning": "",
    "filepath_url": "",
    "category": "Import-Export"}


##################
# IMPORT MODULES #
##################

import io, re
import os, sys, zlib
import time, datetime
import math, mathutils
import bpy, bpy_extras
import struct, numpy, array
from bpy_extras import node_shader_utils
from bpy_extras.image_utils import load_image
from bpy_extras.io_utils import axis_conversion
from bpy_extras.io_utils import orientation_helper

@orientation_helper(axis_forward='Y', axis_up='Z')

### IMPORT OPERATOR ###
class Import_max(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import Autodesk MAX"""
    bl_idname = "import_autodesk.max"
    bl_label = "Import Autodesk MAX (.max)"

    filename_ext = ".max"
    filter_glob: bpy.props.StringProperty(default="*.max", options={'HIDDEN'},)

    def execute(self, context):
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
        global_matrix = axis_conversion(from_forward=self.axis_forward, from_up=self.axis_up,).to_4x4()
        keywords["global_matrix"] = global_matrix

        return load(self, context, **keywords)

### REGISTER ###
def menu_func(self, context):
    self.layout.operator(Import_max.bl_idname, text="Autodesk MAX (.max)")

def register():
    bpy.utils.register_class(Import_max)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    bpy.utils.unregister_class(Import_max)


###################
# DATA STRUCTURES #
###################

MAGIC = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
WORD_CLSID = "00020900-0000-0000-C000-000000000046"

MAXREGSECT = 0xFFFFFFFA  # (-6) maximum SECT
DIFSECT = 0xFFFFFFFC  # (-4) denotes a DIFAT sector in a FAT
FATSECT = 0xFFFFFFFD  # (-3) denotes a FAT sector in a FAT
ENDOFCHAIN = 0xFFFFFFFE  # (-2) end of a virtual stream chain
FREESECT = 0xFFFFFFFF  # (-1) unallocated sector
MAXREGSID = 0xFFFFFFFA  # (-6) maximum directory entry ID
NOSTREAM = 0xFFFFFFFF  # (-1) unallocated directory entry
UNKNOWN_SIZE = 0x7FFFFFFF
MIN_FILE_SIZE = 1536

STGTY_EMPTY = 0 #: empty directory entry
STGTY_STORAGE = 1 #: element is a storage object
STGTY_STREAM = 2 #: element is a stream object
STGTY_LOCKBYTES = 3 #: element is an ILockBytes object
STGTY_PROPERTY = 4 #: element is an IPropertyStorage object
STGTY_ROOT = 5 #: element is a root storage

VT_EMPTY=0; VT_NULL=1; VT_I2=2; VT_I4=3; VT_R4=4; VT_R8=5; VT_CY=6;
VT_DATE=7; VT_BSTR=8; VT_DISPATCH=9; VT_ERROR=10; VT_BOOL=11;
VT_VARIANT=12; VT_UNKNOWN=13; VT_DECIMAL=14; VT_I1=16; VT_UI1=17;
VT_UI2=18; VT_UI4=19; VT_I8=20; VT_UI8=21; VT_INT=22; VT_UINT=23;
VT_VOID=24; VT_HRESULT=25; VT_PTR=26; VT_SAFEARRAY=27; VT_CARRAY=28;
VT_USERDEFINED=29; VT_LPSTR=30; VT_LPWSTR=31; VT_FILETIME=64;
VT_BLOB=65; VT_STREAM=66; VT_STORAGE=67; VT_STREAMED_OBJECT=68;
VT_STORED_OBJECT=69; VT_BLOB_OBJECT=70; VT_CF=71; VT_CLSID=72;
VT_VECTOR=0x1000;

INVALID_NAME = re.compile('^[0-9].*')
UNPACK_BOX_DATA = struct.Struct('<HIHHBff').unpack_from  # Index, int, short, short, byte, float, Length

DEBUG = False
TYP_NAME = 0x0962

CONFIG = []
CLS_DATA = []
DLL_DIR_LIST = []
CLS_DIR3_LIST = []
VID_PST_QUE = []
SCENE_LIST = []

SKIPPABLE = {
	0x0000000000001002: 'Camera',
	0x0000000000001011: 'Omni',
	0x0000000000001013: 'Free Direct',
	0x0000000000001020: 'Camera Target',
	0x0000000000001040: 'Line',
	0x0000000000001065: 'Rectangle',
	0x0000000000001097: 'Ellipse',
	0x0000000000001999: 'Circle',
	0x0000000000002013: 'Point',
	0x0000000000009125: 'Biped Object',
	0x0000000000876234: 'Dummy',
	0x05622B0D69011E82: 'Compass',
	0x12A822FB76A11646: 'CV Surface',
	0x1EB3430074F93B07: 'Particle View',
	0x2ECCA84028BF6E8D: 'Bone',
	0x3BDB0E0C628140F6: 'VRayPlane',
	0x4E9B599047DB14EF: 'Slider',
	0x522E47057BF61478: 'Sky',
	0x5FD602DF3C5575A1: 'VRayLight',
	0x77566F65081F1DFC: 'Plane',
}


def get_valid_name(name):
    if (INVALID_NAME.match(name)): return "_%s"%(name.encode('utf8'))
    return "%s"%(name.encode('utf8'))

def i8(data):
    return data if data.__class__ is int else data[0]

def i16(data, offset=0):
    return struct.unpack("<H", data[offset:offset + 2])[0]

def i32(data, offset=0):
    return struct.unpack("<I", data[offset:offset + 4])[0]

def get_byte(data, offset=0):
    size = offset + 1
    value = struct.unpack('<B', data[offset:size])[0]
    return value, size

def get_short(data, offset=0):
    size = offset + 2
    value = struct.unpack('<H', data[offset:size])[0]
    return value, size

def get_long(data, offset=0):
    size = offset + 4
    value = struct.unpack('<I', data[offset:size])[0]
    return value, size

def get_float(data, offset=0):
    size = offset + 4
    value = struct.unpack('<f', data[offset:size])[0]
    return value, size

def get_bytes(data, offset=0, count=1):
    size = offset + count
    values = struct.unpack('<'+'B'*count, data[offset:size])
    return values, size

def get_shorts(data, offset=0, count=1):
    size = offset + count * 2
    values = struct.unpack('<'+'H'*count, data[offset:size])
    return values, size

def get_longs(data, offset=0, count=1):
    size = offset + count * 4
    values = struct.unpack('<'+'I'*count, data[offset:size])
    return values, size

def get_floats(data, offset=0, count=1):
    size = offset + count * 4
    values = struct.unpack('<'+'f'*count, data[offset:size])
    return values, size


def _clsid(clsid):
    """Converts a CLSID to a readable string."""
    assert len(clsid) == 16
    if not clsid.strip(b"\0"):
        return ""
    return (("%08X-%04X-%04X-%02X%02X-" + "%02X" * 6) %
            ((i32(clsid, 0), i16(clsid, 4), i16(clsid, 6)) +
            tuple(map(i8, clsid[8:16]))))

def is_maxfile (filename):
    if hasattr(filename, 'read'):
        header = filename.read(len(MAGIC))
        filename.seek(0)
    elif isinstance(filename, bytes) and len(filename) >= MIN_FILE_SIZE:
        header = filename[:len(MAGIC)]
    else:
        with open(filename, 'rb') as fp:
            header = fp.read(len(MAGIC))
    if header == MAGIC:
        return True
    else:
        return False


class MaxStream(io.BytesIO):

    def __init__(self, fp, sect, size, offset, sectorsize, fat, filesize):
        unknown_size = False
        if size == UNKNOWN_SIZE:
            size = len(fat)*sectorsize
            unknown_size = True
        nb_sectors = (size + (sectorsize-1)) // sectorsize

        data = []
        for i in range(nb_sectors):
            try:
                fp.seek(offset + sectorsize * sect)
            except:
                break
            sector_data = fp.read(sectorsize)
            data.append(sector_data)
            try:
                sect = fat[sect] & 0xFFFFFFFF
            except IndexError:
                break
        data = b"".join(data)
        if len(data) >= size:
            data = data[:size]
            self.size = size
        else:
            self.size = len(data)
        io.BytesIO.__init__(self, data)


class MaxFileDirEntry:
    STRUCT_DIRENTRY = '<64sHBBIII16sIQQIII'
    DIRENTRY_SIZE = 128
    assert struct.calcsize(STRUCT_DIRENTRY) == DIRENTRY_SIZE

    def __init__(self, entry, sid, maxfile):
        self.sid = sid
        self.maxfile = maxfile
        self.kids = []
        self.kids_dict = {}
        self.used = False
        (
            self.name_raw,
            self.namelength,
            self.entry_type,
            self.color,
            self.sid_left,
            self.sid_right,
            self.sid_child,
            clsid,
            self.dwUserFlags,
            self.createTime,
            self.modifyTime,
            self.isectStart,
            self.sizeLow,
            self.sizeHigh
        ) = struct.unpack(MaxFileDirEntry.STRUCT_DIRENTRY, entry)

        if self.namelength>64:
            self.namelength = 64
        self.name_utf16 = self.name_raw[:(self.namelength - 2)]
        self.name = maxfile._decode_utf16_str(self.name_utf16)
        # print('DirEntry SID=%d: %s' % (self.sid, repr(self.name)))
        if maxfile.sectorsize == 512:
            self.size = self.sizeLow
        else:
            self.size = self.sizeLow + (int(self.sizeHigh) << 32)
        self.clsid = _clsid(clsid)
        self.is_minifat = False
        if self.entry_type in (STGTY_ROOT, STGTY_STREAM) and self.size > 0:
            if self.size < maxfile.minisectorcutoff \
            and self.entry_type == STGTY_STREAM: # only streams can be in MiniFAT
                self.is_minifat = True
            else:
                self.is_minifat = False
            maxfile._check_duplicate_stream(self.isectStart, self.is_minifat)
        self.sect_chain = None

    def build_sect_chain(self, maxfile):
        if self.sect_chain:
            return
        if self.entry_type not in (STGTY_ROOT, STGTY_STREAM) or self.size == 0:
            return
        self.sect_chain = list()
        if self.is_minifat and not maxfile.minifat:
            maxfile.loadminifat()
        next_sect = self.isectStart
        while next_sect != ENDOFCHAIN:
            self.sect_chain.append(next_sect)
            if self.is_minifat:
                next_sect = maxfile.minifat[next_sect]
            else:
                next_sect = maxfile.fat[next_sect]

    def build_storage_tree(self):
        if self.sid_child != NOSTREAM:
            self.append_kids(self.sid_child)
            self.kids.sort()

    def append_kids(self, child_sid):
        if child_sid == NOSTREAM:
            return
        else:
            child = self.maxfile._load_direntry(child_sid)
            if child.used:
                return
            child.used = True
            self.append_kids(child.sid_left)
            name_lower = child.name.lower()
            self.kids.append(child)
            self.kids_dict[name_lower] = child
            self.append_kids(child.sid_right)
            child.build_storage_tree()

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)


class ImportMaxFile:

    def __init__(self, filename=None, write_mode=False, debug=False):

        self.write_mode = write_mode
        self._filesize = None
        self.byte_order = None
        self.directory_fp = None
        self.direntries = None
        self.dll_version = None
        self.fat = None
        self.first_difat_sector = None
        self.first_dir_sector = None
        self.first_mini_fat_sector = None
        self.fp = None
        self.header_clsid = None
        self.header_signature = None
        self.metadata = None
        self.mini_sector_shift = None
        self.mini_sector_size = None
        self.mini_stream_cutoff_size = None
        self.minifat = None
        self.minifatsect = None
        self.minisectorcutoff = None
        self.minisectorsize = None
        self.ministream = None
        self.minor_version = None
        self.nb_sect = None
        self.num_difat_sectors = None
        self.num_dir_sectors = None
        self.num_fat_sectors = None
        self.num_mini_fat_sectors = None
        self.reserved1 = None
        self.reserved2 = None
        self.root = None
        self.sector_shift = None
        self.sector_size = None
        self.transaction_signature_number = None
        if filename:
            self.open(filename, write_mode=write_mode)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _decode_utf16_str(self, utf16_str, errors='replace'):
        unicode_str = utf16_str.decode('UTF-16LE', errors)
        return unicode_str

    def open(self, filename, write_mode=False):
        self.write_mode = write_mode
        if hasattr(filename, 'read'):
            self.fp = filename
        elif isinstance(filename, bytes) and len(filename) >= MIN_FILE_SIZE:
            self.fp = io.BytesIO(filename)
        else:
            if self.write_mode:
                mode = 'r+b'
            else:
                mode = 'rb'
            self.fp = open(filename, mode)
        filesize=0
        self.fp.seek(0, os.SEEK_END)
        try:
            filesize = self.fp.tell()
        finally:
            self.fp.seek(0)
        self._filesize = filesize
        self._used_streams_fat = []
        self._used_streams_minifat = []
        header = self.fp.read(512)

        fmt_header = '<8s16sHHHHHHLLLLLLLLLL'
        header_size = struct.calcsize(fmt_header)
        header1 = header[:header_size]
        (
            self.header_signature,
            self.header_clsid,
            self.minor_version,
            self.dll_version,
            self.byte_order,
            self.sector_shift,
            self.mini_sector_shift,
            self.reserved1,
            self.reserved2,
            self.num_dir_sectors,
            self.num_fat_sectors,
            self.first_dir_sector,
            self.transaction_signature_number,
            self.mini_stream_cutoff_size,
            self.first_mini_fat_sector,
            self.num_mini_fat_sectors,
            self.first_difat_sector,
            self.num_difat_sectors
        ) = struct.unpack(fmt_header, header1)

        self.sector_size = 2**self.sector_shift
        self.mini_sector_size = 2**self.mini_sector_shift
        if self.mini_stream_cutoff_size != 0x1000:
            self.mini_stream_cutoff_size = 0x1000
        self.nb_sect = ((filesize + self.sector_size-1) // self.sector_size) - 1

        # file clsid
        self.header_clsid = _clsid(header[8:24])
        self.sectorsize = self.sector_size  #1 << i16(header, 30)
        self.minisectorsize = self.mini_sector_size   #1 << i16(header, 32)
        self.minisectorcutoff = self.mini_stream_cutoff_size  # i32(header, 56)
        self._check_duplicate_stream(self.first_dir_sector)
        if self.num_mini_fat_sectors:
            self._check_duplicate_stream(self.first_mini_fat_sector)
        if self.num_difat_sectors:
            self._check_duplicate_stream(self.first_difat_sector)

        # Load file allocation tables
        self.loadfat(header)
        self.loaddirectory(self.first_dir_sector)
        self.minifatsect = self.first_mini_fat_sector

    def close(self):
        self.fp.close()

    def _check_duplicate_stream(self, first_sect, minifat=False):
        if minifat:
            used_streams = self._used_streams_minifat
        else:
            if first_sect in (DIFSECT,FATSECT,ENDOFCHAIN,FREESECT):
                return
            used_streams = self._used_streams_fat
        if first_sect in used_streams:
            pass
        else:
            used_streams.append(first_sect)

    def sector_array(self, sect):
        ary = array.array('I', sect)
        if sys.byteorder == 'big':
            ary.byteswap()
        return ary

    def loadfat_sect(self, sect):
        if isinstance(sect, array.array):
            fat1 = sect
        else:
            fat1 = self.sector_array(sect)
        isect = None
        for isect in fat1:
            isect = isect & 0xFFFFFFFF
            if isect == ENDOFCHAIN or isect == FREESECT:
                break
            sector = self.getsect(isect)
            nextfat = self.sector_array(sector)
            self.fat = self.fat + nextfat
        return isect

    def loadfat(self, header):
        sect = header[76:512]
        self.fat = array.array('I')
        self.loadfat_sect(sect)
        if self.num_difat_sectors != 0:
            nb_difat_sectors = (self.sectorsize//4) - 1
            nb_difat = (self.num_fat_sectors - 109 + nb_difat_sectors - 1) // nb_difat_sectors
            isect_difat = self.first_difat_sector
            for i in range(nb_difat):
                sector_difat = self.getsect(isect_difat)
                difat = self.sector_array(sector_difat)
                self.loadfat_sect(difat[:nb_difat_sectors])
                isect_difat = difat[nb_difat_sectors]
        if len(self.fat) > self.nb_sect:
            self.fat = self.fat[:self.nb_sect]

    def loadminifat(self):
        stream_size = self.num_mini_fat_sectors * self.sector_size
        nb_minisectors = (self.root.size + self.mini_sector_size - 1) // self.mini_sector_size
        used_size = nb_minisectors * 4
        sect = self._open(self.minifatsect, stream_size, force_FAT=True).read()
        self.minifat = self.sector_array(sect)
        self.minifat = self.minifat[:nb_minisectors]

    def getsect(self, sect):
        try:
            self.fp.seek(self.sectorsize * (sect + 1))
        except:
            print('MAX sector index out of range')
        sector = self.fp.read(self.sectorsize)
        return sector

    def loaddirectory(self, sect):
        self.directory_fp = self._open(sect, force_FAT=True)
        max_entries = self.directory_fp.size // 128
        self.direntries = [None] * max_entries
        root_entry = self._load_direntry(0)
        self.root = self.direntries[0]
        self.root.build_storage_tree()

    def _load_direntry (self, sid):
        if self.direntries[sid] is not None:
            return self.direntries[sid]
        self.directory_fp.seek(sid * 128)
        entry = self.directory_fp.read(128)
        self.direntries[sid] = MaxFileDirEntry(entry, sid, self)
        return self.direntries[sid]

    def _open(self, start, size = UNKNOWN_SIZE, force_FAT=False):
        if size < self.minisectorcutoff and not force_FAT:
            if not self.ministream:
                self.loadminifat()
                size_ministream = self.root.size
                self.ministream = self._open(self.root.isectStart,
                    size_ministream, force_FAT=True)
            return MaxStream(fp=self.ministream, sect=start, size=size,
                             offset=0, sectorsize=self.minisectorsize,
                             fat=self.minifat, filesize=self.ministream.size)
        else:
            return MaxStream(fp=self.fp, sect=start, size=size,
                             offset=self.sectorsize,
                             sectorsize=self.sectorsize, fat=self.fat,
                             filesize=self._filesize)

    def _list(self, files, prefix, node, streams=True, storages=False):
        prefix = prefix + [node.name]
        for entry in node.kids:
            if entry.entry_type == STGTY_STORAGE:
                if storages:
                    files.append(prefix[1:] + [entry.name])
                self._list(files, prefix, entry, streams, storages)
            elif entry.entry_type == STGTY_STREAM:
                if streams:
                    files.append(prefix[1:] + [entry.name])

    def listdir(self, streams=True, storages=False):
        files = []
        self._list(files, [], self.root, streams, storages)
        return files

    def _find(self, filename):
        if isinstance(filename, str):
            filename = filename.split('/')
        node = self.root
        for name in filename:
            for kid in node.kids:
                if kid.name.lower() == name.lower():
                    break
            node = kid
        return node.sid

    def openstream(self, filename):
        sid = self._find(filename)
        entry = self.direntries[sid]
        return self._open(entry.isectStart, entry.size)

    def get_type(self, filename):
        try:
            sid = self._find(filename)
            entry = self.direntries[sid]
            return entry.entry_type
        except:
            return False

    def getclsid(self, filename):
        sid = self._find(filename)
        entry = self.direntries[sid]
        return entry.clsid

    def get_size(self, filename):
        sid = self._find(filename)
        entry = self.direntries[sid]
        return entry.size

    def get_rootentry_name(self):
        return self.root.name

    def getproperties(self, filename, convert_time=False, no_conversion=None):
        if no_conversion == None:
            no_conversion = []
        streampath = filename
        if not isinstance(streampath, str):
            streampath = '/'.join(streampath)
        fp = self.openstream(filename)
        data = {}
        try:
            s = fp.read(28)
            clsid = _clsid(s[8:24])
            s = fp.read(20)
            fmtid = _clsid(s[:16])
            fp.seek(i32(s, 16))
            s = b"****" + fp.read(i32(fp.read(4)) - 4)
            num_props = i32(s, 4)
        except BaseException as exc:
            return data

        num_props = min(num_props, int(len(s) / 8))
        for i in range(num_props):
            property_id = 0
            try:
                property_id = i32(s, 8 + i*8)
                offset = i32(s, 12 + i*8)
                property_type = i32(s, offset)
                if property_type == VT_I2:  # 16-bit signed integer
                    value = i16(s, offset + 4)
                    if value >= 32768:
                        value = value - 65536
                elif property_type == VT_UI2:  # 2-byte unsigned integer
                    value = i16(s, offset + 4)
                elif property_type in (VT_I4, VT_INT, VT_ERROR):
                    value = i32(s, offset + 4)
                elif property_type in (VT_UI4, VT_UINT):  # 4-byte unsigned integer
                    value = i32(s, offset + 4)
                elif property_type in (VT_BSTR, VT_LPSTR):
                    count = i32(s, offset + 4)
                    value = s[offset + 8:offset + 8 + count - 1]
                    value = value.replace(b'\x00', b'')
                elif property_type == VT_BLOB:
                    count = i32(s, offset + 4)
                    value = s[offset + 8:offset + 8 + count]
                elif property_type == VT_LPWSTR:
                    count = i32(s, offset + 4)
                    value = self._decode_utf16_str(s[offset + 8:offset + 8 + count*2])
                elif property_type == VT_FILETIME:
                    value = int(i32(s, offset + 4)) + (int(i32(s, offset + 8)) << 32)
                    if convert_time and property_id not in no_conversion:
                        _FILETIME_null_date = datetime.datetime(1601, 1, 1, 0, 0, 0)
                        value = _FILETIME_null_date + datetime.timedelta(microseconds=value // 10)
                    else:
                        value = value // 10000000
                elif property_type == VT_UI1:  # 1-byte unsigned integer
                    value = i8(s[offset + 4])
                elif property_type == VT_CLSID:
                    value = _clsid(s[offset + 4:offset + 20])
                elif property_type == VT_CF:
                    count = i32(s, offset + 4)
                    value = s[offset + 8:offset + 8 + count]
                elif property_type == VT_BOOL:
                    value = bool(i16(s, offset + 4))
                else:
                    value = None

                data[property_id] = value
            except BaseException as exc:
                print('Error while parsing property_id:', exc)
        return data


class MaxChunk():

    def __init__(self, types, size, level, number):
        self.number = number
        self.types = types
        self.level = level
        self.parent = None
        self.previous = None
        self.next = None
        self.size = size
        self.unknown = True
        self.format = None
        self.data = None
        self.resolved = False

    def __str__(self):
        if (self.unknown == True):
            return "%s[%4x] %04X: %s" %("  "*self.level, self.number, self.types, ":".join("%02x"%(c) for c in self.data))
        return "%s[%4x] %04X: %s=%s" %("  "*self.level, self.number, self.types, self.format, self.data)


class ByteArrayChunk(MaxChunk):

    def __init__(self, types, data, level, number):
        MaxChunk.__init__(self, types, data, level, number)

    def set(self, data, name, fmt, start, end):
        try:
            self.data = struct.unpack(fmt, data[start:end])
            self.format = name
            self.unknown = False
        except Exception as exc:
            self.data = data
            # print('StructError:', exc, name)

    def set_string(self, data):
        try:
            self.data = data.decode('UTF-16LE')
            self.format = "Str16"
            self.unknown = False
        except:
            self.data = data

    def set_le16_string(self, data):
        try:
            long, offset = get_long(data, 0)
            self.data = data[offset:offset + l * 2].decode('utf-16-le')
            if (self.data[-1] == b'\0'):
                self.data = self.data[0:-1]
            self.format = "LStr16"
            self.unknown = False
        except:
            self.data = data

    def set_data(self, data):
        if (self.types in [0x0340, 0x4001, 0x0456, 0x0962]):
            self.set_string(data)
        elif (self.types in [0x2034, 0x2035]):
            self.set(data, "ints", '<'+'I'*int(len(data) / 4), 0, len(data))
        elif (self.types in [0x2501, 0x2503, 0x2504, 0x2505, 0x2511]):
            self.set(data, "floats", '<'+'f'*int(len(data) / 4), 0, len(data))
        elif (self.types == 0x2510):
            self.set(data, "struct", '<'+'f'*int(len(data) / 4 - 1) + 'I', 0, len(data))
        elif (self.types == 0x0100):
            self.set(data, "float", '<f', 0, len(data))
        else:
            self.unknown = True
            self.data = data


class ClassIDChunk(ByteArrayChunk):

    def __init__(self, types, data, level, number):
        MaxChunk.__init__(self, types, data, level, number)
        self.dll = None

    def set_data(self, data):
        if (self.types == 0x2042):
            self.set_string(data)  # ClsName
        elif (self.types == 0x2060):
            self.set(data, "struct", '<IQI', 0, 16)  # DllIndex, ID, SuperID
        else:
            self.unknown = False
            self.data =  ":".join("%02x"%(c) for c in data)


class DirectoryChunk(ByteArrayChunk):

    def __init__(self, types, data, level, number):
        MaxChunk.__init__(self, types, data, level, number)

    def set_data(self, data):
        if (self.types == 0x2039):
            self.set_string(data)
        elif (self.types == 0x2037):
            self.set_string(data)


class ContainerChunk(MaxChunk):

    def __init__(self, types, data, level, number, primitiveReader=ByteArrayChunk):
        MaxChunk.__init__(self, types, data, level, number)
        self.primitiveReader = primitiveReader

    def __str__(self):
        if (self.unknown == True):
            return "%s[%4x] %04X" %("" * self.level, self.number, self.types)
        return "%s[%4x] %04X: %s" %("" * self.level, self.number, self.types, self.format)

    def get_first(self, types):
        for child in self.children:
            if (child.types == types):
                return child
        return None

    def set_data(self, data):
        previous = None
        next = None
        reader = ChunkReader()
        self.children = reader.get_chunks(data, self.level + 1, ContainerChunk, self.primitiveReader)


class SceneChunk(ContainerChunk):

    def __init__(self, types, data, level, number, primitiveReader=ByteArrayChunk):
        MaxChunk.__init__(self, types, data, level, number)
        self.primitiveReader = primitiveReader
        self.matrix = None

    def __str__(self):
        if (self.unknown == True):
            return "%s[%4x] %s" %("  "*self.level, self.number, get_class_name(self))
        return "%s[%4x] %s: %s" %("  "*self.level, self.number, get_class_name(self), self.format)

    def set_data(self, data):
        previous = None
        next = None
        # print('Scene', "%s\n" %(self))
        reader = ChunkReader()
        self.children = reader.get_chunks(data, self.level + 1, SceneChunk, ByteArrayChunk)


class ChunkReader():

    def __init__(self, name=None):
        self.name = name

    def get_chunks(self, data, level, containerReader, primitiveReader):
        chunks = []
        offset = 0
        if (level == 0):
            short, offset = get_short(data, 0)
            long, offset = get_long(data, offset)
            if (short == 0x8B1F):
                short, offset = get_long(data, offset)
                if (short == 0x0B000000):
                    data = zlib.decompress(data, zlib.MAX_WBITS|32)
            print("  reading '%s'..."%self.name, len(data))
        while offset < len(data):
            old = offset
            offset, chunk = self.get_next_chunk(data, offset, level, len(chunks), containerReader, primitiveReader)
            chunks.append(chunk)
        return chunks

    def get_next_chunk(self, data, offset, level, number, containerReader, primitiveReader):
        header = 6
        typ, siz, = struct.unpack("<Hi", data[offset:offset+header])
        chunksize = siz & 0x7FFFFFFF
        if (siz == 0):
            siz, = struct.unpack("<q", data[offset+header:offset+header+8])
            header += 8
            chunksize = siz & 0x7FFFFFFFFFFFFFFF
        if (siz < 0):
            chunk = containerReader(typ, chunksize, level, number, primitiveReader)
        else:
            chunk = primitiveReader(typ, chunksize, level, number)
        chunkdata = data[offset + header:offset + chunksize]
        chunk.set_data(chunkdata)
        return offset + chunksize, chunk


class Point3d():

    def __init__(self):
        self.points = None
        self.flags = 0
        self.fH = 0
        self.f1 = 0
        self.f2 = 0
        self.fA = []

    def __str__(self):
        return "[%s] - %X, %X, %X, [%s]" %('/'.join("%d" %p for p in self.points), self.fH, self.f1, self.f2, ','.join("%X" %f for f in self.fA))


class Material():

    def __init__(self):
        self.data = {}

    def set(self, name, value):
        self.data[name] = value

    def get(self, name, default=None):
        value = None
        if (name in self.data):
            value = self.data[name]
        if (value is None):
            return default
        return value


def get_node(index):
    if isinstance(index, tuple):
        index = index[0]
    global SCENE_LIST
    if (index < len(SCENE_LIST[0].children)):
        return SCENE_LIST[0].children[index]
    return None


def get_node_parent(node):
    parent = None
    if (node):
        chunk = node.get_first(0x0960)
        if (chunk is not None):
            idx, offset = get_long(chunk.data, 0)
            parent = get_node(idx)
            if (parent is None):
                print("parent index %X < %X!\n" %(idx, len(SCENE_LIST)))
    return parent


def get_node_name(node):
    if (node):
        name = node.get_first(TYP_NAME)
        if (name):
            return name.data
    return None


def get_class(chunk):
    global CLS_DIR3_LIST
    if (chunk.types < len(CLS_DIR3_LIST)):
        return CLS_DIR3_LIST[chunk.types]
    return None


def get_dll(container):
    global DLL_DIR_LIST
    idx = container.get_first(0x2060).data[0]
    if (idx < len(DLL_DIR_LIST)):
        return DLL_DIR_LIST[idx]
    return None


def get_guid(chunk):
    cls = get_class(chunk)
    if (cls):
        return cls.get_first(0x2060).data[1]
    return chunk.types


def get_super_id(chunk):
    cls = get_class(chunk)
    if (cls):
        return cls.get_first(0x2060).data[2]
    return None


def get_class_name(chunk):
    cls = get_class(chunk)
    if (cls):
        clsName = cls.get_first(0x2042).data
        try:
            return "'%s'" %(clsName)
        except:
            return "'%r'" %(clsName)
    return u"%04X" %(chunk.types)


def get_references(chunk):
    refs = chunk.get_first(0x2034)
    if (refs):
        references = [get_node(idx) for idx in refs.data]
    return references


def get_reference(chunk):
    references = {}
    refs = chunk.get_first(0x2035)
    if (refs):
        types = refs.data[0]
        offset = 1
        while offset < len(refs.data):
            key = refs.data[offset]
            offset += 1
            idx = refs.data[offset]
            offset += 1
            references[key] = get_node(idx)
    return references


def read_chunks(maxfile, name, filename, containerReader=ContainerChunk, primitiveReader=ByteArrayChunk):
    with maxfile.openstream(name) as file:
        scene = file.read()
        reader = ChunkReader(name)
        return reader.get_chunks(scene, 0, containerReader, primitiveReader)


def read_class_data(maxfile, filename):
    global CLS_DATA
    CLS_DATA = read_chunks(maxfile, 'ClassData', filename+'.ClsDat.bin')


def read_class_directory(maxfile, filename):
    global CLS_DIR3_LIST
    try:
        CLS_DIR3_LIST = read_chunks(maxfile, 'ClassDirectory3', filename+'.ClsDir3.bin', ContainerChunk, ClassIDChunk)
    except:
        CLS_DIR3_LIST = read_chunks(maxfile, 'ClassDirectory', filename+'.ClsDir.bin', ContainerChunk, ClassIDChunk)
    for clsdir in CLS_DIR3_LIST:
        clsdir.dll = get_dll(clsdir)


def read_config(maxfile, filename):
    global CONFIG
    CONFIG = read_chunks(maxfile, 'Config', filename+'.Cnf.bin')


def read_directory(maxfile, filename):
    global DLL_DIR_LIST
    DLL_DIR_LIST = read_chunks(maxfile, 'DllDirectory', filename+'.DllDir.bin', ContainerChunk, DirectoryChunk)


def read_video_postqueue(maxfile, filename):
    global VID_PST_QUE
    VID_PST_QUE = read_chunks(maxfile, 'VideoPostQueue', filename+'.VidPstQue.bin')


def get_point(floatval, default=0.0):
    uid = get_guid(floatval)
    if (uid == 0x2007):  # Bezier-Float
        fl = floatval.get_first(0x7127)
        if (fl):
            try:
                return fl.get_first(0x2501).data[0]
            except:
                print("SyntaxError: %s - assuming 0.0!\n" %(floatval))
        return default
    if (uid == 0x71F11549498702E7):  # Float Wire
        fl = get_references(floatval)[0]
        return get_point(fl)
    else:
        return default


def get_point_3d(chunk, default=0.0):
    floats = []
    if (chunk):
        refs = get_references(chunk)
        for fl in refs:
            flt = get_point(fl, default)
            if (fl is not None):
                floats.append(flt)
    return floats


def get_position(pos):
    position = None
    mtx = mathutils.Matrix.Identity(4)
    if (pos):
        uid = get_guid(pos)
        if (uid == 0xFFEE238A118F7E02):  # Position XYZ
            position = get_point_3d(pos)
        elif (uid == 0x0000000000442312):  # TCB Position
            position = pos.get_first(0x2503).data
        elif (uid == 0x0000000000002008):  # Bezier Position
            position = pos.get_first(0x2503).data
        if (position):
            mtx = mathutils.Matrix.Translation(position)
    return mtx


def get_rotation(pos):
    rotation = None
    mtx = mathutils.Matrix.Identity(4)
    if (pos):
        uid = get_guid(pos)
        if (uid == 0x2012):  # Euler XYZ
            rot = get_point_3d(pos)
            rotation = mathutils.Euler((rot[2], rot[1], rot[0])).to_quaternion()
        elif (uid == 0x0000000000442313):  # TCB Rotation
            rot = pos.get_first(0x2504).data
            rotation = mathutils.Quaternion((rot[0], rot[1], rot[2], rot[3]))
        elif (uid == 0x000000004B4B1003):  #'Rotation List
            refs = get_references(pos)
            if (len(refs) > 3):
                return get_rotation(refs[0])
        elif (uid == 0x3A90416731381913):  # Rotation Wire
            return get_rotation(get_references(pos)[0])
        if (rotation):
            mtx = mathutils.Matrix.Rotation(rotation.angle, 4, rotation.axis)
    return mtx


def get_scale(pos):
    mtx = mathutils.Matrix.Identity(4)
    if (pos):
        uid = get_guid(pos)
        if (uid == 0x2010):  # Bezier Scale
            scale = pos.get_first(0x2501)
            if (scale is None):
                scale = pos.get_first(0x2505)
            pos = scale.data
        elif (uid == 0x0000000000442315): # TCB Zoom
            scale = pos.get_first(0x2501)
            if (scale is None):
                scale = pos.get_first(0x2505)
            pos = scale.data
        elif (uid == 0xFEEE238B118F7C01):  # ScaleXYZ
            pos = get_point_3d(pos, 1.0)
        else:
            return mtx
        mtx = mathutils.Matrix.Diagonal(pos[:3]).to_4x4()
    return mtx


def create_matrix(prc):
    mtx = mathutils.Matrix.Identity(4)
    uid = get_guid(prc)
    scl = None
    rot = None
    pos = None
    if (uid == 0x2005):  # Position/Rotation/Scale
        pos = get_position(get_references(prc)[0])
        rot = get_rotation(get_references(prc)[1])
        scl = get_scale(get_references(prc)[2])
    elif (uid == 0x9154):  # BipSlave Control
        bipedSubAnim = get_references(prc)[2]
        refs = get_references(bipedSubAnim)
        scl = get_scale(get_references(refs[1])[0])
        rot = get_rotation(get_references(refs[2])[0])
        pos = get_position(get_references(refs[3])[0])
    if (pos is not None):
        mtx = pos @ mtx
    if (rot is not None):
        mtx = rot @ mtx
    if (scl is not None):
        mtx = scl @ mtx
    return mtx


def get_property(properties, idx):
    for child in properties.children:
        if (child.types == 0x100E):
            if (get_short(child.data, 0)[0] == idx):
                return child
    return None


def get_color(colors, idx):
    prop = get_property(colors, idx)
    if (prop is not None):
        col, offset = get_floats(prop.data, 15, 3)
        return (col[0], col[1], col[2])
    return None


def get_float(colors, idx):
    prop = get_property(colors, idx)
    if (prop is not None):
        fl, offset = get_float(prp.data, 15)
        return fl
    return None


def get_standard_material(refs):
    material = None
    try:
        if (len(refs) > 2):
            colors = refs[2]
            parameters = get_references(colors)[0]
            material = Material()
            material.set('ambient',  get_color(parameters, 0x00))
            material.set('diffuse',  get_color(parameters, 0x01))
            material.set('specular', get_color(parameters, 0x02))
            material.set('emissive', get_color(parameters, 0x08))
            material.set('shinines', get_float(parameters, 0x0A))
            transparency = refs[4]  # ParameterBlock2
            material.set('transparency', get_float(transparency, 0x02))
    except:
        print('Mat\n')
    return material


def get_vray_material(vry):
    material = Material()
    try:
        material.set('diffuse',  get_color(vry, 0x01))
        material.set('ambient',  get_color(vry, 0x02))
        material.set('specular', get_color(vry, 0x05))
        material.set('emissive', get_color(vry, 0x05))
        material.set('shinines', get_float(vry, 0x0B))
        material.set('transparency', get_float(vry, 0x02))
    except:
        print('VRay\n')
    return material


def get_arch_material(ad):
    material = Material()
    try:
        material.set('diffuse',  get_color(ad, 0x1A))
        material.set('ambient',  get_color(ad, 0x02))
        material.set('specular', get_color(ad, 0x05))
        material.set('emissive', get_color(ad, 0x05))
        material.set('shinines', get_float(ad, 0x0B))
        material.set('transparency', get_float(ad, 0x02))
    except:
        print('Arch\n')
    return material


def adjust_material(obj, mat):
    material = None
    if (mat is not None):
        uid = get_guid(mat)
        if (uid == 0x0002):  # Standard
            refs = get_references(mat)
            material = get_standard_material(refs)
        elif (uid == 0x0000000000000200):  # Multi/Sub-Object
            refs = get_references(mat)
            material = adjust_material(obj, refs[-1])
        elif (uid == 0x7034695C37BF3F2F):  # VRayMtl
            refs = get_reference(mat)
            material = get_vray_material(refs[1])
        elif (uid == 0x4A16365470B05735):  # Arch
            refs = get_references(mat)
            material = get_arch_material(refs[0])
        if (obj is not None) and (material is not None):
            objMaterial = bpy.data.materials.new(get_class_name(mat))
            obj.data.materials.append(objMaterial)
            objMaterial.diffuse_color[:3] = material.get('diffuse', (0.8,0.8,0.8))
            objMaterial.specular_color[:3] = material.get('specular', (0,0,0))
            objMaterial.roughness = material.get('shinines', 0.2)


def create_shape(context, pts, indices, node, key, prc, mat):
    name = node.get_first(TYP_NAME).data
    shape = bpy.data.meshes.new(name)
    if (key is not None):
        name = "%s_%d" %(name, key)
    mtx = create_matrix(prc)
    data = []
    if (pts):
        shape.vertices.add(len(pts) // 3)
        shape.vertices.foreach_set("co", pts)
        nbr_faces = len(indices)
        shape.polygons.add(nbr_faces)
        shape.loops.add(nbr_faces * 3)
        for vtx in indices:
            data.extend(vtx)
        shape.polygons.foreach_set("loop_start", range(0, nbr_faces * 3, 3))
        shape.loops.foreach_set("vertex_index", data)

    if (len(data) > 0):
        shape.validate()
        shape.update()
        obj = bpy.data.objects.new(name, shape)
        context.view_layer.active_layer_collection.collection.objects.link(obj)
        adjust_material(obj, mat)
        return True
    return True


def calc_point(data):
    points = []
    long, offset = get_long(data, 0)
    while (offset < len(data)):
        val, offset = get_long(data, offset)
        flt, offset = get_floats(data, offset, 3)
        points.extend(flt)
    return points


def calc_point_float(data):
    points = []
    long, offset = get_long(data, 0)
    while (offset < len(data)):
        flt, offset = get_floats(data, offset, 3)
        points.extend(flt)
    return points


def get_poly_4p(points):
    vertex = {}
    for point in points:
        ngon = point.points
        key = point.fH
        if (key not in vertex):
            vertex[key] = []
        vertex[key].append(ngon)
    return vertex


def get_poly_5p(data):
    count, offset = get_long(data, 0)
    ngons = []
    while count > 0:
        pt, offset = get_longs(data, offset, 3)
        offset += 8
        ngons.append(pt)
        count -= 1
    return ngons


def get_poly_6p(data):
    count, offset = get_long(data, 0)
    polylist = []
    while (offset < len(data)):
        long, offset = get_longs(data, offset, 6)
        i = 5
        while ((i > 3) and (long[i] < 0)):
            i -= 1
            if (i > 2):
                polylist.append(long[1:i])
    return polylist


def get_poly_ngon(polys):
    vertex = []
    offset = 0
    while (offset < len(polys)):
        num = polys[offset]
        offset += 1
        ngon = []
        keys = 0
        while (keys < num):
            pt = points[polys[offset]][1]
            ngon.append(pt)
            offset += 1
            keys += 1
            vertex.extend(ngon)
    return vertex


def get_poly_data(chunk):
    offset = 0
    polylist = []
    data = chunk.data
    while (offset < len(data)):
        count, offset = get_long(data, offset)
        points, offset = get_longs(data, offset, count)
        polylist.append(points)
    return polylist


def calc_point_3d(chunk):
    data = chunk.data
    cnt, offset = get_long(data, 0)
    pointlist = []
    try:
        while (offset < len(data)):
            pt = Point3d()
            long, offset = get_long(data, offset)
            pt.points, offset = get_longs(data, offset, long)
            pt.flags, offset = get_short(data, offset)
            if ((pt.flags & 0x01) != 0):
                pt.f1, offset = get_long(data, offset)
            if ((pt.flags & 0x08) != 0):
                pt.fH, offset = get_short(data, offset)
            if ((pt.flags & 0x10) != 0):
                pt.f2, offset = get_long(data, offset)
            if ((pt.flags & 0x20) != 0):
                pt.fA, offset = get_longs(data, offset, 2 * (long - 3))
            if (len(pt.points) > 0):
                pointlist.append(pt)
    except Exception as exc:
        print('Error:\n')
        print("%s: o = %d\n" %(exc, offset))
        raise exc
    return pointlist


def create_editable_poly(context, node, msh, mat, mtx):
    name = node.get_first(TYP_NAME).data
    poly = msh.get_first(0x08FE)
    indexList = []
    coordListI = []
    indicesList = []
    point3i = None
    point4i = None
    point6i = None
    pointNi = None
    coords = None
    created = False
    if (poly):
        for child in poly.children:
            if (child.types == 0x0100):
                coords = calc_point(child.data)
            elif (child.types == 0x0108):
                point6i = child.data
            elif (child.types == 0x011A):
                point4i = calc_point_3d(child)
            elif (child.types == 0x0310):
                pointNi = child.data
        if (point4i is not None):
            vertex = get_poly_4p(point4i)
            if (len(vertex) > 0):
                for key, ngons in vertex.items():
                    created |= create_shape(context, coords, ngons, node, key, mtx, mat)
            else:
                created = True
        elif (point6i is not None):
            ngons = get_poly_6p(point6i)
            created = create_shape(context, coords, ngons, node, None, mtx, mat)
        elif (pointNi is not None):
            ngons = get_poly_ngon(pointNi)
            created = create_shape(context, coords, ngons, node, None, mtx, mat)
    return created


def get_point_array(values):
    verts = []
    if len(values) >= 4:
        count, offset = get_long(values, 0)
        while (count > 0):
            floats, offset = get_floats(values, offset, 3)
            verts.extend(floats)
            count -= 1
    return verts


def create_editable_mesh(context, node, msh, mat, mtx):
    name = node.get_first(TYP_NAME).data
    poly = msh.get_first(0x08FE)
    created = False
    if (poly):
        vertexChunk = poly.get_first(0x0914)
        ClassIDChunk = poly.get_first(0x0912)
        coords = get_point_array(vertexChunk.data)
        ngons = get_poly_5p(ClassIDChunk.data)
        created = create_shape(context, coords, ngons, node, None, mtx, mat)
    return created


def get_matrix_mesh_material(node):
    refs = get_reference(node)
    if (refs):
        mtx = refs.get(0, None)
        msh = refs.get(1, None)
        mat = refs.get(3, None)
        lyr = refs.get(6, None)
    else:
        refs = get_references(node)
        mtx = refs[0]
        msh = refs[1]
        mat = refs[3]
        lyr = None
        if (len(refs) > 6):
            lyr = refs[6]
    return mtx, msh, mat, lyr


def adjust_matrix(obj, node):
    mtx = create_matrix(node).flatten()
    plc = mathutils.Matrix(*mtx)
    obj.Placement = plc
    return plc


def create_boolean(context, node, pro, mat, mtx):
    name = node.get_first(TYP_NAME).data
    pBlocks = get_references(pro)
    return True


def create_skipable(context, node, msh, mat, mtx, skip):
    name = node.get_first(TYP_NAME).data
    print("    skipping %s '%s'... " %(skip, name))
    return True


def create_mesh(context, node, msh, mtx, mat):
    created = False
    uid = get_guid(msh)
    msh.geometry = None
    if (uid == 0x0E44F10B3):
        created = create_editable_mesh(context, node, msh, mat, mtx)
    elif (uid == 0x192F60981BF8338D):
        created = create_editable_poly(context, node, msh, mat, mtx)
    else:
        skip = SKIPPABLE.get(uid)
        if (skip is not None):
            created = create_skipable(context, node, msh, mat, mtx, skip)
    return created, uid


def create_object(context, node):
    parent = get_node_parent(node)
    node.parent = parent
    name = get_node_name(node)
    mtx, msh, mat, lyr = get_matrix_mesh_material(node)
    while ((parent is not None) and (get_guid(parent) != 0x0002)):
        name = "%s/%s" %(get_node_name(parent), name)
        parent_mtx = parent.matrix
        if (parent_mtx):
            mtx = mtx.dot(parent_mtx)
        parent = get_node_parent(parent)
    created, uid = create_mesh(context, node, msh, mtx, mat)


def make_scene(context, parent, level=0):
    for chunk in parent.children:
        if (isinstance(chunk, SceneChunk)):
            if ((get_guid(chunk) == 0x0001) and (get_super_id(chunk) == 0x0001)):
                try:
                    create_object(context, chunk)
                except Exception as exc:
                    print('SceneError:', exc, chunk)


def read_scene(context, maxfile, filename):
    global SCENE_LIST
    SCENE_LIST = read_chunks(maxfile, 'Scene', filename+'.Scn.bin', containerReader=SceneChunk)
    make_scene(context, SCENE_LIST[0], 0)


def read(context, filename):
    if (is_maxfile(filename)):
        maxfile = ImportMaxFile(filename)
        prop = maxfile.getproperties('\x05DocumentSummaryInformation', convert_time=True, no_conversion=[10])
        prop = maxfile.getproperties('\x05SummaryInformation', convert_time=True, no_conversion=[10])
        read_class_data(maxfile, filename)
        read_config(maxfile, filename)
        read_directory(maxfile, filename)
        read_class_directory(maxfile, filename)
        read_video_postqueue(maxfile, filename)
        read_scene(context, maxfile, filename)
    else:
        print("File seems to be no 3D Studio Max file!")


def load(operator, context, filepath="", global_matrix=None):
    read(context, filepath)

    return {'FINISHED'}