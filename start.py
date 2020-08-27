#!/usr/bin/env python
import click
import os

@click.group()
def cli():
    pass

@cli.group()
def transform():
    pass

@cli.group()
def analyze():
    pass

# --- utilities

def ls(directory=None, filtr=lambda item:True):
    """returns a list of strings of each file/directories in _directory_
    relative to the current directory

    :directory: the directory to list, defaults to the current directory
    :filtr: TO BE IMPLEMENTED
    :returns: a list of strings 
    """
    items = os.listdir(directory)
    if directory:
        items = [ os.path.join(directory, item) for item in items ]
    # TODO: implement filtr
    return items
    

# --- transform commands

@transform.command()
def test():
    """ test command """
    click.echo("All image categories")
    click.echo(ls('images'))

# --- analyze commands

if __name__ == '__main__':
    cli()
