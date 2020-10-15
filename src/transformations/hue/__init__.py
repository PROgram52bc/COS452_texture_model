import numpy
from PIL import Image

def transform(img, level):
    arr = numpy.array(img.convert(mode='HSV'))
    arr[...,0] += level * 18 # shifting the hue
    return Image.fromarray(arr, mode='HSV')
