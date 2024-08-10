"""
This is mail python file which will connect to AngelOne Server

https://github.com/angel-one/smartapi-python
https://www.insertcart.com/angle-broker-smartapi-setup-guide-with-full-python-api-source-code/


#####OPTION Strategy#############
https://www.gettogetherfinance.com/blog/best-options-strategy/#Iron_butterfly_creditnon-directional

"""

#----------for current folder path------------
#import pathlib
#current_folder_path = pathlib.Path(__file__).parent.resolve()
#df_data.to_csv(f'{current_folder_path}\\01_Data\data_{ticker}.csv')
#---------------------------------------------
from termcolor import colored
#print(colored('hello', 'red'), colored('world', 'green'))

import sys

from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect

#from memory_profiler import profile




import os
import urllib
import json
from pyotp import TOTP # for getting OTP

import threading
import time

import pandas as pd

import datetime as dt
from datetime import timedelta

from statistics import mean

#https://docs.xlwings.org/en/stable/syntax_overview.html
import xlwings as xw

starttime = time.time()

#-------Sleep time variable----------------------
sleep_time_long = 7
sleep_time_short = 4

try_count_long = 7
try_count_short = 4







API_KEY = 'oPvM0VnS' #
CLIENT_CODE = 'C52284659'
PWD = '1030' #Your Pin
AUTH_TOKEN = '2a68e665-d2d5-42b6-9c73-c2139545c8c0'  #Your QR code value
token = 'PGAFWLOTMLQKIR3EMWOGHU6KVY' #for OTP https://smartapi.angelbroking.com/enable-totp


try_con = 0
def connect_ANGELONE():
    global try_con
    global obj
    try:
        obj=SmartConnect(api_key=API_KEY)
        data = obj.generateSession(CLIENT_CODE, PWD, TOTP(token).now())
        feed_token = obj.getfeedToken()        
        if obj is None:
            raise Exception("This is an exception")
        
        try_con = 0
        print(colored(f"CONNECTED TO ANGELONE SERVER $$$$$", 'green'))
        return obj
    
    except Exception as e:
        print(f"CONNECTION Api failed: {e}")
        try_con = try_con+1        
        if try_con <= try_count_long:
            print(colored(f"TRYYY-{try_con} again after {try_con*sleep_time_short} sec", 'red'))
            time.sleep(try_con*sleep_time_short)
            obj = connect_ANGELONE()
            return obj
        else:
            print(colored(f"Better Luck next time, Connection not established", 'red'))
            sys.exit(0) # 0- without error message, 1-with error message in end 
            
#connect_ANGELONE() # Connect with AngelOne API

# --------------------From AngelOne API github page --------------------------------
#retry_strategy=0 for simple retry mechanism
#sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, feed_token, max_retry_attempt=2, retry_strategy=0, retry_delay=10, retry_duration=30)

#retry_strategy=1 for exponential retry mechanism
# sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, feed_token, max_retry_attempt=3, retry_strategy=1, retry_delay=10,retry_multiplier=2, retry_duration=30)
# --------------------End of From AngelOne API github page --------------------------------

# correlation_id = "stream_1" #any string value which will help identify the specific streaming in case of concurrent streaming
# action = 1 #1 subscribe, 0 unsubscribe
# mode = 1 #1 for LTP, 2 for Quote and 2 for SnapQuote


def check_instrument_list_modification_datetime():
    
    # Get the last modified time of the file.
    timestamp = os.path.getmtime('OpenAPIScripMaster.json')
    days_till_last_update = (dt.datetime.now() - dt.datetime.fromtimestamp(timestamp)).seconds
    #days_till_last_update = (dt.datetime.now() - dt.datetime.fromtimestamp(timestamp))/timedelta(days=1) # as compared to above code , it will give days in decimal also
    
    last_update_hour = round(days_till_last_update/3600,2)
    
    #print(last_update_hour)    
    if last_update_hour >= 7: # from 9:15AM to 3:30PM, so end of market day it will update. 
        print(colored(f"Instrument List is {last_update_hour} Hours old, better to Update it now", "red"))
        return "update"
    
    return "Not_to_update"


    


try_inst = 0
def instrument_list_ANGELONE():
    
    
    # if want to download again then comment following 3 lines----
    if check_instrument_list_modification_datetime() == "Not_to_update":
        print("Loadingg previously saved Instrument List file....")
        instrument_list = json.load(open('OpenAPIScripMaster.json'))
        return instrument_list # Function terminate here
    
    
    
    
    print(colored("Instrument List is downloading.......", 'green'))
    global try_inst
    try:
        instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        response = urllib.request.urlopen(instrument_url)
        instrument_list = json.loads(response.read())        
        
        if instrument_list is None:
            raise Exception("Instrument List failed to download")
        #try_inst = 0
        
        
        #----Save JASON file for later use to save time--------
        with open("OpenAPIScripMaster.json", "w") as outfile:
            print("Saving Instrument List for Later use to save time")
            json_object = json.dumps(instrument_list)
            outfile.write(json_object)
    
    
        return instrument_list

    except Exception as e:
    #except IOError as e:
    #except TimeoutError as e:
            print(colored(f"RUN CODE failed: {e}", 'red'))
            try_inst = try_inst+1        
            if try_inst <= 5:
                print(colored(f"TRYYY-{try_con} again after {try_inst*sleep_time_short} sec", 'red'))
                time.sleep(try_inst * sleep_time_short)
                instrument_list = instrument_list_ANGELONE()
                return instrument_list
            else:
                print(colored(f"Better Luck next time, NOTEBOOK MUST HAVE ERROR", 'red'))
                sys.exit(0) # 0- without error message, 1-with error message in end 
            
    
        
    
if __name__ == "__main__":
    connect_ANGELONE()
    instrument_list_ANGELONE()
    
    
    
    
    
    