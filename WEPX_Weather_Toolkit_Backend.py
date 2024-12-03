from multiprocessing import Process
from time import sleep
import download
import convert
import shutil
from os import system

list_of_models = ["HRRR"]
forecastNbDict = {"HRRR":"18"}
vminDict = {"DPT":-60,
            "REFC": -10,
            "CAPE": -1,
            "CIN":-1000,
            "RETOP":0}
vmaxDict = {"DPT":60,
            "REFC": 80,
            "CAPE": 8000,
            "CIN": 1,
            "RETOP":25
            }

#variables to download for each models and surface level
variablesHRRR = {"RETOP":["all_lev"], 
                 "CAPE":["lev_surface"],
                 "CIN":["lev_surface"],
                 "DPT":["lev_2_m_above_ground"],
                 "REFC":["all_lev"]
                 }

#extent of full output
#extent=[-143.261719,13.410994,-39.023438,60.930432]

download.timeToDownload = 59
convert.export_json = True

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
        if (run in ["00", "06", "12", "18"]):
            forecastNb = 48
        else:
            forecastNb = 18
    else:
        forecastNb = forecastNbDict[model]
    
    try:
        shutil.rmtree("../WEPX Website/downloads/" + model + "/" + run)
    except Exception as e:
        print(e)

    for forecast in range(forecastNb):
        system("title Running " + model + " for run " + run + " on forecast " + str(forecast).zfill(2))
        print("downloading")
        forecast = str(forecast).zfill(2)
        gribFiles = getattr(download, "download_"+model)(run, variablesHRRR, forecast,current_time)
        
        print("convert to PNG")
        
        for file in gribFiles:
            #in same folder as grib2 (but still get same name of grib2)
            pngPath = "../WEPX Website/" + ".".join(file.split(".")[:-1]) + "."
            print(pngPath)
            pngFiles = convert.convertFromNCToPNG(file, pngPath, variablesHRRR, vmin=vminDict,vmax=vmaxDict, model=model)

        print("convert to WEBP")
        for file in pngFiles:
            #in same folder as png
            webpFilename = ".".join(file.split(".")[:-1]) + ".webp"
            webpFiles = convert.convertToWEBP(file, webpFilename)
    
while(1):
    for model in list_of_models: 
        isItTimeToDownload, timeOutput, current_time = download.isItTimeToDownload(model)
        if(isItTimeToDownload):
            processModel(model, timeOutput, current_time)
                
        else:
            print(f"Time before downloading: {timeOutput}")
            sleep(10)
