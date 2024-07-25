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


VERSION = "0.4.2"
CWD = os.getcwd()   # current working directory
PKIGNORE = ".pkignore"


fm_path = ""
file_count = 0
dir_count = 0
tasks = []

# valid command line args
VALID_CHECK_ARGS   = ["-c", "--check"]
VALID_VERSION_ARGS = ["-v", "--version"]
VALID_HELP_ARGS    = ["-h", "--help"]

# task names
CHECK_VERSION = "check_version"
CHECK_FILES   = "check_files"
PACK_FILES    = "pack_files"
PRINT_HELP    = "print_help"



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 		initialize ignore lists
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# make sure to exclude any meta stuff
ignored_folders = set([
	"__pycache__",
	".git"
])
ignored_files = set([
	PKIGNORE,
	"bak",
	".log",
	".dat",
	".py",
	".pyc",
	".pk4",
	".zip",
	".7z",
	".rar",
	".gitignore",
	".gitattributes"
])

def load_ignore_file(fm_path):
	file_path = os.path.join(fm_path, PKIGNORE)

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



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
#       TASK
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
class Task:
	type = ""
	arg = ""
	def __init__(self, type, arg=""):
		self.type = type
		if arg:
			self.arg = arg

def add_task(type, arg=""):
	tasks.append(Task(type, arg))



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 	Main stuff
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def main():
	parse_cli_args()
	run_tasks()


def run_tasks():
	# print("running tasks", tasks)
	for t in tasks:
		if t.type == PACK_FILES:
			load_ignore_file(fm_path)
			validate_fm_path()
			pack_fm(fm_path)
		elif t.type == CHECK_VERSION:
			print_version()
		elif t.type == CHECK_FILES:
			validate_fm_path()
			load_ignore_file(fm_path)
			list_files(t)
		elif t.type == PRINT_HELP:
			print_help()

# ignore the maps folder
def add_maps_directory_to_ignore_list(fm_name):
	ignored_folders.add(os.path.join(fm_name, "maps"))

def pack_fm(fm_path):
	_, fm_name = os.path.split(fm_path)
	zipname = fm_name + ".pk4"
	add_maps_directory_to_ignore_list(fm_name)

	print(f"\nPacking '{zipname}'... \n")
	t1 = time.time()


	with zipf.ZipFile(zipname, 'w', zipf.ZIP_DEFLATED, compresslevel=9) as f:
		pack_files(fm_path, f)

	t2 = time.time()
	total_time = "{:.1f}".format(t2-t1)

	print(f"\nFinished packing '{zipname}'")
	print(f"    {dir_count} dirs, {file_count} files, {total_time} seconds")


def pack_files(fm_path, f):
	global file_count, dir_count
	for root, dirs, files in os.walk(fm_path):
		if should_ignore(root, ignored_folders): continue
		for file in files:
			filename = os.path.join(root, file).replace(fm_path, '')[1:]
			if should_ignore(filename, ignored_files): continue
			print(filename)
			f.write(filename)#, os.path.relpath(filename, os.path.join(filename, '..')))
			file_count += 1
		dir_count += 1

	map_files = get_map_files(fm_path)
	for file in map_files:
		filename = file.replace(fm_path, '')[1:]
		print(filename)
		f.write(filename)
		file_count += 1


def parse_cli_args():
	argv = sys.argv

	del argv[0] # the first entry is this program's name
	argc = len(sys.argv)

	if argc == 0:
		usage_error("no fm path provided")

	i = 0
	while i < argc:
		string = argv[i]

		if string.startswith('-'):
			command = string
			args = None
			if ':' in string:
				idx = string.index(':')
				command = string[:idx]
				args = string[idx+1:]
			# print(command, args)

			if   command in VALID_VERSION_ARGS: add_task(CHECK_VERSION, args)
			elif command in VALID_CHECK_ARGS:   add_task(CHECK_FILES, args)
			elif command in VALID_HELP_ARGS:    add_task(PRINT_HELP, args)
			else:
				usage_error(f"unknown argument {string}")
		else:
			set_fm_path(string)
		i += 1

	if len(tasks) == 0 and fm_path != "":
		add_task(PACK_FILES)



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 	utils
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def error(message):
	print("ERROR:", message)
	exit()

def usage_error(message):
	print(message)
	print_quick_help()
	exit()


def validate_fm_path():
	if not os.path.isdir(fm_path):
		error(f"invalid path '{fm_path}'")

	if not os.path.isfile(os.path.join(fm_path, "darkmod.txt")):
		error(f"no 'darkmod.txt' found at path '{fm_path}'")

	# print("fm_path:", fm_path)


def get_files_in_dir(dir_path:str, filters:list = []):
	files = list()

	for name in os.listdir(dir_path):
		filepath = os.path.join(dir_path, name)#.encode("utf-8")
		_, file_ext = os.path.splitext(filepath)
		# print(filepath)
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


def get_map_files(fm_path):
	map_names = get_map_filenames(fm_path)

	map_files = []
	files = get_files_in_dir(os.path.join( fm_path, "maps"))

	for f in files:
		_, tail = os.path.split(f)
		for name in map_names:
			if tail.startswith(name) and not should_ignore(tail, ignored_files):
				map_files.append(f)
				break

	return map_files


def get_map_filenames(fm_path):
	map_names = list()

	startmap = os.path.join(fm_path, "startingmap.txt")
	if os.path.isfile(startmap):
		with open(startmap, 'r') as file:
			map_names = [ file.readlines()[0].strip() ]
		return map_names

	mapseq = os.path.join(fm_path, "tdm_mapsequence.txt")
	if os.path.isfile(mapseq):
		with open(mapseq, 'r') as file:
			for line in file:
				line = "".join(line.split())
				if line == "": continue
				map_names.append(line.strip()[ line.index(':')+1 :])
		return map_names


def set_fm_path(string):
	global fm_path
	fm_path = string

	if fm_path == '.':               fm_path = CWD
	elif not os.path.isabs(fm_path): fm_path = os.path.join(CWD, fm_path)



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
#       TASK FUNCTIONS
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
def print_quick_help():
	print(f"""
    Usage:
        dmpak <fm_path> <options>

    Use 'dmpak -h' for more information.
	""")


def print_help():
	print(f"""
    TDM Packer for The Dark Mod - version {VERSION}"

    Usage:
        dmpak <fm_path> <options>

        'fm_path' can be a dot '.', for current directory.

    Options:
        -c / --check      list all files in 'fm_path', without zipping.
                          A specific directory, relative to the 'fm_path',
                          can be provided using '-c:dir' (no spaces), to only
                          list the files inside 'dir'.

        -v / --version    print out the version of TDM Packer

        -h / --help       display helpful information

        -q / --quick      use quickest compression level
	""")


def print_version():
	print(f"TDM Packer version {VERSION}")


def list_files(task):
	global file_count, dir_count

	_, fm_name = os.path.split(fm_path)
	add_maps_directory_to_ignore_list(fm_name)

	dir = task.arg
	if dir == "":
		for root, dirs, files in os.walk(fm_path):
			if should_ignore(root, ignored_folders): continue
			for file in files:
				filename = os.path.join(root, file).replace(fm_path, '')[1:]
				if should_ignore(filename, ignored_files): continue
				print(filename)
				file_count += 1
			dir_count += 1

		map_files = get_map_files(fm_path)
		for file in map_files:
			filename = file.replace(fm_path, '')[1:]
			print(filename)
			file_count += 1
	elif dir == "maps":
		map_files = get_map_files(fm_path)
		for file in map_files:
			filename = file.replace(fm_path, '')[1:]
			print(filename)
			file_count += 1
	else:
		dirpath = os.path.join(fm_path, dir)

		if not os.path.exists(dirpath):
			error(f"invalid directory '{dir}'" )

		# print("dir", dir, fm_path)
		for root, dirs, files in os.walk(dirpath):
			if should_ignore(root, ignored_folders): continue
			for file in files:
				filename = os.path.join(root, file).replace(fm_path, '')[1:]
				if should_ignore(filename, ignored_files): continue
				print(filename)
				file_count += 1
			dir_count += 1

	# print(ignored_folders)
	# print(ignored_files)

	print(f"\n    {dir_count} dirs, {file_count} files")





#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
# 	run
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=
main()
