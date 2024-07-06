# FM Packer

A command-line script to make packaging Dark Mod missions a bit more convenient. You simply run it and it creates the `.pk4` for you, automatically excluding unwanted files.

Requires either `py7zr` or `zipfile` (`zipfile` should be in python's standard library). Uses `py7zr` by default, though.

## Usage

Usage syntax looks like this
```
fmpak <fm_path> <options>
```

Run `fmpak.py` with the path to your fm. If `fmpak.py` is inside the FM folder, you can use `.` for "current folder".
```
python fmpak.py .
```
###### NOTE: On some windows versions you should be able to ommit the `python` call and the file extension, and abreviate to just `fmpak .`. Below I will be using the abbreviated syntax just for clarity. Use whichever works in your system.

The script is intended to be able to run from outside the FM folder, but I haven't tested this properly yet, so I can't guarantee it will work.

You can print help using `-h` or `--help`:
```
fmpak -h
```

---

By default FM Packer will pack everything in your FM, so if you need to exclude certain files or folders you can create a `.pkignore` file inside your FM folder, specifying what to exclude. This file works similar to `.gitignore`, but limited.

```py
# suports comments

/sources     # folders must start or end with a '/'
/savegames
prefabs/

# anything else is interpreted as a file filter

.blend       
bak
some_file.txt
```

Don't use `*`, as it's not supported. These filters are simply substrings that every dir/file name is tested against: if it has any of these substrings in it, then it's excluded. It's probably better to include dots for file extensions, though.

Some files and folders are automatically excluded by the script: `.log`, `.dat`, `.py`, `.pk4`, `.zip`, `.7z`, `.rar`, and the `__pycache__` directory if it exists.


## Options

#### `-c` or `--check` 
Lists files without packaging, which can be useful to check if the filters are correct. 
```
fmpak . -c
```
You can also specify a directory, to list only the files inside it (don't use spaces):
```
fmpak . -c:maps
```

#### `-q` or `--quick`
This is mostly intended for debugging purposes. It turns off usage of `py7zr` in favor of `zipfile`, which is faster, but creates larger files.
```
fmpak . -q
```
There's currently no support for specifying compression levels.









