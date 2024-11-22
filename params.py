list_of_models = ["HRRR"]
#numbers of forecast done by weather model
forecastNbDict = {"HRRR":"18"}
#absolute maximum to render iamge
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

#variables to download for each models and surface level
variablesHRRR = {"RETOP":["all_lev"], 
                 "CAPE":["lev_surface"],
                 "CIN":["lev_surface"],
                 "DPT":["lev_2_m_above_ground"],
                 "REFC":["all_lev"]
                 }

#extent of full output
#extent=[-143.261719,13.410994,-39.023438,60.930432]
#max delay for downloading a run
download.timeToDownload = 59
#save to json the weather model extent
convert.export_json = True
#models Wait for first file available in minutes
download.modelsLeadTime = {"HRRR": 48}
#models interval of outputs per day in hours
download.modelsIntervalOfOutputs = {"HRRR": 1}

convert.debug = True
convert.export_json = True
convert.file_width_resolution = 3000
convert.output_json_file = "model_extent.json"