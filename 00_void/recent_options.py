"""
This is mail python file which will do the Algorithmic calculations without ML

https://github.com/angel-one/smartapi-python
https://www.insertcart.com/angle-broker-smartapi-setup-guide-with-full-python-api-source-code/
"""

from Connect_ANGELONE import (connect_ANGELONE, instrument_list_ANGELONE)

from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect

import os
import urllib
import json
from pyotp import TOTP # for getting OTP

from statistics import mean
import threading
import time

import pandas as pd
import numpy as np
import datetime as dt
from datetime import timedelta

from termcolor import colored

#import yfinance as yf

#https://docs.xlwings.org/en/stable/syntax_overview.html
import xlwings as xw

starttime = time.time()


#-------Sleep time variable----------------------
sleep_time_long = 20
sleep_time_short = 7

try_count_long = 7
try_count_short = 4


#function to extract all option contracts for a given ticker        
def option_contracts(ticker, instrument_list, option_type, exchange="NFO"):
    
    # it will return all the options of all date expiries
    
    #print("option_contracts Function........")
    option_contracts = []
    for instrument in instrument_list:
        if instrument["name"]==ticker and instrument["instrumenttype"] in ["OPTSTK","OPTIDX"] and instrument["symbol"][-2:]==option_type:
            option_contracts.append(instrument)
    return pd.DataFrame(option_contracts)


#function to extract the closest expiring option contracts
def option_contracts_closest(obj, ticker, instrument_list, duration = 0, option_type="CE", exchange="NFO"):
    
    #print("option_contracts_closest Fucntion........")
    #duration = 0 means the closest expiry, 1 means the next closest and so on
    df_opt_contracts = option_contracts(ticker, instrument_list, option_type)  # it will return all the options of all date expiries
    #print(df_opt_contracts)
    
    
    df_opt_contracts["time_to_expiry"] = (pd.to_datetime(df_opt_contracts["expiry"]) - dt.datetime.now() + timedelta(days=1)).dt.days    
    df_opt_contracts = df_opt_contracts.loc[df_opt_contracts['time_to_expiry']>=0] #ibirdi    
    min_day_count = np.sort(df_opt_contracts["time_to_expiry"].unique())[duration]
    df_final = (df_opt_contracts[df_opt_contracts["time_to_expiry"] == min_day_count]).reset_index(drop=True)
    
    return df_final


#function to extract closest strike options to the underlying price

#hist_data = yf.download("^NSEBANK", period='5d')
#underlying_price = hist_data["Adj Close"].iloc[-1]




#function to extract n closest options to the underlying price
def option_chain(obj, ticker, instrument_list, underlying_price, option_type="CE", duration = 0, num = 5, exchange="NFO"):
    
    #print("option_chain Function.........")
    #duration = 0 means the closest expiry, 1 means the next closest and so on
    #num =5 means return 5 option contracts closest to the market
    df_opt_contracts = option_contracts_closest(obj, ticker, instrument_list, duration, option_type)    
    df_opt_contracts.sort_values(by=["strike"],inplace=True, ignore_index=True)    
    atm_idx = abs(df_opt_contracts["strike"].astype(float)/100 - underlying_price).argmin()
    # ibirdi - in above line, we have divided by 100 beacuse stike price in angleone is in paisa and not in Rs.   
    up = int(num/2)
    dn = num - up
    return df_opt_contracts.iloc[atm_idx-up:atm_idx+dn]


def final_contract(obj, ticker, instrument_list, underlying_price, option_type, duration = 0):
    opt_chain = option_chain(obj, ticker, instrument_list, underlying_price, option_type, duration)
    #print("wahhhhh 22 ji wahhhh")
    #print(opt_chain)
    final_option = opt_chain['symbol'].tolist()
    print("wahhhhh 22 ji wahhhh")
    print(opt_chain['expiry'].tolist()[0])
    
    return final_option











#-----------------------------------this is for calculating Delta only-----------------------------------
#--------------------------------------------------------------------------------------------------------



def option_greeks(row, obj, instrument_list,underlying_price):
    
    #print("option_greeks Fucntion........")
    
    from py_vollib.black_scholes.implied_volatility import implied_volatility
    from py_vollib.black_scholes.greeks.analytical import delta, gamma, rho, theta
    
    from option_all_modules import (get_ltp_INSTRUMENT, get_ltp_OPTION) # to avoid circulation error, I imported inside function and not at start of module
    
    
    # price = 660 #option price
    # S = 46219 #Banknifty current price
    # K = 46000 #Banknifty strike price choosen
    # t = (dt.datetime(2024,2,21,15,30,0) - dt.datetime.now())/timedelta(days=1)/365 # time to expiry in years
    # r = 0.1 # Risk free interest rate, it is mentioned at bottom of option chain page of NSE
    # flag = 'c' # c/p - CE/PE
    
    
    ticker = row['symbol']
    security = row['name']    
    price = float(get_ltp_OPTION(obj, instrument_list, ticker, "NFO")) #option price
    #S = float(get_ltp_INSTRUMENT(obj, instrument_list, security, "NSE")) #Banknifty current price
    S = float(underlying_price) #Banknifty current price
    K = float(row['strike'])/100  #Banknifty strike price choosen, strike is in paisa
    t = float(row['days_to_expiry'])  # time to expiry in years
    r = 0.070184 # Risk free interest rate, As per RBI landing page
    # https://onedrive.live.com/view.aspx?resid=CF99AE98F774C7AC%212619&id=documents&wd=target%28Options.one%7C0D911EA7-79A9-44BB-A651-D7EB1C298703%2FCalculate%20Option%20Greeks%7CC6F26DCD-124A-427C-A765-F6453A9C4FED%2F%29
    
    
    flag = ticker[-2:-1].lower() # c/p - CE/PE
    
    #print(price, S, K, t, r, flag)
    
    IV = implied_volatility(price, S, K, t, r, flag)
    #print(IV)
    delta_option = delta(flag, S, K, t, r, IV)
    #print(delta_option*100)
    return delta_option*100


# date_str = '06MAR24' #'09-19-2022'
# date_object = dt.datetime.strptime(date_str, '%d%b%y').date()
# print(type(date_object))
# print(date_object)  # printed in default format

# option = 'BANKNIFTY06MAR2446000PE'
# instrument = "BANKNIFTY"
# inst_length = len(instrument)
# date1 = option[inst_length:inst_length+7]
# print(date1)






#function to extract the closest expiring option contracts
def option_contracts_closest_DELTA(obj, ticker, instrument_list, underlying_price, delta_cosidered_selling, duration = 0, option_type="CE", exchange="NFO"):
    
    #print("option_contracts_closest Fucntion........")
    #duration = 0 means the closest expiry, 1 means the next closest and so on
    df_opt_contracts = option_contracts(ticker, instrument_list, option_type)    # it will return all the options of all date expiries
    
    #df_opt_contracts["expiry_datetime"] = pd.to_datetime(df_opt_contracts["expiry"]).dt.strftime("%Y-%m-%d 15:30:00").astype('datetime64[ns]')
    df_opt_contracts["time_to_expiry_datetime"] = pd.to_datetime(df_opt_contracts["expiry"]).dt.strftime("%Y-%m-%d 15:30:00").astype('datetime64[ns]') - dt.datetime.now() + timedelta(days=1)
    df_opt_contracts["days_to_expiry"] = df_opt_contracts["time_to_expiry_datetime"]/timedelta(days=1)/365 #Delta cal needs time in years only
    
    #df_opt_contracts = df_opt_contracts.loc[df_opt_contracts['time_to_expiry_datetime']>=0] #ibirdi    
    min_day_count = np.sort(df_opt_contracts["time_to_expiry_datetime"].unique())[duration]
    df_final = (df_opt_contracts[df_opt_contracts["time_to_expiry_datetime"] == min_day_count]).reset_index(drop=True)
    
    df_final = df_final.sort_values(by=['strike']).reset_index(drop=True)
    
    
    #underlying_price = float(get_ltp_INSTRUMENT(obj, instrument_list, security, "NSE")) #Banknifty current price    
    atm_idx = abs(df_final["strike"].astype(float)/100 - underlying_price).argmin()  
    
    if option_type == "CE":
        df_final = df_final.iloc[atm_idx:atm_idx+15]
    else:
        df_final = df_final.iloc[atm_idx-15:atm_idx]
    
    
    #df_final['delta'] = df_final.apply(option_greeks, axis=1, args=(obj,instrument_list))
    df_final['delta'] = df_final.apply(lambda x: option_greeks(x,obj,instrument_list,underlying_price),axis=1) #working
    #df_final['delta_diff_20'] = abs(abs(df_final['delta']) - 20)
    df_final['delta_diff_20'] = abs(abs(df_final['delta']) - delta_cosidered_selling)
        
    delta_20 = df_final['delta_diff_20'].argmin()
    option_delta_20 = df_final.iloc[delta_20]['symbol']
    option_delta = df_final.iloc[delta_20]['delta']
    option_expiry = df_final.iloc[delta_20]['expiry']    
    security_strike = float(df_final.iloc[delta_20]['strike'])/100
    
    #print(f"Option with Delta = {option_delta} for {option_delta_20}")
    
    return option_delta_20, option_delta, option_expiry, security_strike






#def option_price_calculation(row, obj, instrument_list,underlying_price, underlying_price_option):
    
def option_price_calculation(row,obj,instrument_list):
    
    #print("option_greeks Fucntion........")    
    from option_all_modules import (get_ltp_OPTION) # to avoid circulation error, I imported inside function and not at start of module    
    
    ticker = row['symbol']
    price = get_ltp_OPTION(obj, instrument_list, ticker, "NFO") #option price
    
    return price






#function to extract the closest option contracts with same premium
def option_contracts_closest_PREMIUM(obj, ticker, instrument_list, underlying_price, underlying_price_option, expiry_date, option_type="CE", exchange="NFO"):
    
    #print("option_contracts_closest Fucntion........")
    #duration = 0 means the closest expiry, 1 means the next closest and so on
        
        
    df_opt_contracts = option_contracts(ticker, instrument_list, option_type)    # it will return all the options of all date expiries  
    #print(df_opt_contracts)
          
    df_opt_contracts = df_opt_contracts.loc[df_opt_contracts['expiry'] == expiry_date] #ibirdi 
    #print(df_opt_contracts)
    
    df_final = df_opt_contracts.sort_values(by=['strike']).reset_index(drop=True)
    
    print(df_final)      
    atm_idx = abs(df_final["strike"].astype(float)/100 - underlying_price).argmin()
    
    if option_type == "CE":
        df_final = df_final.iloc[atm_idx:atm_idx+15]
    else:
        df_final = df_final.iloc[atm_idx-15:atm_idx]
    
    
    #df_final['delta'] = df_final.apply(option_greeks, axis=1, args=(obj,instrument_list))
    df_final['option_price'] = df_final.apply(lambda x: option_price_calculation(x,obj,instrument_list),axis=1) #working
    df_final['option_price_diff'] = abs(abs(df_final['option_price']) - abs(underlying_price_option))
    
    option_diff_index = df_final['option_price_diff'].argmin()
    option_closest = df_final.iloc[option_diff_index]['symbol']
    option_closest_price = df_final.iloc[option_diff_index]['option_price']
    strike_security = float(df_final.iloc[option_diff_index]['strike'])/100
    
    print(f"Closest Option {option_closest} price = {option_closest_price}")
    
    return strike_security, option_closest, option_closest_price

#--------------------------------end of this is for calculating Delta only-----------------------------------






#function to extract the closest option contracts with same premium
def option_contracts_ATM_expiring_today(obj, ticker, instrument_list, underlying_price, option_type="CE", exchange="NFO"):
    
    #print("option_contracts_closest Fucntion........")        
        
    df_opt_contracts = option_contracts(ticker, instrument_list, option_type)    # it will return all the options of all date expiries  
    #print(df_opt_contracts['expiry'].head())
    
   
    #df_opt_contracts["time_to_expiry_date"] = (pd.to_datetime(df_opt_contracts["expiry"]).dt.strftime("%Y-%m-%d 15:30:00").astype('datetime64[ns]') - dt.datetime.now())/timedelta(days=1)
    # just to make expirty module run , so above statement is modified as below.
    day_ahead_for_expiry = 0 # for same day expiry, use 0
    df_opt_contracts["time_to_expiry_date"] = (pd.to_datetime(df_opt_contracts["expiry"]).dt.strftime("%Y-%m-%d 15:30:00").astype('datetime64[ns]') - dt.datetime.now() - timedelta(days=day_ahead_for_expiry))/timedelta(days=1)
   
    
    #print(df_opt_contracts)
    
    df_opt_contracts = df_opt_contracts.loc[(df_opt_contracts['time_to_expiry_date'] <= 1) & (df_opt_contracts['time_to_expiry_date'] > 0)] # final statement # <1
    #df_opt_contracts = df_opt_contracts.loc[df_opt_contracts['time_to_expiry_date'] <= 2] # modified so that even non expiry dates will cause it to run
    #print(df_opt_contracts)
    
    if len(df_opt_contracts) > 0:
        print(f"Ajjj expiry aa = {ticker}")
        
        df_final = df_opt_contracts.sort_values(by=['strike']).reset_index(drop=True)
        atm_idx = abs(df_final["strike"].astype(float)/100 - underlying_price).argmin()
        
        option = df_final.iloc[atm_idx]['symbol']
        option_expiry = df_final.iloc[atm_idx]['expiry']
        option_strike = float(df_final.iloc[atm_idx]['strike'])/100
        
        print(option, option_expiry, option_strike)        
        
        return option, option_expiry, option_strike
    else:
        print(f"Ajj ni aa expiry = {ticker}")
        return None, None, None
    
    
    
    
    
    
    
    
    
   


#option_contracts_ATM_expiring_today(obj, "FINNIFTY", instrument_list, option_type="CE", exchange="NFO")





    

if __name__ == '__main__':
    obj = connect_ANGELONE()
    instrument_list = instrument_list_ANGELONE()    
    #get underlying price
    security = "BANKNIFTY"
    underlying_price = obj.ltpData("NSE", "BANKNIFTY-EQ", "99926009")["data"]["ltp"]
    print(f"underlying_price = {underlying_price}")
    
    opt_chain = option_chain(obj, security, instrument_list, underlying_price, "PE", 0)
    print("#####Option chain#########")
    print(opt_chain)
    
    final_option = final_contract(obj, security, instrument_list, underlying_price, "PE", 0)
    print(final_option)
    
    
    
 #----------------------------------for Option greeks------------------------------------------------   
    #delta_cosidered_selling = 30
    #option_delta_20 = option_contracts_closest_DELTA(obj, security, instrument_list, underlying_price, 0, delta_cosidered_selling, "CE")
    #print(f"Option with {option_delta_20[1]} Delta Greeks = {option_delta_20[0]}")
    
    
    underlying_price_option = 200
    expiry_date = "18SEP2024"
    strike_security, option_closest, option_closest_price = option_contracts_closest_PREMIUM(obj, security, instrument_list, underlying_price, underlying_price_option, expiry_date, option_type="CE", exchange="NFO")
    
    print(f"Closest Option {option_closest} price = {option_closest_price}")
    
    #{"token":"99919000","symbol":"SENSEX","name":"SENSEX","expiry":"","strike":"0.000000","lotsize":"1","instrumenttype":"AMXIDX","exch_seg":"BSE","tick_size":"0.000000"},
    #{"token":"866186","symbol":"SENSEX24MAR75000PE","name":"SENSEX","expiry":"28MAR2024","strike":"7500000.000000","lotsize":"10","instrumenttype":"OPTIDX","exch_seg":"BFO","tick_size":"5.000000"},
    
    #ac_margin = obj.rmsLimit()
    
    
    
    
    