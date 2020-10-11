from PIL import Image, ImageDraw

def crop_to_circle(img, max_radius=256, bg_color=(255, 255, 255)):
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

def add_orientation_marker(img, marker_color=(0,0,0)):
    """ add orientation marker to an image

    :img: the input image
    :marker_color: the color of the marker
    :returns: the processed image

    """
    marker_length, marker_width = 20, 6
    width, height = img.size
    draw = ImageDraw.Draw(img)
    draw.line((
        (marker_width//2-1,               height-marker_width//2-1-marker_length), 
        (marker_width//2-1,               height-marker_width//2-1), 
        (marker_width//2-1+marker_length, height-marker_width//2-1)),
        fill=marker_color,
        width=marker_width,
        joint="curve")
    draw.line((
        (width-marker_width//2-1,               height-marker_width//2-marker_length), 
        (width-marker_width//2-1,               height-marker_width//2), 
        (width-marker_width//2-1-marker_length, height-marker_width//2)),
        fill=marker_color,
        width=marker_width,
        joint="curve")
    return img

