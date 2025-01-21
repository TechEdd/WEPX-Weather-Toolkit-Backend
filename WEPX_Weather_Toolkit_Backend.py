from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import threading
from time import sleep
import download
import convert
import shutil
from os import system

list_of_models = ["NAMNEST"]
forecastNbDict = {"HRRR":18,
                  "HRRRSH":18,
                  "NAMNEST":60
                  }
#absolute highest and lowest
vminDict = {"DPT":-80,
            "TMP":-80,
            "REFC": -10,
            "CAPE": 0,
            "CIN":-4000,
            "RETOP":0,
            "HAIL":0,
            "SBT124": 100,
            "BRTMP": 100,
            "GUST": 0
            }
vmaxDict = {"DPT":80,
            "TMP":80,
            "REFC": 100,
            "CAPE": 14000,
            "CIN": 0,
            "RETOP":25000,
            "HAIL":1,
            "SBT124": 400,
            "BRTMP": 400,
            "GUST": 115
            }

#variables to download for each models and surface level
variablesHRRR = {"RETOP":["lev_cloud_top"], 
                 "CAPE":["lev_surface"],
                 "CIN":["lev_surface"],
                 "DPT":["lev_2_m_above_ground"],
                 "TMP":["lev_2_m_above_ground"],
                 "HAIL":["lev_0.1_sigma_level"],
                 "REFC":["lev_entire_atmosphere"],
                 "SBT124":["lev_top_of_atmosphere"]
                 }
variablesHRRRSH = {"RETOP":["lev_cloud_top"],
                 "REFC":["lev_entire_atmosphere"],
                 "SBT124":["lev_top_of_atmosphere"]
                 }

variablesNAMNEST = {"RETOP":["lev_cloud_top"], 
                 "CAPE":["lev_surface"],
                 "CIN":["lev_surface"],
                 "DPT":["lev_2_m_above_ground"],
                 "TMP":["lev_2_m_above_ground"],
                 "REFC":["lev_entire_atmosphere_(considered_as_a_single_layer)"],
                 "BRTMP":["lev_top_of_atmosphere"]
                 }

#extent of full output
#extent=[-143.261719,13.410994,-39.023438,60.930432]

download.timeToDownload = 35
convert.export_json = True


# Dictionary to keep track of running models
running_models = {}
lock = threading.Lock()

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
        shutil.rmtree('\\\\192.168.0.54\\testing\\downloads\\' + model + '\\' + run)
        shutil.rmtree("downloads/" + model + "/" + run)

    except Exception as e:
        print(e)

    for forecast in range(forecastNb+1):
        system("title Running " + model + " for run " + run + " on forecast " + str(forecast).zfill(2))
        print("downloading")
        forecast = str(forecast).zfill(2)
        gribFiles = download.download_model(model, run, globals()["variables" + model], forecast, current_time)
        
        print("convert to PNG")
        
        for file in gribFiles:
            #in same folder as grib2 (but still get same name of grib2)
            pngPath = '\\\\192.168.0.54\\testing\\' + ".".join(file.split(".")[:-1]) + "."
            print(pngPath)
            pngFiles = convert.convertFromNCToPNG(file, pngPath, globals()["variables" + model], vmin=vminDict,vmax=vmaxDict, model=model)

        print("convert to WEBP")
        for file in pngFiles:
            #in same folder as png
            webpFilename = ".".join(file.split(".")[:-1]) + ".webp"
            webpFiles = convert.convertToWEBP(file, webpFilename)

with ThreadPoolExecutor() as executor:    
    while(1):
        for model in list_of_models:
            isItTimeToDownload, timeOutput, current_time = download.isItTimeToDownload(model)
            
            if isItTimeToDownload:
                with lock:
                    # Check if the model is already being processed
                    if model not in running_models:
                        print(f"Processing model: {model}")
                        # Submit the original processModel function to the executor
                        future = executor.submit(processModel, model, timeOutput, current_time)
                        # Track the running task
                        running_models[model] = future

                        # Attach a callback to remove from the dictionary once complete
                        def remove_model_callback(fut):
                            with lock:
                                running_models.pop(model, None)
                        
                        future.add_done_callback(remove_model_callback)
                    
            else:
                print(f"Time before downloading {model}: {timeOutput}")
                sleep(10)
