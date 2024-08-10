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

#https://docs.xlwings.org/en/stable/syntax_overview.html
import xlwings as xw

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



#extract the historical data at 9:20 am         
data_0920 = hist_data_0920(tickers, lookbehind_days_low_hi, CANDLE_INTERVAL_HIST_DATA, instrument_list) # if last 2 days are holiday then 2 will not work in fucntion
#FIFTEEN_MINUTE, ONE_DAY 
# if we use one day then volume comparision will be not ok, beacuse
# if we get DAY HIGH as one day value and the will compare FIVE_MIN candle for intraday then
# its not comparable

#time.sleep(try_count_long - ((time.time() - starttime) % try_count_long))



#--------------Get all Stocks HIGH, LOW and VOLUME and input in EXCEL sheet-----------------------
for ticker in tickers:
    #hi_lo_prices[ticker] = [data_0920[ticker]["high"].max(), data_0920[ticker]["low"].min(), data_0920[ticker]["volume"].mean()]
    hi_lo_prices[ticker] = [data_0920[ticker]["high"].max(), data_0920[ticker]["low"].min()]
    #print(hi_lo_prices)

r_start = 2    
for key, value in hi_lo_prices.items():
    
    exl_filter[r_start, 2].value = dt.datetime.now()
    exl_filter[r_start, 3].value = key
    exl_filter[r_start, 5].value = value    
    exl_filter[r_start, 8].value = HIGH_LIMIT * value[0]
    exl_filter[r_start, 9].value = LOW_LIMIT * value[1]
    #exl_filter[r_start, 8].value = VOL_LIMIT * value[2]
    r_start = r_start + 1
    
     
print("Initial Analysis Done i.e L-H for all Filtered Instruments\n")

#fil_tickers = filtered_tickers_nearhighlow(hi_lo_prices) #major change
fil_tickers = tickers
print("filtered tickers", "~~", fil_tickers)

#----------END of Get all Stocks HIGH, LOW and VOLUME and input in EXCEL sheet-----------------------


ML_STRATEGY()



global_row = 2
while dt.datetime.now() < dt.datetime.strptime(dt.datetime.now().strftime('%Y-%m-%d')+' 23:30','%Y-%m-%d %H:%M'):
    
    #global total_spend
    #global spend_limit
    print(colored("\n\nWhile loop running.....", "green"))
    print("starting passthrough at {}".format(dt.datetime.now()))
    
    #print("Remaining Stocks list =", fil_tickers)
    
    
    copy_LTP_to_excel(exchange="NFO") # Only to update LTP in excel sheet
    
    check_individual_open_positions()
    #global_PnL = check_PnL()
    global_PnL = check_global_PnL()  
    print(colored(f"Global P&L = {global_PnL}", "magenta"))
    
    
    exl_filter[global_row, 24].value = dt.datetime.now()
    exl_filter[global_row, 25].value = global_PnL
    global_row = global_row + 1
    
    if global_PnL > pos_size * Total_loss_limit/100:
        print("Changga loss ho gya, band kardo 22")
        print("Exiting all positions.....")
    else:
        if len(fil_tickers) > 0:
            if (total_spend/pos_size)*100 < spend_limit:
                #print("starting passthrough at {}".format(dt.datetime.now()))
                orb_strat(fil_tickers,hi_lo_prices, lookbehind_days_low_hi, "NSE") # last variable is for how many days we need to check max(high) and min(low)
                #all_orders_done()
                time.sleep(try_count_long - ((time.time() - starttime) % try_count_long)) # without this we got "Access denied because of exceeding access rate"
            else:
                print("Global Spend limit has reached")
        else:
            print("All FIltered Stocks are already placed and now only check GLOBAL P&L....")
            if all_orders_done() == True:
                print("All positions closed and now we shut down")
                global_PnL = check_PnL()    
                print(f"\nFinal Global P&L = {global_PnL}")
                break
            time.sleep(try_count_long - ((time.time() - starttime) % try_count_long))
            
    
        
from master import MasterClass
connect = MasterClass()
connect.connect_ANGELONE()
    
    
    
    
    