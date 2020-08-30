#!/usr/bin/env python
import click
import os

@click.group()
def cli():
    pass

@cli.group()
def info():
    pass

@cli.group()
def transform():
    pass

@cli.group()
def analyze():
    pass

# --- utilities

def ls(directory=None, filtr=lambda item:True, mapper=lambda item:item):
    """returns an iterable of strings of each file/directories in _directory_
    The strings will be relative to the current directory

    :directory: the directory to list, defaults to the current directory
    :filtr: the filter function to apply on each returned element
    :mapper: the mapper function to transform each returned element, applied after filter function
    :returns: a list of strings 
    """
    items = os.listdir(directory)
    if directory:
        items = map(lambda item:os.path.join(directory, item), items)
    items = filter(filtr, items)
    items = map(mapper, items)
    return list(items)

def get_image_category_names():
    """gets all existing image categories
    :returns: a list of category names
    """
    return ls('images', filtr=os.path.isdir, mapper=os.path.basename)

def get_transformation_names():
    """gets all available transformations
    :returns: a list of names of transformation
    """
    return ls('src/transformations', filtr=os.path.isdir, mapper=os.path.basename)

def get_analysis_names():
    """gets all available analysis metrics
    :returns: TODO
    """
    return ls('src/analysis', filtr=os.path.isdir, mapper=os.path.basename)

# --- transform utilities

def transform_image(category, transformation, level):
    """TODO: Docstring for transform_image.

    :category: the image category's name. E.g. brick
    :transformation: TODO
    :level: TODO
    :returns: TODO

    """
    pass

# --- transform commands

@transform.command()
def all():
    """ transform all existing images with all available transformations """
    pass

# --- analyze commands

# --- info utilities
def plist(lst, indent="", sep="\n"):
    """print a list
    :lst: the list to print
    :indent: characters to append before each item
    :sep: characters used to separate items
    """
    s = sep.join([ indent + item for item in lst ])
    click.echo(s)

# --- info commands
@info.command()
def all():
    click.echo("Image categories:")
    plist(get_image_category_names(), indent="\t")
    click.echo("Transformations:")
    plist(get_transformation_names(), indent="\t")
    click.echo("Analyses:")
    plist(get_analysis_names(), indent="\t")

if __name__ == '__main__':
    cli()
