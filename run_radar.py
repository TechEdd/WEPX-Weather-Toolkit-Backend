import time
import json
import os
from multiprocessing import Process
import threading
import traceback
import pyart
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import download
import convert
import secret

jsonlatlonPath = "radar_latlon.json"

list_of_radars = {
    "canada": ["CASBV","CASSF","CASFT"]
    }
#absolute range for variables with multiplicator (needs to equal from 0 to 256 for rgb)
variablesRange = {
    "reflectivity_horizontal" : [-20,108],
    "velocity_horizontal" : [-64,63],
    "differential_reflectivity" : [-8,7],
    "specific_differential_phase" : [-2,13],
    "cross_correlation_ratio": [0.2,1.2],
    "total_power_horizontal" : [-20,108],
    "echo_tops" : [0, 25600]
    }
variablesWithFullTilts = ["reflectivity_horizontal","velocity_horizontal"]
variablesWithOneTilt = ["echo_tops"]
limitedTilts = 4;

#numbers of time in minutes to wait for a new file
canadaFileSteps = 6
canadaListOfMinutes = range(0, 60, canadaFileSteps)

def latlonToJSON(radar, radarID, filename=jsonlatlonPath):
    lat = radar.latitude['data'][0]
    lon = radar.longitude['data'][0]
    max_range = str(radar.range['data'].max())
    
    # Load existing data if file exists
    if os.path.exists(filename):
        with open(filename, "r") as f:
            radar_data = json.load(f)
    else:
        radar_data = {}

    # Update or add radar position
    radar_data[radarID] = {"lat": lat, "lon": lon, "range": max_range}

    # Save back to JSON
    with open(filename, "w") as f:
        json.dump(radar_data, f, indent=4)

    print(f"Radar position updated in {filename}")

def processCanadianRadar(radarID, filename, server="HPFX", formatted_date=None):
    if (formatted_date==None):
        formatted_date = datetime.now(timezone.utc).strftime('%Y%m%d')
        
    if (server=="HPFX"):
        serverName = "hpfx.collab.science.gc.ca"
        url=f"http://{serverName}/{formatted_date}/radar/volume-scans/{radarID}/{filename}"

    downloaded_files = download.download(url, "downloads/", username=secret.username, password=secret.password)
    for file in downloaded_files:
        radar = convert.decodeCanadianRadar(file)
        radar = convert.addRadarVariable("Echo Tops",radar)
        latlonToJSON(radar, radarID)
        for variable in list(radar.fields.keys()):
            if variable in list(variablesRange.keys()):
                if variable in variablesWithFullTilts:
                    nbTilts = range(radar.nsweeps)
                elif variable in variablesWithOneTilt:
                    nbTilts = [radar.nsweeps-1]
                else:
                    nbTilts = range(radar.nsweeps-limitedTilts,radar.nsweeps)

                for sweep in nbTilts:
                    print(f"doing sweep {sweep} for {variable} for radar {radarID}: {file}")
                    export_filename = f"downloads/radars/{radarID}/{variable}.tilt{str(radar.nsweeps-sweep)}"
                    convert.processRadarSweep(radar, variable, sweep, variablesRange[variable], export_filename)

    globals()["lastFilename_" + radar] = filename
    time.sleep(60)


# Dictionary to keep track of running models
running_radars = {}
lock = threading.Lock()
if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:

        #initialize last filname of radars variables
        for radar in list_of_radars["canada"]:
            globals()["lastFilename_" + radar] = None

        while(1):
            #canada
            utc_now = datetime.now(timezone.utc)
            minutes_now = utc_now.minute
            hours_now = f"{utc_now.hour:02}"
            
            if (minutes_now in canadaListOfMinutes):
                for radar in list_of_radars["canada"]:
                    isNewFile, filename = download.isNewRadarFile("HPFX",radar,globals()["lastFilename_" + radar])
                    if(isNewFile):
                        with lock:
                            # Check if the model is already being processed
                            if radar not in running_radars:
                                print(f"Processing radar: {radar}")
                                # Submit the original processModel function to the executor
                                future = executor.submit(processCanadianRadar, radar, filename)
                                # Track the running task
                                running_radars[radar] = future

                                # Attach a callback to remove from the dictionary once complete
                                def remove_model_callback(fut, radar=radar):
                                    with lock:
                                        running_radars.pop(radar, None)
                        
                                future.add_done_callback(remove_model_callback)
            time.sleep(5)