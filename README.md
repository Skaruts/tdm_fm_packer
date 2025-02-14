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

- #### `-v | --verbose`
	Display more information, if applicable.

- #### `-li | --list_included [path]`
	List files that will be included in the pk4 without packing them, which can be useful to check if the filters are correct.
	```
	fmpak.py . -li
	```
	You can also specify a relative path, to list only the files inside it:
	```
	fmpak.py . -li guis/assets
	```
- #### `-le | --list_excluded [path]`
	List files that will be included in the pk4 without packing them, which can be useful to check if the filters are correct.

	Works the same way as `--list_included`.

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

### Checking Files / Entities

- ### `-d | --defs`
	Modifier for the checks below, to make them report individual definitions that are unused, instead of files containing no used definitions.

- #### `-c | --check`
	This option has two main uses:
	- to check for unused or problematic files, which can be useful to make sure the final pk4 doesn't contain unnecessary files.
	- to check for entities that don't match the given values, which can be useful to make sure all entties of a certain classname or name pattern are correctly configured (eg, all keys are droppable, certain doors are locked, etc.)


	To perform file related checks use one of the following parameters:
	- **paths** - reports all file paths that contain spaces or special characters that can cause problems.
	- **files** - (very experimental) reports missing files that are mandatory, or which you might want to have in the mission.
	- **entities** - (very experimental) reports custom entities not in use by the maps in the map sequence.
	- **models** - reports 3d models not in use by the maps in the map sequence.
	- **materials** - reports material definitions not in use by the maps in the map sequence.
	- **skins** - reports skin files that contain no definitions in use by the maps in the map sequence.
	- **particles** - reports particle definitions not in use by the maps in the map sequence.
	- **xdata** - reports xdata definitions not in use by the maps in the map sequence.
	- **all** - does all of the above in one go.
	```
	fmpak.py . --check paths
	```
	To check for entities that don't match the given values, pass a string containing `<classname ...>` or `<name ...>` followed by one or more `<property ...>`. A wildcard `*` can be used on both.
	```c#
	fmpak.py . -c "*key*, nodrop 1, inv_drop* 0"
	```
	Using a `?` in place of a value will report any entities containing that property, regarldes of its value.
	```c#
	fmpak.py . -c "*key*, inv_droppable ?"
	```


