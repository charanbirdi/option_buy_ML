# Plotting option payoff graph


import numpy as np
import matplotlib.pyplot as plt
import seaborn






# def plot_final_payoff_extraaaaaaa(ticker, strike_price_short_PE, premium_short_PE, stirke_price_short_CE, premium_short_CE):
    
#     print(f"PRINTINGGGGGG for {ticker} with {strike_price_short_PE}, {stirke_price_short_CE}")
    
#     strike_price_short_PE, premium_short_PE, stirke_price_short_CE, premium_short_CE = float(strike_price_short_PE), float(premium_short_PE), float(stirke_price_short_CE), float(premium_short_CE)
    
    
    
#     min_value = min(strike_price_short_PE, stirke_price_short_CE)
#     max_value = max(strike_price_short_PE, stirke_price_short_CE)
    
#     range_min = int(min_value*0.97)
#     range_max = int(max_value*1.03)    
#     print(f"Range for Plot = ({range_min}, {range_max})")    
    
#     sT = np.arange(range_min,range_max,1)  
#     #sT = np.arange(45000,48000,1)
    
    
#     short_put_payoff = put_payoff(sT, strike_price_short_PE, premium_short_PE)*-1.0
#     short_call_payoff = call_payoff(sT, stirke_price_short_CE, premium_short_CE )*-1.0
#     total_payoff = short_call_payoff + short_put_payoff 
    
#     profit = round(max(total_payoff),1)
#     loss = round(min(total_payoff), 1)
#     print(f"Profit limit = {loss}, {profit}")
    
#     #%matplotlib inline
#     fig, ax = plt.subplots()
#     ax.spines['bottom'].set_position('zero')
#     ax.plot(sT, total_payoff, color ='g')
    
#     title = f"{ticker} ({strike_price_short_PE}, {stirke_price_short_CE})" 
#     ax.set_title(title)
#     plt.xlabel('Option Price (sT)')
#     plt.ylabel('Profit & Loss')
#     plt.show()
    
#     return None








def call_payoff(sT, strike_price, premium):
    return np.where(sT > strike_price, sT - strike_price, 0)-premium


def put_payoff(sT, strike_price, premium):
    return np.where(sT < strike_price, strike_price - sT, 0) - premium





def plot_final_payoff(ticker, all_args):
    
    #print(f"PRINTINGGGGGG for {ticker}")
    
    #strike_price_short_PE, premium_short_PE, stirke_price_short_CE, premium_short_CE = float(strike_price_short_PE), float(premium_short_PE), float(stirke_price_short_CE), float(premium_short_CE)
    long_call_payoff, short_call_payoff, long_put_payoff, short_put_payoff = 0,0,0,0
    
    
            
    list_all = [] # this is needed only for getting max and min values
    for i in all_args:
        sell_buy, ce_pe, strike_price, premium, lots = i
        list_all.append(strike_price)
        
    
    #min_value = min(strike_price_short_PE, stirke_price_short_CE)
    #max_value = max(strike_price_short_PE, stirke_price_short_CE)
    
    min_value = min(x for x in list_all if x != 0)
    max_value = max(x for x in list_all if x != 0)
    
    range_min = int(min_value*0.97)
    range_max = int(max_value*1.03)    
    #print(f"Range for Plot = ({range_min}, {range_max})")    
    
    sT = np.arange(range_min,range_max,1)
    
    
    for i in all_args:
        sell_buy, ce_pe, strike_price, premium, lots = i
        if sell_buy == "BUY" and ce_pe == "PE": 
            long_put_payoff = put_payoff(sT, strike_price, premium)*lots
        elif sell_buy == "BUY" and ce_pe == "CE": 
            long_call_payoff = call_payoff(sT, strike_price, premium)*lots
        elif sell_buy == "SELL" and ce_pe == "PE": 
            short_put_payoff = put_payoff(sT, strike_price, premium)*lots*-1.0
        elif sell_buy == "SELL" and ce_pe == "CE": 
            short_call_payoff = call_payoff(sT, strike_price, premium )*lots*-1.0
        else:
            print("EROOORRRRR")
            
    total_payoff = long_call_payoff + short_call_payoff + long_put_payoff + short_put_payoff
    
    
    
      
    profit = round(max(total_payoff),1)
    loss = round(min(total_payoff), 1)
    #print(f"Profit limit = {loss}, {profit}")
    
    #%matplotlib inline
    fig, ax = plt.subplots()
    ax.spines['bottom'].set_position('zero')
    ax.plot(sT, total_payoff, color ='g')
    
    #title = f"{ticker} ({strike_price_short_PE}, {stirke_price_short_CE})" 
    title = f"{ticker}"
    
    ax.set_title(title)
    plt.xlabel('Option Price (sT)')
    plt.ylabel('Profit & Loss')
    plt.show()
    
    return None





if __name__ == '__main__':
    #plot_final_payoff("BANKNIFTY", 47100, 275, 46600, 327.1)
    
    #all_args = [("BUY", "CE", 1880, 16.15), ("BUY", "PE", 1840, 17), ("SELL", "CE", 1860, 23.8), ("SELL", "PE", 1860, 25.5)]
    all_args = [("BUY", "CE", 45900, 151, 1), ("SELL", "CE", 46400, 37, 5)]
    #all_args = [("BUY", "CE", 45900, 116.4)]
    #all_args = [("SELL", "CE", 46400, 20.3)]
    
    plot_final_payoff("BANKNIFTY", all_args)


