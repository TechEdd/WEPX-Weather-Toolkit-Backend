import time
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
from wand.image import Image

debug = True


#inputFile: file name of png file (works for other formats)
#exportFile: file name of exported webp file
#quality: int pourcentage of quality
#description: convert image file to webp using wand
def convertToWEBP(inputFile="input.png", exportFile="output.webp", quality=50):
    #benchmark time
    if (debug):
        start_time = time.time()

    with Image(filename=inputFile) as img:
        img.format = 'webp'
        img.compression_quality = quality
        img.save(filename='output_python.webp')

    if (debug):
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Finished converting PNG '{inputFile}' to webp '{exportFile}': {elapsed_time:.2f} seconds")
    


#inputFile: file name of NetCDF file
#exportFile: file name of exported PNG
#extent: bbox lat,lon of export PNG
#        xmin ymin xmax ymax
#        eg: [-125,24,-66,50] < USA
#vmin: minimum value in png will be equal to 0
#vmax: maximum value in png will be equal to 255
#nodata: nodata value
#description: convert NetCDF (or GeoTIFF) file to grayscale png
#             only onvert the first raster Band
#             all data under and over vmin and vmax will be capped
def convertFromNCToPNG(inputFile="input.tif", exportFile="output.png", extent=[-125,24,-66,50], vmin=0, vmax=5, nodata=0):
    #benchmark time
    if (debug):
        start_time = time.time()

    dataset = gdal.Open(inputFile)

    gdal.Translate(
        exportFile,
        inputFile,
        outputSRS="EPSG:4326", #Equirectangular
        outputBounds=extent,
        noData=nodata,
        scaleParams=[[vmin, vmax, 0, 255]],
        outputType=gdal.GDT_Byte, # 8 bits
        creationOptions=['ZLEVEL=1'], #Set the amount of time to spend on compression. A value of 1 is fast but does no compression, and a value of 9 is slow but does the best compression.
        format="png")

    if (debug):
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Finished converting NetCDF '{inputFile}' to PNG '{exportFile}': {elapsed_time:.2f} seconds")
    
    #close dataset
    dataset = None

if __name__ == "__main__":
    convertFromNCToPNG(vmin=0.1, vmax=1, nodata=0)
    convertToWEBP("output.png")
    input()
