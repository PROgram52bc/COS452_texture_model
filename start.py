#!/usr/bin/env python
import click
import os
import re
import csv
import numpy
import importlib  # for dynamic import
from scipy.stats import spearmanr
from PIL import Image
from fpdf import FPDF

from src.utils.helpers import crop_to_circle, add_orientation_marker
from src.utils.pdf import lay_images

# --- constants

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

transformation_dir = ['src', 'transformations']
analysis_dir = ['src', 'analysis']
image_dir = ['images']
sorted_data_dir = ['data', 'sort']
metric_sorted_data_dir = [*sorted_data_dir, 'metrics']
human_sorted_data_dir = [*sorted_data_dir, 'humans']
ranked_data_dir = ['data', 'rank']
printable_dir = ['printables']
image_extensions = ['jpg', 'jpeg', 'png']

csv_subfield_delim = '#'  # delimiter for subfields in csv
agent_name_delim = '-'  # delimiter for separating agent type from agent name

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
    return list(items)


def directory_filter(d):
    """ returns True if 'd' is a valid directory, False otherwise """
    return os.path.isdir(d) and not os.path.basename(d).startswith('_')


def csv_filter(f):
    """ returns True if 'f' is a valid csv file, False otherwise """
    return os.path.isfile(f) and os.path.splitext(f)[1] == '.csv'


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


def read_csv(path):
    """read csv file as a list of rows

    :path: path to the csv file
    :returns: the list of rows in the csv file

    """
    with open(path, newline='') as f:
        return list(csv.reader(f))


def agent2file(agent):
    """convert an agent name to file path

    :agent: the agent name, in the form of (humans|metrics)#name
    :returns: the file name corresponding to the agent

    """
    return os.path.join(
        *sorted_data_dir,
        *agent.split(agent_name_delim),
        os.extsep,
        'csv')


def file2agent(filename):
    """convert a csv filename to an agent name

    :filename: the csv filename
    :returns: the agent name in the form of (humans|metrics)#name

    """
    head, tail = os.path.split(filename)
    agent_type = os.path.split(head)[1]
    agent_name = os.path.splitext(tail)[0]
    return agent_name_delim.join([agent_type, agent_name])


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


def rank_standard(f, categories, transformations, override, verbose):
    """ calculate spearman's rank for each category + transformation with each metrics.
    comparisons are made against the standard order (0-10),

    :f: the file to be written into
    :categories: the categories to be considered
    :transformations: the transformations to be considered
    :override: override existing files
    :verbose: print output regarding writing status
    :returns: None

    """
    rows = []
    fieldnames = ['agent']
    # read the sorted data according to each agent (metrics or human)
    # can add a filter later to read only certain agents
    # need a way to name metrics and human agents uniformly
    for csv_file in (ls(os.path.join(*metric_sorted_data_dir),
                        filtr=csv_filter) + ls(os.path.join(*human_sorted_data_dir),
                                               filtr=csv_filter)):
        # set up agent name
        row_r = {}  # row for coefficient
        row_p = {}  # row for p_value
        agent = file2agent(csv_file)
        row_r['agent'] = csv_subfield_delim.join([agent, 'r'])
        row_p['agent'] = csv_subfield_delim.join([agent, 'p'])
        pif(verbose, f"calculating ranks for {agent}...")
        # read file
        with open(csv_file, newline='') as input_file:
            reader = csv.reader(input_file)
            header, *sorted_data = list(reader)
        for category_transformation, *order in sorted_data:
            # discard the label at the first column
            reference_order = header[1:]
            category, transformation = category_transformation.split(
                csv_subfield_delim)
            # filter category and transformation
            if category not in categories:
                pif(verbose,
                    f"Category {category} not specified, skipping {category}, {transformation}...")
                continue
            if transformation not in transformations:
                pif(verbose,
                    f"Transformation {transformation} not specified, skipping {category}, {transformation}...")
                continue
            if category_transformation not in fieldnames:
                # add field name if encountering a new one
                fieldnames.append(category_transformation)
            r, p = spearmanr(reference_order, order)  # calculate spm-rank
            # cell = csv_subfield_delim.join(map(lambda v: str(numpy.round(v,
            # decimals=3)), result)) # combine coefficient and p_value into a
            # single cell
            row_r[category_transformation] = str(numpy.round(r, decimals=2))
            row_p[category_transformation] = str(numpy.round(p, decimals=3))

        rows.append(row_r)
        rows.append(row_p)
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


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
        pif(verbose,
            f"Skip {category}, {transformation}, no level images found")
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


@cli.group(help="Clean up generated data")
def clean():
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
def transform_all(
        categories,
        transformations,
        verbose,
        override,
        circle,
        orientation):
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
    os.makedirs(os.path.join(*metric_sorted_data_dir), exist_ok=True)
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
        path = os.path.join(*metric_sorted_data_dir, f"{metric}.csv")
        if os.path.isfile(path) and not override:
            pif(verbose, f"file at {path} exists, skipping...")
            continue
        with open(os.path.join(*metric_sorted_data_dir, f"{metric}.csv"), 'w', newline='') as data_file:
            writer = csv.writer(data_file)
            writer.writerow([csv_subfield_delim.join(
                ['CATEGORY', 'TRANSFORMATION']), *range(11)])  # header row
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
                        pif(verbose,
                            f"no level images in {category}_{transformation}, skipping...")
                        continue
                    images = analyzer.sort(images, orig)  # sorted image
                    order = [get_level_numeric(image.filename)
                             for image in images]
                    writer.writerow([csv_subfield_delim.join(
                        [category, transformation]), *order])
        pif(verbose, f"data written to {path}")


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
@click.option("--mode",
              type=click.Choice(['standard',
                                 'human']),
              default="standard",
              help="'standard' mode will rank against the normal ordering (0-10), while 'human' mode will rank against human ratings")
@click.option("--override/--no-override", default=True)
@click.option("--verbose/--silent", default=True)
@analyze.command()
def rank(categories, transformations, mode, override, verbose):
    """ Calculate spearmanrank and p-value for each metric and transformation"""
    path = os.path.join(*ranked_data_dir)
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, f"{mode}.csv")
    if os.path.isfile(file_path) and not override:
        pif(verbose, f"file at {file_path} exists, skipping...")
        return
    with open(file_path, "w", newline='') as f:
        if mode == 'standard':
            rank_standard(f, categories, transformations, override, verbose)
        else:
            pass
    pif(verbose, f"data written into {file_path}")

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
            pif(verbose,
                f"Generating printable for {category}, {transformation}...")
            generate_pdf(category, transformation, verbose)


# --- info commands


@info.command('all')
def info_all():
    click.echo("Image categories:")
    plist(get_image_category_names(), indent="\t")
    click.echo("Transformations:")
    plist(get_transformation_names(), indent="\t")
    click.echo("Analyses:")
    plist(get_metric_names(), indent="\t")


# --- clean commands

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
@clean.command('transform')
def transform_clean(categories, transformations, dryrun, verbose):
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


@click.option("--dryrun/--no-dryrun", default=False)
@click.option("--verbose/--silent", default=True)
@clean.command('sort')
def sort_clean(dryrun, verbose):
    """ clean sort data generated with the metrics. """
    path = os.path.join(*metric_sorted_data_dir)
    if os.path.isdir(path):
        rm(path, dryrun=dryrun, verbose=verbose)


@click.option("--dryrun/--no-dryrun", default=False)
@click.option("--verbose/--silent", default=True)
@clean.command('printable')
def printable_clean(dryrun, verbose):
    """ clean generated printable files """
    path = os.path.join(*printable_dir)
    if os.path.isdir(path):
        rm(path, dryrun=dryrun, verbose=verbose)


if __name__ == '__main__':
    cli()
