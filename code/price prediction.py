import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error

def xgboost_model():
    prices = pd.read_csv('data/clean_day_ahead_data.csv', parse_dates=['datetime'])
    weather = pd.read_csv('data/min15_weather_data.csv', parse_dates=['datetime'])

    data = pd.merge(prices, weather, on='datetime')

    data = data.set_index(['datetime'])

    data = add_time_features(data)
    
    data['price_diff'] = data['price'].diff(24)
    data.dropna(inplace=True)

    features = ['FH','T','SQ','Q','hour', 'dayofweek', 'month', 'quarter', 'is_weekend',
    'price_lag_1d', 'price_lag_7d', 'price_roll_7d', 'price_roll_3d']

    X = data[features]
    y = data['price']

    print("gathered data")

    start = int(len(data) * 0.4)
    train_length = 96 * 90
    test_length = 96 * 20
    X_train, X_test = X.iloc[start:start + train_length], X.iloc[start + train_length : start + train_length + test_length]
    y_train, y_test = y.iloc[start:start + train_length], y.iloc[start + train_length : start + train_length + test_length]
    
    #split = int(len(data) * 0.98)
    #X_train, X_test = X.iloc[:split], X.iloc[split:]
    #y_train, y_test = y.iloc[:split], y.iloc[split:]


    model = xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=50,
        random_state=42
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=100
    )

    preds = model.predict(X_test)

    mae  = mean_absolute_error(y_test, preds)
    naive_error = np.mean(np.abs(np.diff(y_train)))
    mase = np.mean(np.abs(y_test.values - preds)) / naive_error
    print(f"MASE: {mase:.3f}")  # < 1 betekent beter dan naïef model
    print(f"MAE:  {mae:.2f}")

    # Plot actual vs predicted
    pd.DataFrame({'actual': y_test, 'predicted': preds}).plot(figsize=(14, 4))
    plt.title('Actual vs Predicted Energy Prices')
    plt.show()

    # Plot feature importance
    #importance = pd.Series(model.feature_importances_, index=features)
    #importance.sort_values().plot(kind='barh', figsize=(8, 6))
    #plt.title('Feature Importance')
    #plt.show()

    
    


def add_time_features(df):
    df['hour']        = df.index.hour
    df['dayofweek']   = df.index.dayofweek
    df['month']       = df.index.month
    df['quarter']     = df.index.quarter
    df['is_weekend']  = df.index.dayofweek >= 5
    
    # Lag features (yesterday, last week)
    df['price_lag_1d']  = df['price'].shift(24)   # 1 day ago (hourly data)
    df['price_lag_7d']  = df['price'].shift(168)  # 1 week ago

    # Rolling averages
    df['price_roll_7d'] = df['price'].shift(1).rolling(168).mean()
    df['price_roll_3d'] = df['price'].shift(1).rolling(72).mean()

    return df


def sarimax_model():

    prices = pd.read_csv('data/clean_day_ahead_data.csv', parse_dates=['datetime'])
    weather = pd.read_csv('data/min15_weather_data.csv', parse_dates=['datetime'])
    
    prices = prices.set_index('datetime')
    weather = weather.set_index('datetime')

    tot_data = pd.merge(prices, weather, on='datetime')

    model = SARIMAX(tot_data['price'], exog=tot_data[['FH','T','SQ','Q']], order=(2,1,2), seasonal_order=(1,1,1,24), freq='15min')

    result = model.fit()

    result.save('sarimax_model.pkl')

def plot_sarimax():

    prices = pd.read_csv('data/clean_day_ahead_data.csv', parse_dates=['datetime'])
    weather = pd.read_csv('data/min15_weather_data.csv', parse_dates=['datetime'])
    prices = prices.set_index(['datetime'])
    weather = weather.set_index(['datetime'])
    fitted_model = SARIMAXResults.load('sarimax_model.pkl')

    in_sample = fitted_model.predict(start=prices.index[0], end=prices.index[-1], exog=weather)


    valid = in_sample.dropna().index
    in_sample_valid = in_sample.loc[valid]
    prices_valid = prices.loc[valid]
    
    errors = np.abs(prices['price'] - in_sample)

    errorsum = np.sum(errors)
    mae = np.mean(np.abs(prices_valid - in_sample_valid))
    rmse = np.sqrt(np.mean((prices_valid - in_sample_valid)**2))

    print(f'MAE:  {mae:.2f}')
    print(f'RMSE: {rmse:.2f}')


xgboost_model()