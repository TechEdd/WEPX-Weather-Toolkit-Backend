import time
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
from wand.image import Image

debug = True

def convertToWEBP(inputFile="input.png", exportFile="output.webp"):
    '''
    Converts an image file (e.g., PNG) to a WebP format using the Wand library.

    This function supports various image formats, not just PNG, and allows 
    for adjusting the quality of the WebP output.

    Parameters:
    inputFile (str): The file name of the input image (supports multiple formats like PNG, JPEG, etc.).
    exportFile (str): The file name for the exported WebP file.
    
    Returns:
    None: The output is saved as a WebP file specified by `exportFile`.
    '''
    
    #benchmark time
    if (debug):
        start_time = time.time()

    with Image(filename=inputFile) as img:
        img.format = 'webp'
        img.options['webp:lossless'] = 'true'
        img.save(filename=exportFile)

    if (debug):
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Finished converting PNG '{inputFile}' to webp '{exportFile}': {elapsed_time:.2f} seconds")


def float_to_rgb(arr, vmin, vmax):
    """
    Convert a float array into a 24-bit RGB representation.
    Each float will be split into three 8-bit values for R, G, and B.
    
    Parameters:
    arr : np.ndarray
        The input array of float values to be converted.
    vmin : float
        The minimum float value for normalization.
    vmax : float
        The maximum float value for normalization.
    
    Returns:
    np.ndarray
        An array representing the RGB image.
    """

    # Step 1: Normalize float value to [0, 16777215]
    old_min = vmin
    old_max = vmax
    int_max = 256 ** 3 - 1  # 16777215 (24-bit maximum)

    # Linear transformation from [vmin, vmax] to [0, 16777215]
    normalized_value = np.round(((arr - old_min) / (old_max - old_min)) * int_max)

    arr = np.clip(normalized_value, 0, int_max)
    
    # Get R, G, B values by base-256 representation
    r = (arr // (256**2)) % 256
    g = (arr // 256) % 256
    b = arr % 256
    
    # Stack to create an RGB image
    rgb = np.stack((r, g, b), axis=-1).astype(np.uint8)
    
    return rgb    

def convertFromNCToPNG(inputFile="input.tif", exportFile="output.png", extent=[-125,24,-66,50], vmin=0, vmax=10, nodata=None):
    '''
    Converts a NetCDF (or GeoTIFF) file to a grayscale PNG.

    This function processes only the first raster band of the input file. 
    Values in the output PNG will range from 0 to 255, with data below `vmin`
    and above `vmax` being capped to 0 and 255, respectively.

    Parameters:
    inputFile (str): The file name of the NetCDF or GeoTIFF input file.
    exportFile (str): The file name for the exported PNG.
    extent (list): Bounding box coordinates [xmin, ymin, xmax, ymax] 
                   in lat/lon for the exported PNG.
                   Example: [-125, 24, -66, 50] (USA).
    vmin (float): The minimum value in the input data. Values equal to `vmin` 
                  will be mapped to 0 in the PNG.
    vmax (float): The maximum value in the input data. Values equal to `vmax` 
                  will be mapped to 255 in the PNG.
    nodata (float): The value representing no data in the input file.

    Returns:
    None: The output is saved as a PNG file specified by `exportFile`.
    '''
    
    #benchmark time
    if (debug):
        start_time = time.time()

    dataset = gdal.Open(inputFile)

    data_array = dataset.GetRasterBand(1).ReadAsArray().astype(float)

    #Rescale input to the desired vmin and vmax to 24bit
    #data_rescaled = np.clip(map_values(data_array, vmin, vmax, 0, 256^3), 0, 256^3)

    #arrange array to rgb standards
    rgb_array = float_to_rgb(data_array, vmin, vmax)

    # Create an in-memory dataset to hold the RGB data
    driver = gdal.GetDriverByName('MEM')
    rows, cols, _ = rgb_array.shape
    rgb_dataset = driver.Create('', cols, rows, 3, gdal.GDT_Byte)
    
    # Write the RGB bands to the dataset
    for i in range(3):  # R, G, B
        rgb_dataset.GetRasterBand(i + 1).WriteArray(rgb_array[:, :, i])

    gdal.Translate(
        exportFile,
        rgb_dataset,
        outputSRS="EPSG:4326", #Equirectangular
        outputBounds=extent,
        width="3000",
        height="1322",
        noData=nodata,
        outputType=gdal.GDT_Byte, # 8 bits
        creationOptions=['ZLEVEL=1'], #Set the amount of time to spend on compression. A value of 1 is fast but does no compression, and a value of 9 is slow but does the best compression.
        format="png")

    if (debug):
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Finished converting NetCDF '{inputFile}' to PNG '{exportFile}': {elapsed_time:.2f} seconds")
    
    #close dataset
    rgb_dataset.FlushCache()
    rgb_dataset = dataset = None

if __name__ == "__main__":
    convertFromNCToPNG(vmin=0.1, vmax=1, nodata=0)
    convertToWEBP("output.png")
    input()
