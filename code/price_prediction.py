import numpy as np
import pandas as pd
from datetime import datetime
from statsmodels.tsa.statespace.sarimax import SARIMAX
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.stats import spearmanr
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

def get_data():
    prices = pd.read_csv('data/clean_day_ahead_data.csv', parse_dates=['datetime'])
    weather = pd.read_csv('data/min15_weather_data.csv', parse_dates=['datetime'])

    data = pd.merge(prices, weather, on='datetime')

    data = data.set_index(['datetime'])

    return data

def add_time_features(df):
    df['hour']        = df.index.hour
    df['dayofweek']   = df.index.dayofweek
    df['month']       = df.index.month
    df['quarter']     = df.index.quarter
    df['is_weekend']  = df.index.dayofweek >= 5
    
    # Lag features (yesterday, last week)
    df['price_lag_1d']  = df['price'].shift(96)   # 1 day ago (hourly data)
    df['price_lag_7d']  = df['price'].shift(672)  # 1 week ago

    # Rolling averages
    df['price_roll_7d'] = df['price'].shift(96).rolling(672).mean()
    df['price_roll_3d'] = df['price'].shift(96).rolling(288).mean()

    return df

def get_metrics(y_test, preds, print_metrics=True):
    mae  = mean_absolute_error(y_test, preds)
    msae = mean_squared_error(y_test, preds)
    rho, _ = spearmanr(y_test, preds)
    if print_metrics:
        print(f"Spearman ρ: {rho:.3f}")  # 1.0 = perfect hour ordering
        print(f"MAE:  {mae:.2f}")
        print(f"MSAE:  {msae:.2f}")
    return mae, msae, rho

def naive_model(train_start = 0, train_length = 90 * 96, test_length = 3 * 96, print_metrics = True):
    
    data = get_data()

    
    #data['price_diff'] = data['price'].diff(24)
    data.dropna(inplace=True)
    y = data['price']
    y_test = y.iloc[train_start + train_length : train_start + train_length + test_length]
    # Naive prediction that just copies the result from the last day we had a prediction for
    rollback = 96
    while train_start + train_length + test_length - rollback > 365 * 96:
        rollback += 96
    naive_pred = y.iloc[train_start + train_length - rollback : train_start + train_length + test_length - rollback]

    min_len = min(len(naive_pred), len(y_test))
    naive_pred = naive_pred.iloc[:min_len]
    y_test = y_test.iloc[:min_len]

    return naive_pred, get_metrics(y_test, naive_pred, print_metrics)

def xgboost_model(train_start = 0, train_length = 90 * 96, test_length = 3 * 96, print_metrics = True):
    data = get_data()

    data = add_time_features(data)
    
    #data['price_diff'] = data['price'].diff(24)
    #data.dropna(inplace=True)

    features = ['FH','T','SQ','Q','hour', 'dayofweek', 'month', 'quarter', 'is_weekend',
    'price_lag_1d', 'price_lag_7d', 'price_roll_7d', 'price_roll_3d']
    X = data[features]
    y = data['price']
    X_train, X_test = X.iloc[train_start:train_start + train_length], X.iloc[train_start + train_length : train_start + train_length + test_length]
    y_train, y_test = y.iloc[train_start:train_start + train_length], y.iloc[train_start + train_length : train_start + train_length + test_length]
    # Naive prediction that just copies the result from 24 hours before
    naive_pred = y.iloc[train_start + train_length - 96 : train_start + train_length + test_length - 96]

    naive_pred.index = naive_pred.index + pd.Timedelta(days=1)

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
    df_preds = pd.DataFrame({'preds' : preds}, index=y_test)


    # Plot actual vs predicted
    #pd.DataFrame({'actual': y_test, 'predicted': naive_pred}).plot(figsize=(14, 4))
    #plt.title('Actual vs Predicted Energy Prices')
    #plt.show()

    # Plot feature importance
    #importance = pd.Series(model.feature_importances_, index=features)
    #importance.sort_values().plot(kind='barh', figsize=(8, 6))
    #plt.title('Feature Importance')
    #plt.show()
    return df_preds, get_metrics(y_test, preds, print_metrics)


def elastic_net(train_start = 0, train_length = 90 * 96, test_length = 3 * 96, print_metrics = True):
    data = get_data()

    data = add_time_features(data)
    
    #data['price_diff'] = data['price'].diff(24)
    #data.dropna(inplace=True)

    features = ['FH','T','SQ','Q','hour', 'dayofweek', 'month', 'quarter', 'is_weekend',
    'price_lag_1d', 'price_lag_7d', 'price_roll_7d', 'price_roll_3d']

    X = data[features]
    y = data['price']


    X_train, X_test = X.iloc[train_start:train_start + train_length], X.iloc[train_start + train_length : train_start + train_length + test_length]
    y_train, y_test = y.iloc[train_start:train_start + train_length], y.iloc[train_start + train_length : train_start + train_length + test_length]
    

    pipe = Pipeline([
        ('scaler', StandardScaler()),  # critical for regularized models
        ('model', ElasticNetCV(
            l1_ratio=[0.1, 0.5, 0.9, 1.0],  # 1.0 = pure LASSO
            cv=5,
            max_iter=5000
        ))
    ])

    pipe.fit(X_train, y_train)

    preds = pipe.predict(X_test)

    df_preds = pd.DataFrame({'preds' : preds}, index=y_test)

    # Plot actual vs predicted
    #pd.DataFrame({'actual': y_test, 'predicted': preds}).plot(figsize=(14, 4))
    #plt.title('Actual vs Predicted Energy Prices')
    #plt.show()
    return df_preds, get_metrics(y_test, preds, print_metrics)

# Sarimax model is currently not used as it took too long to run. Likely due to the long season length (96)
def sarimax_model():

    data = get_data()

    features = ['FH','T','SQ','Q']

    X = data[features]
    y = data['price']


    start = int(len(data) * 0.4)
    train_length = 96 * 120
    test_length = 96 * 3
    X_train, X_test = X.iloc[start:start + train_length], X.iloc[start + train_length : start + train_length + test_length]
    y_train, y_test = y.iloc[start:start + train_length], y.iloc[start + train_length : start + train_length + test_length]


    model = SARIMAX(y_train, exog=X_train, order=(1,1,1),
                    seasonal_order=(1,1,1,96), freq='15min')
    result = model.fit()

    preds = []
    for i in range(3):
        forecast = result.forecast(steps=96, exog=X_test.iloc[96*i : 96*(i+1)])
        preds.append(forecast)

        # Extend the model with new observations instead of refitting
        new_y = y_test.iloc[96*i : 96*(i+1)]
        new_X = X_test.iloc[96*i : 96*(i+1)]
        result = result.append(endog=new_y, exog=new_X, refit=False)

    mae  = mean_absolute_error(y_test, preds)
    msae = mean_squared_error(y_test, preds)
    alternate_error = sum(np.abs(y_test - preds))/len(y_test)
    print(f"MAE:  {mae:.2f}")
    print(f"MSAE:  {msae:.2f}")
    print(alternate_error)

     # Plot actual vs predicted
    pd.DataFrame({'actual': y_test, 'predicted': preds}).plot(figsize=(14, 4))
    plt.title('Actual vs Predicted Energy Prices')
    plt.show()






