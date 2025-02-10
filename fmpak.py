#!/usr/bin/env python3

"""
		FM Packer for The Dark Mod

	Quick Usage Reference:
		- create a .pkignore file in your FM folder, specifying what to exclude
		- run 'python fmpak.py .' from inside your FM folder
"""

import sys
import os
import time
import zipfile as zipf
import argparse as ap
from enum import Enum


echo = print  # just to differentiate from debug prints


VERSION = "0.6"
PKIGNORE_FILENAME = ".pkignore"
MODFILE_FILENAME = "darkmod.txt"

VALID_MODEL_FORMATS = ["ase", "lwo", "obj"]  # TODO: is obj ever used?

INVALID_CHARS = [' ',
	'(', ')', '{', '}', '[', ']', '|', '!', '@', '#', '$', '%', '^', '&',
	'*', ',', '+', '-', '"', '\'', ':', ';', '?', '<', '>', '`', '~', '/'
]

VALID_UNUSED_MATERIALS = [
	"guis/assets/purchase_menu/map_of"
]

# make sure to exclude any meta stuff
ignored_folders = set(["savegames", "__pycache__", ".git"])
ignored_files = set([
	PKIGNORE_FILENAME, ".lin", "bak", ".log", ".dat", ".py", ".pyc",
	".pk4", ".zip", ".7z", ".rar", ".gitignore", ".gitattributes"
])

REPORT_HEADER = "\n\n  Some {} were not found in the maps\n"  # .format(name)
REPORT_HEADER_NONL = "\n\n  Some {} were not found in the maps"  # .format(name)
REPORT_OBJECT = "      {}"    # .format(object)
REPORT_COUNT  = "\n  {} {}\n"   # .format(amount, name)
REPORT_OK     = "  All Ok"


class FileGroup:
	def __init__(self, files, dir_count, file_count):
		self.files      = files
		self.dir_count  = dir_count
		self.file_count = file_count

class mission: # data class to avoid using 'global'
	path    = ""
	name    = ""
	included : FileGroup
	excluded : FileGroup
	map_names = []

class MissionFile:
	def __init__(self, fullpath, relpath):
		self.fullpath = fullpath
		self.relpath = relpath



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		utils
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def error(message):
	echo(f"\nERROR: {message}\n")
	exit()

def warning(message):
	echo(f"\nWARNING: {message}\n")

def task(msg):
	echo(msg, end="")


def parse_path(dir):
	path = dir

	if   path.startswith("/"):   path = path[1:]
	elif path.startswith("\\"):  path = path[1:]
	elif path.startswith("./"):  path = path[2:]
	elif path.startswith(".\\"): path = path[2:]

	if dir == '.':
		path = os.getcwd()
	elif not os.path.isabs(path):
		path = os.path.join(os.getcwd(), path)

	return path


def set_fm_path(path):
	mission.path = parse_path(path)
	mission.name = os.path.basename(mission.path)


def validate_fm_path():
	if not os.path.isdir(mission.path):
		error(f"invalid path '{mission.path}'")

	if not os.path.isfile(os.path.join(mission.path, MODFILE_FILENAME)):
		error(f"no '{MODFILE_FILENAME}' found at path '{mission.path}'")

	is_upper = any(char.isupper() for char in mission.name)
	if is_upper:
		warning(f"mission directory name contains upppercase characters")


def get_files_in_dir(dir_path:str, inclusive_filters:list=[]):
	files = list()

	for name in os.listdir(dir_path):
		filepath = os.path.join(dir_path, name)#.encode("utf-8")
		if not os.path.isfile(filepath): continue

		for filter in inclusive_filters:
			if filter in name:
				files.append(filepath)
				break

	return files


def should_ignore(path, filters):
	for string in filters:
		if string in path:
			return True
	return False


def get_mapsequence_filenames():
	map_names = list()

	startmap = os.path.join(mission.path, "startingmap.txt")
	if os.path.isfile(startmap):
		with open(startmap, 'r') as file:
			map_names = [ file.readlines()[0].strip() ]
		return map_names

	mapseq = os.path.join(mission.path, "tdm_mapsequence.txt")
	if os.path.isfile(mapseq):
		with open(mapseq, 'r') as file:
			for line in file:
				line = "".join(line.split())
				if line == "": continue
				map_names.append(line.strip()[ line.index(':')+1 :])
		return map_names


def load_pkignore():
	file_path = os.path.join(mission.path, PKIGNORE_FILENAME)

	if not os.path.exists(file_path):
		return

	with open(file_path, 'r') as f:
		for line in f:
			if '#' in line: line = line[:line.index('#')]
			line = line.strip()
			if line == "": continue

			if   line.startswith('/'):  ignored_folders.add(line[1:])
			elif line.startswith('./'): ignored_folders.add(line[2:])
			elif line.endswith('/'):    ignored_folders.add(line[:-1])
			else:
				ignored_files.add(line)


def add_ignored_maps():
	mission.map_names = get_mapsequence_filenames()

	maps_dir = os.path.join(mission.path, "maps")
	for root, dirs, files in os.walk(maps_dir):
		invalid_dir = root != maps_dir
		for f in files:
			if invalid_dir:
				ignored_files.add(f)
				continue

			for name in mission.map_names:
				if not f.startswith(name + '.' ):
					ignored_files.add(f)


def gather_files():
	inc, exc = [], []
	num_inc_dirs, num_inc_files = -1, 0
	num_exc_dirs, num_exc_files = -1, 0

	add_ignored_maps()

	for root, dirs, files in os.walk(mission.path):
		included_folder = False
		if should_ignore(root, ignored_folders):
			num_exc_dirs += 1
		else:
			included_folder = True
			num_inc_dirs += 1

		for file in files:
			fullpath = os.path.join(root, file)
			relpath = fullpath.replace(mission.path, '')[1:]
			if included_folder and not should_ignore(relpath, ignored_files):
				inc.append( MissionFile(fullpath, relpath) )
				num_inc_files += 1
			else:
				exc.append( MissionFile(fullpath, relpath) )
				num_exc_files += 1

	mission.included = FileGroup(inc, num_inc_dirs, num_inc_files)
	mission.excluded = FileGroup(exc, num_exc_dirs, num_exc_files)

	# print("\nincluded files")
	# for f in inc:
	# 	print("    ", f)

	# print("\nexcluded files")
	# for f in exc:
	# 	print("        ", f)

	# print(f"\n       included {num_inc_dirs} dirs, {num_inc_files} files  | {len(inc)}" )
	# print(f"\n       excluded {num_exc_dirs} dirs, {num_exc_files} files  | {len(exc)}" )
	# print(f"\n       total {num_inc_dirs+num_exc_dirs} dirs, {num_inc_files+num_exc_files} files  | {len(inc)+len(exc)}" )



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
#       TASK FUNCTIONS
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def print_quick_help():
	echo(f"""
	Usage:
		{os.path.basename(__file__)} <path> <options>

	Use '{os.path.basename(__file__)} -h' for more information.
	""")


def pack_fm():
	zipname = mission.name + ".pk4"

	echo(f"\nPacking '{zipname}'... \n")
	t1 = time.time()

	with zipf.ZipFile(zipname, 'w', zipf.ZIP_DEFLATED, compresslevel=9) as f:
		for file in mission.included.files:
			echo("    ", file.relpath)
			f.write(file.relpath)

	t2 = time.time()
	total_time = "{:.1f}".format(t2-t1)

	echo(f"\nFinished packing '{zipname}'")
	echo(f"    {mission.included.dir_count} dirs, {mission.included.file_count} files, {total_time} seconds")


def check_files(arg, file_group, header):
	abspath = parse_path(arg)
	relpath = abspath.replace(mission.path, '')[1:]
	is_root = arg in ['.', mission.path]

	if is_root: echo(f"\n{header}\n")
	else:       echo(f"\n{header} in '{os.path.join(mission.name, relpath)}'\n")

	num_files = 0
	for f in file_group.files:
		if abspath in f.fullpath:
			num_files += 1
			echo(f"    {f.fullpath.replace(abspath , '')[1:]}")

	if is_root: echo(f"\n       {file_group.file_count} files")
	else:       echo(f"\n       {num_files}/{file_group.file_count} files")


def get_pkignore_csv():
	file_path = os.path.join(mission.path, PKIGNORE_FILENAME)
	if not os.path.exists(file_path):
		return ""

	res = ""
	i = 0
	with open(file_path, 'r') as f:
		for line in f:
			if '#' in line: line = line[:line.index('#')]
			line = line.strip()
			if line == "": continue

			if i > 0: res += ', ' + line
			else:     res += line
			i += 1

	return res


def create_pk_ignore(csv):
	if ',' in csv:
		vals = csv.replace(' ', '').split(',')
	else:
		vals = csv.split()

	content = '\n'.join(vals)

	file_path = os.path.join(mission.path, PKIGNORE_FILENAME)
	with open(file_path, 'w') as f:
		f.write(content)


def validate_filepaths():
	invalid_filespaths = []

	task("Checking filepaths...")

	name_report = ""
	mission_name_has_uppercase = any(char.isupper() for char in mission.name)
	if mission_name_has_uppercase:
		name_report = f"      mission name '{mission.name}' contains uppercase letters"

	for c in INVALID_CHARS:
		if c in mission.name:
			if name_report != "": name_report += " and spaces or special symbols"
			else:                 name_report = f"      mission name '{mission.name}' contanins spaces or special symbols"
			break

	for f in mission.included.files:
		for c in INVALID_CHARS:
			if c in f.relpath:
				invalid_filespaths.append(f.relpath)
				break

	if name_report != "" or len(invalid_filespaths) > 0:
		num_inv_paths = len(invalid_filespaths)
		echo("\n\n  Some paths contain spaces or special symbols\n")

		if name_report != "":
			num_inv_paths += 1
			echo(name_report + "\n")

		for inv_path in invalid_filespaths:
			echo( REPORT_OBJECT.format(inv_path) )

		echo(f"\n  {num_inv_paths} invalid paths." + "\n  Avoid using any of:" + " ".join(INVALID_CHARS)[1:])
	else:
		echo(REPORT_OK)


def get_all_properties_named(prop):
	props = []
	for map in map_parser.maps:
		for ent in map.entities:
			if prop in ent.properties:
				props.append({
					"name"  : prop,
					"value" : ent.properties[prop]
				})
	return props


def parse_maps():
	echo("Parsing maps")
	for map in mission.map_names:
		filepath = os.path.join(mission.path, "maps", map + ".map")
		map_parser.parse(filepath)


def validate_models():
	prop_vals = [ p["value"] for p in get_all_properties_named("model") ]
	model_files = [ f.relpath.replace('\\', '/') for f in mission.included.files if "models" in f.fullpath]

	task("Checking models... ")

	unused = []
	for f in model_files:
		if not f in prop_vals:
			unused.append(f)

	if len(unused) > 0:
		echo( REPORT_HEADER.format("models") )
		# echo("\n  (This may not mean they're unused)\n")
		for o in unused:
			echo( REPORT_OBJECT.format(o) )
		echo( REPORT_COUNT.format(len(unused), "models"))
	else:
		echo(REPORT_OK)


def parse_materials():
	mat_files = get_files_in_dir(os.path.join(mission.path, "materials"), [".mtr"])
	materials_defs = []
	for mf in mat_files:
		scope_level = 0
		with open(mf, 'r') as file:
			for line in file:
				line = line.replace('\n', '').replace('\t', '')
				if line == "": continue

				line_start = line[0]

				if   line_start == '{': scope_level += 1
				elif line_start == '}': scope_level -= 1
				elif line_start == '/': continue
				elif scope_level == 0:  materials_defs.append(line)

	return materials_defs


def is_material_in_maps(mat):
	for map in map_parser.maps:
		for e in map.entities:
			if mat in e.materials:
				return True
	return False


def validate_materials():
	mats = parse_materials()
	unused = []
	task("Checking materials... ")

	if len(unused) == 0:
		echo(" no custom materials found.")
		return

	for m in mats:
		if  not is_material_in_maps(m) \
		and not m in VALID_UNUSED_MATERIALS:
			unused.append(m)

	if len(unused) > 0:
		echo( REPORT_HEADER_NONL.format("materials") )
		echo("  (This may not mean they're unused)\n")
		for o in unused:
			echo( REPORT_OBJECT.format(o) )
		echo( REPORT_COUNT.format(len(unused), "materials"))
	else:
		echo(REPORT_OK)

def parse_skins():
	skin_files = get_files_in_dir(os.path.join(mission.path, "skins"), [".skin"])
	skin_defs = {}
	for path in skin_files:
		scope_level = 0
		skin_defs[path] = []
		with open(path, 'r') as file:
			for line in file:
				line = line.replace('\n', '').replace('\t', '')
				if line == "": continue

				line_start = line[0]

				if   line_start == '{': scope_level += 1
				elif line_start == '}': scope_level -= 1
				elif line_start == '/': continue
				elif scope_level == 0:
					if   line.startswith("skin "):  line = line.replace("skin ", '')
					elif line.startswith("skin\t"): line = line.replace("skin\t", '')
					skin_defs[path].append(line)
	return skin_defs


def is_skin_in_maps(skin_def):
	for map in map_parser.maps:
		for e in map.entities:
			if not "skin" in e.properties: continue
			if e.properties["skin"] == skin_def:
				return True
	return False


def validate_skins():
	# Don't report unused individual skins, report files with no skins used
	# (a file may bundle skins that are not all in use)
	skins_dic = parse_skins()
	unused_files = []
	task("Checking skin files... ")

	if len(skins_dic) == 0:
		echo(" no custom skins found.")
		return

	for filepath in skins_dic:
		skins_list = skins_dic[filepath]
		num_unused = 0
		for skin in skins_list:
		 	if not is_skin_in_maps(skin):
		 		num_unused += 1
		if num_unused == len(skins_list):
		 	unused_files.append(filepath.replace(mission.path, '')[1:])

	if len(unused_files) > 0:
		echo("\n\n  Some skin files have no skins found in the maps\n")
		for f in unused_files:
			echo( REPORT_OBJECT.format(f) )
		echo( REPORT_COUNT.format(len(unused_files), "skin files"))
	else:
		echo(REPORT_OK)


def validate_mission_files(arg):
	if arg == "paths":
		validate_filepaths()
	else:
		parse_maps()

		if   arg == "all":
			validate_filepaths()
			validate_models()
			validate_materials()
		elif arg == "models":
			validate_models()
		elif arg == "materials":
			validate_materials()
		elif arg == "skins":
			validate_skins()
		# elif arg == "files":     pass
		# elif arg == "sounds":    pass
		# elif arg == "guis":      pass
		# elif arg == "scripts":   pass
		# elif arg == "dds":       pass
		# elif arg == "particles": pass


def get_entity_named(name):
	for map in map_parser.maps:
		for e in map.entities:
			if e.name == name:
				return e
	return None


def get_entities_of_class(classname):
	ents = []
	for map in map_parser.maps:
		for e in map.entities:
			if e.classname == classname:
				ents.append(e)
	return ents


def get_entities_wildcard(attr, name):
	ents = []
	start = name.startswith('*')
	end   = name.endswith('*')

	if start and end:
		name = name.replace('*', '')
		for map in map_parser.maps:
			for e in map.entities:
				if name in getattr(e, attr):
					ents.append(e)
	elif start:
		name = name.replace('*', '')
		for map in map_parser.maps:
			for e in map.entities:
				ent_attr = getattr(e, attr)
				if ent_attr.endswith(name):
					ents.append(e)
	elif end:
		name = name.replace('*', '')
		for map in map_parser.maps:
			for e in map.entities:
				ent_attr = getattr(e, attr)
				if ent_attr.startswith(name):
					ents.append(e)
	else:
		substrs = name.split('*', maxsplit=1)
		for map in map_parser.maps:
			for e in map.entities:
				ent_attr = getattr(e, attr)
				if ent_attr.startswith(substrs[0]) and ent_attr.endswith(substrs[1]):
					ents.append(e)
	return ents


def get_entities_by(attr, name):
	if not '*' in name:
		if attr == "name":
			e = get_entity_named(name)
			if not e:
				return []
			return [e]
		else:
			return get_entities_of_class(name)
	else:
		return get_entities_wildcard(attr, name)


def check_entity_properties_by(attr, check_args):
	parse_maps()

	args = check_args.replace(', ', ',').split(',')
	attr_name = args[0]
	props = [ args[i].split(' ') for i in range(1, len(args)) ] # args[1:]

	task(f"Checking properties from '{attr_name}' entities... ")

	ents = get_entities_by(attr, attr_name)

	if len(ents) == 0:
		echo(f"\n\n  No entities found with {attr} '{attr_name}'")
	else:
		inv_ents = check_entities_properties(ents, props)

		if len(inv_ents) > 0:
			echo(f"\n\n    Entities differ:")
			if attr == "classname":
				for e in inv_ents:
					echo(f"        '{e.classname}'{' ' * (30-len(e.classname))} ({e.name})")
			else:
				for e in inv_ents:
					echo(f"        '{e.name}'{' ' * (30-len(e.name))} ({e.classname})")
			echo(f"\n\n  {len(inv_ents)} entities differ\n")
		else:
			echo(f"  All OK")

# f"{sub1:<{gap}} | {sub2:> {gap}}"

def check_entities_properties(ents, props):
	invalid_entities = []
	for e in ents:
		for p in props:
			pname, pval = p[0], p[1]
			if not pname in e.properties \
			or pval != e.properties[pname]:
				invalid_entities.append(e)

	return invalid_entities



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		MAP PARSER
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=

debug_show_scopes = 0
debug_print_props = 0

class Scope(Enum):
	File          = "Scope.File"
	Entity        = "Scope.Entity"
	Property      = "Scope.Property"
	Def           = "Scope.Def"
	BrushDef     = "Scope.BrushDef"
	PatchDef     = "Scope.PatchDef"

class Entity:
	def __init__(self):
		self.classname = ""
		self.name      = ""
		self.properties = {}
		self.brushes = []
		self.patches = []
		self.materials = set()

class Property:
	def __init__(self, name, value):
		self.name = name
		self.value = value

class Brush:
	def __init__(self):
		self.materials = set()

class Patch:
	def __init__(self):
		self.material = ""

class MapData:
	def __init__(self):
		self.entities = []

class MapParser:
	def __init__(self):
		self.scope      = Scope.File
		self.prop       = None
		self.curr_ent   = None
		self.curr_brush = None
		self.curr_patch = None
		self.maps = []
		self.curr_map = None

	def set_scope(self, scope):
		if debug_show_scopes: print(">", scope)
		self.scope = scope

	def is_scope(self, sc):
		return self.scope == sc

	# debug
	# def print_scope(self, name, token):
	# 	if not debug_show_scopes: return
	# 	print("    ", name, token)

	# # debug
	# def print_prop(self, name, value):
	# 	if not debug_print_props: return
	# 	print("       ", name, value)

	def parse_token(self, token):
		if self.scope == Scope.Entity:
			# self.print_scope("Scope.Entity", token)

			if token.startswith('"'):
				self.prop = token[1:-1]
				self.set_scope(Scope.Property)
			elif token == '{':
				self.set_scope(Scope.Def)
			elif token == '}':
				self.curr_map.entities.append(self.curr_ent)
				self.curr_ent = None
				# self.print_prop("----------------------", "")
				self.set_scope(Scope.File)

		elif self.scope == Scope.Def:
			# self.print_scope("Scope.Def", token)

				self.curr_brush = Brush()
				self.set_scope(Scope.BrushDef3)
				self.curr_patch = Patch()
				self.set_scope(Scope.PatchDef3)
			if   token.startswith("brushDef"):
			elif token.startswith("patchDef"):
			elif token == '}':
				self.set_scope(Scope.Entity)

		elif self.scope == Scope.Property:
			# self.print_scope("Scope.Property", token)

			if token.startswith('"'):
				val = token[1:-1]
				if   self.prop == "classname": self.curr_ent.classname = val
				elif self.prop == "name":      self.curr_ent.name = val

				# self.print_prop(self.prop, val)
				self.curr_ent.properties[self.prop] = val
				self.prop = None
				self.set_scope(Scope.Entity)

		elif self.scope == Scope.BrushDef:
			if token.startswith('"'):
				# self.print_prop("brush texture: ", token)
				mat = token[1:-1]
				self.curr_brush.materials.add(mat)
				self.curr_ent.materials.add(mat)
			elif token == '}':
				self.curr_ent.brushes.append(self.curr_brush)
				self.curr_brush = None
				self.set_scope(Scope.Def)

		elif self.scope == Scope.PatchDef:
			if token.startswith('"'):
				# self.print_prop("patch texture: ", token)
				mat = token[1:-1]
				self.curr_patch.material = mat
				self.curr_ent.materials.add(mat)
			elif token == '}':
				self.curr_ent.patches.append(self.curr_patch)
				self.curr_patch = None
				self.set_scope(Scope.Def)

		elif self.scope == Scope.File:   # this branch is the most infrequent, keep it last
			# self.print_scope("Scope.File", token)

			if token == '{':
				self.curr_ent = Entity()
				self.set_scope(Scope.Entity)


	def parse(self, map_file):
		self.curr_map = MapData()
		self.maps.append(self.curr_map)

		task(f"    '{os.path.basename(map_file)}'...")

		t1 = time.time()
		with open(map_file, 'r') as file:

			for line in file:
				line = line.replace('\n', '')
				# line = line.replace('\t', '')

				line_start = line[0]

				if line_start == '(':
					assert self.scope in [Scope.PatchDef, Scope.BrushDef], line
					# when it's brush or patch, skip the faces
					if "textures" in line:  # brush
						q1 = line.find('"')
						q2 = line.rfind('"')
						tokens = [ line[q1:q2+1] ]
					else:                   # patch
						continue
				elif line_start == '"':
					assert self.scope in [Scope.Entity, Scope.PatchDef], line
					q2 = line.find('"', 1) +1
					tokens = [ line[:q2], line[q2+1:] ]
				elif line_start != '/':
					tokens = [line]
				else:  # comments
					continue

				for t in tokens:
					self.parse_token(t)

		t2 = time.time()
		total_time = "{:.1f}".format(t2-t1)
		echo(f" ({total_time} secs)\n")

		assert(self.scope      == Scope.File)
		assert(self.prop       == None)
		assert(self.curr_ent   == None)
		assert(self.curr_brush == None)
		assert(self.curr_patch == None)



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		run
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# keep this check here in case this script may be called from another tool
if __name__ == "__main__":
	map_parser = MapParser()

	parser = ap.ArgumentParser()

	# parser.usage = "" # TODO maybe

	parser.add_argument("--version",           action="version",    version=f"FM Packer v{VERSION} for The Dark Mod")
	parser.add_argument("-qh", "--quick_help", action="store_true", help="show a shortened help message")

	parser.add_argument("path",    type=str, const=None, nargs='?', help="the path (relative or absolute) to the target fm")
	parser.add_argument("--pkset", type=str, metavar="[csv/ssv]",   help="creates a .pkignore file with the given comma- or space-separated filter values")
	parser.add_argument("--pkget", action="store_true",             help="shows the .pkignore content as csv filters")

	parser.add_argument("-i", "--included", type=str, const='.', nargs='?', metavar="path", help="list files to include in pk4 within 'path' without packing them, where 'path' is a relative path (if ommitted, the mission path is used)")
	parser.add_argument("-e", "--excluded", type=str, const='.', nargs='?', metavar="path", help="list files to exclude from pk4 within 'path' without packing them, where 'path' is a relative path (if ommitted, the mission path is used)")

	parser.add_argument("--validate", type=str, choices=["all", "paths", "models", "materials", "skins"], help="validate the mission")
	parser.add_argument("-cn", "--check_named", metavar="[n, p v, ...]", type=str, help="check if properties [p] exist in entity named [n] with values [v]. E.g. -cn \"master_key, nodrop 1, inv_droppable 1\"")
	parser.add_argument("-cc", "--check_class", metavar="[c, p v, ...]", type=str, help="check if properties [p] exist in entities of classname [n] with values [v]. E.g. -cn \"atdm:key*, nodrop 1, inv_droppable 1\"")

	args = parser.parse_args()

	if args.quick_help:
		print_quick_help()
		exit()

	echo() # leave an empty line between the last prompt

	if args.pkset:
		echo("Previous .pkignore:\n\t", get_pkignore_csv())
		create_pk_ignore(args.pkset)
		echo("\nNew .pkignore:\n\t", get_pkignore_csv())
		exit()

	if args.pkget:
		echo(".pkignore:\n\t", get_pkignore_csv())
		exit()

	if not args.path:
		error("a path must be provided")

	set_fm_path(args.path)
	validate_fm_path()
	load_pkignore()
	gather_files()

	if args.validate:
		validate_mission_files(args.validate)
		exit()

	if args.check_named:
		check_entity_properties_by("name", args.check_named)
		exit()

	if args.check_class:
		check_entity_properties_by("classname", args.check_class)
		exit()

	if   args.included: check_files(args.included, mission.included, "Included files")
	elif args.excluded: check_files(args.excluded, mission.excluded, "Excluded files")
	else:               pack_fm()


