"""
This is mail python file which will do the Algorithmic calculations without ML

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

#from recent_options import final_contract

from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect

#from memory_profiler import profile
from recent_options import final_contract, option_contracts_closest_DELTA, option_contracts_closest_PREMIUM
from option_payoff_graph import plot_final_payoff



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
sleep_time_long = 3
sleep_time_short = 3

try_count_long = 5
try_count_short = 4


# -----------LOSS PROFIT LIMITS------------
ordered = [] # All ordered stocks, we are not using it
hi_lo_prices = {}



#-------Ticker FIlter limit to select final stocks--------
# TICKER_HIGH_FILTER_LIMIT = 0.9 # it means stock price is near to ATH and assuming going up, so we can buy
# TICKER_LOW_FILTER_LIMIT = 1.1  # it means stock price is near to ATL and assuming going down, so we can sell it

# Above limit should be less than lower mentioned limits , logically
# below limits are to filter the instruments but I have disabled the same in strategy------
#-----Strategy Limits------------
LOW_LIMIT = 0.99
HIGH_LIMIT = 1.01
#VOL_LIMIT = 0.5








#-----------POSITION SIZE LIMIT-------------------
total_spend = 0
spend_limit = 90 # 90% of total available
loss_limit = 50 # 10% of position size
profit_limit = 100 # 10% of position size

Total_loss_limit = 5
single_pos_size = 20000
#pos_size = single_pos_size * (len(tickers)+1)
pos_size = single_pos_size * 20


r = 16 # order sheet row
row_excel_start_order = 16 # we cannot use r here as it will be updated
row_excel_end_order = 100


row_filter_start = 2
row_filter_end = 100


CANDLE_INTERVAL_HIST_DATA = "FIVE_MINUTE"
CANDLE_INTERVAL_LTP = "FIVE_MINUTE"
#WE HAVE used GLOBAL interval so that Historical data and strategy data remain on same level, specially for volume comparision


#PERCENTAGE_LOSS_LIMIT = 20 # IN %age
#PERCENTAGE_PROFIT_LIMIT = 20 # IN %age


#---------------------For Delta Nutral Strategy only------------------
limit_delta_ind_loss = 40 # in %age
#limit_delta_ind_profit = 10 #40 # not used till now
this_or_next_week_or = 1
delta_cosidered_selling = 30 # in Actual  value, Either check Support/resistance or check delta, usually 20.
#------------------end of For Delta Nutral Strategy only------------------


#---------------------For Bull Spread for Expiry only Strategy------------------
expiry_ind_profit_limit = 50 # in %age
expiry_total_loss_limit = 60 # in %age
expiry_total_profit_limit = 60 # in %age
strike_close_limit = 1 # 1 in %age
premium_limit = 10 # in %age # after that we dont do adjustments

#-------------------end of For Bull Spread for Expiry only Strategy------------------





# # Better to change this function
# # first time make list and then refer that only , instead of checking entire list again and again, ALready changed as below

def token_lookup(ticker, instrument_list, exchange="NSE"):
    for instrument in instrument_list:
        if instrument["name"] == ticker and instrument["exch_seg"] == exchange and instrument["instrumenttype"] == "AMXIDX":
            #print(ticker, "~~", instrument["token"])
            return instrument["token"]
        
        
def token_lookup_OPTION(ticker, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["symbol"] == ticker and instrument["exch_seg"] == exchange and instrument["instrumenttype"] == "OPTIDX":
            #print(ticker, "~~", instrument["token"])
            return instrument["token"], instrument['lotsize']
#print(token_lookup_OPTION("BANKNIFTY25JAN2446000PE", instrument_list))
      




# FUNCTION TO GET LTP for call/put and not Instrument (BANKNIFTY etc.)

def get_ltp_OPTION(obj, instrument_list, ticker, exchange="NFO"):
    #print("Getting OPTION LTP Function....")
    global try_ltp_option
    try_ltp_option = 0
    
    try:
        params = {
                    "tradingsymbol":"{}".format(ticker),
                    "symboltoken": token_lookup_OPTION(ticker, instrument_list)[0]
                    #"symboltoken": ticker_symbol_dict[ticker]
                 }
        response = obj.ltpData(exchange, params["tradingsymbol"], params["symboltoken"])
        ltp_stocks = response["data"]["ltp"]
        #print(f"Deatil checking@@@@@ {ticker} = {response}")
        try_ltp_option = 0
        return ltp_stocks
    
    except Exception as e:
        print(f"Get Option LTP Api failed: {e}")
        print(f"LTP failed for {ticker}")
        try_ltp_option = try_ltp_option + 1        
        if try_ltp_option <= try_count_short:
            print(colored(f"TRYYYYY_LTPPPP {try_ltp_option} again after {try_ltp_option * sleep_time_short} sec\n", 'red'))
            time.sleep(try_ltp_option * sleep_time_short)
            ltp_stocks = get_ltp_OPTION(obj, instrument_list, ticker, exchange)
            return ltp_stocks
        else:
            print(colored(f"No luck for {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_ltp_option = 0
            return None


#get_ltp_OPTION(obj, instrument_list, "BANKNIFTY07FEB2446000PE", exchange="NFO")



try_ltp_instrument = 0
def get_ltp_INSTRUMENT(obj, instrument_list, ticker,exchange="NSE"):
    print("Getting INSTRUMENT LTP Function....")
    global try_ltp_instrument
    try:
        params = {
                    "tradingsymbol":"{}-EQ".format(ticker),
                    "symboltoken": token_lookup(ticker, instrument_list)
                    #"symboltoken": ticker_symbol_dict[ticker]
                 }
        
        response = obj.ltpData(exchange, params["tradingsymbol"], params["symboltoken"])
        ltp_stocks = response["data"]["ltp"]
        #print(f"Deatil checking@@@@@ {ticker} = {response}")
        try_ltp = 0
        return ltp_stocks
    
    except Exception as e:
        print(f"Get Instrument LTP Api failed: {e}")
        print(f"LTP failed for {ticker}")
        try_ltp_instrument = try_ltp_instrument + 1        
        if try_ltp_instrument <= try_count_short:
            print(colored(f"TRYYYYY_LTPPPP {try_ltp_instrument} again after {try_ltp_instrument * sleep_time_short} sec\n", 'red'))
            time.sleep(try_ltp_instrument * sleep_time_short)
            ltp_stocks = get_ltp_INSTRUMENT(obj, instrument_list, ticker,exchange="NSE")
            return ltp_stocks
        else:
            print(colored(f"No luck for {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_ltp_instrument = 0
            return None
        
#print(get_ltp_INSTRUMENT("FINNIFTY",exchange="NSE"))
#print(get_ltp_INSTRUMENT(obj, instrument_list, "INDIA VIX", exchange="NSE"))








def quantity(obj, instrument_list, ticker,exchange="NFO"):
    
    #global single_pos_size    
    ltp = get_ltp_OPTION(obj, instrument_list, ticker, exchange)
    lot_option = int(token_lookup_OPTION(ticker, instrument_list)[1])
    quantity_lots = int(single_pos_size/(ltp*lot_option))
    return quantity_lots

#quantity("FINNIFTY27FEB2420700PE",exchange="NFO")

    
def get_open_orders():
    response = obj.orderBook()
    df = pd.DataFrame(response['data'])
    if len(df) > 0:
        return df[df["orderstatus"]=="open"]
    else:
        return None
  

 
def positions_asin_excel(exl_order):
    # ----------check order List from excel sheet--------- 
    all_positions_list=[]
    for i in range(row_excel_start_order, row_excel_end_order):   
        security = exl_order[i,5].value
        strategy = exl_order[i,2].value
        if security is not None:
            unique_strategy_order = strategy + "#" + security
            all_positions_list.append(unique_strategy_order)
        
    return all_positions_list

    















try_ind_hist = 0
def individual_hist_data(obj, ticker,duration,interval,instrument_list,exchange="NSE"):
    
    global try_ind_hist
    
    try:        
        params = {
                 "exchange": exchange,
                 "symboltoken": token_lookup(ticker,instrument_list),
                 #"symboltoken": ticker_symbol_dict[ticker],
                 "interval": interval,
                 "fromdate": (dt.date.today() - dt.timedelta(duration)).strftime('%Y-%m-%d %H:%M'), 
                 "todate": dt.date.today().strftime('%Y-%m-%d') + ' 09:15'
                 #duration - it subtract that number of days, 
                 #so if today is 12th Oct, it will get data from 09th Oct 09:15:00 to 12th Oct 09:15:00AM
                 #interval = FIVE_MINUTE - means data is provided with 5 min candle
                 }
        hist_data = obj.getCandleData(params)       
        try_ind_hist = 0
        return hist_data
    
    except Exception as e:
        print(f"Individual Historic failed for {ticker}")
        try_ind_hist = try_ind_hist+1        
        if try_ind_hist <= try_count_short:
            print(colored(f"TRYYY_HIST {try_ind_hist} again after {try_ind_hist * sleep_time_short} sec\n", 'red'))
            time.sleep(try_ind_hist * sleep_time_short)
            hist_data = individual_hist_data(obj, ticker,duration,interval,instrument_list,exchange="NSE")
            return hist_data
        else:
            print(colored(f"No luck for Historical {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_ind_hist = 0
            return None
    
    
    
    
    
    
    
        
def hist_data_0920(obj, tickers,duration,interval,instrument_list,exchange="NSE"):
    print("\nHistorical Data Function running.....")
    #try:
    hist_data_tickers = {}
    for ticker in tickers:
        time.sleep(try_count_short) # without this we got "Access denied because of exceeding access rate"
        print(f"Getting Historical Data for {ticker}..")
        hist_data = individual_hist_data(obj,ticker,duration,interval,instrument_list,exchange="NSE")
        
        df_data = pd.DataFrame(hist_data["data"],
                               columns = ["date","open","high","low","close","volume"])
        df_data.set_index("date",inplace=True)
        df_data.index = pd.to_datetime(df_data.index)
        df_data.index = df_data.index.tz_localize(None)
        
        df_data["gap"] = ((df_data["open"]/df_data["close"].shift(1))-1)*100
        
        hist_data_tickers[ticker] = df_data
        
    return hist_data_tickers

#data_0920 = hist_data_0920(tickers, 4, CANDLE_INTERVAL_HIST_DATA, instrument_list)











try_ind_intraday = 0
def individual_intraday_data(obj, ticker, interval, instrument_list,exchange="NSE"):
    
    global try_ind_intraday
    
    try:        
        params = {
                 "exchange": exchange,
                 "symboltoken": token_lookup(ticker,instrument_list),
                 "interval": interval,
                 "fromdate": (dt.date.today() - dt.timedelta(1)).strftime('%Y-%m-%d') + ' 09:15', 
                 "todate": dt.datetime.now().strftime('%Y-%m-%d %H:%M')
                 }
        hist_data = obj.getCandleData(params)       
        try_ind_intraday = 0
        return hist_data
    
    except Exception as e:
        print(f"Individual Intraday failed for {ticker}")
        try_ind_intraday = try_ind_intraday+1        
        if try_ind_intraday <= try_count_short:
            print(colored(f"TRYYY_HIST {try_ind_intraday} again after {try_ind_intraday * sleep_time_short} sec\n", 'red'))
            time.sleep(try_ind_intraday * sleep_time_short)
            hist_data = individual_intraday_data(obj, ticker, interval, instrument_list,exchange="NSE")
            return hist_data
        else:
            print(colored(f"No luck for Historical {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_ind_intraday = 0
            return None


def hist_intraday(obj, tickers, interval, instrument_list, exchange="NSE"):
    print("\nIntraday Historical Data Function running.....")
    #try:
    hist_intraday_tickers = {}
    for ticker in tickers:
        time.sleep(try_count_short) # without this we got "Access denied because of exceeding access rate"
        print(f"Getting Historical Data for {ticker}..")
        hist_data = individual_intraday_data(obj,ticker, interval, instrument_list,exchange="NSE")
        
        df_data = pd.DataFrame(hist_data["data"],
                               columns = ["date","open","high","low","close","volume"])
        df_data.set_index("date",inplace=True)
        df_data.index = pd.to_datetime(df_data.index)
        df_data.index = df_data.index.tz_localize(None)
        
        df_data["gap"] = ((df_data["open"]/df_data["close"].shift(1))-1)*100
        
        hist_intraday_tickers[ticker] = df_data
        
    return hist_intraday_tickers

#intraday_data_0920 = hist_intraday(obj, ['BANKNIFTY'], 'FIVE_MINUTE', instrument_list)
#print(intraday_data_0920)













try_latest = 0
def get_latestdata_DataFrame(obj, ticker, instrument_list, strategy_days, exchange="NSE"):
    
    print("get_latestdata_DF Function running....")    
    print(f"Getting latest price, volume for {ticker} is running.....")
    time.sleep(try_count_short)    
    
    global try_latest
    
    try:        
        params = {
                 "exchange": exchange,
                 "symboltoken": token_lookup(ticker,instrument_list),
                 #"symboltoken": ticker_symbol_dict[ticker],
                 "interval": CANDLE_INTERVAL_LTP,
                 "fromdate": (dt.date.today() - dt.timedelta(strategy_days)).strftime('%Y-%m-%d %H:%M'),
                 "todate": dt.datetime.now().strftime('%Y-%m-%d %H:%M')
                 }
        hist_data = obj.getCandleData(params)
        df_data = pd.DataFrame(hist_data["data"],
                               columns = ["date","open","high","low","close","volume"])
        df_data.set_index("date",inplace=True)
        df_data.index = pd.to_datetime(df_data.index)
        df_data.index = df_data.index.tz_localize(None)
        #df_data["avvol"] = df_data["volume"].rolling(10).mean().shift(1)
        
        try_latest = 0
        return df_data
    
    except Exception as e:
        print(f"Individual Historic failed for {ticker}")
        try_latest = try_latest+1        
        if try_latest <= try_count_short:
            print(colored(f"TRYYY_LATEST_DF {try_latest} again after {try_latest * sleep_time_short} sec\n", 'red'))
            time.sleep(try_latest * sleep_time_short)
            df_data = get_latestdata_DataFrame(obj, ticker, instrument_list, strategy_days, exchange="NSE")
            return df_data
        else:
            print(colored(f"No luck for Latest DF for {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_latest = 0
            return None
        
        
# df = get_latestdata_DataFrame("BANKNIFTY", 2, exchange="NSE")
# print(df)
        
        
        























def place_robo_order(obj, instrument_list, ticker, up_down, strategy, exl_order, exchange="NSE"):
    
    print(f"Place Order Function running {ticker} @@@ {up_down}......")
    
    if up_down == "UP":
        option_type_sell = "PE" # for Selling only
        option_type_buy = "CE" # for Buying only
    else:
        option_type_sell = "CE" # for Selling only
        option_type_buy = "PE" # for Buying only
    
    print("underlying_price")
    underlying_price = get_ltp_INSTRUMENT(obj, instrument_list, ticker, "NSE")
    print(underlying_price)
    
    #def final_contract(obj, ticker, instrument_list, underlying_price, option_type, duration = 0):
    
    final_contract_sell = final_contract(obj, ticker, instrument_list, underlying_price, option_type_sell, duration = 0)[2]
    final_contract_buy = final_contract(obj, ticker, instrument_list, underlying_price, option_type_buy, duration = 0)[2]
    
    print(final_contract_sell + "_" + final_contract_buy)
    
    quantity_option = quantity(obj, instrument_list, final_contract_sell) 
    lot_size = token_lookup_OPTION(final_contract_sell, instrument_list)[1]
    
    #ltp = get_ltp_INSTRUMENT(ticker) ###
    #print(ltp)
    
    global total_spend
    global fil_tickers # need to update global variable inside function
    
    #positions = positions_asin_excel()    
    #print("All Ordered Stocksssssssss = ", positions)
       
    #if ticker not in positions:
    #spend_percentage = (total_spend + (ltp+1)*quantity)/pos_size*100
    
    #spend_percentage = round((total_spend + (ltp)*quantity_option*lot_size)/pos_size*100,0)
    #print("Already Spend==", spend_percentage, "%")
    
    #if spend_percentage < spend_limit:  # To check before placing order so that we dont exceed actual amount available.
    if True:
            
        for i in range(row_excel_start_order, row_excel_end_order):
            
            stock2 = exl_order[i,2].value
            if stock2 is None:
                print(f"Sell {quantity_option} Lots of {final_contract_sell}")
                exl_order[i,1].value = dt.datetime.now()
                exl_order[i,2].value = strategy
                exl_order[i,3].value = "Intraday"
                exl_order[i,4].value = "Together"
                exl_order[i,5].value = ticker
                exl_order[i,6].value = final_contract_sell
                exl_order[i,7].value = lot_size
                exl_order[i,40].value = "SELL"
                exl_order[i,41].value = get_ltp_OPTION(obj, instrument_list, final_contract_sell, exchange="NFO")
                                    #def get_ltp_OPTION(obj, instrument_list, ticker, exchange="NFO")
                exl_order[i,42].value = quantity_option #quantity(final_contract_sell)
                            
                i = i+1
                print(f"Buy {quantity_option} Lots of {final_contract_buy}")
                exl_order[i,1].value = dt.datetime.now()
                exl_order[i,2].value = strategy
                exl_order[i,3].value = "Intraday"
                exl_order[i,4].value = "Together"
                exl_order[i,5].value = ticker
                exl_order[i,6].value = final_contract_buy
                exl_order[i,7].value = lot_size
                exl_order[i,40].value = "BUY"
                exl_order[i,41].value = get_ltp_OPTION(obj, instrument_list, final_contract_buy, exchange="NFO")
                exl_order[i,42].value = quantity_option #quantity(final_contract_buy)

                break  # As above is for 1 ticker only
    
    return 1


#place_robo_order(instrument_list, "BANKNIFTY", "BUY", exchange="NSE")




#get_ltp_OPTION(obj, instrument_list, "BANKNIFTY07FEB2446000PE", exchange="NFO")





# Ibirdi - made this function
def check_global_PnL(exl):
    print(colored("check_global_PnL Fucntion running....","green"))
    global_PnL = 0    
    for i in range(row_excel_start_order, row_excel_end_order):  # we have defined global r to get start of ORDER excel sheet 
        
        stock = exl[i,6].value
        if stock is not None:
            ind_pnl = exl[i,52].value
            if ind_pnl is not None:
                global_PnL = global_PnL + ind_pnl   
                
    return global_PnL



















# Ibirdi - made this function
def place_order_loss(ticker,buy_sell_final,quantity,current_price,ind_PnL,exl_order, excel_row):
    
    print(f"2nd time {buy_sell_final} {quantity} stocks of {ticker}")
    exl_order.range((excel_row+1,1), (excel_row+1,54)).color = (255, 127, 127) # i+1 beacuse range seems like working with index 1 and not 0
    exl_order[excel_row,46].value = dt.datetime.now()
    exl_order[excel_row,47].value = buy_sell_final
    exl_order[excel_row,48].value = ticker
    #exl_order[excel_row,15].value = quantity
    exl_order[excel_row,50].value = current_price
    #exl_order[excel_row,19].value = ind_PnL
    
    #if exl_order.name == "delta_nutral":
    #    print(f"Excelllllllllll sheet = {exl_order.name})
    #    exl_order[excel_row,56].value = current_price # this is to update temperory P&L only
    
    return 1




def check_individual_open_positions(obj, instrument_list, exl_order):
#def check_PnL():
    # check buy/sell from excel sheet, it is good if we get any error in API and have to start code again
    # in actual we can check all the live trades from API only
    print("check_individual_open_positions Fucntion running....")
    
    global loss_limit
    global profit_limit
    global single_pos_size
    #global r # cannot use this as it is going to be updated
    

    #global_PnL = 0
    for i in range(row_excel_start_order, row_excel_end_order):  # we have defined global r to get start of ORDER excel sheet 
        
        stock = exl_order[i,6].value
        initial_order = exl_order[i,40].value
        final_order = exl_order[i,47].value            
        
        if initial_order is not None and final_order is None:
            
            buy_sell = exl_order[i,40].value
            stock_price = exl_order[i,41].value
            stock_qty = exl_order[i,42].value
            lot_per_option = exl_order[i,7].value
            
            total_invested_individual = exl_order[i,43].value
            
            current_price = get_ltp_OPTION(obj, instrument_list, stock, exchange="NFO")
            #print(colored(f"Current price for {stock} = {current_price}", "yellow"))
            
            if current_price is not None:
                
                if buy_sell == "BUY":
                    ind_PnL = (current_price-stock_price)*stock_qty*lot_per_option
                    buy_sell_final = "SELL"
                else:
                    ind_PnL = -(current_price-stock_price)*stock_qty*lot_per_option
                    buy_sell_final = "BUY"
                
                if ind_PnL < -1 * total_invested_individual * loss_limit/100: # if we have Loss 
                    print(colored(f"22222 sahab LOSSSSSS {ind_PnL}", 'red'))
                    place_order_loss(stock,buy_sell_final,stock_qty,current_price,ind_PnL,exl_order, i)
              # def place_order_loss(ticker,buy_sell_final,quantity,current_price,ind_PnL,excel_row):
                    
                if ind_PnL > total_invested_individual * profit_limit/100: # if we have profit 
                    print(colored(f"22222 sahab PROFITTTTT {ind_PnL}", 'red'))
                    place_order_loss(stock,buy_sell_final,stock_qty,current_price,ind_PnL,exl_order, i)  
            else:
                print(f"LTP api failed for {stock}")
                            
    return None
                










#PnL_Tread = threading.Thread(target = check_PnL)
#PnL_Tread.start()


def find_lookbehind_effective_days(days):
    
    holiday_list = ['2024-01-22', '2024-01-26']    
    res = dt.date.today() - timedelta(days=1)
    effective_days = 0
    
    while True:            
        if res.weekday() not in [5,6] and str(res) not in holiday_list: # Sunday = 6
            days = days-1 
            #print(res)
            if days == 0:
                break
            
        effective_days = effective_days+1
        res = res - timedelta(days=1)   

    return res, effective_days+1









def all_orders_done():
    print("All Orders Done function...check if all Orders are completed one cycle....")
    for i in range(row_excel_start_order, row_excel_end_order):
        initial_order = exl_order[i,36].value
        final_order = exl_order[i,43].value
        #print(f"allll orderrrrr {initial_order} ~~~~ {final_order}")
        if (initial_order  is not None and final_order is None):
            return False   
    return True
#if (initial_order == "BUY" & final_order == "SELL") or (initial_order == "SELL" & final_order == "BUY"):

    
def already_in_orderlist(security, exl):
    for i in range(row_excel_start_order, row_excel_end_order):
        security2 = exl[i,5].value            
        
        if security2 == security:
            option = exl[i,6].value
            initial_order = exl[i,40].value
            final_order = exl[i,47].value
            
            if initial_order is not None and final_order is None:
                return True
    return False








def copy_LTP_to_excel(obj, instrument_list, exl_order, exchange="NFO"):
    
    print("copy_LTP_to_excel function.......")    
    for i in range(row_excel_start_order, row_excel_end_order):
        ticker = exl_order[i,6].value
        initial_order = exl_order[i,40].value
        final_order = exl_order[i,48].value
        if (ticker is not None and final_order is None):
            #print(f"{ticker} == {ticker is not None and final_order is None} and.....")
            exl_order[i,50].value = get_ltp_OPTION(obj, instrument_list, ticker, exchange)
            #if exl_order.name == "delta_nutral":
            #    exl_order[i,56].value = exl_order[i,50].value 
    return 1
            
    
        
    
    
 
    
 
#def place_robo_order(obj, instrument_list, ticker, up_down, strategy, exl_order, exchange="NSE"):  

def short_strangle(obj, instrument_list, ticker, current_price_ticker, strategy, exl_order):
    
    '''
    Short Strangle is used when the market is sideways and we are expecting the price 
    to be remains range bound in upcoming days. The strategy can be initiate 
    by selling a call and a selling a put.
    '''
    
    print(colored(f"short_strangle Strategies Function running....{ticker}", 'green'))
    
    # The call strike which we select to sell should be at or above the upper range,
    # similarly the put strike should be at or below the lower range.
    final_contract_CALL = final_contract(obj, ticker, instrument_list, current_price_ticker, "CE", duration = 0)[0]
                        #final_contract(obj, ticker, instrument_list, underlying_price, option_type, duration = 0)
    
    final_contract_PUT = final_contract(obj, ticker, instrument_list, current_price_ticker, "PE", duration = 0)[-1]
    
    lot_size = token_lookup_OPTION(final_contract_CALL, instrument_list)[1]
    
    for i in range(row_excel_start_order, row_excel_end_order):
        
        stock2 = exl_order[i,1].value
        if stock2 is None:
            exl_order[i,1].value = dt.datetime.now()
            exl_order[i,2].value = strategy
            exl_order[i,3].value = "Overnight"
            exl_order[i,4].value = "Together"
            exl_order[i,5].value = ticker
            exl_order[i,6].value = final_contract_CALL
            exl_order[i,7].value = lot_size
            exl_order[i,40].value = "SELL"
            exl_order[i,41].value = get_ltp_OPTION(obj, instrument_list, final_contract_CALL, exchange="NFO")
            exl_order[i,42].value = quantity(obj, instrument_list, final_contract_CALL)
                        
            i = i+1
            exl_order[i,1].value = dt.datetime.now()
            exl_order[i,2].value = strategy
            exl_order[i,3].value = "Overnight"
            exl_order[i,4].value = "Together"
            exl_order[i,5].value = ticker
            exl_order[i,6].value = final_contract_PUT
            exl_order[i,7].value = lot_size
            exl_order[i,40].value = "SELL"
            exl_order[i,41].value = get_ltp_OPTION(obj, instrument_list, final_contract_PUT, exchange="NFO")
            exl_order[i,42].value = quantity(obj, instrument_list, final_contract_PUT)

            break  # As above is for 1 ticker only
    
    
    
    return None

#print(short_strangle("BANKNIFTY", get_ltp_INSTRUMENT(obj, "BANKNIFTY","NSE"), "XXXX"))
    
    

    







def delta_nutral_initial_orders(obj, instrument_list, ticker, underlying_price, strategy, exl_deltanutral):
    
    '''
        Expiry date will remain same for all options including adjustments.
    '''
    
    print(colored(f"Delta Nutral Strategy Function running....{ticker}", 'green'))
    
    
    exl_deltanutral[3,15].value = expiry_total_profit_limit/100 # in %age
    exl_deltanutral[4,15].value = expiry_total_loss_limit/100 # in %age
    exl_deltanutral[6,15].value = strike_close_limit/100 # in %age
    exl_deltanutral[7,15].value = premium_limit # in %age # after that we dont do adjustments

    
    #exl[1,15].value = expiry_ind_profit_limit/100 # in %age
    #exl[3,15].value = expiry_total_profit_limit/100 # in %age
    #exl[4,15].value = expiry_total_loss_limit/100 # in %age
    #exl[6,15].value = strike_close_limit/100 # in %age
    #exl[7,15].value = premium_limit # in %age # after that we dont do adjustments
    
    
    # The call strike which we select to sell should be at or above the upper range,
    # similarly the put strike should be at or below the lower range.
    option_delta_CE, delta_CE, option_expiry_CE, security_strike_CE = option_contracts_closest_DELTA(obj, ticker, instrument_list, underlying_price, delta_cosidered_selling, duration = this_or_next_week_or, option_type="CE", exchange="NFO")
    option_delta_PE, delta_PE, option_expiry_PE, security_strike_PE = option_contracts_closest_DELTA(obj, ticker, instrument_list, underlying_price, delta_cosidered_selling, duration = this_or_next_week_or, option_type="PE", exchange="NFO")
    
    
    #final_contract_CALL = final_contract(obj, ticker, instrument_list, current_price_ticker, "CE", duration = 0)[0]    
    #final_contract_PUT = final_contract(obj, ticker, instrument_list, current_price_ticker, "PE", duration = 0)[-1]
    
    lot_size = token_lookup_OPTION(option_delta_CE, instrument_list)[1]
    no_lots = quantity(obj, instrument_list, option_delta_CE)
    
    for i in range(row_excel_start_order, row_excel_end_order):
        
        stock2 = exl_deltanutral[i,1].value
        if stock2 is None:
            option_ltp_CE = get_ltp_OPTION(obj, instrument_list, option_delta_CE, exchange="NFO")
            
            exl_deltanutral[i,1].value = dt.datetime.now()
            exl_deltanutral[i,2].value = strategy
            exl_deltanutral[i,3].value = "Overnight"
            exl_deltanutral[i,4].value = "Together"
            exl_deltanutral[i,5].value = ticker
            exl_deltanutral[i,6].value = option_delta_CE
            exl_deltanutral[i,7].value = lot_size
            exl_deltanutral[i,8].value = option_expiry_CE
            exl_deltanutral[i,9].value = security_strike_CE
            exl_deltanutral[i,10].value = limit_delta_ind_loss/100
            exl_deltanutral[i,14].value = delta_CE
            exl_deltanutral[i,40].value = "SELL"
            exl_deltanutral[i,41].value = option_ltp_CE
            exl_deltanutral[i,56].value = option_ltp_CE            
            exl_deltanutral[i,42].value = no_lots            
            exl_deltanutral[i,50].value = option_ltp_CE
            exl_deltanutral[i,55].value = "Strangle"
                        
            i = i+1
            
            option_ltp_PE = get_ltp_OPTION(obj, instrument_list, option_delta_PE, exchange="NFO")
            exl_deltanutral[i,1].value = dt.datetime.now()
            exl_deltanutral[i,2].value = strategy
            exl_deltanutral[i,3].value = "Overnight"
            exl_deltanutral[i,4].value = "Together"
            exl_deltanutral[i,5].value = ticker
            exl_deltanutral[i,6].value = option_delta_PE
            exl_deltanutral[i,7].value = lot_size
            exl_deltanutral[i,8].value = option_expiry_PE
            exl_deltanutral[i,9].value = security_strike_PE
            exl_deltanutral[i,10].value = limit_delta_ind_loss/100
            exl_deltanutral[i,14].value = delta_PE
            exl_deltanutral[i,40].value = "SELL"
            exl_deltanutral[i,41].value = option_ltp_PE
            exl_deltanutral[i,56].value = option_ltp_PE            
            exl_deltanutral[i,42].value = no_lots #quantity(obj, instrument_list, option_delta_PE)
            exl_deltanutral[i,50].value = option_ltp_PE
            exl_deltanutral[i,55].value = "Strangle"
            
            exl_deltanutral[i,15].value = (option_ltp_PE + option_ltp_CE)
            #exl_deltanutral[i,16].value = limit_diff_premium_delta_strategy/100
            #exl_deltanutral[i,17].value = limit_diff_premium_delta_strategy*(option_ltp_PE + option_ltp_CE)/100

            break  # As above is for 1 ticker only
    
    return None



def delta_nutral_ADJUSTMENT_orders(ticker, option_closest, option_closest_price, lot_per_option, stock_qty, exl_deltanutral, expiry_date, strike_security, sub_strategy, loss_limit, strategy):
    
    print(colored(f"Delta Nutral Adjustment Function running....{ticker}", 'green'))
    
    for i in range(row_excel_start_order, row_excel_end_order):
        
        stock2 = exl_deltanutral[i,1].value
        if stock2 is None:
            
            exl_deltanutral[i,1].value = dt.datetime.now()
            exl_deltanutral[i,2].value = strategy
            exl_deltanutral[i,3].value = "Overnight"
            exl_deltanutral[i,4].value = "Together"
            exl_deltanutral[i,5].value = ticker
            exl_deltanutral[i,6].value = option_closest
            exl_deltanutral[i,7].value = lot_per_option
            exl_deltanutral[i,8].value = expiry_date
            exl_deltanutral[i,9].value = strike_security            
            
            #exl_deltanutral[i,9].value = f"Adjustment_{ticker}"
            #exl_deltanutral[i,10].value = limit_delta_ind_loss/100
            exl_deltanutral[i,10].value = loss_limit/100
            
            exl_deltanutral[i,13].value = exl_deltanutral[i-1,13].value # for expiry trade, to copy only , just juggad, later change it
                        
            exl_deltanutral[i,40].value = "SELL"
            exl_deltanutral[i,41].value = option_closest_price
            exl_deltanutral[i,42].value = stock_qty  #quantity(obj, instrument_list, option_delta_CE)
            
            exl_deltanutral[i,50].value = option_closest_price
            exl_deltanutral[i,55].value = sub_strategy
            exl_deltanutral[i,56].value = option_closest_price
            break
               
    return None






def expiry_bull_call_spread_ADJUSTMENT_orders(ticker, option_closest, option_closest_price, lot_per_option, stock_qty, exl, expiry_date, strike_security, sub_strategy, loss_limit, strategy):
    
    print(colored(f"Delta Nutral Adjustment Function running....{ticker}", 'green'))
    
    for i in range(row_excel_start_order, row_excel_end_order):
        
        stock2 = exl[i,1].value
        if stock2 is None:
            
            exl[i,1].value = dt.datetime.now()
            exl[i,2].value = strategy
            exl[i,3].value = "Overnight"
            exl[i,4].value = "Together"
            exl[i,5].value = ticker
            exl[i,6].value = option_closest
            exl[i,7].value = lot_per_option
            exl[i,8].value = expiry_date
            exl[i,9].value = strike_security            
            exl[i,11].value = loss_limit/100
            
            exl[i,13].value = exl[i-1,13].value # for expiry trade, to copy only , just juggad, later change it
                        
            exl[i,40].value = "SELL"
            exl[i,41].value = option_closest_price
            exl[i,42].value = stock_qty  #quantity(obj, instrument_list, option_delta_CE)
            
            exl[i,50].value = option_closest_price
            exl[i,55].value = sub_strategy
            exl[i,56].value = option_closest_price
            break
               
    return None










def general_order(*args, **kwargs):
  """Prints the information passed to the function."""
  for arg in args:
    print(arg)
  for key, value in kwargs.items():
    print(f"{key}: {value}")

#general_order("Hello", "world", name="John", age=30)








def expiry_date_from_option(instrument, option):    
    inst_length = len(instrument)
    expiry_date = option[inst_length:inst_length+7]
    ce_pe = option[-2:]
    return expiry_date, ce_pe

#print(expiry_date_from_option("BANKNIFTY", "BANKNIFTY06MAR2446000PE"))




def check_security_percentage_PnL_limit_reached(obj, instrument_list, security, exl):
    
    #print(f"checkkkkkkkkkkkkkkkkk_security_percentage_PnL_limit_reached for {security}")
    
    """
    This is general function for calculating total Profit and Loss
    """
    
    pnl = 0
    investment = 0
    FLAG_reached_loss = False
    
    PERCENTAGE_PROFIT_LIMIT = exl[3,15].value * 100
    PERCENTAGE_LOSS_LIMIT = exl[4,15].value * 100
    
    #print(PERCENTAGE_LOSS_LIMIT)
    
    
    for i in range(row_excel_start_order, row_excel_end_order):
        security2 = exl[i,5].value
        
          
        
        if security2 == security:
            option = exl[i,6].value
            initial_order = exl[i,40].value
            final_order = exl[i,47].value
            
            if initial_order is not None:
                investment = investment + exl[i,43].value
                pnl = pnl + exl[i,52].value  
                
    #print(f"ddddddddddddd {pnl} {investment}")
    
    if investment == 0:
        security_perPnL = 0
    else:
        security_perPnL = round(pnl/investment*100, 2)
    
    if security_perPnL < -1*(PERCENTAGE_LOSS_LIMIT):
        print(colored(f"Percentage loss limit {security_perPnL}% has reached for {security} for STRATEGY {exl.name}", "red"))
        FLAG_reached_loss = True
        exl[4,16].value = "Hit"
        
        for i in range(row_excel_start_order, row_excel_end_order):
            security2 = exl[i,5].value            
            
            if security2 == security:
                option = exl[i,6].value
                initial_order = exl[i,40].value
                final_order = exl[i,47].value
                
                if initial_order is not None and final_order is None:
                    lot_per_option = exl[i,7].value
                    stock_price = exl[i,41].value
                    stock_qty = exl[i,42].value                    
                    ltp_option = exl[i,50].value  
                    current_ltp_option = get_ltp_OPTION(obj, instrument_list, option, exchange="NFO")
                    
                    place_order_loss(option,"Buy",stock_qty,current_ltp_option,"ind_PnL",exl, i)
                    
    if security_perPnL > PERCENTAGE_PROFIT_LIMIT:
        print(colored(f"Percentage Profit limit {security_perPnL}% has reached for {security} for STRATEGY {exl.name}", "green"))
        FLAG_reached_loss = True
        exl[3,16].value = "Hit"
        
        for i in range(row_excel_start_order, row_excel_end_order):
            security2 = exl[i,5].value            
            
            if security2 == security:
                option = exl[i,6].value
                initial_order = exl[i,40].value
                final_order = exl[i,47].value
                
                if initial_order is not None and final_order is None:
                    lot_per_option = exl[i,7].value
                    stock_price = exl[i,41].value
                    stock_qty = exl[i,42].value                    
                    ltp_option = exl[i,50].value  
                    current_ltp_option = get_ltp_OPTION(obj, instrument_list, option, exchange="NFO")
                    
                    place_order_loss(option,"Buy",stock_qty,current_ltp_option,"ind_PnL",exl, i)
                    
        
    return FLAG_reached_loss



def check_security_straddle_limit_reached(obj, instrument_list, security, exl):
    
    """
    This is general function for checking if we reached straddle
    """
    
    FLAG_reached_straddle = False
    
    STRADDLE_LIMIT = exl[6,9].value * 100
    
    
    for i in range(row_excel_start_order, row_excel_end_order):
        security2 = exl[i,5].value
        
          
        
        if security2 == security:
            option = exl[i,6].value
            initial_order = exl[i,40].value
            final_order = exl[i,47].value
            
            if initial_order is not None:
                investment = investment + exl[i,43].value
                pnl = pnl + exl[i,52].value  
                
    #print(f"ddddddddddddd {pnl} {investment}")
    
    if investment == 0:
        security_perPnL = 0
    else:
        security_perPnL = round(pnl/investment*100, 2)       
    
    if security_perPnL < (STRADDLE_LIMIT):
        print(colored(f"Straddle limit {security_perPnL}% has reached for {security} for STRATEGY {exl.name}", "red"))
        FLAG_reached_straddle = True
        exl[6,16].value = "Hit"
        
        for i in range(row_excel_start_order, row_excel_end_order):
            security2 = exl[i,5].value            
            
            if security2 == security:
                option = exl[i,6].value
                initial_order = exl[i,40].value
                final_order = exl[i,47].value
                
                if initial_order is not None and final_order is None:
                    lot_per_option = exl[i,7].value
                    stock_price = exl[i,41].value
                    stock_qty = exl[i,42].value                    
                    ltp_option = exl[i,50].value  
                    current_ltp_option = get_ltp_OPTION(obj, instrument_list, option, exchange="NFO")
                    
                    place_order_loss(option,"Buy",stock_qty,current_ltp_option,"ind_PnL",exl, i)
                    
    
                    
        
    return FLAG_reached_straddle






def delta_nutral_adjustment(obj, instrument_list, tickers, exl_deltanutral):
    
    '''
        Expiry date will remain same for all options including adjustments.
    '''
    
    for ticker in tickers:
        print(colored(f"Adjustments Delta Nutral Strategy Function running....{ticker}", 'green'))
        
        if check_security_percentage_PnL_limit_reached(obj, instrument_list, ticker, exl_deltanutral) == True:
            continue #The continue keyword is used to end the current iteration and continues to the next iteration


#ahhhhaaaa----------------get LTP of all the positions----------------------          
        total_premium = 0        
        current_diff_preimum = 0
        check_highest_profit = -99999999
        check_least_profit = 99999999
        
        for i in range(row_excel_start_order, row_excel_end_order):
            security = exl_deltanutral[i,5].value            
            
            if security == ticker:
                option = exl_deltanutral[i,6].value
                initial_order = exl_deltanutral[i,40].value
                final_order = exl_deltanutral[i,47].value
                
                #if initial_order is not None and final_order is not None:
                    #exl_deltanutral.range((i+1,1), (i+1,54)).color = (255, 127, 127) # i+1 beacuse range seems like working with index 1 and not 0
                    

                if initial_order is not None and final_order is None:
                                      
                    
                    lot_per_option = exl_deltanutral[i,7].value
                    stock_price = exl_deltanutral[i,41].value
                    stock_qty = exl_deltanutral[i,42].value                    
                    ltp_option = exl_deltanutral[i,50].value         
                    #option_profit = exl_deltanutral[i,52].value
                    option_profit = exl_deltanutral[i,58].value # Temp profit/loss
                    
                    #current_price = get_ltp_OPTION(obj, instrument_list, stock, exchange="NFO")
                    #print(colored(f"Current price for {stock} = {current_price}", "yellow"))
                    
                    total_premium = total_premium + ltp_option
                    
                    if option_profit >= check_highest_profit: #-99999999
                        check_highest_profit = option_profit                    
                        row_max_profit = i
                        #exl_deltanutral[i,56].value = check_highest_profit
                        #exl_deltanutral[i,57].value = row_max_profit
                    
                    if option_profit < check_least_profit: #+99999999
                        check_least_profit = option_profit
                        row_min_profit = i
                        #exl_deltanutral[i,58].value = check_least_profit
                        #exl_deltanutral[i,59].value = row_min_profit
                    
                    #current_diff_preimum = abs(ltp_option - current_diff_preimum)
                    row_store = i
                    
        
        #last_premium_diff_limit = exl_deltanutral[row_store,17].value
        
        #option_which_need_adjustment = exl_deltanutral[row_max_profit,6].value # it is option with max profit only
        option_price_adjustment = exl_deltanutral[row_min_profit,50].value # minimum profit premium
        expiry_date = exl_deltanutral[row_max_profit,8].value        
        
        option_with_max_profit = exl_deltanutral[row_max_profit,6].value # it is option which needs adjustment
        option_type = option_with_max_profit[-2:]
        
        option_with_min_profit = exl_deltanutral[row_min_profit,6].value
        
        
        
            
        
#ahhhhaaaa----------------get LTP of all the positions----------------------  



        
        #option, stock_qty, ltp_option, row_max_profit, current_diff_preimum, last_premium_diff_limit, option_price_adjustment, expiry_date, option_type, lot_per_option, option_with_max_profit = update_premium_delta_strategy(ticker, exl_deltanutral)
        
        #running_pnl = exl_deltanutral[row_min_profit,53].value
        temp_running_pnl = exl_deltanutral[row_min_profit,59].value # It will be temp P&L
        
        loss_limit = exl_deltanutral[row_min_profit,10].value        
        security_strike_adjust = exl_deltanutral[row_min_profit,9].value
        
        
        is_straddle1 = exl_deltanutral[row_min_profit,55].value
        is_straddle2 = exl_deltanutral[row_max_profit,55].value
        
           

        if temp_running_pnl < -1*(loss_limit):
            
            if not(is_straddle1 == "Straddle" or is_straddle2 == "Straddle"): 
            # after straddle we dont want to adjust, just checl global P&L and squareoff all orders.
            
                print(f"Lossssss {temp_running_pnl} < {loss_limit}")            
                print(colored(f"Adjustment Started for {ticker}.........", 'red'))
                
                print("ahhhhhhhhhhhhhhhhhhhhhhhhh")
                print(f"Option which needs Adjustment {option_with_max_profit} with premium = {option_price_adjustment}")
                print(f"Row_Max_profit = {row_min_profit}, Least profit = {check_least_profit}")
                print(f"Row_Min_profit = {row_max_profit}, Max Profit = {check_highest_profit}")
                
                          
                
                
                #print(f"Excelllllll row with minimum profit = {}")
                print(colored(f"Step-1 Copy LTP of Loss leg = {option_with_min_profit} to Temporary LTP (column 57)", 'green')) # it is done by below function "place_order_loss"
                exl_deltanutral[row_min_profit,56].value = exl_deltanutral[row_min_profit,50].value # cannot update here as it will update for all rows later
                
                
                
                
                print(colored(f"Step-2 Book prfitable leg = {option_with_max_profit}", 'green'))                        
                current_ltp_option = get_ltp_OPTION(obj, instrument_list, option_with_max_profit, exchange="NFO") #it is mandatory
                place_order_loss(option_with_max_profit,"Buy",stock_qty,current_ltp_option,"ind_PnL",exl_deltanutral, row_max_profit)
                
                
                            
                
                underlying_price = get_ltp_INSTRUMENT(obj, instrument_list, ticker,exchange="NSE")
                strike_security, option_closest, option_closest_price = option_contracts_closest_PREMIUM(obj, ticker, instrument_list, underlying_price, option_price_adjustment, expiry_date, option_type, exchange="NFO")
                
                print(colored(f"Step-3 Adjusted {option_closest} with premium = {option_closest_price}", 'green'))
                strike_security = float(strike_security)
                security_strike_adjust = float(security_strike_adjust)            
                check_straddle_criteria = abs(strike_security-security_strike_adjust)/strike_security*100
                print(f"check_straddle_criteria = {strike_security}")
                
                if check_straddle_criteria < 0.7:
                    print(colored("Make Straddel Nowwwwwwwwwwwwwwwwwwwww", "magenta"))
                    
                    
                    sub_strategy = "Straddle"
                    ce_pe = option_with_max_profit[-2:]
                    option_closest = option_with_min_profit[:-2] + ce_pe
                    print(option_closest)                
                    option_closest_price = get_ltp_OPTION(obj, instrument_list, option_closest, exchange="NFO")
                    strike_security = exl_deltanutral[row_min_profit,9].value          
                    
                    delta_nutral_ADJUSTMENT_orders(ticker, option_closest, option_closest_price, lot_per_option, stock_qty, exl_deltanutral, expiry_date, strike_security, sub_strategy, limit_delta_ind_loss, strategy="Delta Nutral")
                else:
                    sub_strategy = "Strangle"
                    delta_nutral_ADJUSTMENT_orders(ticker, option_closest, option_closest_price, lot_per_option, stock_qty, exl_deltanutral, expiry_date, strike_security, sub_strategy, limit_delta_ind_loss, strategy="Delta Nutral")      
                
                #---Updating premium for max and min profit for analysis only
                #update_premium_delta_strategy(ticker, exl_deltanutral)
                plot_asper_exl(tickers, exl_deltanutral)
            
            else:
                print(colored(f"STOPPED Adjustment for {ticker}.........", 'red'))
            
    return None










def expiry_bull_call_spread_initial_orders(obj, security, option, option_expiry, option_strike, exl, instrument_list, option_type):
    
    '''
        Expiry date will remain same for all options including adjustments.
    '''
    
    print(colored(f"expiry_bull_call_spread_initial_orders Function running....{security}", 'green'))
    
    # The call strike which we select to sell should be at or above the upper range,
    # similarly the put strike should be at or below the lower range.
    #option_delta_CE, delta_CE, option_expiry_CE, security_strike_CE = option_contracts_closest_DELTA(obj, ticker, instrument_list, underlying_price, delta_cosidered_selling, duration = this_or_next_week_or, option_type="CE", exchange="NFO")
    #option_delta_PE, delta_PE, option_expiry_PE, security_strike_PE = option_contracts_closest_DELTA(obj, ticker, instrument_list, underlying_price, delta_cosidered_selling, duration = this_or_next_week_or, option_type="PE", exchange="NFO")
    
    lot_size = token_lookup_OPTION(option, instrument_list)[1]
    no_lots = 1 #quantity(obj, instrument_list, option)
    ratio_considered = 5
    
    strategy = "Bull Spread"
    
    exl[1,15].value = expiry_ind_profit_limit/100 # in %age
    exl[3,15].value = expiry_total_profit_limit/100 # in %age
    exl[4,15].value = expiry_total_loss_limit/100 # in %age
    exl[6,15].value = strike_close_limit/100 # in %age
    exl[7,15].value = premium_limit # in %age # after that we dont do adjustments
    
    
    for i in range(row_excel_start_order, row_excel_end_order):
        
        stock2 = exl[i,1].value
        if stock2 is None:
            option_ltp_buy = get_ltp_OPTION(obj, instrument_list, option, exchange="NFO")
            
            exl[i,1].value = dt.datetime.now()
            exl[i,2].value = strategy
            exl[i,3].value = "Intraday"
            exl[i,4].value = "Together"
            exl[i,5].value = security
            exl[i,6].value = option
            exl[i,7].value = lot_size
            exl[i,8].value = option_expiry
            exl[i,9].value = option_strike
            #exl[i,10].value = limit_delta_ind_loss/100

            exl[i,40].value = "BUY"
            exl[i,41].value = option_ltp_buy          
            exl[i,42].value = no_lots            
            exl[i,50].value = option_ltp_buy
            exl[i,55].value = "Bull Spread"
                        
            i = i+1
            
            sell_premium = round(option_ltp_buy/ratio_considered,2)
            strike_security, option_closest, option_closest_price = option_contracts_closest_PREMIUM(obj, security, instrument_list, option_strike, sell_premium, option_expiry, option_type, exchange="NFO")
            
            
            
            #option_ltp_PE = get_ltp_OPTION(obj, instrument_list, option_delta_PE, exchange="NFO")
            exl[i,1].value = dt.datetime.now()
            exl[i,2].value = strategy
            exl[i,3].value = "Intraday"
            exl[i,4].value = "Together"
            exl[i,5].value = security
            exl[i,6].value = option_closest
            exl[i,7].value = lot_size
            exl[i,8].value = option_expiry
            exl[i,9].value = strike_security
            
            exl[i,11].value = expiry_ind_profit_limit/100
            
            exl[i,13].value = sell_premium # this is extra and will be used later for adjustment
            
            exl[i,40].value = "SELL"
            exl[i,41].value = option_closest_price           
            exl[i,42].value = no_lots*ratio_considered #quantity(obj, instrument_list, option_delta_PE)
            exl[i,50].value = option_closest_price
            exl[i,55].value = "Bull Spread"
            
            plot_asper_exl([security], exl)
            
            break  # As above is for 1 ticker only
    
    return None












def expiry_bull_call_spread_adjustment(obj, instrument_list, tickers, exl):
    
    #print(f"tickersssssdddddd = {tickers}")
       
    for ticker in tickers:
        print(colored(f"Adjustments Bull Call Spread for Expiry Strategy Function running....{ticker}", 'green'))
        
        if check_security_percentage_PnL_limit_reached(obj, instrument_list, ticker, exl) == True:
            #print("Before continueeeeeeeeeeeeeeeeeeeee")
            continue #The continue keyword is used to end the current iteration and continues to the next iteration

        

#ahhhhaaaa----------------get LTP of all the positions----------------------          
        total_premium = 0
        
        current_diff_preimum = 0
        check_highest_profit = -99999999
        check_least_profit = 99999999
        
        for i in range(row_excel_start_order, row_excel_end_order):
            security = exl[i,5].value            
            
            if security == ticker:
                option = exl[i,6].value
                initial_order = exl[i,40].value
                final_order = exl[i,47].value
                
                #if initial_order is not None and final_order is not None:
                    #exl.range((i+1,1), (i+1,54)).color = (255, 127, 127) # i+1 beacuse range seems like working with index 1 and not 0
                    

                if initial_order is not None and final_order is None:
                                      
                    
                    lot_per_option = exl[i,7].value
                    stock_price = exl[i,41].value
                    stock_qty = exl[i,42].value                    
                    ltp_option = exl[i,50].value         
                    #option_profit = exl[i,52].value
                    option_profit = exl[i,58].value # Temp profit/loss
                    
                    #current_price = get_ltp_OPTION(obj, instrument_list, stock, exchange="NFO")
                    #print(colored(f"Current price for {stock} = {current_price}", "yellow"))
                    
                    total_premium = total_premium + ltp_option
                    
                    # if option_profit >= check_highest_profit: #-99999999
                    #     check_highest_profit = option_profit                    
                    #     row_max_profit = i
                    
                    # if option_profit < check_least_profit: #+99999999
                    #     check_least_profit = option_profit
                    #     row_min_profit = i
                        
                    if initial_order == "BUY":
                        row_buy = i
                    
                    if initial_order == "SELL":
                        row_sell = i
                    
                    #current_diff_preimum = abs(ltp_option - current_diff_preimum)
                    row_store = i
        
#ahhhhaaaa----------------get LTP of all the positions----------------------  
 

# --------------check if strike prices are too close-----------------------       
        strike_buy = exl[row_buy,9].value
        strike_sell = exl[row_sell,9].value
        strike_differ = abs(strike_buy-strike_sell)/strike_buy*100        
        if strike_differ < strike_close_limit:
            exl[6,16].value = strike_differ
            exl[6,17].value = "Hit"
            continue
# -----------end of check if strike prices are too close-----------------------       

        
        running_pnl = exl[row_sell,53].value
        book_limit = exl[row_sell,11].value 
        
        
        saved_sell_premium = exl[row_sell,13].value        
        expiry_sell = exl[row_sell,8].value
        option_sell = exl[row_sell,6].value
        option_sell_ce_pe = option_sell[-2:]        
        option_sell_lots = exl[row_sell,42].value
        
        option_sell_lot_per_option = exl[row_sell,7].value
                
        
        if running_pnl > book_limit: # book when we have profit in sell leg
            
            #if not(is_straddle1 == "Straddle" or is_straddle2 == "Straddle"): 
            if True:
                
                print(f"Profitttt {running_pnl} > {book_limit}")            
                print(colored(f"Adjustment Started for {ticker}, now sell for more premium.........", 'red'))
                                                            
                underlying_price = get_ltp_INSTRUMENT(obj, instrument_list, ticker,exchange="NSE")
                strike_security, option_closest, option_closest_price = option_contracts_closest_PREMIUM(obj, ticker, instrument_list, underlying_price, saved_sell_premium, expiry_sell, option_sell_ce_pe, exchange="NFO")
                
                if option_closest_price > premium_limit:
                    
                    print("ahhhhhhhhhhhhhhhhhhhhhhhhh")
                    print(f"Sell another {ticker} with expiry date {expiry_sell} {option_sell_ce_pe} Option with premium = {saved_sell_premium}")
                              
                    
                    print(colored(f"Step-1 Book(buy) SELL leg = {option_sell}", 'green'))                        
                    current_ltp_option = get_ltp_OPTION(obj, instrument_list, option_sell, exchange="NFO") #it is mandatory
                    place_order_loss(option_sell,"BUY",option_sell_lots,current_ltp_option,"ind_PnL",exl, row_sell)
                    
                    print(colored(f"Step-2 Adjusted {option_closest} with premium = {option_closest_price}", 'green'))
                    sub_strategy = "Kuch nahi"
                    expiry_bull_call_spread_ADJUSTMENT_orders(ticker, option_closest, option_closest_price, option_sell_lot_per_option, option_sell_lots, exl, expiry_sell, strike_security, sub_strategy, expiry_ind_profit_limit, strategy="Bull Spread")
                    plot_asper_exl(tickers, exl)
                    
                    if exl[1,16].value is None:
                        exl[1,16].value = 1
                    else:
                        exl[1,16].value = exl[1,16].value+1
                    
                else:
                    print(colored(f"Step-2 Failed for {tickers} as premium = {option_closest_price} is lesssssssss", 'red'))
                    exl[7,16].value = option_closest_price
                    exl[7,17].value = "Hit"
                    
  
    
    return None























#----------------------------------Others


def plot_asper_exl(tickers, exl):
    
    print("Plotting as per Excel sheet is runningggg.....")
    
    for ticker in tickers:
        
        ce_temp = []
        pe_temp = []
        
        all_option_temp = []
        
        for i in range(row_excel_start_order, row_excel_end_order):  # we have defined global r to get start of ORDER excel sheet 
            
            security = exl[i,5].value
            
            
            if security == ticker:
                
                stock = exl[i,6].value
                initial_order = exl[i,40].value
                final_order = exl[i,47].value            
                
                if initial_order is not None and final_order is None:
                    
                    
                    buy_sell = exl[i,40].value
                    stock_price = exl[i,50].value
                    stock_lot_number = exl[i,42].value
                    strike = exl[i,9].value
                    ce_pe = stock[-2:]    
                    
                    #[("BUY", "CE", 1880, 16.15, 1)
                    all_option_temp.append((buy_sell, ce_pe, strike, stock_price, stock_lot_number))
                   
                                           
        #if len(ce_temp)>0 and len(pe_temp)>0:
        if len(all_option_temp)>0:
            
            plot_final_payoff(ticker,all_option_temp)           
            
            #ticker, strike_price_short_PE, premium_short_PE = pe_temp[0]
            #ticker, stirke_price_short_CE, premium_short_CE = ce_temp[0]
            #plot_final_payoff(ticker, strike_price_short_PE, premium_short_PE, stirke_price_short_CE, premium_short_CE)
            
    
    return None



















#--------------------------------GLOBAL P&L of all Strategies of all Days--------------------------------

start_global_excel = 12
end_global_excel = 200

def update_excel_global_pnl(tickers, exl_global_pnl):
    # this function will write datetime and security as per tickers list
    
    last = exl_global_pnl.range('C10000').end('up').row
    #print(f"wahhhhhhhhhhhhhhhh={last}")
    
    for ticker in tickers:
        for i in range(start_global_excel, end_global_excel):
            datetime = exl_global_pnl[i,2].value
            #date = datetime.date()
            security_exl = exl_global_pnl[i,6].value        
            #print(datetime)
            if security_exl is not None:
                if (datetime.date() == dt.datetime.now().date() and security_exl==ticker):
                    #print("Already There")
                    break
                #else:
            if i == end_global_excel-1:
                #print(f"rowwwwwwwwwwwwwwwwwwwwwwwww={i}")
                # now write there 
                
                                
                exl_global_pnl[last,2].value = dt.datetime.now()
                exl_global_pnl[last,3].value = dt.datetime.now().date()
                exl_global_pnl[last,6].value = ticker
                last = last+1
        
    return last

#update_excel_global_pnl(['BANKNIFTY', 'NIFTY'], exl_global_pnl)


def check_PnL_asper_excel_security(security, sheet):
    #print(colored("check_global_PnL Fucntion running....","green"))
    global_PnL = 0    
    for i in range(row_excel_start_order, 20): #row_excel_end_order
        stock = sheet[i,5].value
        #print(sheet.name, stock, security)
        if stock == security:
            ind_pnl = sheet[i,52].value
            
            if ind_pnl is not None:
                global_PnL = global_PnL + ind_pnl            
    return global_PnL


def update_global_pnl_excel(securities, exl_global_pnl, wb):
    
    print("Updating Global P&L excel....")
    
    for security in securities:
        for i in range(start_global_excel, end_global_excel):
            security_exl = exl_global_pnl[i,6].value
            
            if security_exl is not None:
                
                datetime = exl_global_pnl[i,2].value
                date = datetime.date()
                        
                #print(datetime)
                if (datetime.date() == dt.datetime.now().date()):
                    #print(f"{security_exl}, {security}")
                    if security_exl == security:
                        for j in range(12, 20):
                            strategy_exl = exl_global_pnl[11,j].value
                            #print(f"{strategy_exl}")
                            if strategy_exl is not None:
                                #print(f"{security_exl}")
                                for sheet in wb.sheets:
                                    #print(f"{security_exl}, {sheet.name}")
                                    if strategy_exl == sheet.name:  # NOw we have exact columns and excel sheet
                                        #print(strategy_exl)
                                        exl_global_pnl[i,2].value = dt.datetime.now()                                        
                                        exl_global_pnl[i,j].value = check_PnL_asper_excel_security(security, sheet)
    
                                
    return None
#update_global_pnl_excel("BANKNIFTY")
