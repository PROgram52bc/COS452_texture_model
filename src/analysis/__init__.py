import numpy

class AnalyzerBase:
    """the bass class for any analysis algorithms"""
    big_similar = True # Set to false if smaller number means more similar

    def __init__(self):
        pass

    def rate(self, image, orig):
        """rate how similar image is to the original

        :image: the image to be rated
        :orig: the original image to be compared to
        :returns: a floating point number indicating the similarity or dissimilarity

        """
        raise NotImplementedError("Must be implemented in sub-classes")

    def sort(self, images, orig):
        """sort the array of images according to their similarity to orig

        :images: the array of image object
        :orig: the original image to be compared to
        :returns: a sorted list of images

        """
        orig = numpy.array(orig)
        return sorted(images, key=lambda image: self.rate(numpy.array(image), orig), reverse=self.big_similar)

