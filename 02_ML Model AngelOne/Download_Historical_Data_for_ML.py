"""
This file will be used for DOWNLOADING historical data for long time
It will not supposed to run in isolation but called from another programe
"""

#----------for current folder path------------
import pathlib
current_folder_path = pathlib.Path(__file__).parent.resolve()
#---------------------------------------------

from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect

import os
import urllib
import json
from pyotp import TOTP # for getting OTP

from statistics import mean

import time
import datetime as dt
from datetime import timedelta

import threading
import pandas as pd

from termcolor import colored

starttime = time.time()


API_KEY = 'oPvM0VnS'
CLIENT_CODE = 'C52284659'
PWD = '1030' #Your Pin
AUTH_TOKEN = '2a68e665-d2d5-42b6-9c73-c2139545c8c0'  #Your QR code value
token = 'PGAFWLOTMLQKIR3EMWOGHU6KVY' #for OTP https://smartapi.angelbroking.com/enable-totp


#-------Sleep time variable----------------------
sleep_time_long = 20
sleep_time_short = 7

try_count_long = 7
try_count_short = 4



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
        print(colored(f"\n###### CONNECTED TO ANGELONE SERVER FOR DOWNLOADING DATA ONLY ######", 'green'))
        return None
    
    except Exception as e:
        print(f"CONNECTION Api failed: {e}")
        try_con = try_con+1        
        if try_con <= try_count_long:
            print(colored(f"TRYYY-{try_con} again after {try_con*sleep_time_short} sec", 'red'))
            time.sleep(try_con*sleep_time_short)
            connect_ANGELONE()
        else:
            print(colored(f"Better Luck next time, Connection not established", 'red'))
            sys.exit(0) # 0- without error message, 1-with error message in end 
            
connect_ANGELONE() # Connect with AngelOne API










correlation_id = "stream_1" #any string value which will help identify the specific streaming in case of concurrent streaming
action = 1 #1 subscribe, 0 unsubscribe
mode = 1 #1 for LTP, 2 for Quote and 2 for SnapQuote



# instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
# response = urllib.request.urlopen(instrument_url)
# instrument_list = json.loads(response.read())
instrument_list = json.load(open('token_file_updated.json'))





#----------------------Lookup--------------------------------------

#{"token":"99926009","symbol":"Nifty Bank","name":"BANKNIFTY","expiry":"","strike":"0.000000","lotsize":"1",
#"instrumenttype":"AMXIDX","exch_seg":"NSE","tick_size":"0.000000"}

#{"token":"99926017","symbol":"India VIX","name":"INDIA VIX","expiry":"","strike":"0.000000","lotsize":"1",
#"instrumenttype":"AMXIDX","exch_seg":"NSE","tick_size":"0.000000"}

#{"token":"3045","symbol":"SBIN-EQ","name":"SBIN","expiry":"","strike":"-1.000000","lotsize":"1",
#"instrumenttype":"","exch_seg":"NSE","tick_size":"5.000000"} 

def token_lookup(ticker, instrument_list, exchange="NSE"):
    for instrument in instrument_list:
        if instrument["name"] == ticker and instrument["exch_seg"] == exchange and instrument["instrumenttype"] == "AMXIDX":
            #print(ticker, "~~", instrument["token"])
            return instrument["token"]
        
#print(token_lookup("BANKNIFTY", instrument_list, exchange="NSE"))

#----------------------End of Lookup--------------------------------------

holiday_list = ['2024-02-08', '2023-12-25'] 

# Take care -- Below functions only take DATETIME and not Date only
def check_is_inbetween_market_time(test_date):
    #----This block of code will check if we are running code before 3:30PM then it will not take today's data----
    now = dt.datetime.now()
    now_day = dt.date.today()
    
    #print(test_date)
    
    if test_date == now_day:
        if str(now_day) not in holiday_list and now_day.weekday() not in [5, 6]:
            #print("Inside")
            today15_30 = now.replace(hour=15, minute=30, second=0)
        
            if now < today15_30:
                print("It is less than 3:30PM, so need only data till yesterday.")
                return True
            else:
                print("It is already past 3:30PM, so we can take today's data as well.")
                return False
        else:
            print("Market is Closed Today")
    
    return False
#check_is_inbetween_market_time(dt.date.today())



# Take care -- Below functions only take DATETIME and not Date only  
def find_last_working_day(test_date):

    if check_is_inbetween_market_time(test_date) == True:
        test_date = test_date - timedelta(days=1)        
    
    if test_date.weekday() == 0:
        diff = 3
    elif test_date.weekday() == 6:
        diff = 2
    else :
        #diff = 1
        diff = 0

    res = test_date - timedelta(days=diff)
    
    while str(res) in holiday_list:
        res = res - timedelta(days=1)
        
    if res.weekday() in [0, 6]:
        res = find_last_working_day(res) # Recursive call beacuse 
        # may be we have today tuesday and on monday we have holiday
        # then without recursive call it will give sunday as last working day   
    return res

#find_last_working_day(dt.date.today())





    
    
try_ind_hist = 0
def individual_hist_data(ticker,duration,interval,st_date, end_date, exchange="NSE"):
    
    global try_ind_hist
    
    try:        
        params = {
                "exchange": exchange,
                "symboltoken": token_lookup(ticker,instrument_list),
                #"symboltoken": '99926009',
                "interval": interval,
                "fromdate": (st_date).strftime('%Y-%m-%d %H:%M'),
                "todate": (end_date).strftime('%Y-%m-%d %H:%M') 
                }
        hist_data = obj.getCandleData(params)      
        try_ind_hist = 0
        return hist_data
    
    except Exception as e:
        print(colored(f"Individual Historic failed for {ticker}", 'green'))
        try_ind_hist = try_ind_hist+1        
        if try_ind_hist <= 5:
            print(colored(f"TRYYY_HIST {try_ind_hist} again after {try_ind_hist * sleep_time_short} sec\n", 'red'))
            time.sleep(try_ind_hist * sleep_time_short)
            hist_data = individual_hist_data(ticker,duration,interval,st_date, end_date, exchange="NSE")
            return hist_data
        else:
            print(colored(f"No luck for Historical {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_ind_hist = 0
            return None
        
        
        



def hist_data_extended(ticker, duration, interval, exchange="NSE"):
    #st_date = dt.date.today() - dt.timedelta(duration)
    st_date = dt.date(duration, 1, 1)
    #end_date = dt.date.today()
    end_date = find_last_working_day(dt.date.today())
    #end_date = find_last_working_day(dt.datetime.now())
    
    st_date = dt.datetime(st_date.year, st_date.month, st_date.day, 9, 15)
    #end_date = dt.datetime(end_date.year, end_date.month, end_date.day)
    #end_date = dt.datetime(end_date.year, end_date.month, end_date.day+1, 3, 15) # We have add 1 day otherwise today's day has been left out of data
    end_date = dt.datetime(end_date.year, end_date.month, end_date.day, 3, 15) + dt.timedelta(1) # We have add 1 day otherwise today's day has been left out of data

    
    
    df_data = pd.DataFrame(columns=["date","open","high","low","close","volume"])
    
    print(st_date, "!!!!!", end_date - dt.timedelta(1))
    
    #while st_date < end_date:
    while st_date <= end_date:
        time.sleep(10) #avoiding throttling rate limit
        print(f"From {st_date} ~~to~~ {end_date}")
        
        hist_data = individual_hist_data(ticker,duration,interval,st_date, end_date, exchange="NSE")            
            

        temp = pd.DataFrame(hist_data["data"],
                            columns = ["datetime","open","high","low","close","volume"])
        df_data = temp.append(df_data,ignore_index=True)
        #df_data = pd.concat([temp,df_data]) #above line may throw an error in later pandas versions. Use this line instead if that happens
        end_date = dt.datetime.strptime(temp['datetime'].iloc[0][:16], "%Y-%m-%dT%H:%M")
        if len(temp) <= 1: #this takes care of the edge case where start date and end date become same
            break

    df_data.set_index("datetime",inplace=True)
    df_data.index = pd.to_datetime(df_data.index)
    df_data.index = df_data.index.tz_localize(None)
    df_data.drop_duplicates(keep="first",inplace=True)
    
    #df_data.to_csv(f'01_Data\data_{ticker}.csv')
    df_data.to_csv(f'{current_folder_path}\\01_Data\data_{ticker}.csv')
    
    return df_data


        
        
#-----------------------------------GET HISTORICAL DATA-------------------------------------------

if __name__ == "__main__":

    #tickers = ["BANKNIFTY", "NIFTY", "INDIA VIX"]
    tickers = ["BANKNIFTY"]
    data_duration = 2023  # Year from where data is required, as per ANGLEONE, we are getting till 2015 in 2023 year
    dic_predictions = {}
    interval = "ONE_HOUR"
    
    for ticker in tickers:    
        print(f"\nML data collection for {ticker}.....") 
        hist_df = hist_data_extended(ticker, data_duration, interval)    
    
    print("Process of collecting Historical Data Completed")