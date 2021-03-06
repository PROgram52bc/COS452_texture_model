from .. import AnalyzerBase
from skimage.metrics import mean_squared_error
import numpy as np

class Analyzer(AnalyzerBase):
    big_similar = False

    def rate(self, image, orig):
        """rate how similar image is to the original

        :image: the image to be rated as a numpy array
        :orig: the original image to be compared to, as a numpy array
        :returns: a floating point number indicating the similarity or dissimilarity

        """
        return mean_squared_error(image, orig)
