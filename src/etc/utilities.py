import os
import click
import json
import csv
from PIL import Image

def is_directory(d):
    """ returns True if 'd' is a valid directory, False otherwise """
    return os.path.isdir(d) and not os.path.basename(d).startswith('_')


def is_csv(f):
    """ returns True if 'f' ends with .csv, False otherwise """
    return os.path.splitext(f)[1] == '.csv'


def plist(lst, indent="", sep="\n"):
    """print a list
    :lst: the list to print
    :indent: characters to append before each item
    :sep: characters used to separate items
    """
    s = sep.join([indent + item for item in lst])
    click.echo(s)


def pif(verbose, msg):
    """print if verbose

    :verbose: boolean indicating whether or not to print
    :msg: message to be printed
    :returns: None

    """
    if verbose:
        click.echo(msg)


def ls(directory=None, filtr=lambda item: True, mapper=lambda item: item, relative_to_cwd=True):
    """returns a list of strings of each file/directories in _directory_

    :directory: the directory to list, defaults to the current directory
    :filtr: the filter function to apply on each returned element
    :mapper: the mapper function to transform each returned element, applied after filter function
    :relative_to_cwd: the returned string is relative to current working directory rather than the given directory,
    _filtr_ and _mapper_ will always be applied with the paths relative to cwd.
    :returns: a list of strings, empty if the directory does not exist
    """
    # check for non-existing directory
    if directory and not os.path.isdir(directory):
        return []
    items = os.listdir(directory)
    # prepend the directory name if needed
    if directory:
        items = map(lambda item: os.path.join(directory, item), items)
    items = filter(filtr, items)
    items = map(mapper, items)
    if not relative_to_cwd:
        items = map(os.path.basename, items)
    return list(items)


def rm(path, dryrun=False, verbose=True):
    """ remove the file, or recursively remove directories

    :path: the path to the file or directory
    :dryrun: don't actually remove the file
    :verbose: print out files/directories that will be removed
    :returns: None

    """
    # helper function
    def _rm(item, is_file=False):
        pif(verbose, item)
        if not dryrun:
            if is_file:
                os.remove(item)
            else:
                os.rmdir(item)

    if os.path.isfile(path):
        _rm(path, is_file=True)
    elif os.path.isdir(path):
        for root, directories, files in os.walk(path, topdown=False):
            # remove files
            for name in files:
                full_name = os.path.join(root, name)
                _rm(full_name, is_file=True)
            # remove directories
            for name in directories:
                full_name = os.path.join(root, name)
                _rm(full_name, is_file=False)
        # remove the directory itself
        _rm(path, is_file=False)
    else:
        raise ValueError(f"{path} does not point to a file or directory")


def read_image(path):
    """read an image

    :path: the path to the image
    :returns: the image as a PIL.Image object

    """
    return Image.open(path)


def read_csv(path):
    """read csv file as a list of rows

    :path: path to the csv file
    :returns: the list of rows in the csv file

    """
    with open(path, newline='') as f:
        return list(csv.reader(f))


def read_json(path):
    """read json file as a python object

    :path: path to the json file
    :returns: the python object in the json file, None if file doesn't exist

    """
    with open(path) as f:
        return json.load(f)


def write_json(obj, path):
    """write a json object into file 

    :obj: the object to be written
    :path: path to the json file
    :returns: None

    """
    with open(path, "w") as f:
        return json.dump(obj, f)


def write_image(image, path, post_processors=[], override=True, verbose=True):
    """read an image

    :image: the image to be written as a PIL.Image object
    :path: the path to the image
    :post_processors: the processors to apply to the image before writing to the disk
    :override: override existing files
    :verbose: print output regarding writing status
    :returns: None

    """
    if os.path.isfile(path):
        if not override:
            pif(verbose, f"image at {path} exists, not overriding")
            return
        else:
            pif(verbose, f"overriding image at {path}")
    for p in post_processors:
        image = p(image)
    image.save(path)
    pif(verbose, f"successfully write to {path}")


def spearmanrank(seq1, seq2):
    """calculate the spearman's rank coefficient for two sequence

    :seq1: the first sequence
    :seq2: the second sequence
    :returns: a float number representing the rank result

    Note: the two sequence must contain the same set of elements

    """
    if len(seq1) != len(seq2):
        raise ValueError(
            f"the two sequences are of different length: {len(seq1)} and {len(seq2)}")
    n = len(seq1)
    idx = [seq1.index(x) for x in seq2]
    d_total = 0
    for i, x in enumerate(idx):
        d_total += (x - i)**2
    return 1 - 6 * d_total / (n * (n**2 - 1))
