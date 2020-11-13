import click
import os
import csv
import numpy
import importlib
from scipy.stats import spearmanr

from src.etc.exceptions import ModuleError
from src.etc.utilities import pif, ls, csv_filter, read_csv
from src.etc.structure import get_image_category_names, get_transformation_names, get_metric_names, get_agent_names, agent2file, read_output, read_level_images, get_level_numeric
from src.etc.consts import ROOT_DIR, analysis_dir, metric_sorted_data_dir, human_sorted_data_dir, ranked_data_dir, csv_subfield_delim


def rank_standard(f, agents, categories, transformations, override, verbose):
    """ calculate spearman's rank of each category + transformation with each agent.
    comparisons are made against the standard order as listed in the header of each csv file (0-10),

    :f: the file to be written into
    :agents: the agents to be considered
    :categories: the categories to be considered
    :transformations: the transformations to be considered
    :override: override existing files
    :verbose: print output regarding writing status
    :returns: None

    """
    writer = csv.writer(f)
    # The header line
    writer.writerow([
        'agent',
        'category',
        'transformation',
        'coefficient',
        'p-value'
    ])
    for agent in agents:
        # set up data file path for the agent
        csv_file = agent2file(agent)
        if not csv_filter(csv_file):
            pif(verbose,
                f"{csv_file} does not exist, use the 'decode' command to generate sorted data.")
            continue
        pif(verbose, f"calculating ranks for {agent}...")
        # read file
        # the header row and array of data rows
        header, *sorted_data = read_csv(csv_file)
        # TODO: split category_transformation into two separate fields
        # <2020-11-13, David Deng> #
        for category_transformation, *order in sorted_data:
            # get the reference order from the header row
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
            r, p = spearmanr(reference_order, order)  # calculate spm-rank
            writer.writerow([
                agent,
                category,
                transformation,
                str(numpy.round(r, decimals=3)),
                str(numpy.round(p, decimals=3))])

def mean_order(*orders):
    """calculate the mean ordering of several orderings

    :*orders: lists that contains the same elements but in different orders
    :returns: a list representing the mean (average) order
    """
    # FIXME: When an even number of orders is evaluated, a tie might occur
    # <2020-10-28, David Deng> #
    rank = {}
    for order in orders:
        for index, item in enumerate(order):
            # collect the index (ranking) for each item
            rank.setdefault(item, 0)
            rank[item] += index
    return sorted(rank.keys(), key=lambda e: rank[e])


# TODO: change analyze to data?  <2020-11-13, David Deng> #
def create_analyze_cli(cli):
    analyze = click.Group(
        'analyze',
        help="Analyze transformed images with available metrics")

    @click.option("-c",
                  "--category",
                  "categories",
                  default=get_image_category_names(),
                  multiple=True,
                  type=click.Choice(get_image_category_names()))
    @click.option("-t",
                  "--transformation",
                  "transformations",
                  default=get_transformation_names(),
                  multiple=True,
                  type=click.Choice(get_transformation_names()))
    @click.option("-m",
                  "--metrics",
                  "metrics",
                  default=get_metric_names(),
                  multiple=True,
                  type=click.Choice(get_metric_names()))
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

    @click.option("-a",
                  "--agents",
                  "agents",
                  default=get_agent_names(),
                  multiple=True,
                  type=click.Choice(get_agent_names()))
    @click.option("-c",
                  "--category",
                  "categories",
                  default=get_image_category_names(),
                  multiple=True,
                  type=click.Choice(get_image_category_names()))
    @click.option("-t",
                  "--transformation",
                  "transformations",
                  default=get_transformation_names(),
                  multiple=True,
                  type=click.Choice(get_transformation_names()))
    @click.option("--override/--no-override", default=True)
    @click.option("--verbose/--silent", default=True)
    @analyze.command()
    def rank(agents, categories, transformations, override, verbose):
        """ Calculate spearmanrank and p-value for each metric and transformation"""
        path = os.path.join(ROOT_DIR, *ranked_data_dir)
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, "rank.csv")
        if os.path.isfile(file_path) and not override:
            pif(verbose, f"file at {file_path} exists, skipping...")
            return
        with open(file_path, "w", newline='') as f:
            rank_standard(
                f,
                agents,
                categories,
                transformations,
                override,
                verbose)
        pif(verbose, f"data written into {file_path}")
    cli.add_command(analyze)
