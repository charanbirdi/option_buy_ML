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
sleep_time_long = 20
sleep_time_short = 7

try_count_long = 7
try_count_short = 4



#global obj



class MasterClass():
    
    

    # try_con = 0
    # sleep_time_long = 20
    # sleep_time_short = 7
    # try_count_long = 7
    # try_count_short = 4
    
    def __init__(self):
        self.API_KEY = 'oPvM0VnS' #
        self.CLIENT_CODE = 'C52284659'
        self.PWD = '1030' #Your Pin
        self.AUTH_TOKEN = '2a68e665-d2d5-42b6-9c73-c2139545c8c0'  #Your QR code value
        self.token = 'PGAFWLOTMLQKIR3EMWOGHU6KVY' #for OTP https://smartapi.angelbroking.com/enable-totp
        
        
    def connect_ANGELONE(self):
        #global try_con        
        global obj
        # self.API_KEY = API_KEY
        # self.CLIENT_CODE = CLIENT_CODE
        # self.PWD = PWD #Your Pin
        # self.AUTH_TOKEN = AUTH_TOKEN  #Your QR code value
        # self.token = token
        # self.try_con = try_con
        
        try:
            obj=SmartConnect(api_key=self.API_KEY)
            data = obj.generateSession(self.CLIENT_CODE, self.PWD, TOTP(self.token).now())
            feed_token = obj.getfeedToken()        
            if obj is None:
                raise Exception("This is an exception")
            
            self.try_con = 0
            print(colored(f"CONNECTED TO ANGELONE SERVER $$$$$", 'green'))
            return obj
        
        except Exception as e:
            print(f"CONNECTION Api failed: {e}")
            self.try_con = self.try_con+1        
            if self.try_con <= self.try_count_long:
                print(colored(f"TRYYY-{self.try_con} again after {self.try_con*self.sleep_time_short} sec", 'red'))
                time.sleep(self.try_con * self.sleep_time_short)
                obj = self.connect_ANGELONE()
                return obj
            else:
                print(colored(f"Better Luck next time, Connection not established", 'red'))
                sys.exit(0) # 0- without error message, 1-with error message in end
        


connect = MasterClass()
connect.connect_ANGELONE()

print(obj)


















 
            
connect_ANGELONE() # Connect with AngelOne API

# --------------------From AngelOne API github page --------------------------------
#retry_strategy=0 for simple retry mechanism
#sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, feed_token, max_retry_attempt=2, retry_strategy=0, retry_delay=10, retry_duration=30)

#retry_strategy=1 for exponential retry mechanism
# sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, feed_token, max_retry_attempt=3, retry_strategy=1, retry_delay=10,retry_multiplier=2, retry_duration=30)
# --------------------End of From AngelOne API github page --------------------------------


correlation_id = "stream_1" #any string value which will help identify the specific streaming in case of concurrent streaming
action = 1 #1 subscribe, 0 unsubscribe
mode = 1 #1 for LTP, 2 for Quote and 2 for SnapQuote


instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
response = urllib.request.urlopen(instrument_url)
instrument_list = json.loads(response.read())

#instrument_list = json.load(open('token_file_updated.json'))


tickers = ['BANKNIFTY', 'NIFTY', 'FINNIFTY'] #'BANKNIFTY', 'NIFTY', 'FINNIFTY'
print(f"INSTRUMENT OF INTEREST = {tickers}")

wb = xw.Book('AngelOne_Option.xlsx')
exl_filter = wb.sheets['filtered']
exl_order = wb.sheets['orders']

exl_filter.range("A3:K300").clear_contents()
exl_filter.range("Y3:Z300").clear_contents()

exl_order.range("B16:S300").clear_contents()
exl_order.range("AL16:AQ300").clear_contents()
exl_order.range("AU16:AW300").clear_contents()
exl_order.range("AY16:AY300").clear_contents()



# -----------LOSS PROFIT LIMITS------------
ordered = [] # All ordered stocks, we are not using it
hi_lo_prices = {}



#-------Ticker FIlter limit to select final stocks--------
TICKER_HIGH_FILTER_LIMIT = 0.9 # it means stock price is near to ATH and assuming going up, so we can buy
TICKER_LOW_FILTER_LIMIT = 1.1  # it means stock price is near to ATL and assuming going down, so we can sell it

# Above limit should be less than lower mentioned limits , logically
# below limits are to filter the instruments but I have disabled the same in strategy------
#-----Strategy Limits------------
LOW_LIMIT = 1.01
HIGH_LIMIT = 0.9
#VOL_LIMIT = 0.5








#-----------POSITION SIZE LIMIT-------------------
total_spend = 0
spend_limit = 90 # 90% of total available
loss_limit = 50 # 10% of position size
profit_limit = 90 # 10% of position size

Total_loss_limit = 5 # 10% of position size
single_pos_size = 50000
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


class Option:
    
    def __init__(self):
        self.ticker = ticker
        self.exchange = "NFO"
        
        
        
    def get_ltp_OPTION(self):
        #print("Getting OPTION LTP Function....")
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
            try_ltp_option = try_ltp_option+1        
            if try_ltp_option <= try_count_short:
                print(colored(f"TRYYYYY_LTPPPP {try_ltp_option} again after {try_ltp_option * sleep_time_short} sec\n", 'red'))
                time.sleep(sleep_time_short)
                ltp_stocks = get_ltp_OPTION(ticker,exchange="NFO")
                return ltp_stocks
            else:
                print(colored(f"No luck for {ticker}, ~~~~~ Now move ON\n", 'red'))
                try_ltp_option = 0
                return None
    
    
option_object = Option()
print(option_object.get_ltp_OPTION("BANKNIFTY31JAN2445200CE"))
    
    
    
    
    
    
    
    




try_ltp_instrument = 0
def get_ltp_INSTRUMENT(ticker,exchange="NSE"):
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
        try_ltp_instrument = try_ltp_instrument+1        
        if try_ltp_instrument <= try_count_short:
            print(colored(f"TRYYYYY_LTPPPP {try_ltp_instrument} again after {try_ltp_instrument * sleep_time_short} sec\n", 'red'))
            time.sleep(try_ltp_instrument * sleep_time_short)
            ltp_stocks = get_ltp_INSTRUMENT(ticker,exchange="NSE")
            return ltp_stocks
        else:
            print(colored(f"No luck for {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_ltp_instrument = 0
            return None
        
#print(get_ltp_INSTRUMENT("FINNIFTY",exchange="NSE"))       
        
        









def quantity(ticker,exchange="NFO"):
    
    #global single_pos_size    
    ltp = get_ltp_OPTION(ticker,exchange)
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
  

 
def positions_asin_excel():
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
def individual_hist_data(ticker,duration,interval,exchange="NSE"):
    
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
            hist_data = individual_hist_data(ticker,duration,interval,exchange="NSE")
            return hist_data
        else:
            print(colored(f"No luck for Historical {ticker}, ~~~~~ Now move ON\n", 'red'))
            try_ind_hist = 0
            return None
    
        
def hist_data_0920(tickers,duration,interval,instrument_list,exchange="NSE"):
    print("\nHistorical Data Function running.....")
    #try:
    hist_data_tickers = {}
    for ticker in tickers:
        time.sleep(try_count_short) # without this we got "Access denied because of exceeding access rate"
        print(f"Getting Historical Data for {ticker}..")
        hist_data = individual_hist_data(ticker,duration,interval,exchange="NSE")
        
        df_data = pd.DataFrame(hist_data["data"],
                               columns = ["date","open","high","low","close","volume"])
        df_data.set_index("date",inplace=True)
        df_data.index = pd.to_datetime(df_data.index)
        df_data.index = df_data.index.tz_localize(None)
        
        df_data["gap"] = ((df_data["open"]/df_data["close"].shift(1))-1)*100
        
        hist_data_tickers[ticker] = df_data
        
    return hist_data_tickers

#data_0920 = hist_data_0920(tickers, 4, CANDLE_INTERVAL_HIST_DATA, instrument_list)






def short_strangle(ticker, current_price_ticker, strategy):
    
    '''
    Short Strangle is used when the market is sideways and we are expecting the price 
    to be remains range bound in upcoming days. The strategy can be initiate 
    by selling a call and a selling a put.
    '''
    
    print(colored(f"short_strangle Strategies Function running....{ticker}", 'green'))
    
    # The call strike which we select to sell should be at or above the upper range,
    # similarly the put strike should be at or below the lower range.
    final_contract_CALL = final_contract(ticker, current_price_ticker, "CE", duration = 0)[0]
    final_contract_PUT = final_contract(ticker, current_price_ticker, "PE", duration = 0)[-1]
    
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
            exl_order[i,41].value = get_ltp_OPTION(final_contract_CALL)
            exl_order[i,42].value = quantity(final_contract_CALL)
                        
            i = i+1
            exl_order[i,1].value = dt.datetime.now()
            exl_order[i,2].value = strategy
            exl_order[i,3].value = "Overnight"
            exl_order[i,4].value = "Together"
            exl_order[i,5].value = ticker
            exl_order[i,6].value = final_contract_PUT
            exl_order[i,7].value = lot_size
            exl_order[i,40].value = "SELL"
            exl_order[i,41].value = get_ltp_OPTION(final_contract_PUT)
            exl_order[i,42].value = quantity(final_contract_PUT)

            break  # As above is for 1 ticker only
    
    
    
    return None

#print(short_strangle("BANKNIFTY", get_ltp_INSTRUMENT("BANKNIFTY","NSE"), "XXXX"))





# Ibirdi - made this function
def ML_STRATEGY():
    
    #global r
    
    print(colored("Machine Learning Strategies Function running....", 'green'))
    #strategy_list = []
    #strategy_list = [{'BANKNIFTY':['ML_sideway', 'Buy_PUT', 'Sell_CALL']}]
    
    sl=1

    for i in range(row_filter_start, row_filter_end):
        
        security = exl_filter[i,3].value
        
        if security is not None:
            
            #print(f"Machine Learning Strategies Function running....{security}")
            
            #temp_list_each_security = []
            ticker_H = exl_filter[i,5].value
            ticker_L = exl_filter[i,6].value
            current_price_ticker = get_ltp_INSTRUMENT(security,"NSE") # We are getting list of 5 options
           
            #---------Machine Learning Strategy-------------------
            ticker_ML_prediction = exl_filter[i,17].value
            
            if ticker_ML_prediction is not None:
                
                if ticker_ML_prediction == "Side-way":
                    strategy = "ML_sideway_Short_Strangle"
                    short_strangle(security, current_price_ticker, strategy)
                                                                
    return None

#tickers_high = filtered_tickers_nearhighlow(data_0920) #identify tickers with maximum gap up/down



def get_latestdata_DataFrame(ticker, strategy_days, exchange="NSE"):
    
    print("get_latestdata_DF Function running....")
    
    print(f"Getting latest price, volume for {ticker} is running.....")
    time.sleep(try_count_short)
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
        
        
    return df_data

# df = get_latestdata_DataFrame("BANKNIFTY", 2, exchange="NSE")
# print(df)









def place_robo_order(instrument_list, ticker, up_down, strategy, exchange="NSE"):
    
    print(f"Place Order Function running {ticker} @@@ {up_down}......")
    
    if up_down == "UP":
        option_type_sell = "PE" # for Selling only
        option_type_buy = "CE" # for Buying only
    else:
        option_type_sell = "CE" # for Selling only
        option_type_buy = "PE" # for Buying only
    
    
    underlying_price = get_ltp_INSTRUMENT(ticker, "NSE")
    #print(underlying_price)
    
    final_contract_sell = final_contract(ticker, underlying_price, option_type_sell, duration = 0)[2]
    final_contract_buy = final_contract(ticker, underlying_price, option_type_buy, duration = 0)[2]
    
    #print(final_contract_sell + "_" + final_contract_buy)
    
    quantity_option = quantity(final_contract_sell)    
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
                exl_order[i,41].value = get_ltp_OPTION(final_contract_sell)
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
                exl_order[i,41].value = get_ltp_OPTION(final_contract_buy)
                exl_order[i,42].value = quantity_option #quantity(final_contract_buy)

                break  # As above is for 1 ticker only
    
    return 1


#place_robo_order(instrument_list, "BANKNIFTY", "BUY", exchange="NSE")


def orb_strat(tickers, hi_lo_prices, strategy_days, exchange="NSE"): # Here tickers are filtered tickers--
    
    print(colored("ORB strategy Function running....", "green"))
    
    
    for ticker in tickers:
        print(f"ORB strategy Function running for........{ticker}")
        
        unique_strategy_order = "Open_Range_Breakout" + "#" + ticker
        positions = positions_asin_excel() # Order list as per excel sheet
        
        #print(positions)
        #print(unique_strategy_order)
        
        if unique_strategy_order not in positions:
            df_data = get_latestdata_DataFrame(ticker, strategy_days, exchange) # Get latest data
            if df_data["close"].iloc[-1] >= HIGH_LIMIT * hi_lo_prices[ticker][0]:
                
                place_robo_order(instrument_list, ticker, "UP", "Open_Range_Breakout")
                #print("bought {} stocks of {}".format(quantity(ticker),ticker))
            elif df_data["close"].iloc[-1] <= LOW_LIMIT * hi_lo_prices[ticker][1]:
                #print(unique_strategy_order)
                place_robo_order(instrument_list, ticker, "DOWN", "Open_Range_Breakout")
                #print("sold {} stocks of {}".format(quantity(ticker),ticker))
            
    return None







# Ibirdi - made this function
def check_global_PnL():
    print(colored("check_global_PnL Fucntion running....","green"))
    global_PnL = 0    
    for i in range(row_excel_start_order, row_excel_end_order):  # we have defined global r to get start of ORDER excel sheet 
        
        stock = exl_order[i,6].value
        if stock is not None:
            ind_pnl = exl_order[i,52].value
            if ind_pnl is not None:
                global_PnL = global_PnL + ind_pnl            
    return global_PnL



# Ibirdi - made this function
def check_individual_open_positions():
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
            
            current_price = get_ltp_OPTION(stock)
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
                    place_order_loss(stock,buy_sell_final,stock_qty,current_price,ind_PnL,i)
                    
                if ind_PnL > total_invested_individual * profit_limit/100: # if we have profit 
                    print(colored(f"22222 sahab PROFITTTTT {ind_PnL}", 'red'))
                    place_order_loss(stock,buy_sell_final,stock_qty,current_price,ind_PnL,i)  
            else:
                print(f"LTP api failed for {stock}")
                            
    return None
                








# Ibirdi - made this function
def place_order_loss(ticker,buy_sell_final,quantity,current_price,ind_PnL,excel_row):
    
    print(f"2nd time {buy_sell_final} {quantity} stocks of {ticker}")    
    exl_order[excel_row,46].value = dt.datetime.now()
    exl_order[excel_row,47].value = buy_sell_final
    exl_order[excel_row,48].value = ticker
    #exl_order[excel_row,15].value = quantity
    exl_order[excel_row,50].value = current_price
    #exl_order[excel_row,19].value = ind_PnL
    
    return 1


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

working_days_considered = 2
lookbehind_days_low_hi_tuple = find_lookbehind_effective_days(working_days_considered)
lookbehind_days_low_hi = lookbehind_days_low_hi_tuple[1]
print(f'FOR working days considered = {working_days_considered}, LOOKBEHIND_EFFECTIVE_DAYS = {lookbehind_days_low_hi_tuple}')








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

    



def copy_LTP_to_excel(exchange="NFO"):
    
    print("copy_LTP_to_excel function.......")    
    for i in range(row_excel_start_order, row_excel_end_order):
        ticker = exl_order[i,6].value
        initial_order = exl_order[i,40].value
        final_order = exl_order[i,48].value
        if (ticker is not None and final_order is None):
            #print(f"{ticker} == {ticker is not None and final_order is None} and.....")
            exl_order[i,50].value = get_ltp_OPTION(ticker)          
    return 1
            
    
        
    
    
    
    
    
    