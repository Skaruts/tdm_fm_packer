# FM Packer

A command-line python script for packing The Dark Mod missions. It creates the `pk4` for you, automatically excluding any files and folders you specify in a `.pkignore` file.

This tool will also check `startingmap.txt` or `tdm_mapsequence.txt` to see which maps are used by the mission, and will automatically exclude all other map files.

## Using FM Packer
Usage syntax looks like this
```
fmpak.py <fm_path> <options>
```

Run `fmpak.py` with the path to your fm. If you're invoking `fmpak.py` from inside the FM folder, you can use a `.` for *"current directory"*, like this:
```
fmpak.py .
```
The path can be absolute, or relative to the current directory.

On Windows you can also add the location of this script to your system PATH, so you can run it from any FM folder. I don't quite know how this works on Mac and Linux.

The script will abort if it doesn't detect `darkmod.txt` in the folder you run it from, so make sure you run it from inside an FM folder.

You can view help information using `-h` or `--help`:
```
fmpak.py -h
```

## The `.pkignore` file

By default FM Packer will pack everything in your FM folder, but you can create a `.pkignore` file inside your FM folder, and specify what should be excluded. This file works similarly to a `.gitignore` file, but very limited.

```py
# suports comments

/sources     # folders must start or end with a '/'
/savegames
prefabs/

# anything else is interpreted as a file filter

.blend       
todo
some_file.txt
```

Don't use `*`, as it's not supported. These filters are merely substrings that every dir/file name is tested against: if it has any of these substrings in it, then it's excluded. It's better to include dots for file extensions, though.

The filtering system is case-sensitive.

Some files and folders are automatically excluded by the script:
- any file with `bak` in it (backup files)
- file extensions `.log`, `.dat`, `.py`, `.pyc`, `.pk4`, `.zip`, `.7z`, `.rar`, `.gitignore`, `.gitattributes`
- the `.git` and `__pycache__` directories, if they exist.


## Options

- #### `-h` or `--help`
	Displays usage information.

- #### `-v` or `--version`
	Displays the version of the FM Packer you're running.

- #### `-c` or `--check`
	Lists files without packaging, which can be useful to check if the filters are correct.
	```
	fmpak.py . -c
	```
	You can also specify a directory, to list only the files inside it (don't use spaces):
	```
	fmpak.py . -c:maps
	```
