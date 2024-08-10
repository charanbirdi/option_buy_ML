"""
This is mail python file which will do the Algorithmic calculations without ML

https://github.com/angel-one/smartapi-python
https://www.insertcart.com/angle-broker-smartapi-setup-guide-with-full-python-api-source-code/


#####OPTION Strategy#############
https://www.gettogetherfinance.com/blog/best-options-strategy/#Iron_butterfly_creditnon-directional

"""
import warnings 
warnings.filterwarnings('ignore')

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

import sys

from option_all_modules import (token_lookup_OPTION,
                                get_ltp_OPTION, hist_data_0920, hist_intraday, find_lookbehind_effective_days, 
                                copy_LTP_to_excel, check_individual_open_positions,
                                check_global_PnL, positions_asin_excel, get_latestdata_DataFrame,
                                place_robo_order, get_ltp_INSTRUMENT,
                                short_strangle,
                                update_excel_global_pnl, update_global_pnl_excel,
                                plot_asper_exl,
                                delta_nutral_initial_orders, delta_nutral_adjustment,                                
                                expiry_bull_call_spread_initial_orders, expiry_bull_call_spread_adjustment,
                                already_in_orderlist,
                                CLOSE_allindividual_open_positions, closing_theday)

from record_logs import logging_function

from Connect_ANGELONE import (connect_ANGELONE, instrument_list_ANGELONE)



#----------for current folder path------------
#import pathlib
#current_folder_path = pathlib.Path(__file__).parent.resolve()
#df_data.to_csv(f'{current_folder_path}\\01_Data\data_{ticker}.csv')
#---------------------------------------------
from termcolor import colored
#print(colored('hello', 'red'), colored('world', 'green'))

starttime = time.time()

#https://docs.xlwings.org/en/stable/syntax_overview.html
import xlwings as xw

r = 16 # order sheet row
row_excel_start_order = 16 # we cannot use r here as it will be updated
row_excel_end_order = 100

row_filter_start = 2
row_filter_end = 100



global_row = 2
global_row_delta = 17
global_row_call_spread_expiry = 17






wb = xw.Book('AngelOne_Option_BUY.xlsx')
exl_filter = wb.sheets['filtered']
exl_option_buy = wb.sheets['option_buy']
exl_global_pnl = wb.sheets['Global_PnL']
exl_all_order_BUY = wb.sheets['all_order']


#print(exl_filter.name)
#print(exl_filter[1,3].value)

exl_filter.range("A3:K600").clear_contents()
exl_filter.range("Y3:Z600").clear_contents()







# def get_last_row_Pnl_curve(exl):
#     #row = 17
#     last = exl.range('BN5000').end('up').row
#     # for i in range(17, 1000):
#     #     date = exl[i,65].value
#     #     if date is None:
#     #         return i
#     return last
# get_last_row_Pnl_curve(exl_deltanutral)



def clear_excel_function(exl):
    print(f"Clear data for {exl.name}.......") 
    clear_excel = True
    for i in range(row_excel_start_order, row_excel_end_order):
        ticker = exl[i,6].value
        initial_order = exl[i,40].value
        final_order = exl[i,48].value
        if (ticker is not None and final_order is None):
            print(f"No need to clear excel file for {exl.name}")
            clear_excel = False
            last_row = exl.range('BN5000').end('up').row + 1 # so that PnL curve start from where it lefts
            break
            
    if clear_excel:
        exl.range("B16:S300").clear_contents()
        exl.range("AL16:AQ300").clear_contents()
        exl.range("AU16:AW300").clear_contents()
        exl.range("AY16:AY300").clear_contents()  
        
        exl.range("BN16:BO600").clear_contents() #additional
        
        last_row = 17
      
    return last_row

global_row_delta = clear_excel_function(exl_option_buy)


# if exl_expiry_bullspread[16,1].value is None or exl_expiry_bullspread[16,1].value.date() < dt.datetime.now().date():        
#     exl_expiry_bullspread.range("B16:S300").clear_contents()
#     exl_expiry_bullspread.range("AL16:AQ300").clear_contents()
#     exl_expiry_bullspread.range("AU16:AW300").clear_contents()
#     exl_expiry_bullspread.range("AY16:AY300").clear_contents()
#     exl_expiry_bullspread.range("BN16:BO600").clear_contents()
#     exl_expiry_bullspread.range("BD16:BE600").clear_contents()
#     exl_expiry_bullspread.range("A16:BL300").color = None
    
#     exl_expiry_bullspread.range("I2:J12").clear_contents()
#     exl_expiry_bullspread.range("P2:R12").clear_contents()
    







# -----------LOSS PROFIT LIMITS------------
ordered = [] # All ordered stocks, we are not using it
hi_lo_prices = {}



#-------Ticker FIlter limit to select final stocks--------
# TICKER_HIGH_FILTER_LIMIT = 0.9 # it means stock price is near to ATH and assuming going up, so we can buy
# TICKER_LOW_FILTER_LIMIT = 1.1  # it means stock price is near to ATL and assuming going down, so we can sell it

# Above limit should be less than lower mentioned limits , logically
# below limits are to filter the instruments but I have disabled the same in strategy------
#-----Strategy Limits------------
LOW_LIMIT = 1.2 #0.99 # change back to < 1 if not doing experiemnt
HIGH_LIMIT = 0.8 #1.01 # change back to > 1 if not doing experiemnt
#VOL_LIMIT = 0.5

#-----------POSITION SIZE LIMIT-------------------
total_spend = 0
spend_limit = 90 # 90% of total available
#loss_limit = 50 # Not required here, thats weird
#profit_limit = 90 # Not required here, thats weird

Total_loss_limit = 10 # 10% of position size
single_pos_size = 20000
#pos_size = single_pos_size * (len(tickers)+1)
pos_size = single_pos_size * 10


#-------Sleep time variable----------------------
sleep_time_long = 7
sleep_time_short = 3

try_count_long = 5
try_count_short = 4




CANDLE_INTERVAL_HIST_DATA = "FIVE_MINUTE"
CANDLE_INTERVAL_LTP = "FIVE_MINUTE"
#WE HAVE used GLOBAL interval so that Historical data and strategy data remain on same level, specifically for volume comparision


 

"""
How to clean log file
It might be better to truncate the file instead of removing it. 
The easiest solution is to reopen the file for writing from your clearing function and close it:
"""
#with open('option_strategies.log', 'w'):
#    pass
#logger = logging_function()




tickers = ['BANKNIFTY', 'NIFTY'] #'BANKNIFTY', 'NIFTY', 'FINNIFTY'
print(f"INSTRUMENT OF INTEREST = {tickers}")
#logger.info(f"INSTRUMENT OF INTEREST = {tickers}")


global obj
obj = connect_ANGELONE() # Connect with AngelOne API
instrument_list = instrument_list_ANGELONE()
update_excel_global_pnl(tickers, exl_global_pnl) # prepeare sheets for GLOBAL data logging

working_days_considered = 1
lookbehind_days_low_hi_tuple = find_lookbehind_effective_days(working_days_considered)
lookbehind_days_low_hi = lookbehind_days_low_hi_tuple[1]
print(f'for working days considered = {working_days_considered}, LOOKBEHIND_EFFECTIVE_DAYS = {lookbehind_days_low_hi_tuple}')



def indiavix_function():   

    indiavix = get_ltp_INSTRUMENT(obj, instrument_list, "INDIA VIX", exchange="NSE")
    #print(colored(f"Today INDIA VIX = {indiavix}", 'green'))
    #logger.info(f"Today INDIA VIX = {indiavix}")    
    return indiavix















# Ibirdi - made this function
def ML_STRATEGY():
    
    print(colored("Machine Learning Strategies Function running....", 'green'))

    for i in range(row_filter_start, row_filter_end):
        
        security = exl_filter[i,3].value
        
        if security is not None:
            
            #print(f"Machine Learning Strategies Function running....{security}")
            
            ticker_H = exl_filter[i,5].value
            ticker_L = exl_filter[i,6].value
            current_price_ticker = get_ltp_INSTRUMENT(obj, instrument_list, security,"NSE")
                               #def get_ltp_INSTRUMENT(obj, instrument_list, ticker,  exchange="NSE")
           
            #---------Machine Learning Strategy-------------------
            ticker_ML_prediction = exl_filter[i,17].value
            
            if ticker_ML_prediction is not None:
                
                if ticker_ML_prediction == "Side-way":
                    strategy = "ML_sideway_Short_Strangle"
                    short_strangle(obj, instrument_list, security, current_price_ticker, strategy, exl_option_buy)
                    #def short_strangle(obj, instrument_list, ticker, current_price_ticker, strategy):
                                                                
    return None

#tickers_high = filtered_tickers_nearhighlow(data_0920) #identify tickers with maximum gap up/down




def low_high(tickers):
    
    #extract the historical data at 9:20 am         
    #data_0920 = hist_data_0920(obj, tickers, lookbehind_days_low_hi, CANDLE_INTERVAL_HIST_DATA, instrument_list)
    intraday_data_0920 = hist_intraday(obj, tickers, CANDLE_INTERVAL_HIST_DATA, instrument_list)
    
    #FIFTEEN_MINUTE, ONE_DAY 
    # if we use one day then volume comparision will be not ok, beacuse
    # if we get DAY HIGH as one day value and the will compare FIVE_MIN candle for intraday then
    # its not comparable
    
    #--------------Get all Stocks HIGH, LOW and VOLUME and input in EXCEL sheet-----------------------
    for ticker in tickers:
        #hi_lo_prices[ticker] = [data_0920[ticker]["high"].max(), data_0920[ticker]["low"].min(), data_0920[ticker]["volume"].mean()]
        hi_lo_prices[ticker] = [intraday_data_0920[ticker]["high"].max(), intraday_data_0920[ticker]["low"].min()]
        #print(hi_lo_prices)
    
    r_start = 2    
    for key, value in hi_lo_prices.items():
        
        exl_filter[r_start, 2].value = dt.datetime.now()
        exl_filter[r_start, 3].value = key
        exl_filter[r_start, 4].value = lookbehind_days_low_hi
        exl_filter[r_start, 5].value = value    
        exl_filter[r_start, 8].value = HIGH_LIMIT * value[0]
        exl_filter[r_start, 9].value = LOW_LIMIT * value[1]
        #exl_filter[r_start, 8].value = VOL_LIMIT * value[2]
        r_start = r_start + 1
        
         
    print("Initial Analysis Done i.e L-H for all Filtered Instruments\n")
    
    return hi_lo_prices


hi_lo_prices = low_high(tickers)

print(hi_lo_prices)


#fil_tickers = filtered_tickers_nearhighlow(hi_lo_prices) #major change
fil_tickers = tickers
#print("filtered tickers", "~~", fil_tickers)

#----------END of Get all Stocks HIGH, LOW and VOLUME and input in EXCEL sheet-----------------------







def orb_strat(obj, tickers, hi_lo_prices, strategy_days, exchange="NSE"): # Here tickers are filtered tickers--
    
    print(colored("ORB strategy Function running....", "green"))    
    
    for ticker in tickers:
        print(f"ORB strategy Function running for........{ticker}")
        
        unique_strategy_order = "Open_Range_Breakout" + "#" + ticker
        positions = positions_asin_excel(exl_option_buy) # Order list as per excel sheet
        
        #strategy_days = 1 # if holiday put 1 or 2 else 0
        if unique_strategy_order not in positions:
            df_data = get_latestdata_DataFrame(obj, ticker, instrument_list, strategy_days, exchange) # Get latest data
            
            if df_data["close"].iloc[-1] >= HIGH_LIMIT * hi_lo_prices[ticker][0]:                
                place_robo_order(obj, instrument_list, ticker, "UP", "Open_Range_Breakout", exl_option_buy)
                #print("bought {} stocks of {}".format(quantity(ticker),ticker))
            elif df_data["close"].iloc[-1] <= LOW_LIMIT * hi_lo_prices[ticker][1]:
                #print(unique_strategy_order)
                place_robo_order(obj, instrument_list, ticker, "DOWN", "Open_Range_Breakout", exl_option_buy)
                #print("sold {} stocks of {}".format(quantity(ticker),ticker))
            
    return None






def check_starttime_vix_condition(time, vix_limit, exl):
    #if dt.datetime.now() > dt.datetime.strptime(dt.datetime.now().strftime('%Y-%m-%d')+' 09:35','%Y-%m-%d %H:%M') and dt.datetime.now() < dt.datetime.strptime(dt.datetime.now().strftime('%Y-%m-%d')+' 23:00','%Y-%m-%d %H:%M'):
    if (dt.datetime.now() > dt.datetime.strptime(dt.datetime.now().strftime('%Y-%m-%d') + time, '%Y-%m-%d %H:%M') and 
        dt.datetime.now() < dt.datetime.strptime(dt.datetime.now().strftime('%Y-%m-%d')+' 23:00','%Y-%m-%d %H:%M')):
        exl[1, 9].value = str(dt.datetime.now().time())
        if indiavix_function() > vix_limit:
            exl[2, 9].value = indiavix_function()
            return True
    return False

#check_starttime_vix_condition(" 09:35", 12)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~END OF Initial Strategies run--------------------------------





#--------------Set flags--------------------
already_initialorder_done_for_bull_call_spread = False
already_initialorder_done_for_delta_nutral = False
#-------------------------------------------






#ML_STRATEGY()

def copy_alltrades_excel(from_exl, to_exl):
    
    last_row_from = from_exl.range('B5000').end('up').row
    last_row_to = to_exl.range('B5000').end('up').row
    #print(last_row_to)
    
    from_exl.range((16,1), (last_row_from+1,53)).copy()
    to_exl.range((last_row_to+1,1), (last_row_to+1,1)).paste()    #to_exl.range("A1").paste(paste='formats')
    
    return None






while dt.datetime.now() < dt.datetime.strptime(dt.datetime.now().strftime('%Y-%m-%d')+' 19:55','%Y-%m-%d %H:%M'):
    
    print("\n")
    print("_"*80)    
    print(colored("While loop running.....", "green"))
    print("starting passthrough at {}".format(dt.datetime.now()))    
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Check Starategy Condition------------------------------------------------
        
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~end of Check Starategy Condition------------------------------------------------     
    

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Updating the excel sheets with LTP------------------------------------------------    
    copy_LTP_to_excel(obj, instrument_list, exl_option_buy, exchange="NFO") # Only to update LTP in excel sheet    
    check_individual_open_positions(obj, instrument_list, exl_option_buy)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Updating the excel sheets with LTP------------------------------------------------    
    



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Check Global P&L for all strategies------------------------------------------------

    Grand_Global_PnL = 0
    
    
    global_PnL = check_global_PnL(exl_option_buy)  
    print(colored(f"Other Global P&L = {global_PnL}", "magenta"))    
    exl_filter[global_row, 24].value = dt.datetime.now()
    exl_filter[global_row, 25].value = global_PnL
    global_row = global_row + 1
    Grand_Global_PnL = Grand_Global_PnL + global_PnL
    
    
    
    Option_BUY_global_PnL = check_global_PnL(exl_option_buy)  
    print(colored(f"Option BUY Global P&L = {Option_BUY_global_PnL}", "magenta"))    
    exl_option_buy[global_row_delta, 65].value = dt.datetime.now()
    exl_option_buy[global_row_delta, 66].value = Option_BUY_global_PnL
    global_row_delta = global_row_delta + 1
    Grand_Global_PnL = Grand_Global_PnL + Option_BUY_global_PnL
    
    
    
               
        
        
    #Grand_Global_PnL = global_PnL + global_row_delta + expiry_spread_global_PnL
    global_loss_limit = -(pos_size) * (Total_loss_limit)/100
    
    update_global_pnl_excel(tickers, exl_global_pnl, wb)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~end of Check Global P&L for all strategies------------------------------------------------

    
    if Grand_Global_PnL < global_loss_limit:
        print(colored(f"GLOBAL LOSS LIMIT = {global_loss_limit} reached", "red"))
        print(f"Changga {global_PnL} loss ho gya, band kardo 22")
        print("Exiting all positions / only loosing postions, have to check and decide.....")
        #closing_theday()
    
    else:
        if (total_spend/pos_size)*100 < spend_limit:
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Running all strategies adjustments-----------------------------------------------
            
            orb_strat(obj, fil_tickers, hi_lo_prices, lookbehind_days_low_hi, "NSE") # last variable is for how many days we need to check max(high) and min(low)
                      
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~end of Running all strategies adjustments-----------------------------------------------
            time.sleep(1*60 - ((time.time() - starttime) % 1*60))  # here time is in seconds
            # without this we got "Access denied because of exceeding access rate"
        
        else:
            print("Global Spend limit has reached")
            break
       
    
########### close karo 22 ji ##########################
    
closing_theday(obj, instrument_list, exl_option_buy)
copy_alltrades_excel(exl_option_buy, exl_all_order_BUY) 
sys.exit(0) # 0- without error message, 1-with error message in end    
    




# if __name__ == '__main__':
#     main()
    
    
    