import click
import random
import os
import json
from click import ClickException
from src.etc.utilities import plist, read_json, write_json, pif
from src.etc.consts import ROOT_DIR, sequence_data_dir, sequence_filename
from string import ascii_lowercase, ascii_uppercase

sequence_path = os.path.join(ROOT_DIR, *sequence_data_dir, sequence_filename)


def read_sequences():
    """read existing sequences from the sequence file
    :returns: a python object

    """
    if not os.path.isfile(sequence_path):
        return {}
    try:
        return read_json(
            os.path.join(
                ROOT_DIR,
                *sequence_data_dir,
                sequence_filename))
    except FileNotFoundError:
        return {}
    except json.decoder.JSONDecodeError as e:
        raise ClickException(
            f"invalid file structure in {sequence_filename}: {e}")


def decode_sequence(sequence_name, input_sequence):
    """ decode an ordering according to the specified existing sequence

    :sequence_name: the name of the existing sequence. If sequence_name does not exist, the input sequence is returned as is.
    :input_sequence: the given ordering encoded with sequence_name
    :returns: the output sequence consisting of integers starting from 0

    """
    pass


def write_sequences(sequences):
    """write sequences to the sequence file, will overwrite existing ones, so perform read_sequences first
    :returns: None
    """
    os.makedirs(os.path.join(ROOT_DIR, *sequence_data_dir), exist_ok=True)
    write_json(
        sequences,
        os.path.join(
            ROOT_DIR,
            *sequence_data_dir,
            sequence_filename))


def generate_random_sequence(
        count=10,
        set_name='Alpha',
        replacement=False,
        truncate=True):
    """ generate random sequence.

    :count: the number of items in the sequence
    :set_name: the character set to use in the sequence, default to upper case letters
    :replacement: choose with replacement, meaning items can be repetitive
    :truncate: truncate the population set to the first 'count' items in the set
    :returns: a list of items in the sequence

    For 'alpha' and 'Alpha' set, if count is greater than 26, an exception will be thrown
    Can enhance this feature by supporting sequence of arbitrary length using a permutation of two or more letters
    """
    if set_name == 'alpha':
        symbol_set = ascii_lowercase
    elif set_name == 'Alpha':
        symbol_set = ascii_uppercase
    elif set_name == 'numeric':
        symbol_set = range(count)
    else:
        raise ValueError(f"Invalid set name {set_name}")

    if not replacement and count > len(symbol_set):
        raise ClickException(
            "Count {count} is greater than the length of the symbol set {set_name} {len(symbol_set)}")
    if truncate:
        symbol_set = symbol_set[:count]

    if replacement:
        sample = random.choices(symbol_set, k=count)
    else:
        sample = random.sample(symbol_set, k=count)

    return sample


def create_sequence_cli(cli):
    sequence = click.Group(
        'sequence',
        help="Manage sequences used to encode human images")

    @click.option("-n", "--name", prompt="Enter the name of the sequence")
    @click.option("-c", "--count", default=10)
    @click.option("-s",
                  "--set",
                  "set_name",
                  required=True,
                  default='alpha',
                  type=click.Choice(['alpha', 'Alpha', 'numeric']))
    @click.option("-f", "--force", is_flag=True, default=False)
    @click.option("--replacement/--no-replacement",
                  default=False, help="choose with replacement")
    @click.option("--truncate/--no-truncate", default=True,
                  help="truncate the symbol set to the first 'count' symbols")
    @click.option("--verbose/--silent", default=True)
    @sequence.command('new')
    def new_sequence(
            name,
            count,
            set_name,
            force,
            replacement,
            truncate,
            verbose):
        sequences = read_sequences()
        if not force and name in sequences.keys():
            click.echo(
                f"{name} already exists in sequence data, choose another one or use --force to override")
            return
        sequence = generate_random_sequence(
            count, set_name, replacement, truncate)
        sequences[name] = sequence
        write_sequences(sequences)
        pif(verbose,
            f"Successfully added new sequence {name}: {','.join(sequence)}")

    @click.option("-n", "--name", "names", multiple=True)
    @sequence.command('list')
    def list_sequences(names):
        click.echo(f"Reading sequences from {sequence_path}")
        sequences = read_sequences()
        names = names or sequences.keys()
        if sequences:
            for sequence_name in sequences:
                if sequence_name in names:
                    click.echo(f"Sequence [{sequence_name}]:")
                    plist(sequences[sequence_name], sep=', ')
        else:
            click.echo("No sequence.")

    cli.add_command(sequence)
