import click
import random
import os
import json
from click import ClickException
from src.etc.utilities import plist, read_json, write_json, pif
from src.etc.consts import ROOT_DIR, sequence_data_dir, sequence_filename
from string import ascii_lowercase, ascii_uppercase

sequence_path = os.path.join(ROOT_DIR, *sequence_data_dir, sequence_filename)
sequences_cache = {}


def read_sequences():
    """read existing sequences from the sequence file
    :returns: a python object, where the key is the name of the sequence, and value is the sequence as a list

    """
    global sequences_cache
    if sequences_cache:
        # print("returning from cache")
        return sequences_cache
    if not os.path.isfile(sequence_path):
        return {}
    try:
        # print("reading from file")
        sequences_cache = read_json(
            os.path.join(
                ROOT_DIR,
                *sequence_data_dir,
                sequence_filename))
        return sequences_cache
    except FileNotFoundError:
        return {}
    except json.decoder.JSONDecodeError as e:
        raise ClickException(
            f"invalid file structure in {sequence_filename}: {e}")


def read_sequence(sequence_name):
    """read a particular existing sequence

    :sequence_name: the name of the existing sequence. If sequence_name does not exist, the input sequence is returned as is. E.g. 'wheat_noise'
    :returns: the request sequence as list, None if doesn't exist

    """
    return read_sequences().get(sequence_name, None)


def decode_sequence(sequence_name, input_sequence):
    """ decode an ordering according to the specified existing sequence

    :sequence_name: the name of the existing sequence. If sequence_name does not exist, the input sequence is returned as is. E.g. 'wheat_noise'
    :input_sequence: the given ordering encoded with sequence_name
    :returns: the output sequence consisting of integers starting from 0

    """
    sequence_keys = read_sequence(sequence_name)
    if not sequence_keys:
        return input_sequence
    sequence_map = { key: index for index, key in enumerate(sequence_keys) }
    return [ sequence_map[key] for key in input_sequence ]


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
    # print("update cache")
    global sequences_cache
    sequences_cache = sequences


def write_sequence(sequence_name, sequence):
    """write a single sequence into the sequence collection.
    will overwrite existing sequence_name

    :sequence_name: the name of the sequence to be written
    :sequence: the actual sequence
    :returns: None

    """
    write_sequences({**read_sequences(), sequence_name: sequence})



def remove_sequence(sequence_name):
    """remove a sequence from the storage

    :sequence_name: the name of the sequence to be removed
    :returns: the sequence removed, None if sequence does not exist

    """
    sequences = read_sequences()
    removed = sequences.pop(sequence_name, None)
    write_sequences(sequences)
    return removed


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
        if not force and read_sequence(name):
            click.echo(
                f"{name} already exists in sequence data, choose another one or use --force to override")
            return
        sequence = generate_random_sequence(
            count, set_name, replacement, truncate)
        write_sequence(name, sequence)
        pif(verbose,
            f"Successfully added new sequence [{name}]: {', '.join(sequence)}")

    @click.option("-n", "--name", required=True)
    @click.option("-f", "--force", is_flag=True, default=False)
    @click.option("--verbose/--silent", default=True)
    @sequence.command('delete')
    def delete_sequence(name, force, verbose):
        if not read_sequence(name):
            click.echo(f"Sequence [{name}] does not exist")
            return
        elif not force:
            click.echo(f"Use --force to confirm action. Caution: This operation is not reversible")
            return
        sequence = remove_sequence(name)
        pif(verbose, f"Sequence [{name}] removed:\n{', '.join(sequence)}")


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
