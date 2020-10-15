import click
from src.etc.utilities import plist
from src.etc.structure import get_image_category_names, get_transformation_names, get_metric_names

def create_info_cli(cli):
    info = click.Group('info', help="Show information related to various modules")

    @info.command('all')
    def info_all():
        click.echo("Image categories:")
        plist(get_image_category_names(), indent="\t")
        click.echo("Transformations:")
        plist(get_transformation_names(), indent="\t")
        click.echo("Analyses:")
        plist(get_metric_names(), indent="\t")

    cli.add_command(info)
