# FM Packer

A command-line python script for packing The Dark Mod missions. It creates the `pk4` for you, automatically excluding any files and folders you specify in a `.pkignore` file.

This tool will also check `startingmap.txt` or `tdm_mapsequence.txt` to see which maps are used by the mission, and will automatically exclude all other map files.

## Using FM Packer
Usage syntax looks like this
```
fmpak.py <fm_path> <options>
```

Run `fmpak.py` with the path to your fm. If you're invoking `fmpak.py` from inside the FM directory, you can use a `.` for *"current directory"*:
```
fmpak.py .
```
The path can be absolute, or relative to the current directory.

The script will abort if it doesn't detect `darkmod.txt` in the directory you run it from, so make sure you run it from inside a valid FM directory.

You can view help information using `-h` or `--help`:
```
fmpak.py -h
```

## The `.pkignore` file

By default FM Packer will pack everything in your FM directory, but you can create a `.pkignore` file inside your FM directory, and specify what should be excluded. This file works, in a limited way, similarly to a `.gitignore` file.

```py
# suports comments

/sources     # folders must start or end with a '/'
prefabs/

# anything else is interpreted as a file filter

.blend       
todo
some_file.txt
```

The filtering is case-sensitive. Don't use `*`, as it's not supported. These filters are merely substrings that every dir/file name is tested against: if it has any of these substrings in it, then it's excluded. It's better to include dots for file extensions, though.


Some files and folders are automatically excluded by the script:
- any file with `bak` in it (backup files)
- file extensions `.lin`, .log`, `.dat`, `.py`, `.pyc`, `.pk4`, `.zip`, `.7z`, `.rar`, `.gitignore`, `.gitattributes`
- the `savegames`, `.git` and `__pycache__` directories, if they exist.


## Options
- #### `-h` / `--help`
	Displays usage information.

- #### `-qh` / `--quick_help`
	Displays shortened usage information.

- #### --version`
	Displays the version of the FM Packer

- #### `-c` / `--check`
	List files that will be included in the pk4 without packing them, which can be useful to check if the filters are correct.
	```
	fmpak.py . -c
	```
	You can also specify a directory, to list only the files inside it:
	```
	fmpak.py . -c guis/assets
	```

- #### `--pk_set`
	Creates a .pkignore file with the given comma- or space-separated filters - may be needed to enclose them in quotes.
	```
	fmpak . --pk_set "sources/, .blend, some_file.txt"
	```
- #### `--pk_get`
	Shows the current content of the .pkignore file as csv filters.
	```
	fmpak . --pk_get
	```
