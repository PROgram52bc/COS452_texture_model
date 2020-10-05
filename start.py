#!/usr/bin/env python
import click
import os
import re
import csv
import importlib  # for dynamic import
from PIL import Image
from fpdf import FPDF

from src.utils.helpers import crop_to_circle, add_orientation_marker
from src.utils.pdf import lay_images

# --- constants

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

transformation_dir = ['src', 'transformations']
analysis_dir = ['src', 'analysis']
image_dir = ['images']
analysis_data_dir = ['data', 'metrics']
printable_dir = ['printables']
image_extensions = ['jpg', 'jpeg', 'png']

# --- exceptions


class ModuleError(Exception):
    """ when a module is not implemented according to the specification """
    pass

# --- utilities


def pif(verbose, msg):
    """print if verbose

    :verbose: boolean indicating whether or not to print
    :msg: message to be printed
    :returns: None

    """
    if verbose:
        click.echo(msg)


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


def validate_metrics(ctx, param, value):
    """ makes sure that the given image transformations are valid """
    invalid_metrics = set(value) - set(get_metric_names())
    if invalid_metrics:
        raise ValueError(
            f"Invalid image analysis names: {invalid_metrics}")
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


def directory_filter(d):
    return os.path.isdir(d) and not os.path.basename(d).startswith('_')


def get_image_category_names():
    """gets all existing image categories
    :returns: a list of category names
    """
    return ls(
        os.path.join(
            *image_dir),
        filtr=directory_filter,
        mapper=os.path.basename)


def get_transformation_names():
    """gets all available transformations
    :returns: a list of names of transformation
    """
    return ls(
        os.path.join(
            *transformation_dir),
        filtr=directory_filter,
        mapper=os.path.basename)


def get_metric_names():
    """gets all available analysis metrics
    :returns: a list of names of analysis method
    """
    return ls(
        os.path.join(
            *analysis_dir),
        filtr=directory_filter,
        mapper=os.path.basename)


def read_image(path):
    """read an image

    :path: the path to the image
    :returns: the image as a PIL.Image object

    """
    return Image.open(path)


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


def read_output(category):
    """read the output reference image for a certain category

    :category: the category to be read
    :returns: the Image object

    """
    output_path = get_existing_path(
        os.path.join(*image_dir, category, 'output'))
    if not output_path:
        raise ModuleError(f"no output image found in category {category}")
    output = read_image(output_path)
    return output


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


def get_existing_path(path, extensions=image_extensions):
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


def read_level_image_paths(category, transformation):
    """read the transformed image for a certain category

    :category: the category to be read
    :transformation: the specific transformation
    :returns: an array of image paths that exist

    """
    base_path = os.path.join(*image_dir, category, transformation)
    level_paths = [
        get_existing_path(
            os.path.join(
                base_path,
                f"level_{level:02}")) for level in range(
            0,
            11)]
    return list(filter(None, level_paths))


def read_level_images(category, transformation):
    """read the transformed image for a certain category

    :category: the category to be read
    :transformation: the specific transformation
    :returns: an array of image objects

    """
    return [
        read_image(path) for path in read_level_image_paths(
            category,
            transformation)]


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


# --- transform utilities


def transform_image(image, transformation, level):
    """ transforms an image
    :image: the image to be transformed
    :transformation: transformation name. E.g. rotate
    :level: integer from 0 to 10
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
            f"level_{level:02}" +
            os.extsep +
            extension)
        write_image(
            out,
            out_path,
            post_processors=post_processors,
            override=override,
            verbose=verbose)

# --- analyze utilities


def get_level_numeric(filename):
    """get the numeric level from filename

    :filename: the file name of the level image. E.g. '.../level_00.jpg'
    :returns: an integer representing the transformed level

    """
    match = re.search(
        rf"level_(\d+)\.(?:{'|'.join(image_extensions)})$",
        filename)
    if not match:
        raise ValueError(f"No numeric level found in filename {filename}")
    return int(match.group(1))

# --- printable utilities


def generate_pdf(category, transformation, verbose):
    """generate pdf file with transformed images

    :category: the category of image
    :transformation: the transformation to be used
    :returns: None

    """
    # read available images
    image_paths = read_level_image_paths(category, transformation)
    if len(image_paths) == 0:
        pif(verbose, f"Skip {category}, {transformation}, no level images found")
        return None
    # generate pdf
    pdf = FPDF(orientation="L", unit="pt", format="letter")
    pdf.set_auto_page_break(False)
    pdf.set_margins(20, 20, 20)
    pdf.set_font('Arial', 'B', 20)
    pdf.add_page()
    pdf.cell(
        pdf.w,
        30,
        f"Category: {category}; Transformation: {transformation}",
        border=0,
        ln=1,
        align="C")
    pdf.set_font('Arial', '', 10)
    pdf.cell(
        pdf.w,
        30,
        f"Images to be sorted first from left to right, then from top to bottom. From level_0 to level_10",
        border=0,
        ln=1,
        align="C")
    lay_images(pdf, image_paths, width=240, space=10)
    output_path = os.path.join(
        *printable_dir, f"{category}_{transformation}.pdf")
    pdf.output(output_path)
    pif(verbose, f"File written to {output_path}")


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


@cli.group(help="Show information related to various modules")
def info():
    pass


@cli.group(help="Transform images using available transformations")
def transform():
    pass


@cli.group(help="Analyze transformed images with available metrics")
def analyze():
    pass


@cli.group(help="Generate printable documents")
def printable():
    pass

# --- transform commands


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
@click.option("--orientation-mark/--no-orientation-mark",
              "orientation", default=True)
@transform.command('all')
def transform_all(categories, transformations, verbose, override, circle, orientation):
    """ Transform all existing images with all available transformations.

    if category is given, transform only the specified categories
    if transformation is given, transform with only the specified transformations
    by default, images will be cropped into a circle, can override this behavior with --no-circle
    if images are cropped, an orientation mark will by default be added, override this behavior with --no-orientation-mark
    """
    post_processors = []
    if circle:
        post_processors.append(crop_to_circle)
        if orientation:
            post_processors.append(add_orientation_marker)

    for category in categories:
        pif(verbose, f"Processing category {category}...")
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
            pif(verbose, f"Transforming with {transformation}...")
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
        # remove the reference output image
        output_path = os.path.join(*image_dir, category, "output.jpg")
        if os.path.isfile(output_path):
            rm(output_path, dryrun=dryrun, verbose=verbose)
        # remove images under each transformation
        for transformation in transformations:
            transformation_path = os.path.join(
                *image_dir, category, transformation)
            if os.path.isdir(transformation_path):
                rm(transformation_path, dryrun=dryrun, verbose=verbose)

# --- analyze commands


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
@click.option("-m",
              "--metrics",
              "metrics",
              default=get_metric_names(),
              multiple=True,
              callback=validate_metrics)
@click.option("--override/--no-override", default=True)
@click.option("--verbose/--silent", default=True)
@analyze.command()
def sort(categories, transformations, metrics, override, verbose):
    """sort the generated images by comparing them with output.jpg """
    os.makedirs(os.path.join(*analysis_data_dir), exist_ok=True)
    for metric in metrics:
        # import the metric module
        mod = importlib.import_module(
            '.'.join([*analysis_dir, metric]))
        Analyzer = getattr(mod, 'Analyzer', None)
        if not Analyzer:
            raise ModuleError(
                f"no analyzer class implemented in metric {metric}")
        analyzer = Analyzer()
        pif(verbose, f"sorting images with {metric}...")
        # check if file exists
        path = os.path.join(*analysis_data_dir, f"{metric}.csv")
        if os.path.isfile(path) and not override:
            pif(verbose, f"file at {path} exists, skipping...")
            continue
        with open(os.path.join(*analysis_data_dir, f"{metric}.csv"), 'w') as data_file:
            writer = csv.writer(data_file)
            writer.writerow(['dataset', *range(11)])  # header row
            for category in categories:
                try:
                    orig = read_output(category)
                except ModuleError as e:
                    pif(verbose, e)
                    pif(verbose, f"Skipping category {category}...")
                    continue
                for transformation in transformations:
                    images = read_level_images(category, transformation)
                    if not images:
                        pif(verbose, f"no level images in {category}_{transformation}, skipping...")
                        continue
                    images = analyzer.sort(images, orig)  # sorted image
                    order = [get_level_numeric(image.filename)
                             for image in images]
                    writer.writerow([f"{category}_{transformation}", *order])
        pif(verbose, f"data written to {path}")


# --- printable commands

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
@click.option("--verbose/--silent", default=True)
@printable.command('all')
def printable_all(categories, transformations, verbose):
    """ generate printable files with the transformed images """
    os.makedirs(os.path.join(*printable_dir), exist_ok=True)
    for category in categories:
        for transformation in transformations:
            # read available level images
            pif(verbose, f"Generating printable for {category}, {transformation}...")
            generate_pdf(category, transformation, verbose)


@click.option("--dryrun/--no-dryrun", default=False)
@click.option("--verbose/--silent", default=True)
@printable.command()
def clean(dryrun, verbose):
    """ clean generated printable files """
    path = os.path.join(*printable_dir)
    if os.path.isdir(path):
        rm(path, dryrun=dryrun, verbose=verbose)


# --- info commands


@info.command('all')
def info_all():
    click.echo("Image categories:")
    plist(get_image_category_names(), indent="\t")
    click.echo("Transformations:")
    plist(get_transformation_names(), indent="\t")
    click.echo("Analyses:")
    plist(get_metric_names(), indent="\t")


if __name__ == '__main__':
    cli()
