# Project structure

-   `images/`: contains source images to be ranked according to different metrics

    -   `<category>/`\*: contains a certain category of image. For example, 'brick,' 'wheat,' etc.
        -   `orig.jpg`: the original image
        -   `<transformation>/`\*: contains images that are transformed from the original image with a certain transformation. For example, 'crop,' 'watermark,' etc.
            -   `level_[1-9].jpg`\*: images transformed with different intensity with the particular `<transformation>`. Level 1 is the least transformed.

-   `transform.sh`: transforms each `<category>/orig.jpg` with different `<transformation>`s using ImageMagick.

-   `analysis/`: contains code to calculate ranks based on different metrics

    -   `<metric>/`\*: represents a metric. For example, MSE.
		-   `__init__.py`: contains a `rate(orig, comp): float` function to calculate the difference rating according to `<metric>`.
		-   `rank.yaml`: contains rank output data in the following form
			- `<category>`*
				- `<transformation>`*
					- `[ level_4, level_2, ... ]`: the first element in the list is the closest to the original image.


-   `env.py`: contains environmental variables for python (e.g. `ROOT_DIR`)

-   `env.sh`: to be sourced before running the project
