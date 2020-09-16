# Project structure

-   `start.py`: executable script implementing commands that can transform or
	analyze images accordingly

-   `images/`: contains source images to be ranked according to different
	metrics

	-   `<category>/`\*: contains a certain category of image. For example,
		'brick,' 'wheat,' etc.
		-   `orig.jpg`: the original image; everything else in this directory is
			derived from this image.
		-   `output.jpg`: the output image without being transformed with any
			specific transformation.
		-   `<transformation>/`\*: contains images that are transformed from the
			original image with a certain transformation. For example, 'crop,'
			'watermark,' etc.
			-   `level_[0-10].jpg`\*: images transformed with different
				intensity with the particular `<transformation>`. Level 0 is
				identical to `output.jpg`, and Level 10 is the most transformed.

-   `printables/`: contains the transformed images in printable format
	(currently only pdf format)
	-   `<category>_<transformation>.pdf`\*: the file containing all levels of
		transformed images in `<category>` transformed using `<transformation>`

-   `data/`: contains analysis data
	-   `rank.yaml`: contains rank output data in the following form
		- `<category>/`\*
			- `<transformation>/`\*
				- `rank.yaml`: the rank result of images in `<category>`
				  transformed using `<transformation>`
					- `[ level_4, level_2, ... ]`: the first element in the list
					  is the closest to the original image.

-   `src/`: contains source code

	-   `transformations/`: contains code to transform images
		-   `<transformation>/`\*: represents a transformatio.For example, blur.
			-   `__init__.py`: contains a `transform(img, level): img` public
				function to transform a given image with the given `level`. The
				function should ensure that when `level` is 0, the image
				returned is identical to the image passed to it.

	-   `analysis/`: contains code to calculate ranks based on different metrics

		-   `<metric>/`\*: represents a metric. For example, MSE.
			-   `__init__.py`: contains a `rate(orig, comp): float` function to
				calculate the difference rating according to `<metric>`.

-   `env.py`: contains environmental variables for python (e.g.  `ROOT_DIR`)

-   `env.sh`: to be sourced before running the project
