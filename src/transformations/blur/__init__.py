from PIL import ImageFilter


def transform(img, level):
    return img.filter(ImageFilter.GaussianBlur(level))
