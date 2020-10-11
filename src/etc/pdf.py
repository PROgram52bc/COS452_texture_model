
def get_xy(pdf):
    """ get current cursor position """
    return (pdf.get_x(), pdf.get_y())

def add_x(pdf, n):
    """ add n to the x value """
    pdf.set_x(pdf.get_x() + n)

def add_y(pdf, n):
    """ add n to the y value """
    pdf.set_y(pdf.get_y() + n)

def reset_x(pdf):
    """ reset x to the left """
    pdf.set_x(pdf.l_margin)

def reset_y(pdf):
    """ reset y to the left """
    pdf.set_y(pdf.t_margin)

def advance(pdf, dist, cutoff_x=0, cutoff_y=0, line_height=None):
    """ advance the cursor by dist, 
    change line if after advancing, there is less than cutoff units to the right margin 
    add a page if after changing line, 
    line_height specifies the line's height, default to dist """
    if line_height is None:
        line_height = dist
    add_x(pdf, dist)
    # check whether new line needed
    if pdf.get_x() + cutoff_x > pdf.w - pdf.r_margin:
        add_y(pdf, line_height)
        reset_x(pdf)
        # check whether new page needed
        if pdf.get_y() + cutoff_y > pdf.h - pdf.b_margin:
            pdf.add_page()



def lay_images(pdf, image_paths, width, space):
    """lay a grid of the images, 
    images are layed out horizontally and then vertically

    :pdf: the fpdf object
    :image_paths: a list of paths of images to be laid out in a pdf
    :width: the image width for each image
    :space: space between images and page edge
    :returns: the modified fpdf object

    """
    for path in image_paths:
        x, y = get_xy(pdf)
        pdf.image(path, w=width)
        pdf.set_xy(x, y) # reset the cursor to previous position
        advance(pdf, dist=width+space, cutoff_x=width, cutoff_y=width)
    return pdf

    

