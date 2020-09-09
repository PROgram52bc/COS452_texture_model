from matplotlib.pyplot import imread
import numpy as np


def rank(img_map, img_orig):
    """A function to rank images according to the MSE metric

    :img_map: a dictionary containing imgkey: filename pairs, where imgkey is a unique identifier for the image, and filename is a string indicating the absolute path of the image
    :img_orig: a string containing the absolute path to the original image
    :returns: a list containing imgkeys of images, indicating the ranks of the images from the most similar to the original to the least.

    """
    errors = []
    orig = imread(img_orig)
    for img_key in img_map:
        img_name = img_map[img_key]
        image = imread(img_name)
        error = ((image - orig)**2).mean()
        errors.append((img_key, error))

    errors.sort(key=lambda t: t[1])
    return [error[0] for error in errors]


def main():
    from os import path
    from env import ROOT_DIR
    from yaml import safe_load, safe_dump

    # get the names of each image set
    with open(path.join(ROOT_DIR, 'images.yaml'), 'r') as f:
        images_map = safe_load(f)

    try:
        # open if file exists
        with open(path.join(path.dirname(__file__), 'rank.yaml'), "r") as f:
            # ranks == { 'image_set1': ['img1', 'img2', ...], ... }
            ranks = safe_load(f)
    except OSError:
        ranks = {}

    # calculate rank for each image set
    for image_set_name in images_map:
        image_map = images_map[image_set_name]
        image_orig = image_map['orig']
        # delete the original
        del image_map['orig']

        result = rank(image_map, image_orig)
        ranks.update({image_set_name: result})
    print("ranks: {}".format(ranks))

    # overwrite the file
    with open(path.join(path.dirname(__file__), 'rank.yaml'), "w") as f:
        f.write(safe_dump(ranks, default_flow_style=False))


if __name__ == "__main__":
    main()
