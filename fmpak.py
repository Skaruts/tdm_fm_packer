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


echo = print  # just to differentiate from debug prints

VERSION = "0.5.1"
PKIGNORE_FILENAME = ".pkignore"
MODFILE_FILENAME = "darkmod.txt"

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

# make sure to exclude any meta stuff
ignored_folders = set(["savegames", "__pycache__", ".git"])
ignored_files = set([
	PKIGNORE_FILENAME, ".lin", "bak", ".log", ".dat", ".py", ".pyc",
	".pk4", ".zip", ".7z", ".rar", ".gitignore", ".gitattributes"
])


class MissionFile:
	def __init__(self, fullpath, relpath):
		self.fullpath = fullpath
		self.relpath = relpath



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		utils
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def error(message):
	echo("ERROR:", message)
	exit()


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


def get_files_in_dir(dir_path:str, filters:list = []):
	files = list()

	for name in os.listdir(dir_path):
		filepath = os.path.join(dir_path, name)#.encode("utf-8")
		_, file_ext = os.path.splitext(filepath)
		if os.path.isfile(filepath):
			is_valid = True
			for filter in filters:
				if filter in name:
					is_valid = False
					break

			if is_valid:
				files.append(filepath)

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
	map_names = get_mapsequence_filenames()
	print(map_names)
	files = get_files_in_dir(os.path.join(mission.path, "maps"))

	for f in files:
		_, tail = os.path.split(f)
		for name in map_names:
			if tail.startswith(name): continue
			ignored_files.add(tail)


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



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		run
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# keep this check here in case this script may be called from another tool
if __name__ == "__main__":
	parser = ap.ArgumentParser()

	# parser.usage = "" # TODO

	parser.add_argument("--version",           action="version",    version=f"FM Packer v{VERSION} for The Dark Mod")
	parser.add_argument("-qh", "--quick_help", action="store_true", help="show a shortened help message")

	parser.add_argument("path",      type=str, const=None, nargs='?', help="the path (relative or absolute) to the target fm")
	parser.add_argument("--pk_set",  type=str,                        help="creates a .pkignore file with the given comma- or space-separated filters")
	parser.add_argument("--pk_get",  action="store_true",             help="shows the .pkignore content as csv filters")

	parser.add_argument("-i", "--included", type=str, const='.', nargs='?', help="list files to include in pk4 within 'INCLUDED' without packing them, where 'INCLUDED' is a relative path")
	parser.add_argument("-e", "--excluded", type=str, const='.', nargs='?', help="list files to exclude from pk4 within 'EXCLUDED' without packing them, where 'EXCLUDED' is a relative path")

	args = parser.parse_args()

	if args.quick_help:
		print_quick_help()
		exit()

	if args.pk_set:
		echo("Previous .pkignore:\n\t", get_pkignore_csv())
		create_pk_ignore(args.pk_set)
		echo("\nNew .pkignore:\n\t", get_pkignore_csv())
		exit()

	if args.pk_get:
		echo(".pkignore:\n\t", get_pkignore_csv())
		exit()

	if not args.path:
		error("a path must be provided")

	set_fm_path(args.path)
	validate_fm_path()
	load_pkignore()
	gather_files()

	if   args.included: check_files(args.included, mission.included, "Included files")
	elif args.excluded: check_files(args.excluded, mission.excluded, "Excluded files")
	else:               pack_fm()


