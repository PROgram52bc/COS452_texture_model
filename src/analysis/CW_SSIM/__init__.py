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
        image_pil = Image.fromarray(image.astype('uint8'), 'RGB')
        orig_pil = Image.fromarray(orig.astype('uint8'), 'RGB')
        ssim = SSIM(image_pil)
        result = ssim.cw_ssim_value(orig_pil)
        return result
