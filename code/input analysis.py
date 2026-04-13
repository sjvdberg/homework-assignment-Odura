import numpy as np
import pandas as pd
from entsoe import EntsoePandasClient
from config import *
from datetime import datetime, date, time
import matplotlib.pyplot as plt
import seaborn as sns



def import_entsoe_data():
    client = EntsoePandasClient(api_key=entsoe_api_key)
    start = pd.Timestamp('20250101', tz='Europe/Amsterdam')
    end = pd.Timestamp('20251231', tz='Europe/Amsterdam')
    country_code = 'NL'

    ts = client.query_day_ahead_prices(country_code, start, end)
    ts.to_csv('data/day_ahead_data.csv')

# Converts the price data to UTC and interpolates missing values
def clean_entsoe_data():

    prices = pd.read_csv('data/day_ahead_data.csv')
    prices['datetime'] = pd.to_datetime(prices['datetime'], utc=True)
    prices = prices.set_index('datetime')
    min15_prices = prices.resample('15min').interpolate()

    min15_prices.to_csv('data/clean_day_ahead_data.csv')

# Adds timezones to the weather data and respamples them on a month by month basis
def clean_weather_data():
    hourly_weather_data = pd.read_csv('data/uurdata_knmi_2025.txt', comment='#')
    hourly_weather_data.columns = hourly_weather_data.columns.str.strip()
    hourly_weather_data['datetime'] = pd.to_datetime(hourly_weather_data['YYYYMMDD'], format='%Y%m%d') + pd.to_timedelta(hourly_weather_data['HH'] -1, unit='h')
    hourly_weather_data = hourly_weather_data[["datetime", "FH", "T", "SQ", "Q"]]
    hourly_weather_data = hourly_weather_data.set_index('datetime')
    hourly_weather_data.index = hourly_weather_data.index.tz_localize('Europe/Amsterdam', ambiguous='NaT', nonexistent='NaT')
    hourly_weather_data = hourly_weather_data[hourly_weather_data.index.notna()]
    hourly_weather_data.index = hourly_weather_data.index.tz_convert('UTC')

    min15_weather_data = hourly_weather_data.resample('15min').ffill()

    
    min15_weather_data.to_csv('data/min15_weather_data.csv')


# Creates a graph showing the average price for each day
def plot_data():
    prices = pd.read_csv('data/clean_day_ahead_data.csv')
    prices.plot(x='datetime', y='price')
    plt.tight_layout()
    plt.show()

#Creates a graph containing the average price for each month
def daily_average():
    prices = pd.read_csv('data/clean_day_ahead_data.csv', parse_dates=['datetime'])
    prices = prices.set_index('datetime')
    prices = prices.tz_convert('Europe/Amsterdam')

    df = pd.DataFrame()

    df['average'] = prices.resample('ME').mean()

    #df['daily_mean'] = prices.resample('ME').mean()
    #df['daily_min'] = prices.resample('D').min()
    #df['daily_max']  = prices.resample('D').max()
    #df['daily_min'] = df['daily_min'].resample('ME').mean()
    #df['daily_max']  = df['daily_max'].resample('ME').mean()

    df.plot()
    plt.tight_layout()
    plt.show()

#Creates a correlation matrix between the different variables
def correlation_matrix():
    prices = pd.read_csv('data/clean_day_ahead_data.csv', parse_dates=['datetime'])
    prices = prices.set_index('datetime')

    weather = pd.read_csv('data/min15_weather_data.csv', parse_dates=['datetime'])
    weather = weather.set_index('datetime')

    data = prices.join(weather, how='inner')

    corr = data.corr(method='spearman')

    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
    plt.title('Spearman correlation — weather vs price')
    plt.tight_layout()
    plt.show()

correlation_matrix()