from PIL import Image, ImageDraw


def crop_to_circle(img, max_radius=256, bg_color=(0, 0, 0)):
    """ crop the given image into a circle.

    :img: the image to be img
    :max_radius: the maximum radius of the circle, default to 256 pixels
    If greater than img.width//2 or img.height//2,
    then it is set to min(img.height//2, img.width//2)
    :bg_color: the background color for the img image, default to black
    :returns: the img image

    """
    width, height = img.size
    radius = min(max_radius, width // 2, height // 2)
    # crop the given image
    x1 = width // 2 - radius
    x2 = width // 2 + radius
    y1 = height // 2 - radius
    y2 = height // 2 + radius
    box = (x1, y1, x2, y2)
    img = img.crop(box)
    # create mask
    mask = Image.new("1", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, radius * 2, radius * 2), 1)
    # create background image
    bg = Image.new("RGB", img.size, bg_color)
    # merge the images together
    result = Image.composite(img, bg, mask)
    return result
