from PIL import Image, ImageFilter

def transform(img, level):
    return img.filter(ImageFilter.GaussianBlur(level))
