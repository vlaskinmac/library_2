# Parse library

**The code collects book data from an online library.**


This script is written as part of the task of the courses [Devman](https://dvmn.org).

- The code collects data about the book in the dictionary.

- Downloads books in txt format.

- Downloads the picture from the cover of the books.

- Loads book covers.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Python Version

Python 3.6 and later.

### Installing

To install the software, you need to install the dependency packages from the file: **requirements.txt**.

Perform the command:

```

pip3 install -r requirements.txt

```


## Launch code

#### Arguments
- Set the initial id for book (it`s argument required) use arguments: **-s** or **--start_id**
- Set the end id for book use arguments: **-e** or **--end_id**
- To call help, use the required arguments **-h** or **--help**
- Set path to the directory with parsing results: **-d** or **--dest_folder**
- Set the path to the json file, use the argument: **-j** or **--json_path**
- Set not to download images, use argument: **-i** or **--skip_imgs**
- Set not to download books, use argument: **-t** or **--skip_txt**



**Examples of commands:**


```python
$ python parse_library.py -s 1 -e 10
```

```python
$ python parse_library.py -s 1
```

```python
$ python parse_library.py -s 1 -e 10 -d
```

```python
$ python parse_library.py -s 1 -e 10 -i
```

```python
$ python parse_library.py -s 1 -e 10 -t
```
```python
$ python parse_library.py -s 1 -e 10 -j /any path/
```



## Authors

**vlaskinmac**  - [GitHub-vlaskinmac](https://github.com/vlaskinmac/)
