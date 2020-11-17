from .. import AnalyzerBase
from ssim.ssimlib import SSIM
from PIL import Image
from skimage.metrics import structural_similarity
import numpy as np


class Analyzer(AnalyzerBase):
    def rate(self, image, orig):
        """rate how similar image is to the original

        :image: the image to be rated as a numpy array
        :orig: the original image to be compared to, as a numpy array
        :returns: a floating point number indicating the similarity or dissimilarity

        """
        result = structural_similarity(image, orig, data_range=255, multichannel=True)
        return result
