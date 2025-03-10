import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cycler
import MetaTrader5 as mt5
import MT5Trading as mtt
from datetime import datetime

############ Graph settings ##########

colors = cycler('color', ['#669FEE', '#66EE91', '#9988DD', '#EECC55', '#88BB44', '#FFBBBB'])
plt.rc('figure', facecolor='#313233')
plt.rc('axes', facecolor='#313233', edgecolor='none', axisbelow=True, grid=True, prop_cycle=colors, labelcolor='gray')
plt.rc('grid', color='#474A4A', linestyle='solid')
plt.rc('xtick', color='gray')
plt.rc('ytick', direction='out', color='gray')
plt.rc('legend', facecolor='#313233', edgecolor='#313233')
plt.rc('text', color='#C9C9C9')

############ Graph settings ##########

# Calculate Stochastic Oscillator (5-3-3)
def calculate_stochastic_oscillator(df):
    low_min = df['low'].rolling(window=5).min()
    high_max = df['high'].rolling(window=5).max()
    df['%K'] = ((df['close'] - low_min) / (high_max - low_min)) * 100
    df['%D'] = df['%K'].rolling(window=3).mean()

# Calculate Bollinger Bands with dynamic SD
def calculate_bollinger_bands(df, sd=3):
    df['Middle Band'] = df['close'].rolling(window=13).mean()
    df['STD'] = df['close'].rolling(window=13).std()
    df['Upper Band'] = df['Middle Band'] + (df['STD'] * sd)
    df['Lower Band'] = df['Middle Band'] - (df['STD'] * sd)

# Determine Exit Signal based on Stochastic and Bollinger Bands
def determine_exit_signal(df):
    calculate_stochastic_oscillator(df)
    calculate_bollinger_bands(df, sd=3)  # Default to 3SD; adjust based on volatility or preference

    # Exit logic based on Stochastic and Bollinger Bands interaction
    df['Exit Signal'] = False
    for i in range(1, len(df)):
        if ((df['close'][i] > df['Upper Band'][i] or df['close'][i] < df['Lower Band'][i]) and df['%K'][i] < df['%D'][i]) or \
           (df['%K'][i-1] > df['%D'][i-1] and df['%K'][i] < df['%D'][i]):
            df['Exit Signal'][i] = True

def support_resistance(symbol):
    
    # Import the data
    while True:
        try:
            # Import the data
            df = mtt.MT5.get_data(symbol, 720, timeframe=mt5.TIMEFRAME_M2)[["open", "high", "low", "close", "tick_volume"]]
            break  # If the import is successful, break the loop
        except Exception as e:
            print("Could not retrieve data from mt5: ", e)
            continue  # If an error occurs, continue the loop and try again
            
    df_copy = df.copy()
    
    df_copy.columns = ["open", "high", "low", "close", "volume"]
    
    # Create empty columns
    df_copy["support"] = np.nan
    df_copy["resistance"] = np.nan
    
    # Calculate SMAs
    df_copy['SMA_5'] = df_copy['close'].rolling(window=5).mean()
    df_copy['SMA_8'] = df_copy['close'].rolling(window=8).mean()
    df_copy['SMA_13'] = df_copy['close'].rolling(window=13).mean()

    # Determine Entry Signal
    # Buy Signal: When SMA_5 > SMA_8 > SMA_13
    df_copy['Buy_Signal'] = (df_copy['SMA_5'] > df_copy['SMA_8']) & (df_copy['SMA_8'] > df_copy['SMA_13'])

    # Sell Signal: When SMA_5 < SMA_8 < SMA_13
    df_copy['Sell_Signal'] = (df_copy['SMA_5'] < df_copy['SMA_8']) & (df_copy['SMA_8'] < df_copy['SMA_13'])

    # Directly assign the boolean values
    buy = df_copy["Buy_Signal"].iloc[-1]
    sell = df_copy["Sell_Signal"].iloc[-1]
    
    return buy, sell

# mt5.initialize()
# True = Live Trading and False = Screener
# live = True

# if live:
#     current_account_info = mt5.account_info()
#     print("------------------------------------------------------------------")
#     print("Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#     print(f"Balance: {current_account_info.balance} ZAR, \t"
#           f"Equity: {current_account_info.equity} ZAR, \t"
#           f"Profit: {current_account_info.profit} ZAR")
#     print("------------------------------------------------------------------")
   
# # List of Stocks
# info_order = {
#     "EURUSD.ifx": ["EURUSD.ifx", 0.01],
# }
# returns = pd.DataFrame()

# start = datetime.now().strftime("%H:%M:%S")
# while True:
    
#     current_account_info = mt5.account_info()
#     if current_account_info.profit > current_account_info.balance * 0.01:
#         mtt.MT5.close_all_night()
    
#     if datetime.now().weekday() not in (5,6):
#         is_time = (datetime.now().minute % 1) == 0 and (datetime.now().second == 0) # be true every 3 minutes
#     else:
#         is_time = False

#     # Launch the algorithm
#     if is_time:
#         live = True
#         # Open the trades
#         for asset in info_order.keys():

#             # Initialize the inputs
#             symbol = info_order[asset][0]
#             lot = info_order[asset][1]

#             buy, sell = support_resistance(symbol)
            
#              # Run the algorithm
#             if live:
#              # print("buy:" + str(buy) + " sell:" + str(sell))
#                 # mtt.MT5.run(symbol, sell, buy, lot)
#                 mtt.MT5.run(symbol, buy, sell, lot)

#             else:
#                 print(f"Symbol: {symbol}\t"
#                      f"Buy: {buy}\t"
#                      f"Sell: {sell}")


