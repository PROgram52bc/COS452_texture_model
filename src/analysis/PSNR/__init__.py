from .. import AnalyzerBase
import numpy as np
import math

class Analyzer(AnalyzerBase):
    big_similar = True

    def rate(self, image, orig):
        """rate how similar image is to the original

        :image: the image to be rated as a numpy array
        :orig: the original image to be compared to, as a numpy array
        :returns: a floating point number indicating the similarity or dissimilarity

        """
        # from https://cvnote.ddlee.cn/2019/09/12/psnr-ssim-python
        # image and orig have range [0, 255]
        image = image.astype(np.float64)
        orig = orig.astype(np.float64)
        mse = np.mean((image - orig)**2)
        if mse == 0:
            return float('inf')
        return 20 * math.log10(255.0 / math.sqrt(mse))
