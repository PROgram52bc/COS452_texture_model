import click
import os
from src.etc.consts import ROOT_DIR, image_dir, metric_sorted_data_dir, printable_dir
from src.etc.structure import validate_image_categories, validate_transformations, get_image_category_names, get_transformation_names
from src.etc.utilities import rm


def create_clean_cli(cli):
    clean = click.Group('clean', help="Clean up generated data")

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
    cli.add_command(clean)
