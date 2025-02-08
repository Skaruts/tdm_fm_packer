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

VERSION = "0.5"
PKIGNORE_FILENAME = ".pkignore"
MODFILE_FILENAME = "darkmod.txt"


class data: # to avoid using 'global'
	fm_path    = ""
	file_count = 0
	dir_count  = -1  # -1 to compensate for path.walk counting with the root dir


# make sure to exclude any meta stuff
ignored_folders = set(["__pycache__", ".git"])
ignored_files = set([
	PKIGNORE_FILENAME, ".lin", "bak", ".log", ".dat", ".py", ".pyc",
	".pk4", ".zip", ".7z", ".rar", ".gitignore", ".gitattributes"
])



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		utils
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def error(message):
	echo("ERROR:", message)
	exit()


def set_fm_path(path):
	data.fm_path = path
	if path == '.':
		data.fm_path = os.getcwd()
	elif not os.path.isabs(path):
		data.fm_path = os.path.join(os.getcwd(), data.fm_path)


def validate_fm_path():
	if not os.path.isdir(data.fm_path):
		error(f"invalid path '{data.fm_path}'")

	if not os.path.isfile(os.path.join(data.fm_path, MODFILE_FILENAME)):
		error(f"no '{MODFILE_FILENAME}' found at path '{data.fm_path}'")


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


def get_map_files():
	map_names = get_map_filenames()

	map_files = []
	files = get_files_in_dir(os.path.join(data.fm_path, "maps"))

	for f in files:
		_, tail = os.path.split(f)
		for name in map_names:
			if tail.startswith(name) and not should_ignore(tail, ignored_files):
				map_files.append(f)
				break

	return map_files


def get_map_filenames():
	map_names = list()

	startmap = os.path.join(data.fm_path, "startingmap.txt")
	if os.path.isfile(startmap):
		with open(startmap, 'r') as file:
			map_names = [ file.readlines()[0].strip() ]
		return map_names

	mapseq = os.path.join(data.fm_path, "tdm_mapsequence.txt")
	if os.path.isfile(mapseq):
		with open(mapseq, 'r') as file:
			for line in file:
				line = "".join(line.split())
				if line == "": continue
				map_names.append(line.strip()[ line.index(':')+1 :])
		return map_names


# ignore the maps folder
def add_maps_directory_to_ignore_list(fm_name):
	ignored_folders.add(os.path.join(fm_name, "maps"))


def load_pkignore():
	file_path = os.path.join(data.fm_path, PKIGNORE_FILENAME)

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

	# print(ignored_folders)
	# print(ignored_files)

def get_pkignore_csv():
	file_path = os.path.join(data.fm_path, PKIGNORE_FILENAME)
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






#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
#       TASK FUNCTIONS
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def print_quick_help():
	echo(f"""
    Usage:
        {os.path.basename(__file__)} <fm_path> <options>

    Use '{os.path.basename(__file__)} -h' for more information.
	""")


def pack_fm():
	fm_name = os.path.basename(data.fm_path)
	zipname = fm_name + ".pk4"
	add_maps_directory_to_ignore_list(fm_name)

	echo(f"\nPacking '{zipname}'... \n")
	t1 = time.time()

	with zipf.ZipFile(zipname, 'w', zipf.ZIP_DEFLATED, compresslevel=9) as f:
		pack_files(f)

	t2 = time.time()
	total_time = "{:.1f}".format(t2-t1)

	echo(f"\nFinished packing '{zipname}'")
	echo(f"    {data.dir_count} dirs, {data.file_count} files, {total_time} seconds")


def pack_files(f):
	for root, dirs, files in os.walk(data.fm_path):
		if should_ignore(root, ignored_folders): continue
		data.dir_count += 1
		for file in files:
			filename = os.path.join(root, file).replace(data.fm_path, '')[1:]
			if should_ignore(filename, ignored_files): continue
			echo(filename)
			f.write(filename)#, os.path.relpath(filename, os.path.join(filename, '..')))
			data.file_count += 1

	map_files = get_map_files()
	data.dir_count += 1
	for file in map_files:
		filename = file.replace(data.fm_path, '')[1:]
		echo(filename)
		f.write(filename)
		data.file_count += 1


def check_files():
	dir = args.check
	if dir.startswith("./"):
		dir = dir.replace("./", '')

	if dir == "maps":
		map_files = get_map_files()
		data.dir_count = 0
		for file in map_files:
			filename = file.replace(data.fm_path, '')[1:]
			echo(filename)
			data.file_count += 1
	else:
		if dir == '.':
			dirpath = data.fm_path
			fm_name = os.path.basename(dirpath)
			add_maps_directory_to_ignore_list(fm_name)
		else:
			dirpath = os.path.join(data.fm_path, dir)

		if not os.path.exists(dirpath):
			error(f"invalid directory '{dir}'" )

		for root, dirs, files in os.walk(dirpath):
			if should_ignore(root, ignored_folders): continue
			for file in files:
				rel_filepath = os.path.join(root, file).replace(dirpath, '')[1:]
				if should_ignore(rel_filepath, ignored_files): continue
				echo(rel_filepath)
				data.file_count += 1
			data.dir_count += 1

		if dir == '.':
			map_files = get_map_files()
			data.dir_count += 1
			for file in map_files:
				filename = file.replace(data.fm_path, '')[1:]
				echo(filename)
				data.file_count += 1

	# print(ignored_folders)
	# print(ignored_files)

	echo(f"\n    {data.dir_count} dirs, {data.file_count} files")


def create_pk_ignore(csv):
	if ',' in csv:
		vals = csv.replace(' ', '').split(',')
	else:
		vals = csv.split()

	content = '\n'.join(vals)

	file_path = os.path.join(data.fm_path, PKIGNORE_FILENAME)
	with open(file_path, 'w') as f:
		f.write(content)





#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		run
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# keep this check here in case this script may be called from another tool
if __name__ == "__main__":
	parser = ap.ArgumentParser()
	group = parser.add_mutually_exclusive_group()

	# parser.usage = ""

	parser.add_argument("--version",          action="version",    version=f"FM Packer for The Dark Mod - v{VERSION}")
	group.add_argument("-qh", "--quick_help", action="store_true",            help="show a shortened help message")
	parser.add_argument("path",               type=str,            help="the path (relative or absolute) to the target fm")
	parser.add_argument("-c", "--check",      type=str, const='.', nargs='?', help="list files to include in pk4 within 'CHECK' without packing them, where 'CHECK' is a relative path")
	parser.add_argument("--pk_set",           type=str, help="creates a .pkignore file with the given comma- or space-separated filters")
	parser.add_argument("--pk_get",           action="store_true", help="shows the .pkignore content as csv filters")

	args = parser.parse_args()

	if args.pk_set:
		echo("Previous .pkignore:", get_pkignore_csv())
		create_pk_ignore(args.pk_set)
		echo("\nNew .pkignore:", get_pkignore_csv())
		exit()

	if args.pk_get:
		echo(".pkignore:", get_pkignore_csv())
		exit()


	if args.quick_help:
		print_quick_help()
		exit()

	set_fm_path(args.path)
	validate_fm_path()
	load_pkignore()

	if args.check: check_files()
	else:          pack_fm()

