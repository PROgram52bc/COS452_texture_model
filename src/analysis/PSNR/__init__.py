from .. import AnalyzerBase
import numpy as np
from skimage.metrics import peak_signal_noise_ratio


class Analyzer(AnalyzerBase):
    big_similar = True

    def rate(self, image, orig):
        """rate how similar image is to the original

        :image: the image to be rated as a numpy array
        :orig: the original image to be compared to, as a numpy array
        :returns: a floating point number indicating the similarity or dissimilarity

        """
        # turn off divide warning
        old_settings = np.seterr(divide='ignore')
        # assume image and orig have range [0, 255]
        result = peak_signal_noise_ratio(image, orig, data_range=255)
        # turn on divide warning
        np.seterr(**old_settings)
        return result
