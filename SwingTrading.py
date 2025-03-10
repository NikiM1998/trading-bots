import ta
import numpy as np
import warnings
from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
import MT5Trading as mtt
import AlgorithmicScalpingPriceActionSMARSI as gb #importing GoldenBoy
warnings.filterwarnings("ignore")
mt5.initialize()

timeFrames = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M10, mt5.TIMEFRAME_M15, mt5.TIMEFRAME_M30, mt5.TIMEFRAME_H1, mt5.TIMEFRAME_H4]
num_days = [1440*1, 288*2, 144*3, 96*4, 48*5, 24*6, 6*7] # number of days you want to look back to for each time frame defined. NB: number of elements of this array must match number in timeFrames 
# 1440 is how many minutes are in 1 day. You multiply with the number of days you want to go into the past by. Here I am looking 1 day for the min chart, 2 days for the 5 min chart and so on.

def svm_reg_trading(symbol):
    buy_count = 0
    sell_count = 0

    num_days_inx_cnt = 0
    for timeFrame in timeFrames:
        def feature_engineering(df):
            """ Create new variables"""
    
            # We copy the dataframe to avoid interferences in the data
            df_copy = df.dropna().copy()
    
            # Create the returns
            df_copy["returns"] = df_copy["close"].pct_change(1)
    
            # Create the SMAs
            df_indicators = ta.add_all_ta_features(
            df, open="open", high="high", low="low", close="close", volume="volume", fillna=True).shift(1)
            
            # Add MACD
            df_copy['MACD'] = ta.trend.macd(df_copy["close"])
    
            dfc = pd.concat((df_indicators, df_copy), axis=1)
    
            return dfc.dropna()
    
    
        while True:
            try:
                # Import the data
                df = mtt.MT5.get_data(symbol, num_days[num_days_inx_cnt], timeframe=timeFrame)[["open", "high", "low", "close", "tick_volume"]]
                break  # If the import is successful, break the loop
            except Exception as e:
                print("Could not retrieve data from mt5: ", e)
                continue  # If an error occurs, continue the loop and try again
        
        num_days_inx_cnt += 1 # increment index counter
        
        df.columns = ["open", "high", "low", "close", "volume"]
    
        dfc = feature_engineering(df)
    
        # Percentage train set
        split = int(0.99*len(dfc))
    
        # Train set creation
        X_train = dfc.iloc[:split,6:dfc.shape[1]-1]
        y_train = dfc[["returns"]].iloc[:split]
    
        # Test set creation
        X_test = dfc.iloc[split:,6:dfc.shape[1]-1]
        y_test = dfc[["returns"]].iloc[split:]
    
        # What you need to remind about this chapter
        from sklearn.preprocessing import StandardScaler
        sc = StandardScaler()
    
        X_train_sc = sc.fit_transform(X_train)
        X_test_sc = sc.transform(X_test)
    
        from sklearn.decomposition import PCA
        pca = PCA(n_components=6)
        X_train_pca = pca.fit_transform(X_train_sc)
        X_test_pca = pca.transform(X_test_sc)
    
        # Import the class
        from sklearn.svm import SVR
    
        # Initialize the class
        reg = SVR()
    
        # Fit the model
        reg.fit(X_train_pca, y_train)
    
        # Create predictions for the whole dataset
        X = np.concatenate((X_train_pca, X_test_pca), axis=0)
    
        dfc["prediction"] = reg.predict(X)
    
        buy = dfc["prediction"].iloc[-1]>0
        sell = dfc["prediction"].iloc[-1]<0
        
        if buy:
            buy_count += 1
        elif sell:
            sell_count += 1
                
        if buy_count > sell_count:
            return 1, 0
        elif sell_count > buy_count:
            return 0, 1
        else:
            return 0, 0


mt5.initialize()
# True = Live Trading and False = Screener
live = True

if live:
    current_account_info = mt5.account_info()
    print("------------------------------------------------------------------")
    print("Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(f"Balance: {current_account_info.balance} USD, \t"
          f"Equity: {current_account_info.equity} USD, \t"
          f"Profit: {current_account_info.profit} USD")
    print("------------------------------------------------------------------")

# info_order = {
#     # "EURUSD.ifx": ["EURUSD.ifx", 0.03],
#     # "AUDCAD.ifx": ["AUDCAD.ifx", 0.02],
#     # "USDCAD.ifx": ["USDCAD.ifx", 0.02],
#     # "GBPUSD.ifx": ["GBPUSD.ifx", 0.02]
#     "EURUSD.ifx": ["EURUSD.ifx", 0.01],
# }

info_order = {
    "EURAUD": ["EURAUD", 2.0],
    "USDCAD": ["USDCAD", 2.0],
    "EURUSD": ["EURUSD", 2.0],    
}

start = datetime.now().strftime("%H:%M:%S")
while True:
    # Verfication for launch
    
    current_account_info = mt5.account_info()
    if current_account_info.profit > current_account_info.balance * 0.005:
        mtt.MT5.close_all_night()
        # print("profit:" + str(current_account_info.profit))
        
    if datetime.now().weekday() not in (5,6):
        is_time = (datetime.now().minute % 3) == 0 and (datetime.now().second == 0) # be true every 3 minutes
    else:
        is_time = False

    # Launch the algorithm
    if is_time:

        # Open the trades
        for asset in info_order.keys():

            # Initialize the inputs
            symbol = info_order[asset][0]
            lot = info_order[asset][1]

            # Create the signals
            buy, sell = svm_reg_trading(symbol)

             # Run the algorithm
            if live:
                mtt.MT5.run(symbol, buy, sell,lot)
                # print("buy:" + str(buy) + " sell:" + str(sell))

            else:
                print(f"Symbol: {symbol}\t"
                     f"Buy: {buy}\t"
                     f"Sell: {sell}")
        time.sleep(1)