import click
import os
import importlib  # for dynamic import
from src.etc.consts import ROOT_DIR, transformation_dir, image_dir
from src.etc.structure import validate_image_categories, validate_transformations, get_image_category_names, get_transformation_names, read_orig
from src.etc.postprocessors import crop_to_circle, add_orientation_marker, add_margin, add_border
from src.etc.utilities import pif, write_image


def transform_image(image, transformation, level):
    """ transforms an image
    :image: the image to be transformed
    :transformation: transformation name. E.g. rotate
    :level: integer from 0 to 10
    :returns: the transformed image
    """
    if transformation not in get_transformation_names():
        raise ValueError(
            f"transformation with name {transformation} is not available")
    mod = importlib.import_module(
        '.'.join([*transformation_dir, transformation]))
    transform = getattr(mod, 'transform', None)
    if not transform:
        raise ModuleError(
            f"no transform function implemented in transformation module {transformation}")
    new_image = transform(image, level)
    return new_image


def transform_image_by_category(
        category,
        transformation,
        levels=range(11),
        extension='jpg',
        override=True,
        verbose=True,
        post_processors=[]):
    """ transform the image of a certain category

    :category: the category to be transformed, assumes that it is a valid category
    :transformation: the transformation to apply
    :levels: an iterable of integers
    :extension: the extension of the output file
    :returns: None

    """
    orig = read_orig(category)
    for level in levels:
        out_dir = os.path.join(ROOT_DIR, *image_dir, category, transformation)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(
            out_dir,
            f"level_{level:02}" +
            os.extsep +
            extension)
        # skip image computation if not overriding existing image
        if os.path.isfile(out_path) and not override:
            pif(verbose, f"skip image at {out_path}")
            continue
        out = transform_image(orig, transformation, level)
        write_image(
            out,
            out_path,
            post_processors=post_processors,
            verbose=verbose)


def create_transform_cli(cli):
    transform = click.Group(
        'transform',
        help="Transform images using available transformations")

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
    @click.option("--override/--no-override", default=True)
    @click.option("--verbose/--silent", default=True)
    @click.option("--circle/--no-circle", "circle", default=True)
    @click.option("--orientation-mark/--no-orientation-mark",
                  "orientation", default=True)
    @click.option("--margin", default=30)
    @click.option("--border", default=1)
    @transform.command('all')
    def transform_all(
            categories,
            transformations,
            verbose,
            override,
            circle,
            orientation,
            margin,
            border):
        """ Transform all existing images with all available transformations.

        if category is given, transform only the specified categories
        if transformation is given, transform with only the specified transformations
        by default, images will be cropped into a circle, can override this behavior with --no-circle
        if images are cropped, an orientation mark will by default be added, override this behavior with --no-orientation-mark


        """
        post_processors = []
        if circle:
            post_processors.append(crop_to_circle)
            if orientation:
                post_processors.append(add_orientation_marker)
        if margin:
            post_processors.append(
                lambda img: add_margin(
                    img, margin_width=margin))
        if border:
            post_processors.append(
                lambda img: add_border(
                    img, border_width=border))

        for category in categories:
            pif(verbose, f"Processing category {category}...")
            # generate the unmodified reference image
            orig = read_orig(category)
            out_path = os.path.join(
                ROOT_DIR, *image_dir, category, "output.jpg")
            write_image(
                orig,
                out_path,
                post_processors=post_processors,
                override=override,
                verbose=verbose)

            for transformation in transformations:
                pif(verbose, f"Transforming with {transformation}...")
                transform_image_by_category(
                    category,
                    transformation,
                    post_processors=post_processors,
                    override=override,
                    verbose=verbose)
    cli.add_command(transform)
