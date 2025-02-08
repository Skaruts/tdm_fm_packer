#!/usr/bin/env python3

"""
		TDM Packer for The Dark Mod

	Quick Usage Reference:
		- create a .pkignore file in your FM folder, specifying what to exclude
		- run 'python dmpak.py .' from inside your FM folder
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
	dir_count  = 0


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
		if string in path.lower():
			return True
	return False


def get_map_files():
	map_names = get_map_filenames()

	map_files = []
	files = get_files_in_dir(os.path.join( data.fm_path, "maps"))

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




#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
#       TASK FUNCTIONS
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def print_quick_help():
	echo(f"""
    Usage:
        {os.path.basename(__file__)} <fm_path> <options>

    Use '{os.path.basename(__file__)} -h' for more information.
	""")


def print_version():
	echo(f"TDM Packer version {VERSION}")


# ignore the maps folder
def add_maps_directory_to_ignore_list(fm_name):
	ignored_folders.add(os.path.join(fm_name, "maps"))


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
		for file in files:
			filename = os.path.join(root, file).replace(data.fm_path, '')[1:]
			if should_ignore(filename, ignored_files): continue
			echo(filename)
			f.write(filename)#, os.path.relpath(filename, os.path.join(filename, '..')))
			data.file_count += 1
		data.dir_count += 1

	map_files = get_map_files()
	for file in map_files:
		filename = file.replace(data.fm_path, '')[1:]
		echo(filename)
		f.write(filename)
		data.file_count += 1


def load_ignore_file():
	file_path = os.path.join(data.fm_path, PKIGNORE_FILENAME)

	if not os.path.exists(file_path):
		return

	with open(file_path, 'r') as file:
		for line in file:
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




def check_files():
	fm_name = os.path.basename(data.fm_path)
	add_maps_directory_to_ignore_list(fm_name)

	dir = args.check
	if dir == "":
		for root, dirs, files in os.walk(data.fm_path):
			if should_ignore(root, ignored_folders): continue
			for file in files:
				filename = os.path.join(root, file).replace(data.fm_path, '')[1:]
				if should_ignore(filename, ignored_files): continue
				echo(filename)
				data.file_count += 1
			data.dir_count += 1

		map_files = get_map_files()
		for file in map_files:
			filename = file.replace(data.fm_path, '')[1:]
			echo(filename)
			data.file_count += 1
	elif dir == "maps":
		map_files = get_map_files()
		for file in map_files:
			filename = file.replace(data.fm_path, '')[1:]
			echo(filename)
			data.file_count += 1
	else:
		dirpath = os.path.join(data.fm_path, dir)

		if not os.path.exists(dirpath):
			error(f"invalid directory '{dir}'" )

		# print("dir", dir, data.fm_path)
		for root, dirs, files in os.walk(dirpath):
			if should_ignore(root, ignored_folders): continue
			for file in files:
				filename = os.path.join(root, file).replace(data.fm_path, '')[1:]
				if should_ignore(filename, ignored_files): continue
				echo(filename)
				data.file_count += 1
			data.dir_count += 1

	# print(ignored_folders)
	# print(ignored_files)

	echo(f"\n    {data.dir_count} dirs, {data.file_count} files")





#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		run
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# keep this check here in case this script may be called from another tool
if __name__ == "__main__":
	parser = ap.ArgumentParser()
	group = parser.add_mutually_exclusive_group()

	# parser.usage = ""

	parser.add_argument("--version",          action="version",    version=f"TDM Packer v{VERSION}")
	group.add_argument("-qh", "--quick_help", action="store_true",            help="show a shortened help message")
	parser.add_argument("path",                type=str,            help="the path (relative or absolute) to the target fm")
	parser.add_argument("-c", "--check",      type=str, const='.', nargs='?', help="list files to include in pk4 within 'CHECK' without packing them, where 'CHECK' is a relative path")

	args = parser.parse_args()

	if args.quick_help:
		print_quick_help()
		exit()

	set_fm_path(args.path)
	validate_fm_path()
	load_ignore_file()

	if args.check: check_files()
	else:          pack_fm()

