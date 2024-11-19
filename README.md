# WEPX Weather Toolkit Backend
WEPX Weather Toolkit Backend is the repo for the Backend programs used in a future weather website. There is also a Frontend repo containing the visual website and front-end code to decode the data done by this backend program.

## Description
This program automates the downloading of files of weather models and more (will be added). It checks for the availability of a weather model output grib2 file and downloads a subset of the forecast containing only the requested variables. 

It then converts it to PNG file using GDAL. The outputed file is a PNG file containing a 24bit Float array. It then converts it to lossless WEBP for the best compression. Data then has to be converted back to a colormap on the client side.

## Usage
**WEPX_Weather_Toolkit_Backend.py** is the main program containing the loop to check and download the file using the other python files.

**createMapSVG.py** is a test python code to render the world map using Cartopy for FrontEnd use.

.


***Other files which can be used as librairies:***

**convert.py** contains the code to convert the downloaded raster to an image and outputing the raster lat/lon extent to JSON.

**download.py** contains the code to download the weather model subset.

.

In-files comments can be used as guidance to code.

## Installation

Librairies need to be first downloaded either using an environnement or pip.

For this project, geospatial binairies have been downloaded [here](https://github.com/cgohlke/geospatial-wheels/).

Currently none-standard libraries are:

* [numpy](https://github.com/numpy/numpy)
* [GDAL](https://github.com/OSGeo/gdal)
* [wand](https://github.com/emcconville/wand)



## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
