def transform(img, level):
    width, height = img.size
    left = level * width / 25
    upper = level * height / 25
    right = width - level * width / 25
    lower = height - level * height / 25
    zoomed = img.crop((left, upper, right, lower))
    return zoomed.resize((width, height))
