from datetime import datetime, timedelta, timezone
from time import sleep
import urllib.request
from multiprocessing import Process
import os

timeToDownload = 30

#models Wait for first file available in minutes (delay before availability)
modelsLeadTime = {"HRRR": 48,
                  "HRRRSH": 48,
                  "NAMNEST": 100,
                  "HRDPS": 195
                  }
#models interval of outputs per day in hours (hours between each runs)
modelsIntervalOfOutputs = {"HRRR": 1,
                           "HRRRSH": 1,
                           "NAMNEST": 6,
                           "HRDPS": 6
                           }

def isItTimeToDownload(model):
    """
    Determines if it's time to download data from a weather model based on the model's update frequency and lead time.
    
    The function calculates the model's output times for the current day, compares the current time with the latest available run,
    and checks if the download window is open. If it is time to download, the function returns True, the hour of the latest run,
    and the current date. If it's not time yet, it returns False, the time remaining before the next run, and the current date.
    
    Parameters:
    model : str
        The name of the weather model to check.
    
    Returns:
    tuple:
        - bool : True if it's time to download, False otherwise.
        - int or float : The hour of the latest run or the time before the next run (in seconds).
        - str : The current date in "YYYYMMDD" format.
    """

    modelLeadTime = modelsLeadTime[model]
    current_time = datetime.now(timezone.utc)

    listOfOutputTimes = []
    for hour in range(0, 24, modelsIntervalOfOutputs[model]):
        listOfOutputTimes.append(
            datetime(current_time.year,
                    current_time.month, 
                    current_time.day, 
                    hour, 
                    0, 
                    tzinfo=timezone.utc) + timedelta(
                        minutes=modelLeadTime)
        )
    
    # get latest run available
    latestRun = None
    for i, outputTimes in enumerate(listOfOutputTimes):
        if (current_time>outputTimes):
            latestRun = outputTimes
    
    # Current time is the day after last run
    if (latestRun==None):
        #2 days because of utc time aware
        latestRun = listOfOutputTimes[-1]-timedelta(days=2)
        current_time = current_time-timedelta(days=1)

    if (latestRun<current_time<latestRun+timedelta(minutes=timeToDownload)):
        return True, latestRun.hour-modelLeadTime//60, current_time.strftime("%Y%m%d")
    else:
        time_before_next_run = ((latestRun + timedelta(hours=modelsIntervalOfOutputs[model]))-current_time).total_seconds()
        return False, time_before_next_run, current_time.strftime("%Y%m%d")


def linkGenerator(model, run, forecastTime, variables, current_time=None, server=None, sharedModel=None):
    """
    Generates a download link for weather model data from the specified server, based on the model, run time, forecast time, variable, and level.

    For the "NOMADS" server, the function constructs a URL to access the data for the HRRR model. If no current time is provided, 
    it defaults to the current UTC time and formats it as "YYYYMMDD". The link includes the specified variable and level parameters.

    Parameters:
    model : str
        The name of the weather model (e.g., "HRRR").
    run : int
        The model run time (e.g., "00" for 00Z).
    forecastTime : int
        The forecast hour (e.g., 3 for the 3-hour forecast).
    variables: dict 
        variables as keys and items as level
    current_time : str, optional
        The current date in "YYYYMMDD" format. Defaults to the current UTC time.
    server : str, optional
        The server to use for the data download. Defaults to "NOMADS".
    sharedModel : model object with server proprety

    Returns:
    str:
        The download link for the specified weather model data.
    
    Raises:
    NotImplementedError:
        If a server other than "NOMADS" is specified.
    """

    if (server==None):
        if (model in ["HRRR","HRRRSH","NAMNEST"]):
            server = "NOMADS"
        elif (model in ["HRDPS","GDPS","RDPS"]):
            server = "HPFX"
    
    #set server attribute to object model
    try:
        sharedModel.server = server
    except:
        pass

    if (server=="NOMADS"):
        serverUrl = r"https://nomads.ncep.noaa.gov/cgi-bin/"
        
        if (current_time == None):
            current_time = datetime.now(timezone.utc)
            current_time = f"{current_time.year:04}{current_time.month:02}{current_time.day:02}"

        if (model=="HRRR"):
            isRunNbGood(run, model)

            variableURL = ""
            for variable in variables:
                for level in variables[variable]:
                    variableURL += f"var_{variable}=on&{level}=on&"
            
            url=f"{serverUrl}filter_hrrr_2d.pl?dir=%2Fhrrr.{current_time}%2Fconus&file=hrrr.t{run}z.wrfsfcf{str(forecastTime).zfill(2)}.grib2&{variableURL}"
            print (f"download link: {url}")
            return [url]
        elif (model=="HRRRSH"):
            isRunNbGood(run, model)
            
            variableURL = ""
            for variable in variables:
                for level in variables[variable]:
                    variableURL += f"var_{variable}=on&{level}=on&"

            url=f"{serverUrl}filter_hrrr_sub.pl?dir=%2Fhrrr.{current_time}%2Fconus&file=hrrr.t{run}z.wrfsubhf{str(forecastTime).zfill(2)}.grib2&{variableURL}"
            print (f"download link: {url}")
            return [url]
        elif (model=="NAMNEST"):
            isRunNbGood(run, model)

            variableURL = ""
            for variable in variables:
                for level in variables[variable]:
                    variableURL += f"var_{variable}=on&{level}=on&"
            url=f"{serverUrl}filter_nam_conusnest.pl?dir=%2Fnam.{current_time}&file=nam.t{run}z.conusnest.hiresf{str(forecastTime).zfill(2)}.tm00.grib2&{variableURL}"
            print (f"download link: {url}")
            return [url]

        else:
            raise Exception("model not implemented in current server")
    
    elif (server=="MSC"):
        raise Exception("server not yet implemented (WIP), use HPFX instead")

    elif (server=="HPFX"):
        serverURL = "http://hpfx.collab.science.gc.ca"
        isRunNbGood(run, model)
        if (current_time == None):
            current_time = datetime.now(timezone.utc)
            current_time = f"{current_time.year:04}{current_time.month:02}{current_time.day:02}"
        
        if (model=="HRDPS"):  
            isRunNbGood(run, model)
            url = []
            for variable in variables:
                for level in variables[variable]:
                    #https://hpfx.collab.science.gc.ca/20250123/WXO-DD/model_hrdps/continental/2.5km/06/001/20250123T06Z_MSC_HRDPS_DPT_AGL-2m_RLatLon0.0225_PT001H.grib2
                    remoteFilename = f"{current_time}T{run}Z_MSC_HRDPS_{variable}_{level}_RLatLon0.0225_PT{str(forecastTime).zfill(3)}H.grib2"
                    url.append(f"{serverURL}/{current_time}/WXO-DD/model_hrdps/continental/2.5km/{run}/{str(forecastTime).zfill(3)}/{remoteFilename}") 
                    print (f"download link: {url}")
            return url


    else:
        raise Exception("server not implemented")

    return url

def isRunNbGood(run, model):
    if (int(run) not in range(0, 24, modelsIntervalOfOutputs[model])):
        raise Exception(str(run) + " is not in the model's accepted runs: " + str([hour for hour in range(0, 24, 6)]))
        return False
    return True

def download(link, filepath = None, numbersOfRetry = 30, delayBeforeTryingAgain = 35):
    
    downloadedFiles = []

    #if only one link, put it into array
    if (isinstance(link, str)):
        link = [link]

    for link in link:
        for test in range(numbersOfRetry):
            #skip urlParams
            filename = (link.split("/")[-1]).split("?")[0]
            if ("nomads" in link):
                filename = filename.replace("pl","grib2")
                print(filename)
            print("link " + link)
            downloadPath = filepath + filename
            
            try:
                print(f"downloading try: {test}")
                print(link)

                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                status = urllib.request.urlopen(link).getcode()
                urllib.request.urlretrieve(link, downloadPath) #download the file
                f = open(downloadPath)
                f.close()
                downloadedFiles.append(downloadPath)
                break
            except Exception as e:
                print("Download unsuccessful")
                print(e)
                sleep(delayBeforeTryingAgain)
                pass
        else:
            raise Exception("Download unsucessful, numbersOfRetry reached")
    return downloadedFiles

def download_model(model, run, variables, forecastTime=None, forecastNb=None, current_time=None, sharedModel=None):
    """
    Downloads HRRR model data for a given run and forecast time.

    If no specific forecast time is provided, the function iterates over all forecast hours for the run. 
    It generates download links for each variable and level, and saves the data in the appropriate directory.

    Parameters:
    - model : str
        The model name (e.g., "HRRR")
    - run : str
        The model run time (e.g., "00", "06", "12", or "18").
    - variables: dict
        variables as keys and their item represent a list of the height to download
    - forecastNb : int or None
        Numbers of forecast in the model does, if in non-automated run (if forecastTime==None)
    - forecastTime : str or None
        The forecast hour to download (e.g., "03" for the 3-hour forecast). If None, all available forecast times are downloaded.
    - current_time : str
        The current date in "YYYYMMDD" format.
    
    Returns:
    - The output filepath: list
    """
    print(f"started download {model}")
    if (model=="HRRR"):
        if (run in ["00","06","12","18"]):
            forecastNb = 48
        else:
            forecastNb = 18

    
    #iterate over all forecastNb
    if (forecastTime==None):
        outputFile = []
        for forecast in range(forecastNb):
            preOutputFile = f"./downloads/{model}/{run}/total.{forecastTime}."
            forecastTime = str(forecast).zfill(2)
            download_link = linkGenerator(model,run,forecastTime,variables,current_time,sharedModel=sharedModel)
            outputFile.append(download(download_link, preOutputFile))

        return outputFile
    
    #in automated run:
    else:
        preOutputFile = f"./downloads/{model}/{run}/total.{forecastTime}."
        download_link = linkGenerator(model,run,forecastTime,variables,current_time,sharedModel=sharedModel)
        return download(download_link, preOutputFile)
        
 

def waitForDataAvailable():
    """
    Checks the availability of weather model data and initiates the download process when data becomes available.

    The function loops through all models defined in `modelsLeadTime`. It uses `isItTimeToDownload` to check if
    data is ready for each model. If data is available, a new process is started to download the data using the 
    corresponding model's download function. If data is not yet available, it prints the time remaining before the next
    download window.

    Process:
    - Each model's availability is checked.
    - If data is available, the download is initiated in a separate process.
    - If data is not yet available, the time remaining before the download is printed.
    
    """
    for models in modelsLeadTime.keys():
        isAvailable, timeOutput = isItTimeToDownload(models)
        if (isAvailable):
            print(f"{models} is available for {timeOutput}z")
            # 2 digit attributes
            p = Process(target=globals()["download_" + models], args=((str(timeOutput).zfill(2),)))
            p.start()
            p.join()
                
        else:
            print(f"Time before downloading: {timeOutput}")
    

if __name__ == "__main__":
    while(1):
        waitForDataAvailable()