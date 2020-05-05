import numpy as np
from matplotlib.pyplot import imread
import glob

orig_name = './images/orig/1_orig.jpg'
image_names = glob.glob('./images/1_red_carpet/*.jpg')

errors = []
orig = imread(orig_name)
for image_name in image_names:
    print("image_name: {}".format(image_name))
    image = imread(image_name)
    error = ((image-orig)**2).mean()
    errors.append((image_name, error))
    print("error: {}".format(error))

errors.sort(key=lambda t:t[1])
print("sorted errors: {}".format(errors))
