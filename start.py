#!/usr/bin/env python
import click
import os
import importlib  # for dynamic import
from PIL import Image
from src.utils.helpers import crop_to_circle

# --- constants

transformation_dir = ['src', 'transformations']
analysis_dir = ['src', 'analysis']
image_dir = ['images']

# --- exceptions


class ModuleError(Exception):
    """ when a module is not implemented according to the specification """
    pass

# --- utilities


def validate_image_categories(ctx, param, value):
    """ makes sure that the given image categories are valid """
    invalid_categories = set(value) - set(get_image_category_names())
    if invalid_categories:
        raise ValueError(f"Invalid image categories: {invalid_categories}")
    return value


def validate_transformations(ctx, param, value):
    """ makes sure that the given image transformations are valid """
    invalid_transformations = set(value) - set(get_transformation_names())
    if invalid_transformations:
        raise ValueError(
            f"Invalid image transformations: {invalid_transformations}")
    return value


def ls(directory=None, filtr=lambda item: True, mapper=lambda item: item):
    """returns a list of strings of each file/directories in _directory_
    The strings will be relative to the current directory

    :directory: the directory to list, defaults to the current directory
    :filtr: the filter function to apply on each returned element
    :mapper: the mapper function to transform each returned element, applied after filter function
    :returns: a list of strings
    """
    items = os.listdir(directory)
    if directory:
        items = map(lambda item: os.path.join(directory, item), items)
    items = filter(filtr, items)
    items = map(mapper, items)
    return list(items)


def get_image_category_names():
    """gets all existing image categories
    :returns: a list of category names
    """
    return ls(
        os.path.join(
            *image_dir),
        filtr=os.path.isdir,
        mapper=os.path.basename)


def get_transformation_names():
    """gets all available transformations
    :returns: a list of names of transformation
    """
    return ls(
        os.path.join(
            *transformation_dir),
        filtr=os.path.isdir,
        mapper=os.path.basename)


def get_analysis_names():
    """gets all available analysis metrics
    :returns: a list of names of analysis method
    """
    return ls(
        os.path.join(
            *analysis_dir),
        filtr=os.path.isdir,
        mapper=os.path.basename)


def read_image(path):
    """read an image

    :path: the path to the image
    :returns: the image as a PIL.Image object

    """
    return Image.open(path)


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
            if verbose:
                click.echo(f"image at {path} exists, not overriding")
            return
        else:
            if verbose:
                click.echo(f"overriding image at {path}")
    for p in post_processors:
        image = p(image)
    image.save(path)
    if verbose:
        click.echo(f"successfully write to {path}")


def get_existing_path(path, extensions=['jpg', 'jpeg', 'png']):
    """

    :path: the path to a file
    :extensions: an array specifying alternative extensions to use when the given path is not available
    :returns: the resolved path, None if failed to resolve the image

    """
    path_root = os.path.splitext(path)[0]
    options = [path] + [path_root + os.extsep + ext for ext in extensions]
    for option in options:
        if os.path.isfile(option):
            return option
    return None


def rm(path, dryrun=False, verbose=True):
    """ remove the file, or recursively remove directories

    :path: the path to the file or directory
    :dryrun: don't actually remove the file
    :verbose: print out files/directories that will be removed
    :returns: None

    """
    # helper function
    def _rm(item, is_file=False):
        if verbose:
            click.echo(item)
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
        if rmself:
            _rm(path, is_file=False)
    else:
        raise ValueError(f"{path} does not point to a file or directory")


# --- transform utilities


def read_orig(category):
    """read the original image for a certain category

    :category: the category to be read
    :returns: the Image object

    """
    orig_path = get_existing_path(os.path.join(*image_dir, category, 'orig'))
    if not orig_path:
        raise ModuleError(f"no orig image found in category {category}")
    orig = read_image(orig_path)
    return orig


def transform_image(image, transformation, level):
    """ transforms an image
    :image: the image to be transformed
    :transformation: transformation name. E.g. rotate
    :level: integer from 1 to 9
    :returns: the transformed image
    """
    if transformation not in get_transformation_names():
        raise ValueError(
            f"transformation with name {transformation} is not available")
    mod = importlib.import_module(
        '.'.join([*transformation_dir, transformation]))
    transform = getattr(mod, 'transform', None)
    if not transform:
        raise ModuleError(
            f"no transform function implemented in transformation module {transformation}")
    new_image = transform(image, level)
    return new_image


def transform_image_by_category(
        category,
        transformation,
        levels=range(11),
        extension='jpg',
        override=True,
        verbose=True,
        post_processors=[]):
    """ transform the image of a certain category

    :category: the category to be transformed, assumes that it is a valid category
    :transformation: the transformation to apply
    :levels: an iterable of integers
    :extension: the extension of the output file
    :returns: None

    """
    orig = read_orig(category)
    for level in levels:
        out = transform_image(orig, transformation, level)
        out_path = os.path.join(*image_dir, category, transformation)
        os.makedirs(out_path, exist_ok=True)
        out_path = os.path.join(
            out_path,
            f"level_{level}" +
            os.extsep +
            extension)
        write_image(
            out,
            out_path,
            post_processors=post_processors,
            override=override,
            verbose=verbose)

# --- info utilities


def plist(lst, indent="", sep="\n"):
    """print a list
    :lst: the list to print
    :indent: characters to append before each item
    :sep: characters used to separate items
    """
    s = sep.join([indent + item for item in lst])
    click.echo(s)

# --- commands


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

# --- transform commands


@transform.command()
@click.option("-c",
              "--category",
              "categories",
              default=get_image_category_names(),
              multiple=True,
              callback=validate_image_categories)
@click.option("-t",
              "--transformation",
              "transformations",
              default=get_transformation_names(),
              multiple=True,
              callback=validate_transformations)
@click.option("--override/--no-override", default=True)
@click.option("--verbose/--silent", default=True)
@click.option("--circle/--no-circle", "circle", default=True)
def all(categories, transformations, verbose, override, circle):
    """ transform all existing images with all available transformations
    if category is given, transform only the specified categories
    if transformation is given, transform with only the specified transformations
    """
    print("categories: {}".format(categories))
    print("transformations: {}".format(transformations))
    post_processors = []
    if circle:
        post_processors.append(crop_to_circle)

    for category in categories:
        # generate the unmodified reference image
        orig = read_orig(category)
        out_path = os.path.join(*image_dir, category, "output.jpg")
        write_image(
            orig,
            out_path,
            post_processors=post_processors,
            override=override,
            verbose=verbose)

        for transformation in transformations:
            transform_image_by_category(
                category,
                transformation,
                post_processors=post_processors,
                override=override,
                verbose=verbose)


@transform.command()
@click.option("-c",
              "--category",
              "categories",
              default=get_image_category_names(),
              multiple=True,
              callback=validate_image_categories)
@click.option("-t",
              "--transformation",
              "transformations",
              default=get_transformation_names(),
              multiple=True,
              callback=validate_transformations)
@click.option("--dryrun/--no-dryrun", default=False)
@click.option("--verbose/--silent", default=True)
def clean(categories, transformations, dryrun, verbose):
    """ clean transformed images """
    for category in categories:
        output_path = os.path.join(*image_dir, category, "output.jpg")
        if os.path.isfile(output_path):
            rm(output_path, dryrun=dryrun, verbose=verbose)
        for transformation in transformations:
            transformation_path = os.path.join(
                *image_dir, category, transformation)
            if os.path.isdir(transformation_path):
                rm(path, dryrun=dryrun, verbose=verbose)

# --- analyze commands

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
