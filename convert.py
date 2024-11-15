import time
import json
import os
import numpy as np
from osgeo import gdal, osr
gdal.UseExceptions()
from wand.image import Image

debug = True
export_json = True
file_width_resolution = 3000
output_json_file = "model_extent.json"

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

def saveToJSON(extent, output_file, model):
    # Check if the JSON file exists
        if os.path.exists(output_file):
            # Load the existing JSON data
            with open(output_file, 'r') as f:
                data = json.load(f)
        else:
            # If the file doesn't exist, create an empty dictionary
            data = {}
                
        # Update or add the model_name key with the extent value
        data[model] = [extent[0],extent[1],extent[2],extent[3]]

        # Save the updated data back to the JSON file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)

def get_raster_extent_in_lonlat(dataset, model, output_file=output_json_file):
    """
    Get the extent of a raster in longitude and latitude (WGS84).

    This function opens a raster file and iterates to find the true highest and lowest
    lons and lats.

    Save the raster extent to a JSON file. If the model key exists, update its value.
    Otherwise, append the model key with the new value.

    Parameters:
    - GDAL dataset: dataset of raster to analyze
    - model (str): model name for indexing in file 
    - output_file (str): output file name for extent
                         if None, will not output file

    Returns:
    - list: A tuple list representing the extent (xmin, ymin, xmax, ymax) in 
             longitude and latitude.
    - file: A json file containing the model name and the extent if output_file is
            not None

    If the raster is already in lon/lat, the function returns the extent as is.
    Otherwise, it transforms the extent to lon/lat.
    """

    # Get the raster's geotransform and projection
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    
    # Get dataset dimensions
    x_size = dataset.RasterXSize
    y_size = dataset.RasterYSize

    # Extract extent in the original CRS (coordinate reference system)
    x_min = geotransform[0]
    y_max = geotransform[3]
    x_max = x_min + geotransform[1] * x_size
    y_min = y_max + geotransform[5] * y_size
    
    # Define the source projection
    source_proj = osr.SpatialReference()
    source_proj.ImportFromWkt(dataset.GetProjection())

    if source_proj.IsGeographic():
        # Return the extent using the geotransform if already in lat/lon (WGS84)
        lon_max = geotransform[0]
        lon_min = geotransform[0] + dataset.RasterXSize * geotransform[1]
        lat_max = geotransform[3]
        lat_min = geotransform[3] + dataset.RasterYSize * geotransform[5]
        extent = [lat_min, lon_min, lat_max, lon_max]


    # Define the target projection (WGS84, lat/lon)
    target_proj = osr.SpatialReference()
    target_proj.ImportFromEPSG(4326)  # EPSG code for WGS84

    # Create a coordinate transformation object
    transform = osr.CoordinateTransformation(source_proj, target_proj)

    # Initialize min and max values
    lat_min, lon_max = float('inf'), -float('inf')
    lon_min, lat_max = float('inf'), -float('inf')

    #To avoid processing every single pixel, sample along the edges of the image at a specified rate
    #A lower sample_rate will make the result more accurate but slower.
    sample_rate = 10

    # Iterate over the dataset edges at the sample rate
    for x in range(0, x_size, sample_rate):
        for y in [0, y_size - 1]:  # top and bottom edges
            # Get pixel (x, y) coordinates in dataset's projection
            x_geo = geotransform[0] + x * geotransform[1]
            y_geo = geotransform[3] + y * geotransform[5]

            # Transform the coordinates to lat/lon
            lon, lat, _ = transform.TransformPoint(x_geo, y_geo)

            # Update min/max lat and lon
            lat_min = min(lat_min, lat)
            lat_max = max(lat_max, lat)
            lon_min = min(lon_min, lon)
            lon_max = max(lon_max, lon)

    for y in range(0, y_size, sample_rate):
        for x in [0, x_size - 1]:  # left and right edges
            # Get pixel (x, y) coordinates in dataset's projection
            x_geo = geotransform[0] + x * geotransform[1]
            y_geo = geotransform[3] + y * geotransform[5]

            # Transform the coordinates to lat/lon
            lon, lat, _ = transform.TransformPoint(x_geo, y_geo)

            # Update min/max lat and lon
            lat_min = min(lat_min, lat)
            lat_max = max(lat_max, lat)
            lon_min = min(lon_min, lon)
            lon_max = max(lon_max, lon)

    print([lat_min, lon_min, lat_max, lon_max])
    extent = [lat_min, lon_min, lat_max, lon_max]
    
    #export file
    if (output_file != None or export_json == True):
        print("exported")
        saveToJSON(extent, output_file, model)

        # Return the extent in lon/lat
    return extent

def calculateAspectRatio(extent):
    """
    Calculate the aspect ratio (width / height) of the raster from its extent.
    """
    x_min, y_min, x_max, y_max = tuple(extent)
    
    # Calculate width and height
    width = x_max - x_min  # Distance in the X direction (longitude or X axis)
    height = y_max - y_min  # Distance in the Y direction (latitude or Y axis)
    
    # Aspect ratio = width / height
    if height != 0:  # Prevent division by zero
        aspect_ratio = width / height
    else:
        aspect_ratio = None  # Undefined aspect ratio
    
    return aspect_ratio

def convertFromNCToPNG(inputFile="input.tif", exportFile="output.png", extent=None, vmin=0, vmax=10, nodata=None, model=None, width=None):
    '''
    Converts a NetCDF (or GeoTIFF) file to a grayscale PNG.

    This function processes only the first raster band of the input file. 
    Values are set in a RGB array which contains 256-base of the raster base
    giving a 24-bit image that can afterwards be processed.
    Calculates automatically width


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
    model (str): (optional) model name for extent name
                 if extent not set, model use for render setting the extent
                 in a file and naming it

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

    # Get the geotransform and projection from the source dataset
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()

    #arrange array to rgb standards
    rgb_array = float_to_rgb(data_array, vmin, vmax)

    if (extent==None):
        extent = get_raster_extent_in_lonlat(dataset, model)

    # Create an in-memory dataset to hold the RGB data
    driver = gdal.GetDriverByName('MEM')
    rows, cols, _ = rgb_array.shape
    rgb_dataset = driver.Create('', cols, rows, 3, gdal.GDT_Byte)
    
    # Inject the geotransform and projection into the new dataset
    rgb_dataset.SetGeoTransform(geotransform)
    rgb_dataset.SetProjection(projection)
    
    # Write the RGB bands to the dataset
    for i in range(3):  # R, G, B
        rgb_dataset.GetRasterBand(i + 1).WriteArray(rgb_array[:, :, i])
    
    # determine height
    if (width != None):
        width_resolution = width
    else:
        width_resolution = file_width_resolution
    
    height_resolution = width_resolution/calculateAspectRatio(extent)

    gdal.Warp(
        exportFile,
        rgb_dataset,
        dstSRS="EPSG:4326",
        outputBounds=extent,
        width=int(abs(width_resolution)),
        height=int(abs(height_resolution)),
        srcNodata=nodata,
        outputType=gdal.GDT_Byte,
        creationOptions=['ZLEVEL=1'],
        format="PNG"
    )

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
