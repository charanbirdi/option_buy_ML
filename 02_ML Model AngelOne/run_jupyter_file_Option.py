#-----Python file for Training Machine Learning Models----
# First - Get Historical Data
# Second - Train ML model with jupyter file

# Best resourse for importing information from python file to jupyter Notebook
# https://felixchenier.uqam.ca/a-better-way-to-run-a-jupyter-notebook-with-arguments/




import json
import subprocess
import time
import subprocess
import sys

from termcolor import colored

from Download_Historical_Data_for_ML import hist_data_extended 

data_duration = 2021  # Year from where data is required, as per ANGLEONE, we are getting till 2016 in 2023 year
interval = "ONE_HOUR"

#-------Sleep time variable----------------------
sleep_time_long = 7
sleep_time_short = 5

try_count_long = 2
try_count_short = 2


#tickers = ["BANKNIFTY", "NIFTY", "INDIA VIX"]
tickers = ["BANKNIFTY", "NIFTY", "FINNIFTY"]


def check_return_code(return_code):
    if return_code == 0:
        print(colored("ML Model jupyter file executed successfully.", 'magenta'))
    else:
        print("ML Model jupyter file failed with return code", return_code)
   
    

def run_ML_notebook(notebook_file, **arguments):
    
    print(colored(f"\nHistorical Data ~~ {arguments['ticker']}", "green"))    
    df = hist_data_extended(arguments['ticker'], data_duration, interval) # Call MODULE for historical Data
    #print(df)
    
   
    print(colored(f"ML Jupyter file running for ~~ {arguments['ticker']}", "green"))
    
    """Pass arguments to a Jupyter notebook, run it and convert to html.
       We will store that arguments in jason file which will be stored locally and 
       later JUpyter notebook take that argument for checking stock for which jupyter notebook
       needs to be run.    
    """
    
    
    # Create the arguments file
    with open('arguments.json', 'w') as fid:
        json.dump(arguments, fid)
        
    run_final(notebook_file)
    
    


#try_con = 0
def run_final(notebook_file):
    global try_con
    try:
        # Run the notebook
        # subprocess.call() will run the process and will move to next command only when task is completed.
        exit_code_ML = subprocess.call([
            'jupyter-nbconvert',
            '--execute',
            '--to', 'html',
            #'--output', output_file,
            notebook_file])
        
        check_return_code(exit_code_ML)
        if exit_code_ML != 0:
            raise Exception("This is an exception")
        try_con = 0

    except Exception as e:
            print(colored(f"RUN CODE failed: {e}", 'red'))
            try_con = try_con+1        
            if try_con <= 5:
                print(colored(f"TRYYY-{try_con} again after {sleep_time_short} sec", 'red'))
                time.sleep(sleep_time_short)
                run_final(notebook_file)
            else:
                print(colored(f"Better Luck next time, NOTEBOOK MUST HAVE ERROR", 'red'))
                #sys.exit(0) # 0- without error message, 1-with error message in end 
                # Disabled above , so that atleast historical data ran for all tickers
        
    
# Run the notebook with different arguments
for ticker in tickers:
    #print(f"RUnning for~~~~{ticker}")
    try_con = 0
    run_ML_notebook('AngleOne_ML_Model_Option.ipynb', ticker=ticker)






