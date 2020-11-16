# Workflow

This section describes the typical workflow for using this tool.

## Preparation
### Add a sample image

Images must first be added before being transformed and analyzed.
Each sample image has a unique name, and we will refer to that name as its "category."
Some example "categories" can be: "brick," "dirt," etc.

To add a new sample image,

1. Create a directory under the `images` directory with the name of the image
   category.
1. Copy your sample image to the `images/<category>` directory. The sample
   image must be named "orig.jpg".

Instead of `jpg` format, `jpeg` or `png` can also be used. When multiple
options are available, images are resolved in the following priority:

1. jpg
1. jpeg
1. png

### Add a transformation

The sample images you added in the previous step can be transformed using
various transformations.  Each transformation is defined by a single python
function with the following signature:

```python
transform(img: PIL.Image, level: int): PIL.Image
```

It accepts as the first argument an `Image` object defined by the PIL library,
each of the sample images will be passed to the function via this argument.

It accepts an integer as the second argument, representing the level of
transformation.

It returns a new `Image` object, which is the transformed image.

If `level == 0`, the returned image should be identical to `img`, the function
should support a range of `level` from 0 to 10.

To add the transformation,

1. Create a directory under the `src/transformations` directory with the name
   of the transformation.
1. Create a file named `__init__.py` under the
   `src/transformations/<transformation>` directory.
1. Define a function named `transform` in
   `src/transformations/<transformation>/__init__.py`. The function should have
   the signature and standard as described above.

Some sample transformations are implemented in `src/transformations/` directory
for reference.

### Add a metric

## Image manipulation

### Transform

### Analyze

## Human data

### Sequence

### Printables

# Project structure

This section describes the overall project structure.

> __Legends__:

> Each list item is either a directory or a file, or multiple
> directories/files, if they are followed with a asterisk ("\*") sign

> Each list item has two parts, separated by a colon (":"), the part before
> the colon is the name of the directory or the file, while the part after
> the colon is a description for the directory or the file.

> `directory/` names are followed by a slash, while `file` names are not
> followed by a slash.

> sub-directories and files for a given directory are nested below the
> given directory.

> if a name of a directory or a file contains a word surrounded by angle
> bracket (`<placeholder>`), the word is a placeholder that can be replaced
> by specific names according to the description.

-   `start.py`: executable script implementing commands that can transform or
    analyze images accordingly

-   `images/`: contains source images to be ranked according to different
    metrics

    -   `<category>/`\*: contains a certain category of image. For example,
        'brick,' 'wheat,' etc.
        -   `orig.jpg`: the original image; everything else in this directory
            is derived from this image.
        -   `output.jpg`: the output image without being transformed with any
            specific transformation.
        -   `<transformation>/`\*: contains images that are transformed from
            the original image with a certain transformation. For example,
            'crop,' 'watermark,' etc.
            -   `level_[0-10].jpg`\*: images transformed with different
                intensity with the particular `<transformation>`. Level 0 is
                identical to `output.jpg`, and Level 10 is the most
                transformed.

-   `printables/`: contains the transformed images in printable format
    (currently only pdf format)

    -   `<category>_<transformation>.pdf`\*: the file containing all levels of
        transformed images in `<category>` transformed using `<transformation>`

-   `data/`: contains ranking data

	-   `sequence/`: contains sequence related data
		-   `sequences.json`: existing sequence mappings. Data has the
			[following structure](#sequence-data-structure)

	-   `sort/`
		-   `humans/`: contains human sorted data, converted from manually
			typed data.

			-   `<id>.csv`\*: data collected from person associated with `<id>`.
				Data has the [following structure](#sorted-data-structure)

		-   `metrics/`: contains computer ranked data, automatically generated by
			the `analyze` command
			-   `<metric>.csv`\*: data generated by `<metric>`. E.g. MSE. Data
				has the [following structure](#sorted-data-structure)
	-   `rank/`
		-   `standard.csv`: Spearman's rank correlation against the standard
			order, grouped by metrics and category-transformation. Data has the
			the [following structure](#ranked-data-structure)
		-   `human.csv`: Spearman's rank correlation against human ranked
			order, not implemented.

-   `src/`: contains source code

    -   `transformations/`: contains code to transform images

        -   `<transformation>/`\*: represents a transformation. For example,
            blur.
            -   `__init__.py`: contains a `transform(img, level): img` public
                function to transform a given image with the given `level`. The
                function should ensure that when `level` is 0, the image
                returned is identical to the image passed to it.

    -   `analysis/`: contains code to calculate ranks based on different
        metrics

        -   `<metric>/`\*: represents a metric. For example, MSE.
            -   `__init__.py`: contains a class definition of subclass derived
                from the `Analyzer` class, with a method `rate(orig, comp): float` to calculate the difference rating according to
                `<metric>`.

-   `env.sh`: to be sourced before running the project

# Data file structures

## sorted data structure
| dataset                       | 1   | 2   | ... |
| ----------------------------- | --- | --- | --- |
| `<category>_<transformation>` | 4   | 2   | ... |
| `<category>_<transformation>` | ... | ... | ... |
| `<category>_<transformation>` | ... | ... | ... |
| ...                           | ... | ... | ... |

> the first row contains the reference sequence, ordered according to their
> level of distortion, where the first item is the most similar to the
> reference image, and the last is the least similar.

> `<category>_<transformation>` represents a dataset of a
> category-transformation, for example, "wheat\_blur" means the images in the
> "wheat" category that is transformed using the "blur" transformation.

> the numbers in each row correspond to the level to which each image is
> transformed. For example, the "4" under the (1) column means that the image
> with a transformation level of 4 (with a name similar to "level\_04.jpg") is
> rated to be the most similar to the reference image.

> in human rated data, the numbers can also be arbitrary symbols, as long as
> the symbols are consistent across different rows.

## ranked data structure

| AGENT     | CATEGORY     | TRANSFORMATION     | spearman rank | p-value |
| --------- | ------------ | ------------------ | ------------- | ------- |
| `<agent>` | `<category>` | `<transformation>` | 1             | 0       |
| `<agent>` | `<category>` | `<transformation>` | 0.39          | 0.235   |
| `<agent>` | `<category>` | `<transformation>` | 0.81          | 0.003   |
| ...       | ...          | ...                | ...           | ...     |

## sequence data structure

```
{
	"category#transformation": ['A', 'B', 'C', 'D', 'E', ...],
	...
}
```

> Each key-item pair in the json file represents the symbol sequence used to
> encode the transformed images, from the most similar to the least. 

# Notes

## Imagemagick commands

## Show levels of transformations
To show various transformations, execute the following in any `images/<category>/<transformation>/` directory:

```bash
montage -pointsize 60 -geometry "48x48+5+5<" -label "%t" -tile 5x2 level_{[0][1-9],10}*.jpg levels.jpg
```
Sample output:

![transformation level showcase](assets/levels.jpg)

## Show transformations
To show various transformations, execute the following in any `images/<category>/` directory:
```bash
mkdir tmp
for transformed in */level_05.jpg; do cp $transformed ./tmp/${transformed%%/*}.jpg; done
montage -pointsize 50 -geometry "48x48+5+5<" -label "%t" -tile 3x2 \( output.jpg -set label original \) tmp/* transformations.jpg
rm -rf tmp
```
Sample output:

![transformations showcase](assets/transformations.jpg)

## Show textures
To show available texture images, execute the following in `images/` directory:
```bash
# assumes blue_carpet,dirt,fur,shirt are existing categories
montage -geometry "+5+5" {blue_carpet,dirt,fur,shirt}/orig.jpg textures.jpg
```
Sample output:

![textures showcase](assets/textures.jpg)
