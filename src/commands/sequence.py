import click
import random
from click import ClickException
from src.etc.utilities import plist
from string import ascii_lowercase, ascii_uppercase


def create_sequence_cli(cli):
    sequence = click.Group('sequence', help="Generate sequences")
    @click.option("-c", "--count", default=10)
    @click.option("-d",
                  "--delimiter",
                  default=",")
    @click.option("-s",
                  "--set",
                  "set_name",
                  required=True,
                  default='alpha',
                  type=click.Choice(['alpha', 'Alpha', 'numeric']))
    @click.option("--replacement/--no-replacement", default=False, help="choose with replacement")
    @click.option("--truncate/--no-truncate", default=False, help="truncate the symbol set to the first 'count' symbols")
    @sequence.command('random')
    def generate_random_sequence(count, delimiter, set_name, replacement, truncate):
        """ generate random sequence.

        For 'alpha' and 'Alpha' set, if count is greater than 26, an exception will be thrown
        """
        if set_name == 'alpha':
            symbol_set = ascii_lowercase
        elif set_name == 'Alpha':
            symbol_set = ascii_uppercase
        elif set_name == 'numeric':
            symbol_set = range(count)
        else:
            symbol_set = []

        if not replacement and count > len(symbol_set):
            raise ClickException("Count {count} is greater than the length of the symbol set {set_name} {len(symbol_set)}")
        if truncate:
            symbol_set = symbol_set[:count]

        if replacement:
            sample = random.choices(symbol_set, k=count)
        else:
            sample = random.sample(symbol_set, k=count)

        plist(sample, sep=delimiter)

    cli.add_command(sequence)
