import click
import os
import csv
import numpy
import importlib
from scipy.stats import spearmanr

from src.commands.sequence import decode_sequence
from src.etc.exceptions import ModuleError, SequenceError
from src.etc.utilities import pif, ls, is_csv, read_csv
from src.etc.structure import get_image_category_names, get_transformation_names, get_metric_names, get_agent_names, agent2file, read_output, read_level_images, get_level_numeric
from src.etc.consts import ROOT_DIR, analysis_dir, metric_sorted_data_dir, human_sorted_data_dir, ranked_data_dir, csv_subfield_delim, raw_sorted_data_dir, seq_num_formatter, plot_data_dir, agent_name_delim


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
        if not is_csv(csv_file):
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
            if categories and category not in categories:
                pif(verbose,
                    f"Category {category} not specified, skipping {category}, {transformation}...")
                continue
            if transformations and transformation not in transformations:
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
    # When an even number of orders is evaluated, a tie might occur
    # But this function is not currently used.
    # <2020-10-28, David Deng> #
    rank = {}
    for order in orders:
        for index, item in enumerate(order):
            # collect the index (ranking) for each item
            rank.setdefault(item, 0)
            rank[item] += index
    return sorted(rank.keys(), key=lambda e: rank[e])


def create_data_cli(cli):
    data = click.Group(
        'data',
        help="Process numerical data")

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
    @data.command()
    def sort(categories, transformations, metrics, override, verbose):
        """sort the generated images by comparing them with output.jpg """
        os.makedirs(
            os.path.join(
                ROOT_DIR,
                *metric_sorted_data_dir),
            exist_ok=True)
        for metric in metrics:
            pif(verbose, f"Metric: {metric}")
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
                # TODO: remove the subfield delimiter <2020-11-17, David Deng>
                writer.writerow([csv_subfield_delim.join(
                    ['CATEGORY', 'TRANSFORMATION']), *map(seq_num_formatter, range(11))])  # header row
                for category in categories:
                    try:
                        orig = read_output(category)
                    except ModuleError as e:
                        pif(verbose, e)
                        pif(verbose, f"Skipping category {category}...")
                        continue
                    for transformation in transformations:
                        pif(verbose,
                            f"category, transformation: {category},{transformation}...")
                        images = read_level_images(category, transformation)
                        if not images:
                            pif(verbose,
                                f"no level images in {category}_{transformation}, skipping...")
                            continue
                        images = analyzer.sort(images, orig)  # sorted image
                        order = [
                            seq_num_formatter(
                                get_level_numeric(
                                    image.filename))
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
    @click.option("-c", "--category", "categories", default=[], multiple=True,
                  help="a category filter, if not specified, all categories associated with the agent will be ranked")
    @click.option("-t", "--transformation", "transformations", default=[], multiple=True,
                  help="a transformation filter, if not specified, all transformations associated with the agent will be ranked")
    @click.option("--override/--no-override", default=True)
    @click.option("--verbose/--silent", default=True)
    @data.command()
    def rank(agents, categories, transformations, override, verbose):
        """ Calculate spearmanrank and p-value for each agent specified """
        path = os.path.join(ROOT_DIR, *ranked_data_dir)
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, "rank.csv")
        if os.path.isfile(file_path) and not override:
            pif(verbose, f"file at {file_path} exists, skipping...")
            return
        with open(file_path, "w", newline='') as f:
            rank_standard(
                f=f,
                agents=agents,
                categories=categories,
                transformations=transformations,
                override=override,
                verbose=verbose)
        pif(verbose, f"data written into {file_path}")

    @click.option("-a",
                  "--raw-file",
                  "file_names",
                  multiple=True,
                  type=click.Choice(ls(os.path.join(*raw_sorted_data_dir),
                                       filtr=is_csv,
                                       relative_to_cwd=False)),
                  default=ls(os.path.join(*raw_sorted_data_dir),
                             filtr=is_csv,
                             relative_to_cwd=False))
    @click.option("--verbose/--silent", default=True)
    @data.command('decode', help="decode raw data into human data")
    def decode_command(file_names, verbose):
        for file_name in file_names:
            input_path = os.path.join(*raw_sorted_data_dir, file_name)
            output_path = os.path.join(*human_sorted_data_dir, file_name)
            header_line, *rows = read_csv(input_path)
            with open(output_path, "w") as output_file:
                writer = csv.writer(output_file)
                pif(verbose, f"Decoding {file_name}...")
                writer.writerow(
                    [header_line[0], *map(seq_num_formatter, range(1, 11))])
                for sequence_name, *sequence in rows:
                    try:
                        writer.writerow(
                            [sequence_name, *decode_sequence(sequence_name, sequence)])
                    except SequenceError as e:
                        click.echo(
                            f"Sequence Error in {input_path}: {sequence_name}")
                        click.echo(e)
            pif(verbose,
                f"Successfully written decoded sequences into {output_path}")


    # TODO: use pre-defined name and algorithm to generate data <2020-11-18, David Deng> #
    # TODO: run the gnuplot script all together? <2020-11-18, David Deng> #
    @click.option("-n", "--plot-name", default="clustered_hist",
            help="the name of the pre-defined plot")
    @data.command('plot')
    def plot_command(plot_name):
        """ Generate plot data files.

        :plot_name: TODO
        :returns: TODO

        """
        output_path = os.path.join(*plot_data_dir, f"{plot_name}.dat")
        with open(output_path, "w") as output_file:
            if plot_name == "clustered_hist":
                metrics = {}
                transformations = ['metric']
            # example data
# OrderedDict([('agent', 'metrics-MSE'), ('category', 'dirt'), ('transformation', 'zoom'), ('coefficient', '0.973'), ('p-value', '0.0')])
# OrderedDict([('agent', 'metrics-MSE'), ('category', 'dirt'), ('transformation', 'rotate'), ('coefficient', '1.0'), ('p-value', '0.0')])
# OrderedDict([('agent', 'metrics-MSE'), ('category', 'tree_bark'), ('transformation', 'noise'), ('coefficient', '1.0'), ('p-value', '0.0')])
# OrderedDict([('agent', 'metrics-MSE'), ('category', 'tree_bark'), ('transformation', 'blur'), ('coefficient', '1.0'), ('p-value', '0.0')])
                for row in read_csv(os.path.join(*ranked_data_dir, "rank.csv"), reader=csv.DictReader):
                    agent_type, agent_name = row['agent'].split(agent_name_delim)
                    # have different way of collecting?  <2020-11-18, David Deng> #
                    transformation = row['transformation']
                    p_value = float(row['p-value'])
                    if agent_type == 'metrics':
                        metrics.setdefault(agent_name, {}) # for the metric, collect successful numbers for each transformation
                        metrics[agent_name].setdefault(transformation, 0) # start count at 0
                        if transformation not in transformations:
                            transformations.append(transformation)
                        if p_value < 0.05:
                            metrics[agent_name][transformation] += 1
                writer = csv.DictWriter(output_file, fieldnames=transformations)
                writer.writeheader()
                for metric_name, metric_data in metrics.items():
                    writer.writerow({ 'metric': metric_name, **metric_data })
            elif plot_name == 'human_hist':
                tmp_map = { 'n': 'noise', 'r': 'rotation', 'z': 'zoom', 'h': 'hue', 'b': 'blur' } # TODO: remove this dirty hack
                transformations = {}
                for row in read_csv(os.path.join(*ranked_data_dir, "rank.csv"), reader=csv.DictReader):
                    agent_type, agent_name = row['agent'].split(agent_name_delim)
                    p_value = float(row['p-value'])
                    if agent_type == 'humans':
                        transformation = tmp_map[row['transformation']] # TODO: remove this dirty hack
                        transformations.setdefault(transformation, 0) # start count at 0
                        if p_value < 0.05:
                            transformations[transformation] += 1
                writer = csv.writer(output_file)
                for transformation_name, count in transformations.items():
                    writer.writerow([transformation_name, count])
            else:
                raise NotImplementedError("Other plots are not implemented")

    cli.add_command(data)
