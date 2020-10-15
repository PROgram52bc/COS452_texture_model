import numpy
from PIL import Image

def transform(img, level):
    arr = numpy.array(img, dtype="float64")
    arr += numpy.random.normal(0, level*8, arr.shape)
    return Image.fromarray(arr.astype('uint8'))
