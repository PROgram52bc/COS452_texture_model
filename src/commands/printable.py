import click
import os
from fpdf import FPDF
from src.etc.pdf import lay_images
from src.etc.consts import ROOT_DIR, printable_dir
from src.etc.utilities import pif
from src.etc.structure import get_image_category_names, get_transformation_names, read_level_image_paths


def generate_pdf(category, transformation, gap, verbose):
    """generate pdf file with transformed images

    :category: the category of image
    :transformation: the transformation to be used
    :returns: None

    """
    # read available images
    image_paths = read_level_image_paths(category, transformation)
    if len(image_paths) == 0:
        pif(verbose,
            f"Skip {category}, {transformation}, no level images found")
        return None
    # generate pdf
    pdf = FPDF(orientation="L", unit="pt", format="letter")
    pdf.set_auto_page_break(False)
    pdf.set_margins(30, 30, 30)
    pdf.set_font('Arial', 'B', 20)
    pdf.add_page()
    pdf.cell(
        pdf.w,
        30,
        f"Category: {category}; Transformation: {transformation}",
        border=0,
        ln=1,
        align="C")
    pdf.set_font('Arial', '', 10)
    pdf.cell(
        pdf.w,
        30,
        f"Images to be sorted first from left to right, then from top to bottom. From level_0 to level_10",
        border=0,
        ln=1,
        align="C")
    lay_images(pdf, image_paths, width=240, space=gap)
    output_path = os.path.join(
        ROOT_DIR, *printable_dir, f"{category}_{transformation}.pdf")
    pdf.output(output_path)
    pif(verbose, f"File written to {output_path}")


def create_printable_cli(cli):
    printable = click.Group('printable', help="Generate printable documents")

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
    @click.option("--gap", default=5, show_default=True,
                  help="The gap between each image")
    @click.option("--verbose/--silent", default=True)
    @printable.command('all')
    def printable_all(categories, transformations, gap, verbose):
        """ generate printable files with the transformed images """
        os.makedirs(os.path.join(ROOT_DIR, *printable_dir), exist_ok=True)
        for category in categories:
            for transformation in transformations:
                # read available level images
                pif(verbose,
                    f"Generating printable for {category}, {transformation}...")
                generate_pdf(category, transformation, gap, verbose)

    cli.add_command(printable)
