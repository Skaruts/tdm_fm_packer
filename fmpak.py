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
from fnmatch import fnmatch

echo = print  # just to differentiate from debug prints


VERSION = "0.7.2"

VALID_MODEL_FORMATS = ["*.ase", "*.lwo", "*.obj"]  # TODO: is obj ever used?

INVALID_CHARS = [' ',
	'(', ')', '{', '}', '[', ']', '|', '!', '@', '#', '$', '%', '^', '&',
	'*', ',', '+', '-', '"', '\'', ':', ';', '?', '<', '>', '`', '~', '/'
]

VALID_UNUSED_MATERIALS = [
	"guis/assets/purchase_menu/map_of"
]

VALID_UNUSED_XDATA_FILES = [
	"xdata/briefing.xd"
]

REPORT_HEADER = "\n\n  Some {} were not found in the maps\n"  # .format(name)
REPORT_FILE   = "    > in file: {}"    # .format(file)
REPORT_OBJECT = "        {}"    # .format(object)
REPORT_COUNT  = "\n  {} {}\n"   # .format(amount, name)
REPORT_OK     = "all Ok"

PKIGNORE_FILENAME    = ".pkignore"
MODFILE_FILENAME     = "darkmod.txt"
README_FILENAME      = "readme.txt"
STARTMAP_FILENAME    = "startingmap.txt"
MAPSEQUENCE_FILENAME = "tdm_mapsequence.txt"
BRIEFING_FILENAME    = "xdata/briefing.xd"

# make sure to exclude any meta stuff
ignored_folders = set(["savegames", "__pycache__", ".git"])
ignored_files = set([
	PKIGNORE_FILENAME, ".lin", "bak", ".log", ".dat", ".py", ".pyc",
	".pk4", ".zip", ".7z", ".rar", ".gitignore", ".gitattributes"
])


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
	warning_count = 0

class MissionFile:
	def __init__(self, fullpath, relpath):
		self.fullpath = fullpath
		self.relpath = relpath



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		utils
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def error(message):
	echo(f"\n\nERROR: {message}\n")
	exit()

def warning(message):
	mission.warning_count += 1
	echo(f"WARNING: {message}")

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


def get_files_in_dir(dir_path:str, filters=[]):
	if not os.path.exists(dir_path): return []
	dir_files = list()
	for filename in os.listdir(dir_path):
		fullpath = os.path.join(dir_path, filename)#.encode("utf-8")
		if not os.path.isfile(fullpath): continue
		if not filters:
			dir_files.append(fullpath)
		else:
			for p in filters:
				if fnmatch(filename, p):
					dir_files.append(fullpath)
					break
	return dir_files


def get_files_in_dir_recursive(dir_path:str, patterns=[]):
	if not os.path.exists(dir_path): return []
	dir_files = list()
	for root, dirs, files in os.walk(dir_path):
		for file in files:
			fullpath = os.path.join(root, file)
			if not os.path.isfile(fullpath): continue  # TODO: is this needed here?
			if not patterns:
				dir_files.append(fullpath)
			else:
				for p in patterns:
					if fnmatch(file, p):
						dir_files.append(fullpath)
						break
	return dir_files


def get_filenames_in_dir_recursive(dir_path:str, patterns=[]):
	dir_files = list()
	for root, dirs, files in os.walk(dir_path):
		for file in files:
			fullpath = os.path.join(root, file)
			if not os.path.isfile(fullpath): continue  # TODO: is this needed here?
			if not patterns:
				dir_files.append(file)
			else:
				for p in patterns:
					if fnmatch(file, p):
						dir_files.append(file)
						break
	return dir_files


def should_ignore(path, filters):
	for string in filters:
		if string in path:
			return True
	return False


def get_mapsequence_filenames():
	map_names = list()

	startmap = os.path.join(mission.path, STARTMAP_FILENAME)
	mapseq = os.path.join(mission.path, MAPSEQUENCE_FILENAME)
	if os.path.isfile(startmap):
		with open(startmap, 'r') as file:
			for line in file:
				line = "".join(line.split())
				if line == "": continue
				map_names.append(line.strip())
				break # TODO: check if startingmap.txt can take more than one map
	elif os.path.isfile(mapseq):
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
	if not mission.map_names:
		warning(f"no maps are specified in {STARTMAP_FILENAME} or {MAPSEQUENCE_FILENAME}.")

	maps_dir = os.path.join(mission.path, "maps")
	for root, dirs, files in os.walk(maps_dir):
		invalid_dir = root != maps_dir
		for f in files:
			if invalid_dir:
				ignored_files.add(f)
				continue
			if mission.map_names:
				for name in mission.map_names:
					if not f.startswith(name + '.' ):
						ignored_files.add(f)
			else:
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



def parse_maps():
	if args.verbose: echo("Parsing maps")

	for map in mission.map_names:
		filepath = os.path.join(mission.path, "maps", map + ".map")
		map_parser.parse(filepath)


def get_included_files_in_dir(dirname, filters=[]):
	dir_relpath = os.path.join(mission.name, dirname)
	files = []
	for f in mission.included.files:
		if dir_relpath in f.fullpath:
			f_relpath = f.relpath.replace('\\', '/')
			if not filters:
				files.append(f_relpath)
			else:
				for filter in filters:
					if fnmatch(f_relpath, filter):
						files.append(f_relpath)
						break
	return files


def get_property_values(prop_name, patterns=[]):
	props = []

	for map in map_parser.maps:
		for e in map.entities:
			if not prop_name in e.properties: continue
			if not patterns:
				props.append(e.properties[prop_name])
			else:
				prop_val = e.properties[prop_name]
				for p in patterns:
					if fnmatch(prop_val, p):
						props.append(prop_val)
						break
	return props


def parse_def_files(dirname, file_filters, match_pattern=None, include_prefixes=[], exclude_prefixes=[]):
	files = get_included_files_in_dir(dirname, file_filters)
	defs = {}

	for path in files:
		scope_level = 0
		defs[path]  = []

		with open(path, 'r') as file:
			in_block_comment = False

			for line in file:
				token_count    = 0
				include_line   = False
				token          = ""
				line           = line.replace('\t', '')
				num_line_parts = len(line.split())

				for i in range(len(line)):
					ch = line[i]
					nc = '' if i >= len(line)-1 else line[i+1]
					pc = '' if i == 0 else line[i-1]

					if   ch == '{':
						if not in_block_comment: scope_level += 1
					elif ch == '}':
						if not in_block_comment: scope_level -= 1
					elif ch == '/' and nc == '/':   #  //     do test this comment type first
						if not in_block_comment: break
					elif ch == '*' and pc == '/':   #  /*
						scope_level += 1
						in_block_comment = True
						token = ""
					elif ch == '/' and pc == '*':   #  */
						scope_level -= 1
						if scope_level == 0:
							in_block_comment = False
						token = ""
					elif scope_level == 0:
						if in_block_comment: continue
						if ch in [' ','\n','\t','\r'] :
							if token == "": continue
							token_count += 1

							if num_line_parts > 1 and token_count == 1:
								if (exclude_prefixes and     token in exclude_prefixes)\
								or (include_prefixes and not token in include_prefixes):
									token = ""
									continue

							if num_line_parts == 1 or token_count > 1: #never store the prefix
								if not match_pattern or fnmatch(token, match_pattern):
									# print(token)
									defs[path].append(token)
							token = ""
						else:
							token += ch
	# for f in defs:
	# 	print(defs[f])
	return defs


def report_unused_definitions(name, unused):
	file_count = 0
	item_count = 0
	if len(unused) > 0:
		echo( REPORT_HEADER.format(name) )
		for file in unused:
			echo( REPORT_FILE.format(file) )
			file_count += 1
			for d in unused[file]:
				echo( REPORT_OBJECT.format(d) )
				item_count += 1
		echo( f"\n  {item_count} {name}, {file_count} files\n" )
	else:
		echo(REPORT_OK)


def report_unused_files(name, unused):
	if len(unused) > 0:
		echo(f"\n\n  Some {name} files have zero {name}s in use\n")
		for f in unused:
			echo( REPORT_OBJECT.format(f) )
		echo( REPORT_COUNT.format(len(unused), f"{name} files"))
	else:
		echo(REPORT_OK)


def check_unused_defs_in(files, used, valid_unused_defs=[], valid_unused_files=[]):
	unused = {}
	for filepath in files:
		if filepath in valid_unused_files: continue
		defs = files[filepath]
		for d in defs:
			if d in valid_unused_defs: continue
			if not d in used:
				if not filepath in unused:
					unused[filepath] = []
				unused[filepath].append(d)
	return unused


def check_unused_files_in(files, used, valid_unused_defs=[], valid_unused_files=[]):
	if isinstance(files, dict):
		unused = {}
		for filepath in files:
			if filepath in valid_unused_files: continue
			defs = files[filepath]
			num_unused = 0
			for d in defs:
				if d in valid_unused_defs: continue
				if not d in used:
					num_unused += 1
			if num_unused == len(defs):
				unused[filepath] = defs
	else:
		unused = []
		for d in files:
			if d in valid_unused_defs: continue
			if not d in used:
				unused.append(d)
	return unused


def check_any_found(files, name):
	if len(files) == 0:
		echo(f" no custom {name} found.")
		return False
	return True



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

	echo(f"\nPacking '{zipname}' completed with {mission.warning_count} warnings.")
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


def validate_models():
	task("Checking models... ")

	files = get_included_files_in_dir("models")
	if not check_any_found(files, "models"): return

	used = get_property_values("model")
	unused = check_unused_files_in(files, used)

	report_unused_files("model", unused)


def validate_materials():
	if args.defs: task("Checking material definitions... ")
	else:         task("Checking material files... ")

	files = parse_def_files("materials", ["*.mtr"])
	if not check_any_found(files, "materials"): return

	used = []
	for map in map_parser.maps:
		for e in map.entities:
			used += e.materials

	if args.defs:
		unused = check_unused_defs_in(files, used, VALID_UNUSED_MATERIALS)
		report_unused_definitions("materials", unused)
	else:
		unused = check_unused_files_in(files, used, VALID_UNUSED_MATERIALS)
		report_unused_files("material", unused)


def validate_skins():
	if args.defs: task("Checking skin definitions... ")
	else:         task("Checking skin files... ")

	files = parse_def_files("skins", ["*.skin"])
	if not check_any_found(files, "skins"):	return

	used = get_property_values("skin")
	if args.defs:
		unused = check_unused_defs_in(files, used)
		report_unused_definitions("skins", unused)
	else:
		unused = check_unused_files_in(files, used)
		report_unused_files("skin", unused)


def validate_particles():
	if args.defs: task("Checking particle definitions... ")
	else:         task("Checking particle files... ")

	files = parse_def_files("particles", ["*.prt"])
	if not check_any_found(files, "particles"): return

	used = get_property_values("model", ["*.prt"])
	if args.defs:
		unused = check_unused_defs_in(files, used)
		report_unused_definitions("particles", unused)
	else:
		unused = check_unused_files_in(files, used)
		report_unused_files("particle", unused)


def validate_xdata():
	if args.defs: task("Checking xdata definitions... ")
	else:         task("Checking xdata files... ")

	# TODO: are all the user xdata prefixed as "readables/"?
	files = parse_def_files("xdata", ["*.xd"])#, match_pattern="readables/*")
	if not check_any_found(files, "xdata"):	return

	valid_unused_defs = []
	for map_name in mission.map_names:
		valid_unused_defs.append(f"maps/{map_name}/mission_briefing")

	used = get_property_values("xdata_contents")

	if args.defs:
		unused = check_unused_defs_in(files, used, valid_unused_defs, VALID_UNUSED_XDATA_FILES)
		report_unused_definitions("xdata", unused)
	else:
		unused = check_unused_files_in(files, used, valid_unused_defs, VALID_UNUSED_XDATA_FILES)
		report_unused_files("xdata", unused)



def parse_entities():
	files = get_included_files_in_dir("def", ["*.def"])
	defs = []
	for path in files:
		scope_level = 0
		with open(path, 'r') as file:
			for line in file:
				line = line.replace('\n', '').replace('\t', '')
				if line == "": continue
				if not line.startswith("entityDef"): continue
				defs.append(line.split()[1])
	return defs


def validate_entities():
	task("Checking entities (experimental)... ")

	files = parse_def_files("def", ["*.def"], include_prefixes=["entityDef"])
	if not check_any_found(files, "entities"):	return

	used = []
	for map in map_parser.maps:
		for e in map.entities:
			used.append(e.classname)

	if args.defs:
		unused = check_unused_defs_in(files, used)
		report_unused_definitions("entities", unused)
	else:
		unused = check_unused_files_in(files, used)
		report_unused_files("entity", unused)



# TODO
RECOMMENDED_FILES = [
	"guis/assets/purchase_menu/map_of.tga",
	"guis/map_of.gui",
	# TODO: maybe check 'guis/map/*.gui' files with same name as the used maps
]

def validate_files():
	task("Checking mission files... ")

	# first pass for basic mission files
	files_to_check = [
		MODFILE_FILENAME,
		README_FILENAME,
		STARTMAP_FILENAME,
		BRIEFING_FILENAME,
	]

	missing_files = [ f
		for f in files_to_check
			if not os.path.isfile(os.path.join(mission.path, f))]

	if STARTMAP_FILENAME in missing_files and len(mission.map_names) > 0:
		missing_files.remove(STARTMAP_FILENAME)

	# second pass for other files that are recommended or require special treatment
	files_to_check = RECOMMENDED_FILES

	missing_files += [ f
		for f in files_to_check
			if not os.path.isfile(os.path.join(mission.path, f))]

	if len(missing_files) > 0:
		echo("\n\n  Some required or recommended files are missing\n")
		# echo("  (Some are just suggestions, not all files are strictly required.)\n")
		for p in missing_files:
			echo( REPORT_OBJECT.format(p) )
		echo( REPORT_COUNT.format(len(missing_files), "missing files"))
	else:
		echo(REPORT_OK)





check_params = "[\n  all, paths, files, models, materials, skins, particles,\n  entities, xdata\n]"

VALIDATION_PARAMS = [
	"paths",
	"files",
	"models",
	"materials",
	"skins",
	"particles",
	"entities",
	"xdata",
]

_validate_funcs = {
	"paths"     : validate_filepaths,
	"files"     : validate_files,
	"models"    : validate_models,
	"materials" : validate_materials,
	"skins"     : validate_skins,
	"particles" : validate_particles,
	"entities"  : validate_entities,
	"xdata"     : validate_xdata,
}


def validate_mission_files():
	if not args.check in ["paths", "files"]:
		parse_maps()

	if args.check == "all":
		for string in VALIDATION_PARAMS:
			_validate_funcs[string]()
	else:
		_validate_funcs[args.check]()


def get_entities_named(entities, name):
	ents = []
	contains_wildcard = '*' in name
	# print(contains_wildcard, name, len(map_parser.maps))

	for e in entities:
		if not contains_wildcard:
			if e.name == name:
				return [e]
		elif fnmatch(e.name, name):
			ents.append(e)

	return ents


def get_entities_of_class(entities, classname):
	ents = []
	contains_wildcard = '*' in classname
	for e in entities:
		if not contains_wildcard:
			if e.classname == classname:
				ents.append(e)
		else:
			if fnmatch(e.classname, classname):
				ents.append(e)
	return ents


def validate_ents_and_props(ents, props):
	invalid_entities = []
	for prp in props:
		k, v = prp
		k_has_wildcard = '*' in k
		v_has_wildcard = '*' in v
		for e in ents:
			if not k_has_wildcard:
				if not k in e.properties \
				or v == '?':
					invalid_entities.append(e)
					continue

				if v_has_wildcard:
					if not fnmatch(e.properties[k], v):
						invalid_entities.append(e)
				else:
					if v != e.properties[k]:
						invalid_entities.append(e)
			else:
				match = None
				for p in e.properties:
					if fnmatch(p, k):
						match = p

				if match:
					if v == '?':
						invalid_entities.append(e)
						continue

					if v_has_wildcard:
						if not fnmatch(e.properties[match], v):
							invalid_entities.append(e)
					else:
						if v != e.properties[match]:
							invalid_entities.append(e)
	return invalid_entities


def validate_ents_and_props2(ents, props):
	invalid_entities = []
	for e in ents:
		for p in props:
			pname, pval = p
			if not pname in e.properties \
			or pval != e.properties[pname]:
				invalid_entities.append(e)

	return invalid_entities


def check_entity_properties():
	parse_maps()

	params = args.check.replace(', ', ',').split(',')
	ident_params = params[0].split(' ')
	if len(ident_params) != 2:
		error(f"invalid argument '{','.join(ident_params)}' for entity checking")

	attr = ident_params[0]
	ident = ident_params[1]
	props = [ params[i].split(' ') for i in range(1, len(params)) ]

	for i in range(len(map_parser.maps)):
		map = map_parser.maps[i]
		task(f"Checking properties from '{ident}' entities in map '{mission.map_names[i]}'... ")

		if   attr == "name":      ents = get_entities_named(map.entities, ident)
		elif attr == "classname": ents = get_entities_of_class(map.entities, ident)
		else:                     error(f"invalid attribute '{attr}' for entity checking")

		if len(ents) == 0:
			echo(f"\n\n  No entities found with {attr} '{ident}'")
		else:
			invalid_ents = validate_ents_and_props(ents, props)

			if len(invalid_ents) > 0:
				echo(f"\n\n    Entities differ:")
				if attr == "classname":
					for e in invalid_ents:
						echo(f"        {e.classname}{' ' * (30-len(e.classname))} {e.name}")
				else:
					for e in invalid_ents:
						# echo(f"        {e.name}{' ' * (30-len(e.name))} {e.classname}")
						echo(f"        {e.name:<30} {e.classname}")
				echo(f"\n\n  {len(invalid_ents)} entities differ\n")
			else:
				echo(f"all OK")



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
	BrushDef      = "Scope.BrushDef"
	PatchDef      = "Scope.PatchDef"

class Entity:
	def __init__(self, id):
		self.id        = id
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
	def __init__(self, id):
		self.id = id
		self.materials = set()

class Patch:
	def __init__(self, id):
		self.id = id
		self.material = ""

class MapData:
	def __init__(self):
		self.entities = []

class MapParser:
	def __init__(self):
		self.scope        = Scope.File
		self.curr_prop    = None
		self.curr_ent     = None
		self.curr_brush   = None
		self.curr_patch   = None
		self.maps         = []
		self.entities     = []
		self.curr_map     = None

		self.curr_primitive_id  = -1
		self.curr_entity_id     = -1

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
				self.curr_prop = token[1:-1]
				self.set_scope(Scope.Property)
			elif token == '{':
				self.set_scope(Scope.Def)
			elif token == '}':
				# commit entity
				self.curr_map.entities.append(self.curr_ent)
				self.curr_ent = None
				# self.print_prop("----------------------", "")
				self.set_scope(Scope.File)

		elif self.scope == Scope.Def:
			# self.print_scope("Scope.Def", token)
			if   token.startswith("brushDef"):
				self.curr_brush = Brush(self.curr_primitive_id)
				self.set_scope(Scope.BrushDef)
			elif token.startswith("patchDef"):
				self.curr_patch = Patch(self.curr_primitive_id)
				self.set_scope(Scope.PatchDef)
			elif token == '}':
				self.set_scope(Scope.Entity)

		elif self.scope == Scope.Property:
			# self.print_scope("Scope.Property", token)
			if token.startswith('"'):
				val = token[1:-1]
				if   self.curr_prop == "classname": self.curr_ent.classname = val
				elif self.curr_prop == "name":      self.curr_ent.name = val
				# self.print_prop(self.curr_prop, val)
				self.curr_ent.properties[self.curr_prop] = val
				self.curr_prop = None
				self.set_scope(Scope.Entity)

		elif self.scope == Scope.BrushDef:
			if token.startswith('"'):
				# self.print_prop("brush texture: ", token)
				mat = token[1:-1]
				self.curr_brush.materials.add(mat)
				self.curr_ent.materials.add(mat)
			elif token == '}':
				# commit brush
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
				# commit patch
				self.curr_ent.patches.append(self.curr_patch)
				self.curr_patch = None
				self.set_scope(Scope.Def)

		elif self.scope == Scope.File:   # this branch is the most infrequent, keep it last
			# self.print_scope("Scope.File", token)
			if token == '{':
				self.curr_ent = Entity(self.curr_entity_id)
				self.entities.append(self.curr_ent)
				self.set_scope(Scope.Entity)


	def parse(self, map_file):
		self.curr_map = MapData()
		self.maps.append(self.curr_map)

		if args.verbose: task(f"    '{os.path.basename(map_file)}'...")

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
					parts = line.split()
					curr_id = int(parts[2])
					if parts[1] == "entity":
						assert self.scope == Scope.File, line
						self.curr_entity_id = curr_id
					elif parts[1] == "primitive":
						assert self.scope == Scope.Entity, line
						self.curr_primitive_id = curr_id
					continue

				for t in tokens:
					self.parse_token(t)

		t2 = time.time()
		total_time = "{:.1f}".format(t2-t1)
		if args.verbose: echo(f" ({total_time} secs)\n")

		assert(self.scope      == Scope.File)
		assert(self.curr_prop       == None)
		assert(self.curr_ent   == None)
		assert(self.curr_brush == None)
		assert(self.curr_patch == None)

		# add the materials under the "texture" properties
		# that weren't detected during parsing
		for e in self.curr_map.entities:
			if "texture" in e.properties:
				e.materials.add(e.properties["texture"])


#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		run
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
class CustomFormatter(ap.HelpFormatter):
	def _split_lines(self, text, width):
		return text.splitlines()
		# return ap.HelpFormatter._split_lines(self, text, width)


# keep this check here in case this script is ever called from another tool
if __name__ == "__main__":
	map_parser = MapParser()

	parser = ap.ArgumentParser(formatter_class=CustomFormatter)

	# parser.usage = "" # TODO maybe

	parser.add_argument("--version",           action="version",    version=f"FM Packer v{VERSION} for The Dark Mod\n\n")
	parser.add_argument("-qh", "--quick_help", action="store_true", help="show a shortened help message\n\n")

	parser.add_argument("path",    type=str, const=None, nargs='?',
		help="the path (relative or absolute) to the target fm\n\n")

	parser.add_argument("--pkset", type=str, metavar="[csv/ssv]",
		help= \
				"creates a .pkignore file with the given comma- or \n"
				"space-separated filters. Using * is not supported yet.\n"
				"Eg: \"_docs/, test_, .blend\"\n\n"
				)

	parser.add_argument("-v", "--verbose", action="store_true", help="show more information during the process.")

	parser.add_argument("--pkget", action="store_true",
		help= "outputs the .pkignore content as csv filters\n\n")

	parser.add_argument("-li", "--list_included", type=str, const='.', nargs='?', metavar="path",
		help= \
				"list files to include in pk4 within 'path' without packing,\n"
				"where 'path' is a relative path, and if ommitted, the\n"
				"mission path is used\n\n"
	)
	parser.add_argument("-le", "--list_excluded", type=str, const='.', nargs='?', metavar="path",
		help= \
				"list files to exclude from pk4 within 'path' without packing,\n"
				"where 'path' is a relative path, and if ommitted, the\n"
				"mission path is used\n\n"
	)

	parser.add_argument("-c", "--check", type=str, metavar = "[params]",
		help= \
				"check for unused or problematic files or entity values.\n"
				"To check files, you can use one of\n"
				f"{check_params}\n"
				"Use 'all' to perform all file-related checks at once.\n\n"

				"To find entities that don't match the given values,\n"
				"provide a comma-separated string argument with <name ...>\n"
				"or <classname ...>, followed by one or more <property val>.\n"
				"E.g. \"name *key*, nodrop 0, inv_droppable 1\".\n\n"
				"Using a '?' in place of a value will report all entities\n"
				"containing that property, regardless of its value.\n\n"
	)

	parser.add_argument("-d", "--defs", default=False, action="store_true",
		help= \
				"when looking up definitions (eg '-c skins'), report individual\n"
				"unused definitions, instead of files with no used definitions.\n\n"
	)

	args = parser.parse_args()
	# print(args)

	if args.quick_help:
		print_quick_help()
		exit()

	echo() # leave an empty line between the last prompt

	if args.pkset:
		echo("Previous .pkignore:\n\t", get_pkignore_csv())
		create_pk_ignore(args.pkset)
		echo(f"\nNew .pkignore:\n\t{get_pkignore_csv()}\n")
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

	if args.check:
		if args.check in ["all"] + VALIDATION_PARAMS:
			validate_mission_files()
		else:
			check_entity_properties()
		# else:
		# 	echo("wrong params for check - TODO proper error message")
			# arg_parser.py: error: argument -c/--check: invalid choice: 'derp' (choose from 'foo', 'bar')
		exit()


	if   args.included: check_files(args.included, mission.included, "Included files")
	elif args.excluded: check_files(args.excluded, mission.excluded, "Excluded files")
	else:               pack_fm()


