import click
import os
import csv
import numpy
import importlib
from scipy.stats import spearmanr

from src.etc.exceptions import ModuleError
from src.etc.utilities import pif, ls, csv_filter
from src.etc.structure import validate_image_categories, validate_transformations, validate_metrics, get_image_category_names, get_transformation_names, get_metric_names, file2agent, read_output, read_level_images, get_level_numeric
from src.etc.consts import ROOT_DIR, analysis_dir, metric_sorted_data_dir, human_sorted_data_dir, ranked_data_dir, csv_subfield_delim


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


def create_analyze_cli(cli):
    analyze = click.Group(
        'analyze',
        help="Analyze transformed images with available metrics")

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
        os.makedirs(
            os.path.join(
                ROOT_DIR,
                *metric_sorted_data_dir),
            exist_ok=True)
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
            path = os.path.join(
                ROOT_DIR,
                *metric_sorted_data_dir,
                f"{metric}.csv")
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
                rank_standard(
                    f,
                    categories,
                    transformations,
                    override,
                    verbose)
            else:
                pass
        pif(verbose, f"data written into {file_path}")
    cli.add_command(analyze)
