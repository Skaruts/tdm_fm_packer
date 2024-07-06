# FM Packer

A little command line script to make packaging Dark Mod missions a bit more convenient. 


# Usage

Usage syntax looks like this
```
fmpak <fm_path> <options>
```

Run `fmpak.py` with the path to your fm. If `fmpak.py` is inside the FM folder, you can use `.` for "current folder".
```
python fmpak.py .
```
On some windows versions you should be able to abreviate to just `fmpak .`

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
```

Don't use `*`, as it's not supported. These filters are simply substrings that every dir/file name is tested against: if it has any of these substrings in it, then it's excluded. It's probably better to include dots for file extensions, though.

