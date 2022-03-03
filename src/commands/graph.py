import click
import os
import csv
import PyGnuplot as gp
from src.etc.consts import graph_dir, ranked_data_dir, agent_name_delim
from src.etc.utilities import read_csv

graphs = {
        "human_hist": {
            "description": "A clustered histogram with human data",
            "title": "Ranking Results of Human Participants",
            "get_data": get_human_hist_data,
            "commands": """
set terminal pngcairo noenhanced font "arial,10" fontscale 1.0 size 600, 400 
set output 'human_hist.2.png'
set boxwidth 0.9 absolute
set style fill solid 1.00 border lt -1
set key fixed right top vertical Right noreverse noenhanced autotitle nobox
set style histogram title textcolor lt -1
set style data histograms
set xtics ()
set title "Ranking Results of Human Participants" 
set ylabel "Number of successful rankings"
set arrow nohead from graph 0,first 15 to graph 1,first 15 # add a horizontal line
set yrange [ 0 : 16 ] noreverse writeback # set the maximum for y axis
plot 'graphs/human_hist.dat' using 2:xtic(1) title "Human"
"""
        }
}

def get_human_hist_data():
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
    data = list(zip(*transformations.items()))

def create_graph_cli(cli):
    graph = click.Group('graph', help="Generate graphs based on data")

    # TODO: use pre-defined name and algorithm to generate data <2020-11-18, David Deng> #
    # TODO: run the gnuplot script all together? <2020-11-18, David Deng> #
    @click.option("-n", "--plot-name", default="clustered_hist",
            type=click.Choice(["clustered_hist", "human_hist"]),
            help="the name of the pre-defined plot")
    @graph.command('plot')
    def plot_command(plot_name):
        """ Generate plot data files.  """
        output_data_path = os.path.join(*graph_dir, f"{plot_name}.dat")
        output_graph_path = os.path.join(*graph_dir, f"{plot_name}.png")
        if plot_name == "clustered_hist":
            metrics = {}
            # transformations = ['metric']
            # for row in read_csv(os.path.join(*ranked_data_dir, "rank.csv"), reader=csv.DictReader):
            #     agent_type, agent_name = row['agent'].split(agent_name_delim)
            #     # have different way of collecting?  <2020-11-18, David Deng> #
            #     transformation = row['transformation']
            #     p_value = float(row['p-value'])
            #     if agent_type == 'metrics':
            #         metrics.setdefault(agent_name, {}) # for the metric, collect successful numbers for each transformation
            #         metrics[agent_name].setdefault(transformation, 0) # start count at 0
            #         if transformation not in transformations:
            #             transformations.append(transformation)
            #         if p_value < 0.05:
            #             metrics[agent_name][transformation] += 1
            # writer = csv.DictWriter(output_file, fieldnames=transformations)
            # writer.writeheader()
            # for metric_name, metric_data in metrics.items():
            #     writer.writerow({ 'metric': metric_name, **metric_data })
        elif plot_name == 'human_hist':
            gp.s(data, output_data_path)
            for command in graphs['human_hist']['commands'].strip().split("\n"):
                gp.c(command)
        else:
            raise NotImplementedError("Other plots are not implemented")

        click.echo(f"Data written to: {output_data_path}")

    cli.add_command(graph)
