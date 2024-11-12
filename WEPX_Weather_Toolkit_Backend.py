from multiprocessing import Process
from time import sleep
import download
import convert

list_of_models = ["HRRR"]
forecastNbDict = {"HRRR":"18"}
vminDict = {"DPT":-60,
            "REFC": -10,
            "CAPE": 0,
            "CIN":-1000,
            "RETOP":0}
vmaxDict = {"DPT":60,
            "REFC": 80,
            "CAPE": 8000,
            "CIN": 0,
            "RETOP":25
            }

#extent of full output
#extent=[-143.261719,13.410994,-39.023438,60.930432]

download.timeToDownload = 59;

def processModel(model, timeOutput,current_time):
    """
    Downloads weather model data for a specified model and time, and converts the downloaded files to PNG and WEBP formats.

    The function first determines the number of forecast hours to download based on the model and run time. It then iterates
    through each forecast hour, downloads the corresponding data, converts the data from GRIB to PNG, and finally converts 
    the PNG to WEBP format for web use.

    Parameters:
    - model : str
        The weather model to process (e.g., "HRRR").
    - timeOutput : int
        The model run time, which will be zero-padded to two digits (e.g., 00, 06, 12, 18).
    - current_time : str
        The current date in "YYYYMMDD" format used for downloading the correct dataset.
    
    Process:
    - Determine the number of forecast hours based on the model and run time.
    - Download the GRIB2 data for each forecast hour.
    - Convert each GRIB2 file to PNG using a variable-specific range (vmin, vmax).
    - Convert the PNG files to WEBP format for optimized web use.
    """
    print(current_time)
    run = str(timeOutput).zfill(2)
    if (model=="HRRR"):
        if (run == "00" or run == "06" or run == "12" or run == "18"):
            forecastNb = 48
        else:
            forecastNb = 18
    else:
        forecastNb = forecastNbDict[model]

    for forecast in range(forecastNb):
        print("downloading")
        forecast = str(forecast).zfill(2)
        gribFile, variable = getattr(download, "download_"+model)(run,forecast,current_time)
        for i, files in enumerate(gribFile):
            #take files name but change extension
            pngFile = str(".".join(files.split(".")[:-1]))+".png"
            webpFile = str(".".join(files.split(".")[:-1]))+".webp"
            print("convert to PNG")
            convert.convertFromNCToPNG(files, pngFile, vmin=vminDict[variable[i]],vmax=vmaxDict[variable[i]], model=model)
            print("convert to WEBP")
            convert.convertToWEBP(pngFile,webpFile)
    
while(1):
    for model in list_of_models:
        isItTimeToDownload, timeOutput, current_time = download.isItTimeToDownload(model)
        if(isItTimeToDownload):
            processModel(model, timeOutput, current_time)
                
        else:
            print(f"Time before downloading: {timeOutput}")
            sleep(10)

