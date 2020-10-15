#!/usr/bin/env python
import click
import os

from src.commands.transform import create_transform_cli
from src.commands.analyze import create_analyze_cli
from src.commands.printable import create_printable_cli
from src.commands.info import create_info_cli
from src.commands.clean import create_clean_cli
from src.commands.sequence import create_sequence_cli


cli = click.Group()
create_transform_cli(cli)
create_analyze_cli(cli)
create_printable_cli(cli)
create_info_cli(cli)
create_clean_cli(cli)
create_sequence_cli(cli)

if __name__ == '__main__':
    cli()
