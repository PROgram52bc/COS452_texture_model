""" utilities related to the project structure, as specified in README.md """
import os
import re
from .utilities import directory_filter, ls, read_image, csv_filter
from src.etc.consts import ROOT_DIR, transformation_dir, analysis_dir, image_dir, sorted_data_dir, metric_sorted_data_dir, human_sorted_data_dir, agent_name_delim, image_extensions


def validate_image_categories(ctx, param, value):
    """ makes sure that the given image categories are valid """
    invalid_categories = set(value) - set(get_image_category_names())
    if invalid_categories:
        raise ValueError(f"Invalid image categories: {invalid_categories}")
    return value


def validate_transformations(ctx, param, value):
    """ makes sure that the given image transformations are valid """
    invalid_transformations = set(value) - set(get_transformation_names())
    if invalid_transformations:
        raise ValueError(
            f"Invalid image transformations: {invalid_transformations}")
    return value


def validate_metrics(ctx, param, value):
    """ makes sure that the given image transformations are valid """
    invalid_metrics = set(value) - set(get_metric_names())
    if invalid_metrics:
        raise ValueError(
            f"Invalid image analysis names: {invalid_metrics}")
    return value


def validate_agent_names(ctx, param, value):
    """ makes sure that the given agent names are valid """
    invalid_agents = set(value) - set(get_agent_names())
    if invalid_agents:
        raise ValueError(
            f"Invalid agent names: {invalid_agents}")
    return value


def get_image_category_names():
    """gets all existing image categories
    :returns: a list of category names
    """
    return ls(
        os.path.join(
            ROOT_DIR, *image_dir),
        filtr=directory_filter,
        mapper=os.path.basename)


def get_transformation_names():
    """gets all available transformations
    :returns: a list of names of transformation
    """
    return ls(
        os.path.join(
            ROOT_DIR, *transformation_dir),
        filtr=directory_filter,
        mapper=os.path.basename)


def get_metric_names():
    """gets all available analysis metrics
    :returns: a list of names of analysis method
    """
    return ls(
        os.path.join(
            ROOT_DIR, *analysis_dir),
        filtr=directory_filter,
        mapper=os.path.basename)


def get_agent_names():
    """gets all available agent names as listed data/sort directory

    :returns: a list of agent names in the form of (humans|metrics)#name

    """
    return (ls(os.path.join(ROOT_DIR, *metric_sorted_data_dir),
               filtr=csv_filter,
               mapper=file2agent) +
            ls(os.path.join(ROOT_DIR, *human_sorted_data_dir),
               filtr=csv_filter,
               mapper=file2agent))


def agent2file(agent):
    """convert an agent name to file path

    :agent: the agent name, in the form of (humans|metrics)#name
    :returns: the file name corresponding to the agent

    """
    return os.path.join(
        ROOT_DIR, *sorted_data_dir,
        *agent.split(agent_name_delim)) + os.extsep + 'csv'


def file2agent(filename):
    """convert a csv filename to an agent name

    :filename: the csv filename
    :returns: the agent name in the form of (humans|metrics)#name

    """
    head, tail = os.path.split(filename)
    agent_type = os.path.split(head)[1]
    agent_name = os.path.splitext(tail)[0]
    return agent_name_delim.join([agent_type, agent_name])


def read_orig(category):
    """read the original image for a certain category

    :category: the category to be read
    :returns: the Image object

    """
    orig_path = get_existing_path(
        os.path.join(
            ROOT_DIR,
            *image_dir,
            category,
            'orig'))
    if not orig_path:
        raise ModuleError(f"no orig image found in category {category}")
    orig = read_image(orig_path)
    return orig


def read_output(category):
    """read the output reference image for a certain category

    :category: the category to be read
    :returns: the Image object

    """
    output_path = get_existing_path(
        os.path.join(ROOT_DIR, *image_dir, category, 'output'))
    if not output_path:
        raise ModuleError(f"no output image found in category {category}")
    output = read_image(output_path)
    return output


def get_existing_path(path, extensions=image_extensions):
    """

    :path: the path to a file
    :extensions: an array specifying alternative extensions to use when the given path is not available
    :returns: the resolved path, None if failed to resolve the image

    """
    path_root = os.path.splitext(path)[0]
    options = [path] + [path_root + os.extsep + ext for ext in extensions]
    for option in options:
        if os.path.isfile(option):
            return option
    return None


def read_level_image_paths(category, transformation):
    """read the transformed image for a certain category

    :category: the category to be read
    :transformation: the specific transformation
    :returns: an array of image paths that exist

    """
    base_path = os.path.join(ROOT_DIR, *image_dir, category, transformation)
    level_paths = [
        get_existing_path(
            os.path.join(
                base_path,
                f"level_{level:02}")) for level in range(
            0,
            11)]
    return list(filter(None, level_paths))


def read_level_images(category, transformation):
    """read the transformed image for a certain category

    :category: the category to be read
    :transformation: the specific transformation
    :returns: an array of image objects

    """
    return [
        read_image(path) for path in read_level_image_paths(
            category,
            transformation)]


def get_level_numeric(filename):
    """get the numeric level from filename

    :filename: the file name of the level image. E.g. '.../level_00.jpg'
    :returns: an integer representing the transformed level

    """
    match = re.search(
        rf"level_(\d+)\.(?:{'|'.join(image_extensions)})$",
        filename)
    if not match:
        raise ValueError(f"No numeric level found in filename {filename}")
    return int(match.group(1))
