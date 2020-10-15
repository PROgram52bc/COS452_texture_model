#!/usr/bin/env python
import click
import os
from PIL import Image
from fpdf import FPDF

from src.etc.utilities import pif, plist, rm
from src.etc.pdf import lay_images
from src.etc.consts import ROOT_DIR, image_dir, metric_sorted_data_dir, printable_dir
from src.etc.structure import validate_image_categories, validate_transformations, get_image_category_names, get_transformation_names, get_metric_names, read_level_image_paths
from src.commands.transform import create_transform_cli 
from src.commands.analyze import create_analyze_cli 



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



cli = click.Group()
create_transform_cli(cli)
create_analyze_cli(cli)


@cli.group(help="Show information related to various modules")
def info():
    pass



@cli.group(help="Generate printable documents")
def printable():
    pass


@cli.group(help="Clean up generated data")
def clean():
    pass


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
