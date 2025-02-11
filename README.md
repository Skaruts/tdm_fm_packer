# FM Packer

A command-line python script for packing The Dark Mod missions. It creates the `pk4` for you, automatically excluding any files and folders you specify in a `.pkignore` file.

This tool will also check `startingmap.txt` or `tdm_mapsequence.txt` to see which maps are used by the mission, and will automatically exclude all other map files.

## Using FM Packer
Usage syntax looks like this
```
fmpak.py <fm_path> <options>
```

Run `fmpak.py` with the path to your fm. The path can be absolute or relative to the current directory. If you invoke `fmpak.py` from inside the FM directory, you can use a `.`.

The process will abort if it doesn't detect `darkmod.txt` in the given `fm_path`.

You can view help information using `-h` or `--help`:
```
fmpak.py -h
```

## The `.pkignore` file

By default FM Packer will pack everything in your FM directory, but you can create a `.pkignore` file in it, and specify what should be excluded. You can do it either with a text editor or using the `--pkset` argument (see below).

The `.pkignore` works, in a limited way, similarly to a `.gitignore` file.

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
- #### `-h | --help`
	Displays usage information.

- #### `-qh | --quick_help`
	Displays shortened usage information.

- #### `--version`
	Displays the version of the FM Packer

- #### `-i | --included [path]`
	List files that will be included in the pk4 without packing them, which can be useful to check if the filters are correct.
	```
	fmpak.py . -i
	```
	You can also specify a relative path, to list only the files inside it:
	```
	fmpak.py . -i guis/assets
	```
- #### `-e | --excluded [path]`
	List files that will be included in the pk4 without packing them, which can be useful to check if the filters are correct.

	Works the same way as `--included`.

- #### `--pkset`
	Creates a .pkignore file with the given comma- or space-separated filters - may be needed to enclose them in quotes.
	```
	fmpak.py . --pkset "sources/, .blend, some_file.txt"
	```
- #### `--pkget`
	Shows the current content of the .pkignore file as csv filters.
	```
	fmpak.py . --pkget
	```

### Validating / Checking Files

- #### `--validate [all | paths | files | models | materials | skins | particles]`
	Checks for unused files or problems in the mission files.
	- **paths** - reports all file paths that contain spaces or special characters that can cause problems.
	- **files** - reports missing files that are mandatory, or which you might want to have in the mission.
	- **models** - reports 3d models not in use by the maps in the map sequence.
	- **materials** - reports material definitions not in use by the maps in the map sequence.
	- **skins** - reports skin files that contain no definitions in use by the maps in the map sequence.
	- **particles** - reports particle definitions not in use by the maps in the map sequence.
	- **all** - does all of the above in one go.
	```
	fmpak.py . --validate paths
	```

- #### `-cn | --check_named [name, prop1 val1, prop2 val2, ...]`
	Checks whether entities named `name` contain the given properties with the given values. If the property values are different they get reported.

	The name and properties need to be all contained in one string argument, separated by commas, and the property values separated by spaces.

	Supports `*` for checking several different names at once.

	```
	fmpak.py . -cn "*key*, inv_map_start 0, nodrop 1, inv_droppable 0"
	```

- #### `-cc | --check_class [classname, prop1 val1, prop2 val2, ...]`
	Checks whether entities with classname `classname` contain the given properties with the given values. If the property values are different they get reported.

	The classname and properties need to be all contained in one string argument, separated by commas, and the property values separated by spaces.

	Supports `*` for checking several different names at once.

	```
	fmpak.py . -cc "atdm:key_*, inv_droppable 1"
	```

