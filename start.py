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

from src.etc.postprocessors import crop_to_circle, add_orientation_marker
from src.etc.utilities import pif, plist, ls, rm, read_csv, read_image, write_image, directory_filter, csv_filter
from src.etc.exceptions import ModuleError
from src.etc.pdf import lay_images
from src.etc.consts import ROOT_DIR, transformation_dir, analysis_dir, image_dir, metric_sorted_data_dir, human_sorted_data_dir, ranked_data_dir, printable_dir, image_extensions, csv_subfield_delim
from src.etc.structure import validate_image_categories, validate_transformations, validate_metrics, get_image_category_names, get_transformation_names, get_metric_names, agent2file, file2agent, read_orig, read_output, get_existing_path, read_level_image_paths, read_level_images, get_level_numeric

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
        out_dir = os.path.join(ROOT_DIR, *image_dir, category, transformation)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(
            out_dir,
            f"level_{level:02}" +
            os.extsep +
            extension)
        # skip image computation if not overriding existing image
        if os.path.isfile(out_path) and not override:
            pif(verbose, f"skip image at {out_path}")
            continue
        out = transform_image(orig, transformation, level)
        write_image(
            out,
            out_path,
            post_processors=post_processors,
            verbose=verbose)

# --- analyze utilities


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
    for csv_file in (ls(os.path.join(ROOT_DIR,
                                     *metric_sorted_data_dir),
                        filtr=csv_filter) + ls(os.path.join(ROOT_DIR,
                                                            *human_sorted_data_dir),
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
        ROOT_DIR, *printable_dir, f"{category}_{transformation}.pdf")
    pdf.output(output_path)
    pif(verbose, f"File written to {output_path}")

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
        out_path = os.path.join(ROOT_DIR, *image_dir, category, "output.jpg")
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
    os.makedirs(os.path.join(ROOT_DIR, *metric_sorted_data_dir), exist_ok=True)
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
        path = os.path.join(ROOT_DIR, *metric_sorted_data_dir, f"{metric}.csv")
        if os.path.isfile(path) and not override:
            pif(verbose, f"file at {path} exists, skipping...")
            continue
        with open(os.path.join(ROOT_DIR, *metric_sorted_data_dir, f"{metric}.csv"), 'w', newline='') as data_file:
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
    path = os.path.join(ROOT_DIR, *ranked_data_dir)
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
    os.makedirs(os.path.join(ROOT_DIR, *printable_dir), exist_ok=True)
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
        output_path = os.path.join(
            ROOT_DIR, *image_dir, category, "output.jpg")
        if os.path.isfile(output_path):
            rm(output_path, dryrun=dryrun, verbose=verbose)
        # remove images under each transformation
        for transformation in transformations:
            transformation_path = os.path.join(
                ROOT_DIR, *image_dir, category, transformation)
            if os.path.isdir(transformation_path):
                rm(transformation_path, dryrun=dryrun, verbose=verbose)


@click.option("--dryrun/--no-dryrun", default=False)
@click.option("--verbose/--silent", default=True)
@clean.command('sort')
def sort_clean(dryrun, verbose):
    """ clean sort data generated with the metrics. """
    path = os.path.join(ROOT_DIR, *metric_sorted_data_dir)
    if os.path.isdir(path):
        rm(path, dryrun=dryrun, verbose=verbose)


@click.option("--dryrun/--no-dryrun", default=False)
@click.option("--verbose/--silent", default=True)
@clean.command('printable')
def printable_clean(dryrun, verbose):
    """ clean generated printable files """
    path = os.path.join(ROOT_DIR, *printable_dir)
    if os.path.isdir(path):
        rm(path, dryrun=dryrun, verbose=verbose)


if __name__ == '__main__':
    cli()
